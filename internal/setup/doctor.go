package setup

import (
	"context"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"runtime"
	"slices"
	"strconv"
	"strings"
	"text/tabwriter"
	"time"
)

type Status string

const (
	Pass Status = "PASS"
	Warn Status = "WARN"
	Fail Status = "FAIL"
)

type Check struct {
	Name   string `json:"name"`
	Status Status `json:"status"`
	Detail string `json:"detail"`
	Hint   string `json:"hint"`
}

type Report struct {
	Checks []Check `json:"checks"`
}

func (r Report) ExitCode() int {
	code := 0
	for _, c := range r.Checks {
		if c.Status == Fail {
			return 1
		}
		if c.Status == Warn {
			code = 2
		}
	}
	return code
}

func (r Report) Write(w io.Writer, asJSON bool) error {
	if asJSON {
		e := json.NewEncoder(w)
		e.SetIndent("", "  ")
		return e.Encode(r)
	}
	t := tabwriter.NewWriter(w, 0, 4, 2, ' ', 0)
	if _, err := fmt.Fprintln(t, "STATUS\tCHECK\tDETAIL\tFIX"); err != nil {
		return err
	}
	for _, c := range r.Checks {
		if _, err := fmt.Fprintf(t, "%s\t%s\t%s\t%s\n", c.Status, c.Name, c.Detail, c.Hint); err != nil {
			return err
		}
	}
	return t.Flush()
}

type CommandResult struct {
	Code   int
	Output string
}
type CommandRunner func(context.Context, string, []string, []string) (CommandResult, error)

// DoctorOptions names local inputs explicitly. Doctor never reads profile secrets.
// Run and LookPath allow callers to test against fixtures without host commands.
type DoctorOptions struct {
	RepoDir      string
	EnvFile      string
	ProfileDir   string
	HermesRoot   string
	HermesPython string
	HomeDir      string
	Timeout      time.Duration
	Run          CommandRunner
	LookPath     func(string) (string, error)
	HTTPClient   HTTPDoer
	BinaryPaths  []string
}

type doctor struct {
	opts   DoctorOptions
	report Report
	values map[string]string
}

// Doctor performs diagnostics only: no deployment commands, key files or service changes.
// AI_HEALTH_CMD is the sole configured command executed; like the daemon it is
// whitespace-split, never passed through a shell. It must be a read-only probe.
func Doctor(ctx context.Context, opts DoctorOptions) Report {
	if opts.RepoDir == "" {
		opts.RepoDir = "."
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
	if opts.Timeout <= 0 {
		opts.Timeout = 5 * time.Second
	}
	if opts.Run == nil {
		opts.Run = runCommand
	}
	if opts.LookPath == nil {
		opts.LookPath = exec.LookPath
	}
	d := doctor{opts: opts, values: map[string]string{}}
	d.host()
	d.config()
	d.tools(ctx)
	d.redis(ctx)
	d.rpc(ctx)
	d.ai(ctx)
	d.services(ctx)
	d.skill()
	d.resources()
	d.binaries()
	return d.report
}

func (d *doctor) add(name string, status Status, detail, hint string) {
	d.report.Checks = append(d.report.Checks, Check{name, status, detail, hint})
}

func (d *doctor) host() {
	s := Pass
	hint := ""
	if runtime.GOOS != "linux" {
		s = Warn
		hint = "Use Linux for the systemd user services; foreground execution is available."
	}
	d.add("host", s, runtime.GOOS+"/"+runtime.GOARCH, hint)
}

func (d *doctor) config() {
	info, err := os.Lstat(d.opts.EnvFile)
	if err != nil {
		d.add("env.file", Fail, "Configuration file is missing or unreadable.", "Create the selected .env from .env.example and set its permissions to 0600.")
		return
	}
	if !info.Mode().IsRegular() {
		d.add("env.file", Fail, "Configuration must be a regular file, not a symlink.", "Select a regular .env file.")
		return
	}
	if info.Mode().Perm() != 0600 {
		d.add("env.permissions", Fail, "Configuration permissions must be 0600.", "Run chmod 600 on the selected .env.")
	} else {
		d.add("env.permissions", Pass, "Configuration permissions are 0600.", "")
	}
	f, err := os.Open(d.opts.EnvFile)
	if err != nil {
		d.add("env.file", Fail, "Cannot open configuration.", "Check file ownership and read permission.")
		return
	}
	defer f.Close()
	values, err := ParseEnv(io.LimitReader(f, 1024*1024+1))
	if err != nil || info.Size() > 1024*1024 {
		d.add("env.syntax", Fail, "Cannot parse literal dotenv assignments.", "Use NAME=value or quoted literal values; shell expansion is not supported.")
		return
	}
	d.values = values
	modes := ActiveModes(values)
	issues := ValidateConfig(values, modes)
	for _, issue := range issues {
		d.add("env."+issue.Name, Fail, issue.Message, issue.Hint)
	}
	if len(issues) == 0 {
		d.add("env.schema", Pass, "Present settings and routing requirements match the schema.", "")
	}
	if values["DRY_RUN"] != "true" {
		d.add("env.dry_run", Warn, "Dry-run safety is not enabled explicitly.", "Set DRY_RUN=true until ready for live operation.")
	} else {
		d.add("env.dry_run", Pass, "Selected config requests dry runs; profile executor settings are not inspected.", "")
	}
}

func (d *doctor) command(ctx context.Context, timeout time.Duration, name string, args ...string) (CommandResult, error) {
	ctx, cancel := context.WithTimeout(ctx, timeout)
	defer cancel()
	return d.opts.Run(ctx, name, args, []string{"PYTHONDONTWRITEBYTECODE=1"})
}

var versionPattern = regexp.MustCompile(`(?:^|[^0-9])([0-9]+)\.([0-9]+)(?:\.[0-9]+)?`)

var bundledPythonVersionPattern = regexp.MustCompile(`^python-([0-9]+)\.([0-9]+)\.([0-9]+)(?:\+([0-9]+))?-`)

func newestBundledPython(base string) string {
	paths, _ := filepath.Glob(filepath.Join(base, "tools", "python-*", "bin", "python3"))
	var newest [4]uint64
	var selected string
	for _, path := range paths {
		name := filepath.Base(filepath.Dir(filepath.Dir(path)))
		match := bundledPythonVersionPattern.FindStringSubmatch(name)
		if match == nil {
			continue
		}
		var version [4]uint64
		valid := true
		for i := range version {
			if match[i+1] == "" {
				continue
			}
			n, err := strconv.ParseUint(match[i+1], 10, 64)
			if err != nil {
				valid = false
				break
			}
			version[i] = n
		}
		if !valid {
			continue
		}
		if info, err := os.Stat(path); err != nil || info.IsDir() {
			continue
		}
		if selected == "" || slices.Compare(version[:], newest[:]) > 0 {
			selected, newest = path, version
		}
	}
	return selected
}

func (d *doctor) tools(ctx context.Context) {
	for _, name := range []string{"npm", "redis-cli", "git"} {
		if _, err := d.opts.LookPath(name); err != nil {
			d.add("tool."+name, Warn, "Optional tool is not installed.", "Install "+name+" if its installation or operator features are needed.")
		} else {
			d.add("tool."+name, Pass, "Optional tool is installed.", "")
		}
	}
	for _, tool := range []struct {
		name         string
		args         []string
		major, minor int
		required     bool
	}{
		{"go", []string{"version"}, 1, 22, false}, {"python3", []string{"--version"}, 3, 10, true}, {"node", []string{"--version"}, 18, 0, true},
	} {
		status := Warn
		if tool.required {
			status = Fail
		}
		path, err := d.opts.LookPath(tool.name)
		if err != nil {
			d.add("tool."+tool.name, status, "Tool is not installed.", "Install "+tool.name+" and add it to PATH.")
			continue
		}
		res, err := d.command(ctx, d.opts.Timeout, path, tool.args...)
		m := versionPattern.FindStringSubmatch(res.Output)
		if err != nil || res.Code != 0 || len(m) < 3 {
			d.add("tool."+tool.name, status, "Cannot determine the installed version.", "Install a host-compatible "+tool.name+" binary.")
			continue
		}
		major, _ := strconv.Atoi(m[1])
		minor, _ := strconv.Atoi(m[2])
		if major < tool.major || (major == tool.major && minor < tool.minor) {
			d.add("tool."+tool.name, status, "Installed version is below the supported minimum.", fmt.Sprintf("Install %s %d.%d or newer.", tool.name, tool.major, tool.minor))
			continue
		}
		d.add("tool."+tool.name, Pass, fmt.Sprintf("Version %d.%d meets the minimum.", major, minor), "")
	}
	hermes, err := d.opts.LookPath("hermes")
	if err != nil {
		d.add("tool.hermes", Warn, "Hermes is not installed.", "Install Hermes for the AI route and messaging integrations.")
	} else {
		d.add("tool.hermes", Pass, "Hermes executable is installed.", "")
	}
	python := d.opts.HermesPython
	legacy := false
	root := d.opts.HermesRoot
	if root == "" && hermes != "" {
		if real, e := filepath.EvalSymlinks(hermes); e == nil {
			root = filepath.Dir(filepath.Dir(real))
		}
	}
	if python == "" {
		base := os.Getenv("HERMES_HOME_BASE")
		if base == "" {
			base = filepath.Join(d.opts.HomeDir, ".hermes")
		}
		python = newestBundledPython(base)
	}
	if python == "" && root != "" {
		for _, venv := range []string{"venv", ".venv"} {
			p := filepath.Join(root, venv, "bin", "python")
			if info, e := os.Stat(p); e == nil && info.Mode().IsRegular() {
				python = p
				legacy = true
				break
			}
		}
	}
	if python == "" {
		d.add("hermes.runtime", Warn, "Bundled Python runtime was not located.", "Install Hermes' bundled runtime under HERMES_HOME_BASE/tools or pass --hermes-python.")
		return
	}
	d.opts.HermesPython = python
	code := "import hermes_bootstrap; from hermes_cli.config import load_config; from hermes_cli.runtime_provider import resolve_runtime_provider"
	args := []string{"-I", "-c", code}
	if legacy {
		code = "import sys; sys.path.insert(0, sys.argv[1]); import dotenv; from hermes_cli.config import load_config; from hermes_cli.runtime_provider import resolve_runtime_provider"
		args = []string{"-c", code, root}
	}
	res, err := d.command(ctx, d.opts.Timeout, python, args...)
	if err != nil || res.Code != 0 {
		d.add("hermes.runtime", Fail, "Selected Hermes runtime cannot import the AI provider dependencies.", "Repair Hermes' bundled runtime and point AI_HEALTH_CMD at that interpreter.")
	} else if legacy {
		d.add("hermes.runtime", Warn, "legacy venv; AI_HEALTH_CMD should use the bundled runtime", "Install Hermes' bundled runtime under HERMES_HOME_BASE/tools or pass --hermes-python.")
	} else {
		d.add("hermes.runtime", Pass, "Selected runtime imports hermes_bootstrap and the Hermes provider resolver.", "")
	}
}

func (d *doctor) ai(ctx context.Context) {
	args := strings.Fields(d.values["AI_HEALTH_CMD"])
	if len(args) == 0 {
		d.add("ai.probe", Pass, "AI route is not configured.", "")
		return
	}
	res, err := d.command(ctx, 65*time.Second, args[0], args[1:]...)
	if res.Code == 14 {
		d.add("ai.probe", Fail, "AI probe returned config_error (exit 14); runtime dependencies or configuration are missing.", "Run the probe with Hermes' bundled interpreter and repair its configuration; fallback would hide this error.")
		return
	}
	if err != nil || res.Code != 0 {
		d.add("ai.probe", Fail, "AI health command could not complete successfully.", "Check the probe interpreter, provider availability and timeout locally.")
		return
	}
	d.add("ai.probe", Pass, "Read-only AI health command succeeded.", "")
}

// Only bounded output is retained, and callers never echo command errors.
type boundedOutput struct{ data []byte }

func (b *boundedOutput) Write(p []byte) (int, error) {
	n := len(p)
	if left := 4096 - len(b.data); left > 0 {
		if len(p) > left {
			p = p[:left]
		}
		b.data = append(b.data, p...)
	}
	return n, nil
}

func runCommand(ctx context.Context, name string, args, extraEnv []string) (CommandResult, error) {
	cmd := exec.CommandContext(ctx, name, args...)
	cmd.Env = append(os.Environ(), extraEnv...)
	cmd.WaitDelay = time.Second
	var out boundedOutput
	cmd.Stdout = &out
	cmd.Stderr = &out
	err := cmd.Run()
	code := 0
	if err != nil {
		code = -1
		if e, ok := err.(*exec.ExitError); ok {
			code = e.ExitCode()
		}
	}
	return CommandResult{code, string(out.data)}, err
}
