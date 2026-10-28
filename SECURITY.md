# Security and deployment

This repository is a local development application. The normal launcher binds to loopback and uses a development identity. Do not expose that configuration as a shared internet service.

For shared deployment, establish production authentication and account/session lifecycle, organization/tenant access controls, restricted CORS, secure secrets and storage, database backups/migration checks, rate limits and worker operations. Existing ownership and read-only-role tests cover specific paths; they do not certify all deployment configurations.

Never commit real environment files, provider sessions/cookies, private databases, uploads or credentials in examples/comments. Browser map keys must have appropriate domain/API restrictions; server credentials stay server-side.

Tests and screenshots must use explicitly synthetic disposable data. Do not include private evidence in public issues. Report security concerns through GitHub's private vulnerability reporting if enabled; otherwise contact the repository owner without posting secrets or private records publicly.
