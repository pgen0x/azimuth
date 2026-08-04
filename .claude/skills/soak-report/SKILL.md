---
name: soak-report
description: Summarize an azimuth soak window from the journal — batches, deploys, and the gates that actually decided each outcome, per mode. Use when judging whether a mode or threshold change is working.
---

# Soak report

Answers one question: **over this window, what did each mode see, and what
stopped it?** A mode that emits fifty batches and deploys nothing is not idle —
one gate is eating everything, and the gate narrative names it.

## 1. Run the counter

```bash
.claude/skills/soak-report/soak_report.sh "24 hours ago"
```

The argument is passed straight to `journalctl --since`, so `"3 days ago"`,
`"2026-08-01"`, and `"09:00"` all work. Counts come from fixed greps so two runs
over the same window agree.

## 2. Read it, don't just paste it

- **signals ≫ deploys** — the pipeline is rejecting after the daemon's screen.
  The "Decisive gates" block is the answer; the top entry is the binding
  constraint. `Batch reject` is the conviction layer, `Skipping` is a
  per-candidate live gate (rent, entry timing, cooldown), `Aborting:` is
  pre-flight (balance, malformed payload).
- **signals ≈ 0** — nothing survived the daemon's own screen. Look at
  "Pre-screen rejects", then at the mode's `ModeParams` in
  `internal/meteora/screen.go`. Remember the fee/TVL floor is scoped to the
  discovery *window*, not to 24h: 0.3 over a 30m window is ~14.4%/day.
- **deployed=false with no gate lines** — the pipeline ran and picked nothing
  silently. That is a bug in the narrative plumbing, not a quiet market.
- **errors nonzero** — fetch errors mean the window's counts undercount; say so
  rather than reporting the numbers flat.

## 3. Check the mode was actually enabled

A mode absent from the table may simply be off. The startup banner has the
truth:

```bash
journalctl --user -u azimuth --no-pager | grep -m1 'scanner started'
```

Do not infer "the screen is too tight" from a mode that never ran.

## 4. Reporting rules

Report what the journal says. If the window is short, say the sample is thin
rather than drawing a conclusion from four batches. Never state a P&L or a
position outcome from this skill — the journal records *entry decisions*; exits
belong to `dlmm_monitor.py` and its own reporting. If asked whether a change
worked, compare two windows explicitly (before/after the restart) instead of
eyeballing one.
