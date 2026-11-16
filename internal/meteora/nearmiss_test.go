package meteora

import (
	"strings"
	"testing"
)

func TestNearMissFee(t *testing.T) {
	const floor = 0.025
	tests := []struct {
		name   string
		mutate func(*Pool)
		floor  float64
		want   bool
	}{
		{"fails only fee", func(p *Pool) { p.FeeActiveTVLRatio = 0.03 }, floor, true},
		{"fails fee at exactly the floor", func(p *Pool) { p.FeeActiveTVLRatio = floor }, floor, true},
		{"fails fee and volume", func(p *Pool) { p.FeeActiveTVLRatio = 0.03; p.VolumeWindow = 100 }, floor, false},
		{"fails fee and holders", func(p *Pool) { p.FeeActiveTVLRatio = 0.03; p.TokenX.Holders = 10 }, floor, false},
		{"passes every gate", func(p *Pool) {}, floor, false},
		{"fee below the floor", func(p *Pool) { p.FeeActiveTVLRatio = 0.02 }, floor, false},
		{"floor zero disables", func(p *Pool) { p.FeeActiveTVLRatio = 0.03 }, 0, false},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			p := pulsePool()
			tt.mutate(&p)
			if _, ok := NearMissFee(p, Pulse, tt.floor); ok != tt.want {
				_, reason := Screen(p, Pulse)
				t.Fatalf("NearMissFee = %v, want %v (Screen reason %q)", ok, tt.want, reason)
			}
		})
	}
	// A mode without the gate never reports a near miss.
	p := pulsePool()
	p.FeeActiveTVLRatio = 0.03
	if _, ok := NearMissFee(p, Turnover, floor); ok {
		t.Fatal("turnover has no fee/active-TVL gate, so it has no near miss")
	}
}

// The supply shadow widens ONLY the query's fee/active-TVL bar, and only
// downward; Screen keeps the real bar either way.
func TestBuildFiltersSupplyShadowPrefilter(t *testing.T) {
	off := buildFilters(Pulse)
	if !strings.Contains(off, "fee_active_tvl_ratio>=0.050") {
		t.Fatalf("shadow off must keep the gate's bar: %s", off)
	}
	on := Pulse
	on.PrefilterFeeActiveTVL = 0.025
	got := buildFilters(on)
	if !strings.Contains(got, "fee_active_tvl_ratio>=0.025") || strings.Contains(got, "fee_active_tvl_ratio>=0.050") {
		t.Fatalf("shadow on must push the near-miss floor: %s", got)
	}
	if strings.Replace(got, "0.025", "0.050", 1) != off {
		t.Fatalf("shadow must change only the fee/active-TVL clause\non:  %s\noff: %s", got, off)
	}
	above := Pulse
	above.PrefilterFeeActiveTVL = 0.08
	if buildFilters(above) != off {
		t.Fatal("a prefilter above the gate must never tighten the query")
	}
	noGate := Turnover
	noGate.PrefilterFeeActiveTVL = 0.025
	if strings.Contains(buildFilters(noGate), "fee_active_tvl_ratio") {
		t.Fatal("a mode without the gate must not gain the clause")
	}
	// Screen ignores the prefilter: a 0.03 pool is still rejected.
	p := pulsePool()
	p.FeeActiveTVLRatio = 0.03
	if _, reason := Screen(p, on); !strings.HasPrefix(reason, "fee/active-TVL") {
		t.Fatalf("Screen must keep the real bar, got %q", reason)
	}
}
