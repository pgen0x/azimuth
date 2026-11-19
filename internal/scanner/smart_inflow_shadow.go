package scanner

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"log"
	"os"
	"path/filepath"
	"strconv"
	"syscall"
	"time"

	"github.com/pgen0x/azimuth/internal/meteora"
)

// Smart-money inflow shadow (paper-trade journal S2). LOGGING ONLY: it reads
// the GMGN holder counts the gate already fetched, compares them with the
// previous reading for the same pool, and never feeds back into a gate, the
// dedup store or dispatch.
const (
	// smartInflowMinSmart / smartInflowMinKol are the pre-registered increases
	// between two readings of one pool that count as an inflow event.
	smartInflowMinSmart = 2
	smartInflowMinKol   = 1
	// smartInflowDedup bounds the journal to one row per pool per window.
	smartInflowDedup = 30 * time.Minute
	// smartInflowBaselineMax drops a baseline older than this. GMGN is only
	// re-read when the pool is re-offered (every PULSE_SEEN_TTL for pulse), so a
	// stale baseline would turn a day of slow drift into one "inflow" and would
	// keep every pool ever seen in memory.
	smartInflowBaselineMax = 6 * time.Hour
)

// smartReading is the last GMGN holder-tag reading seen for one pool.
type smartReading struct {
	smart, kol *int
	at         time.Time
}

// smartInflowRow is one row of memories/dlmm_smart_inflow_shadow.jsonl.
// fee_active_tvl_5m is the screened fee/active-TVL ratio of the mode's own
// discovery window, named for pulse (5m); fee_window states the window so a
// casual/turnover row is not misread.
type smartInflowRow struct {
	TS             int64   `json:"ts"`
	Pool           string  `json:"pool"`
	Mint           string  `json:"mint"`
	Symbol         string  `json:"symbol"`
	SmartBefore    *int    `json:"smart_before"`
	SmartAfter     *int    `json:"smart_after"`
	KolBefore      *int    `json:"kol_before"`
	KolAfter       *int    `json:"kol_after"`
	Mode           string  `json:"mode"`
	ActiveTVL      float64 `json:"active_tvl"`
	FeeActiveTVL5m float64 `json:"fee_active_tvl_5m"`
	FeeWindow      string  `json:"fee_window"`
}

// rose reports whether both readings are known and after-before >= min.
// Unknown on either side is never an event: GMGN omits the tags for some
// tokens, and nil -> N is a data gap, not money arriving.
func rose(before, after *int, min int) bool {
	return before != nil && after != nil && *after-*before >= min
}

// recordSmartInflow compares cand's freshly applied GMGN counts with the last
// reading for its pool, journals an inflow event, and stores the new reading.
// Called right after cand.ApplyGmgn, so it only ever sees pools that passed
// Screen, dedup and every earlier gate. A write error is logged and ignored.
func (s *Scanner) recordSmartInflow(mp meteora.ModeParams, p meteora.Pool, cand *meteora.Candidate) {
	if s.cfg.SmartInflowShadowPath == "" || cand == nil || cand.Pool == "" {
		return
	}
	now := s.clock()
	if s.smartLast == nil {
		s.smartLast = map[string]smartReading{}
		s.smartRowAt = map[string]time.Time{}
	}
	for pool, r := range s.smartLast {
		if now.Sub(r.at) >= smartInflowBaselineMax {
			delete(s.smartLast, pool)
		}
	}
	for pool, at := range s.smartRowAt {
		if now.Sub(at) >= smartInflowDedup {
			delete(s.smartRowAt, pool)
		}
	}

	prev, hadPrev := s.smartLast[cand.Pool]
	cur := smartReading{smart: cand.GmgnSmartWallets, kol: cand.GmgnKolWallets, at: now}
	// Keep a known count when this reading lacks it, so one blank answer does
	// not erase the baseline the next reading is compared against.
	if hadPrev {
		if cur.smart == nil {
			cur.smart = prev.smart
		}
		if cur.kol == nil {
			cur.kol = prev.kol
		}
	}
	s.smartLast[cand.Pool] = cur
	if !hadPrev {
		return
	}
	if !rose(prev.smart, cand.GmgnSmartWallets, smartInflowMinSmart) &&
		!rose(prev.kol, cand.GmgnKolWallets, smartInflowMinKol) {
		return
	}
	if _, recent := s.smartRowAt[cand.Pool]; recent {
		return
	}
	s.smartRowAt[cand.Pool] = now

	data, err := json.Marshal(smartInflowRow{
		TS: now.Unix(), Pool: cand.Pool, Mint: cand.BaseMint, Symbol: cand.BaseSymbol,
		SmartBefore: prev.smart, SmartAfter: cand.GmgnSmartWallets,
		KolBefore: prev.kol, KolAfter: cand.GmgnKolWallets,
		Mode: mp.Mode, ActiveTVL: p.ActiveTVL, FeeActiveTVL5m: p.FeeActiveTVLRatio, FeeWindow: mp.Timeframe,
	})
	if err != nil {
		log.Printf("smart-inflow-shadow: encode: %v", err)
		return
	}
	if err := appendLine(s.cfg.SmartInflowShadowPath, data); err != nil {
		log.Printf("smart-inflow-shadow: %v", err)
		return
	}
	log.Printf("scanner[%s]: smart-inflow shadow %s (%s) smart %s->%s kol %s->%s",
		mp.Mode, cand.BaseSymbol, shortPool(cand.Pool), fmtCount(prev.smart), fmtCount(cand.GmgnSmartWallets),
		fmtCount(prev.kol), fmtCount(cand.GmgnKolWallets))
	requestPricePath(mp.Mode, cand, now)
}

// requestPricePath asks the candidate price-path sampler (dlmm_price_path.py)
// to follow an inflow pool, by appending a row to the same candidate watch
// journal recordSolanaWatch writes. The sampler keys on pool and keeps a
// candidate for CANDIDATE_MAX_AGE_SECONDS after the row, so this buys the
// first 30 minutes of path, not the 24h paper horizon. Best effort.
func requestPricePath(mode string, c *meteora.Candidate, now time.Time) {
	if os.Getenv("DRY_RUN") == "true" || c.SolIsX || c.BaseMint == meteora.SolMint ||
		!watchAddress.MatchString(c.Pool) || !watchAddress.MatchString(c.BaseMint) {
		return
	}
	switch mode {
	case "turnover", "pulse", "casual", "multiday":
	default:
		return
	}
	stamp := now.Unix()
	key, _ := json.Marshal([]any{mode, c.Pool, stamp, "smart_inflow"})
	digest := sha256.Sum256(key)
	row, err := json.Marshal(map[string]any{
		"id": "watch:" + hex.EncodeToString(digest[:]), "ts": stamp, "pool": c.Pool, "mode": mode,
		"source": "smart_inflow_shadow", "candidate": map[string]any{"base_mint": c.BaseMint, "sol_is_x": false},
	})
	if err != nil {
		return
	}
	file := solanaWatchPath()
	if file == "" || os.MkdirAll(filepath.Dir(file), 0700) != nil {
		return
	}
	f, err := os.OpenFile(file, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0600)
	if err != nil {
		return
	}
	defer f.Close()
	if syscall.Flock(int(f.Fd()), syscall.LOCK_EX|syscall.LOCK_NB) != nil {
		return
	}
	defer syscall.Flock(int(f.Fd()), syscall.LOCK_UN)
	_, _ = f.Write(append(row, '\n'))
}

func appendLine(file string, data []byte) error {
	if err := os.MkdirAll(filepath.Dir(file), 0700); err != nil {
		return err
	}
	f, err := os.OpenFile(file, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0600)
	if err != nil {
		return err
	}
	defer f.Close()
	_, err = f.Write(append(data, '\n'))
	return err
}

func fmtCount(n *int) string {
	if n == nil {
		return "?"
	}
	return strconv.Itoa(*n)
}

func shortPool(pool string) string {
	if len(pool) > 8 {
		return pool[:8]
	}
	return pool
}
