package config

import (
	"os"
	"strconv"
	"strings"
	"time"

	"github.com/pgen0x/azimuth/internal/robinhood"
)

// Config holds all runtime settings, sourced from environment variables.
type Config struct {
	// Meteora discovery
	DiscoverURL  string        // base discovery endpoint
	PollInterval time.Duration // how often to poll each timeframe

	// Hermes webhook sink
	WebhookURL    string
	WebhookSecret string

	// Redis dedup (optional; empty RedisAddr -> in-memory dedup)
	RedisAddr    string
	RedisSeenKey string
	SeenTTL      time.Duration
	// Turnover dedups on a shorter window: its positions live minutes, not
	// hours, so a still-qualifying pool must be able to re-signal once the
	// prior cycle ends (pool/symbol cooldowns still gate fee-dead re-entries).
	TurnoverSeenTTL time.Duration
	// Casual gets the same treatment at a gentler setting: positions live
	// ~30m-2h and the monitor's close cooldown lapses in 1-2h, but the full
	// SEEN_TTL silenced a proven pool for the rest of the day. 6h lets it
	// re-compete after the cooldown clears without the re-signal spam a 1-2h
	// window would cause (77% of screen passes are dedup re-qualifiers).
	CasualSeenTTL time.Duration
	// Pulse polls a 5m discovery window, so its pools churn even faster than
	// turnover's; it shares turnover's short re-signal window.
	PulseSeenTTL time.Duration

	// Screening thresholds per mode are defined in the meteora package;
	// only the enable toggles live here.
	EnableCasual   bool
	EnableMultiday bool
	EnableTurnover bool
	// EnablePulse runs the ported reference-bot screen (5m/trending)
	// alongside turnover (30m/all), so entries are the union of both screens
	// instead of only the pools turnover's window happens to surface.
	EnablePulse bool

	// EnableMomentumGate fetches DexScreener momentum to reject downtrends
	// before emitting (matches the Python downtrend gate). Best-effort.
	EnableMomentumGate bool

	// EnableAuditGate fetches the Jupiter token audit (bot-holder %, global
	// fees) for every fresh candidate and hard-rejects bot-farmed tokens
	// before emitting. Best-effort, fail-open like the momentum gate.
	EnableAuditGate bool

	// LoneMinScore is the conviction floor for single-candidate batches: when
	// a cycle produces exactly one fresh pool, it must score at least this to
	// be emitted. Prevents "only option so deploy it" entries on weak solo
	// candidates. 0 disables the gate.
	LoneMinScore float64

	// EnableGmgnGate fetches the GMGN token snapshot (smart-money holder
	// count, insider/bundler volume share, dev track record) for every fresh
	// candidate and attaches it to the payload. Hard-rejects candidates whose
	// insider ("rat") or bundler volume share exceeds the caps below — the
	// strongest pre-rug signals available (three -100% rug closes drove the
	// journal's entire net loss). Missing fields still pass (fail-open);
	// requires GmgnAPIKey (empty key disables the fetch regardless of the
	// toggle). A cap <= 0 disables that check (enrichment stays on).
	EnableGmgnGate    bool
	GmgnAPIKey        string
	GmgnMaxRatPct     float64
	GmgnMaxBundlerPct float64

	// EnablePVPCheck searches for an established same-symbol rival token with
	// its own live DLMM pool and flags contested candidates (is_pvp + rival
	// stats) in the payload. Advisory only — never rejects. Best-effort,
	// fail-open like the momentum/audit gates.
	EnablePVPCheck bool

	// EnableRobinhood turns on the Robinhood Chain venue: GeckoTerminal
	// new-pool discovery + screening (internal/robinhood). Phase 1 is
	// signal-only — robinhood batches ALWAYS go to the webhook sink, never to
	// DeployCmd, because the deploy pipeline only speaks Solana (see
	// docs/ROBINHOOD_CHAIN_PLAN.md). Off by default.
	EnableRobinhood bool
	// EnableRobinhoodMature turns on the venue's SECOND mode (rh-mature):
	// established pools still printing outsized fee/TVL, discovered through
	// Uniswap's own interface gateway rather than GeckoTerminal. Independent of
	// EnableRobinhood on purpose — the two modes share every safety gate but no
	// discovery source, and either can run alone. Off by default.
	EnableRobinhoodMature bool
	// EnableRobinhoodLadder turns on the venue's THIRD mode (rh-ladder): the
	// weth_ladder thesis, which parks a one-sided WETH bid wall under an
	// established pool and never buys the token. It shares rh-mature's
	// discovery source (Uniswap's gateway) but screens on churn instead of
	// yield, so the two select largely different pools from the same feed —
	// see robinhood.Ladder. Independent toggle for the same reason the other
	// two are: either can run alone. Off by default.
	EnableRobinhoodLadder bool
	// EnableRobinhoodStockLadder turns on the venue's FOURTH mode
	// (rh-usdg-ladder): the same one-sided bid-wall shape as rh-ladder, run
	// against the chain's USDG-quoted tokenized equities instead of its WETH
	// memecoins. Same gateway feed, far lower yield bar (0.2%/day vs 1.5%),
	// and it spends the wallet's USDG rather than its WETH — so it competes
	// with rh-ladder for gas but not for capital. Off by default; see
	// robinhood.StockLadder.
	EnableRobinhoodStockLadder bool
	// EnableRobinhoodPulseLadder turns on the venue's FIFTH mode
	// (rh-pulse-ladder): the same one-sided WETH bid wall as rh-ladder, aimed at
	// memecoin pools in their FIRST DAY — the band between the launch feed and
	// the gateway's 24h floor. It is the only mode that needs a carried
	// registry, because new_pools scrolls a pool off within minutes and nothing
	// else here indexes an eight-hour-old pool (pulse.go). It spends the same
	// WETH balance rh-ladder does, so running both splits one wallet across two
	// age bands. Off by default; see robinhood.PulseLadder.
	EnableRobinhoodPulseLadder bool
	// EnableRobinhoodTurnover turns on the venue's SIXTH mode (rh-turnover):
	// the port of Solana's turnover thesis — ONE one-sided quote rung
	// (weth_below) resting adjacent to spot in an oscillating pool, re-pinned
	// when price drifts off it or it stops earning instead of closed. It
	// replaces the ladder modes as the venue's deploy strategy (2026-08-07):
	// 104 live ladder rung closes produced zero fee-positive exits, because
	// two thirds of a wall's capital sits in rungs the market never reaches.
	// Shares rh-mature's gateway feed and every safety gate, and needs
	// uni_monitor.py's re-center loop to work at all — a resting bid nobody
	// re-pins is just the ladder again. Off by default; see robinhood.Turnover.
	EnableRobinhoodTurnover bool
	// RobinhoodDiscoverURL overrides the GeckoTerminal new_pools endpoint
	// (empty = the package default). The public tier allows 30 req/min.
	// Applies to the Fresh mode only; rh-mature has its own source.
	RobinhoodDiscoverURL string
	// RobinhoodSeenTTL is the venue's dedup window. Fresh-pool signals age out
	// of the thesis within a day; 6h lets a still-qualifying pool re-signal.
	RobinhoodSeenTTL time.Duration
	// RobinhoodStockSeenTTL is the stock ladder's own, much shorter window.
	// The venue default assumes a pool is only worth re-signalling once its
	// thesis has had time to change, which is exactly wrong for a strategy
	// whose EXIT IS A RE-PIN: the usdg_ladder closes precisely so it can be
	// rebuilt around the new price, and 6h of silence on the pool it just left
	// is 6h of idle capital. The tokenized-equity universe is also a handful of
	// pools, so one long TTL silences the whole mode at once — observed
	// 2026-08-05, every cycle deduped 18 of 18 and sent nothing.
	RobinhoodStockSeenTTL time.Duration
	// RobinhoodMinHolders is the Blockscout holder-count floor per candidate
	// (fail-open when the fetch fails; 0 disables). New-chain tokens
	// accumulate holders fast — 50 filters single-wallet theater without
	// demanding Solana-scale (500+) adoption.
	RobinhoodMinHolders int
	// RobinhoodWebhook forwards robinhood batches to the webhook sink. Off by
	// default (observe-only: batches are journaled to the log): the live
	// Hermes subscription prompt only understands Solana DLMM payloads, and
	// an EVM candidate reaching it could trigger a nonsense deploy attempt.
	// Enable once the subscription prompt handles the robinhood schema.
	RobinhoodWebhook bool

	// RobinhoodDeployEnabled switches the venue to direct-deploy, mirroring
	// Solana's DEPLOY_CMD mode: instead of observing/forwarding, the daemon
	// picks the highest-scoring candidate in each batch and mints it directly
	// via RobinhoodExecutorCmd (uni_executor.js), bypassing the webhook
	// entirely. There is no monitor/exit automation for this venue yet
	// (docs/ROBINHOOD_CHAIN_PLAN.md Phase 3) — positions stay open until
	// closed by hand, so RobinhoodMaxOpenPositions is the only safety brake.
	// Off by default; requires RobinhoodExecutorCmd.
	RobinhoodDeployEnabled bool
	// RobinhoodDeployModes limits direct-deploy to the listed modes; batches
	// from other modes fall back to the observe/webhook sink instead. The
	// deploy toggle alone is all-or-nothing, and the fresh feed's live record
	// (uni_closes.jsonl 2026-07-13/14: 9 of 10 closes were emergency stop
	// losses at a median −49% within ~1 minute) showed why mature-only deploy
	// with fresh kept as an observe journal must be expressible. Keys are the
	// mode names with the "rh-" prefix stripped ("fresh", "mature").
	RobinhoodDeployModes map[string]bool
	// RobinhoodExecutorCmd is the whitespace-split command line for
	// uni_executor.js, e.g.
	// "node /home/ubuntu/.hermes/profiles/<profile>/skills/solana-dlmm/scripts/uni_executor.js".
	// Wallet keys stay in the profile .env — the executor loads them itself.
	RobinhoodExecutorCmd string
	// RobinhoodV4ExecutorCmd is the same for uni_v4_executor.js, the v4
	// sibling (docs/ROBINHOOD_CHAIN_PLAN.md Phase 7). Empty (default) keeps
	// v4 candidates observe-only: they are journaled/forwarded upstream but
	// excluded from deploy, exactly the pre-Phase-7 behavior.
	RobinhoodV4ExecutorCmd string
	// RobinhoodDeployTimeout bounds one uni_executor.js invocation
	// (swap + mint can take a few blocks even at Robinhood Chain's ~100ms pace).
	RobinhoodDeployTimeout time.Duration
	// RobinhoodSize sizes each deploy dynamically from the live WETH balance
	// (robinhood.ComputeDeployAmount) — the venue's port of the Solana
	// pipeline's compute_deploy_amount. Replaces the old fixed
	// ROBINHOOD_DEPLOY_AMOUNT_WETH, which minted a flat 0.003 WETH regardless of
	// wallet size (~17% of a 0.0174 WETH stack) and never grew with the balance.
	RobinhoodSize robinhood.SizeParams
	// RobinhoodSizeUSDG sizes USDG-quoted v4 deploys from the live USDG
	// balance — same shape, dollar units (USDG's 6 decimals are already
	// applied by the executor's balance output). Separate params because a
	// sensible WETH floor (~0.003 ≈ $8) and a sensible dollar floor are
	// different numbers, and sharing one config would silently misprice
	// whichever asset the operator wasn't thinking about.
	RobinhoodSizeUSDG robinhood.SizeParams
	// RobinhoodTenure grades a pool by how many turnover cycles it has survived
	// and how many of those ended in a fill, then sizes the deploy accordingly:
	// an unproven pool gets a floor-sized probe, a pool that has earned its
	// tenure gets the full percentage, and a pool that fills too often is
	// declined outright. See robinhood.TenureParams for the book it came from.
	//
	// Inert with no REDIS_ADDR — the counters live there and are written by
	// uni_monitor.py, so a wallet with no Redis keeps flat sizing rather than
	// probing every pool forever.
	RobinhoodTenure robinhood.TenureParams
	// RobinhoodMinGasEth is the native-ETH floor required to deploy. Unlike
	// Solana — where SOL is gas AND quote, so one reserve covers both — this
	// venue pays gas in ETH but LPs in WETH, so a wallet flush with WETH can
	// still be unable to pay for the mint. Fail closed below this.
	RobinhoodMinGasEth float64
	// RobinhoodDeployStrategy is the uni_executor.js mint strategy:
	// "balanced_tight" (two-sided, swaps half) or "weth_below" (one-sided).
	// rh-turnover ignores it and pins weth_below in scanner.sizeFor — its shape
	// is part of the thesis, not an operator knob.
	RobinhoodDeployStrategy string
	RobinhoodRangePct       float64
	RobinhoodSlippagePct    float64
	// RobinhoodMaxOpenPositions caps concurrent NPM positions this venue will
	// hold. Checked via a live `positions` count before every deploy attempt
	// (fail-closed on any read error) since nothing closes positions
	// automatically yet. Keep this low until Phase 3 monitor exists.
	RobinhoodMaxOpenPositions int
	// RobinhoodMaxPerToken caps how many of those slots ONE underlying may hold
	// (0 disables). The venue lists the same token in several pools — a
	// tokenized equity commonly trades at the 0.05%, 0.3% and 1% tiers at once,
	// and in v4 one pair+fee can exist at several tick spacings — so the
	// wallet-wide cap alone let a single underlying take every slot (GME held
	// three of three on 2026-08-05). Walls in different pools of the same token
	// are not diversification; they are one price bet minted three times, and
	// they all fill together.
	RobinhoodMaxPerToken int
	// RobinhoodRPCURL is the chain's JSON-RPC endpoint, used by the entry gate's
	// on-chain candle fallback (internal/robinhood/onchain.go). Defaults to the
	// public keyless endpoint because that is what the fallback is FOR: a
	// fallback that needed its own provider account would expire quietly and
	// leave the gate back where it started. Override to point at a private node.
	RobinhoodRPCURL string
	// RobinhoodOnchainCandles lets the entry-timing gate rebuild its 15m candles
	// from the pool's Swap logs when GeckoTerminal will not serve them (429,
	// cooldown, queue too long, any error). ON by default: GT's public tier is
	// ~10 req/min for an IP three processes share, and the measured consequence
	// of not having this was 82 `geckoterminal status 429` in six hours with the
	// downtrend veto failing open through all of them — a gate that is absent
	// precisely when the venue is busiest is worse than no gate, because the
	// journal still reads as though it ran. Turn OFF only to isolate the RPC as
	// a suspect; the gate then fails open on a GT refusal as it did before.
	RobinhoodOnchainCandles bool

	// RobinhoodIndicatorGate runs the supertrend_or_rsi entry-timing check
	// (internal/robinhood/indicators.go, the Go port of local_indicators.py)
	// on each deploy pick, skipping candidates whose token is in a confirmed
	// downtrend. Fail-open on missing candle data. On by default — the same
	// check already gates Solana entries via dlmm_pipeline.py.
	RobinhoodIndicatorGate bool

	// DeployCmd switches the daemon to direct-deploy mode: instead of
	// forwarding each batch to the Hermes agent webhook (LLM pick, observed at
	// 19-54 min/decision), the daemon runs this command with
	// `--from-batch <payload JSON> --mode <mode>` appended and the pipeline
	// picks + deploys deterministically in seconds. Point it at the skill's
	// pipeline, e.g. `python3 <profile>/skills/solana-dlmm/scripts/dlmm_pipeline.py`.
	// Empty (default) keeps the webhook flow. Whitespace-split; no spaces in paths.
	DeployCmd string
	// DeployTimeout bounds one direct-deploy run (pre-swap + on-chain deploy
	// can take a couple of minutes on congested RPC).
	DeployTimeout time.Duration
	// ReportCmd, when set in direct-deploy mode, receives a short outcome
	// report on stdin after each run — e.g. `hermes send -t telegram` (no LLM,
	// reuses the gateway's bot credentials). Empty = log only.
	ReportCmd string
	// ReportRejects also delivers REJECT outcomes to ReportCmd. Off by default:
	// re-signalling modes produce rejects every few cycles and the journal
	// already logs them; deploys are always reported.
	ReportRejects bool
}

func getenv(key, def string) string {
	if v := os.Getenv(key); v != "" {
		return v
	}
	return def
}

func getbool(key string, def bool) bool {
	v := os.Getenv(key)
	if v == "" {
		return def
	}
	b, err := strconv.ParseBool(v)
	if err != nil {
		return def
	}
	return b
}

func getint(key string, def int) int {
	v := os.Getenv(key)
	if v == "" {
		return def
	}
	n, err := strconv.Atoi(v)
	if err != nil {
		return def
	}
	return n
}

func getfloat(key string, def float64) float64 {
	v := os.Getenv(key)
	if v == "" {
		return def
	}
	f, err := strconv.ParseFloat(v, 64)
	if err != nil {
		return def
	}
	return f
}

func getdur(key string, def time.Duration) time.Duration {
	v := os.Getenv(key)
	if v == "" {
		return def
	}
	d, err := time.ParseDuration(v)
	if err != nil {
		return def
	}
	return d
}

// getmodes parses a comma-separated mode list into a set. Entries are
// lowercased and the "rh-" prefix is stripped, so "mature", "rh-mature" and
// "RH-Mature" all name the same mode.
func getmodes(key, def string) map[string]bool {
	v := os.Getenv(key)
	if v == "" {
		v = def
	}
	set := make(map[string]bool)
	for _, m := range strings.Split(v, ",") {
		m = strings.TrimPrefix(strings.ToLower(strings.TrimSpace(m)), "rh-")
		if m != "" {
			set[m] = true
		}
	}
	return set
}

// Load builds a Config from the environment with sane public defaults.
func Load() Config {
	cfg := loadConfig()
	// Install the venue's RPC settings in the robinhood package. It happens here
	// rather than in scanner.New (where SetCandleStore is wired) because the
	// fallback lives behind fetchOHLCV, a leaf HTTP helper the scanner never
	// names — there is no call site up there to hand a URL to. Idempotent, and
	// the package's own defaults already work if this never runs.
	robinhood.SetOnchainFallback(cfg.RobinhoodRPCURL, cfg.RobinhoodOnchainCandles)
	return cfg
}

func loadConfig() Config {
	return Config{
		DiscoverURL:           getenv("METEORA_DISCOVER_URL", "https://pool-discovery-api.datapi.meteora.ag/pools"),
		PollInterval:          getdur("POLL_INTERVAL", 60*time.Second),
		WebhookURL:            getenv("HERMES_WEBHOOK_URL", "http://127.0.0.1:8646/webhooks/dlmm-signal"),
		WebhookSecret:         getenv("HERMES_WEBHOOK_SECRET", "dlmm-signal-secret-change-me"),
		RedisAddr:             getenv("REDIS_ADDR", ""),
		RedisSeenKey:          getenv("REDIS_SEEN_KEY", "dlmm:signal:seen_pools"),
		SeenTTL:               getdur("SEEN_TTL", 24*time.Hour),
		TurnoverSeenTTL:       getdur("TURNOVER_SEEN_TTL", 2*time.Hour),
		CasualSeenTTL:         getdur("CASUAL_SEEN_TTL", 6*time.Hour),
		PulseSeenTTL:          getdur("PULSE_SEEN_TTL", 2*time.Hour),
		EnablePulse:           getbool("ENABLE_PULSE", false),
		EnableCasual:          getbool("ENABLE_CASUAL", true),
		EnableMultiday:        getbool("ENABLE_MULTIDAY", true),
		EnableTurnover:        getbool("ENABLE_TURNOVER", false), // off by default; enable after validating the screen on your own journal
		EnableMomentumGate:    getbool("ENABLE_MOMENTUM_GATE", true),
		EnableAuditGate:       getbool("ENABLE_AUDIT_GATE", true),
		EnableGmgnGate:        getbool("ENABLE_GMGN_GATE", true),
		GmgnAPIKey:            getenv("GMGN_API_KEY", ""),
		GmgnMaxRatPct:         getfloat("GMGN_MAX_RAT_PCT", 40),
		GmgnMaxBundlerPct:     getfloat("GMGN_MAX_BUNDLER_PCT", 40),
		LoneMinScore:          getfloat("LONE_MIN_SCORE", 50),
		EnablePVPCheck:        getbool("ENABLE_PVP_CHECK", true),
		EnableRobinhood:       getbool("ROBINHOOD_ENABLED", false),
		EnableRobinhoodMature: getbool("ROBINHOOD_MATURE", false),
		EnableRobinhoodLadder: getbool("ROBINHOOD_LADDER", false),

		EnableRobinhoodStockLadder: getbool("ROBINHOOD_STOCK_LADDER", false),
		EnableRobinhoodPulseLadder: getbool("ROBINHOOD_PULSE_LADDER", false),
		EnableRobinhoodTurnover:    getbool("ROBINHOOD_TURNOVER", false),

		RobinhoodDiscoverURL: getenv("ROBINHOOD_DISCOVER_URL", ""),
		RobinhoodWebhook:     getbool("ROBINHOOD_WEBHOOK", false),
		// Robinhood deploy disabled by default. Observe-only until the venue's
		// own close journal argues otherwise.
		RobinhoodDeployEnabled: getbool("ROBINHOOD_DEPLOY_ENABLED", false),
		// Mode keys are the Mode string minus its "rh-" prefix, so the stock
		// ladder is "usdg-ladder". It is NOT in the default set: the USDG rungs
		// spend a balance the wallet may not hold, and enabling discovery for it
		// should not silently enable spending.
		RobinhoodDeployModes:   getmodes("ROBINHOOD_DEPLOY_MODES", "fresh,mature,ladder,turnover"),
		RobinhoodExecutorCmd:   getenv("ROBINHOOD_EXECUTOR_CMD", ""),
		RobinhoodV4ExecutorCmd: getenv("ROBINHOOD_V4_EXECUTOR_CMD", ""),
		RobinhoodDeployTimeout: getdur("ROBINHOOD_DEPLOY_TIMEOUT", 2*time.Minute),
		RobinhoodSize: robinhood.SizeParams{
			// Same 45% pct as the Solana pipeline. Floor is the old fixed size —
			// a position smaller than that isn't worth its gas + round-trip swap.
			// Ceil bounds a single position while the venue is still young; raise
			// it as the wallet and the venue's close journal grow.
			Reserve: getfloat("ROBINHOOD_DEPLOY_RESERVE_WETH", 0.002),
			Pct:     getfloat("ROBINHOOD_DEPLOY_PCT", 0.45),
			Floor:   getfloat("ROBINHOOD_DEPLOY_FLOOR_WETH", 0.003),
			Ceil:    getfloat("ROBINHOOD_DEPLOY_CEIL_WETH", 0.05),
		},
		RobinhoodSizeUSDG: robinhood.SizeParams{
			// Dollar units. Floor ≈ the WETH floor's dollar value; ceil bounds a
			// single USDG position at roughly the WETH ceil's dollar value.
			Reserve: getfloat("ROBINHOOD_DEPLOY_RESERVE_USDG", 5),
			Pct:     getfloat("ROBINHOOD_DEPLOY_PCT_USDG", 0.45),
			Floor:   getfloat("ROBINHOOD_DEPLOY_FLOOR_USDG", 8),
			Ceil:    getfloat("ROBINHOOD_DEPLOY_CEIL_USDG", 150),
		},
		RobinhoodTenure: robinhood.TenureParams{
			// The bucket edges are the measured ones, not round numbers: 8 cycles
			// is where the book stops losing (-0.35%) and 20 is where it starts
			// paying (+6.50%). Everything under 8 lost 5-22%.
			ProbeCycles: getint("ROBINHOOD_TENURE_PROBE_CYCLES", 8),
			FullCycles:  getint("ROBINHOOD_TENURE_FULL_CYCLES", 20),
			// 0.35 sits between the profitable bucket's 13% and the two losing
			// buckets' 39-43%, so it convicts a pool for the pattern that lost
			// money without touching the pools that made it.
			MaxFillPct: getfloat("ROBINHOOD_TENURE_MAX_FILL_PCT", 0.35),
			// Four cycles before the veto may fire. Below that the "rate" is one
			// or two events, and rejecting on it would re-create the one-and-done
			// selection this whole change exists to stop making.
			MinSample: getint("ROBINHOOD_TENURE_MIN_SAMPLE", 4),
		},
		RobinhoodMinGasEth: getfloat("ROBINHOOD_MIN_GAS_ETH", 0.0002),
		// weth_ladder, not balanced_tight. balanced_tight swaps half the commit
		// into the memecoin before minting, so every position is long a token on
		// a chain where tokens bleed, and in backtest every exit it took was a
		// price exit rather than a fee take-profit. weth_ladder never buys the
		// token. It is still the loser's default only if you override this back.
		RobinhoodDeployStrategy: getenv("ROBINHOOD_DEPLOY_STRATEGY", "weth_ladder"),
		// Both ignored by weth_ladder (its geometry is rungs x rung-ticks, tuned
		// executor-side via UNI_LADDER_*); they still drive balanced_tight and
		// weth_below.
		RobinhoodRangePct:    getfloat("ROBINHOOD_RANGE_PCT", 10),
		RobinhoodSlippagePct: getfloat("ROBINHOOD_SLIPPAGE_PCT", 5),
		// Counted in LADDERS (funded pools), not NPM NFTs — one ladder is N
		// rungs, so an NFT-denominated cap would let a single entry exhaust the
		// budget. See robinhood.Runner.OpenPositions. Raised from 1 because the
		// ladder thesis is diversification across many small books: the observed
		// wallet ran 23 concurrently. 3 is the scaled-down starting point, not a
		// measured optimum — raise it as the close journal earns the confidence.
		RobinhoodMaxOpenPositions: getint("ROBINHOOD_MAX_OPEN_POSITIONS", 3),
		RobinhoodMaxPerToken:      getint("ROBINHOOD_MAX_PER_TOKEN", 1),
		RobinhoodIndicatorGate:    getbool("ROBINHOOD_INDICATOR_GATE", true),
		RobinhoodRPCURL:           getenv("ROBINHOOD_RPC_URL", "https://rpc.mainnet.chain.robinhood.com"),
		RobinhoodOnchainCandles:   getbool("ROBINHOOD_ONCHAIN_CANDLES", true),
		RobinhoodSeenTTL:          getdur("ROBINHOOD_SEEN_TTL", 6*time.Hour),
		RobinhoodStockSeenTTL:     getdur("ROBINHOOD_STOCK_SEEN_TTL", 90*time.Minute),
		RobinhoodMinHolders:       getint("ROBINHOOD_MIN_HOLDERS", 50),
		DeployCmd:                 getenv("DEPLOY_CMD", ""),
		DeployTimeout:             getdur("DEPLOY_TIMEOUT", 5*time.Minute),
		ReportCmd:                 getenv("REPORT_CMD", ""),
		ReportRejects:             getbool("REPORT_REJECTS", false),
	}
}
