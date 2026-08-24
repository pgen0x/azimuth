## What this changes

<!-- One logical change per PR (see CONTRIBUTING.md). -->

## Why

<!-- The failure mode this fixes or the false rejection/reason for a
gate/threshold change. "Seemed better" isn't enough — this trades real
funds. -->

## Type of change

- [ ] `fix` — bug fix (no behavior contract change)
- [ ] `feat` — new gate / mode / config option (backward-compatible)
- [ ] `feat!` / `BREAKING CHANGE` — webhook payload, `.env` surface, or CLI break
- [ ] `docs` / `chore` / `refactor` — no behavior change

## Checklist

- [ ] `go build -o azimuth .` and `go vet ./...` pass
- [ ] Read [`CLAUDE.md`](../CLAUDE.md) and this doesn't revert a documented
      convention (batch-not-per-pool, fail-open gates, Redis TTL semantics)
      without prior discussion
- [ ] If this touches screening logic, the webhook payload, or the
      `solana-dlmm` / `robinhood` skill scripts: exercised manually against a
      real or `DRY_RUN` Hermes profile
- [ ] If the webhook payload shape changed: updated
      [`docs/SIGNAL_SCHEMA.md`](../docs/SIGNAL_SCHEMA.md)
- [ ] Commit messages follow
      [Conventional Commits](https://www.conventionalcommits.org/)

## Related issues

<!-- Closes #... -->
