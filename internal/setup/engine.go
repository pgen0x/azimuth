package setup

import (
	"bytes"
	"context"
	"crypto/rand"
	"encoding/hex"
	"errors"
	"fmt"
	"io"
	"net"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"slices"
	"strings"
	"time"

	"github.com/pgen0x/azimuth/internal/pwhash"
)

// The setup engine is the one place configuration is written. The CLI wizard
// (`azimuth setup`) drives it today; the planned localhost-only dashboard
// wizard is meant to drive the same Plan/Apply and WriteSecret calls, so every
// safety rule lives here rather than in a front end:
//   - DRY_RUN=true is written unless a plan carries a typed live confirmation;
//   - secrets are written 0600 and never appear in a log, plan description or error;
//   - re-runs edit files in place and keep keys setup does not own.

// Target names the file a change lands in.
type Target string

const (
	// DaemonEnv is <repo>/.env, the azimuth.service EnvironmentFile.
	DaemonEnv Target = "daemon"
	// ProfileEnv is <profile>/.env, read by the executor and the monitor loop.
	// It holds the wallet key; the daemon never reads it.
	ProfileEnv Target = "profile"
)

// LivePhrase must be typed exactly to set DRY_RUN to anything but "true".
const LivePhrase = "I UNDERSTAND THIS TRADES REAL FUNDS"

// webhookPlaceholder is the repo's shipped secret; it is never a real value.
const webhookPlaceholder = "dlmm-signal-secret-change-me"

// ErrLiveNotConfirmed is returned when a plan would go live without the phrase.
var ErrLiveNotConfirmed = errors.New("going live requires the typed confirmation phrase")

// ProfileVariables are the profile .env keys setup owns. They are not in the
// daemon schema because the daemon never reads them.
var ProfileVariables = []Variable{
	{Name: "SOLANA_PUBLIC_KEY", Description: "Wallet public key the executor and monitor act for.", Kind: "pubkey"},
	{Name: "SOLANA_PRIVATE_KEY", Description: "Wallet private key (base58) that signs transactions.", Kind: "string", Secret: true},
	{Name: "SOLANA_RPC_URLS", Description: "Comma-separated Solana RPC endpoints, tried in order.", Kind: "urls", Secret: true},
	{Name: "DRY_RUN", Description: "true = executor simulates every transaction.", Kind: "enum", Choices: []string{"true", "false"}, Default: "true"},
	{Name: "DLMM_ALERT_TARGET", Description: "Trade alert target for `hermes send` (e.g. telegram); empty disables.", Kind: "string"},
}

func lookupVariable(t Target, key string) (Variable, bool) {
	vars := ProfileVariables
	if t == DaemonEnv {
		vars = Schema()
	}
	for _, v := range vars {
		if v.Name == key {
			return v, true
		}
	}
	return Variable{}, false
}

// IsSecret reports whether a key's value must never be shown. Unknown keys
// are treated as secret.
func IsSecret(t Target, key string) bool {
	v, ok := lookupVariable(t, key)
	return !ok || v.Secret
}

// Change is one assignment in a plan.
type Change struct {
	Target Target
	Key    string
	Value  string
}

// InstallRequest maps one-to-one onto install.sh flags.
type InstallRequest struct {
	WithDashboard, WithAlerts, WithOps, WithRentReclaimSignsTx, WithResearch, NoBuild bool
}

// Args renders the install.sh argument list.
func (r InstallRequest) Args(profile string) []string {
	args := []string{profile}
	for _, f := range []struct {
		on   bool
		flag string
	}{{r.WithDashboard, "--with-dashboard"}, {r.WithAlerts, "--with-alerts"}, {r.WithOps, "--with-ops"},
		{r.WithRentReclaimSignsTx, "--with-rent-reclaim-signs-tx"}, {r.WithResearch, "--with-research"}, {r.NoBuild, "--no-build"}} {
		if f.on {
			args = append(args, f.flag)
		}
	}
	return args
}

// Plan is everything one setup run will change. Nothing is written until Apply.
type Plan struct {
	Changes []Change
	// Install runs install.sh with these flags after the env files are written.
	Install *InstallRequest
	// Linger runs `loginctl enable-linger` for the current user.
	Linger bool
	// DashboardHash is a pwhash value written to ~/.config/azimuth/dashboard-auth.env.
	DashboardHash string
	// SyncWebhookSecret copies HERMES_WEBHOOK_SECRET into the profile's
	// webhook_subscriptions.json when the entry there is missing or the placeholder.
	SyncWebhookSecret bool
	// Source attests where the plan's secrets came from. A plan that writes a
	// secret is refused without a trusted source and setup mode, so a front
	// end cannot route around WriteSecret's checks through Apply.
	Source SecretSource

	liveConfirmed bool
}

// hasSecrets reports whether applying the plan writes secret material.
func (p *Plan) hasSecrets() bool {
	if p.DashboardHash != "" {
		return true
	}
	for _, c := range p.Changes {
		if c.Value != "" && IsSecret(c.Target, c.Key) {
			return true
		}
	}
	return false
}

// Set records an assignment, replacing an earlier one for the same key.
func (p *Plan) Set(t Target, key, value string) {
	for i, c := range p.Changes {
		if c.Target == t && c.Key == key {
			p.Changes[i].Value = value
			return
		}
	}
	p.Changes = append(p.Changes, Change{t, key, value})
}

// Get returns a planned value.
func (p *Plan) Get(t Target, key string) (string, bool) {
	for _, c := range p.Changes {
		if c.Target == t && c.Key == key {
			return c.Value, true
		}
	}
	return "", false
}

// GoesLive reports whether any DRY_RUN change disables dry runs.
func (p *Plan) GoesLive() bool {
	for _, c := range p.Changes {
		if c.Key == "DRY_RUN" && c.Value != "true" {
			return true
		}
	}
	return false
}

// ConfirmLive arms a live plan. The phrase must match LivePhrase exactly.
func (p *Plan) ConfirmLive(phrase string) error {
	if strings.TrimSpace(phrase) != LivePhrase {
		return ErrLiveNotConfirmed
	}
	p.liveConfirmed = true
	return nil
}

// ExecRequest is one external command. Stdin carries secrets when needed, so
// they never appear in argv or the environment of a listed process.
type ExecRequest struct {
	Name   string
	Args   []string
	Env    []string
	Dir    string
	Stdin  []byte
	Stdout io.Writer // nil keeps output bounded and returns it in CommandResult
}

// Executor runs commands; tests replace it so nothing touches the host.
type Executor func(ctx context.Context, req ExecRequest) (CommandResult, error)

// EngineOptions names every input explicitly.
type EngineOptions struct {
	RepoDir      string
	EnvFile      string // default <repo>/.env
	ProfileDir   string // default ~/.hermes/profiles/dlmm
	HomeDir      string
	HermesRoot   string
	HermesPython string
	Timeout      time.Duration
	Exec         Executor
	LookPath     func(string) (string, error)
	HTTPClient   HTTPDoer
	// Log receives progress lines. Secrets are never written to it.
	Log io.Writer
}

// Engine applies setup plans.
type Engine struct {
	opts      EngineOptions
	setupMode bool
}

// NewEngine fills defaults the same way Doctor does.
func NewEngine(opts EngineOptions) *Engine {
	if opts.RepoDir == "" {
		opts.RepoDir = "."
	}
	if abs, err := filepath.Abs(opts.RepoDir); err == nil {
		opts.RepoDir = abs
	}
	if opts.EnvFile == "" {
		opts.EnvFile = filepath.Join(opts.RepoDir, ".env")
	}
	if opts.HomeDir == "" {
		opts.HomeDir, _ = os.UserHomeDir()
	}
	if opts.ProfileDir == "" {
		opts.ProfileDir = filepath.Join(opts.HomeDir, ".hermes", "profiles", "dlmm")
	}
	if abs, err := filepath.Abs(opts.ProfileDir); err == nil {
		opts.ProfileDir = abs
	}
	if opts.Timeout <= 0 {
		opts.Timeout = 10 * time.Second
	}
	if opts.Exec == nil {
		opts.Exec = execCommand
	}
	if opts.LookPath == nil {
		opts.LookPath = exec.LookPath
	}
	if opts.Log == nil {
		opts.Log = io.Discard
	}
	return &Engine{opts: opts}
}

// Options returns the resolved options.
func (e *Engine) Options() EngineOptions { return e.opts }

// EnterSetupMode allows WriteSecret. A long-running front end (the planned web
// wizard) enables it only while its setup flow is open and calls
// LeaveSetupMode when the flow ends.
func (e *Engine) EnterSetupMode() { e.setupMode = true }

// LeaveSetupMode disables WriteSecret again.
func (e *Engine) LeaveSetupMode() { e.setupMode = false }

// Path returns the env file a target writes to.
func (e *Engine) Path(t Target) string {
	if t == ProfileEnv {
		return filepath.Join(e.opts.ProfileDir, ".env")
	}
	return e.opts.EnvFile
}

// State is the current configuration with secret values withheld.
type State struct {
	DaemonExists, ProfileExists bool
	// Daemon and Profile hold non-secret values only.
	Daemon, Profile map[string]string
	// SecretSet reports, per target, which secret keys hold a real value.
	SecretSet map[Target]map[string]bool
}

// Value returns a non-secret current value.
func (s State) Value(t Target, key string) string {
	if t == ProfileEnv {
		return s.Profile[key]
	}
	return s.Daemon[key]
}

// Load reads both env files. Secret values never leave this function.
func (e *Engine) Load() (State, error) {
	st := State{Daemon: map[string]string{}, Profile: map[string]string{}, SecretSet: map[Target]map[string]bool{DaemonEnv: {}, ProfileEnv: {}}}
	for _, t := range []Target{DaemonEnv, ProfileEnv} {
		doc, exists, err := ReadEnvDoc(e.Path(t))
		if err != nil {
			return st, fmt.Errorf("%s config: %w", t, err)
		}
		if t == DaemonEnv {
			st.DaemonExists = exists
		} else {
			st.ProfileExists = exists
		}
		if doc == nil {
			continue
		}
		dst := st.Daemon
		if t == ProfileEnv {
			dst = st.Profile
		}
		for k, v := range doc.Values() {
			if IsSecret(t, k) {
				st.SecretSet[t][k] = v != "" && v != webhookPlaceholder
				continue
			}
			dst[k] = v
		}
	}
	return st, nil
}

// DiffLine is one planned change as shown to the operator.
type DiffLine struct {
	Target Target
	File   string
	Key    string
	Shown  string // value, or a mask for secrets
	Status string // "set" or "unchanged"
}

// Describe lists the plan without secret values. Unchanged keys are reported
// as such so a re-run shows it would do nothing.
func (e *Engine) Describe(p Plan) ([]DiffLine, error) {
	current := map[Target]map[string]string{}
	for _, t := range []Target{DaemonEnv, ProfileEnv} {
		doc, exists, err := ReadEnvDoc(e.Path(t))
		if err != nil {
			return nil, fmt.Errorf("%s config: %w", t, err)
		}
		if !exists {
			doc = e.template(t)
		}
		current[t] = doc.Values()
	}
	var out []DiffLine
	for _, c := range p.Changes {
		shown := c.Value
		if IsSecret(c.Target, c.Key) {
			shown = "<secret>"
			if c.Value == "" {
				shown = "<empty>"
			}
		}
		status := "set"
		if old, ok := current[c.Target][c.Key]; (ok && old == c.Value) || (!ok && c.Value == "") {
			status = "unchanged"
		}
		out = append(out, DiffLine{c.Target, e.Path(c.Target), c.Key, shown, status})
	}
	return out, nil
}

// WritePlanDescription renders Describe plus the non-file actions.
func (e *Engine) WritePlanDescription(w io.Writer, p Plan) error {
	lines, err := e.Describe(p)
	if err != nil {
		return err
	}
	for _, t := range []Target{DaemonEnv, ProfileEnv} {
		header := false
		for _, l := range lines {
			if l.Target != t {
				continue
			}
			if !header {
				fmt.Fprintf(w, "  %s:\n", l.File)
				header = true
			}
			fmt.Fprintf(w, "    %-9s %s=%s\n", l.Status, l.Key, l.Shown)
		}
	}
	if p.DashboardHash != "" {
		fmt.Fprintf(w, "  write %s (DASHBOARD_PASSWORD_HASH=<secret>)\n", e.dashboardAuthPath())
		fmt.Fprintf(w, "  write %s\n", e.dashboardDropinPath())
	}
	if p.Install != nil {
		fmt.Fprintf(w, "  run   %s %s\n", filepath.Join(e.opts.RepoDir, "install.sh"), strings.Join(p.Install.Args(e.opts.ProfileDir), " "))
	}
	if p.SyncWebhookSecret {
		fmt.Fprintf(w, "  sync  %s (dlmm-signal.secret=<secret>, only if missing or the placeholder)\n", e.subscriptionPath())
	}
	if p.Linger {
		fmt.Fprintln(w, "  run   loginctl enable-linger")
	}
	if p.GoesLive() {
		fmt.Fprintln(w, "  ⚠ DRY_RUN=false: positions will be opened with real funds.")
	}
	return nil
}

// Apply writes the plan. Order: env files, dashboard auth, install.sh, webhook
// secret sync, linger. Validation and the live gate run before any write.
func (e *Engine) Apply(ctx context.Context, p Plan) error {
	if p.GoesLive() && !p.liveConfirmed {
		return ErrLiveNotConfirmed
	}
	if p.hasSecrets() {
		if !e.setupMode {
			return errors.New("secret writes are only accepted in setup mode")
		}
		if p.Source == nil {
			return errors.New("secret source is not trusted")
		}
		if err := p.Source.trustedLocal(); err != nil {
			return err
		}
	}
	for _, c := range p.Changes {
		if c.Key == "SOLANA_PRIVATE_KEY" && c.Target != ProfileEnv {
			return errors.New("SOLANA_PRIVATE_KEY belongs in the profile .env only")
		}
		if v, ok := lookupVariable(c.Target, c.Key); ok && v.Validate(c.Value) != nil {
			return fmt.Errorf("%s: value does not match the schema (%s)", c.Key, v.Kind)
		}
		if _, err := FormatEnvValue(c.Value); err != nil {
			return fmt.Errorf("%s: %w", c.Key, err)
		}
	}
	for _, t := range []Target{DaemonEnv, ProfileEnv} {
		var changes []Change
		for _, c := range p.Changes {
			if c.Target == t {
				changes = append(changes, c)
			}
		}
		if err := e.writeEnv(t, changes); err != nil {
			return err
		}
	}
	if p.DashboardHash != "" {
		if err := e.writeDashboardAuth(p.DashboardHash); err != nil {
			return err
		}
	}
	if p.Install != nil {
		fmt.Fprintln(e.opts.Log, "→ Running install.sh")
		res, err := e.opts.Exec(ctx, ExecRequest{Name: "bash", Args: append([]string{filepath.Join(e.opts.RepoDir, "install.sh")}, p.Install.Args(e.opts.ProfileDir)...), Dir: e.opts.RepoDir, Stdout: e.opts.Log})
		if err != nil || res.Code != 0 {
			return errors.New("install.sh failed; fix the reported step and re-run setup (it is idempotent)")
		}
	}
	if p.SyncWebhookSecret {
		if err := e.syncWebhookSecret(ctx); err != nil {
			return err
		}
	}
	if p.Linger {
		res, err := e.opts.Exec(ctx, ExecRequest{Name: "loginctl", Args: []string{"enable-linger"}})
		if err != nil || res.Code != 0 {
			fmt.Fprintln(e.opts.Log, "   ⚠ loginctl enable-linger failed; run it yourself (it may need your login password or sudo).")
		} else {
			fmt.Fprintln(e.opts.Log, "   linger enabled: user services survive logout and reboot")
		}
	}
	return nil
}

func (e *Engine) writeEnv(t Target, changes []Change) error {
	if len(changes) == 0 {
		return nil
	}
	path := e.Path(t)
	doc, exists, err := ReadEnvDoc(path)
	if err != nil {
		return fmt.Errorf("%s config: %w", t, err)
	}
	if !exists {
		doc = e.template(t)
	}
	before := doc.Bytes()
	for _, c := range changes {
		if err := doc.Set(c.Key, c.Value); err != nil {
			return err
		}
	}
	if exists && bytes.Equal(before, doc.Bytes()) {
		if err := os.Chmod(path, 0o600); err != nil {
			return errors.New("cannot set configuration permissions")
		}
		return nil
	}
	if t == ProfileEnv {
		if err := os.MkdirAll(e.opts.ProfileDir, 0o700); err != nil {
			return errors.New("cannot create profile directory")
		}
	}
	if err := WriteFile0600(path, doc.Bytes()); err != nil {
		return fmt.Errorf("%s config: %w", t, err)
	}
	fmt.Fprintf(e.opts.Log, "   wrote %s (0600)\n", path)
	return nil
}

// template seeds a new daemon config from .env.example so the operator gets
// every documented knob; a new profile config starts with a short header.
func (e *Engine) template(t Target) *EnvDoc {
	if t == DaemonEnv {
		if data, err := os.ReadFile(filepath.Join(e.opts.RepoDir, ".env.example")); err == nil {
			if doc, err := ParseEnvDoc(data); err == nil {
				return doc
			}
		}
		return &EnvDoc{}
	}
	doc, _ := ParseEnvDoc([]byte("# Hermes profile settings for the solana-dlmm skill (executor + monitor).\n# Holds the wallet private key: keep this file 0600 and back it up offline.\n"))
	return doc
}

func (e *Engine) dashboardAuthPath() string {
	return filepath.Join(e.opts.HomeDir, ".config", "azimuth", "dashboard-auth.env")
}

func (e *Engine) dashboardDropinPath() string {
	return filepath.Join(e.opts.HomeDir, ".config", "systemd", "user", "azimuth-dashboard.service.d", "auth.conf")
}

// writeDashboardAuth follows docs/DASHBOARD_DEPLOY.md#password-hash: the hash in
// a private file outside the repo, wired in by a drop-in.
func (e *Engine) writeDashboardAuth(hash string) error {
	if _, err := pwhash.Parse(hash); err != nil {
		return errors.New("dashboard password hash is malformed")
	}
	if err := WriteFile0600(e.dashboardAuthPath(), []byte("DASHBOARD_PASSWORD_HASH="+hash+"\n")); err != nil {
		return fmt.Errorf("dashboard auth: %w", err)
	}
	if err := os.MkdirAll(filepath.Dir(e.dashboardDropinPath()), 0o755); err != nil {
		return errors.New("cannot create dashboard drop-in directory")
	}
	if err := WriteFile0600(e.dashboardDropinPath(), []byte("[Service]\nEnvironmentFile=%h/.config/azimuth/dashboard-auth.env\n")); err != nil {
		return fmt.Errorf("dashboard drop-in: %w", err)
	}
	fmt.Fprintf(e.opts.Log, "   wrote %s (0600) and its drop-in; restart azimuth-dashboard if it is running\n", e.dashboardAuthPath())
	return nil
}

func (e *Engine) subscriptionPath() string {
	return filepath.Join(e.opts.ProfileDir, "webhook_subscriptions.json")
}

// subscriptionScript sets dlmm-signal.secret only when it is missing or the
// placeholder. The secret arrives on stdin, never argv; python keeps key order
// the way install.sh's own merge does.
const subscriptionScript = `import json, os, sys
path = sys.argv[1]
secret = sys.stdin.read()
d = json.load(open(path))
entry = d.get("dlmm-signal")
if not isinstance(entry, dict):
    print("missing"); sys.exit(0)
if entry.get("secret") not in (None, "", "dlmm-signal-secret-change-me"):
    print("kept"); sys.exit(0)
entry["secret"] = secret
tmp = path + ".setup-tmp"
fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
with os.fdopen(fd, "w") as f:
    json.dump(d, f, indent=2)
os.replace(tmp, path)
print("set")
`

func (e *Engine) syncWebhookSecret(ctx context.Context) error {
	doc, _, err := ReadEnvDoc(e.opts.EnvFile)
	if err != nil || doc == nil {
		return errors.New("cannot read daemon config for the webhook secret")
	}
	secret := doc.Values()["HERMES_WEBHOOK_SECRET"]
	if secret == "" || secret == webhookPlaceholder {
		return errors.New("HERMES_WEBHOOK_SECRET is not set")
	}
	if info, err := os.Lstat(e.subscriptionPath()); err != nil || !info.Mode().IsRegular() {
		fmt.Fprintln(e.opts.Log, "   ⚠ webhook_subscriptions.json not found; run install.sh, then re-run setup")
		return nil
	}
	res, err := e.opts.Exec(ctx, ExecRequest{Name: "python3", Args: []string{"-I", "-c", subscriptionScript, e.subscriptionPath()}, Stdin: []byte(secret)})
	if err != nil || res.Code != 0 {
		return errors.New("cannot update webhook_subscriptions.json")
	}
	switch strings.TrimSpace(res.Output) {
	case "set":
		fmt.Fprintln(e.opts.Log, "   webhook subscription secret set; restart the Hermes gateway to load it")
	case "kept":
		fmt.Fprintln(e.opts.Log, "   webhook subscription already has a secret; kept it (it must match HERMES_WEBHOOK_SECRET)")
	default:
		fmt.Fprintln(e.opts.Log, "   ⚠ no dlmm-signal entry in webhook_subscriptions.json; run install.sh")
	}
	return nil
}

// NewWebhookSecret returns 32 random bytes as hex.
func NewWebhookSecret() (string, error) {
	b := make([]byte, 32)
	if _, err := rand.Read(b); err != nil {
		return "", errors.New("cannot generate secret")
	}
	return hex.EncodeToString(b), nil
}

// ── Trusted local secret writes ───────────────────────────────────────────

// SecretSource attests where a secret came from. Only this package can
// implement it, so a caller cannot invent its own notion of "trusted".
type SecretSource interface {
	trustedLocal() error
}

type terminalSource struct{}

func (terminalSource) trustedLocal() error { return nil }

// TerminalSource is for a secret the local operator typed (with echo off) or
// supplied from a file they own.
func TerminalSource() SecretSource { return terminalSource{} }

type loopbackSource struct{ r *http.Request }

// LoopbackRequestSource attests an HTTP request for the planned web wizard.
// It is trusted only when the listener and the peer are both loopback (direct
// or through an SSH tunnel), the Host header names loopback (blocks DNS
// rebinding), and no proxy forwarding header is present.
func LoopbackRequestSource(r *http.Request) SecretSource { return loopbackSource{r} }

func loopbackIP(hostport string) bool {
	host := hostport
	if h, _, err := net.SplitHostPort(hostport); err == nil {
		host = h
	}
	ip := net.ParseIP(strings.Trim(host, "[]"))
	return ip != nil && ip.IsLoopback()
}

func loopbackHostHeader(host string) bool {
	if h, _, err := net.SplitHostPort(host); err == nil {
		host = h
	}
	return strings.EqualFold(host, "localhost") || loopbackIP(host)
}

func (s loopbackSource) trustedLocal() error {
	r := s.r
	if r == nil {
		return errors.New("secret source is not trusted")
	}
	if !loopbackIP(r.RemoteAddr) {
		return errors.New("secret writes are accepted from loopback peers only")
	}
	local, ok := r.Context().Value(http.LocalAddrContextKey).(net.Addr)
	if !ok || !loopbackIP(local.String()) {
		return errors.New("secret writes require a loopback-bound listener")
	}
	if !loopbackHostHeader(r.Host) {
		return errors.New("secret writes require a loopback Host header")
	}
	for _, h := range []string{"Forwarded", "X-Forwarded-For", "X-Forwarded-Host", "X-Real-Ip"} {
		if r.Header.Get(h) != "" {
			return errors.New("secret writes are refused through a proxy")
		}
	}
	return nil
}

// SecretKeys are the secrets WriteSecret accepts. DASHBOARD_PASSWORD is the
// plain password; only its hash is stored.
var SecretKeys = []string{"SOLANA_PRIVATE_KEY", "HERMES_WEBHOOK_SECRET", "REDISCLI_AUTH", "GMGN_API_KEY", "BIRDEYE_API_KEY", "DASHBOARD_PASSWORD"}

// WriteSecret stores one secret from a trusted local caller, immediately and
// without a plan. value is zeroed before return. Nothing about the value is
// logged or returned; errors are fixed strings. It requires setup mode, and it
// cannot touch DRY_RUN, so it is never a path to going live.
//
// SOLANA_PRIVATE_KEY also writes the derived SOLANA_PUBLIC_KEY to both files;
// the returned string is that public key (empty for other keys).
func (e *Engine) WriteSecret(src SecretSource, key string, value []byte) (string, error) {
	defer clear(value)
	if !e.setupMode {
		return "", errors.New("secret writes are only accepted in setup mode")
	}
	if src == nil {
		return "", errors.New("secret source is not trusted")
	}
	if err := src.trustedLocal(); err != nil {
		return "", err
	}
	if !slices.Contains(SecretKeys, key) {
		return "", errors.New("not a setup-managed secret")
	}
	text := strings.TrimSpace(string(value))
	if text == "" {
		return "", errors.New("secret is empty")
	}
	switch key {
	case "SOLANA_PRIVATE_KEY":
		w, err := ParsePrivateKey([]byte(text))
		if err != nil {
			return "", err
		}
		if err := e.writeEnv(ProfileEnv, []Change{{ProfileEnv, "SOLANA_PRIVATE_KEY", w.Secret()}, {ProfileEnv, "SOLANA_PUBLIC_KEY", w.PublicKey}}); err != nil {
			return "", err
		}
		return w.PublicKey, e.writeEnv(DaemonEnv, []Change{{DaemonEnv, "SOLANA_PUBLIC_KEY", w.PublicKey}})
	case "DASHBOARD_PASSWORD":
		hash, err := HashDashboardPassword(text)
		if err != nil {
			return "", err
		}
		return "", e.writeDashboardAuth(hash)
	default:
		if _, err := FormatEnvValue(text); err != nil {
			return "", errors.New("secret contains characters a dotenv file cannot hold literally")
		}
		return "", e.writeEnv(DaemonEnv, []Change{{DaemonEnv, key, text}})
	}
}

// HashDashboardPassword enforces a minimum length and returns the pwhash value.
func HashDashboardPassword(password string) (string, error) {
	if len(password) < 12 {
		return "", errors.New("dashboard password must be at least 12 characters")
	}
	hash, err := pwhash.Hash(password, pwhash.DefaultIterations)
	if err != nil {
		return "", errors.New("cannot hash dashboard password")
	}
	return hash, nil
}

// ── Live tests used by the wizard steps ───────────────────────────────────

// currentValue reads one value from a target file, for engine-internal use
// only; secret values never leave the engine through it.
func (e *Engine) currentValue(t Target, key string) string {
	doc, _, err := ReadEnvDoc(e.Path(t))
	if err != nil || doc == nil {
		return ""
	}
	return doc.Values()[key]
}

// TestRPC runs read-only getHealth against each endpoint and, when pubkey is
// set, getBalance on the first healthy one. Reuses doctor's checks. Empty
// endpoints tests the configured ones (profile first) without exposing them.
func (e *Engine) TestRPC(ctx context.Context, endpoints, pubkey string) Report {
	if endpoints == "" {
		if endpoints = e.currentValue(ProfileEnv, "SOLANA_RPC_URLS"); endpoints == "" {
			endpoints = e.currentValue(DaemonEnv, "SOLANA_RPC_URLS")
		}
	}
	d := doctor{opts: DoctorOptions{Timeout: e.opts.Timeout, HTTPClient: e.opts.HTTPClient}, values: map[string]string{"SOLANA_RPC_URLS": endpoints, "SOLANA_PUBLIC_KEY": pubkey}}
	d.rpc(ctx)
	return d.report
}

// AICommands returns the DEPLOY_CMD and AI_HEALTH_CMD for this profile, plus
// the probe argv that runs the same script from the repo (the profile's
// symlink may not exist before install.sh).
func (e *Engine) AICommands() (deploy, health string, probe []string, err error) {
	if strings.ContainsAny(e.opts.ProfileDir+e.opts.RepoDir, " \t'") {
		return "", "", nil, errors.New("profile and repo paths must not contain spaces or quotes (commands are whitespace-split)")
	}
	scripts := filepath.Join(e.opts.ProfileDir, "skills", "solana-dlmm", "scripts")
	deploy = "python3 " + filepath.Join(scripts, "dlmm_pipeline.py")
	python, root := e.hermesRuntime()
	if python == "" {
		return deploy, "", nil, errors.New("Hermes' bundled Python was not found; pass --hermes-python")
	}
	if strings.ContainsAny(python+root, " \t'") {
		return deploy, "", nil, errors.New("Hermes paths must not contain spaces or quotes")
	}
	health = strings.Join([]string{python, filepath.Join(scripts, "dlmm_ai_health.py"), "--profile", e.opts.ProfileDir, "--hermes-root", root}, " ")
	probe = []string{python, filepath.Join(e.opts.RepoDir, "assets", "skill", "scripts", "dlmm_ai_health.py"), "--profile", e.opts.ProfileDir, "--hermes-root", root}
	return deploy, health, probe, nil
}

func (e *Engine) hermesRuntime() (python, root string) {
	base := os.Getenv("HERMES_HOME_BASE")
	if base == "" {
		base = filepath.Join(e.opts.HomeDir, ".hermes")
	}
	root = e.opts.HermesRoot
	if root == "" {
		root = filepath.Join(base, "hermes-agent")
	}
	python = e.opts.HermesPython
	if python == "" {
		python = newestBundledPython(base)
	}
	return python, root
}

// TestAI runs the read-only AI health probe (65s deadline, like the daemon).
func (e *Engine) TestAI(ctx context.Context, probe []string) Check {
	if len(probe) == 0 {
		return Check{"ai.probe", Fail, "No probe command.", "Install Hermes or choose the deterministic route."}
	}
	ctx, cancel := context.WithTimeout(ctx, 65*time.Second)
	defer cancel()
	res, err := e.opts.Exec(ctx, ExecRequest{Name: probe[0], Args: probe[1:], Env: []string{"PYTHONDONTWRITEBYTECODE=1"}})
	switch {
	case res.Code == 14:
		return Check{"ai.probe", Fail, "AI probe returned config_error (exit 14).", "Repair the Hermes runtime or provider configuration; until then AI-first falls back to deterministic every batch."}
	case err != nil || res.Code != 0:
		return Check{"ai.probe", Fail, "AI probe did not succeed.", "Check the Hermes model/provider; AI-first falls back to deterministic while it fails."}
	}
	return Check{"ai.probe", Pass, "AI probe succeeded.", ""}
}

// ReportCommand is the REPORT_CMD setup writes for Telegram delivery.
const ReportCommand = "hermes send -t telegram"

// TestTelegram sends one test message through the same command the daemon uses.
func (e *Engine) TestTelegram(ctx context.Context) Check {
	ctx, cancel := context.WithTimeout(ctx, 30*time.Second)
	defer cancel()
	args := strings.Fields(ReportCommand)
	res, err := e.opts.Exec(ctx, ExecRequest{Name: args[0], Args: args[1:], Stdin: []byte("azimuth setup: test message. Trade reports will arrive here.\n")})
	if err != nil || res.Code != 0 {
		return Check{"telegram", Fail, "Test message was not sent.", "Configure Telegram in Hermes (hermes gateway setup), then re-run setup."}
	}
	return Check{"telegram", Pass, "Test message sent.", ""}
}

// Doctor runs the read-only doctor against this engine's files.
func (e *Engine) Doctor(ctx context.Context) Report {
	return Doctor(ctx, DoctorOptions{RepoDir: e.opts.RepoDir, EnvFile: e.opts.EnvFile, ProfileDir: e.opts.ProfileDir, HomeDir: e.opts.HomeDir,
		HermesRoot: e.opts.HermesRoot, HermesPython: e.opts.HermesPython, LookPath: e.opts.LookPath, HTTPClient: e.opts.HTTPClient,
		Run: func(ctx context.Context, name string, args, env []string, dir string) (CommandResult, error) {
			return e.opts.Exec(ctx, ExecRequest{Name: name, Args: args, Env: env, Dir: dir})
		}})
}

func execCommand(ctx context.Context, req ExecRequest) (CommandResult, error) {
	cmd := exec.CommandContext(ctx, req.Name, req.Args...)
	cmd.Dir = req.Dir
	cmd.Env = append(os.Environ(), req.Env...)
	cmd.WaitDelay = time.Second
	if req.Stdin != nil {
		cmd.Stdin = bytes.NewReader(req.Stdin)
	}
	var out boundedOutput
	if req.Stdout != nil {
		cmd.Stdout, cmd.Stderr = req.Stdout, req.Stdout
	} else {
		cmd.Stdout, cmd.Stderr = &out, &out
	}
	err := cmd.Run()
	code := 0
	if err != nil {
		code = -1
		var ee *exec.ExitError
		if errors.As(err, &ee) {
			code = ee.ExitCode()
		}
	}
	return CommandResult{code, string(out.data)}, err
}
