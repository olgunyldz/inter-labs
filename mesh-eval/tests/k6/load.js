// mesh-eval genel yük script'i (k6)
// PHASES : "hız:süre,hız:süre,..." (ör. "100:30s,300:30s"). Her aşama ayrı ölçülür (etiket phase=<i>).
// GAP    : aşamalar arası bekleme (sn), varsayılan 5
// TARGET : istek adresi;  METHOD: GET|POST;  HEADERS: "Ad: değer;Ad2: değer"
// MAX_VUS: en fazla sanal kullanıcı (varsayılan 3000)
import http from 'k6/http';

const phases = (__ENV.PHASES || '100:30s').split(',').map((p) => {
  const [rate, dur] = p.split(':');
  return { rate: parseInt(rate, 10), dur };
});
const gap = parseInt(__ENV.GAP || '5', 10);
const secs = (d) => (d.endsWith('m') ? parseFloat(d) * 60 : parseFloat(d));
const target = __ENV.TARGET;
const method = __ENV.METHOD || 'GET';
const headers = {};
(__ENV.HEADERS || '').split(';').filter((h) => h.includes(':')).forEach((h) => {
  const i = h.indexOf(':');
  headers[h.slice(0, i).trim()] = h.slice(i + 1).trim();
});

const scenarios = {};
const thresholds = {};
let start = 0;
phases.forEach((p, i) => {
  scenarios[`p${i}`] = {
    executor: 'constant-arrival-rate',
    rate: p.rate, timeUnit: '1s', duration: p.dur, startTime: `${start}s`,
    preAllocatedVUs: Math.min(Math.max(20, Math.ceil(p.rate / 10)), 500),
    maxVUs: parseInt(__ENV.MAX_VUS || '3000', 10),
    tags: { phase: `${i}` }, gracefulStop: '5s',
  };
  // eşikler alt metriklerin (aşama bazında) özete yazılmasını sağlar
  thresholds[`http_req_duration{phase:${i}}`] = ['max>=0'];
  thresholds[`http_req_failed{phase:${i}}`] = ['rate>=0'];
  thresholds[`http_reqs{phase:${i}}`] = ['count>=0'];
  thresholds[`dropped_iterations{scenario:p${i}}`] = ['count>=0'];
  start += secs(p.dur) + gap;
});

export const options = {
  scenarios, thresholds,
  summaryTrendStats: ['avg', 'min', 'med', 'p(90)', 'p(95)', 'p(99)', 'p(99.9)', 'max'],
  discardResponseBodies: true,
  noConnectionReuse: false,
  insecureSkipTLSVerify: true,
};

export function setup() {
  return { t0: Date.now() / 1000, phases, gap };
}

export default function () {
  http.request(method, target, null, { headers, timeout: '10s' });
}

export function handleSummary(data) {
  return { stdout: '\n==K6SUMMARY==\n' + JSON.stringify(data) + '\n==END==\n' };
}
