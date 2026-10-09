package meteora

import "testing"

func TestAuditRejectBotHolderLimitByMode(t *testing.T) {
	for _, tc := range []struct {
		name string
		mode string
		pct  float64
		want string
	}{
		{"pulse over its empirical limit", "pulse", 25.1, "bot holders 25.1% > 25%"},
		{"pulse at its limit", "pulse", 25, ""},
		{"turnover keeps shared limit", "turnover", 25.1, ""},
		{"turnover over shared limit", "turnover", 30.1, "bot holders 30.1% > 30%"},
	} {
		t.Run(tc.name, func(t *testing.T) {
			got := AuditReject(&AuditInfo{BotHoldersPct: &tc.pct}, tc.mode)
			if got != tc.want {
				t.Fatalf("AuditReject() = %q, want %q", got, tc.want)
			}
		})
	}
	if got := AuditReject(nil, "pulse"); got != "" {
		t.Fatalf("AuditReject(nil) = %q, want empty", got)
	}
	if got := AuditReject(&AuditInfo{}, "pulse"); got != "" {
		t.Fatalf("AuditReject(missing bot-holder audit) = %q, want empty", got)
	}
}
