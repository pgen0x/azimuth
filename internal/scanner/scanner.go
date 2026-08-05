package scanner

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"sort"
	"strings"
	"time"

	"github.com/pgen0x/azimuth/internal/config"
	"github.com/pgen0x/azimuth/internal/deploy"
	"github.com/pgen0x/azimuth/internal/meteora"
	"github.com/pgen0x/azimuth/internal/robinhood"
	"github.com/pgen0x/azimuth/internal/store"
	"github.com/pgen0x/azimuth/internal/webhook"
)

// batchSummary renders a compact "SYM(score)" list for one log line.
func batchSummary(batch []*meteora.Candidate) string {
	parts := make([]string, 0, len(batch))
	for _, c := range batch {
		parts = append(parts, fmt.Sprintf("%s(%.0f)", c.BaseSymbol, c.Score))
	}
	return strings.Join(parts, ", ")
}

// reasonKey collapses a Screen reject reason to its stable prefix (the text
// before the first number or colon) so per-pool reasons group into a tally.
// "fee/TVL 0.02% < 0.10%" -> "fee/TVL", "non-SOL pool" -> "non-SOL_pool".
func reasonKey(reason string) string {
	if i := strings.IndexAny(reason, "0123456789:"); i >= 0 {
		reason = reason[:i]
	}
	reason = strings.TrimRight(reason, " $<>=(%-")
	if reason == "" {
		return "other"
	}
	return strings.ReplaceAll(reason, " ", "_")
}

// rejectSummary renders a reject tally as "k=v k=v", highest count first.
func rejectSummary(rejects map[string]int) string {
	keys := make([]string, 0, len(rejects))
	for k := range rejects {
		keys = append(keys, k)
	}
	sort.Slice(keys, func(i, j int) bool {
		if rejects[keys[i]] != rejects[keys[j]] {
			return rejects[keys[i]] > rejects[keys[j]]
		}
		return keys[i] < keys[j]
	})
	parts := make([]string, 0, len(keys))
	for _, k := range keys {
		parts = append(parts, fmt.Sprintf("%s=%d", k, rejects[k]))
	}
	return strings.Join(parts, " ")
}

// Scanner polls the Meteora discovery API for each enabled mode, screens pools,
// dedups, and forwards newly-qualifying pools to the Hermes webhook.
type Scanner struct {
	cfg     config.Config
	seen    *store.Seen
	fwd     *webhook.Forwarder
	dep     *deploy.Runner
	rhDep   rhRunner // uni_executor.js (v3)
	rhDepV4 rhRunner // uni_v4_executor.js; disabled when unset
}

// rhRunner is the slice of *robinhood.Runner the deploy path uses, narrowed to an
// interface so a test can drive the ordering below with a fake instead of
// spawning the node executor and hitting a live wallet.
type rhRunner interface {
	Enabled() bool
	Inventory(ctx context.Context) (robinhood.Inventory, error)
	Balance(ctx context.Context) (robinhood.Balances, error)
	Deploy(ctx context.Context, pool string, amount, rangePct, slippagePct float64, strategy, quote string) (string, error)
}

// entryTiming is robinhood.EntryTimingConfirm behind a var: it is the one call in
// the deploy path that spends a GeckoTerminal request per candidate, so a test
// has to be able to COUNT it — how many of these a cycle makes is the whole
// point of the ordering in robinhoodDeploy.
var entryTiming = robinhood.EntryTimingConfirm

// New wires a Scanner from config.
func New(cfg config.Config) *Scanner {
	seen := store.New(cfg.RedisAddr, cfg.RedisSeenKey, cfg.SeenTTL)
	// Give the robinhood package's OHLCV cache a persistent half, so candles
	// survive a restart: the daemon restarted twice on 2026-08-05 and each restart
	// re-fetched every walked pool's candles from GeckoTerminal at once. With no
	// REDIS_ADDR configured, *store.Seen answers "not cached" to every read and
	// this is a no-op — no branch needed here.
	robinhood.SetCandleStore(seen)
	return &Scanner{
		cfg:     cfg,
		seen:    seen,
		fwd:     webhook.New(cfg.WebhookURL, cfg.WebhookSecret),
		dep:     deploy.New(cfg.DeployCmd, cfg.ReportCmd, cfg.DeployTimeout),
		rhDep:   robinhood.New(cfg.RobinhoodExecutorCmd, cfg.RobinhoodDeployTimeout),
		rhDepV4: robinhood.New(cfg.RobinhoodV4ExecutorCmd, cfg.RobinhoodDeployTimeout),
	}
}

// modes returns the enabled screening modes.
func (s *Scanner) modes() []meteora.ModeParams {
	var out []meteora.ModeParams
	if s.cfg.EnableCasual {
		out = append(out, meteora.Casual)
	}
	if s.cfg.EnableMultiday {
		out = append(out, meteora.Multiday)
	}
	if s.cfg.EnableTurnover {
		out = append(out, meteora.Turnover)
	}
	// Pulse samples the same universe through a different window (5m
	// trending vs turnover's 30m fee-sorted full universe), so the two modes
	// surface largely disjoint pools — running both is the point.
	if s.cfg.EnablePulse {
		out = append(out, meteora.Pulse)
	}
	return out
}

// Run blocks, polling on PollInterval until ctx is cancelled.
func (s *Scanner) Run(ctx context.Context) {
	// The robinhood deploy fields are logged too, not just the mode toggles:
	// .env is the only place they can be set and it is unreadable by design
	// (guard-secrets.sh), so this line is the operator's ONLY way to confirm a
	// config edit actually took effect. A silently-wrong strategy here spends
	// real money on the wrong shape.
	log.Printf("scanner: started (interval=%v, casual=%v, multiday=%v, turnover=%v, pulse=%v, momentum=%v, robinhood=%v, rh-mature=%v, rh-ladder=%v, rh-usdg-ladder=%v)",
		s.cfg.PollInterval, s.cfg.EnableCasual, s.cfg.EnableMultiday, s.cfg.EnableTurnover, s.cfg.EnablePulse,
		s.cfg.EnableMomentumGate, s.cfg.EnableRobinhood, s.cfg.EnableRobinhoodMature, s.cfg.EnableRobinhoodLadder,
		s.cfg.EnableRobinhoodStockLadder)
	if s.cfg.EnableRobinhood || s.cfg.EnableRobinhoodMature || s.cfg.EnableRobinhoodLadder || s.cfg.EnableRobinhoodStockLadder {
		modes := make([]string, 0, len(s.cfg.RobinhoodDeployModes))
		for m := range s.cfg.RobinhoodDeployModes {
			modes = append(modes, m)
		}
		sort.Strings(modes) // map order is random; a config line must be stable
		log.Printf("scanner: robinhood deploy (enabled=%v, executor=%v, v4executor=%v, strategy=%s, modes=%s, max_open=%d, indicator_gate=%v)",
			s.cfg.RobinhoodDeployEnabled, s.rhDep.Enabled(), s.rhDepV4.Enabled(),
			s.cfg.RobinhoodDeployStrategy, strings.Join(modes, ","),
			s.cfg.RobinhoodMaxOpenPositions, s.cfg.RobinhoodIndicatorGate)
	}

	ticker := time.NewTicker(s.cfg.PollInterval)
	defer ticker.Stop()

	s.pollAll(ctx)
	for {
		select {
		case <-ticker.C:
			s.pollAll(ctx)
		case <-ctx.Done():
			log.Println("scanner: stopped")
			return
		}
	}
}

func (s *Scanner) pollAll(ctx context.Context) {
	for _, mp := range s.modes() {
		s.pollMode(ctx, mp)
	}
	if s.cfg.EnableRobinhood {
		// Each mode brings its own discovery source: the two theses sit on
		// opposite sides of a 24h age line and NO single feed spans both.
		// GeckoTerminal's new_pools is a launch feed (a pool scrolls off it in
		// minutes); Uniswap's gateway is a TVL leaderboard that indexes nothing
		// younger than a day. See mature.go.
		s.pollRobinhood(ctx, robinhood.Fresh, func(now time.Time) ([]robinhood.Pool, error) {
			return robinhood.FetchNewPools(s.cfg.RobinhoodDiscoverURL, now)
		})
	}
	if s.cfg.EnableRobinhoodMature {
		s.pollRobinhood(ctx, robinhood.Mature, func(now time.Time) ([]robinhood.Pool, error) {
			return robinhood.FetchMaturePools(robinhood.Mature, now)
		})
	}
	if s.cfg.EnableRobinhoodLadder {
		// TWO sources unioned (FetchLadderPools): the same gateway feed as
		// rh-mature — prefiltered with the LADDER params, since FetchMaturePools
		// takes the mode so its local prefilter matches the gates that will
		// actually run, which is what keeps the GeckoTerminal enrich to one
		// request — plus the CACHED GeckoTerminal trending page, which carries
		// v3 pools the gateway does not index at all (LEMON.FUN/WETH, measured
		// 2026-08-05). The trending page costs no extra request while rh-fresh
		// is enabled; see trending.go.
		//
		// Running rh-ladder alongside rh-mature makes entries the union of a
		// yield screen and a churn screen; the dedup store keys per pool per
		// mode, so a pool both modes like signals once each and then goes quiet
		// for its SEEN_TTL.
		s.pollRobinhood(ctx, robinhood.Ladder, func(now time.Time) ([]robinhood.Pool, error) {
			return robinhood.FetchLadderPools(robinhood.Ladder, now)
		})
	}
	if s.cfg.EnableRobinhoodStockLadder {
		// The same gateway feed a third time, prefiltered with the USDG-pinned
		// params. It costs an extra pair of gateway calls per cycle and cannot
		// share rh-ladder's: the prefilter is what keeps the GeckoTerminal
		// enrich to ONE request, and it can only be tuned to one mode's gates.
		// The two ladders never contest a pool — one takes WETH-quoted pools,
		// the other USDG-quoted, and the quote pin is checked in both the
		// prefilter and Screen.
		s.pollRobinhood(ctx, robinhood.StockLadder, func(now time.Time) ([]robinhood.Pool, error) {
			return robinhood.FetchMaturePools(robinhood.StockLadder, now)
		})
	}
}

// rhBatchSummary renders a compact "SYM(score)" list for one log line.
func rhBatchSummary(batch []*robinhood.Candidate) string {
	parts := make([]string, 0, len(batch))
	for _, c := range batch {
		parts = append(parts, fmt.Sprintf("%s(%.0f)", c.BaseSymbol, c.Score))
	}
	return strings.Join(parts, ", ")
}

// pollRobinhood runs one discovery cycle for the Robinhood Chain venue
// (Phase 1, signal-only — see docs/ROBINHOOD_CHAIN_PLAN.md). Batches go to
// the webhook sink ONLY: the direct-deploy pipeline speaks Solana and must
// never receive an EVM candidate until the Phase 2 executor lands.
// robinhoodDeploy picks the batch's single highest-scoring candidate and
// mints it via uni_executor.js. There is no re-ranking pipeline like
// dlmm_pipeline.py here — screen.go already scores every candidate, so the
// pick is a plain argmax. Fails closed on any OpenPositions read error: with
// no monitor yet to close stale positions, an unknown count must never be
// treated as "room to deploy".
// pickOrder returns candidates in pick preference: clean candidates by score
// descending, then copycats by score descending — the ranking pickBest used
// to argmax over, kept as a full order so the entry-timing gate can fall
// through to the next-best candidate instead of forfeiting the cycle
// (mirroring dlmm_pipeline.py's batch pick loop).
func pickOrder(batch []*robinhood.Candidate) []*robinhood.Candidate {
	out := append([]*robinhood.Candidate(nil), batch...)
	sort.SliceStable(out, func(i, j int) bool {
		if out[i].IsCopycat != out[j].IsCopycat {
			return !out[i].IsCopycat
		}
		return out[i].Score > out[j].Score
	})
	return out
}

// protoKey is the cache key for anything read once per EXECUTOR rather than once
// per candidate — the wallet balance, today. v4 poolIds mint through
// uni_v4_executor.js and everything else through uni_executor.js, and the two
// executors can hold different wallets, so a v3 and a v4 candidate in one batch
// must not share a balance.
func protoKey(c *robinhood.Candidate) string {
	if c.Protocol == "v4" {
		return "v4"
	}
	return "v3"
}

// runnerFor picks the executor that can mint this candidate. Same rule as
// protoKey, and it must stay that way: a balance cached under one key has to have
// come from the runner that later spends it.
func (s *Scanner) runnerFor(c *robinhood.Candidate) rhRunner {
	if c.Protocol == "v4" {
		return s.rhDepV4
	}
	return s.rhDep
}

// deploySize is one candidate's sizing answer, computed before the entry-timing
// walk so an unfundable batch costs zero GeckoTerminal requests. A non-empty skip
// means "do not deploy this one" and carries the operator-facing reason; the
// remaining fields are only meaningful when skip is empty, except that the log
// line for the winning pick reads them all.
type deploySize struct {
	skip     string // non-empty: reason this candidate cannot be funded
	amount   float64
	unit     string // "WETH" or "USDG" — the quote asset amount is denominated in
	quote    string // quote token address handed to the executor
	strategy string
	sizeCfg  robinhood.SizeParams
	sizeBal  float64
}

// sizeFor sizes one candidate from the LIVE wallet, not a fixed constant — same
// rationale as the Solana pipeline's compute_deploy_amount. The caller has
// already failed closed on an unreadable balance: guessing a size is how you
// overspend or mint dust.
func (s *Scanner) sizeFor(c *robinhood.Candidate, bal robinhood.Balances) deploySize {
	// Gas is native ETH here, not the assets we LP with — a WETH/USDG-rich
	// wallet can still be too broke to pay for the mint.
	if bal.ETH < s.cfg.RobinhoodMinGasEth {
		return deploySize{skip: fmt.Sprintf("gas %.6f ETH < %.6f floor — fund the wallet",
			bal.ETH, s.cfg.RobinhoodMinGasEth)}
	}
	// Size in the candidate's quote asset. USDG pools size off the USDG
	// balance with the dollar-unit params; WETH and native-ETH pools size off
	// WETH (the executor unwraps on demand for native settles). The quote
	// address goes to BOTH executors now — v4 needs it to know which side of
	// the PoolKey to settle in, and v3 needs it since the usdg_ladder landed
	// (uni_executor.js resolves the pool's quote side from it, defaulting to
	// WETH when the flag is absent).
	sz := deploySize{
		sizeCfg: s.cfg.RobinhoodSize,
		sizeBal: bal.WETH,
		unit:    "WETH",
		quote:   c.QuoteAddress,
	}
	if strings.EqualFold(sz.quote, robinhood.USDG) {
		sz.sizeCfg, sz.sizeBal, sz.unit = s.cfg.RobinhoodSizeUSDG, bal.USDG, "USDG"
	}
	// The ladder shape is quote-agnostic but its NAME is not: the journal, the
	// close report and uni_monitor.py's re-pin rulebook all read the strategy
	// string, and a USDG ladder logged as "weth_ladder" would be unreadable in
	// a close journal that mixes both. Same executor path either way.
	sz.strategy = s.cfg.RobinhoodDeployStrategy
	if sz.strategy == "weth_ladder" && sz.unit == "USDG" {
		sz.strategy = "usdg_ladder"
	}
	sz.amount = robinhood.ComputeDeployAmount(sz.sizeBal, sz.sizeCfg)
	if sz.amount <= 0 {
		sz.skip = fmt.Sprintf("%.5f %s balance cannot fund a %.5f floor position (reserve %.5f)",
			sz.sizeBal, sz.unit, sz.sizeCfg.Floor, sz.sizeCfg.Reserve)
	}
	return sz
}

func (s *Scanner) robinhoodDeploy(ctx context.Context, mode string, batch []*robinhood.Candidate) {
	// Keep only candidates an enabled executor can actually mint: v3 pools
	// need uni_executor.js, v4 poolIds need uni_v4_executor.js (Phase 7).
	// With no v4 executor configured, v4 candidates stay observe-only —
	// exactly the pre-Phase-7 behavior.
	eligible := batch[:0:0]
	for _, c := range batch {
		if c.Protocol == "v4" && s.rhDepV4.Enabled() || c.Protocol != "v4" && s.rhDep.Enabled() {
			eligible = append(eligible, c)
		}
	}
	if len(eligible) < len(batch) {
		log.Printf("scanner[%s]: %d candidate(s) excluded from deploy (no executor for their protocol)", mode, len(batch)-len(eligible))
	}
	if len(eligible) == 0 {
		return
	}

	// Walk candidates in score order (copycats demoted: a same-symbol collision
	// means we can't tell the real token from the imposter, so LPing one is a
	// coin flip on holding the loser). The supertrend_or_rsi entry-timing gate
	// vetoes candidates whose token is in a confirmed downtrend — the FOX
	// lesson: rh-mature's fee/TVL selection loves pools whose yield is paid by
	// a collapsing price, and the raw h1 screen gate (-15%) sits looser than
	// the monitor's downtrend exit (-5%), so an unchecked pick can be one tick
	// from its own close. Data-unavailable fails open, per the gate convention.
	// The position census comes BEFORE the pick, not after it, because the
	// per-token cap must be able to skip a blocked candidate and fall through to
	// the next-best one. Both caps read this one census. It spans BOTH executors
	// — v3 NPM positions and v4 posm positions draw on the same wallet, so the
	// brake is per-wallet, not per-protocol — and fails closed if any enabled
	// executor cannot be counted.
	open := 0
	held := map[string]int{}
	for _, r := range []rhRunner{s.rhDep, s.rhDepV4} {
		if !r.Enabled() {
			continue
		}
		inv, err := r.Inventory(ctx)
		if err != nil {
			log.Printf("scanner[%s]: DEPLOY SKIPPED (position count unknown, failing closed): %v", mode, err)
			return
		}
		open += inv.Ladders
		for t, n := range inv.ByToken {
			held[t] += n
		}
	}
	if open >= s.cfg.RobinhoodMaxOpenPositions {
		log.Printf("scanner[%s]: DEPLOY SKIPPED %s (%s): at position cap %d/%d",
			mode, eligible[0].BaseSymbol, eligible[0].Pool[:10], open, s.cfg.RobinhoodMaxOpenPositions)
		return
	}

	order := pickOrder(eligible)

	// Sizing comes BEFORE the candidate walk, and the reason is GeckoTerminal
	// budget rather than tidiness. Every walked candidate can cost one OHLCV
	// request (the entry-timing gate below), and GT's public tier is ~10
	// requests/minute for the whole box — measured 2026-08-05, when rh-usdg-ladder
	// logged 82 `status 429` in six hours and ~23% of its cycles discovered nothing
	// because the mature enrich call fails closed without a slot. What the wallet
	// holds never depended on which candidate won, so a mode whose quote asset is
	// unfunded used to spend a request per candidate to reach a skip that was
	// already certain — every cycle, forever, since nothing about an empty wallet
	// changes on its own. Reading it first makes that cycle cost zero requests.
	//
	// Balance is per EXECUTOR while the executor is per candidate (v3 pools mint
	// through uni_executor.js, v4 poolIds through uni_v4_executor.js), so balances
	// are read once per protocol present in the batch and cached; the pick still
	// deploys through its own runner further down. This moves WHEN the wallet is
	// read, never which executor mints.
	bals := map[string]robinhood.Balances{}
	for _, c := range order {
		key := protoKey(c)
		if _, ok := bals[key]; ok {
			continue
		}
		bal, err := s.runnerFor(c).Balance(ctx)
		if err != nil {
			log.Printf("scanner[%s]: DEPLOY SKIPPED (balance unknown, failing closed): %v", mode, err)
			return
		}
		bals[key] = bal
	}
	sizes := make(map[string]deploySize, len(order))
	fundable := 0
	for _, c := range order {
		sz := s.sizeFor(c, bals[protoKey(c)])
		sizes[c.Pool] = sz
		if sz.skip == "" {
			fundable++
		}
	}
	if fundable == 0 {
		// Nothing here is affordable, and no entry-timing request was spent to learn
		// it. The line names the top-ranked candidate because a mode pins ONE quote
		// asset (ModeParams.QuoteAsset), so the reason is identical for every
		// candidate in the batch and this is the one the old post-pick check would
		// have reported.
		c := order[0]
		log.Printf("scanner[%s]: DEPLOY SKIPPED %s (%s): %s", mode, c.BaseSymbol, c.Pool[:10], sizes[c.Pool].skip)
		return
	}

	var best *robinhood.Candidate
	for _, c := range order {
		// Per-token cap. The same underlying lists in several pools here — three
		// fee tiers is normal for an equity, and v4 multiplies that by tick
		// spacing — so without this one token can hold every slot: three walls
		// under one price, filling together, which is the concentration the slot
		// budget exists to prevent.
		if n := s.cfg.RobinhoodMaxPerToken; n > 0 {
			if h := held[strings.ToLower(c.BaseAddress)]; h >= n {
				log.Printf("scanner[%s]: %s (%s) skipped: wallet already holds %d/%d wall(s) of this token",
					mode, c.BaseSymbol, c.Pool[:10], h, n)
				continue
			}
		}
		if sz := sizes[c.Pool]; sz.skip != "" {
			// Only reachable when one batch mixes protocols whose executors report
			// different assets (the v4 build reports USDG; an older v3 build may
			// not) — with one fundability answer for the batch the pre-walk check
			// above has already returned. Skipping the candidate rather than the
			// cycle keeps an affordable sibling deployable, and costs no request.
			log.Printf("scanner[%s]: %s (%s) skipped: %s", mode, c.BaseSymbol, c.Pool[:10], sz.skip)
			continue
		}
		if s.cfg.RobinhoodIndicatorGate {
			if confirmed, detail, ok := entryTiming(c.Pool); ok && !confirmed {
				log.Printf("scanner[%s]: %s (%s) rejected on entry timing: %s",
					mode, c.BaseSymbol, c.Pool[:10], detail)
				continue
			} else if !ok {
				log.Printf("scanner[%s]: %s (%s) entry timing unavailable (%s) — proceeding on other gates (fail-open)",
					mode, c.BaseSymbol, c.Pool[:10], detail)
			}
		}
		best = c
		break
	}
	if best == nil {
		log.Printf("scanner[%s]: DEPLOY SKIPPED — per-token cap and entry timing rejected all %d candidate(s)", mode, len(eligible))
		return
	}
	if best.IsCopycat {
		log.Printf("scanner[%s]: DEPLOY PICK is a copycat (%s, %d share ticker %q) — no clean candidate this batch",
			mode, best.Pool[:10], best.CopycatCount, best.BaseSymbol)
	}
	runner := s.rhDep
	if best.Protocol == "v4" {
		runner = s.rhDepV4
	}

	sz := sizes[best.Pool]
	log.Printf("scanner[%s]: DEPLOY PICK %s (%s, %s) score=%.0f amount=%.5f %s (%.0f%% of %.5f bal, reserve %.5f) strategy=%s",
		mode, best.BaseSymbol, best.Pool[:10], best.Protocol, best.Score, sz.amount, sz.unit,
		sz.sizeCfg.Pct*100, sz.sizeBal, sz.sizeCfg.Reserve, sz.strategy)

	out, err := runner.Deploy(ctx, best.Pool, sz.amount, s.cfg.RobinhoodRangePct, s.cfg.RobinhoodSlippagePct, sz.strategy, sz.quote)
	if err != nil {
		log.Printf("scanner[%s]: DEPLOY FAILED %s (%s): %v\n%s", mode, best.BaseSymbol, best.Pool[:10], err, out)
		return
	}
	deployed := robinhood.Deployed(out)
	summary := robinhood.Summarize(out)
	log.Printf("scanner[%s]: DEPLOY done (deployed=%v) %s\n%s", mode, deployed, best.BaseSymbol, summary)
	if deployed {
		if rerr := s.dep.Report(ctx, summary); rerr != nil {
			log.Printf("scanner[%s]: report delivery failed: %v", mode, rerr)
		}
	}
}

// rhFetcher is a mode's discovery source. It takes the cycle's clock so the
// mature source can age-filter before spending its enrichment budget, keeping
// the single clock read at this edge (see the no-hidden-clock-reads rule).
type rhFetcher func(now time.Time) ([]robinhood.Pool, error)

func (s *Scanner) pollRobinhood(ctx context.Context, mp robinhood.ModeParams, fetch rhFetcher) {
	now := time.Now()
	pools, err := fetch(now)
	if err != nil {
		log.Printf("scanner[%s]: fetch error: %v", mp.Mode, err)
		return
	}

	var screened, deduped, holderRejected, secRejected, hqRejected, gmgnEnriched int
	rejects := map[string]int{}

	var batch []*robinhood.Candidate
	var batchKeys []string
	for _, p := range pools {
		cand, reason := robinhood.Screen(p, mp, now)
		if reason != "" {
			rejects[reasonKey(reason)]++
			continue
		}
		screened++

		// Dedup BEFORE the safety fetches — same budget discipline as the
		// Solana venue's momentum/audit ordering. The rh: prefix keeps venue
		// keys disjoint from Solana pool keys in the shared store.
		poolKey := "rh:" + mp.Mode + ":" + cand.Pool
		seenTTL := s.cfg.RobinhoodSeenTTL
		if mp.Mode == robinhood.StockLadder.Mode {
			// A re-pin exit wants its own pool back, not a different one — see
			// RobinhoodStockSeenTTL. The stock universe is small enough that
			// the venue default silences every candidate simultaneously.
			seenTTL = s.cfg.RobinhoodStockSeenTTL
		}
		fresh, err := s.seen.MarkIfNewTTL(ctx, poolKey, seenTTL)
		if err != nil {
			log.Printf("scanner[%s]: seen store error: %v", mp.Mode, err)
			continue
		}
		if !fresh {
			deduped++
			continue
		}

		// Blockscout holder floor (fail-open on fetch failure).
		if n, ok := robinhood.FetchHolders(cand.BaseAddress); ok {
			if s.cfg.RobinhoodMinHolders > 0 && n < s.cfg.RobinhoodMinHolders {
				holderRejected++
				log.Printf("scanner[%s]: %s (%s) rejected: holders %d < %d",
					mp.Mode, cand.BaseSymbol, cand.Pool[:10], n, s.cfg.RobinhoodMinHolders)
				continue
			}
			cand.Holders = &n
		}

		// GMGN contract-security gate. DIVERGENCE from the fail-open rule,
		// on purpose: a POSITIVE honeypot/blacklist/sell-tax detection hard
		// rejects (EVM's #1 rug vector); unknown (-1/null) still passes.
		if s.cfg.GmgnAPIKey != "" {
			if sec, ok := robinhood.FetchSecurity(s.cfg.GmgnAPIKey, cand.BaseAddress, now.Unix()); ok {
				if r := robinhood.SecurityReject(sec); r != "" {
					secRejected++
					log.Printf("scanner[%s]: %s (%s) rejected on security: %s",
						mp.Mode, cand.BaseSymbol, cand.Pool[:10], r)
					continue
				}
				cand.ApplySecurity(sec)
			}

			// GMGN holder-quality gate — same rat/bundler caps as Solana.
			if ti, ok := robinhood.FetchTokenInfo(s.cfg.GmgnAPIKey, cand.BaseAddress, now.Unix()); ok {
				if r := robinhood.HolderQualityReject(ti, s.cfg.GmgnMaxRatPct, s.cfg.GmgnMaxBundlerPct); r != "" {
					hqRejected++
					log.Printf("scanner[%s]: %s (%s) rejected on gmgn: %s",
						mp.Mode, cand.BaseSymbol, cand.Pool[:10], r)
					continue
				}
				cand.ApplyTokenInfo(ti)
				gmgnEnriched++
			}
		}

		batch = append(batch, cand)
		batchKeys = append(batchKeys, poolKey)
	}

	// Copycat guard: flag same-symbol collisions within this batch (advisory —
	// never rejects; the picker demotes flagged candidates). Cheap, no I/O.
	if flagged := robinhood.EnrichCopycat(batch); flagged > 0 {
		log.Printf("scanner[%s]: copycat guard flagged %d candidate(s)", mp.Mode, flagged)
	}

	sent := 0
	if len(batch) > 0 {
		if s.cfg.RobinhoodDeployEnabled && (s.rhDep.Enabled() || s.rhDepV4.Enabled()) &&
			s.cfg.RobinhoodDeployModes[strings.TrimPrefix(mp.Mode, "rh-")] {
			// Direct deploy (Phase 2): bypasses OBSERVE/webhook entirely,
			// mirroring how Solana's DEPLOY_CMD bypasses its webhook. Gated
			// per-mode by ROBINHOOD_DEPLOY_MODES — a mode outside the set
			// (e.g. fresh while only mature trades) still journals below.
			s.robinhoodDeploy(ctx, mp.Mode, batch)
			sent = len(batch)
		} else if !s.cfg.RobinhoodWebhook {
			// Observe-only (Phase 1 default): journal the full payload so the
			// gate thresholds can be calibrated from logs, without exposing the
			// Solana-only Hermes subscription / deploy pipeline to EVM batches.
			sent = len(batch)
			if body, err := json.Marshal(batch); err == nil {
				log.Printf("scanner[%s]: OBSERVE batch of %d pools: %s\n%s", mp.Mode, sent, rhBatchSummary(batch), body)
			}
		} else if err := s.fwd.Send("robinhood_pool_discovery", batch, now.Unix()); err != nil {
			for _, k := range batchKeys {
				s.seen.Unmark(ctx, k)
			}
			log.Printf("scanner[%s]: webhook error for batch of %d (will retry): %v", mp.Mode, len(batch), err)
		} else {
			sent = len(batch)
			log.Printf("scanner[%s]: SIGNAL batch sent %d pools: %s", mp.Mode, sent, rhBatchSummary(batch))
		}
	}

	line := fmt.Sprintf("scanner[%s]: cycle done — fetched=%d passed_screen=%d deduped=%d holder_rejected=%d sec_rejected=%d gmgn_rejected=%d gmgn_enriched=%d sent=%d",
		mp.Mode, len(pools), screened, deduped, holderRejected, secRejected, hqRejected, gmgnEnriched, sent)
	if len(rejects) > 0 {
		line += " rejects[" + rejectSummary(rejects) + "]"
	}
	log.Print(line)
}

// directDeploy hands the batch straight to the deterministic picker pipeline
// (DEPLOY_CMD) instead of the agent webhook, then delivers a short outcome
// report via REPORT_CMD. Runs synchronously inside the poll loop: deploys are
// rare relative to poll cycles and serializing them prevents two modes from
// racing the same wallet balance. Returns the number of candidates handed
// over (0 on execution failure, which unmarks the batch for retry).
func (s *Scanner) directDeploy(ctx context.Context, mode string, batch []*meteora.Candidate, batchKeys []string) int {
	body, err := json.Marshal(batch)
	if err != nil {
		log.Printf("scanner[%s]: batch marshal error: %v", mode, err)
		return 0
	}
	out, err := s.dep.Deploy(ctx, body, mode)
	if err != nil {
		// Execution failure (timeout, non-zero exit — e.g. failed on-chain
		// deploy), not a deterministic reject: unmark so the batch retries
		// next cycle, mirroring the webhook-failure path.
		for _, k := range batchKeys {
			s.seen.Unmark(ctx, k)
		}
		log.Printf("scanner[%s]: direct deploy failed for batch of %d (will retry): %v\n%s", mode, len(batch), err, out)
		return 0
	}
	deployed := deploy.Deployed(out)
	summary := deploy.Summarize(out, mode)
	log.Printf("scanner[%s]: direct deploy done (deployed=%v) for %s\n%s", mode, deployed, batchSummary(batch), summary)
	// Journal the per-candidate gate decisions — without these, a run of
	// deterministic rejects is undiagnosable from the logs alone.
	if narrative := deploy.GateNarrative(out); narrative != "" {
		log.Printf("scanner[%s]: conviction narrative:\n%s", mode, narrative)
	}
	if deployed || s.cfg.ReportRejects {
		if rerr := s.dep.Report(ctx, summary); rerr != nil {
			log.Printf("scanner[%s]: report delivery failed: %v", mode, rerr)
		}
	}
	return len(batch)
}

func (s *Scanner) pollMode(ctx context.Context, mp meteora.ModeParams) {
	pools, err := meteora.FetchTopPools(s.cfg.DiscoverURL, mp)
	if err != nil {
		log.Printf("scanner[%s]: fetch error: %v", mp.Mode, err)
		return
	}

	// Per-poll tally so a quiet cycle logs "scanned N, 0 passed" instead of
	// nothing — distinguishes "working, nothing qualified" from "API empty".
	var screened, cooldownBlocked, deduped, momRejected, auditRejected, gmgnRejected, gmgnEnriched, loneHeld, pvpFlagged int
	rejects := map[string]int{}

	// Batch mode: collect every fresh, momentum-passing candidate this cycle and
	// emit ONE signal carrying the whole array. The agent then compares the set,
	// picks the strongest pool + strategy, and deploys — instead of first-come
	// per-pool sends where a mediocre early pool grabs a slot the best pool wanted.
	var batch []*meteora.Candidate
	var batchKeys []string
	var momRejectedKeys []string
	for _, p := range pools {
		cand, reason := meteora.Screen(p, mp)
		if reason != "" {
			rejects[reasonKey(reason)]++ // per-pool detail too noisy; tallied per gate
			continue
		}
		screened++

		// Re-entry cooldown gate: dlmm_monitor.py sets a per-token cooldown on
		// every close (1-2h base, escalating to 24h/72h on repeat losses).
		// Until now this was only enforced at deploy time, so a batch full of
		// cooling tokens wasted the whole signal and crowded out eligible
		// pools. Checked BEFORE MarkIfNew so the pool re-signals as soon as
		// its cooldown lapses instead of staying silenced for SEEN_TTL.
		if cd := s.seen.CooldownRemaining(ctx, cand.BaseSymbol); cd > 0 {
			cooldownBlocked++
			log.Printf("scanner[%s]: %s (%s) in re-entry cooldown (%s left)",
				mp.Mode, cand.BaseSymbol, cand.Pool[:8], cd.Round(time.Minute))
			continue
		}

		// Dedup BEFORE the momentum fetch so we don't hit DexScreener for
		// pools we've already emitted this window. Turnover uses its own
		// shorter window: fast-cycle positions live minutes, and the default
		// TTL silenced still-qualifying pools long after their cycle ended.
		poolKey := mp.Mode + ":" + cand.Pool
		seenTTL := s.cfg.SeenTTL
		switch mp.Mode {
		case "turnover":
			seenTTL = s.cfg.TurnoverSeenTTL
		case "pulse":
			// 5m discovery window — the pools churn faster than turnover's, so
			// re-signalling must not be silenced for the default TTL either.
			seenTTL = s.cfg.PulseSeenTTL
		case "casual":
			// Casual positions + their close cooldown resolve within hours;
			// see CasualSeenTTL in config for why 24h over-silenced.
			seenTTL = s.cfg.CasualSeenTTL
		}
		fresh, err := s.seen.MarkIfNewTTL(ctx, poolKey, seenTTL)
		if err != nil {
			log.Printf("scanner[%s]: seen store error: %v", mp.Mode, err)
			continue
		}
		if !fresh {
			deduped++
			continue
		}

		// Momentum / downtrend gate (best-effort, fail-open). Momentum-rejected
		// pools stay marked seen (no unmark) so we don't re-hit DexScreener for
		// them every cycle within the SEEN_TTL window. Per-mode opt-out via
		// ModeParams.SkipMomentumGate — a directional gate does not fit every
		// screen; see the Pulse comment in meteora/screen.go.
		if s.cfg.EnableMomentumGate && !mp.SkipMomentumGate {
			if m, ok := meteora.GetMomentum(cand.BaseMint); ok {
				if r := meteora.MomentumReject(m); r != "" {
					momRejected++
					momRejectedKeys = append(momRejectedKeys, poolKey)
					log.Printf("scanner[%s]: %s (%s) rejected on momentum: %s", mp.Mode, cand.BaseSymbol, cand.Pool[:8], r)
					continue
				}
			}
		}

		// Jupiter audit gate (best-effort, fail-open, same seen semantics as
		// momentum). Hard-rejects bot-farmed tokens; otherwise enriches the
		// candidate with bot % / global fees so the agent judges with the
		// audit on-screen instead of re-fetching it.
		if s.cfg.EnableAuditGate {
			if a, ok := meteora.FetchAudit(cand.BaseMint); ok {
				if r := meteora.AuditReject(a); r != "" {
					auditRejected++
					log.Printf("scanner[%s]: %s (%s) rejected on audit: %s", mp.Mode, cand.BaseSymbol, cand.Pool[:8], r)
					continue
				}
				cand.ApplyAudit(a)
			}
		}

		// GMGN holder-quality gate (fail-open, same seen semantics as
		// momentum/audit). Hard-rejects tokens whose insider ("rat") or
		// bundler volume share exceeds the configured caps — the pre-rug
		// signals none of the other gates can see. Otherwise attaches
		// smart-money/KOL holder counts, insider + bundler volume share and
		// the dev's track record so the agent ranks smart-money-backed pools
		// above bot-farmed ones. A failed fetch just ships the candidate bare.
		if s.cfg.EnableGmgnGate && s.cfg.GmgnAPIKey != "" {
			if g, ok := meteora.FetchGmgn(s.cfg.GmgnAPIKey, cand.BaseMint, time.Now().Unix()); ok {
				if r := meteora.GmgnReject(g, s.cfg.GmgnMaxRatPct, s.cfg.GmgnMaxBundlerPct); r != "" {
					gmgnRejected++
					log.Printf("scanner[%s]: %s (%s) rejected on gmgn: %s", mp.Mode, cand.BaseSymbol, cand.Pool[:8], r)
					continue
				}
				cand.ApplyGmgn(g)
				gmgnEnriched++
			}
		}

		// Pool memory summary: surface this pool's journaled close record so
		// the agent weighs a mixed history when picking (the pipeline's
		// deterministic ">=2 closes net negative" skip still applies at
		// deploy time — this is the advisory layer on top).
		if n, pnl, ok := s.seen.PoolCloseStats(ctx, cand.Pool); ok {
			cand.PriorCloses = &n
			cand.PriorNetPnlSOL = &pnl
		}

		batch = append(batch, cand)
		batchKeys = append(batchKeys, poolKey)
	}

	// A momentum reject normally stays marked seen for the whole SEEN_TTL so we
	// don't re-hit DexScreener for a dumping pool every cycle. But when it took
	// the LAST candidate with it, that trade-off silences the entire mode for
	// hours: turnover's live supply is 1-4 qualifying pools per cycle, so a
	// single -3.9% 5m print blanked it for the full 2h TTL (observed
	// 2026-07-28). Momentum is the one *transient* reject — the price recovers
	// in minutes — unlike the audit / GMGN safety rejects, which stay sticky by
	// design. Unmark only when the batch ended up empty, so the extra
	// DexScreener traffic is bounded to cycles that would have sent nothing.
	if len(batch) == 0 && len(momRejectedKeys) > 0 {
		for _, k := range momRejectedKeys {
			s.seen.Unmark(ctx, k)
		}
		log.Printf("scanner[%s]: batch empty — unmarked %d momentum-rejected pool(s) to retry next cycle",
			mp.Mode, len(momRejectedKeys))
	}

	// PVP rival check (advisory, fail-open): flag candidates whose symbol is
	// contested by an established rival token with its own live DLMM pool, so
	// the agent weighs the war before entering the weaker side. Runs on the
	// final batch only — post-gate, post-dedup — to keep the request budget
	// bounded (one symbol search per unique symbol per cycle).
	if s.cfg.EnablePVPCheck && len(batch) > 0 {
		pvpFlagged = meteora.EnrichPVP(batch)
	}

	// Lone-candidate conviction gate: a single-pool batch removes the agent's
	// ability to compare, and "only option" must not read as "good option".
	// A solo candidate ships only when its score clears the conviction floor.
	// The pool is unmarked so it can ride a future, richer batch (or re-pass
	// alone once its score improves) instead of being silenced for SEEN_TTL.
	if len(batch) == 1 && s.cfg.LoneMinScore > 0 && batch[0].Score < s.cfg.LoneMinScore {
		log.Printf("scanner[%s]: lone candidate %s (%s) score %.1f < %.1f — held back",
			mp.Mode, batch[0].BaseSymbol, batch[0].Pool[:8], batch[0].Score, s.cfg.LoneMinScore)
		s.seen.Unmark(ctx, batchKeys[0])
		loneHeld++
		batch, batchKeys = nil, nil
	}

	sent := 0
	if len(batch) > 0 {
		if s.dep.Enabled() {
			sent = s.directDeploy(ctx, mp.Mode, batch, batchKeys)
		} else if err := s.fwd.Send("meteora_pool_discovery", batch, time.Now().Unix()); err != nil {
			// Delivery failed — unmark the whole batch so these pools retry on the
			// next poll instead of being silently dropped for the SEEN_TTL window.
			for _, k := range batchKeys {
				s.seen.Unmark(ctx, k)
			}
			log.Printf("scanner[%s]: webhook error for batch of %d (will retry): %v", mp.Mode, len(batch), err)
		} else {
			sent = len(batch)
			log.Printf("scanner[%s]: SIGNAL batch sent %d pools: %s", mp.Mode, sent, batchSummary(batch))
		}
	}

	line := fmt.Sprintf("scanner[%s]: cycle done — fetched=%d passed_screen=%d cooldown_blocked=%d deduped=%d mom_rejected=%d audit_rejected=%d gmgn_rejected=%d gmgn_enriched=%d pvp_flagged=%d lone_held=%d sent=%d",
		mp.Mode, len(pools), screened, cooldownBlocked, deduped, momRejected, auditRejected, gmgnRejected, gmgnEnriched, pvpFlagged, loneHeld, sent)
	if len(rejects) > 0 {
		line += " rejects[" + rejectSummary(rejects) + "]"
	}
	log.Print(line)
}
