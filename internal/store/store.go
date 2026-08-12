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

// RobinhoodCooldown reports how long this pool (or its token) is still blocked
// from re-entry, and why. Zero duration means clear.
//
// The keys are written by uni_monitor.py when a resting wall is run over —
// rh:cooldown:pool:<pool> and rh:cooldown:token:<base>, the venue's port of the
// Solana monitor's sol:dlmm:cooldown:* block. Only the FILL class of close
// writes them: `ladder idle` and `ladder stale` are re-pins by design, and
// cooling those off would switch the ladder modes off entirely.
//
// Both arguments are lowercased here because the two sides spell addresses
// differently — GeckoTerminal returns mixed case, the monitor writes what the
// executor reported — and a cooldown that missed on capitalization would read
// as "clear" every time.
//
// Fails OPEN (returns 0) with no Redis backend or on any read error, matching
// this venue's gate convention: the position cap and the screen still stand
// between an unknown cooldown and a deploy.
func (s *Seen) RobinhoodCooldown(ctx context.Context, pool, token string) (time.Duration, string) {
	// Nil receiver included in the fail-open case: this is read from the deploy
	// walk, which a caller may reach with no store wired at all (the scanner
	// tests build a Scanner directly). A risk brake must not be the thing that
	// panics the daemon.
	if s == nil || s.rdb == nil {
		return 0, ""
	}
	for _, k := range []struct{ kind, id string }{{"pool", pool}, {"token", token}} {
		if k.id == "" {
			continue
		}
		key := "rh:cooldown:" + k.kind + ":" + strings.ToLower(k.id)
		d, err := s.rdb.TTL(ctx, key).Result()
		if err != nil || d <= 0 {
			continue
		}
		reason, _ := s.rdb.Get(ctx, key).Result()
		return d, reason
	}
	return 0, ""
}

// RobinhoodSecurityTTL is how long one POSITIVE contract-security detection
// silences a token. Not permanent, on the same reasoning that retired the
// permanent Solana rug blacklist (2026-08-07): a monotonic deny-list only ever
// grows and eventually eats the recycling universe. A week is long past the
// life of the memecoins this venue screens.
const RobinhoodSecurityTTL = 7 * 24 * time.Hour

// rhSecKey namespaces the sticky security verdict. Lowercased for the same
// reason as RobinhoodCooldown: GeckoTerminal and the gateway spell the same
// address in different cases, and a verdict that missed on capitalization
// would read as "clean".
func rhSecKey(token string) string {
	return "rh:sec:blacklist:" + strings.ToLower(token)
}

// SecurityBlacklisted reports the stored reason a token was hard-rejected by
// the contract-security gate, or "" when it is clear.
//
// This is what makes a positive detection STICK. GMGN answers per call, and on
// 2026-08-09 BLINK read `honeypot` on ten cycles and unknown on two — the gate
// fails open on unknown, so those two minted into it, and one of those
// positions can no longer be closed at all (`collect` reverts TF against a
// token that blocks transfers). A verdict that only holds for the cycle that
// observed it is not a gate.
//
// With no Redis backend there is nowhere to remember, so this returns "" and
// the live gate stays the only layer. Where a verdict IS recorded it outranks
// a later "unknown": affirmative evidence must not expire because the next
// request timed out.
func (s *Seen) SecurityBlacklisted(ctx context.Context, token string) string {
	if s == nil || s.rdb == nil || token == "" {
		return ""
	}
	reason, err := s.rdb.Get(ctx, rhSecKey(token)).Result()
	if err != nil {
		return ""
	}
	return reason
}

// BlacklistSecurity records a positive contract-security detection for a token.
// Best-effort: a write failure only costs the stickiness, and the live gate has
// already rejected the candidate on the call that produced reason.
func (s *Seen) BlacklistSecurity(ctx context.Context, token, reason string) {
	if s == nil || s.rdb == nil || token == "" || reason == "" {
		return
	}
	s.rdb.Set(ctx, rhSecKey(token), reason, RobinhoodSecurityTTL)
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
