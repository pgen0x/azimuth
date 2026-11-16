package scanner

import (
	"encoding/json"
	"log"
	"os"
	"path/filepath"
	"time"

	"github.com/pgen0x/azimuth/internal/meteora"
)

// supplyShadowRow is one line of the pulse near-miss journal.
type supplyShadowRow struct {
	TS             int64   `json:"ts"`
	Pool           string  `json:"pool"`
	Symbol         string  `json:"symbol"`
	Mint           string  `json:"mint"`
	FeeActiveTVL5m float64 `json:"fee_active_tvl_5m"`
	ActiveTVL      float64 `json:"active_tvl"`
	TVL            float64 `json:"tvl"`
	Volume5m       float64 `json:"volume_5m"`
	Mode           string  `json:"mode"`
}

// supplyShadowOn reports whether mp's cycle feeds the supply shadow.
func (s *Scanner) supplyShadowOn(mp meteora.ModeParams) bool {
	return mp.Mode == "pulse" && s.cfg.SupplyShadowPath != "" && s.cfg.PulseNearMissFeeFloor > 0 &&
		mp.MinFeeActiveTVL > 0 && s.cfg.PulseNearMissFeeFloor < mp.MinFeeActiveTVL
}

// fetchPools returns the page to screen and the page to journal near misses
// from. With the shadow off they are the same strict query (shadow nil).
//
// With it on, the discovery query's fee/active-TVL bar drops to the near-miss
// floor: the API applies filter_by BEFORE paging, so the strict query can never
// return the band the shadow measures. Screen still enforces the real bar, so
// a widened page that is NOT full holds every strict passer and is screened
// as-is. A FULL widened page may have been truncated by the sort, pushing out
// pools the strict query would have returned; then the strict query runs too
// (one extra request, only on a full page) and ITS page is what gets screened,
// so live entries are never displaced by the shadow.
func (s *Scanner) fetchPools(mp meteora.ModeParams) (screen, shadow []meteora.Pool, err error) {
	if !s.supplyShadowOn(mp) {
		screen, err = meteora.FetchTopPools(s.cfg.DiscoverURL, mp)
		return screen, nil, err
	}
	widened := mp
	widened.PrefilterFeeActiveTVL = s.cfg.PulseNearMissFeeFloor
	shadow, err = meteora.FetchTopPools(s.cfg.DiscoverURL, widened)
	if err != nil {
		// The shadow must never cost an entry cycle: fall back to the strict query.
		log.Printf("supply-shadow: widened %s query failed, screening strict page: %v", mp.Mode, err)
		screen, err = meteora.FetchTopPools(s.cfg.DiscoverURL, mp)
		return screen, nil, err
	}
	if len(shadow) < meteora.DiscoverPageSize {
		return shadow, shadow, nil
	}
	log.Printf("supply-shadow: widened %s query returned full page (%d); re-fetching strict page for screening", mp.Mode, len(shadow))
	screen, err = meteora.FetchTopPools(s.cfg.DiscoverURL, mp)
	return screen, shadow, err
}

func (s *Scanner) clock() time.Time {
	if s.now != nil {
		return s.now()
	}
	return time.Now()
}

// recordSupplyShadow journals a pulse pool that failed ONLY the fee/active-TVL
// gate with a ratio at or above PULSE_NEARMISS_FEE_FLOOR. It measures whether
// lowering that bar would add good supply, and is logging only: it is fed the
// widened discovery page (fetchPools) and never touches dedup, dispatch or the
// pipeline. At most one row per pool per PULSE_SEEN_TTL (in-memory, so a
// restart may repeat a row — the reader dedups by pool). A write error is
// logged and swallowed; it must never break the cycle.
func (s *Scanner) recordSupplyShadow(p meteora.Pool, mp meteora.ModeParams) {
	if s.cfg.SupplyShadowPath == "" || s.cfg.PulseNearMissFeeFloor <= 0 {
		return
	}
	ratio, ok := meteora.NearMissFee(p, mp, s.cfg.PulseNearMissFeeFloor)
	if !ok {
		return
	}
	now := s.clock()
	ttl := s.cfg.PulseSeenTTL
	if s.nearMissSeen == nil {
		s.nearMissSeen = map[string]time.Time{}
	}
	if last, seen := s.nearMissSeen[p.PoolAddress]; seen && now.Sub(last) < ttl {
		return
	}
	for pool, last := range s.nearMissSeen { // bound the map to one TTL of pools
		if now.Sub(last) >= ttl {
			delete(s.nearMissSeen, pool)
		}
	}
	s.nearMissSeen[p.PoolAddress] = now

	base := p.TokenX
	if p.TokenX.Address == meteora.SolMint {
		base = p.TokenY
	}
	data, err := json.Marshal(supplyShadowRow{
		TS: now.Unix(), Pool: p.PoolAddress, Symbol: base.Symbol, Mint: base.Address,
		FeeActiveTVL5m: ratio, ActiveTVL: p.ActiveTVL, TVL: p.TVL, Volume5m: p.VolumeWindow,
		Mode: mp.Mode,
	})
	if err != nil {
		log.Printf("supply-shadow: encode: %v", err)
		return
	}
	file := s.cfg.SupplyShadowPath
	if err = os.MkdirAll(filepath.Dir(file), 0700); err != nil {
		log.Printf("supply-shadow: mkdir: %v", err)
		return
	}
	f, err := os.OpenFile(file, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0600)
	if err != nil {
		log.Printf("supply-shadow: open: %v", err)
		return
	}
	defer f.Close()
	if _, err = f.Write(append(data, '\n')); err != nil {
		log.Printf("supply-shadow: write: %v", err)
	}
}
