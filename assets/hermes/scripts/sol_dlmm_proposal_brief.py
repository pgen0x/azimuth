#!/usr/bin/env python3
"""Pre-run script for the `sol_dlmm_daily_proposal` cron job.

Builds the evidence brief the proposal agent reasons over. Everything the agent
is allowed to cite is computed HERE, deterministically, and printed once; the
agent reads only this text and proposes threshold changes to the operator.

WHY THE ARITHMETIC IS NOT THE AGENT'S JOB. Stage 2 of the restore-AI plan asks
an LLM to recommend parameter changes over a journal of several hundred closes.
An agent that greps that journal itself burns a large prompt and — worse — has
been observed inventing the numbers it could not read (the fabricated deploy
reports that removed the LLM from the entry path in the first place). A
proposal is only as good as its evidence, so the evidence is precomputed and
the agent's contribution is confined to judgment over it.

WHAT IS DELIBERATELY REPORTED AS "NOT MEASURABLE". Three sections can be too
thin to support a proposal, and each says so in its own words rather than
printing a confident-looking number over a handful of samples:
  - the signal-weight lifts, when no signal separates winners from losers;
  - the AI-hold comparison, until enough closes carry `ai_holds`;
  - any mode or exit reason under MIN_MODE_SAMPLES closes.
An agent told "this is not measurable yet" proposes nothing, which is the
correct output. An agent shown a number computed from four samples proposes
noise — the failure this whole job was gated on avoiding.
"""
import collections
import json
import os
import re
import statistics
import subprocess
import sys
import time

PROFILE = "__PROFILE__"
MEMORIES = os.path.join(PROFILE, "memories")
CLOSES_PATH = os.path.join(MEMORIES, "dlmm_closes.jsonl")
HOLDS_PATH = os.path.join(MEMORIES, "ai_holds.jsonl")
WEIGHTS_PATH = os.path.join(MEMORIES, "signal_weights.json")
SOUL_PATH = os.path.join(PROFILE, "SOUL.md")

WINDOW_DAYS = 7
# Below this a win rate is a coin flip dressed as a statistic.
MIN_MODE_SAMPLES = 15
# |lift| below this is indistinguishable from noise at these sample counts —
# the learner's own smoothing parks such a signal near weight 1.0, where
# dlmm_pipeline.py skips it entirely.
LIFT_NOISE_FLOOR = 0.08
SOLANA_MODES = ("casual", "multiday", "turnover", "pulse")


def load_closes():
    """Real, attributable closes inside the window."""
    if not os.path.exists(CLOSES_PATH):
        return []
    cutoff = time.time() - WINDOW_DAYS * 86400
    out = []
    with open(CLOSES_PATH, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("dry_run") or rec.get("pnl_sol") is None:
                continue
            if (rec.get("ts") or 0) < cutoff:
                continue
            out.append(rec)
    return out


# Prepositions left dangling once a measurement is stripped off the end
# ("out of range for 2.1m" -> "out of range for" -> "out of range").
_TRAILING_STOPWORDS = {"for", "at", "of", "to", "in", "by", "after", "under", "over"}


def reason_class(reason):
    """Collapse one close reason to the rule that fired.

    Reasons carry their own measurements ("Sustained downtrend dump (1h -34.6%
    <= -5.0% ...)", "Out of range for 2.1m"), which makes every string unique
    and every naive tally a list of ones. Cutting at the first parenthesis or
    dash is not enough on its own: the OOR rule states its minutes inline and
    so fragments into one row per elapsed time — 2.0m, 2.1m, 2.2m — hiding the
    rule that fires most often in this system behind a dozen samples of one.
    So drop any token carrying a digit, then the preposition it leaves
    stranded."""
    text = re.split(r"[(—-]", str(reason or "unknown"), maxsplit=1)[0]
    words = [w for w in text.lower().split() if not any(ch.isdigit() for ch in w)]
    while words and words[-1] in _TRAILING_STOPWORDS:
        words.pop()
    return " ".join(words) or "unknown"


def fmt_sol(v):
    return f"{v:+.4f}"


def section_modes(closes):
    print(f"\n## Outcomes by mode ({WINDOW_DAYS}d window, {len(closes)} closes)\n")
    if not closes:
        print("No closes in the window. Propose nothing on outcome grounds.")
        return
    by_mode = collections.defaultdict(list)
    for r in closes:
        by_mode[r.get("mode") or "unknown"].append(r)
    print("| mode | n | win% | net SOL | mean % | median hold |")
    print("|---|---|---|---|---|---|")
    for mode in sorted(by_mode, key=lambda m: -len(by_mode[m])):
        rs = by_mode[mode]
        pnl = [float(r["pnl_sol"]) for r in rs]
        pct = [float(r.get("pnl_pct") or 0) for r in rs]
        ages = [float(r.get("age_min") or 0) for r in rs]
        wins = sum(1 for v in pnl if v > 0)
        thin = "" if len(rs) >= MIN_MODE_SAMPLES else " ⚠thin"
        print(f"| {mode}{thin} | {len(rs)} | {100.0 * wins / len(rs):.0f}% | "
              f"{fmt_sol(sum(pnl))} | {statistics.mean(pct):+.2f}% | "
              f"{statistics.median(ages):.0f}m |")
    thin_modes = sorted(m for m, rs in by_mode.items() if len(rs) < MIN_MODE_SAMPLES)
    if thin_modes:
        print(f"\n⚠ Under {MIN_MODE_SAMPLES} closes, so NOT a basis for a proposal: "
              f"{', '.join(thin_modes)}.")


def section_reasons(closes):
    print(f"\n## Which exit rule costs what ({WINDOW_DAYS}d)\n")
    if not closes:
        print("No closes in the window.")
        return
    by_reason = collections.defaultdict(list)
    for r in closes:
        by_reason[reason_class(r.get("reason"))].append(float(r["pnl_sol"]))
    print("The actionable table: a rule with a large negative net is either firing")
    print("too late, or firing on positions it should not be firing on at all.\n")
    print("| exit reason | n | net SOL | mean SOL | win% |")
    print("|---|---|---|---|---|")
    for reason, pnl in sorted(by_reason.items(), key=lambda kv: sum(kv[1])):
        wins = sum(1 for v in pnl if v > 0)
        thin = "" if len(pnl) >= MIN_MODE_SAMPLES else " ⚠thin"
        print(f"| {reason}{thin} | {len(pnl)} | {fmt_sol(sum(pnl))} | "
              f"{fmt_sol(statistics.mean(pnl))} | {100.0 * wins / len(pnl):.0f}% |")


def section_weights():
    print("\n## Signal weights — what the learner found\n")
    try:
        with open(WEIGHTS_PATH, encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Unreadable ({exc}). Treat signal weighting as unknown; propose nothing about it.")
        return
    weights = data.get("weights") or {}
    lifts = data.get("lifts") or {}
    print(f"last recalc {data.get('last_recalc') or 'never'} "
          f"(recalc_count {data.get('recalc_count') or 0})\n")
    print("| signal | weight | lift |")
    print("|---|---|---|")
    for name in sorted(weights):
        lift = lifts.get(name)
        shown = "no read" if lift is None else f"{lift:+.4f}"
        print(f"| {name} | {weights[name]:.3f} | {shown} |")
    measured = [abs(v) for v in lifts.values() if v is not None]
    if not measured:
        print("\nNo lift was measurable this window. Propose nothing about entry signals.")
    elif max(measured) < LIFT_NOISE_FLOOR:
        print(f"\n**Every |lift| is below {LIFT_NOISE_FLOOR} — no entry signal separates winners from")
        print("losers in this window.** The weights are converging toward 1.0 by design, and")
        print("dlmm_pipeline.py skips any weight within 0.05 of 1.0. Do NOT propose entry-gate")
        print("changes justified by these weights: they say the screen's inputs carry no")
        print("predictive information, not that any particular one should move.")


def section_holds(closes):
    print("\n## AI exit-review holds\n")
    held = [r for r in closes if (r.get("ai_holds") or 0) > 0]
    unheld = [r for r in closes if r.get("ai_holds") == 0]
    journaled = 0
    if os.path.exists(HOLDS_PATH):
        with open(HOLDS_PATH, encoding="utf-8") as f:
            journaled = sum(1 for line in f if line.strip())
    print(f"holds journaled: {journaled} | closes carrying the field: {len(held) + len(unheld)}")
    if len(held) < MIN_MODE_SAMPLES:
        print(f"\nOnly {len(held)} held close(s) in the window. The stage-1 exit review is NOT yet")
        print("measurable — say so plainly and propose no change to the hold bands or its prompt.")
        return
    hp = statistics.mean(float(r["pnl_sol"]) for r in held)
    up = statistics.mean(float(r["pnl_sol"]) for r in unheld) if unheld else 0.0
    print(f"\nheld    n={len(held):<4} mean {fmt_sol(hp)} SOL")
    print(f"unheld  n={len(unheld):<4} mean {fmt_sol(up)} SOL")
    verdict = "BEATING" if hp > up else "LOSING TO"
    print(f"\nHolds are {verdict} the rules by {fmt_sol(hp - up)} SOL/close.")


def section_funnel():
    print("\n## Daemon screen funnel (last 24h)\n")
    try:
        proc = subprocess.run(
            ["journalctl", "--user", "-u", "azimuth", "--since", "24 hours ago", "--no-pager"],
            capture_output=True, text=True, timeout=60,
        )
        lines = proc.stdout.splitlines()
    except Exception as exc:
        print(f"journalctl unavailable ({exc}) — no funnel data; propose nothing about screening.")
        return
    totals = collections.defaultdict(collections.Counter)
    cycles = collections.Counter()
    for line in lines:
        m = re.search(r"scanner\[([\w-]+)\]: cycle done — (.+)$", line)
        if not m:
            continue
        mode = m.group(1)
        if mode not in SOLANA_MODES:
            continue  # the Robinhood modes are a different venue and thesis
        cycles[mode] += 1
        for key, val in re.findall(r"(\w+)=(\d+)", m.group(2)):
            totals[mode][key] += int(val)
    if not cycles:
        print("No Solana scanner cycles in the last 24h — the daemon is down, or every")
        print("Solana mode is switched off. Check before reading anything else here.")
        return
    print("Summed over each mode's cycles. `sent` is what reached the deploy path; a mode")
    print("with high `fetched` and zero `sent` is being screened out, and the counter naming")
    print("the stage is where a threshold would have to move.\n")
    for mode in sorted(cycles, key=lambda m: -cycles[m]):
        parts = " ".join(f"{k}={v}" for k, v in totals[mode].most_common())
        print(f"- **{mode}** ({cycles[mode]} cycles): {parts}")


_GATE_CLASSES = (
    ("dev-blocklisted", "dev blocklist"),
    ("rug-blacklisted", "rug mint blacklist"),
    ("pool memory", "pool memory"),
    ("mint cooldown", "mint cooldown"),
    ("pool cooldown", "pool cooldown"),
    ("already exposed to token", "already exposed (token)"),
    ("already have an active position", "already exposed (pool)"),
    ("entry timing check", "entry timing"),
    ("dumping", "momentum"),
    ("trend", "momentum"),
)


def gate_class(tail):
    """Bucket a pipeline `Skipping X-SOL - <tail>` reason into a stable class."""
    low = tail.lower()
    for needle, label in _GATE_CLASSES:
        if needle in low:
            return label
    return "other"


def section_gates():
    print("\n## Pipeline gates — what was refused after the screen (last 24h)\n")
    try:
        proc = subprocess.run(
            ["journalctl", "--user", "-u", "azimuth", "--since", "24 hours ago", "--no-pager"],
            capture_output=True, text=True, timeout=60,
        )
        lines = proc.stdout.splitlines()
    except Exception as exc:
        print(f"journalctl unavailable ({exc}) — no gate data; propose nothing about blocklists.")
        return

    # DISTINCT tokens per class, not line counts: the pipeline re-prints the same
    # skip every cycle, so a raw count measures how long a pool stayed in the
    # feed, not how much the gate actually refused.
    per_class = collections.defaultdict(set)
    for line in lines:
        m = re.search(r"Skipping ([\w.\-]+)-SOL - (.+)$", line)
        if m:
            per_class[gate_class(m.group(2))].add(m.group(1))
    dead = collections.Counter(
        m.group(1).strip().rstrip(".")
        for m in (re.search(r"❌ (No candidates.+)$", ln) for ln in lines) if m
    )

    if not per_class and not dead:
        print("No pipeline skips logged in the last 24h — either nothing reached the")
        print("deploy path at all (check the screen funnel above) or every batch deployed.")
    else:
        print("`section_funnel` above stops at `sent`. This is what happened AFTER that:")
        print("the gates inside `dlmm_pipeline.py`, which is where a batch that reached")
        print("the deploy path can still end in nothing. Counted as distinct tokens.\n")
        if per_class:
            print("| gate | distinct tokens refused |")
            print("|---|---|")
            for label, toks in sorted(per_class.items(), key=lambda kv: -len(kv[1])):
                print(f"| {label} | {len(toks)} |")
        if dead:
            print("\nBatches that reached the deploy path and deployed nothing:\n")
            for reason, n in dead.most_common():
                print(f"- {n}x — {reason}")

    # Live blocklist stock against its cap. This is the number that starves the
    # venue on a delay: a TTL bounds each entry's age, the cap bounds the set.
    print("")
    for pattern, cap_env, cap_default, label in (
        ("sol:dlmm:blocklist:dev:*", "DEV_BLOCKLIST_MAX", 12, "dev blocklist"),
        ("sol:dlmm:blocklist:mint:*", "MINT_BLACKLIST_MAX", 20, "rug mint blacklist"),
    ):
        try:
            out = subprocess.run(["redis-cli", "--scan", "--pattern", pattern],
                                 capture_output=True, text=True, timeout=20).stdout
            n = len([k for k in out.splitlines() if k.strip()])
            cap = int(os.environ.get(cap_env, cap_default))
            flag = " — **at cap**" if n >= cap else ""
            print(f"- {label} stock: **{n}** / cap {cap}{flag}")
        except Exception as exc:
            print(f"- {label} stock: unreadable ({exc}) — not evidence either way")
    print("\nA blocklist sitting at its cap is not proof of over-blocking, but it does")
    print("mean eviction — not expiry — is deciding what we may trade. Read it next to")
    print("the refusal table above before proposing any TTL or cap change.")


def section_soul():
    print("\n## Current parameters — SOUL.md section 9 (verbatim)\n")
    try:
        with open(SOUL_PATH, encoding="utf-8") as f:
            text = f.read()
    except OSError as exc:
        print(f"Unreadable ({exc}). Do not propose a change to a value you cannot see.")
        return
    start = text.find("## 9.")
    if start < 0:
        print("Section 9 not found. Do not propose a change to a value you cannot see.")
        return
    end = text.find("\n## ", start + 4)
    print("```")
    print(text[start:end if end > 0 else len(text)].rstrip())
    print("```")


def main():
    print(f"# DLMM proposal brief — {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())}")
    closes = load_closes()
    section_modes(closes)
    section_reasons(closes)
    section_weights()
    section_holds(closes)
    section_funnel()
    section_gates()
    section_soul()
    return 0


if __name__ == "__main__":
    sys.exit(main())
