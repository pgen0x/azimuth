package main

// Trace: one position's lifecycle, or every position and pipeline reject of a pool or symbol, from the
// same journals the dashboard reads. Same collector, run in its `trace` mode; read only.

import (
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"os"
	"os/exec"
	"path/filepath"
	"sort"
	"strconv"
	"strings"
	"time"
	"unicode"
)

const traceCLIDeadline = 90 * time.Second

func runTrace(ctx context.Context, profile, state, query string, days int) (object, error) {
	cmd := collectorCommand(ctx, profile, state, "0", "UTC", "trace", strconv.Itoa(days), query)
	output, err := cmd.Output()
	if err != nil {
		detail := ""
		if exit, ok := err.(*exec.ExitError); ok {
			lines := strings.Split(strings.TrimSpace(string(exit.Stderr)), "\n")
			if detail = lines[len(lines)-1]; len(detail) > 300 {
				detail = detail[:300]
			}
		}
		return nil, fmt.Errorf("trace collector failed: %v %s", err, detail)
	}
	var data object
	if err := json.Unmarshal(output, &data); err != nil {
		return nil, fmt.Errorf("trace collector output: %v", err)
	}
	return data, nil
}

// validQuery accepts a position or pool address, or a token symbol: 1-64 printable runes, no spaces.
func validQuery(q string) bool {
	if q == "" || len([]rune(q)) > 64 || strings.HasPrefix(q, "-") {
		return false
	}
	for _, r := range q {
		if unicode.IsSpace(r) || !unicode.IsPrint(r) {
			return false
		}
	}
	return true
}

// traceMain is the `azimuth-dashboard trace <position|pool|symbol>` subcommand: no HTTP, no auth, no Redis.
// The query may come before or after the flags. Exit 3 = nothing found.
func traceMain(args []string, stdout, stderr io.Writer) int {
	return traceMainWith(args, stdout, stderr, runTrace)
}

func traceMainWith(args []string, stdout, stderr io.Writer, run func(context.Context, string, string, string, int) (object, error)) int {
	home, _ := os.UserHomeDir()
	fs := flag.NewFlagSet("trace", flag.ContinueOnError)
	fs.SetOutput(stderr)
	fs.Usage = func() {
		fmt.Fprintln(stderr, "usage: azimuth-dashboard trace <position|pool|symbol> [-profile P] [-state S] [--json] [--days N]")
		fs.PrintDefaults()
	}
	asJSON := fs.Bool("json", false, "print the trace as JSON")
	days := fs.Int("days", 7, "window in days for pool/symbol listings (1-30)")
	profile := fs.String("profile", filepath.Join(home, ".hermes/profiles/dlmm"), "Hermes profile directory")
	state := fs.String("state", filepath.Join(home, ".local/state/azimuth"), "persisted state directory")
	// flag stops at the first positional; keep parsing after it so flags may sit on either side.
	positional := []string{}
	for {
		if err := fs.Parse(args); err != nil {
			return 2
		}
		if fs.NArg() == 0 {
			break
		}
		positional = append(positional, fs.Arg(0))
		args = fs.Args()[1:]
	}
	if len(positional) > 1 {
		fmt.Fprintf(stderr, "unexpected argument %q\n", positional[1])
		return 2
	}
	query := ""
	if len(positional) == 1 {
		query = positional[0]
	}
	if !validQuery(query) {
		fs.Usage()
		return 2
	}
	if *days < 1 || *days > 30 {
		fmt.Fprintln(stderr, "invalid days: use 1 to 30")
		return 2
	}
	if info, err := os.Stat(*profile); err != nil || !info.IsDir() {
		fmt.Fprintf(stderr, "profile directory %s not found; pass --profile <dir>\n", *profile)
		return 2
	}
	ctx, cancel := context.WithTimeout(context.Background(), traceCLIDeadline)
	defer cancel()
	data, err := run(ctx, *profile, *state, query, *days)
	if err != nil {
		fmt.Fprintln(stderr, err)
		return 1
	}
	if *asJSON {
		json.NewEncoder(stdout).Encode(data)
	} else {
		io.WriteString(stdout, traceText(data))
	}
	if data["status"] == "not_found" {
		return 3
	}
	return 0
}

// --- text rendering ---

func short(v any) string {
	s := str(v)
	if r := []rune(s); len(r) > 12 {
		return string(r[:4]) + "…" + string(r[len(r)-4:])
	}
	return s
}

func dur(v any) string {
	f, ok := numOK(v)
	if !ok {
		return "?"
	}
	if f < 120 {
		return fmt.Sprintf("%.0fm", f)
	}
	return fmt.Sprintf("%.1fh", f/60)
}

// scalars renders the non-nested fields of a row other than stage/time/source, sorted by name.
func scalars(e object) string {
	parts := []string{}
	for k, v := range e {
		if k == "stage" || k == "time" || k == "source" || k == "basis" {
			continue
		}
		switch v.(type) {
		case map[string]any, []any:
			continue
		}
		parts = append(parts, k+"="+str(v))
	}
	sort.Strings(parts)
	return strings.Join(parts, " ")
}

// traceEvent renders one timeline row's detail; unknown stages fall back to their scalar fields.
func traceEvent(e object) string {
	switch str(e["stage"]) {
	case "batch_sent":
		syms := []string{}
		for _, x := range list(e["pools"]) {
			p := obj(x)
			mark := ""
			if p["this"] == true {
				mark = "*"
			}
			syms = append(syms, fmt.Sprintf("%s%s(%s)", mark, str(p["symbol"]), solN(p["score"], false, 0)))
		}
		return fmt.Sprintf("webhook batch %s · %s candidate(s): %s", short(e["delivery_id"]), str(e["candidates"]), strings.Join(syms, " "))
	case "webhook_accepted":
		return "HTTP " + str(e["http_status"]) + " (acceptance only, not execution)"
	case "batch_logged", "cooldown_set":
		return clip(str(e["line"]), 110)
	case "route":
		if e["fallback_reason"] != nil {
			return str(e["route"]) + " reason=" + str(e["fallback_reason"])
		}
		return str(e["route"])
	case "direct_deploy":
		return "deployed=" + str(e["deployed"])
	case "hermes_decision":
		if e["text"] == nil {
			return "session " + str(e["status"])
		}
		return fmt.Sprintf("[%s] %s", str(e["status"]), clip(str(e["text"]), 300))
	case "pipeline_reject":
		return "gate " + str(e["gate"]) + " (" + str(e["mode"]) + ")"
	case "entry":
		return fmt.Sprintf("%s %s %s SOL · route %s · bin %s (-%s/+%s) · score %s · entry %s", str(e["mode"]), str(e["strategy"]), str(e["size_sol"]),
			str(e["route"]), str(e["entry_bin"]), str(e["bins_below"]), str(e["bins_above"]), solN(e["score"], false, 1), short(e["entry_id"]))
	case "monitor_ticks":
		if f, _ := numOK(e["ticks"]); f == 0 {
			return "no MONITOR_REPORT found (" + str(e["status"]) + ")"
		}
		return fmt.Sprintf("%s ticks to %s · MARK pnl %s%%..%s%% (%s..%s SOL) · OOR ticks %s · %s", str(e["ticks"]), stamp(e["last"]),
			solN(e["pnl_pct_min"], true, 2), solN(e["pnl_pct_max"], true, 2), solN(e["pnl_sol_min"], true, 6), solN(e["pnl_sol_max"], true, 6), str(e["oor_ticks"]), str(e["status"]))
	case "close":
		return fmt.Sprintf("%s · held %sm · MARK %s%% (%s) · ai_holds %s · txs %s", clip(str(e["reason"]), 90), str(e["age_min"]), solN(e["mark_pnl_pct"], true, 2),
			str(e["mark_basis"]), str(e["ai_holds"]), str(e["txs"]))
	case "settlement":
		return str(e["state"]) + " " + str(e["reason"])
	case "realized":
		return fmt.Sprintf("%s SOL (%s%%) · deposit %s · withdrawal %s · fees %s", solN(e["realized_sol"], true, 6), solN(e["realized_pct"], true, 2),
			solN(e["deposit_sol"], false, 6), solN(e["withdrawal_sol"], false, 6), solN(e["fee_sol"], false, 6))
	case "cooldown_blocked":
		return fmt.Sprintf("daemon skipped it %s× until %s · last: %s", str(e["count"]), stamp(e["last"]), clip(str(e["last_line"]), 80))
	}
	return clip(scalars(e), 160)
}

func traceText(d object) string {
	var b strings.Builder
	fmt.Fprintf(&b, "azimuth trace %s · %s · %s · window %sd · read-only\n", str(d["query"]), str(d["kind"]), str(d["status"]), str(d["days"]))
	if d["status"] == "not_found" {
		b.WriteString("  nothing found in closes, realized, entry files or pipeline rejects\n")
		return b.String()
	}
	if d["kind"] == "position" {
		s := obj(d["summary"])
		fmt.Fprintf(&b, "%s %s · pool %s · route %s · %s\n", str(s["pair"]), str(s["mode"]), str(s["pool"]), str(s["route"]), str(s["state"]))
		fmt.Fprintf(&b, "  deployed %s · closed %s · realized %s SOL (%s)\n", stamp(s["deployed_at"]), stamp(s["closed_at"]), solN(s["realized_sol"], true, 6), str(s["pnl_basis"]))
		for _, x := range list(d["events"]) {
			e := obj(x)
			fmt.Fprintf(&b, "  %s %-19s %s\n", stamp(e["time"]), str(e["stage"]), traceEvent(e))
		}
	} else {
		pos := list(d["positions"])
		fmt.Fprintf(&b, "POSITIONS %d · realized %s SOL over %s measured\n", len(pos), solN(d["realized_sum_sol"], true, 6), str(d["realized_measured"]))
		for _, x := range pos {
			p := obj(x)
			fmt.Fprintf(&b, "  %s %s %-8s %-13s %6s %10s %-14s %s\n", stamp(p["deployed_at"]), str(p["position"]), str(p["mode"]), str(p["route"]),
				dur(p["hold_min"]), solN(p["realized_sol"], true, 6), str(p["pnl_basis"]), clip(str(p["close_reason"]), 60))
		}
		fmt.Fprintf(&b, "PIPELINE REJECTS %s · %s\n", str(d["rejects_total"]), counts(d["reject_gates"], 8))
		rej := list(d["rejects"])
		if len(rej) > 10 {
			fmt.Fprintf(&b, "  (last 10 of %d shown; see --json)\n", len(rej))
			rej = rej[len(rej)-10:]
		}
		for _, x := range rej {
			r := obj(x)
			fmt.Fprintf(&b, "  %s %-24s %-8s %s\n", stamp(r["ts"]), str(r["gate"]), str(r["mode"]), short(r["pool"]))
		}
	}
	srcs := []string{}
	for k, v := range obj(d["sources"]) {
		if v != "ok" {
			srcs = append(srcs, k+"="+str(v))
		}
	}
	sort.Strings(srcs)
	if len(srcs) > 0 {
		fmt.Fprintf(&b, "SOURCES not ok: %s\n", strings.Join(srcs, " "))
	}
	b.WriteString("pnl in monitor/close rows is a MARK; realized_sol (dlmm_realized.jsonl) is the arbiter.\n")
	return b.String()
}
