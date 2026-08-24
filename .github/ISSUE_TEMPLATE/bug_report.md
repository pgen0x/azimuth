---
name: Bug report
about: Something in the daemon or skill scripts isn't working as expected
title: "fix: "
labels: bug
assignees: ''
---

## What happened

<!-- Clear description of the bug. -->

## What you expected

<!-- What should have happened instead. -->

## Steps to reproduce

1.
2.
3.

## Logs

<!-- Relevant daemon log lines, e.g. from:
journalctl --user -u azimuth -n 200 --no-pager
Redact anything sensitive (wallet addresses, secrets). -->

```
paste here
```

## Environment

- Mode(s) enabled (Casual / Multiday / Turnover / Pulse / Robinhood modes):
- `azimuth -version` output:
- Deploy mode: webhook / direct (`DEPLOY_CMD` set)
- OS / Go version:

## Config

<!-- Your relevant .env values, WITH SECRETS REDACTED (webhook secret, RPC
keys, private keys). Never paste raw secrets here. -->

```
paste here
```
