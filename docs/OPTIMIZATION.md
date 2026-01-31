# NEURAXIS Performance Optimization Checklist

## Frontend (Next.js)

- [x] **Configuration**: `next.config.js` updated with `compress: true` and `swcMinify`.
- [x] **Bundle Analysis**: Use `ANALYZE=true npm run build` to check bundles. Target initial size < 300KB.
- [ ] **Image Optimization**: Ensure all `<Image />` components use `priority` for LCP candidates and `sizes` prop.
- [ ] **Code Splitting**: Verify `dynamic()` imports for heavy components (e.g. `TiptapEditor`, `DicomViewer`).
- [ ] **Fonts**: Use `next/font` with `swap` display strategy.
- [ ] **Virtualization**: Use `react-window` for any list > 50 items.

## Backend (FastAPI)

- [x] **Rate Limiting**: `RateLimitMiddleware` enabled (100 req/min default).
- [x] **Compression**: `GZipMiddleware` enabled for responses > 1KB.
- [x] **Caching**: `RedisCache` decorator applied to expensive GET endpoints (e.g. CDSS rules, Report generation).
- [x] **Database**: Run `scripts/check_indexes.py` weekly to identify missing indexes.
- [ ] **Async DB**: Ensure all DB calls use `await` and `asyncpg`.

## Infrastructure & Ops

- [ ] **CDN**: Configure CloudFront/Vercel Edge for static assets.
- [ ] **Database Replicas**: Enable Read Replicas for reporting queries.
- [x] **Load Testing**: Run `k6 run scripts/load_test_k6.js` before major releases. Target p95 < 200ms.
- [ ] **Monitoring**: Set up Prometheus/Grafana or Datadog for API latency and Error Rates.
- [ ] **Background Jobs**: Offload heavy processing (e.g. DICOM analysis) to Celery workers.

## Production Launch Constraints

- **Lighthouse Score**: Must be > 90 on Desktop.
- **API Latency**: p95 < 200ms.
- **Error Rate**: < 0.1%.
