package store

import (
	"context"
	"errors"
	redis "github.com/redis/go-redis/v9"
	"testing"
	"time"
)

type cooldownHook map[string]time.Duration

func (h cooldownHook) DialHook(next redis.DialHook) redis.DialHook { return next }
func (h cooldownHook) ProcessPipelineHook(next redis.ProcessPipelineHook) redis.ProcessPipelineHook {
	return next
}
func (h cooldownHook) ProcessHook(next redis.ProcessHook) redis.ProcessHook {
	return func(ctx context.Context, cmd redis.Cmder) error {
		key := cmd.Args()[1].(string)
		ttl, ok := h[key]
		if !ok {
			return errors.New("unavailable")
		}
		cmd.(*redis.DurationCmd).SetVal(ttl)
		return nil
	}
}

func TestSolanaCooldownScopes(t *testing.T) {
	for _, scope := range []string{"YAP", "mint:MintCase", "pool:PoolCase"} {
		t.Run(scope, func(t *testing.T) {
			client := redis.NewClient(&redis.Options{Addr: "unused:0"})
			defer client.Close()
			hook := cooldownHook{"sol:dlmm:cooldown:" + scope: time.Minute}
			client.AddHook(hook)
			seen := &Seen{rdb: client}
			if got := seen.CooldownRemaining(context.Background(), "yap", "MintCase", "PoolCase"); got != time.Minute {
				t.Fatalf("cooldown %s was missed: %v", scope, got)
			}
			hook["sol:dlmm:cooldown:"+scope] = -2 * time.Second
			if got := seen.CooldownRemaining(context.Background(), "yap", "MintCase", "PoolCase"); got != 0 {
				t.Fatalf("expired cooldown still blocks: %v", got)
			}
		})
	}
	if got := (&Seen{}).CooldownRemaining(context.Background(), "", "MintCase", "PoolCase"); got != 0 {
		t.Fatalf("memory backend unexpectedly blocks: %v", got)
	}
}
