package setup

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"net"
	"net/http"
	"net/http/httptest"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"testing"
)

func TestBase58RoundTrip(t *testing.T) {
	for _, in := range [][]byte{{}, {0}, {0, 0, 1}, {255, 254, 0, 7}, bytes.Repeat([]byte{9}, 64)} {
		out, err := base58Decode(base58Encode(in))
		if err != nil || !bytes.Equal(out, in) {
			t.Fatalf("round trip failed for %v", in)
		}
	}
	if _, err := base58Decode("0OIl"); err == nil {
		t.Fatal("invalid alphabet accepted")
	}
}

func TestWalletGenerateAndImportForms(t *testing.T) {
	w, err := GenerateWallet()
	if err != nil {
		t.Fatal(err)
	}
	if !validPubkey(w.PublicKey) {
		t.Fatal("generated public key fails the schema validator")
	}
	if strings.Contains(fmt.Sprintf("%v %+v %#v %s", w, w, w, w), w.Secret()) {
		t.Fatal("formatting a Wallet printed its private key")
	}
	raw, _ := base58Decode(w.Secret())
	if len(raw) != 64 {
		t.Fatal("secret key is not 64 bytes")
	}
	nums := make([]string, len(raw))
	for i, b := range raw {
		nums[i] = fmt.Sprint(b)
	}
	for name, input := range map[string]string{
		"base58":  w.Secret(),
		"json":    "[" + strings.Join(nums, ",") + "]",
		"seed":    base58Encode(raw[:32]),
		"padded":  "  " + w.Secret() + "\n",
		"jsonpad": "\n[" + strings.Join(nums, ", ") + "]\n",
	} {
		got, err := ParsePrivateKey([]byte(input))
		if err != nil || got.PublicKey != w.PublicKey || got.Secret() != w.Secret() {
			t.Fatalf("%s import did not reproduce the keypair", name)
		}
	}
	other, _ := GenerateWallet()
	otherRaw, _ := base58Decode(other.Secret())
	mismatch := append(append([]byte(nil), raw[:32]...), otherRaw[32:]...)
	for _, bad := range []string{base58Encode(mismatch), "not-a-key", "[1,2,3]", "[999]", base58Encode(raw[:31])} {
		_, err := ParsePrivateKey([]byte(bad))
		if err == nil {
			t.Fatal("invalid key accepted")
		}
		if strings.Contains(err.Error(), bad) {
			t.Fatal("error echoed the input")
		}
	}
}

func TestEnvDocEditsInPlace(t *testing.T) {
	src := "# header\nKEEP=1\nexport DRY_RUN=false # inline\n\n#DEPLOY_CMD=python3 /path/x.py\nUNKNOWN_TOOL_KEY='a b'\n"
	doc, err := ParseEnvDoc([]byte(src))
	if err != nil {
		t.Fatal(err)
	}
	must := func(err error) {
		t.Helper()
		if err != nil {
			t.Fatal(err)
		}
	}
	must(doc.Set("DRY_RUN", "true"))
	must(doc.Set("DEPLOY_CMD", "python3 /p/dlmm_pipeline.py"))
	must(doc.Set("NEW_KEY", "x"))
	must(doc.Set("ABSENT_EMPTY", ""))
	got := string(doc.Bytes())
	want := "# header\nKEEP=1\nexport DRY_RUN=true\n\nDEPLOY_CMD='python3 /p/dlmm_pipeline.py'\nUNKNOWN_TOOL_KEY='a b'\n\n# ─── Written by azimuth setup ───\nNEW_KEY=x\n"
	if got != want {
		t.Fatalf("unexpected render:\n%s", got)
	}
	values := doc.Values()
	if values["DEPLOY_CMD"] != "python3 /p/dlmm_pipeline.py" || values["UNKNOWN_TOOL_KEY"] != "a b" || values["KEEP"] != "1" {
		t.Fatal("values did not round trip")
	}
	before := string(doc.Bytes())
	must(doc.Set("DRY_RUN", "true"))
	must(doc.Set("NEW_KEY", "x"))
	if string(doc.Bytes()) != before {
		t.Fatal("re-setting the same values changed the file")
	}
	for _, bad := range []string{"it's", "a\nb", "a\x00"} {
		if err := doc.Set("K", bad); err == nil || strings.Contains(err.Error(), bad) {
			t.Fatal("unrepresentable value accepted or echoed")
		}
	}
	if _, err := ParseEnvDoc([]byte("not an assignment\n")); err == nil {
		t.Fatal("unparseable file accepted for editing")
	}
}

func TestEnvValuesSurviveShellAndSystemdQuoting(t *testing.T) {
	if _, err := exec.LookPath("bash"); err != nil {
		t.Skip("bash unavailable")
	}
	doc := &EnvDoc{}
	values := map[string]string{"A": "python3 /x/y.py --flag $HOME `id` \"q\"", "B": "plain-1.2:3/x", "C": "#notacomment"}
	for k, v := range values {
		if err := doc.Set(k, v); err != nil {
			t.Fatal(err)
		}
	}
	path := filepath.Join(t.TempDir(), "e.env")
	os.WriteFile(path, doc.Bytes(), 0o600)
	out, err := exec.Command("bash", "-c", `set -a; . "$1"; printf '%s\n%s\n%s' "$A" "$B" "$C"`, "_", path).Output()
	if err != nil {
		t.Fatal(err)
	}
	if string(out) != values["A"]+"\n"+values["B"]+"\n"+values["C"] {
		t.Fatalf("bash read a different value: %q", out)
	}
	if got := doc.Values(); got["A"] != values["A"] || got["C"] != values["C"] {
		t.Fatal("ParseEnv read a different value")
	}
}

func TestWriteFile0600(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "sub", "f.env")
	if err := WriteFile0600(path, []byte("A=1\n")); err != nil {
		t.Fatal(err)
	}
	loose := filepath.Join(dir, "loose.env")
	os.WriteFile(loose, []byte("A=0\n"), 0o644)
	if err := WriteFile0600(loose, []byte("A=1\n")); err != nil {
		t.Fatal(err)
	}
	for _, p := range []string{path, loose} {
		info, err := os.Stat(p)
		if err != nil || info.Mode().Perm() != 0o600 {
			t.Fatalf("%s is not 0600", p)
		}
	}
	link := filepath.Join(dir, "link.env")
	os.Symlink(loose, link)
	if err := WriteFile0600(link, []byte("A=2\n")); err == nil {
		t.Fatal("wrote through a symlink")
	}
	if data, _ := os.ReadFile(loose); string(data) != "A=1\n" {
		t.Fatal("symlink target changed")
	}
	if matches, _ := filepath.Glob(filepath.Join(dir, ".*setup-*")); len(matches) != 0 {
		t.Fatal("temporary file left behind")
	}
}

type execLog struct {
	reqs []ExecRequest
	fn   func(ExecRequest) (CommandResult, error)
}

func (l *execLog) exec(_ context.Context, req ExecRequest) (CommandResult, error) {
	l.reqs = append(l.reqs, req)
	if l.fn != nil {
		return l.fn(req)
	}
	return CommandResult{}, nil
}

func testEngine(t *testing.T) (*Engine, *execLog, *bytes.Buffer) {
	t.Helper()
	root := t.TempDir()
	repo := filepath.Join(root, "repo")
	os.MkdirAll(repo, 0o700)
	if data, err := os.ReadFile("../../.env.example"); err == nil {
		os.WriteFile(filepath.Join(repo, ".env.example"), data, 0o644)
	}
	log := &execLog{}
	var out bytes.Buffer
	e := NewEngine(EngineOptions{RepoDir: repo, ProfileDir: filepath.Join(root, "profile"), HomeDir: root, Exec: log.exec, Log: &out,
		LookPath: func(string) (string, error) { return "", errors.New("absent") }})
	return e, log, &out
}

func readValues(t *testing.T, path string) map[string]string {
	t.Helper()
	info, err := os.Stat(path)
	if err != nil {
		t.Fatal(err)
	}
	if info.Mode().Perm() != 0o600 {
		t.Fatalf("%s is %v, want 0600", path, info.Mode().Perm())
	}
	f, _ := os.Open(path)
	defer f.Close()
	v, err := ParseEnv(f)
	if err != nil {
		t.Fatal(err)
	}
	return v
}

func TestApplyRefusesLiveWithoutPhrase(t *testing.T) {
	e, _, _ := testEngine(t)
	var p Plan
	p.Set(DaemonEnv, "DRY_RUN", "false")
	if err := e.Apply(context.Background(), p); !errors.Is(err, ErrLiveNotConfirmed) {
		t.Fatal("live plan applied without confirmation")
	}
	if _, err := os.Stat(e.Path(DaemonEnv)); !os.IsNotExist(err) {
		t.Fatal("refused plan still wrote a file")
	}
	for _, wrong := range []string{"", "yes", strings.ToLower(LivePhrase), LivePhrase + "!"} {
		if p.ConfirmLive(wrong) == nil {
			t.Fatalf("phrase %q accepted", wrong)
		}
	}
	if err := p.ConfirmLive(LivePhrase); err != nil {
		t.Fatal(err)
	}
	if err := e.Apply(context.Background(), p); err != nil {
		t.Fatal(err)
	}
	if v := readValues(t, e.Path(DaemonEnv)); v["DRY_RUN"] != "false" || v["POLL_INTERVAL"] != "60s" {
		t.Fatal("new daemon config was not seeded from .env.example")
	}
}

func TestApplySecretsRequireTrustedSourceAndStayMasked(t *testing.T) {
	e, _, out := testEngine(t)
	w, _ := GenerateWallet()
	var p Plan
	p.Set(ProfileEnv, "SOLANA_PRIVATE_KEY", w.Secret())
	p.Set(ProfileEnv, "SOLANA_PUBLIC_KEY", w.PublicKey)
	p.Set(ProfileEnv, "DRY_RUN", "true")
	if err := e.Apply(context.Background(), p); err == nil {
		t.Fatal("secret plan applied outside setup mode")
	}
	e.EnterSetupMode()
	if err := e.Apply(context.Background(), p); err == nil {
		t.Fatal("secret plan applied without a source")
	}
	var desc bytes.Buffer
	p.Source = TerminalSource()
	e.WritePlanDescription(&desc, p)
	if err := e.Apply(context.Background(), p); err != nil {
		t.Fatal(err)
	}
	v := readValues(t, e.Path(ProfileEnv))
	if v["SOLANA_PRIVATE_KEY"] != w.Secret() || v["SOLANA_PUBLIC_KEY"] != w.PublicKey {
		t.Fatal("wallet not written")
	}
	if dir, _ := os.Stat(filepath.Dir(e.Path(ProfileEnv))); dir.Mode().Perm() != 0o700 {
		t.Fatal("new profile directory is not 0700")
	}
	all := desc.String() + out.String()
	if strings.Contains(all, w.Secret()) || !strings.Contains(desc.String(), "SOLANA_PRIVATE_KEY=<secret>") {
		t.Fatal("secret leaked into plan description or log")
	}
	st, err := e.Load()
	if err != nil || st.Profile["SOLANA_PRIVATE_KEY"] != "" || !st.SecretSet[ProfileEnv]["SOLANA_PRIVATE_KEY"] || st.Profile["SOLANA_PUBLIC_KEY"] != w.PublicKey {
		t.Fatal("Load exposed a secret or lost the public key")
	}
	if lines, _ := e.Describe(p); lines[0].Status != "unchanged" {
		t.Fatal("re-describing an applied plan should show no change")
	}
	var bad Plan
	bad.Source = TerminalSource()
	bad.Set(DaemonEnv, "SOLANA_PRIVATE_KEY", w.Secret())
	if err := e.Apply(context.Background(), bad); err == nil {
		t.Fatal("private key accepted for the daemon config")
	}
	var invalid Plan
	invalid.Set(DaemonEnv, "POLL_INTERVAL", "soon")
	if err := e.Apply(context.Background(), invalid); err == nil {
		t.Fatal("schema-invalid value accepted")
	}
}

func loopbackRequest(remote, local, host string) *http.Request {
	r := httptest.NewRequest(http.MethodPost, "http://localhost/setup/secret", nil)
	r.RemoteAddr = remote
	r.Host = host
	addr, _ := net.ResolveTCPAddr("tcp", local)
	return r.WithContext(context.WithValue(r.Context(), http.LocalAddrContextKey, addr))
}

func TestWriteSecretTrustedLocalCaller(t *testing.T) {
	e, _, out := testEngine(t)
	w, _ := GenerateWallet()
	ok := loopbackRequest("127.0.0.1:50000", "127.0.0.1:8787", "localhost:8787")
	if _, err := e.WriteSecret(LoopbackRequestSource(ok), "SOLANA_PRIVATE_KEY", []byte(w.Secret())); err == nil {
		t.Fatal("secret write accepted outside setup mode")
	}
	e.EnterSetupMode()
	value := []byte(w.Secret())
	pub, err := e.WriteSecret(LoopbackRequestSource(ok), "SOLANA_PRIVATE_KEY", value)
	if err != nil || pub != w.PublicKey {
		t.Fatalf("trusted write failed: %v", err)
	}
	if !bytes.Equal(value, make([]byte, len(value))) {
		t.Fatal("secret buffer was not zeroed")
	}
	if readValues(t, e.Path(ProfileEnv))["SOLANA_PRIVATE_KEY"] != w.Secret() || readValues(t, e.Path(DaemonEnv))["SOLANA_PUBLIC_KEY"] != w.PublicKey {
		t.Fatal("wallet not written to both configs")
	}
	if _, has := readValues(t, e.Path(DaemonEnv))["SOLANA_PRIVATE_KEY"]; has {
		t.Fatal("private key reached the daemon config")
	}
	forwarded := loopbackRequest("[::1]:1", "[::1]:8787", "[::1]:8787")
	forwarded.Header.Set("X-Forwarded-For", "203.0.113.9")
	for name, r := range map[string]*http.Request{
		"remote peer":     loopbackRequest("192.0.2.10:5000", "127.0.0.1:8787", "localhost:8787"),
		"public listener": loopbackRequest("127.0.0.1:5000", "0.0.0.0:8787", "localhost:8787"),
		"rebinding host":  loopbackRequest("127.0.0.1:5000", "127.0.0.1:8787", "attacker.example:8787"),
		"proxy":           forwarded,
		"no local addr":   httptest.NewRequest(http.MethodPost, "http://localhost/", nil),
	} {
		if _, err := e.WriteSecret(LoopbackRequestSource(r), "REDISCLI_AUTH", []byte("test-only-value")); err == nil {
			t.Fatalf("%s accepted", name)
		}
	}
	if _, err := e.WriteSecret(LoopbackRequestSource(loopbackRequest("[::1]:1", "[::1]:8787", "[::1]:8787")), "REDISCLI_AUTH", []byte("test-only-value")); err != nil {
		t.Fatal("IPv6 loopback refused")
	}
	for _, key := range []string{"DRY_RUN", "SOLANA_PUBLIC_KEY", "HERMES_WEBHOOK_URL"} {
		if _, err := e.WriteSecret(TerminalSource(), key, []byte("false")); err == nil {
			t.Fatalf("%s accepted as a secret", key)
		}
	}
	if _, err := e.WriteSecret(nil, "REDISCLI_AUTH", []byte("x")); err == nil {
		t.Fatal("nil source accepted")
	}
	if _, err := e.WriteSecret(TerminalSource(), "DASHBOARD_PASSWORD", []byte("short")); err == nil {
		t.Fatal("short dashboard password accepted")
	}
	if _, err := e.WriteSecret(TerminalSource(), "DASHBOARD_PASSWORD", []byte("correct horse battery")); err != nil {
		t.Fatal(err)
	}
	if !strings.HasPrefix(readValues(t, e.dashboardAuthPath())["DASHBOARD_PASSWORD_HASH"], "pbkdf2-sha256:600000:") {
		t.Fatal("dashboard hash not written")
	}
	for _, leaked := range []string{w.Secret(), "test-only-value", "correct horse battery"} {
		if strings.Contains(out.String(), leaked) {
			t.Fatal("secret written to the log")
		}
	}
	e.LeaveSetupMode()
	if _, err := e.WriteSecret(TerminalSource(), "REDISCLI_AUTH", []byte("x")); err == nil {
		t.Fatal("write accepted after leaving setup mode")
	}
}

func TestApplyActionsOrderAndSecretOnStdin(t *testing.T) {
	e, log, _ := testEngine(t)
	e.EnterSetupMode()
	os.MkdirAll(e.opts.ProfileDir, 0o700)
	os.WriteFile(e.subscriptionPath(), []byte(`{"dlmm-signal":{"secret":"dlmm-signal-secret-change-me"}}`), 0o600)
	log.fn = func(req ExecRequest) (CommandResult, error) {
		if req.Name == "python3" {
			return CommandResult{Output: "set\n"}, nil
		}
		return CommandResult{}, nil
	}
	hash, err := HashDashboardPassword("correct horse battery")
	if err != nil {
		t.Fatal(err)
	}
	p := Plan{Install: &InstallRequest{WithDashboard: true, NoBuild: true}, Linger: true, DashboardHash: hash, SyncWebhookSecret: true, Source: TerminalSource()}
	p.Set(DaemonEnv, "HERMES_WEBHOOK_SECRET", "0123abcd")
	if err := e.Apply(context.Background(), p); err != nil {
		t.Fatal(err)
	}
	var names []string
	for _, r := range log.reqs {
		names = append(names, r.Name)
		if strings.Contains(strings.Join(r.Args, " "), "0123abcd") {
			t.Fatal("secret passed in argv")
		}
	}
	if strings.Join(names, ",") != "bash,python3,loginctl" {
		t.Fatalf("unexpected action order %v", names)
	}
	if got := strings.Join(log.reqs[0].Args[1:], " "); got != e.opts.ProfileDir+" --with-dashboard --no-build" {
		t.Fatalf("install.sh args: %s", got)
	}
	if string(log.reqs[1].Stdin) != "0123abcd" {
		t.Fatal("webhook secret not passed on stdin")
	}
	drop, _ := os.ReadFile(e.dashboardDropinPath())
	if string(drop) != "[Service]\nEnvironmentFile=%h/.config/azimuth/dashboard-auth.env\n" {
		t.Fatal("dashboard drop-in content")
	}
}

func TestSubscriptionScriptKeepsRealSecret(t *testing.T) {
	if _, err := exec.LookPath("python3"); err != nil {
		t.Skip("python3 unavailable")
	}
	dir := t.TempDir()
	path := filepath.Join(dir, "subs.json")
	run := func(content string) (string, map[string]any) {
		os.WriteFile(path, []byte(content), 0o644)
		res, err := execCommand(context.Background(), ExecRequest{Name: "python3", Args: []string{"-I", "-c", subscriptionScript, path}, Stdin: []byte("new-secret")})
		if err != nil {
			t.Fatal(err)
		}
		var d map[string]any
		data, _ := os.ReadFile(path)
		json.Unmarshal(data, &d)
		return strings.TrimSpace(res.Output), d
	}
	if out, d := run(`{"dlmm-signal":{"secret":"dlmm-signal-secret-change-me","prompt":"p"},"other":{}}`); out != "set" || d["dlmm-signal"].(map[string]any)["secret"] != "new-secret" || d["other"] == nil {
		t.Fatal("placeholder not replaced")
	}
	if info, _ := os.Stat(path); info.Mode().Perm() != 0o600 {
		t.Fatal("subscription file not rewritten 0600")
	}
	if out, d := run(`{"dlmm-signal":{"secret":"operator-set"}}`); out != "kept" || d["dlmm-signal"].(map[string]any)["secret"] != "operator-set" {
		t.Fatal("operator secret overwritten")
	}
}
