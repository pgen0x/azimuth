package store

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	redis "github.com/redis/go-redis/v9"
	"testing"
	"time"
)

type historyHook struct {
	entries []string
	cash    string
}

func (h *historyHook) DialHook(n redis.DialHook) redis.DialHook { return n }
func (h *historyHook) ProcessPipelineHook(n redis.ProcessPipelineHook) redis.ProcessPipelineHook {
	return n
}
func (h *historyHook) ProcessHook(n redis.ProcessHook) redis.ProcessHook {
	return func(ctx context.Context, cmd redis.Cmder) error {
		switch c := cmd.(type) {
		case *redis.StringSliceCmd:
			c.SetVal(h.entries)
		case *redis.StringCmd:
			if h.cash == "" {
				return errors.New("missing")
			}
			c.SetVal(h.cash)
		}
		return nil
	}
}
func TestPoolHistoryCashProvenance(t *testing.T) {
	now := time.Now().Unix()
	client := redis.NewClient(&redis.Options{Addr: "unused:0"})
	defer client.Close()
	hook := &historyHook{}
	client.AddHook(hook)
	seen := &Seen{rdb: client}
	ctx := context.Background()
	row, _ := json.Marshal(map[string]any{"ts": now - 10, "pnl_sol": 0.01})
	hook.entries = []string{string(row)}
	h := seen.PoolCloseHistory(ctx, "P")
	if h == nil || h.Net != nil || h.Mark == nil || *h.Mark != .01 {
		t.Fatal("legacy mark promoted to cash", h)
	}
	net := -.02
	good := PoolHistory{Closes: 1, Net: &net, LastClose: now - 10, ObservedAt: float64(now), Basis: "matched_refund_cash"}
	set := func(c PoolHistory) { raw, _ := json.Marshal(map[string]PoolHistory{"P": c}); hook.cash = string(raw) }
	set(good)
	h = seen.PoolCloseHistory(ctx, "P")
	if h.Net == nil || *h.Net != net || h.Basis != "matched_refund_cash" {
		t.Fatal("valid cash missing", h)
	}
	bad := []PoolHistory{good, good, good, good, good, good}
	bad[0].LastClose--
	bad[1].Closes++
	bad[2].ObservedAt -= 1000
	bad[3].ObservedAt += 60
	bad[4].Net = nil
	bad[5].Basis = "pre_swap_mark_only"
	for _, c := range bad {
		set(c)
		if seen.PoolCloseHistory(ctx, "P").Net != nil {
			t.Fatal("stale/incomplete cash accepted", c)
		}
	}
	lo, hi := .001, .002
	bounds := PoolHistory{Closes: 1, Lower: &lo, Upper: &hi, LastClose: now - 10, ObservedAt: float64(now), Basis: "matched_refund_cash_bounds"}
	set(bounds)
	if h = seen.PoolCloseHistory(ctx, "P"); h.Net != nil || h.Lower == nil || *h.Lower != lo || h.Upper == nil || *h.Upper != hi || h.Basis != bounds.Basis {
		t.Fatal("bounds lost or promoted to exact cash", h)
	}
	invalid := []PoolHistory{bounds, bounds, bounds, bounds, bounds, bounds, bounds}
	invalid[0].Lower = nil
	invalid[1].Upper = nil
	invalid[2].Lower, invalid[2].Upper = &hi, &lo
	invalid[3].ObservedAt -= 1000
	invalid[4].LastClose--
	invalid[5].Net = &net
	invalid[6].Closes++
	for _, c := range invalid {
		set(c)
		if h = seen.PoolCloseHistory(ctx, "P"); h.Lower != nil || h.Upper != nil || h.Net != nil {
			t.Fatal("invalid or stale bounds accepted", c)
		}
	}

	upper := -.00001
	upperOnly := PoolHistory{Closes: 1, Upper: &upper, LastClose: now - 10, ObservedAt: float64(now), Basis: "nonpositive_cash_upper_bound"}
	set(upperOnly)
	if h = seen.PoolCloseHistory(ctx, "P"); h.Upper == nil || *h.Upper != upper || h.Lower != nil || h.Net != nil || h.Basis != upperOnly.Basis {
		t.Fatal("upper-only loss lost or fabricated exact cash", h)
	}
	invalidUpper := []PoolHistory{upperOnly, upperOnly, upperOnly, upperOnly}
	invalidUpper[0].Upper = &hi
	invalidUpper[1].Lower = &lo
	invalidUpper[2].Net = &net
	invalidUpper[3].ObservedAt -= 1000
	for _, c := range invalidUpper {
		set(c)
		if h = seen.PoolCloseHistory(ctx, "P"); h.Upper != nil || h.Net != nil {
			t.Fatal("invalid upper-only history accepted", c)
		}
	}

	net = 0
	set(good)
	if h = seen.PoolCloseHistory(ctx, "P"); h.Net == nil || *h.Net != 0 {
		t.Fatal("known zero lost")
	}
	row, _ = json.Marshal(map[string]any{"ts": now - 10, "pnl_sol": nil})
	hook.entries = []string{string(row)}
	hook.cash = ""
	if h = seen.PoolCloseHistory(ctx, "P"); h.Mark != nil || h.Net != nil {
		t.Fatal("unknown converted to zero")
	}
}

func TestRecoveredCloseHistoryBindsOriginalJournal(t *testing.T) {
	now := time.Now().Unix()
	client := redis.NewClient(&redis.Options{Addr: "unused:0"})
	defer client.Close()
	hook := &historyHook{entries: []string{`{"ts":` + fmt.Sprint(now-100) + `,"pnl_sol":0.01}`}}
	client.AddHook(hook)
	seen := &Seen{rdb: client}
	n, ts, upper := 1, now-100, -.000025
	cash := PoolHistory{Closes: 2, LastClose: now - 10, JournalCloses: &n, JournalLastClose: &ts,
		ObservedAt: float64(now), Upper: &upper, Basis: "nonpositive_cash_upper_bound"}
	set := func() { raw, _ := json.Marshal(map[string]PoolHistory{"P": cash}); hook.cash = string(raw) }
	set()
	h := seen.PoolCloseHistory(context.Background(), "P")
	if h == nil || h.Closes != 2 || h.Upper == nil || *h.Upper != upper || h.Mark != nil {
		t.Fatal("recovered loss missing", h)
	}
	ts-- // Journal changed: cache must not override it.
	set()
	h = seen.PoolCloseHistory(context.Background(), "P")
	if h.Closes != 1 || h.Upper != nil || h.Mark == nil {
		t.Fatal("unmatched journal accepted", h)
	}
	n, ts = 0, 0
	hook.entries = nil
	set()
	h = seen.PoolCloseHistory(context.Background(), "P")
	if h == nil || h.Closes != 2 || h.Upper == nil {
		t.Fatal("recovered-only history missing", h)
	}
	cash.ObservedAt -= 901
	set()
	if h = seen.PoolCloseHistory(context.Background(), "P"); h != nil {
		t.Fatal("expired recovered-only history accepted", h)
	}
}
