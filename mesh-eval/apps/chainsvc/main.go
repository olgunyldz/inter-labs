// chainsvc: mesh-eval servis zinciri test uygulaması.
//
// fake-service ile aynı ortam değişkenlerini ve JSON cevap biçimini kullanır; fark: HTTP keep-alive doğru
// çalışır (fake-service upstream hatasından sonra kalıcı bağlantıya bozuk cevap yazıyordu), gRPC istemcisi
// kalıcı tek bağlantı kullanır (L4 yük dengeleme davranışı gözlenebilir), SIGTERM'de bağlantıları boşaltır.
//
// Ortam değişkenleri:
//
//	NAME, MESSAGE, LISTEN_ADDR (:9090), SERVER_TYPE (http|grpc)
//	UPSTREAM_URIS (virgüllü; http://host:port veya grpc://host:port), UPSTREAM_WORKERS (paralel çağrı)
//	TIMING_50_PERCENTILE / _90_ / _99_ (süre, ör. 1ms)
//	ERROR_RATE (0..1), ERROR_TYPE (http_error|delay), ERROR_CODE (500), ERROR_DELAY (süre)
//	HTTP_CLIENT_REQUEST_TIMEOUT (10s), HTTP_CLIENT_APPEND_REQUEST (true: gelen yol upstream'e eklenir)
//	TRACING_ZIPKIN (http://host:9411 -> /api/v2/spans; boşsa kapalı, B3 başlıkları her zaman taşınır)
package main

import (
	"bytes"
	"context"
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	mrand "math/rand/v2"
	"net"
	"net/http"
	"os"
	"os/signal"
	"strconv"
	"strings"
	"sync"
	"syscall"
	"time"

	"google.golang.org/grpc"
	"google.golang.org/grpc/codes"
	"google.golang.org/grpc/credentials/insecure"
	"google.golang.org/grpc/encoding"
	"google.golang.org/grpc/metadata"
	"google.golang.org/grpc/status"
)

// ---------------------------------------------------------------- yapılandırma

type config struct {
	name, message, listen, serverType string
	upstreams                         []string
	workers                           int
	p50, p90, p99                     time.Duration
	errRate                           float64
	errType                           string
	errCode                           int
	errDelay                          time.Duration
	timeout                           time.Duration
	appendReq                         bool
	zipkin                            string
}

func env(k, d string) string {
	if v := os.Getenv(k); v != "" {
		return v
	}
	return d
}
func envDur(k, d string) time.Duration {
	v, err := time.ParseDuration(env(k, d))
	if err != nil {
		return 0
	}
	return v
}

func load() config {
	c := config{
		name: env("NAME", "service"), message: env("MESSAGE", "Hello World"), listen: env("LISTEN_ADDR", "0.0.0.0:9090"),
		serverType: env("SERVER_TYPE", "http"), errType: env("ERROR_TYPE", "http_error"),
		p50: envDur("TIMING_50_PERCENTILE", "0s"), errDelay: envDur("ERROR_DELAY", "0s"),
		timeout: envDur("HTTP_CLIENT_REQUEST_TIMEOUT", "10s"), appendReq: env("HTTP_CLIENT_APPEND_REQUEST", "true") == "true",
		zipkin: env("TRACING_ZIPKIN", ""),
	}
	c.p90 = envDur("TIMING_90_PERCENTILE", c.p50.String())
	c.p99 = envDur("TIMING_99_PERCENTILE", c.p90.String())
	c.workers, _ = strconv.Atoi(env("UPSTREAM_WORKERS", "1"))
	if c.workers < 1 {
		c.workers = 1
	}
	c.errRate, _ = strconv.ParseFloat(env("ERROR_RATE", "0"), 64)
	c.errCode, _ = strconv.Atoi(env("ERROR_CODE", "500"))
	for _, u := range strings.Split(os.Getenv("UPSTREAM_URIS"), ",") {
		if u = strings.TrimSpace(u); u != "" {
			c.upstreams = append(c.upstreams, u)
		}
	}
	if c.zipkin != "" && !strings.Contains(c.zipkin, "/api/") {
		c.zipkin = strings.TrimRight(c.zipkin, "/") + "/api/v2/spans"
	}
	return c
}

// ---------------------------------------------------------------- cevap

type Response struct {
	Name          string      `json:"name"`
	URI           string      `json:"uri"`
	Type          string      `json:"type"`
	IPAddresses   []string    `json:"ip_addresses"`
	StartTime     string      `json:"start_time"`
	EndTime       string      `json:"end_time"`
	Duration      string      `json:"duration"`
	Body          string      `json:"body,omitempty"`
	UpstreamCalls []*Response `json:"upstream_calls,omitempty"`
	Code          int         `json:"code"`
	Error         string      `json:"error,omitempty"`
}

type callRequest struct {
	Path string `json:"path"`
}

var (
	cfg      config
	localIPs []string
	httpc    *http.Client
	grpcMu   sync.Mutex
	grpcConn = map[string]*grpc.ClientConn{}
	tracer   *zipkinTracer
)

func ips() []string {
	var out []string
	addrs, _ := net.InterfaceAddrs()
	for _, a := range addrs {
		if n, ok := a.(*net.IPNet); ok && !n.IP.IsLoopback() && n.IP.To4() != nil {
			out = append(out, n.IP.String())
		}
	}
	return out
}

// işlem süresi: yüzdelik değerler arasında doğrusal dağılım
func sample() time.Duration {
	r := mrand.Float64()
	lerp := func(a, b time.Duration, f float64) time.Duration { return a + time.Duration(float64(b-a)*f) }
	switch {
	case r < 0.5:
		return lerp(0, cfg.p50, r/0.5)
	case r < 0.9:
		return lerp(cfg.p50, cfg.p90, (r-0.5)/0.4)
	case r < 0.99:
		return lerp(cfg.p90, cfg.p99, (r-0.9)/0.09)
	default:
		return cfg.p99
	}
}

// handle: tek isteğin işlenmesi (HTTP ve gRPC ortak). ok=false ise çağırana hata döner.
func handle(ctx context.Context, path string, tc traceCtx) (*Response, bool) {
	start := time.Now()
	resp := &Response{Name: cfg.name, URI: path, Type: "HTTP", IPAddresses: localIPs, Body: cfg.message, Code: 200}
	if cfg.serverType == "grpc" {
		resp.Type = "gRPC"
		resp.Code = 0
	}
	ok := true
	injectDelay := time.Duration(0)
	if cfg.errRate > 0 && mrand.Float64() < cfg.errRate {
		if cfg.errType == "delay" {
			injectDelay = cfg.errDelay
		} else {
			ok = false
			resp.Error = "Service error automatically injected"
			resp.Code = cfg.errCode
			if cfg.serverType == "grpc" {
				resp.Code = int(codes.Internal)
			}
		}
	}
	if ok && len(cfg.upstreams) > 0 {
		resp.UpstreamCalls = make([]*Response, len(cfg.upstreams))
		sem := make(chan struct{}, cfg.workers)
		var wg sync.WaitGroup
		for i, u := range cfg.upstreams {
			wg.Add(1)
			sem <- struct{}{}
			go func(i int, u string) {
				defer wg.Done()
				defer func() { <-sem }()
				resp.UpstreamCalls[i] = callUpstream(ctx, u, path, tc)
			}(i, u)
		}
		wg.Wait()
		for _, uc := range resp.UpstreamCalls {
			good := uc.Code == 200 || (uc.Type == "gRPC" && uc.Code == 0)
			if !good {
				ok = false
				resp.Error = fmt.Sprintf("Error processing upstream request: %s, %s", uc.URI, uc.Error)
				resp.Code = 500
				if cfg.serverType == "grpc" {
					resp.Code = int(codes.Internal)
				}
			}
		}
	}
	time.Sleep(sample() + injectDelay)
	end := time.Now()
	resp.StartTime, resp.EndTime = start.Format("2006-01-02T15:04:05.000000"), end.Format("2006-01-02T15:04:05.000000")
	resp.Duration = end.Sub(start).String()
	return resp, ok
}

func upstreamPath(path string) string {
	if cfg.appendReq && path != "" {
		return path
	}
	return "/"
}

func callUpstream(ctx context.Context, uri, path string, tc traceCtx) *Response {
	child := tc.child()
	start := time.Now()
	var r *Response
	if strings.HasPrefix(uri, "grpc://") {
		r = callGRPC(ctx, strings.TrimPrefix(uri, "grpc://"), path, child)
	} else {
		r = callHTTP(ctx, uri, path, child)
	}
	tracer.span(child, "client", cfg.name, uri, start, time.Since(start))
	return r
}

func callHTTP(ctx context.Context, base, path string, tc traceCtx) *Response {
	u := strings.TrimRight(base, "/") + upstreamPath(path)
	errResp := func(code int, e error) *Response {
		return &Response{URI: u, Type: "HTTP", Code: code, Error: e.Error()}
	}
	ctx, cancel := context.WithTimeout(ctx, cfg.timeout)
	defer cancel()
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, u, nil)
	if err != nil {
		return errResp(-1, err)
	}
	tc.inject(req.Header.Set)
	res, err := httpc.Do(req)
	if err != nil {
		return errResp(-1, err)
	}
	defer res.Body.Close()
	b, err := io.ReadAll(res.Body) // gövde her zaman okunur -> bağlantı havuza temiz döner
	if err != nil {
		return errResp(-1, err)
	}
	var out Response
	if json.Unmarshal(b, &out) != nil || out.Name == "" {
		return &Response{URI: u, Type: "HTTP", Code: res.StatusCode, Error: fmt.Sprintf("expected code 200, got %d", res.StatusCode)}
	}
	out.URI = u
	out.Code = res.StatusCode
	if res.StatusCode != 200 && out.Error == "" {
		out.Error = fmt.Sprintf("expected code 200, got %d", res.StatusCode)
	}
	return &out
}

func grpcClient(target string) (*grpc.ClientConn, error) {
	grpcMu.Lock()
	defer grpcMu.Unlock()
	if c, ok := grpcConn[target]; ok {
		return c, nil
	}
	c, err := grpc.NewClient("passthrough:///"+target, grpc.WithTransportCredentials(insecure.NewCredentials()),
		grpc.WithDefaultCallOptions(grpc.CallContentSubtype(jsonCodec{}.Name())))
	if err == nil {
		grpcConn[target] = c
	}
	return c, err
}

func callGRPC(ctx context.Context, target, path string, tc traceCtx) *Response {
	uri := "grpc://" + target
	c, err := grpcClient(target)
	if err != nil {
		return &Response{URI: uri, Type: "gRPC", Code: int(codes.Unavailable), Error: err.Error()}
	}
	ctx, cancel := context.WithTimeout(ctx, cfg.timeout)
	defer cancel()
	md := metadata.MD{}
	tc.inject(func(k, v string) { md.Set(strings.ToLower(k), v) })
	ctx = metadata.NewOutgoingContext(ctx, md)
	var out Response
	err = c.Invoke(ctx, "/chain.Chain/Call", &callRequest{Path: upstreamPath(path)}, &out)
	if err != nil {
		st, _ := status.FromError(err)
		msg := st.Message()
		if strings.HasPrefix(msg, "{") && json.Unmarshal([]byte(msg), &out) == nil {
			msg = out.Error
		} else {
			out = Response{}
		}
		out.Code, out.Error = int(st.Code()), msg
	}
	out.URI, out.Type = uri, "gRPC"
	return &out
}

// ---------------------------------------------------------------- gRPC (JSON codec, protobuf gerektirmez)

type jsonCodec struct{}

func (jsonCodec) Marshal(v any) ([]byte, error)   { return json.Marshal(v) }
func (jsonCodec) Unmarshal(b []byte, v any) error { return json.Unmarshal(b, v) }
func (jsonCodec) Name() string                    { return "json" }

type chainServer interface{}

func grpcHandler(_ any, ctx context.Context, dec func(any) error, _ grpc.UnaryServerInterceptor) (any, error) {
	var in callRequest
	if err := dec(&in); err != nil {
		return nil, err
	}
	md, _ := metadata.FromIncomingContext(ctx)
	tc := extract(func(k string) string {
		if v := md.Get(strings.ToLower(k)); len(v) > 0 {
			return v[0]
		}
		return ""
	})
	start := time.Now()
	resp, ok := handle(ctx, in.Path, tc)
	tracer.span(tc, "server", cfg.name, "/chain.Chain/Call", start, time.Since(start))
	if !ok {
		// cevap gövdesi de taşınır ki çağıran upstream ayrıntısını görsün
		// gRPC hata durumu (mesh hatayı görür) + mesaj olarak JSON cevap (çağıran zincir ayrıntısını görür)
		b, _ := json.Marshal(resp)
		return nil, status.Error(codes.Code(resp.Code), string(b))
	}
	return resp, nil
}

var serviceDesc = grpc.ServiceDesc{
	ServiceName: "chain.Chain",
	HandlerType: (*chainServer)(nil),
	Methods:     []grpc.MethodDesc{{MethodName: "Call", Handler: grpcHandler}},
	Metadata:    "chain.proto",
}

// ---------------------------------------------------------------- B3 / Zipkin

type traceCtx struct{ traceID, spanID, parentID, sampled string }

func newID(n int) string {
	b := make([]byte, n)
	_, _ = rand.Read(b)
	return hex.EncodeToString(b)
}

func extract(get func(string) string) traceCtx {
	tc := traceCtx{traceID: get("X-B3-TraceId"), spanID: get("X-B3-SpanId"), parentID: get("X-B3-ParentSpanId"), sampled: get("X-B3-Sampled")}
	if tc.traceID == "" {
		tc = traceCtx{traceID: newID(16), spanID: newID(8), sampled: "1"}
	}
	if tc.sampled == "" {
		tc.sampled = "1"
	}
	return tc
}

func (t traceCtx) child() traceCtx {
	return traceCtx{traceID: t.traceID, spanID: newID(8), parentID: t.spanID, sampled: t.sampled}
}

func (t traceCtx) inject(set func(string, string)) {
	set("X-B3-TraceId", t.traceID)
	set("X-B3-SpanId", t.spanID)
	if t.parentID != "" {
		set("X-B3-ParentSpanId", t.parentID)
	}
	set("X-B3-Sampled", t.sampled)
}

type zipkinTracer struct {
	url string
	ch  chan map[string]any
}

func newTracer(url string) *zipkinTracer {
	t := &zipkinTracer{url: url, ch: make(chan map[string]any, 10000)}
	if url == "" {
		return t
	}
	go func() {
		batch := []map[string]any{}
		tick := time.NewTicker(time.Second)
		flush := func() {
			if len(batch) == 0 {
				return
			}
			b, _ := json.Marshal(batch)
			if r, err := http.Post(t.url, "application/json", bytes.NewReader(b)); err == nil {
				_, _ = io.Copy(io.Discard, r.Body)
				r.Body.Close()
			}
			batch = batch[:0]
		}
		for {
			select {
			case s := <-t.ch:
				if batch = append(batch, s); len(batch) >= 200 {
					flush()
				}
			case <-tick.C:
				flush()
			}
		}
	}()
	return t
}

func (t *zipkinTracer) span(tc traceCtx, kind, svc, name string, start time.Time, d time.Duration) {
	if t == nil || t.url == "" || tc.sampled == "0" {
		return
	}
	s := map[string]any{"traceId": tc.traceID, "id": tc.spanID, "kind": strings.ToUpper(kind), "name": name,
		"timestamp": start.UnixMicro(), "duration": d.Microseconds(), "localEndpoint": map[string]any{"serviceName": svc}}
	if tc.parentID != "" {
		s["parentId"] = tc.parentID
	}
	select {
	case t.ch <- s:
	default: // kuyruk doluysa düşür (yükü etkilemesin)
	}
}

// ---------------------------------------------------------------- sunucular

func httpHandler(w http.ResponseWriter, r *http.Request) {
	_, _ = io.Copy(io.Discard, r.Body)
	tc := extract(r.Header.Get)
	start := time.Now()
	resp, ok := handle(r.Context(), r.URL.Path, tc)
	tracer.span(tc, "server", cfg.name, r.Method+" "+r.URL.Path, start, time.Since(start))
	b, _ := json.MarshalIndent(resp, "", "  ")
	w.Header().Set("Content-Type", "application/json")
	w.Header().Set("Content-Length", strconv.Itoa(len(b)+1))
	if !ok {
		w.WriteHeader(resp.Code)
	}
	_, _ = w.Write(append(b, '\n'))
}

func main() {
	cfg = load()
	localIPs = ips()
	tracer = newTracer(cfg.zipkin)
	httpc = &http.Client{Transport: &http.Transport{
		MaxIdleConns: 1000, MaxIdleConnsPerHost: 200, IdleConnTimeout: 60 * time.Second,
		DialContext: (&net.Dialer{Timeout: 3 * time.Second, KeepAlive: 30 * time.Second}).DialContext,
	}}
	lis, err := net.Listen("tcp", cfg.listen)
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
	stop := make(chan os.Signal, 1)
	signal.Notify(stop, syscall.SIGTERM, os.Interrupt)

	if cfg.serverType == "grpc" {
		encoding.RegisterCodec(jsonCodec{})
		gs := grpc.NewServer()
		gs.RegisterService(&serviceDesc, struct{}{})
		go func() { <-stop; gs.GracefulStop() }()
		if err := gs.Serve(lis); err != nil {
			fmt.Fprintln(os.Stderr, err)
		}
		return
	}
	encoding.RegisterCodec(jsonCodec{})
	mux := http.NewServeMux()
	mux.HandleFunc("/ready", func(w http.ResponseWriter, _ *http.Request) { _, _ = w.Write([]byte("OK\n")) })
	mux.HandleFunc("/health", func(w http.ResponseWriter, _ *http.Request) { _, _ = w.Write([]byte("OK\n")) })
	mux.HandleFunc("/", httpHandler)
	srv := &http.Server{Handler: mux, ReadHeaderTimeout: 5 * time.Second, IdleTimeout: 90 * time.Second}
	go func() {
		<-stop
		// SIGTERM: yeni bağlantı kabul etme, mevcut istekleri bitir (en fazla 8 sn)
		ctx, cancel := context.WithTimeout(context.Background(), 8*time.Second)
		defer cancel()
		_ = srv.Shutdown(ctx)
	}()
	if err := srv.Serve(lis); err != nil && !errors.Is(err, http.ErrServerClosed) {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
