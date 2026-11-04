package main

import (
	"bytes"
	"context"
	"errors"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"
)

var t0 = time.Unix(1_800_000_000, 0)

func codes(l []*alertRecord) string {
	s := []string{}
	for _, r := range l {
		s = append(s, r.Code)
	}
	return strings.Join(s, ",")
}

func TestStepAlertsRaiseStandClear(t *testing.T) {
	st := &alertState{}
	disk := alert{"disk_low", "disk_low", "disk free 9%"}
	d := stepAlerts(st, []alert{disk}, t0, false)
	if codes(d.raised) != "disk_low" || len(d.cleared)+len(d.standing) != 0 {
		t.Fatalf("first run: %+v", d)
	}
	d = stepAlerts(st, []alert{disk}, t0.Add(10*time.Minute), false)
	if len(d.raised)+len(d.cleared) != 0 || codes(d.standing) != "disk_low" {
		t.Fatalf("standing alert must not resend: %+v", d)
	}
	// Clears inside the 6h window are held back, then sent once the window opens.
	d = stepAlerts(st, nil, t0.Add(time.Hour), false)
	if len(d.cleared) != 0 {
		t.Fatalf("clear sent inside repeat window")
	}
	d = stepAlerts(st, nil, t0.Add(6*time.Hour), false)
	if codes(d.cleared) != "disk_low" {
		t.Fatalf("clear not sent after window: %+v", d)
	}
	d = stepAlerts(st, nil, t0.Add(13*time.Hour), false)
	if len(d.cleared)+len(d.raised) != 0 || len(st.Alerts) != 0 {
		t.Fatalf("quiet alert not forgotten: %+v %+v", d, st.Alerts)
	}
}

func TestStepAlertsFlapIsCapped(t *testing.T) {
	st := &alertState{}
	a := alert{"monitor_tick_stale", "monitor_tick_stale", "tick 300s"}
	stepAlerts(st, []alert{a}, t0, false)
	stepAlerts(st, nil, t0.Add(10*time.Minute), false)
	// Back while the operator still believes it is firing: nothing to say.
	d := stepAlerts(st, []alert{a}, t0.Add(20*time.Minute), false)
	if len(d.raised)+len(d.cleared) != 0 {
		t.Fatalf("flap re-raised: %+v", d)
	}
	// Clear goes out after 6h; a new episode one run later waits for the next window.
	stepAlerts(st, nil, t0.Add(6*time.Hour), false)
	d = stepAlerts(st, []alert{a}, t0.Add(6*time.Hour+10*time.Minute), false)
	if len(d.raised) != 0 {
		t.Fatalf("raise inside window after clear")
	}
	d = stepAlerts(st, []alert{a}, t0.Add(12*time.Hour), false)
	if codes(d.raised) != "monitor_tick_stale" {
		t.Fatalf("held raise never sent: %+v", d)
	}
}

func TestStepAlertsPerUnitIDs(t *testing.T) {
	st := &alertState{}
	stepAlerts(st, []alert{{"core_unit_down:a.service", "core_unit_down", "a"}}, t0, false)
	d := stepAlerts(st, []alert{{"core_unit_down:a.service", "core_unit_down", "a"}, {"core_unit_down:b.service", "core_unit_down", "b"}}, t0.Add(time.Minute), false)
	if len(d.raised) != 1 || d.raised[0].Message != "b" {
		t.Fatalf("second unit under the same code must raise: %+v", d)
	}
}

func TestStepAlertsKeepMissing(t *testing.T) {
	st := &alertState{}
	stepAlerts(st, []alert{{"disk_low", "disk_low", "x"}}, t0, false)
	d := stepAlerts(st, []alert{{"collector_failed", "collector_failed", "boom"}}, t0.Add(7*time.Hour), true)
	if len(d.cleared) != 0 || !st.Alerts["disk_low"].Notified {
		t.Fatalf("blind run cleared an alert: %+v", d)
	}
	if codes(d.raised) != "collector_failed" {
		t.Fatalf("collector failure not raised: %+v", d)
	}
}

func TestAlertsTextOrderAndCap(t *testing.T) {
	d := stepAlerts(&alertState{}, []alert{{"no_deploy_12h", "no_deploy_12h", "n"}, {"disk_low", "disk_low", "d"}}, t0, false)
	if text := alertsText(d, t0); !strings.Contains(text, "! disk_low: d\ni no_deploy_12h: n") {
		t.Fatalf("red flags first, info marked: %q", text)
	}
	many := []alert{}
	for i := 0; i < 40; i++ {
		many = append(many, alert{strings.Repeat("x", i+1), "c", strings.Repeat("m", 300)})
	}
	if n := len([]rune(alertsText(stepAlerts(&alertState{}, many, t0, false), t0))); n > alertMaxChars {
		t.Fatalf("message %d chars > %d", n, alertMaxChars)
	}
}

func TestParseAlerts(t *testing.T) {
	got, err := parseAlerts([]byte(`{"alerts":[{"code":"disk_low","message":"m","id":"disk_low"},{"code":"x","message":"y"}]}`))
	if err != nil || len(got) != 2 || got[1].ID != "x" {
		t.Fatalf("%v %+v", err, got)
	}
	if _, err := parseAlerts([]byte(`{}`)); err == nil {
		t.Fatal("missing alerts list must be an error, not all-clear")
	}
}

func runAlerts(t *testing.T, state string, collect []alert, collectErr, sendErr error, now time.Time, extra ...string) (int, string, string, []string) {
	t.Helper()
	var out, errb bytes.Buffer
	sent := []string{}
	deps := alertDeps{
		now:     func() time.Time { return now },
		collect: func(context.Context, string) ([]alert, error) { return collect, collectErr },
		send: func(_ context.Context, _, text string) error {
			sent = append(sent, text)
			return sendErr
		},
	}
	code := alertsRun(append([]string{"-state-file", state}, extra...), &out, &errb, deps)
	return code, out.String(), errb.String(), sent
}

func TestAlertsRunSendAndRetry(t *testing.T) {
	state := filepath.Join(t.TempDir(), "s", "alerts.json")
	disk := []alert{{"disk_low", "disk_low", "disk free 9%"}}
	code, _, errs, sent := runAlerts(t, state, disk, nil, errors.New("down"), t0, "-send-cmd", "x")
	if code != 0 || len(sent) != 1 || !strings.Contains(errs, "send failed") {
		t.Fatalf("send failure must log and exit 0: %d %q", code, errs)
	}
	if _, err := os.Stat(state); err == nil {
		t.Fatal("state saved after a failed send; the alert would be lost")
	}
	_, _, _, sent = runAlerts(t, state, disk, nil, nil, t0.Add(10*time.Minute), "-send-cmd", "x")
	if len(sent) != 1 || !strings.Contains(sent[0], "! disk_low: disk free 9%") {
		t.Fatalf("retry: %q", sent)
	}
	_, _, _, sent = runAlerts(t, state, disk, nil, nil, t0.Add(20*time.Minute), "-send-cmd", "x")
	if len(sent) != 0 {
		t.Fatalf("standing alert resent: %q", sent)
	}
}

func TestAlertsRunPrintsByDefaultAndSurvivesFailures(t *testing.T) {
	state := filepath.Join(t.TempDir(), "alerts.json")
	os.WriteFile(state, []byte("{torn"), 0o600)
	code, out, errs, sent := runAlerts(t, state, nil, errors.New("python3 missing"), nil, t0)
	if code != 0 || len(sent) != 0 || !strings.Contains(out, "collector_failed") || !strings.Contains(errs, "unreadable") {
		t.Fatalf("code=%d out=%q errs=%q", code, out, errs)
	}
	if code, _, _, _ := runAlerts(t, state, nil, nil, nil, t0, "stray"); code != 2 {
		t.Fatalf("bad usage must exit 2, got %d", code)
	}
}
