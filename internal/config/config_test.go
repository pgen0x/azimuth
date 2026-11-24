package config

import "testing"

func TestPulseMaxBotHoldersPct(t *testing.T) {
	for _, tc := range []struct {
		value string
		set   bool
		want  float64
	}{
		{"", false, 25},
		{"30", true, 30},
		{"27.5", true, 27.5},
		{"100", true, 100},
		{"", true, 25},
		{"thirty", true, 25},
		{"0", true, 25},
		{"-5", true, 25},
		{"100.1", true, 25},
		{"NaN", true, 25},
		{"Inf", true, 25},
	} {
		if tc.set {
			t.Setenv("PULSE_MAX_BOT_HOLDERS_PCT", tc.value)
		} else {
			t.Setenv("PULSE_MAX_BOT_HOLDERS_PCT", "")
		}
		if got := Load().PulseMaxBotHoldersPct; got != tc.want {
			t.Errorf("PULSE_MAX_BOT_HOLDERS_PCT=%q: got %v, want %v", tc.value, got, tc.want)
		}
	}
}
