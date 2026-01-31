import { check, sleep } from "k6";
import http from "k6/http";

export const options = {
  stages: [
    { duration: "30s", target: 20 }, // Ramp to 20 users
    { duration: "1m", target: 50 }, // Stay at 50
    { duration: "30s", target: 0 }, // Ramp down
  ],
  thresholds: {
    http_req_duration: ["p(95)<200"], // 95% of requests must complete below 200ms
    http_req_failed: ["rate<0.01"], // <1% errors
  },
};

export default function () {
  const BASE_URL = __ENV.API_URL || "http://localhost:8000";

  // Health Check
  const res = http.get(`${BASE_URL}/health`);
  check(res, { "status was 200": (r) => r.status == 200 });

  // Simulate usage (if auth token available, would test secured endpoints)
  // const res2 = http.get(`${BASE_URL}/api/v1/cdss/rules`);
  // check(res2, { 'rules ok': (r) => r.status == 200 });

  sleep(1);
}
