package main

import (
	"context"
	"errors"
	"fmt"
	"strings"
	"testing"
	"time"
)

// fakeCollector records each mode it is asked for and answers with a small snapshot.
type fakeCollector struct {
	calls    []string
	slowFail bool
	n        int
}

func (f *fakeCollector) run(_ context.Context, mode string, zones []string) ([]byte, error) {
	f.n++
	f.calls = append(f.calls, mode)
	switch mode {
	case "fast":
		return []byte(fmt.Sprintf(`{"collected_at":%d,"journal":[],"nav":{"ts":%d}}`, f.n, f.n)), nil
	case "slow":
		if f.slowFail {
			return nil, errors.New("killed")
		}
		return []byte(fmt.Sprintf(`{"collected_at":%d,"by_tz":{"UTC":{"run":%d}},"nav_bridge":{"run":%d},"live":{"dust":{}},"robinhood":{},"zones":%q}`, f.n, f.n, f.n, strings.Join(zones, ","))), nil
	case "daily":
		return []byte(fmt.Sprintf(`{"collected_at":%d,"by_tz":{%q:{"north_star":{"days":[]}}}}`, f.n, zones[0])), nil
	}
	return nil, errors.New("unknown mode " + mode)
}

func TestRefreshRunsSlowPanelsOnTheirOwnPeriod(t *testing.T) {
	f := &fakeCollector{}
	s := &server{runCollector: f.run}

	s.refresh()
	if got := strings.Join(f.calls, ","); got != "slow,fast" {
		t.Fatalf("first refresh must collect both halves, got %s", got)
	}
	d := s.data
	if d["nav_bridge"].(map[string]any)["run"] != 1.0 || d["slow_collected_at"] != 1.0 || d["collected_at"] != 2.0 {
		t.Fatalf("merged snapshot wrong: %v", d)
	}
	if _, leaked := d["zones"]; leaked {
		t.Fatal("only slowKeys may be merged from the slow snapshot")
	}

	s.refresh()
	if got := strings.Join(f.calls, ","); got != "slow,fast,fast" {
		t.Fatalf("slow panels refreshed before their period: %s", got)
	}
	if s.data["nav_bridge"].(map[string]any)["run"] != 1.0 || s.data["collected_at"] != 3.0 {
		t.Fatalf("slow panels not retained across a fast refresh: %v", s.data)
	}

	s.slowAt = time.Now().Add(-slowPeriod)
	s.refresh()
	if got := strings.Join(f.calls, ","); got != "slow,fast,fast,slow,fast" {
		t.Fatalf("slow panels not refreshed once due: %s", got)
	}
}

func TestSlowFailureKeepsLastGoodPanelsAndRetries(t *testing.T) {
	f := &fakeCollector{}
	s := &server{runCollector: f.run}
	s.refresh()
	f.slowFail = true
	s.slowAt = time.Now().Add(-slowPeriod)
	s.refresh()
	if s.data["nav_bridge"].(map[string]any)["run"] != 1.0 || s.failure == "" {
		t.Fatalf("failed slow run must keep the last panels and say so: %v %q", s.data, s.failure)
	}
	s.refresh()
	if got := strings.Join(f.calls, ","); got != "slow,fast,slow,fast,slow,fast" {
		t.Fatalf("failed slow run must be retried on the next tick: %s", got)
	}
	f.slowFail = false
	s.refresh()
	if s.failure != "" || s.data["nav_bridge"].(map[string]any)["run"] != 7.0 {
		t.Fatalf("recovery must clear the failure: %q %v", s.failure, s.data)
	}
}

func TestFirstSlowFailureStillServesFastPanels(t *testing.T) {
	f := &fakeCollector{slowFail: true}
	s := &server{runCollector: f.run}
	s.refresh()
	if s.data == nil || s.data["nav"] == nil || s.failure == "" {
		t.Fatalf("fast panels must be served with a failure note: %v %q", s.data, s.failure)
	}
	if _, ok := s.data["by_tz"]; ok {
		t.Fatal("no slow panels exist yet")
	}
}

func TestOnDemandZoneSurvivesTheNextFastRefresh(t *testing.T) {
	f := &fakeCollector{}
	s := &server{runCollector: f.run, profile: "unused"}
	s.refresh()
	if panels, problem := s.daily(s.data, "Asia/Jakarta"); panels == nil {
		t.Fatalf("zone not computed: %s", problem)
	}
	s.refresh()
	if zonePanels(s.data, "Asia/Jakarta") == nil || zonePanels(s.data, "UTC") == nil {
		t.Fatalf("zone dropped by the fast refresh: %v", s.data["by_tz"])
	}
	s.slowAt = time.Now().Add(-slowPeriod)
	s.refresh()
	if !strings.Contains(fmt.Sprint(s.slow["zones"]), "Asia/Jakarta") {
		t.Fatalf("next slow run must include the zone: %v", s.slow["zones"])
	}
}
