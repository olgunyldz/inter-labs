# Edge load balancer: internetten gelen 80/443'ü L4 (TCP) olarak dmz-a / dmz-b
# ingress'lerine dağıtır. TLS DMZ ingress'lerinde sonlanır; istemci IP'si
# PROXY protocol ile iletilir. __DMZ_A__ / __DMZ_B__ up.sh tarafından doldurulur.
global
  log stdout format raw local0

defaults
  mode tcp
  log global
  option tcplog
  timeout connect 3s
  timeout client 60s
  timeout server 60s

frontend http
  bind :80
  default_backend dmz_http

frontend https
  bind :443
  default_backend dmz_https

# Sağlık kontrolü: ingress-nginx default server'ının /healthz'i (port 80)
backend dmz_http
  balance roundrobin
  option httpchk GET /healthz
  http-check expect status 200
  default-server send-proxy check-send-proxy inter 3s fall 2 rise 2
  server dmz-a __DMZ_A__:80 check
  server dmz-b __DMZ_B__:80 check

backend dmz_https
  balance roundrobin
  option httpchk GET /healthz
  http-check expect status 200
  default-server send-proxy check-send-proxy inter 3s fall 2 rise 2
  server dmz-a __DMZ_A__:443 check port 80
  server dmz-b __DMZ_B__:443 check port 80

frontend stats
  mode http
  bind :8404
  stats enable
  stats uri /
  stats refresh 5s
