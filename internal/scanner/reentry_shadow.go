package scanner

import (
	"context"
	"encoding/json"
	"log"
	"os"
	"path/filepath"
	"time"

	"github.com/pgen0x/azimuth/internal/meteora"
)

// reentryShadowDedup bounds the "blocked" rows to one per pool per window; a
// pulse pool in cooldown is re-screened every poll and would otherwise write a
// row a minute for the whole cooldown.
const reentryShadowDedup = 10 * time.Minute

// reentryShadowBlocked is a "blocked" row of memories/dlmm_reentry_shadow.jsonl.
// The "close" rows in the same file are written by dlmm_monitor.py; the
// evaluator joins the two on pool+mint, so a blocked row stands for a
// candidate fast re-entry only when a qualifying close row precedes it.
type reentryShadowBlocked struct {
	Kind                  string  `json:"kind"`
	TS                    int64   `json:"ts"`
	Pool                  string  `json:"pool"`
	Mint                  string  `json:"mint"`
	BlockReason           string  `json:"block_reason"`
	FeeActiveTVL5m        float64 `json:"fee_active_tvl_5m"`
	ActiveTVL             float64 `json:"active_tvl"`
	CooldownRemainingSecs int64   `json:"cooldown_remaining_secs"`
}

func (s *Scanner) cooldownRemaining(ctx context.Context, symbol, mint, pool string) time.Duration {
	if s.cooldownLookup != nil {
		return s.cooldownLookup(ctx, symbol, mint, pool)
	}
	return s.seen.CooldownRemaining(ctx, symbol, mint, pool)
}

// recordReentryBlocked journals a pulse candidate that passed every Screen
// gate and was stopped ONLY by the re-entry cooldown (the cooldown check is the
// first gate after Screen, so nothing later has run yet). LOGGING ONLY: it is
// called after the reject is already decided, reads nothing back, and a write
// error is logged and swallowed. The m5-dump half of the shadow lives in
// dlmm_pipeline.py, which is where that gate runs for pulse.
func (s *Scanner) recordReentryBlocked(p meteora.Pool, cand *meteora.Candidate, cd time.Duration) {
	if s.cfg.ReentryShadowPath == "" || cand == nil {
		return
	}
	now := s.clock()
	if s.reentrySeen == nil {
		s.reentrySeen = map[string]time.Time{}
	}
	if last, ok := s.reentrySeen[cand.Pool]; ok && now.Sub(last) < reentryShadowDedup {
		return
	}
	for pool, last := range s.reentrySeen {
		if now.Sub(last) >= reentryShadowDedup {
			delete(s.reentrySeen, pool)
		}
	}
	s.reentrySeen[cand.Pool] = now

	data, err := json.Marshal(reentryShadowBlocked{
		Kind: "blocked", TS: now.Unix(), Pool: cand.Pool, Mint: cand.BaseMint,
		BlockReason: "cooldown", FeeActiveTVL5m: p.FeeActiveTVLRatio, ActiveTVL: p.ActiveTVL,
		CooldownRemainingSecs: int64(cd / time.Second),
	})
	if err != nil {
		log.Printf("reentry-shadow: encode: %v", err)
		return
	}
	file := s.cfg.ReentryShadowPath
	if err = os.MkdirAll(filepath.Dir(file), 0700); err != nil {
		log.Printf("reentry-shadow: mkdir: %v", err)
		return
	}
	f, err := os.OpenFile(file, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0600)
	if err != nil {
		log.Printf("reentry-shadow: open: %v", err)
		return
	}
	defer f.Close()
	if _, err = f.Write(append(data, '\n')); err != nil {
		log.Printf("reentry-shadow: write: %v", err)
	}
}
