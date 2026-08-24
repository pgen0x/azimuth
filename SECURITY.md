# Security Policy

## Reporting a Vulnerability

**Do not open a public issue for a security vulnerability.** Use GitHub's
[private security advisory](https://github.com/pgen0x/azimuth/security/advisories/new)
feature for this repository instead. This lets us discuss and fix the issue
before it's publicly disclosed.

Please include:
- A description of the vulnerability and its potential impact.
- Steps to reproduce (or a proof of concept).
- The affected version/commit.

## Scope

Azimuth trades real funds autonomously. Security issues most relevant to
this project:

- Anything that could leak or exfiltrate `SOLANA_PRIVATE_KEY`, RPC provider
  keys, or `HERMES_WEBHOOK_SECRET`.
- Webhook signature verification bypass (HMAC-SHA256 over
  `X-Webhook-Signature`).
- Injection or command-execution issues in the direct-deploy path
  (`DEPLOY_CMD`) or the `solana-dlmm` / `robinhood` skill scripts.
- Screening-gate logic that could be manipulated to force a deploy that
  should have been rejected.

Out of scope: pool/token quality judgment calls, PnL outcomes, or general
trading-strategy disagreements — those are bugs or design discussions, not
security reports (open a normal issue for those).

## Supported Versions

This project ships a single rolling `master` branch (see
[CHANGELOG.md](CHANGELOG.md) for released versions). Only the latest release
is supported — please upgrade before reporting.

## What's already covered

See [Security](README.md#security) in the README: wallet keys and RPC keys
never live in this repo (profile `.env` only), and the webhook is
HMAC-SHA256 signed.
