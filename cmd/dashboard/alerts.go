package main

// `azimuth-dashboard alerts`: the brief's alert rules, run unattended by a timer, with a state file so the
// operator hears about an alert when it starts and when it clears, not every run. Read only, like brief.

import (
	"context"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"io"
	"os"
	"os/exec"
	"path/filepath"
	"sort"
	"strings"
	"time"
)

const (
	// alertRepeat caps messages per alert: one raise or clear per alert id per 6h, so a flapping
	// condition cannot page every timer run.
	alertRepeat      = 6 * time.Hour
	alertMaxChars    = 1000
	alertSendTimeout = 30 * time.Second
)

// alert is one rule hit from the collector. ID names the condition (code, plus the unit for per-unit rules).
type alert struct {
	ID, Code, Message string
}

// alertRecord is what the state file remembers per alert id.
type alertRecord struct {
	Code     string `json:"code"`
	Message  string `json:"message"`
	Active   bool   `json:"active"`    // firing on the last run
	Notified bool   `json:"notified"`  // the operator's last message about it said "firing"
	Since    int64  `json:"since"`     // first run it fired, this episode
	LastSent int64  `json:"last_sent"` // unix seconds of the last raise or clear sent
}

type alertState struct {
	Alerts map[string]*alertRecord `json:"alerts"`
}

// infoCodes are reported but are not red flags.
var infoCodes = map[string]bool{"no_deploy_12h": true}

func runAlertCollector(ctx context.Context, profile string) ([]alert, error) {
	cmd := exec.CommandContext(ctx, "python3", "-c", collector, profile, "", "0", "UTC", "alerts")
	output, err := cmd.Output()
	if err != nil {
		detail := ""
		if exit, ok := err.(*exec.ExitError); ok {
			lines := strings.Split(strings.TrimSpace(string(exit.Stderr)), "\n")
			detail = clip(lines[len(lines)-1], 200)
		}
		return nil, fmt.Errorf("alert collector failed: %v %s", err, detail)
	}
	return parseAlerts(output)
}

func parseAlerts(output []byte) ([]alert, error) {
	var data struct {
		Alerts []map[string]any `json:"alerts"`
	}
	if err := json.Unmarshal(output, &data); err != nil {
		return nil, fmt.Errorf("alert collector output: %v", err)
	}
	if data.Alerts == nil {
		return nil, fmt.Errorf("alert collector output has no alerts list")
	}
	out := make([]alert, 0, len(data.Alerts))
	for _, a := range data.Alerts {
		code := str(a["code"])
		id, _ := a["id"].(string)
		if id == "" {
			id = code
		}
		out = append(out, alert{ID: id, Code: code, Message: str(a["message"])})
	}
	return out, nil
}

// alertDiff is what one run tells the operator.
type alertDiff struct {
	raised, cleared, standing []*alertRecord
}

// stepAlerts folds one run's alerts into the state and returns what to send. keepMissing is set when the
// run could not see every rule's evidence (collector or section failure): an alert missing from such a run
// is unknown, not cleared, so it stays as it was.
func stepAlerts(st *alertState, current []alert, now time.Time, keepMissing bool) alertDiff {
	if st.Alerts == nil {
		st.Alerts = map[string]*alertRecord{}
	}
	t := now.Unix()
	allowed := func(r *alertRecord) bool { return r.LastSent == 0 || t-r.LastSent >= int64(alertRepeat/time.Second) }
	var d alertDiff
	firing := map[string]bool{}
	for _, a := range current {
		if firing[a.ID] {
			continue
		}
		firing[a.ID] = true
		r := st.Alerts[a.ID]
		if r == nil {
			r = &alertRecord{}
			st.Alerts[a.ID] = r
		}
		if !r.Active {
			r.Since = t
		}
		r.Code, r.Message, r.Active = a.Code, a.Message, true
		switch {
		case r.Notified:
			d.standing = append(d.standing, r)
		case allowed(r):
			r.Notified, r.LastSent = true, t
			d.raised = append(d.raised, r)
		}
	}
	for id, r := range st.Alerts {
		if firing[id] || keepMissing {
			continue
		}
		r.Active = false
		switch {
		case r.Notified && allowed(r):
			r.Notified, r.LastSent = false, t
			d.cleared = append(d.cleared, r)
		case !r.Notified && allowed(r):
			delete(st.Alerts, id) // quiet and outside the repeat window: nothing left to remember
		}
	}
	for _, l := range [][]*alertRecord{d.raised, d.cleared, d.standing} {
		sort.Slice(l, func(i, j int) bool {
			if infoCodes[l[i].Code] != infoCodes[l[j].Code] {
				return !infoCodes[l[i].Code]
			}
			return l[i].Code+l[i].Message < l[j].Code+l[j].Message
		})
	}
	return d
}

func alertsText(d alertDiff, now time.Time) string {
	var b strings.Builder
	fmt.Fprintf(&b, "azimuth alerts %s\n", now.UTC().Format("01-02 15:04Z"))
	for _, r := range d.raised {
		mark := "!"
		if infoCodes[r.Code] {
			mark = "i"
		}
		fmt.Fprintf(&b, "%s %s: %s\n", mark, r.Code, clip(r.Message, 220))
	}
	for _, r := range d.cleared {
		fmt.Fprintf(&b, "ok %s cleared (since %s): %s\n", r.Code, time.Unix(r.Since, 0).UTC().Format("01-02 15:04Z"), clip(r.Message, 120))
	}
	if len(d.standing) > 0 {
		codes := make([]string, 0, len(d.standing))
		for _, r := range d.standing {
			codes = append(codes, r.Code)
		}
		fmt.Fprintf(&b, "still firing: %s\n", strings.Join(codes, ", "))
	}
	return clip(strings.TrimRight(b.String(), "\n"), alertMaxChars)
}

func loadAlertState(path string) (*alertState, error) {
	st := &alertState{Alerts: map[string]*alertRecord{}}
	raw, err := os.ReadFile(path)
	if errors.Is(err, os.ErrNotExist) {
		return st, nil
	}
	if err != nil {
		return st, err
	}
	if err := json.Unmarshal(raw, st); err != nil {
		return &alertState{Alerts: map[string]*alertRecord{}}, err
	}
	if st.Alerts == nil {
		st.Alerts = map[string]*alertRecord{}
	}
	return st, nil
}

// saveAlertState writes via rename so a crash mid-write never leaves a torn state file.
func saveAlertState(path string, st *alertState) error {
	if err := os.MkdirAll(filepath.Dir(path), 0o700); err != nil {
		return err
	}
	raw, err := json.MarshalIndent(st, "", " ")
	if err != nil {
		return err
	}
	tmp, err := os.CreateTemp(filepath.Dir(path), ".alerts-*.json")
	if err != nil {
		return err
	}
	defer os.Remove(tmp.Name())
	if _, err := tmp.Write(append(raw, '\n')); err != nil {
		tmp.Close()
		return err
	}
	if err := tmp.Close(); err != nil {
		return err
	}
	return os.Rename(tmp.Name(), path)
}

// sendAlert pipes text to the whitespace-split command on stdin, REPORT_CMD style.
func sendAlert(ctx context.Context, sendCmd, text string) error {
	argv := strings.Fields(sendCmd)
	cctx, cancel := context.WithTimeout(ctx, alertSendTimeout)
	defer cancel()
	cmd := exec.CommandContext(cctx, argv[0], argv[1:]...)
	cmd.Stdin = strings.NewReader(text + "\n")
	if out, err := cmd.CombinedOutput(); err != nil {
		return fmt.Errorf("%v %s", err, clip(strings.TrimSpace(string(out)), 200))
	}
	return nil
}

type alertDeps struct {
	now     func() time.Time
	collect func(ctx context.Context, profile string) ([]alert, error)
	send    func(ctx context.Context, sendCmd, text string) error
}

// alertsMain is the subcommand. Every runtime failure (collector, state, send) exits 0 and is logged to
// stderr, i.e. the journal: the timer must stay green. Only bad usage exits non-zero.
func alertsMain(args []string, stdout, stderr io.Writer) int {
	return alertsRun(args, stdout, stderr, alertDeps{time.Now, runAlertCollector, sendAlert})
}

func alertsRun(args []string, stdout, stderr io.Writer, deps alertDeps) int {
	home, _ := os.UserHomeDir()
	fs := flag.NewFlagSet("alerts", flag.ContinueOnError)
	fs.SetOutput(stderr)
	profile := fs.String("profile", filepath.Join(home, ".hermes/profiles/dlmm"), "Hermes profile directory")
	stateFile := fs.String("state-file", filepath.Join(home, ".local/state/azimuth/alerts.json"), "dedup state file")
	sendCmd := fs.String("send-cmd", "", "command that receives the message on stdin, e.g. \"hermes send -t telegram\"; empty prints it")
	if err := fs.Parse(args); err != nil {
		return 2
	}
	if fs.NArg() > 0 {
		fmt.Fprintf(stderr, "alerts: unexpected argument %q\n", fs.Arg(0))
		return 2
	}
	now := deps.now()
	st, err := loadAlertState(*stateFile)
	if err != nil {
		// A broken state file costs at most one repeat of each standing alert; never stop alerting over it.
		fmt.Fprintf(stderr, "alerts: state %s unreadable, starting fresh: %v\n", *stateFile, err)
	}
	ctx, cancel := context.WithTimeout(context.Background(), briefCLIDeadline)
	defer cancel()
	current, err := deps.collect(ctx, *profile)
	keep := false
	if err != nil {
		fmt.Fprintln(stderr, "alerts:", err)
		current, keep = []alert{{ID: "collector_failed", Code: "collector_failed", Message: clip(err.Error(), 200)}}, true
	}
	for _, a := range current {
		if a.Code == "section_unavailable" {
			keep = true
		}
	}
	d := stepAlerts(st, current, now, keep)
	if len(d.raised)+len(d.cleared) > 0 {
		text := alertsText(d, now)
		if strings.TrimSpace(*sendCmd) == "" {
			fmt.Fprintln(stdout, text)
		} else if err := deps.send(ctx, *sendCmd, text); err != nil {
			// State stays unsaved, so the next run sends this message again.
			fmt.Fprintln(stderr, "alerts: send failed, will retry next run:", err)
			return 0
		}
	}
	if err := saveAlertState(*stateFile, st); err != nil {
		fmt.Fprintln(stderr, "alerts: state not saved:", err)
	}
	return 0
}
