package meteora

import "testing"

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
