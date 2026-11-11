package setup

import (
	"bufio"
	"context"
	"errors"
	"flag"
	"fmt"
	"io"
	"os"
	"slices"
	"strings"
	"time"
)

// SetupIO is the wizard's I/O. ReadSecret reads one hidden line; the CLI's
// default refuses anything that is not a terminal.
type SetupIO struct {
	In         io.Reader
	Out, Err   io.Writer
	ReadSecret func(prompt string) ([]byte, error)
	// Engine overrides engine options (tests inject Exec/HTTP/LookPath).
	Engine func(*EngineOptions)
}

// RunSetupCLI is `azimuth setup`.
func RunSetupCLI(ctx context.Context, args []string, stdin *os.File, out, errOut io.Writer) int {
	return RunSetup(ctx, args, SetupIO{In: stdin, Out: out, Err: errOut, ReadSecret: func(prompt string) ([]byte, error) {
		fmt.Fprint(out, prompt)
		defer fmt.Fprintln(out)
		return readNoEcho(stdin)
	}})
}

type setupFlags struct {
	nonInteractive, dryRun, skipPreflight, skipTests, skipDoctor bool
	modes, route, wallet, privateKeyFile, rpcURLs, telegram      string
	replaceWallet, live, simulate, install, linger               bool
	confirmLive                                                  string
	inst                                                         InstallRequest
	dashboardPasswordFile, gmgnKeyFile                           string
	sets                                                         multiFlag
}

type multiFlag []string

func (m *multiFlag) String() string     { return strings.Join(*m, ",") }
func (m *multiFlag) Set(v string) error { *m = append(*m, v); return nil }

type discoveryMode struct{ name, key, help string }

// discoveryModes are the Solana screens setup offers, in display order.
var discoveryModes = []discoveryMode{
	{"casual", "ENABLE_CASUAL", "30m fee/TVL screen over established pools"},
	{"multiday", "ENABLE_MULTIDAY", "24h screen for deeper, slower pools"},
	{"turnover", "ENABLE_TURNOVER", "fee-capture screen, fast churn"},
	{"pulse", "ENABLE_PULSE", "5m trending screen"},
}

// riskKeys are the daemon's entry-gate knobs offered in the sizing/risk step.
var riskKeys = []string{"LONE_MIN_SCORE", "ENABLE_MOMENTUM_GATE", "ENABLE_AUDIT_GATE", "ENABLE_PVP_CHECK", "ENABLE_GMGN_GATE", "GMGN_MAX_RAT_PCT", "GMGN_MAX_BUNDLER_PCT", "DEPLOY_TIMEOUT"}

const defaultRPC = "https://api.mainnet-beta.solana.com"

type wizard struct {
	ctx      context.Context
	e        *Engine
	io       SetupIO
	in       *bufio.Reader
	f        setupFlags
	st       State
	plan     Plan
	tests    bool
	exitCode int
}

// RunSetup is the testable entry point. Exit code: 1 on error, otherwise the
// closing doctor's code (0 all pass, 1 any FAIL, 2 WARN only); 0 for --dry-run.
func RunSetup(ctx context.Context, args []string, sio SetupIO) int {
	fs := flag.NewFlagSet("azimuth setup", flag.ContinueOnError)
	fs.SetOutput(io.Discard)
	var f setupFlags
	var opts EngineOptions
	fs.StringVar(&opts.RepoDir, "repo", ".", "repository root")
	fs.StringVar(&opts.EnvFile, "env-file", "", "daemon config (default <repo>/.env)")
	fs.StringVar(&opts.ProfileDir, "profile", "", "Hermes profile (default ~/.hermes/profiles/dlmm)")
	fs.StringVar(&opts.HermesRoot, "hermes-root", "", "Hermes source checkout (default <HERMES_HOME_BASE>/hermes-agent)")
	fs.StringVar(&opts.HermesPython, "hermes-python", "", "Hermes bundled Python (default: newest under <HERMES_HOME_BASE>/tools)")
	fs.BoolVar(&f.nonInteractive, "non-interactive", false, "never prompt; answers come from flags (unset flags keep current values)")
	fs.BoolVar(&f.dryRun, "dry-run", false, "print the planned changes and write nothing")
	fs.BoolVar(&f.skipPreflight, "skip-preflight", false, "skip the opening doctor run")
	fs.BoolVar(&f.skipDoctor, "skip-doctor", false, "skip the closing doctor run")
	fs.BoolVar(&f.skipTests, "skip-tests", false, "skip the live RPC, AI and Telegram tests")
	fs.StringVar(&f.modes, "modes", "", "comma-separated discovery modes to enable: casual,multiday,turnover,pulse")
	fs.StringVar(&f.route, "route", "", "entry route: deterministic or ai")
	fs.StringVar(&f.wallet, "wallet", "keep", "keep, generate or import")
	fs.StringVar(&f.privateKeyFile, "private-key-file", "", "file holding the private key to import (- = stdin)")
	fs.BoolVar(&f.replaceWallet, "replace-wallet", false, "allow --wallet generate/import to replace an existing key")
	fs.StringVar(&f.rpcURLs, "rpc-urls", "", "comma-separated Solana RPC URLs")
	fs.StringVar(&f.telegram, "telegram", "keep", "Telegram reports via `hermes send`: keep, on or off")
	fs.BoolVar(&f.live, "live", false, "set DRY_RUN=false (needs --confirm-live)")
	fs.BoolVar(&f.simulate, "simulate-trades", false, "set DRY_RUN=true (switch a live config back to dry run)")
	fs.StringVar(&f.confirmLive, "confirm-live", "", "the exact phrase: "+LivePhrase)
	fs.BoolVar(&f.install, "install", false, "run install.sh (systemd user units) after writing config")
	fs.BoolVar(&f.inst.WithDashboard, "with-dashboard", false, "install.sh --with-dashboard")
	fs.BoolVar(&f.inst.WithAlerts, "with-alerts", false, "install.sh --with-alerts")
	fs.BoolVar(&f.inst.WithOps, "with-ops", false, "install.sh --with-ops")
	fs.BoolVar(&f.inst.WithRentReclaimSignsTx, "with-rent-reclaim-signs-tx", false, "install.sh --with-rent-reclaim-signs-tx (SIGNS transactions)")
	fs.BoolVar(&f.inst.WithResearch, "with-research", false, "install.sh --with-research")
	fs.BoolVar(&f.inst.NoBuild, "no-build", false, "install.sh --no-build")
	fs.BoolVar(&f.linger, "linger", false, "run loginctl enable-linger")
	fs.StringVar(&f.dashboardPasswordFile, "dashboard-password-file", "", "file holding the dashboard password (- = stdin)")
	fs.StringVar(&f.gmgnKeyFile, "gmgn-api-key-file", "", "file holding GMGN_API_KEY (- = stdin)")
	fs.Var(&f.sets, "set", "KEY=VALUE for a non-secret daemon setting (repeatable)")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			fmt.Fprintln(sio.Out, "Usage: azimuth setup [flags]\n\nInteractive by default; re-running edits the existing config and keeps keys it does not own.")
			fs.SetOutput(sio.Out)
			fs.PrintDefaults()
			fmt.Fprintln(sio.Out, "\nDRY_RUN: a new config gets true. An existing value only changes with --simulate-trades (true)")
			fmt.Fprintln(sio.Out, "or --live --confirm-live '"+LivePhrase+"' (false).")
			return 0
		}
		fmt.Fprintln(sio.Err, "Invalid setup arguments. Use azimuth setup --help.")
		return 1
	}
	if fs.NArg() != 0 {
		fmt.Fprintln(sio.Err, "Setup takes flags only. Use azimuth setup --help.")
		return 1
	}
	opts.Log = sio.Out
	if sio.Engine != nil {
		sio.Engine(&opts)
	}
	w := &wizard{ctx: ctx, e: NewEngine(opts), io: sio, in: bufio.NewReader(sio.In), f: f, tests: !f.skipTests}
	if err := w.run(); err != nil {
		fmt.Fprintln(sio.Err, "setup: "+err.Error())
		return 1
	}
	return w.exitCode
}

func (w *wizard) interactive() bool { return !w.f.nonInteractive }

func (w *wizard) say(format string, a ...any) { fmt.Fprintf(w.io.Out, format+"\n", a...) }

func (w *wizard) ask(prompt, def string) (string, error) {
	if !w.interactive() {
		return def, nil
	}
	if def != "" {
		fmt.Fprintf(w.io.Out, "%s [%s]: ", prompt, def)
	} else {
		fmt.Fprintf(w.io.Out, "%s: ", prompt)
	}
	line, err := w.in.ReadString('\n')
	if err != nil && line == "" {
		return "", errors.New("input ended")
	}
	line = strings.TrimSpace(line)
	if line == "" {
		return def, nil
	}
	return line, nil
}

func (w *wizard) askBool(prompt string, def bool) (bool, error) {
	if !w.interactive() {
		return def, nil
	}
	hint := "y/N"
	if def {
		hint = "Y/n"
	}
	for range 3 {
		ans, err := w.ask(prompt+" ("+hint+")", "")
		if err != nil {
			return false, err
		}
		switch strings.ToLower(ans) {
		case "":
			return def, nil
		case "y", "yes":
			return true, nil
		case "n", "no":
			return false, nil
		}
		w.say("  please answer y or n")
	}
	return false, errors.New("no valid answer")
}

// askVar prompts for a schema value until it validates.
func (w *wizard) askVar(t Target, key, def string) (string, error) {
	v, _ := lookupVariable(t, key)
	for range 3 {
		ans, err := w.ask(fmt.Sprintf("%s — %s", key, v.Description), def)
		if err != nil {
			return "", err
		}
		if v.Validate(ans) == nil {
			return ans, nil
		}
		w.say("  not a valid %s", v.Kind)
	}
	return "", fmt.Errorf("%s: no valid answer", key)
}

func (w *wizard) secretFromFile(path string) ([]byte, error) {
	var r io.Reader
	if path == "-" {
		r = w.in
	} else {
		info, err := os.Stat(path)
		if err != nil {
			return nil, errors.New("cannot read the secret file")
		}
		if info.Mode().Perm()&0o077 != 0 {
			w.say("  ⚠ %s is readable by other users; chmod 600 it or delete it after setup", path)
		}
		f, err := os.Open(path)
		if err != nil {
			return nil, errors.New("cannot read the secret file")
		}
		defer f.Close()
		r = f
	}
	data, err := io.ReadAll(io.LimitReader(r, 4096))
	if err != nil {
		return nil, errors.New("cannot read the secret file")
	}
	defer clear(data)
	text := append([]byte(nil), trimSpaceBytes(data)...)
	if len(text) == 0 {
		return nil, errors.New("secret file is empty")
	}
	return text, nil
}

func trimSpaceBytes(b []byte) []byte {
	for len(b) > 0 && strings.ContainsRune(" \t\r\n", rune(b[0])) {
		b = b[1:]
	}
	for len(b) > 0 && strings.ContainsRune(" \t\r\n", rune(b[len(b)-1])) {
		b = b[:len(b)-1]
	}
	return b
}

func (w *wizard) readSecret(prompt string) ([]byte, error) {
	if w.io.ReadSecret == nil {
		return nil, errors.New("hidden input is unavailable")
	}
	return w.io.ReadSecret(prompt)
}

func (w *wizard) step(n int, title string) { w.say("\n[%d/9] %s", n, title) }

func (w *wizard) run() error {
	w.say("azimuth setup — every answer can be changed by re-running this command.")
	w.say("  daemon config:  %s", w.e.Path(DaemonEnv))
	w.say("  profile config: %s (the wallet key lives here)", w.e.Path(ProfileEnv))
	if w.f.dryRun {
		w.say("  --dry-run: nothing will be written")
	}
	if !w.interactive() && w.f.wallet == "import" && w.f.privateKeyFile == "" {
		return errors.New("--wallet import needs --private-key-file in non-interactive mode")
	}
	stdinSecrets := 0
	for _, p := range []string{w.f.privateKeyFile, w.f.dashboardPasswordFile, w.f.gmgnKeyFile} {
		if p == "-" {
			stdinSecrets++
		}
	}
	if stdinSecrets > 1 {
		return errors.New("only one secret can come from stdin")
	}
	if stdinSecrets == 1 && w.interactive() {
		return errors.New("reading a secret from stdin (-) needs --non-interactive")
	}
	st, err := w.e.Load()
	if err != nil {
		return err
	}
	w.st = st
	w.plan.Source = TerminalSource()
	w.e.EnterSetupMode()
	defer w.e.LeaveSetupMode()
	for _, s := range []func() error{w.preflight, w.modes, w.wallet, w.rpc, w.route, w.telegram, w.risk, w.install} {
		if err := s(); err != nil {
			return err
		}
	}
	return w.finish()
}

func (w *wizard) preflight() error {
	w.step(1, "Preflight (read-only doctor)")
	if w.f.skipPreflight {
		w.say("  skipped")
		return nil
	}
	r := w.e.Doctor(w.ctx)
	var shown Report
	for _, c := range r.Checks {
		if c.Status != Pass {
			shown.Checks = append(shown.Checks, c)
		}
	}
	if len(shown.Checks) == 0 {
		w.say("  all checks pass")
		return nil
	}
	w.say("  Issues before setup (the steps below fix many of them):")
	return shown.Write(w.io.Out, false)
}

func boolValue(s, def string) bool {
	if s == "" {
		s = def
	}
	return s == "true" || s == "1"
}

func (w *wizard) schemaDefault(key string) string {
	v, _ := lookupVariable(DaemonEnv, key)
	return v.Default
}

func (w *wizard) modes() error {
	w.step(2, "Discovery modes and dry run")
	var chosen []string
	if w.f.modes != "" {
		for _, m := range strings.Split(w.f.modes, ",") {
			m = strings.TrimSpace(m)
			if !slices.ContainsFunc(discoveryModes, func(d discoveryMode) bool { return d.name == m }) {
				return fmt.Errorf("unknown discovery mode %q", m)
			}
			chosen = append(chosen, m)
		}
	}
	for _, m := range discoveryModes {
		on := boolValue(w.st.Daemon[m.key], w.schemaDefault(m.key))
		if w.f.modes != "" {
			on = slices.Contains(chosen, m.name)
		} else {
			var err error
			if on, err = w.askBool(fmt.Sprintf("Enable %s (%s)?", m.name, m.help), on); err != nil {
				return err
			}
		}
		w.plan.Set(DaemonEnv, m.key, fmt.Sprint(on))
	}

	// Mirrors how the processes read it: the daemon passes its DRY_RUN to the
	// pipeline when set, and the executor/monitor treat anything but "true" in
	// the profile (including unset) as live.
	daemonDry, daemonSet := w.st.Daemon["DRY_RUN"]
	profileDry := w.st.Profile["DRY_RUN"]
	currentLive := (daemonSet && daemonDry != "true") || (w.st.ProfileExists && profileDry != "true")
	if w.f.live && w.f.simulate {
		return errors.New("--live and --simulate-trades conflict")
	}
	// DRY_RUN only changes on an explicit answer or flag. A re-run that edits
	// something else must never stop (or start) live trading as a side effect.
	dry := "true"
	switch {
	case w.f.simulate:
		if currentLive {
			w.say("  --simulate-trades: switching this LIVE config to DRY_RUN=true")
		}
	case w.interactive() && currentLive:
		keep, err := w.askBool("This config is currently LIVE (DRY_RUN is not true). Keep live trading? (n switches to dry run)", true)
		if err != nil {
			return err
		}
		if keep {
			w.say("  keeping the current DRY_RUN values unchanged (live)")
			return nil
		}
	case w.interactive():
		simulate, err := w.askBool("Keep DRY_RUN on (simulate every trade; recommended until doctor is clean)?", true)
		if err != nil {
			return err
		}
		if !simulate {
			w.say("  Going live opens positions with real funds. Type exactly:\n  %s", LivePhrase)
			phrase, err := w.ask("Confirmation", "")
			if err != nil {
				return err
			}
			if w.plan.ConfirmLive(phrase) == nil {
				dry = "false"
			} else {
				w.say("  phrase did not match; DRY_RUN stays true")
			}
		}
	case w.f.live:
		if err := w.plan.ConfirmLive(w.f.confirmLive); err != nil {
			return errors.New("--live needs --confirm-live with the exact phrase: " + LivePhrase)
		}
		dry = "false"
	case currentLive:
		w.say("  config is currently LIVE; DRY_RUN left unchanged (--simulate-trades switches to dry run)")
		return nil
	}
	w.plan.Set(DaemonEnv, "DRY_RUN", dry)
	w.plan.Set(ProfileEnv, "DRY_RUN", dry)
	return nil
}

func (w *wizard) wallet() error {
	w.step(3, "Wallet")
	has := w.st.SecretSet[ProfileEnv]["SOLANA_PRIVATE_KEY"]
	pub := w.st.Profile["SOLANA_PUBLIC_KEY"]
	choice := w.f.wallet
	if w.interactive() {
		def := "generate"
		if has {
			def = "keep"
			w.say("  current wallet: %s", orUnknown(pub))
		}
		var err error
		if choice, err = w.ask("Wallet: keep, generate (new keypair) or import", def); err != nil {
			return err
		}
	}
	switch choice {
	case "keep", "":
		if pub != "" && w.st.Daemon["SOLANA_PUBLIC_KEY"] != pub {
			w.plan.Set(DaemonEnv, "SOLANA_PUBLIC_KEY", pub)
		}
		if !has {
			w.say("  no wallet key configured; nothing can trade until one is added (re-run setup)")
		}
		return nil
	case "generate", "import":
	default:
		return fmt.Errorf("unknown wallet choice %q (keep, generate, import)", choice)
	}
	if has {
		if !w.interactive() && !w.f.replaceWallet {
			return errors.New("a wallet key already exists; pass --replace-wallet to replace it")
		}
		if w.interactive() {
			w.say("  ⚠ This replaces the existing key in %s. Funds on the old wallet need that key; back it up first.", w.e.Path(ProfileEnv))
			ans, err := w.ask("Type REPLACE to continue", "")
			if err != nil {
				return err
			}
			if ans != "REPLACE" {
				w.say("  kept the existing wallet")
				return nil
			}
		}
	}
	var wal Wallet
	var err error
	if choice == "generate" {
		if wal, err = GenerateWallet(); err != nil {
			return err
		}
		w.say("  new wallet: %s", wal.PublicKey)
		if w.f.dryRun {
			w.say("  (--dry-run: this key is discarded; a real run generates a new one)")
		} else {
			w.say("  Its private key is written only to %s (0600) and never printed. Back that file up offline.", w.e.Path(ProfileEnv))
		}
	} else {
		var raw []byte
		if w.f.privateKeyFile != "" {
			raw, err = w.secretFromFile(w.f.privateKeyFile)
		} else {
			raw, err = w.readSecret("Private key (base58 or solana-keygen JSON; input hidden): ")
		}
		if err != nil {
			return err
		}
		wal, err = ParsePrivateKey(raw)
		clear(raw)
		if err != nil {
			return err
		}
		w.say("  imported wallet: %s", wal.PublicKey)
	}
	w.plan.Set(ProfileEnv, "SOLANA_PRIVATE_KEY", wal.Secret())
	w.plan.Set(ProfileEnv, "SOLANA_PUBLIC_KEY", wal.PublicKey)
	w.plan.Set(DaemonEnv, "SOLANA_PUBLIC_KEY", wal.PublicKey)
	return nil
}

func orUnknown(s string) string {
	if s == "" {
		return "(public key not recorded)"
	}
	return s
}

func (w *wizard) pubkey() string {
	if v, ok := w.plan.Get(ProfileEnv, "SOLANA_PUBLIC_KEY"); ok {
		return v
	}
	return w.st.Profile["SOLANA_PUBLIC_KEY"]
}

func (w *wizard) rpc() error {
	w.step(4, "Solana RPC")
	has := w.st.SecretSet[ProfileEnv]["SOLANA_RPC_URLS"] || w.st.SecretSet[DaemonEnv]["SOLANA_RPC_URLS"]
	urls := w.f.rpcURLs
	for attempt := 0; ; attempt++ {
		if w.interactive() && w.f.rpcURLs == "" {
			def := defaultRPC
			if has {
				def = "keep current"
			}
			if attempt == 0 {
				w.say("  A private RPC (Helius, QuickNode, ...) is strongly recommended; the public one rate-limits.")
			}
			ans, err := w.ask("RPC URLs (comma-separated)", def)
			if err != nil {
				return err
			}
			urls = ans
			if ans == "keep current" {
				urls = ""
			}
		} else if urls == "" && !has {
			urls = defaultRPC
		}
		if urls != "" && (Variable{Kind: "urls"}).Validate(urls) != nil {
			if !w.interactive() || w.f.rpcURLs != "" || attempt >= 2 {
				return errors.New("RPC URLs must be comma-separated http(s) URLs")
			}
			w.say("  not a valid URL list")
			continue
		}
		if !w.tests {
			break
		}
		r := w.e.TestRPC(w.ctx, urls, w.pubkey())
		if err := r.Write(w.io.Out, false); err != nil {
			return err
		}
		if r.ExitCode() != 1 || !w.interactive() || w.f.rpcURLs != "" {
			break
		}
		use, err := w.askBool("RPC test failed. Use these URLs anyway?", false)
		if err != nil {
			return err
		}
		if use || attempt >= 2 {
			break
		}
	}
	if urls != "" {
		w.plan.Set(ProfileEnv, "SOLANA_RPC_URLS", urls)
		w.plan.Set(DaemonEnv, "SOLANA_RPC_URLS", urls)
	}
	return nil
}

func (w *wizard) route() error {
	w.step(5, "Entry route")
	current := "deterministic"
	switch {
	case w.st.Daemon["AI_HEALTH_CMD"] != "":
		current = "ai"
	case w.st.DaemonExists && w.st.Daemon["DEPLOY_CMD"] == "" && w.st.SecretSet[DaemonEnv]["HERMES_WEBHOOK_URL"]:
		current = "webhook" // existing agent-only install: keep it unless asked
	}
	route := current
	if w.f.route != "" {
		route = w.f.route
	} else if w.interactive() {
		w.say("  deterministic: the daemon ranks each batch and deploys itself, in seconds.")
		w.say("  ai: a Hermes agent picks first; when its model probe fails, that batch goes deterministic.")
		w.say("  webhook: the Hermes agent alone decides; no deterministic fallback.")
		var err error
		if route, err = w.ask("Route: deterministic, ai or webhook", current); err != nil {
			return err
		}
	}
	if route != "deterministic" && route != "ai" && route != "webhook" {
		return fmt.Errorf("unknown route %q (deterministic, ai, webhook)", route)
	}
	deploy, health, probe, err := w.e.AICommands()
	if deploy == "" {
		return err
	}
	if route == "ai" && err != nil {
		if !w.interactive() {
			return errors.New("ai route unavailable: " + err.Error())
		}
		w.say("  ⚠ %s; using the deterministic route", err.Error())
		route = "deterministic"
	}
	if route == "ai" && w.tests {
		w.say("  probing the AI model (read-only, up to 65s)...")
		c := w.e.TestAI(w.ctx, probe)
		if err := (Report{Checks: []Check{c}}).Write(w.io.Out, false); err != nil {
			return err
		}
		if c.Status == Fail {
			keep, err := w.askBool("Keep the AI route anyway (each batch falls back while the probe fails)?", true)
			if err != nil {
				return err
			}
			if !keep {
				route = "deterministic"
			}
		}
	}
	switch route {
	case "deterministic":
		w.plan.Set(DaemonEnv, "DEPLOY_CMD", deploy)
		w.plan.Set(DaemonEnv, "AI_HEALTH_CMD", "")
		return nil
	case "webhook":
		w.plan.Set(DaemonEnv, "DEPLOY_CMD", "")
		w.plan.Set(DaemonEnv, "AI_HEALTH_CMD", "")
	default:
		w.plan.Set(DaemonEnv, "DEPLOY_CMD", deploy)
		w.plan.Set(DaemonEnv, "AI_HEALTH_CMD", health)
	}
	if !w.st.SecretSet[DaemonEnv]["HERMES_WEBHOOK_URL"] {
		w.plan.Set(DaemonEnv, "HERMES_WEBHOOK_URL", w.schemaDefault("HERMES_WEBHOOK_URL"))
	}
	if !w.st.SecretSet[DaemonEnv]["HERMES_WEBHOOK_SECRET"] {
		secret, err := NewWebhookSecret()
		if err != nil {
			return err
		}
		w.plan.Set(DaemonEnv, "HERMES_WEBHOOK_SECRET", secret)
	}
	w.plan.SyncWebhookSecret = true
	return nil
}

func (w *wizard) telegram() error {
	w.step(6, "Telegram reports (optional)")
	on := w.st.Daemon["REPORT_CMD"] != ""
	switch w.f.telegram {
	case "on":
		on = true
	case "off":
		on = false
	case "keep", "":
		if !w.interactive() {
			w.say("  unchanged")
			return nil
		}
		var err error
		if on, err = w.askBool("Send trade reports and alerts to Telegram through Hermes?", on); err != nil {
			return err
		}
	default:
		return fmt.Errorf("unknown --telegram %q (keep, on, off)", w.f.telegram)
	}
	if !on {
		w.plan.Set(DaemonEnv, "REPORT_CMD", "")
		w.plan.Set(ProfileEnv, "DLMM_ALERT_TARGET", "")
		return nil
	}
	if _, err := w.e.opts.LookPath("hermes"); err != nil {
		w.say("  ⚠ hermes is not on PATH; reports fail until Hermes is installed with Telegram configured")
	}
	w.plan.Set(DaemonEnv, "REPORT_CMD", ReportCommand)
	w.plan.Set(ProfileEnv, "DLMM_ALERT_TARGET", "telegram")
	if w.tests && !w.f.dryRun {
		c := w.e.TestTelegram(w.ctx)
		return (Report{Checks: []Check{c}}).Write(w.io.Out, false)
	}
	return nil
}

func (w *wizard) risk() error {
	w.step(7, "Sizing and risk")
	w.say("  Solana ticket size is fixed in the pipeline: 45%% of the wallet above its SOL reserve,")
	w.say("  0.3 SOL floor, 5 SOL cap; the hard stop-loss lives in the monitor. Neither is set here.")
	w.say("  DRY_RUN (step 2) is the main safety switch. The entry gates below keep safe values by default.")
	accept, err := w.askBool("Keep the current/default entry-gate values?", true)
	if err != nil {
		return err
	}
	for _, key := range riskKeys {
		val := w.st.Daemon[key]
		if val == "" {
			val = w.schemaDefault(key)
		}
		if !accept {
			if val, err = w.askVar(DaemonEnv, key, val); err != nil {
				return err
			}
		}
		w.plan.Set(DaemonEnv, key, val)
	}
	for _, kv := range w.f.sets {
		key, val, ok := strings.Cut(kv, "=")
		v, known := lookupVariable(DaemonEnv, key)
		switch {
		case !ok || !known:
			return fmt.Errorf("--set %s: not a daemon setting", key)
		case v.Secret || key == "DRY_RUN":
			return fmt.Errorf("--set %s: use the dedicated flag for this setting", key)
		case v.Validate(val) != nil:
			return fmt.Errorf("--set %s: invalid %s", key, v.Kind)
		}
		w.plan.Set(DaemonEnv, key, val)
	}
	gmgn, _ := w.plan.Get(DaemonEnv, "ENABLE_GMGN_GATE")
	if gmgn != "true" || (w.st.SecretSet[DaemonEnv]["GMGN_API_KEY"] && w.f.gmgnKeyFile == "") {
		return nil
	}
	var key []byte
	switch {
	case w.f.gmgnKeyFile != "":
		key, err = w.secretFromFile(w.f.gmgnKeyFile)
	case w.interactive():
		w.say("  The GMGN gate (rat/bundler holders) needs an API key; without one it fails open.")
		key, err = w.readSecret("GMGN API key (input hidden, Enter to skip): ")
	default:
		return nil
	}
	if err != nil {
		return err
	}
	if len(key) > 0 {
		w.plan.Set(DaemonEnv, "GMGN_API_KEY", string(key))
		clear(key)
	}
	return nil
}

func (w *wizard) install() error {
	w.step(8, "Services")
	req := w.f.inst
	run, linger := w.f.install, w.f.linger
	if w.interactive() {
		var err error
		if run, err = w.askBool("Install or refresh the systemd user services now (runs install.sh)?", true); err != nil {
			return err
		}
		if run {
			for _, o := range []struct {
				p  string
				to *bool
			}{{"Local dashboard on 127.0.0.1:8787?", &req.WithDashboard}, {"Loss alerts timer?", &req.WithAlerts},
				{"Ops timers (marker archive, journal retention)?", &req.WithOps}, {"Research timers (read-only)?", &req.WithResearch}} {
				if *o.to, err = w.askBool(o.p, *o.to); err != nil {
					return err
				}
			}
			if req.WithRentReclaimSignsTx, err = w.askBool("Rent reclaim timer? It SIGNS AND SENDS transactions every 30m", false); err != nil {
				return err
			}
			if req.WithRentReclaimSignsTx {
				ans, err := w.ask("Type SIGNS TX to confirm", "")
				if err != nil {
					return err
				}
				req.WithRentReclaimSignsTx = ans == "SIGNS TX"
			}
			if linger, err = w.askBool("Enable linger so services survive logout and reboot?", true); err != nil {
				return err
			}
		}
	} else if !run && (req != InstallRequest{}) {
		return errors.New("--with-* and --no-build need --install")
	}
	if run {
		w.plan.Install = &req
	}
	w.plan.Linger = linger
	if !req.WithDashboard {
		return nil
	}
	if _, err := os.Stat(w.e.dashboardAuthPath()); err == nil && w.f.dashboardPasswordFile == "" {
		w.say("  dashboard password already set (%s); keeping it", w.e.dashboardAuthPath())
		return nil
	}
	var pw []byte
	var err error
	switch {
	case w.f.dashboardPasswordFile != "":
		pw, err = w.secretFromFile(w.f.dashboardPasswordFile)
	case w.interactive():
		if pw, err = w.readSecret("Dashboard password (12+ chars, input hidden): "); err == nil {
			var again []byte
			if again, err = w.readSecret("Repeat password: "); err == nil && string(again) != string(pw) {
				err = errors.New("passwords do not match")
			}
			clear(again)
		}
	default:
		w.say("  ⚠ no --dashboard-password-file: the dashboard serves no data until a password hash is set")
		return nil
	}
	if err != nil {
		return err
	}
	hash, err := HashDashboardPassword(string(pw))
	clear(pw)
	if err != nil {
		return err
	}
	w.plan.DashboardHash = hash
	return nil
}

func (w *wizard) finish() error {
	w.say("\nPlanned changes (secrets masked):")
	if err := w.e.WritePlanDescription(w.io.Out, w.plan); err != nil {
		return err
	}
	if w.f.dryRun {
		w.say("\n--dry-run: nothing was written.")
		return nil
	}
	ok, err := w.askBool("Apply these changes?", true)
	if err != nil {
		return err
	}
	if !ok {
		w.say("Nothing written.")
		return nil
	}
	if err := w.e.Apply(w.ctx, w.plan); err != nil {
		return err
	}
	w.step(9, "Final doctor")
	if w.f.skipDoctor {
		w.say("  skipped; run ./azimuth doctor")
		return nil
	}
	ctx, cancel := context.WithTimeout(w.ctx, 3*time.Minute)
	defer cancel()
	r := w.e.Doctor(ctx)
	if err := r.Write(w.io.Out, false); err != nil {
		return err
	}
	w.exitCode = r.ExitCode()
	if w.exitCode == 0 {
		w.say("\nAll checks pass.")
	} else {
		w.say("\nFix the WARN/FAIL rows above, then re-run ./azimuth doctor (setup is safe to re-run).")
	}
	return nil
}
