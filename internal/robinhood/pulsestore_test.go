package robinhood

import (
	"context"
	"encoding/json"
	"testing"
	"time"
)

// fakeWatchStore is the persistent half kept in a map, so a "restart" is just a
// resetWatch() with the same store still installed.
type fakeWatchStore struct {
	m    map[string][]byte
	ttls map[string]time.Duration
}

func newFakeWatchStore(t *testing.T) *fakeWatchStore {
	t.Helper()
	f := &fakeWatchStore{m: map[string][]byte{}, ttls: map[string]time.Duration{}}
	SetWatchStore(f)
	t.Cleanup(func() { SetWatchStore(nil) })
	return f
}

func (f *fakeWatchStore) LoadYoungPools(_ context.Context) [][]byte {
	out := make([][]byte, 0, len(f.m))
	for _, b := range f.m {
		out = append(out, b)
	}
	return out
}

func (f *fakeWatchStore) SaveYoungPool(_ context.Context, addr string, v any, ttl time.Duration) {
	b, err := json.Marshal(v)
	if err != nil {
		return
	}
	f.m[addr] = b
	f.ttls[addr] = ttl
}

// The point of persisting at all: a restart used to drop the whole carry, and
// entries are only useful once they are MinAge old — so the mode went blind for
// an hour and thin for a day every deploy.
func TestRestoreWatchSurvivesRestart(t *testing.T) {
	resetWatch()
	db := newFakeWatchStore(t)
	now := time.Now()

	publishYoung([]Pool{
		youngPool("0xaaa", now.Add(-3*time.Hour)),
		youngPool("0xbbb", now.Add(-90*time.Minute)),
	}, now)
	if len(db.m) != 2 {
		t.Fatalf("want both first sightings persisted, got %d", len(db.m))
	}

	// The restart: process memory is gone, the store is not.
	resetWatch()
	SetWatchStore(db)
	restoreWatch(now)

	got := addrsOf(watchWindow(PulseLadder, now))
	if len(got) != 2 {
		t.Fatalf("want the carry restored into the window, got %v", got)
	}
}

// A restored entry must age on the pool's own clock, exactly like a carried one.
func TestRestoreWatchDropsAgedOut(t *testing.T) {
	resetWatch()
	db := newFakeWatchStore(t)
	now := time.Now()

	publishYoung([]Pool{youngPool("0xold", now.Add(-2*time.Hour))}, now)

	resetWatch()
	SetWatchStore(db)
	// Restored a full day later: the entry is past watchKeep and must not land.
	restoreWatch(now.Add(watchKeep))

	watch.mu.Lock()
	defer watch.mu.Unlock()
	if len(watch.pools) != 0 {
		t.Fatalf("an entry past watchKeep must not be restored, got %d", len(watch.pools))
	}
}

// The TTL is what makes Redis expire an entry at the same moment pruneWatch
// would drop it — a fixed watchKeep would keep a 23h-old pool for another day.
func TestPersistYoungTTLIsRemainingWindow(t *testing.T) {
	resetWatch()
	db := newFakeWatchStore(t)
	now := time.Now()

	publishYoung([]Pool{youngPool("0xaaa", now.Add(-6*time.Hour))}, now)

	want := watchKeep - 6*time.Hour
	if got := db.ttls["0xaaa"]; got != want {
		t.Fatalf("want ttl %v (the pool's remaining window), got %v", want, got)
	}
}

// A live sighting outranks a stored one: the running process saw the pool for
// itself, and publishYoung's first-sighting rule is what keeps identity stable.
func TestRestoreWatchNeverOverwritesLiveEntry(t *testing.T) {
	resetWatch()
	db := newFakeWatchStore(t)
	now := time.Now()

	publishYoung([]Pool{youngPool("0xaaa", now.Add(-3*time.Hour))}, now)

	resetWatch()
	SetWatchStore(db)
	live := youngPool("0xaaa", now.Add(-2*time.Hour))
	live.Name = "live sighting"
	publishYoung([]Pool{live}, now)
	restoreWatch(now)

	watch.mu.Lock()
	defer watch.mu.Unlock()
	if got := watch.pools["0xaaa"].Name; got != "live sighting" {
		t.Fatalf("the live entry must win, got %q", got)
	}
}

// Without a store installed the registry stays exactly what it was: an
// operator running without REDIS_ADDR must see no behavior change.
func TestPublishYoungWithoutStore(t *testing.T) {
	resetWatch()
	SetWatchStore(nil)
	now := time.Now()

	publishYoung([]Pool{youngPool("0xaaa", now.Add(-2*time.Hour))}, now)
	restoreWatch(now)

	if got := addrsOf(watchWindow(PulseLadder, now)); len(got) != 1 {
		t.Fatalf("memory-only registry must still carry its own entries, got %v", got)
	}
}
