package meteora

import (
	"encoding/json"
	"math"
	"strings"
	"testing"
)

func TestAuditRejectBotHolderLimitByMode(t *testing.T) {
	for _, tc := range []struct {
		name string
		mode string
		bar  float64
		pct  float64
		want string
	}{
		{"pulse over its default limit", "pulse", 25, 25.1, "bot holders 25.1% > 25%"},
		{"pulse at its default limit", "pulse", 25, 25, ""},
		{"pulse default 24.9 passes", "pulse", 25, 24.9, ""},
		{"pulse default 29.9 rejects", "pulse", 25, 29.9, "bot holders 29.9% > 25%"},
		{"pulse default 30.0 rejects", "pulse", 25, 30, "bot holders 30.0% > 25%"},
		{"pulse bar 30 admits 24.9", "pulse", 30, 24.9, ""},
		{"pulse bar 30 admits 25.0", "pulse", 30, 25, ""},
		{"pulse bar 30 admits 29.9", "pulse", 30, 29.9, ""},
		{"pulse bar 30 admits 30.0 (gate is strictly above)", "pulse", 30, 30, ""},
		{"pulse bar 30 rejects 30.1", "pulse", 30, 30.1, "bot holders 30.1% > 30%"},
		{"fractional bar prints exactly", "pulse", 27.5, 27.6, "bot holders 27.6% > 27.5%"},
		{"invalid bar zero falls back to 25", "pulse", 0, 25.1, "bot holders 25.1% > 25%"},
		{"invalid bar over 100 falls back to 25", "pulse", 101, 25.1, "bot holders 25.1% > 25%"},
		{"NaN bar falls back to 25", "pulse", math.NaN(), 25.1, "bot holders 25.1% > 25%"},
		{"turnover ignores the pulse bar", "turnover", 20, 25.1, ""},
		{"turnover over shared limit", "turnover", 40, 30.1, "bot holders 30.1% > 30%"},
	} {
		t.Run(tc.name, func(t *testing.T) {
			got := AuditReject(&AuditInfo{BotHoldersPct: &tc.pct}, tc.mode, tc.bar)
			if got != tc.want {
				t.Fatalf("AuditReject() = %q, want %q", got, tc.want)
			}
		})
	}
	if got := AuditReject(nil, "pulse", 30); got != "" {
		t.Fatalf("AuditReject(nil) = %q, want empty", got)
	}
	if got := AuditReject(&AuditInfo{}, "pulse", 30); got != "" {
		t.Fatalf("AuditReject(missing bot-holder audit) = %q, want empty", got)
	}
}

func TestPulseBotBarRidesOnThePayload(t *testing.T) {
	bar := 30.0
	with, _ := json.Marshal(Candidate{PulseBotBarPct: &bar})
	without, _ := json.Marshal(Candidate{})
	if !strings.Contains(string(with), `"pulse_bot_bar_pct":30`) || strings.Contains(string(without), "pulse_bot_bar_pct") {
		t.Fatalf("payload: with=%s without=%s", with, without)
	}
}
