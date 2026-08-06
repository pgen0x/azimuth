package store

import (
	"context"
	"encoding/json"
	"strings"
	"sync"
	"time"

	redis "github.com/redis/go-redis/v9"
)

// Seen tracks which pools have already been emitted, so each qualifying pool
// fires exactly once until its TTL lapses. Backed by Redis when configured,
// otherwise an in-memory map (single-instance).
type Seen struct {
	rdb *redis.Client
	key string
	ttl time.Duration
	mu  sync.Mutex
	mem map[string]time.Time
}

// New builds a Seen store. addr == "" selects the in-memory backend.
func New(addr, key string, ttl time.Duration) *Seen {
	s := &Seen{key: key, ttl: ttl, mem: make(map[string]time.Time)}
	if addr != "" {
		s.rdb = redis.NewClient(&redis.Options{Addr: addr})
	}
	return s
}

// MarkIfNew atomically records id and reports whether it was newly added
// (true == first time we've seen it, caller should emit a signal).
func (s *Seen) MarkIfNew(ctx context.Context, id string) (bool, error) {
	return s.MarkIfNewTTL(ctx, id, s.ttl)
}

// MarkIfNewTTL is MarkIfNew with a caller-chosen window — the scanner passes a
// shorter TTL for turnover mode so a still-qualifying pool re-signals after a
// fast cycle ends instead of being silenced for the full default window.
func (s *Seen) MarkIfNewTTL(ctx context.Context, id string, ttl time.Duration) (bool, error) {
	if ttl <= 0 {
		ttl = s.ttl
	}
	if s.rdb != nil {
		// One key per pool with its own TTL. A Redis SET can only expire as a
		// whole, so the old SAdd+Expire refreshed the entire set's TTL on every
		// write — the rolling window never lapsed while the scanner kept polling,
		// so once-seen pools were deduped forever and never re-signalled.
		// SetNX gives each pool an independent SEEN_TTL window that actually ages out.
		ok, err := s.rdb.SetNX(ctx, s.key+":"+id, 1, ttl).Result()
		if err != nil {
			return false, err
		}
		return ok, nil
	}

	s.mu.Lock()
	defer s.mu.Unlock()
	now := time.Now()
	// Lazy expiry of the in-memory map (values are expiry deadlines).
	for k, t := range s.mem {
		if now.After(t) {
			delete(s.mem, k)
		}
	}
	if _, ok := s.mem[id]; ok {
		return false, nil
	}
	s.mem[id] = now.Add(ttl)
	return true, nil
}

// PoolCloseStats summarizes a pool's close journal written by dlmm_monitor.py
// (sol:dlmm:history:pool:<pool> — last 10 closes, 30d TTL). Returns ok=false
// when there is no history, no Redis backend, or the read fails: absent data
// must read as "unknown", never as "clean record" (fail-open convention).
func (s *Seen) PoolCloseStats(ctx context.Context, pool string) (closes int, netPnlSOL float64, ok bool) {
	if s.rdb == nil {
		return 0, 0, false
	}
	entries, err := s.rdb.LRange(ctx, "sol:dlmm:history:pool:"+pool, 0, 9).Result()
	if err != nil || len(entries) == 0 {
		return 0, 0, false
	}
	for _, e := range entries {
		var rec struct {
			PnlSOL float64 `json:"pnl_sol"`
		}
		if json.Unmarshal([]byte(e), &rec) != nil {
			continue
		}
		closes++
		netPnlSOL += rec.PnlSOL
	}
	return closes, netPnlSOL, closes > 0
}

// CooldownRemaining reports how long a token symbol is still under the
// monitor's re-entry cooldown (sol:dlmm:cooldown:<SYMBOL>, written by
// dlmm_monitor.py on every close). Zero means not cooling or unknown: the
// in-memory backend and Redis errors read as "no cooldown" (fail-open) —
// the deploy-time pipeline check stays the enforcing layer.
func (s *Seen) CooldownRemaining(ctx context.Context, symbol string) time.Duration {
	if s.rdb == nil || symbol == "" {
		return 0
	}
	d, err := s.rdb.TTL(ctx, "sol:dlmm:cooldown:"+strings.ToUpper(symbol)).Result()
	if err != nil || d <= 0 {
		return 0
	}
	return d
}

// CachedCandles reads a Robinhood pool's cached GeckoTerminal candle set into
// out (a pointer, JSON-decoded) and reports whether it was served. ok=false
// covers no Redis backend, no cached entry and an unreadable/undecodable value
// alike: every one of them means "fetch it", which is the only safe reading —
// the indicator math must never run on a half-decoded series.
//
// The key namespace is rh:ohlcv:<pool> so it cannot collide with the Solana
// keys (sol:dlmm:*) or the seen keys sharing this instance. Pool addresses
// arrive from GeckoTerminal in mixed case, so they are lowercased: the same
// pool reached from two feeds must be one cache entry, not two.
//
// Why persist candles at all: the daemon restarted twice on 2026-08-05 and each
// restart re-fetched every pool's 15m candles from scratch, which is precisely
// the request burst that earns GT's 429 on a ~10 req/min public tier.
func (s *Seen) CachedCandles(ctx context.Context, pool string, out any) bool {
	if s.rdb == nil || pool == "" {
		return false
	}
	b, err := s.rdb.Get(ctx, "rh:ohlcv:"+strings.ToLower(pool)).Bytes()
	if err != nil || len(b) == 0 {
		return false
	}
	return json.Unmarshal(b, out) == nil
}

// PutCandles caches v as this pool's candle set for ttl. Best-effort and
// silent by design: the caller has already served the value from its in-memory
// half, so a Redis hiccup here costs a future request, never a correct answer,
// and logging it would repeat once per pool per TTL.
func (s *Seen) PutCandles(ctx context.Context, pool string, v any, ttl time.Duration) {
	if s.rdb == nil || pool == "" || ttl <= 0 {
		return
	}
	b, err := json.Marshal(v)
	if err != nil {
		return
	}
	s.rdb.Set(ctx, "rh:ohlcv:"+strings.ToLower(pool), b, ttl)
}

// youngPoolPrefix namespaces the pulse ladder's carried young-pool registry.
// One key per pool rather than one hash for the set, because the registry is
// organized on AGE and per-key TTLs let Redis do that eviction itself: an entry
// written with the pool's remaining watch window expires exactly when the
// in-process prune would have dropped it.
const youngPoolPrefix = "rh:young:"

// LoadYoungPools returns every carried young-pool record still live in Redis,
// as raw JSON for the caller to decode. Read once at startup: the registry is
// the pulse ladder's only view of the 1h-24h band (no feed can answer "which
// WETH pools are three hours old"), and it lived in process memory alone — so
// a restart blinded the mode for an hour and starved it for a day while ~2400
// carried pools rebuilt from scratch. Measured 2026-08-07.
//
// Best-effort: a missing backend or a failed scan returns what it has. An
// empty result is indistinguishable from a cold cache on purpose — both mean
// "carry nothing yet", which is where the mode already starts.
func (s *Seen) LoadYoungPools(ctx context.Context) [][]byte {
	if s.rdb == nil {
		return nil
	}
	var (
		out    [][]byte
		cursor uint64
	)
	for {
		keys, next, err := s.rdb.Scan(ctx, cursor, youngPoolPrefix+"*", 500).Result()
		if err != nil {
			return out
		}
		if len(keys) > 0 {
			vals, err := s.rdb.MGet(ctx, keys...).Result()
			if err != nil {
				return out
			}
			for _, v := range vals {
				// A key can expire between the SCAN and the MGET; that reads as nil.
				if sv, ok := v.(string); ok && sv != "" {
					out = append(out, []byte(sv))
				}
			}
		}
		cursor = next
		if cursor == 0 {
			return out
		}
	}
}

// SaveYoungPool persists one registry entry for ttl. Silent and best-effort for
// the same reason PutCandles is: the in-process registry has already recorded
// the pool, so a Redis hiccup costs a future restart's head start, never a
// candidate this cycle.
func (s *Seen) SaveYoungPool(ctx context.Context, addr string, v any, ttl time.Duration) {
	if s.rdb == nil || addr == "" || ttl <= 0 {
		return
	}
	b, err := json.Marshal(v)
	if err != nil {
		return
	}
	s.rdb.Set(ctx, youngPoolPrefix+strings.ToLower(addr), b, ttl)
}

// Unmark removes id from the seen set so a failed emit can retry on the next
// poll. Called when webhook delivery fails after MarkIfNew already recorded it.
func (s *Seen) Unmark(ctx context.Context, id string) {
	if s.rdb != nil {
		s.rdb.Del(ctx, s.key+":"+id)
		return
	}
	s.mu.Lock()
	delete(s.mem, id)
	s.mu.Unlock()
}
