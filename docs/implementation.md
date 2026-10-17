# Implementation Status and Roadmap

## Included in this MVP
- [x] React dashboard and application form
- [x] FastAPI health endpoint and OpenAPI docs
- [x] PDF/DOCX resume parsing with file size/signature checks
- [x] Basic requirement coverage and matched/missing/unclear buckets
- [x] Optional LLM-based draft generation with conservative fallback
- [x] PDF downloads and LaTeX source download
- [x] Backend unit tests

## Recommended before production
- [ ] Add authentication and per-user application ownership
- [ ] Add delete endpoint, expiry job and explicit retention policy
- [ ] Move artifacts to private object storage and avoid persistent candidate data
- [ ] Add malware scanning, stricter file parser sandboxing, request rate limits and audit logging
- [ ] Add structured candidate-fact review/edit step before generating documents
- [ ] Add integration tests for upload and all artifact downloads
- [ ] Add a real LaTeX compiler in an isolated worker if compiled-from-TeX PDF output is required
- [ ] Add accessibility review and deployment configuration
