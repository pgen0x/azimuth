package setup

import (
	"bytes"
	"context"
	"errors"
	"io"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

type wizardEnv struct {
	repo, profile, home string
	exec                *execLog
	rpc                 *httptest.Server
	python              string
}

func newWizardEnv(t *testing.T) *wizardEnv {
	t.Helper()
	root := t.TempDir()
	w := &wizardEnv{repo: filepath.Join(root, "repo"), profile: filepath.Join(root, "profile"), home: root, exec: &execLog{}}
	os.MkdirAll(w.repo, 0o700)
	data, err := os.ReadFile("../../.env.example")
	if err != nil {
		t.Fatal(err)
	}
	os.WriteFile(filepath.Join(w.repo, ".env.example"), data, 0o644)
	w.python = filepath.Join(root, "bundled-python3")
	os.WriteFile(w.python, []byte("#!/bin/sh\nexit 0\n"), 0o700)
	w.rpc = httptest.NewServer(http.HandlerFunc(func(rw http.ResponseWriter, r *http.Request) {
		body, _ := io.ReadAll(r.Body)
		switch {
		case bytes.Contains(body, []byte(`"getHealth"`)):
			io.WriteString(rw, `{"jsonrpc":"2.0","id":1,"result":"ok"}`)
		case bytes.Contains(body, []byte(`"getBalance"`)):
			io.WriteString(rw, `{"jsonrpc":"2.0","id":1,"result":{"value":0}}`)
		default:
			t.Error("non-read-only RPC call")
			rw.WriteHeader(400)
		}
	}))
	t.Cleanup(w.rpc.Close)
	return w
}

func (w *wizardEnv) run(t *testing.T, stdin string, secrets [][]byte, args ...string) (int, string, string) {
	t.Helper()
	var out, errOut bytes.Buffer
	sio := SetupIO{In: strings.NewReader(stdin), Out: &out, Err: &errOut,
		ReadSecret: func(prompt string) ([]byte, error) {
			out.WriteString(prompt + "\n")
			if len(secrets) == 0 {
				return nil, errors.New("no secret scripted")
			}
			s := secrets[0]
			secrets = secrets[1:]
			return append([]byte(nil), s...), nil
		},
		Engine: func(o *EngineOptions) {
			o.HomeDir = w.home
			o.Exec = w.exec.exec
			o.LookPath = func(string) (string, error) { return "", errors.New("absent") }
		}}
	base := []string{"--repo", w.repo, "--profile", w.profile, "--hermes-python", w.python, "--skip-preflight", "--skip-doctor"}
	code := RunSetup(context.Background(), append(base, args...), sio)
	return code, out.String(), errOut.String()
}

func (w *wizardEnv) daemon(t *testing.T) map[string]string {
	return readValues(t, filepath.Join(w.repo, ".env"))
}

func (w *wizardEnv) prof(t *testing.T) map[string]string {
	return readValues(t, filepath.Join(w.profile, ".env"))
}

func TestSetupNonInteractiveFreshInstall(t *testing.T) {
	w := newWizardEnv(t)
	code, out, errOut := w.run(t, "", nil, "--non-interactive", "--wallet", "generate", "--rpc-urls", w.rpc.URL, "--modes", "pulse,casual", "--route", "deterministic")
	if code != 0 {
		t.Fatalf("exit %d: %s", code, errOut)
	}
	d, p := w.daemon(t), w.prof(t)
	if d["DRY_RUN"] != "true" || p["DRY_RUN"] != "true" {
		t.Fatal("DRY_RUN must default to true in both configs")
	}
	if d["ENABLE_PULSE"] != "true" || d["ENABLE_CASUAL"] != "true" || d["ENABLE_MULTIDAY"] != "false" || d["ENABLE_TURNOVER"] != "false" {
		t.Fatal("discovery modes not applied")
	}
	if d["DEPLOY_CMD"] != "python3 "+filepath.Join(w.profile, "skills/solana-dlmm/scripts/dlmm_pipeline.py") || d["AI_HEALTH_CMD"] != "" {
		t.Fatal("deterministic route not configured")
	}
	if d["SOLANA_RPC_URLS"] != w.rpc.URL || p["SOLANA_RPC_URLS"] != w.rpc.URL {
		t.Fatal("RPC URLs not written")
	}
	wal, err := ParsePrivateKey([]byte(p["SOLANA_PRIVATE_KEY"]))
	if err != nil || wal.PublicKey != p["SOLANA_PUBLIC_KEY"] || d["SOLANA_PUBLIC_KEY"] != wal.PublicKey {
		t.Fatal("generated wallet not written consistently")
	}
	if _, leaked := d["SOLANA_PRIVATE_KEY"]; leaked {
		t.Fatal("private key in daemon config")
	}
	if strings.Contains(out+errOut, wal.Secret()) || strings.Contains(out, w.rpc.URL) {
		t.Fatal("secret or RPC URL printed")
	}
	if !strings.Contains(out, wal.PublicKey) {
		t.Fatal("public key should be shown so the operator can fund it")
	}
	if d["LONE_MIN_SCORE"] != "50" || d["POLL_INTERVAL"] != "60s" {
		t.Fatal("risk defaults or template keys missing")
	}
	for _, r := range w.exec.reqs {
		if r.Name == "bash" || r.Name == "loginctl" || r.Name == "hermes" {
			t.Fatalf("unrequested action ran: %s", r.Name)
		}
	}
}

func TestSetupRerunIsIdempotentAndPreservesUnknownKeys(t *testing.T) {
	w := newWizardEnv(t)
	args := []string{"--non-interactive", "--wallet", "generate", "--rpc-urls", w.rpc.URL, "--skip-tests"}
	if code, _, e := w.run(t, "", nil, args...); code != 0 {
		t.Fatal(e)
	}
	dpath := filepath.Join(w.repo, ".env")
	f, _ := os.OpenFile(dpath, os.O_APPEND|os.O_WRONLY, 0)
	f.WriteString("OPERATOR_CUSTOM_KEY=keep-me\n")
	f.Close()
	ppath := filepath.Join(w.profile, ".env")
	pf, _ := os.OpenFile(ppath, os.O_APPEND|os.O_WRONLY, 0)
	pf.WriteString("DLMM_TZ=UTC\n")
	pf.Close()
	before, _ := os.ReadFile(dpath)
	pbefore, _ := os.ReadFile(ppath)
	code, out, e := w.run(t, "", nil, "--non-interactive", "--rpc-urls", w.rpc.URL, "--skip-tests")
	if code != 0 {
		t.Fatal(e)
	}
	after, _ := os.ReadFile(dpath)
	pafter, _ := os.ReadFile(ppath)
	if !bytes.Equal(before, after) || !bytes.Equal(pbefore, pafter) {
		t.Fatalf("identical re-run changed a config:\n%s", out)
	}
	if strings.Contains(out, "\n    set ") {
		t.Fatal("re-run plan should report every key unchanged")
	}
	if code, _, _ := w.run(t, "", nil, "--non-interactive", "--wallet", "generate", "--skip-tests"); code != 1 {
		t.Fatal("replacing a wallet without --replace-wallet must fail")
	}
	if now, _ := os.ReadFile(ppath); !bytes.Equal(pafter, now) {
		t.Fatal("refused run modified the profile")
	}
}

func TestSetupDryRunWritesNothing(t *testing.T) {
	w := newWizardEnv(t)
	code, out, e := w.run(t, "", nil, "--non-interactive", "--dry-run", "--wallet", "generate", "--telegram", "on", "--install", "--linger")
	if code != 0 {
		t.Fatal(e)
	}
	for _, p := range []string{filepath.Join(w.repo, ".env"), w.profile} {
		if _, err := os.Stat(p); !os.IsNotExist(err) {
			t.Fatalf("--dry-run created %s", p)
		}
	}
	if len(w.exec.reqs) != 0 {
		t.Fatalf("--dry-run ran %s", w.exec.reqs[0].Name)
	}
	if !strings.Contains(out, "SOLANA_PRIVATE_KEY=<secret>") || !strings.Contains(out, "install.sh") || !strings.Contains(out, "nothing was written") {
		t.Fatalf("plan not printed:\n%s", out)
	}
}

func TestSetupLiveNeedsPhrase(t *testing.T) {
	w := newWizardEnv(t)
	if code, _, _ := w.run(t, "", nil, "--non-interactive", "--live", "--skip-tests"); code != 1 {
		t.Fatal("--live without phrase accepted")
	}
	if code, _, _ := w.run(t, "", nil, "--non-interactive", "--live", "--confirm-live", "yes", "--skip-tests"); code != 1 {
		t.Fatal("--live with wrong phrase accepted")
	}
	if _, err := os.Stat(filepath.Join(w.repo, ".env")); !os.IsNotExist(err) {
		t.Fatal("refused live run wrote config")
	}
	if code, _, e := w.run(t, "", nil, "--non-interactive", "--live", "--confirm-live", LivePhrase, "--skip-tests"); code != 0 {
		t.Fatal(e)
	}
	if w.daemon(t)["DRY_RUN"] != "false" || w.prof(t)["DRY_RUN"] != "false" {
		t.Fatal("confirmed live run did not set DRY_RUN=false")
	}
	// An unrelated non-interactive edit must not stop live trading.
	code, out, e := w.run(t, "", nil, "--non-interactive", "--set", "LONE_MIN_SCORE=60", "--skip-tests")
	if code != 0 {
		t.Fatal(e)
	}
	if w.daemon(t)["DRY_RUN"] != "false" || w.prof(t)["DRY_RUN"] != "false" || w.daemon(t)["LONE_MIN_SCORE"] != "60" || !strings.Contains(out, "DRY_RUN left unchanged") {
		t.Fatal("a non-interactive edit without a DRY_RUN flag changed DRY_RUN")
	}
	if code, _, _ := w.run(t, "", nil, "--non-interactive", "--simulate-trades", "--live", "--confirm-live", LivePhrase, "--skip-tests"); code != 1 {
		t.Fatal("--simulate-trades with --live accepted")
	}
	if code, _, e := w.run(t, "", nil, "--non-interactive", "--simulate-trades", "--skip-tests"); code != 0 {
		t.Fatal(e)
	}
	if w.daemon(t)["DRY_RUN"] != "true" || w.prof(t)["DRY_RUN"] != "true" {
		t.Fatal("--simulate-trades did not switch back to dry run")
	}
}

func TestSetupFreshConfigDefaultsToDryRun(t *testing.T) {
	w := newWizardEnv(t)
	if code, _, e := w.run(t, "", nil, "--non-interactive", "--set", "LONE_MIN_SCORE=60", "--skip-tests"); code != 0 {
		t.Fatal(e)
	}
	if w.daemon(t)["DRY_RUN"] != "true" || w.prof(t)["DRY_RUN"] != "true" {
		t.Fatal("fresh config must get DRY_RUN=true")
	}
}

func TestSetupInteractiveLiveDefaultsToKeep(t *testing.T) {
	w := newWizardEnv(t)
	if code, _, e := w.run(t, "", nil, "--non-interactive", "--live", "--confirm-live", LivePhrase, "--skip-tests"); code != 0 {
		t.Fatal(e)
	}
	// Enter at every prompt: modes, "keep live?", wallet, RPC, route, telegram, gates, install, apply.
	code, out, e := w.run(t, strings.Repeat("\n", 20), [][]byte{{}}, "--skip-tests")
	if code != 0 {
		t.Fatalf("%s\n%s", e, out)
	}
	if !strings.Contains(out, "Keep live trading? (n switches to dry run) (Y/n)") || w.daemon(t)["DRY_RUN"] != "false" || w.prof(t)["DRY_RUN"] != "false" {
		t.Fatal("interactive default on a live config must keep it live")
	}
	if code, _, e := w.run(t, "\n\n\n\nn\n"+strings.Repeat("\n", 20), [][]byte{{}}, "--skip-tests"); code != 0 {
		t.Fatal(e)
	}
	if w.daemon(t)["DRY_RUN"] != "true" || w.prof(t)["DRY_RUN"] != "true" {
		t.Fatal("answering n must switch to dry run")
	}
}

func TestSetupInteractiveImportAndRefusedLive(t *testing.T) {
	w := newWizardEnv(t)
	wal, _ := GenerateWallet()
	answers := strings.Join([]string{
		"y", "n", "n", "y", // modes: casual, multiday, turnover, pulse
		"n", "please", // decline dry run, wrong phrase -> stays dry
		"import",                          // wallet (key comes from ReadSecret)
		w.rpc.URL,                         // RPC
		"ai",                              // route; probe succeeds via fake exec
		"y",                               // telegram on
		"y",                               // keep gate defaults
		"y", "y", "n", "n", "n", "n", "y", // install, dashboard, alerts, ops, research, rent, linger
		"y", // apply
	}, "\n") + "\n"
	code, out, e := w.run(t, answers, [][]byte{[]byte(wal.Secret()), {}, []byte("correct horse battery"), []byte("correct horse battery")})
	if code != 0 {
		t.Fatalf("exit %d: %s\n%s", code, e, out)
	}
	d, p := w.daemon(t), w.prof(t)
	if d["DRY_RUN"] != "true" || !strings.Contains(out, "phrase did not match") {
		t.Fatal("wrong live phrase must keep dry run")
	}
	if p["SOLANA_PRIVATE_KEY"] != wal.Secret() || d["SOLANA_PUBLIC_KEY"] != wal.PublicKey {
		t.Fatal("imported wallet not written")
	}
	if !strings.HasPrefix(d["AI_HEALTH_CMD"], w.python+" ") || len(d["HERMES_WEBHOOK_SECRET"]) != 64 || d["HERMES_WEBHOOK_URL"] == "" {
		t.Fatal("ai route not configured")
	}
	if d["REPORT_CMD"] != ReportCommand || p["DLMM_ALERT_TARGET"] != "telegram" {
		t.Fatal("telegram not configured")
	}
	if !strings.HasPrefix(readValues(t, filepath.Join(w.home, ".config/azimuth/dashboard-auth.env"))["DASHBOARD_PASSWORD_HASH"], "pbkdf2-sha256:") {
		t.Fatal("dashboard hash not written")
	}
	var ran []string
	for _, r := range w.exec.reqs {
		ran = append(ran, filepath.Base(r.Name))
		if r.Name == "bash" && strings.Join(r.Args[1:], " ") != w.profile+" --with-dashboard" {
			t.Fatalf("install.sh flags: %v", r.Args)
		}
	}
	// The webhook sync is skipped (no subscription file in the fixture).
	if strings.Join(ran, ",") != "bundled-python3,hermes,bash,loginctl" {
		t.Fatalf("unexpected commands %v", ran)
	}
	for _, leaked := range []string{wal.Secret(), "correct horse battery", d["HERMES_WEBHOOK_SECRET"]} {
		if strings.Contains(out+e, leaked) {
			t.Fatal("secret printed")
		}
	}
}

func TestSetupRejectsBadFlags(t *testing.T) {
	w := newWizardEnv(t)
	for _, args := range [][]string{
		{"--non-interactive", "--modes", "bogus"},
		{"--non-interactive", "--route", "llm", "--skip-tests"},
		{"--non-interactive", "--live", "--confirm-live", "i understand this trades real funds", "--skip-tests"},
		{"--non-interactive", "--wallet", "import"},
		{"--non-interactive", "--set", "DRY_RUN=false", "--skip-tests"},
		{"--non-interactive", "--set", "HERMES_WEBHOOK_SECRET=x", "--skip-tests"},
		{"--non-interactive", "--set", "POLL_INTERVAL=soon", "--skip-tests"},
		{"--non-interactive", "--with-dashboard", "--skip-tests"},
		{"--non-interactive", "--private-key-file", "-", "--dashboard-password-file", "-"},
		{"positional"},
	} {
		if code, _, _ := w.run(t, "", nil, args...); code != 1 {
			t.Fatalf("accepted %v", args)
		}
	}
	if _, err := os.Stat(filepath.Join(w.repo, ".env")); !os.IsNotExist(err) {
		t.Fatal("a rejected run wrote config")
	}
	var out bytes.Buffer
	if RunSetup(context.Background(), []string{"--help"}, SetupIO{In: strings.NewReader(""), Out: &out, Err: io.Discard}) != 0 || !strings.Contains(out.String(), LivePhrase) {
		t.Fatal("help output")
	}
}

func TestSetupImportFromFileWarnsOnLoosePermissions(t *testing.T) {
	w := newWizardEnv(t)
	wal, _ := GenerateWallet()
	keyFile := filepath.Join(w.home, "key.txt")
	os.WriteFile(keyFile, []byte(wal.Secret()+"\n"), 0o644)
	code, out, e := w.run(t, "", nil, "--non-interactive", "--wallet", "import", "--private-key-file", keyFile, "--skip-tests")
	if code != 0 {
		t.Fatal(e)
	}
	if !strings.Contains(out, "readable by other users") || w.prof(t)["SOLANA_PUBLIC_KEY"] != wal.PublicKey {
		t.Fatal("import from file")
	}
}

func TestSetupKeepsExistingWebhookRouteAndSeesLegacyLive(t *testing.T) {
	w := newWizardEnv(t)
	os.MkdirAll(w.profile, 0o700)
	// A pre-setup install: agent-only routing, no DRY_RUN anywhere. The
	// executor treats an unset profile DRY_RUN as live.
	os.WriteFile(filepath.Join(w.repo, ".env"), []byte("HERMES_WEBHOOK_URL=http://127.0.0.1:8646/webhooks/dlmm-signal\nHERMES_WEBHOOK_SECRET=test-only-secret\n"), 0o600)
	os.WriteFile(filepath.Join(w.profile, ".env"), []byte("DLMM_TZ=UTC\n"), 0o600)
	code, out, e := w.run(t, "", nil, "--non-interactive", "--skip-tests")
	if code != 0 {
		t.Fatal(e)
	}
	d := w.daemon(t)
	if d["DEPLOY_CMD"] != "" || d["AI_HEALTH_CMD"] != "" || d["HERMES_WEBHOOK_SECRET"] != "test-only-secret" {
		t.Fatal("webhook-only route was changed without being asked")
	}
	_, daemonDry := d["DRY_RUN"]
	_, profileDry := w.prof(t)["DRY_RUN"]
	if !strings.Contains(out, "currently LIVE") || daemonDry || profileDry {
		t.Fatal("legacy config without DRY_RUN must be recognised as live and left unchanged")
	}
	if strings.Contains(out, "test-only-secret") {
		t.Fatal("secret printed")
	}
}
