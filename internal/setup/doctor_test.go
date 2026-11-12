package setup

import (
	"bytes"
	"context"
	"crypto/ed25519"
	"crypto/rand"
	"encoding/binary"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"math/big"
	"net/http"
	"net/http/httptest"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
	"testing"
	"time"
)

func fakePubkey() string {
	pub, _, err := ed25519.GenerateKey(rand.Reader)
	if err != nil {
		panic(err)
	}
	n := new(big.Int).SetBytes(pub)
	radix := big.NewInt(58)
	var result []byte
	for n.Sign() > 0 {
		remainder := new(big.Int)
		n.QuoRem(n, radix, remainder)
		result = append(result, "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"[remainder.Int64()])
	}
	for _, b := range pub {
		if b != 0 {
			break
		}
		result = append(result, '1')
	}
	for i, j := 0, len(result)-1; i < j; i, j = i+1, j-1 {
		result[i], result[j] = result[j], result[i]
	}
	return string(result)
}

func fixture(t *testing.T) DoctorOptions {
	t.Helper()
	root := t.TempDir()
	profile := filepath.Join(root, "profile")
	for _, dir := range []string{"assets/skill/scripts", "profile/skills/solana-dlmm", ".local/bin"} {
		if err := os.MkdirAll(filepath.Join(root, dir), 0700); err != nil {
			t.Fatal(err)
		}
	}
	if err := os.Symlink(filepath.Join(root, "assets", "skill", "scripts"), filepath.Join(profile, "skills", "solana-dlmm", "scripts")); err != nil {
		t.Fatal(err)
	}
	write := func(path, content string) {
		t.Helper()
		if err := os.WriteFile(path, []byte(content), 0600); err != nil {
			t.Fatal(err)
		}
	}
	write(filepath.Join(root, ".env"), "HERMES_WEBHOOK_URL=http://example.invalid/webhook\nHERMES_WEBHOOK_SECRET=test-only-placeholder\nDRY_RUN=true\n")
	script := filepath.Join(root, "interpreter")
	write(script, "#!/bin/sh\nexit 0\n")
	write(filepath.Join(root, "azimuth"), "#!/bin/sh\nexit 0\n")
	write(filepath.Join(root, ".local", "bin", "azimuth-dashboard"), "#!/bin/sh\nexit 0\n")
	opts := DoctorOptions{RepoDir: root, EnvFile: filepath.Join(root, ".env"), HomeDir: root, ProfileDir: profile, HermesRoot: root, HermesPython: script, Timeout: time.Second}
	opts.LookPath = func(string) (string, error) { return script, nil }
	opts.Run = func(_ context.Context, name string, args, env []string, dir string) (CommandResult, error) {
		if name == "systemctl" {
			return CommandResult{Output: "LoadState=loaded\nActiveState=active\nUnitFileState=enabled"}, nil
		}
		if name == "loginctl" {
			return CommandResult{Output: "yes"}, nil
		}
		if len(args) > 0 && args[0] == "version" {
			return CommandResult{Output: "go version go1.22.0"}, nil
		}
		if len(args) > 0 && args[0] == "--version" {
			return CommandResult{Output: "version 30.0.0"}, nil
		}
		if len(args) > 0 && (args[0] == "-c" || args[0] == "-I") {
			return CommandResult{}, nil
		}
		return CommandResult{}, fmt.Errorf("unexpected command")
	}
	return opts
}

func findCheck(t *testing.T, r Report, name string) Check {
	t.Helper()
	for _, c := range r.Checks {
		if c.Name == name {
			return c
		}
	}
	t.Fatalf("missing check %s", name)
	return Check{}
}

func TestReportExitCodesAndOutput(t *testing.T) {
	for _, tt := range []struct {
		statuses []Status
		code     int
	}{{[]Status{Pass}, 0}, {[]Status{Pass, Warn}, 2}, {[]Status{Warn, Fail}, 1}, {[]Status{Fail, Warn}, 1}} {
		r := Report{}
		for _, s := range tt.statuses {
			r.Checks = append(r.Checks, Check{"example", s, "detail", "fix"})
		}
		if r.ExitCode() != tt.code {
			t.Fatal("incorrect severity precedence")
		}
		for _, asJSON := range []bool{false, true} {
			var out bytes.Buffer
			if err := r.Write(&out, asJSON); err != nil {
				t.Fatal(err)
			}
			if asJSON {
				var decoded Report
				if json.Unmarshal(out.Bytes(), &decoded) != nil || len(decoded.Checks) != len(tt.statuses) {
					t.Fatal("invalid JSON")
				}
			} else if !strings.Contains(out.String(), "STATUS") || !strings.Contains(out.String(), "fix") {
				t.Fatal("missing table fields")
			}
		}
	}
}

func TestDoctorFixtureAndSecretRedaction(t *testing.T) {
	opts := fixture(t)
	secret := "test-value-never-print-this"
	f, err := os.OpenFile(opts.EnvFile, os.O_APPEND|os.O_WRONLY, 0600)
	if err != nil {
		t.Fatal(err)
	}
	fmt.Fprintf(f, "GMGN_API_KEY=%s\nREDISCLI_AUTH=%s\nAI_HEALTH_CMD=probe %s\n", secret, secret, secret)
	f.Close()
	run := opts.Run
	opts.Run = func(ctx context.Context, name string, args, env []string, dir string) (CommandResult, error) {
		if name == "probe" {
			return CommandResult{Code: 14, Output: secret}, errors.New(secret)
		}
		return run(ctx, name, args, env, dir)
	}
	r := Doctor(context.Background(), opts)
	if c := findCheck(t, r, "ai.probe"); c.Status != Fail || !strings.Contains(c.Detail, "config_error") {
		t.Fatal("AI exit 14 must identify configuration failure")
	}
	for _, asJSON := range []bool{false, true} {
		var out bytes.Buffer
		r.Write(&out, asJSON)
		if strings.Contains(out.String(), secret) || strings.Contains(out.String(), opts.RepoDir) {
			t.Fatal("report disclosed configured values or local paths")
		}
	}
	if findCheck(t, r, "env.permissions").Status != Pass || findCheck(t, r, "profile.skill").Status != Pass {
		t.Fatal("fixture checks failed")
	}
}

func TestDoctorEnvFailures(t *testing.T) {
	for _, tt := range []struct {
		name, content string
		mode          os.FileMode
		check         string
	}{
		{"permissions", "DRY_RUN=true\n", 0644, "env.permissions"},
		{"required", "DRY_RUN=true\n", 0600, "env.HERMES_WEBHOOK_SECRET"},
		{"invalid", "POLL_INTERVAL=not-a-duration\n", 0600, "env.POLL_INTERVAL"},
		{"syntax", "not-an-assignment", 0600, "env.syntax"},
	} {
		t.Run(tt.name, func(t *testing.T) {
			opts := fixture(t)
			if err := os.WriteFile(opts.EnvFile, []byte(tt.content), 0600); err != nil {
				t.Fatal(err)
			}
			if err := os.Chmod(opts.EnvFile, tt.mode); err != nil {
				t.Fatal(err)
			}
			r := Doctor(context.Background(), opts)
			if findCheck(t, r, tt.check).Status != Fail {
				t.Fatal("invalid config passed")
			}
		})
	}
	opts := fixture(t)
	os.Remove(opts.EnvFile)
	if findCheck(t, Doctor(context.Background(), opts), "env.file").Status != Fail {
		t.Fatal("missing env passed")
	}
	target := filepath.Join(opts.RepoDir, "not-an-env")
	os.WriteFile(target, []byte("not read"), 0600)
	os.Symlink(target, opts.EnvFile)
	if findCheck(t, Doctor(context.Background(), opts), "env.file").Status != Fail {
		t.Fatal("symlink env passed")
	}
}

func TestDoctorDoesNotExecuteDeployOrReport(t *testing.T) {
	opts := fixture(t)
	file, err := os.OpenFile(opts.EnvFile, os.O_APPEND|os.O_WRONLY, 0600)
	if err != nil {
		t.Fatal(err)
	}
	fmt.Fprintln(file, "DEPLOY_CMD=must-not-run-deploy\nREPORT_CMD=must-not-run-report")
	file.Close()
	run := opts.Run
	opts.Run = func(ctx context.Context, name string, args, env []string, dir string) (CommandResult, error) {
		if strings.HasPrefix(name, "must-not-run") {
			t.Fatal("doctor executed an action command")
		}
		return run(ctx, name, args, env, dir)
	}
	Doctor(context.Background(), opts)
}

func TestDoctorToolVersionAndCommandDeadline(t *testing.T) {
	opts := fixture(t)
	run := opts.Run
	opts.Run = func(ctx context.Context, name string, args, env []string, dir string) (CommandResult, error) {
		if _, ok := ctx.Deadline(); !ok {
			t.Fatal("command has no deadline")
		}
		if len(args) > 0 && args[0] == "--version" {
			return CommandResult{Output: "version 1.0.0"}, nil
		}
		return run(ctx, name, args, env, dir)
	}
	r := Doctor(context.Background(), opts)
	if findCheck(t, r, "tool.python3").Status != Fail || findCheck(t, r, "tool.node").Status != Fail {
		t.Fatal("unsupported version passed")
	}
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	opts.Run = func(ctx context.Context, _ string, _ []string, _ []string, _ string) (CommandResult, error) {
		<-ctx.Done()
		return CommandResult{Code: -1}, ctx.Err()
	}
	d := doctor{opts: opts, values: map[string]string{"AI_HEALTH_CMD": "read-only-test-probe"}}
	d.ai(ctx)
	if findCheck(t, d.report, "ai.probe").Status != Fail {
		t.Fatal("canceled probe passed")
	}
}

func TestHermesRuntimeSelection(t *testing.T) {
	const imports = "import sys; sys.path.insert(0, sys.argv[1]); import hermes_bootstrap; from hermes_cli.config import load_config; from hermes_cli.runtime_provider import resolve_runtime_provider"
	for _, tt := range []struct {
		name       string
		versions   []string
		venv       string
		want       string
		explicit   bool
		customBase bool
		broken     bool
		status     Status
	}{
		{name: "bundled preferred over venv", versions: []string{"3.12.4"}, venv: "venv", want: "3.12.4", status: Pass},
		{name: "newest numeric version", versions: []string{"3.9.20", "3.10.18", "3.12.9", "3.12.10"}, want: "3.12.10", status: Pass},
		{name: "venv only warns", venv: "venv", status: Warn},
		{name: "dot venv only warns", venv: ".venv", status: Warn},
		{name: "home base override", versions: []string{"3.13.2"}, want: "3.13.2", customBase: true, status: Pass},
		{name: "broken bundle does not fall back", versions: []string{"3.12.4"}, venv: "venv", want: "3.12.4", broken: true, status: Fail},
		{name: "explicit interpreter wins", versions: []string{"3.12.4"}, explicit: true, status: Pass},
	} {
		t.Run(tt.name, func(t *testing.T) {
			opts := fixture(t)
			base := filepath.Join(opts.HomeDir, ".hermes")
			t.Setenv("HERMES_HOME_BASE", "")
			if tt.customBase {
				base = t.TempDir()
				t.Setenv("HERMES_HOME_BASE", base)
			}
			writePython := func(path string) {
				t.Helper()
				if err := os.MkdirAll(filepath.Dir(path), 0700); err != nil {
					t.Fatal(err)
				}
				if err := os.WriteFile(path, []byte("#!/bin/sh\nexit 0\n"), 0700); err != nil {
					t.Fatal(err)
				}
			}
			want := opts.HermesPython
			if !tt.explicit {
				opts.HermesPython = ""
			}
			for _, version := range tt.versions {
				path := filepath.Join(base, "tools", "python-"+version+"-"+runtime.GOOS+"-"+runtime.GOARCH, "bin", "python3")
				writePython(path)
				if version == tt.want && !tt.explicit {
					want = path
				}
			}
			legacy := !tt.explicit && tt.want == ""
			if tt.venv != "" {
				path := filepath.Join(opts.HermesRoot, tt.venv, "bin", "python")
				writePython(path)
				if legacy {
					want = path
				}
			}
			run := opts.Run
			var probed []string
			opts.Run = func(ctx context.Context, name string, args, env []string, dir string) (CommandResult, error) {
				if len(args) > 0 && (args[0] == "-I" || args[0] == "-c") {
					probed = append(probed, name)
					if legacy {
						if len(args) != 3 || args[0] != "-c" || args[2] != opts.HermesRoot {
							t.Error("legacy probe lost its source checkout")
						}
					} else if len(args) != 4 || args[0] != "-I" || args[1] != "-c" || args[2] != imports || args[3] != opts.HermesRoot {
						t.Error("bundled probe must use isolated mode and hermes_bootstrap")
					}
					if dir != opts.HermesRoot {
						t.Error("runtime probe must run from the source checkout")
					}
					if tt.broken {
						return CommandResult{Code: 1}, errors.New("fixture import failure")
					}
					return CommandResult{}, nil
				}
				return run(ctx, name, args, env, dir)
			}
			d := doctor{opts: opts}
			d.tools(context.Background())
			if len(probed) != 1 || probed[0] != want {
				t.Fatalf("expected exactly the selected runtime to be probed; got %d probes", len(probed))
			}
			if d.opts.HermesPython != want {
				t.Error("architecture check did not receive the selected runtime")
			}
			check := findCheck(t, d.report, "hermes.runtime")
			if check.Status != tt.status {
				t.Errorf("expected %s, got %s", tt.status, check.Status)
			}
			if legacy && !strings.Contains(check.Detail, "legacy venv; AI_HEALTH_CMD should use the bundled runtime") {
				t.Error("legacy venv warning missing")
			}
		})
	}
}

func TestHermesBundledRuntimeBuildsAndSymlinks(t *testing.T) {
	for _, tt := range []struct {
		name string
		dirs []string
		want string
	}{
		{
			name: "real bundled layout",
			dirs: []string{"python-3.14.7+20260901-linux-arm64", "python-3.14.9+20261021-linux-arm64"},
			want: "python-3.14.9+20261021-linux-arm64",
		},
		{
			name: "numeric build breaks version tie",
			dirs: []string{"python-3.14.9-linux-arm64", "python-3.14.9+9-linux-arm64", "python-3.14.9+10-linux-arm64"},
			want: "python-3.14.9+10-linux-arm64",
		},
		{
			name: "version precedes build",
			dirs: []string{"python-3.14.7+20261022-linux-arm64", "python-3.14.9+20261021-linux-arm64"},
			want: "python-3.14.9+20261021-linux-arm64",
		},
	} {
		t.Run(tt.name, func(t *testing.T) {
			opts := fixture(t)
			opts.HermesPython = ""
			base := filepath.Join(opts.HomeDir, ".hermes")
			t.Setenv("HERMES_HOME_BASE", base)
			for _, dir := range tt.dirs {
				bin := filepath.Join(base, "tools", dir, "bin")
				if err := os.MkdirAll(bin, 0700); err != nil {
					t.Fatal(err)
				}
				if err := os.WriteFile(filepath.Join(bin, "python3.14"), []byte("#!/bin/sh\nexit 0\n"), 0700); err != nil {
					t.Fatal(err)
				}
				if err := os.Symlink("python3.14", filepath.Join(bin, "python3")); err != nil {
					t.Fatal(err)
				}
			}
			want := filepath.Join(base, "tools", tt.want, "bin", "python3")
			if got := newestBundledPython(base); got != want {
				t.Fatal("wrong bundled runtime selected")
			}
			run := opts.Run
			var probed []string
			opts.Run = func(ctx context.Context, name string, args, env []string, dir string) (CommandResult, error) {
				if len(args) > 0 && args[0] == "-I" {
					probed = append(probed, name)
				}
				return run(ctx, name, args, env, dir)
			}
			d := doctor{opts: opts}
			d.tools(context.Background())
			if len(probed) != 1 || probed[0] != want || d.opts.HermesPython != want {
				t.Fatal("selected symlink was not used by the runtime probe")
			}
			if findCheck(t, d.report, "hermes.runtime").Status != Pass {
				t.Fatal("bundled runtime did not pass the import check")
			}
		})
	}
}

func TestHermesRuntimeSourceRootAndWorkingDirectory(t *testing.T) {
	python, err := exec.LookPath("python3")
	if err != nil {
		t.Fatal("Python 3 is required for the fixture import check")
	}
	for _, name := range []string{"default root with regular launcher", "home base override", "explicit root", "launcher symlink fallback", "relative interpreter"} {
		t.Run(name, func(t *testing.T) {
			opts := fixture(t)
			opts.HermesPython = python
			if name == "relative interpreter" {
				cwd, err := os.Getwd()
				if err != nil {
					t.Fatal(err)
				}
				opts.HermesPython, err = filepath.Rel(cwd, python)
				if err != nil {
					t.Fatal(err)
				}
			}
			opts.HermesRoot = ""
			base := filepath.Join(opts.HomeDir, ".hermes")
			t.Setenv("HERMES_HOME_BASE", "")
			if name == "home base override" {
				base = t.TempDir()
				t.Setenv("HERMES_HOME_BASE", base)
			}
			root := filepath.Join(base, "hermes-agent")
			if name == "explicit root" {
				if err := os.MkdirAll(root, 0700); err != nil {
					t.Fatal(err)
				}
				root = filepath.Join(opts.HomeDir, "explicit-source")
				opts.HermesRoot = root
			} else if name == "launcher symlink fallback" {
				root = filepath.Join(opts.HomeDir, "fallback-source")
			}
			if err := os.MkdirAll(filepath.Join(root, "hermes_cli"), 0700); err != nil {
				t.Fatal(err)
			}
			for file, code := range map[string]string{
				"hermes_bootstrap.py":            "import os\nfrom pathlib import Path\nassert os.getcwd() == str(Path(__file__).parent)\n",
				"hermes_cli/__init__.py":         "",
				"hermes_cli/config.py":           "def load_config(): pass\n",
				"hermes_cli/runtime_provider.py": "def resolve_runtime_provider(): pass\n",
				"hermes_cli/main.py":             "",
			} {
				if err := os.WriteFile(filepath.Join(root, file), []byte(code), 0600); err != nil {
					t.Fatal(err)
				}
			}
			launcher := filepath.Join(opts.HomeDir, ".local", "bin", "hermes")
			if name == "launcher symlink fallback" {
				if err := os.Symlink(filepath.Join(root, "hermes_cli", "main.py"), launcher); err != nil {
					t.Fatal(err)
				}
			} else if err := os.WriteFile(launcher, []byte("#!/bin/sh\nexit 0\n"), 0700); err != nil {
				t.Fatal(err)
			}
			lookup := opts.LookPath
			opts.LookPath = func(tool string) (string, error) {
				if tool == "hermes" {
					return launcher, nil
				}
				return lookup(tool)
			}
			run := opts.Run
			probes := 0
			opts.Run = func(ctx context.Context, command string, args, env []string, dir string) (CommandResult, error) {
				if len(args) > 0 && args[0] == "-I" {
					probes++
					if len(args) != 4 || args[1] != "-c" || args[3] != root || dir != root {
						t.Fatal("runtime probe must receive the source root as argv and cwd")
					}
					return runCommand(ctx, command, args, env, dir)
				}
				return run(ctx, command, args, env, dir)
			}
			d := doctor{opts: opts}
			d.tools(context.Background())
			if probes != 1 || findCheck(t, d.report, "hermes.runtime").Status != Pass {
				t.Fatal("fixture Hermes modules could not be imported from the selected source root")
			}
		})
	}
}

func TestDoctorRPCReadOnlyAndRedacted(t *testing.T) {
	pubkey := fakePubkey()
	var methods []string
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			t.Error("unexpected HTTP method")
		}
		var body struct {
			Method string            `json:"method"`
			Params []json.RawMessage `json:"params"`
		}
		json.NewDecoder(r.Body).Decode(&body)
		methods = append(methods, body.Method)
		switch body.Method {
		case "getHealth":
			io.WriteString(w, `{"jsonrpc":"2.0","id":1,"result":"ok"}`)
		case "getBalance":
			var got string
			json.Unmarshal(body.Params[0], &got)
			if got != pubkey {
				t.Error("balance did not use public key")
			}
			io.WriteString(w, `{"jsonrpc":"2.0","id":1,"result":{"value":123456789}}`)
		default:
			t.Error("non-read-only RPC method")
			w.WriteHeader(400)
		}
	}))
	defer server.Close()
	d := doctor{opts: DoctorOptions{Timeout: time.Second}, values: map[string]string{"SOLANA_RPC_URLS": server.URL + "/credential-token", "SOLANA_PUBLIC_KEY": pubkey}}
	d.rpc(context.Background())
	if findCheck(t, d.report, "rpc.1").Status != Pass || findCheck(t, d.report, "wallet.balance").Status != Pass {
		t.Fatal("read-only RPC failed")
	}
	if strings.Join(methods, ",") != "getHealth,getBalance" {
		t.Fatal("unexpected RPC requests")
	}
	var out bytes.Buffer
	d.report.Write(&out, true)
	for _, private := range []string{server.URL, "credential-token", pubkey, "123456789"} {
		if strings.Contains(out.String(), private) {
			t.Fatal("RPC report disclosed configured data")
		}
	}
}

func TestDoctorRPCFailureAndRedirect(t *testing.T) {
	for _, body := range []string{`{"jsonrpc":"2.0","id":1,"error":{"message":"credential-token"}}`, `{"id":1,"result":null}`, `{"id":2,"result":"ok"}`, `{"id":1,"result":"behind"}`, "invalid"} {
		server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) { io.WriteString(w, body) }))
		d := doctor{opts: DoctorOptions{Timeout: time.Second}, values: map[string]string{"SOLANA_RPC_URLS": server.URL}}
		d.rpc(context.Background())
		server.Close()
		if findCheck(t, d.report, "rpc.1").Status != Fail {
			t.Fatal("invalid RPC passed")
		}
	}
	target := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) { t.Error("RPC followed a redirect") }))
	defer target.Close()
	redirect := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) { http.Redirect(w, r, target.URL, 307) }))
	defer redirect.Close()
	d := doctor{opts: DoctorOptions{Timeout: time.Second}, values: map[string]string{"SOLANA_RPC_URLS": redirect.URL}}
	d.rpc(context.Background())
	if findCheck(t, d.report, "rpc.1").Status != Fail {
		t.Fatal("redirect passed")
	}
}

func TestDoctorToolsServicesAndSkill(t *testing.T) {
	opts := fixture(t)
	opts.LookPath = func(string) (string, error) { return "", errors.New("not installed") }
	opts.Run = func(context.Context, string, []string, []string, string) (CommandResult, error) {
		return CommandResult{Code: 1}, errors.New("unavailable")
	}
	os.Remove(filepath.Join(opts.ProfileDir, "skills", "solana-dlmm", "scripts"))
	os.Symlink(opts.HomeDir, filepath.Join(opts.ProfileDir, "skills", "solana-dlmm", "scripts"))
	r := Doctor(context.Background(), opts)
	for _, name := range []string{"tool.go", "tool.hermes", "unit.azimuth.service", "linger"} {
		if findCheck(t, r, name).Status != Warn {
			t.Fatalf("expected optional warning: %s", name)
		}
	}
	for _, name := range []string{"tool.python3", "tool.node", "hermes.runtime", "profile.skill"} {
		if findCheck(t, r, name).Status != Fail {
			t.Fatalf("expected failure: %s", name)
		}
	}
}

func TestBinaryArchitectureMismatch(t *testing.T) {
	path := filepath.Join(t.TempDir(), "foreign-binary")
	header := make([]byte, 64)
	copy(header, []byte{0x7f, 'E', 'L', 'F', 2, 1, 1})
	binary.LittleEndian.PutUint16(header[16:], 2)
	machine := uint16(183)
	if runtime.GOARCH == "arm64" {
		machine = 62
	}
	binary.LittleEndian.PutUint16(header[18:], machine)
	binary.LittleEndian.PutUint32(header[20:], 1)
	binary.LittleEndian.PutUint16(header[52:], 64)
	if err := os.WriteFile(path, header, 0700); err != nil {
		t.Fatal(err)
	}
	opts := fixture(t)
	opts.BinaryPaths = []string{path}
	d := doctor{opts: opts}
	d.binaries()
	if findCheck(t, d.report, "binary.extra.1").Status != Fail {
		t.Fatal("foreign executable passed architecture check")
	}
}

func TestDoctorCLIHelpAndInvalidArgs(t *testing.T) {
	for _, args := range [][]string{{"--help"}, {"--unknown=test-secret"}, {"--timeout=0"}, {"unexpected"}} {
		var out, errOut bytes.Buffer
		code := RunDoctorCLI(context.Background(), args, &out, &errOut)
		if args[0] == "--help" {
			if code != 0 || !strings.Contains(out.String(), "Exit codes") {
				t.Fatal("help failed")
			}
		} else if code != 1 {
			t.Fatal("invalid arguments accepted")
		}
		if strings.Contains(errOut.String(), "test-secret") {
			t.Fatal("argument error disclosed user input")
		}
	}
}

func TestDoctorCLIJSONAndExitCodes(t *testing.T) {
	for _, status := range []Status{Pass, Warn, Fail} {
		want := Report{Checks: []Check{{Name: "fixture", Status: status, Detail: "Fixture diagnostic.", Hint: "Fixture fix."}}}
		var out, errOut bytes.Buffer
		code := runDoctorCLI(context.Background(), []string{"--json", "--repo", "fixture-repo", "--env-file", "fixture.env", "--profile", "fixture-profile"}, &out, &errOut, func(_ context.Context, opts DoctorOptions) Report {
			if opts.RepoDir != "fixture-repo" || opts.EnvFile != "fixture.env" || opts.ProfileDir != "fixture-profile" {
				t.Fatal("CLI options were not passed to the engine")
			}
			return want
		})
		var got Report
		if code != want.ExitCode() || errOut.Len() != 0 || json.Unmarshal(out.Bytes(), &got) != nil || got.Checks[0].Status != status {
			t.Fatal("CLI rendering or exit code mismatch")
		}
	}
}

func TestHermesScriptsDrift(t *testing.T) {
	setup := func(t *testing.T, repoFiles, profileFiles map[string]string) DoctorOptions {
		t.Helper()
		opts := fixture(t)
		for dir, files := range map[string]map[string]string{
			filepath.Join(opts.RepoDir, "assets", "hermes", "scripts"): repoFiles,
			filepath.Join(opts.ProfileDir, "scripts"):                  profileFiles,
		} {
			if err := os.MkdirAll(dir, 0700); err != nil {
				t.Fatal(err)
			}
			for name, content := range files {
				if err := os.WriteFile(filepath.Join(dir, name), []byte(content), 0600); err != nil {
					t.Fatal(err)
				}
			}
		}
		return opts
	}
	check := func(opts DoctorOptions) Check {
		return findCheck(t, Doctor(context.Background(), opts), "hermes.scripts.drift")
	}

	t.Run("identical passes", func(t *testing.T) {
		files := map[string]string{"a.py": "print(1)\n", "b.sh": "echo hi\n"}
		if c := check(setup(t, files, files)); c.Status != Pass {
			t.Fatalf("got %s: %s", c.Status, c.Detail)
		}
	})
	t.Run("differing file warns and names it", func(t *testing.T) {
		c := check(setup(t, map[string]string{"a.py": "new", "b.sh": "same"}, map[string]string{"a.py": "old", "b.sh": "same"}))
		if c.Status != Warn || !strings.Contains(c.Detail, "a.py") || strings.Contains(c.Detail, "b.sh") || !strings.Contains(c.Hint, "install.sh") {
			t.Fatalf("got %+v", c)
		}
		if strings.Contains(c.Detail, "new") || strings.Contains(c.Detail, "old") {
			t.Fatalf("contents leaked: %q", c.Detail)
		}
	})
	t.Run("missing file warns", func(t *testing.T) {
		c := check(setup(t, map[string]string{"a.py": "x", "b.sh": "y"}, map[string]string{"a.py": "x"}))
		if c.Status != Warn || !strings.Contains(c.Detail, "missing: b.sh") {
			t.Fatalf("got %+v", c)
		}
	})
	t.Run("profile token rewrite passes", func(t *testing.T) {
		opts := setup(t, map[string]string{"a.py": "ROOT = '__PROFILE__/x'\n"}, nil)
		rewritten := "ROOT = '" + opts.ProfileDir + "/x'\n"
		if err := os.WriteFile(filepath.Join(opts.ProfileDir, "scripts", "a.py"), []byte(rewritten), 0600); err != nil {
			t.Fatal(err)
		}
		if c := check(opts); c.Status != Pass {
			t.Fatalf("got %s: %s", c.Status, c.Detail)
		}
	})
	t.Run("skipped without profile dir", func(t *testing.T) {
		opts := setup(t, map[string]string{"a.py": "x"}, nil)
		opts.ProfileDir = filepath.Join(opts.RepoDir, "absent")
		for _, c := range Doctor(context.Background(), opts).Checks {
			if c.Name == "hermes.scripts.drift" {
				t.Fatalf("unexpected check %+v", c)
			}
		}
	})
}

func TestDoctorRelativeRepoDirSkillAndDrift(t *testing.T) {
	opts := fixture(t) // profile skill link is absolute
	hermes := filepath.Join(opts.RepoDir, "assets", "hermes", "scripts")
	if err := os.MkdirAll(hermes, 0700); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(hermes, "a.py"), []byte("x"), 0600); err != nil {
		t.Fatal(err)
	}
	if err := os.MkdirAll(filepath.Join(opts.ProfileDir, "scripts"), 0700); err != nil {
		t.Fatal(err)
	}
	if err := os.WriteFile(filepath.Join(opts.ProfileDir, "scripts", "a.py"), []byte("x"), 0600); err != nil {
		t.Fatal(err)
	}
	wd, err := os.Getwd()
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = os.Chdir(wd) })
	if err := os.Chdir(filepath.Dir(opts.RepoDir)); err != nil {
		t.Fatal(err)
	}
	opts.RepoDir = filepath.Base(opts.RepoDir) // relative
	opts.EnvFile = ""
	r := Doctor(context.Background(), opts)
	for _, name := range []string{"profile.skill", "hermes.scripts.drift"} {
		if c := findCheck(t, r, name); c.Status != Pass {
			t.Fatalf("%s: got %s: %s", name, c.Status, c.Detail)
		}
	}
}
