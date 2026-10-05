package store

import (
	"context"
	"encoding/json"
	"errors"
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
