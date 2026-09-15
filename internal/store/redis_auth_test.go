package store

import (
	"context"
	"os"
	"testing"
	"time"
)

// Read-only integration check against a password-protected Redis server.
func TestRedisAuthentication(t *testing.T) {
	addr := os.Getenv("REDIS_AUTH_TEST_ADDR")
	password := os.Getenv("REDISCLI_AUTH")
	if addr == "" || password == "" {
		t.Skip("requires REDIS_AUTH_TEST_ADDR and REDISCLI_AUTH")
	}
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	s := New(addr, "auth-test", time.Minute)
	defer s.rdb.Close()
	if err := s.rdb.Ping(ctx).Err(); err != nil {
		t.Fatal("authenticated Redis ping failed")
	}
	t.Setenv("REDISCLI_AUTH", "")
	unauth := New(addr, "auth-test", time.Minute)
	defer unauth.rdb.Close()
	if unauth.rdb.Ping(ctx).Err() == nil {
		t.Fatal("test Redis must reject unauthenticated clients")
	}
}
