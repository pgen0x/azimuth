package main

// Agent brief: a compact read of wallet, positions, closes, entry funnel, health and alerts for an
// orchestrating agent. Same collector as the dashboard, run in its `brief` mode; read only.

import (
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"log"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"sort"
	"strconv"
	"strings"
	"sync"
	"time"
)

const (
	briefCacheTTL = 20 * time.Second
	// The HTTP server's WriteTimeout is 10s; the brief must answer inside it.
	briefHTTPDeadline = 8 * time.Second
	briefCLIDeadline  = 60 * time.Second
)

type briefCache struct {
	mu      sync.Mutex // one collector run at a time; waiters reuse its result
	entries map[string]briefEntry
}

type briefEntry struct {
	at   time.Time
	data object
}

func runBrief(ctx context.Context, profile, state string, hours, n int, tz string, since int64) (object, error) {
	cmd := collectorCommand(ctx, profile, state, strconv.FormatInt(since, 10), tz, "brief", strconv.Itoa(hours), strconv.Itoa(n))
	output, err := cmd.Output()
	if err != nil {
		detail := ""
		if exit, ok := err.(*exec.ExitError); ok {
			lines := strings.Split(strings.TrimSpace(string(exit.Stderr)), "\n")
			if detail = lines[len(lines)-1]; len(detail) > 300 {
				detail = detail[:300]
			}
		}
		return nil, fmt.Errorf("brief collector failed: %v %s", err, detail)
	}
	var data object
	if err := json.Unmarshal(output, &data); err != nil {
		return nil, fmt.Errorf("brief collector output: %v", err)
	}
	return data, nil
}

// briefParams validates hours (1-168), n (1-50) and tz; empty values take the defaults.
func briefParams(hours, n, tz string) (int, int, string, error) {
	h, c := 12, 10
	var err error
	if hours != "" {
		if h, err = strconv.Atoi(hours); err != nil || h < 1 || h > 168 {
			return 0, 0, "", fmt.Errorf("invalid hours: use 1 to 168")
		}
	}
	if n != "" {
		if c, err = strconv.Atoi(n); err != nil || c < 1 || c > 50 {
			return 0, 0, "", fmt.Errorf("invalid n: use 1 to 50")
		}
	}
	zone := "UTC"
	if tz != "" {
		if zone = validZone(tz); zone == "" {
			return 0, 0, "", fmt.Errorf("invalid tz: use an IANA zone")
		}
	}
	return h, c, zone, nil
}

// funnelSince parses the entry-funnel score-band start: RFC3339 or unix seconds. Empty = 0, which the
// collector reads as its default start (FUNNEL_SINCE_DEFAULT).
func funnelSince(v string) (int64, error) {
	if v == "" {
		return 0, nil
	}
	if t, err := time.Parse(time.RFC3339, v); err == nil {
		return t.Unix(), nil
	}
	if n, err := strconv.ParseInt(v, 10, 64); err == nil && n >= 0 {
		return n, nil
	}
	return 0, fmt.Errorf("invalid funnel_since: use RFC3339 (2026-11-05T15:00:00Z) or unix seconds")
}

func (s *server) agentBrief(hours, n int, tz string, since int64) (object, error) {
	key := fmt.Sprintf("%d/%d/%s/%d", hours, n, tz, since)
	s.briefs.mu.Lock()
	defer s.briefs.mu.Unlock()
	if e, ok := s.briefs.entries[key]; ok && time.Since(e.at) < briefCacheTTL {
		return e.data, nil
	}
	ctx, cancel := context.WithTimeout(context.Background(), briefHTTPDeadline)
	defer cancel()
	run := s.runBrief
	if run == nil {
		run = runBrief
	}
	data, err := run(ctx, s.profile, s.state, hours, n, tz, since)
	if err != nil {
		return nil, err
	}
	if s.briefs.entries == nil || len(s.briefs.entries) > 16 {
		s.briefs.entries = map[string]briefEntry{}
	}
	s.briefs.entries[key] = briefEntry{time.Now(), data}
	return data, nil
}

// briefMain is the `azimuth-dashboard brief` subcommand: no HTTP, no auth, no Redis.
func briefMain(args []string, stdout, stderr io.Writer) int {
	home, _ := os.UserHomeDir()
	fs := flag.NewFlagSet("brief", flag.ContinueOnError)
	fs.SetOutput(stderr)
	asJSON := fs.Bool("json", false, "print the brief as JSON")
	hours := fs.Int("hours", 12, "entry-funnel and close window in hours (1-168)")
	n := fs.Int("n", 10, "number of recent closes (1-50)")
	tz := fs.String("tz", "UTC", "IANA zone for wallet day buckets")
	profile := fs.String("profile", filepath.Join(home, ".hermes/profiles/dlmm"), "Hermes profile directory")
	state := fs.String("state", filepath.Join(home, ".local/state/azimuth"), "persisted state directory")
	sinceFlag := fs.String("funnel-since", "", "start of the entry-funnel score bands, RFC3339 or unix seconds (default 2026-11-05T15:00:00Z)")
	if err := fs.Parse(args); err != nil {
		return 2
	}
	since, err := funnelSince(*sinceFlag)
	if err != nil {
		fmt.Fprintln(stderr, err)
		return 2
	}
	h, c, zone, err := briefParams(strconv.Itoa(*hours), strconv.Itoa(*n), *tz)
	if err != nil {
		fmt.Fprintln(stderr, err)
		return 2
	}
	if info, err := os.Stat(*profile); err != nil || !info.IsDir() {
		fmt.Fprintf(stderr, "profile directory %s not found; pass --profile <dir>\n", *profile)
		return 2
	}
	ctx, cancel := context.WithTimeout(context.Background(), briefCLIDeadline)
	defer cancel()
	data, err := runBrief(ctx, *profile, *state, h, c, zone, since)
	if err != nil {
		fmt.Fprintln(stderr, err)
		return 1
	}
	if *asJSON {
		json.NewEncoder(stdout).Encode(data)
	} else {
		io.WriteString(stdout, briefText(data))
	}
	return 0
}

// --- text rendering: fixed sections, at most ~60 lines ---

func obj(v any) object {
	m, _ := v.(map[string]any)
	return m
}

func list(v any) []any {
	l, _ := v.([]any)
	return l
}

func numOK(v any) (float64, bool) {
	f, ok := v.(float64)
	return f, ok
}

// sol prints a SOL figure, or "n/a" when unmeasured (never 0).
func sol(v any, signed bool) string { return solN(v, signed, 4) }

func solN(v any, signed bool, digits int) string {
	f, ok := numOK(v)
	if !ok {
		return "n/a"
	}
	if signed {
		return fmt.Sprintf("%+.*f", digits, f)
	}
	return fmt.Sprintf("%.*f", digits, f)
}

func str(v any) string {
	if v == nil {
		return "?"
	}
	if f, ok := v.(float64); ok {
		return strconv.FormatFloat(f, 'f', -1, 64)
	}
	return fmt.Sprint(v)
}

func stamp(v any) string {
	f, ok := numOK(v)
	if !ok || f <= 0 {
		return "?"
	}
	return time.Unix(int64(f), 0).UTC().Format("01-02 15:04Z")
}

func ago(now, v any) string {
	a, ok1 := numOK(now)
	b, ok2 := numOK(v)
	if !ok1 || !ok2 || b <= 0 {
		return "?"
	}
	d := a - b
	switch {
	case d < 120:
		return fmt.Sprintf("%.0fs ago", d)
	case d < 7200:
		return fmt.Sprintf("%.0fm ago", d/60)
	default:
		return fmt.Sprintf("%.1fh ago", d/3600)
	}
}

// counts renders a histogram as "k n, k n" sorted by count, at most limit entries.
func counts(v any, limit int) string {
	m := obj(v)
	if len(m) == 0 {
		return "none"
	}
	type kv struct {
		k string
		n float64
	}
	items := make([]kv, 0, len(m))
	for k, x := range m {
		f, _ := numOK(x)
		items = append(items, kv{k, f})
	}
	sort.Slice(items, func(i, j int) bool {
		if items[i].n != items[j].n {
			return items[i].n > items[j].n
		}
		return items[i].k < items[j].k
	})
	parts := []string{}
	for i, it := range items {
		if i == limit {
			parts = append(parts, fmt.Sprintf("+%d more", len(items)-limit))
			break
		}
		parts = append(parts, fmt.Sprintf("%s %.0f", it.k, it.n))
	}
	return strings.Join(parts, ", ")
}

func clip(s string, n int) string {
	r := []rune(s)
	if len(r) <= n {
		return s
	}
	return string(r[:n-1]) + "…"
}

// realizedCells renders {group: {n, measured, sum_sol, mean_sol}} as "group n=.. sum .. mean ..", largest n first.
func realizedCells(v any) string {
	m := obj(v)
	if len(m) == 0 {
		return "none"
	}
	keys := make([]string, 0, len(m))
	for k := range m {
		keys = append(keys, k)
	}
	sort.Slice(keys, func(i, j int) bool {
		a, _ := numOK(obj(m[keys[i]])["n"])
		c, _ := numOK(obj(m[keys[j]])["n"])
		if a != c {
			return a > c
		}
		return keys[i] < keys[j]
	})
	parts := []string{}
	for _, k := range keys {
		c := obj(m[k])
		cell := fmt.Sprintf("%s n=%s sum %s mean %s", k, str(c["n"]), solN(c["sum_sol"], true, 6), solN(c["mean_sol"], true, 6))
		if c["measured"] != c["n"] {
			cell += fmt.Sprintf(" (%s measured)", str(c["measured"]))
		}
		parts = append(parts, cell)
	}
	return strings.Join(parts, " · ")
}

func sectionError(b *strings.Builder, m object) bool {
	if e, ok := m["collection_error"].(string); ok {
		fmt.Fprintf(b, "  unavailable: %s\n", e)
		return true
	}
	return false
}

// growthParts names the today-split components in brief order; a missing one prints "unmeasured".
var growthParts = []struct{ key, name string }{
	{"realized_lp", "realized LP"}, {"rent_reclaimed", "rent"}, {"network_fees", "fees"}, {"external", "external"}, {"other", "other"},
}

func briefGrowth(b *strings.Builder, g object) {
	// One line: the TODAY section above already names the day and zone.
	if e, ok := g["collection_error"].(string); ok {
		fmt.Fprintf(b, "GROWTH unavailable: %s\n", e)
		return
	}
	if g["components"] == nil {
		fmt.Fprintf(b, "GROWTH Δnative %s SOL · %s\n", sol(g["d_native_sol"], true), str(g["status"]))
		return
	}
	byKey := map[string]object{}
	for _, x := range list(g["components"]) {
		byKey[str(obj(x)["component"])] = obj(x)
	}
	parts := []string{}
	for _, p := range growthParts {
		c, v := byKey[p.key], "unmeasured"
		if c != nil && c["sol"] != nil {
			v = solN(c["sol"], true, 6)
		}
		if n, _ := numOK(c["pending"]); n > 0 && p.key == "realized_lp" {
			v += fmt.Sprintf(" (%s/%s closes not reconciled, so far %s)", str(c["pending"]), str(c["closes"]), solN(c["measured_subtotal_sol"], true, 6))
		} else if n > 0 && c["sol"] == nil {
			v += fmt.Sprintf(" (%s pending, verified so far %s)", str(c["pending"]), solN(c["measured_subtotal_sol"], true, 6))
		}
		parts = append(parts, p.name+" "+v)
	}
	fmt.Fprintf(b, "GROWTH Δnative %s SOL · %s · %s\n", sol(g["d_native_sol"], true), strings.Join(parts, " · "), str(g["status"]))
}

// briefExperiments is one line: counts only, each study's own report decides.
func briefExperiments(b *strings.Builder, e object) {
	if e["collection_error"] != nil {
		fmt.Fprintf(b, "EXPERIMENTS unavailable: %s\n", str(e["collection_error"]))
		return
	}
	g, hc, ra := obj(e["geometry_shadow"]), obj(e["hold_canary"]), obj(e["active_bin_reanchor"])
	rep, arms := obj(g["report"]), obj(hc["arms"])
	verdict := str(rep["verdict"])
	if rep["status"] != "ok" {
		verdict = "report " + str(rep["status"])
	}
	fmt.Fprintf(b, "EXPERIMENTS geometry shadow %s entries/%s paired/%s treated %s · hold canary A %s B %s · re-anchor %s/%s entries\n",
		str(g["entries"]), str(rep["closed"]), str(rep["treated"]), verdict, str(arms["A"]), str(arms["B"]), str(ra["reanchored"]), str(ra["entries"]))
}

func briefText(d object) string {
	var b strings.Builder
	now := d["collected_at"]
	fmt.Fprintf(&b, "azimuth brief · %s · window %sh · read-only\n", stamp(now), str(d["hours"]))

	alerts := list(d["alerts"])
	if len(alerts) == 0 {
		b.WriteString("ALERTS none\n")
	} else {
		fmt.Fprintf(&b, "ALERTS %d\n", len(alerts))
		for i, a := range alerts {
			if i == 8 {
				fmt.Fprintf(&b, "  +%d more (see --json)\n", len(alerts)-8)
				break
			}
			fmt.Fprintf(&b, "  ! %s: %s\n", str(obj(a)["code"]), clip(str(obj(a)["message"]), 100))
		}
	}

	w := obj(d["wallet"])
	fmt.Fprintf(&b, "WALLET native %s · cash %s · known %s · rent %s SOL · as of %s · %s\n", sol(w["native_sol"], false), sol(w["cash_sol"], false), sol(w["known_sol"], false), sol(w["refundable_rent_sol"], false), ago(now, w["as_of"]), str(w["status"]))
	if !sectionError(&b, w) {
		fmt.Fprintf(&b, "  Δknown sum %s SOL over %s measured days (days in %s; external flows not netted)\n", sol(w["d_known_measured_sum_sol"], true), str(w["d_known_measured_days"]), str(w["tz"]))
		b.WriteString("  day          native     cash    Δcash    known   Δknown\n")
		for _, x := range list(w["days"]) {
			r := obj(x)
			if r["native_sol"] == nil {
				fmt.Fprintf(&b, "  %-10s  %s\n", str(r["day"]), str(r["status"]))
				continue
			}
			mark := ""
			if r["status"] == "partial_day" {
				mark = " (so far)"
			}
			fmt.Fprintf(&b, "  %-10s %7s %8s %8s %8s %8s%s\n", str(r["day"]), sol(r["native_sol"], false), sol(r["cash_sol"], false), sol(r["d_cash_sol"], true), sol(r["known_sol"], false), sol(r["d_known_sol"], true), mark)
		}
	}

	td := obj(d["today"])
	fmt.Fprintf(&b, "TODAY %s %s · native Δ %s SOL vs prior day · rent reclaimed %s SOL (%s tx, net of fees %s) · Δ ex-rent %s · rent %s\n",
		str(td["day"]), str(td["tz"]), sol(td["native_delta_sol"], true), sol(td["rent_reclaimed_sol"], true), str(td["rent_tx"]),
		sol(td["rent_native_gain_sol"], true), sol(td["native_delta_ex_rent_sol"], true), str(td["rent_status"]))
	if !sectionError(&b, td) && td["rent_reclaimed_sol"] == nil && td["rent_verified_subtotal_sol"] != nil {
		fmt.Fprintf(&b, "  rent total unverified; verified subtotal %s SOL over %s of %s tx (not a total)\n",
			sol(td["rent_verified_subtotal_sol"], true), str(td["rent_verified_tx"]), str(td["rent_tx"]))
	}

	rz := obj(d["realized_7d"])
	fmt.Fprintf(&b, "REALIZED %sd (arbiter) · %s\n", str(rz["days"]), str(rz["status"]))
	if !sectionError(&b, rz) {
		for _, group := range []string{"by_mode", "by_route"} {
			fmt.Fprintf(&b, "  %-6s %s\n", strings.TrimPrefix(group, "by_"), realizedCells(rz[group]))
		}
	}
	briefGrowth(&b, obj(d["growth"]))
	briefExperiments(&b, obj(d["experiments"]))

	p := obj(d["positions"])
	pos := list(p["positions"])
	fmt.Fprintf(&b, "OPEN %d · pnl is a MARK · monitor report %s · %s\n", len(pos), ago(now, p["report_at"]), str(p["status"]))
	if !sectionError(&b, p) {
		for i, x := range pos {
			if i == 8 {
				fmt.Fprintf(&b, "  +%d more\n", len(pos)-8)
				break
			}
			r := obj(x)
			rng := "OOR " + str(r["oor_minutes"]) + "m"
			if r["in_range"] == true {
				rng = "in-range"
			}
			pct, _ := numOK(r["pnl_pct"])
			fmt.Fprintf(&b, "  %-14s %-8s age %sm  mark %+.2f%% (%s SOL)  %s  size %s\n", clip(str(r["pair"]), 14), str(r["mode"]), str(r["age_minutes"]), pct, sol(r["pnl_sol"], true), rng, str(r["size_sol"]))
		}
	}

	c := obj(d["closes"])
	recent := list(c["recent"])
	fmt.Fprintf(&b, "CLOSES last %d · window: %s closes, %s measured, realized %s SOL\n", len(recent), str(c["window_closes"]), str(c["window_measured"]), solN(c["window_realized_sol"], true, 6))
	if !sectionError(&b, c) {
		for _, x := range recent {
			r := obj(x)
			fmt.Fprintf(&b, "  %s %-14s %-8s %5sm %10s %-14s %s\n", stamp(r["ts"]), clip(str(r["pair"]), 14), str(r["mode"]), str(r["hold_min"]), solN(r["realized_sol"], true, 6), str(r["pnl_basis"]), clip(str(r["reason"]), 48))
		}
	}

	f := obj(d["funnel"])
	dd := obj(f["direct_deploy"])
	fmt.Fprintf(&b, "FUNNEL %sh · batches %s (%s pools) · deploys %s (last %s) · direct deployed %s / not %s · %s\n", str(f["hours"]), str(f["batches"]), str(f["batch_pools"]), str(f["deploys"]), ago(now, f["last_deploy_ts"]), str(dd["deployed"]), str(dd["not_deployed"]), str(f["status"]))
	if !sectionError(&b, f) {
		fmt.Fprintf(&b, "  routes: %s\n", counts(f["routes"], 6))
		fmt.Fprintf(&b, "  daemon rejects: %s\n", counts(f["daemon_rejects"], 6))
		fmt.Fprintf(&b, "  pipeline rejects: %s\n", counts(f["pipeline_rejects"], 8))
	}

	briefEntryFunnel(&b, obj(d["entry_funnel"]))

	h := obj(d["health"])
	fmt.Fprintf(&b, "HEALTH disk free %s%% · MemAvailable %s MB · monitor tick %ss ago · failed units %d\n", str(h["disk_free_pct"]), str(h["mem_available_mb"]), str(h["monitor_tick_age_s"]), len(list(h["failed_units"])))
	if !sectionError(&b, h) {
		units := []string{}
		for _, x := range list(h["units"]) {
			u := obj(x)
			units = append(units, fmt.Sprintf("%s=%s/%s", strings.TrimSuffix(str(u["unit"]), ".service"), str(u["active"]), str(u["enabled"])))
		}
		fmt.Fprintf(&b, "  %s\n", strings.Join(units, " "))
	}
	return b.String()
}

// serveBrief answers /api/agent/brief (auth checked by ServeHTTP). format=text returns the CLI's text.
func (s *server) serveBrief(w http.ResponseWriter, r *http.Request) {
	q := r.URL.Query()
	hours, n, tz, err := briefParams(q.Get("hours"), q.Get("n"), q.Get("tz"))
	if err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}
	since, err := funnelSince(q.Get("funnel_since"))
	if err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}
	data, err := s.agentBrief(hours, n, tz, since)
	if err != nil {
		log.Print(err)
		w.Header().Set("Content-Type", "application/json")
		w.WriteHeader(http.StatusServiceUnavailable)
		w.Write([]byte(`{"error":"brief collection failed"}` + "\n"))
		return
	}
	if q.Get("format") == "text" {
		w.Header().Set("Content-Type", "text/plain; charset=utf-8")
		io.WriteString(w, briefText(data))
		return
	}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(data)
}

// briefEntryFunnel renders the entry_funnel section: two windows, the live ticket, score bands. Six lines.
func briefEntryFunnel(b *strings.Builder, f object) {
	fmt.Fprintf(b, "ENTRY FUNNEL · %s\n", str(f["status"]))
	if sectionError(b, f) {
		return
	}
	for _, x := range list(f["windows"]) {
		w := obj(x)
		r, dp := obj(w["routes"]), obj(w["deploys"])
		fb := str(r["deterministic_fallback"])
		if len(obj(w["fallback_reasons"])) > 0 {
			fb += " (" + counts(w["fallback_reasons"], 3) + ")"
		}
		fmt.Fprintf(b, "  %sh batches %s (%s pools) · route ai %s / fallback %s · deploys %s: verified %s, unverified %s, unknown %s\n",
			str(w["hours"]), str(w["batches"]), str(w["batch_pools"]), str(r["hermes_ai"]), fb,
			str(dp["total"]), str(dp["verified"]), str(dp["unverified"]), str(dp["unknown"]))
		fmt.Fprintf(b, "    rejects: %s\n", counts(w["rejects"], 8))
	}
	t := obj(f["ticket"])
	modes := obj(t["min_score"])
	keys := make([]string, 0, len(modes))
	for k := range modes {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	cells := make([]string, 0, len(keys))
	for _, k := range keys {
		m := obj(modes[k])
		s := "none"
		if v, ok := numOK(m["min_score"]); ok {
			s = fmt.Sprintf(">=%.1f", v)
		}
		cells = append(cells, fmt.Sprintf("%s %s (floor %s)", k, s, str(m["floor"])))
	}
	fmt.Fprintf(b, "  ticket base %s SOL · minimum %s · clearing score %s · %s\n",
		sol(t["base_ticket_sol"], false), sol(t["minimum_entry_sol"], false), strings.Join(cells, ", "), str(t["status"]))
	sb := obj(f["score_bands"])
	bands := obj(sb["bands"])
	parts := []string{}
	for _, k := range []string{"<50", "50-70", ">=70", "unscored"} {
		c := obj(bands[k])
		parts = append(parts, fmt.Sprintf("%s n=%s realized %s (%s measured, %s pending)", k, str(c["n"]), solN(c["sum_sol"], true, 6), str(c["measured"]), str(c["pending"])))
	}
	fmt.Fprintf(b, "  score bands since %s: %s\n", stamp(sb["since"]), strings.Join(parts, " · "))
}
