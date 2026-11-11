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
	opts.Run = func(_ context.Context, name string, args, env []string) (CommandResult, error) {
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
		if len(args) > 0 && args[0] == "-c" {
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
	opts.Run = func(ctx context.Context, name string, args, env []string) (CommandResult, error) {
		if name == "probe" {
			return CommandResult{Code: 14, Output: secret}, errors.New(secret)
		}
		return run(ctx, name, args, env)
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
	opts.Run = func(ctx context.Context, name string, args, env []string) (CommandResult, error) {
		if strings.HasPrefix(name, "must-not-run") {
			t.Fatal("doctor executed an action command")
		}
		return run(ctx, name, args, env)
	}
	Doctor(context.Background(), opts)
}

func TestDoctorToolVersionAndCommandDeadline(t *testing.T) {
	opts := fixture(t)
	run := opts.Run
	opts.Run = func(ctx context.Context, name string, args, env []string) (CommandResult, error) {
		if _, ok := ctx.Deadline(); !ok {
			t.Fatal("command has no deadline")
		}
		if len(args) > 0 && args[0] == "--version" {
			return CommandResult{Output: "version 1.0.0"}, nil
		}
		return run(ctx, name, args, env)
	}
	r := Doctor(context.Background(), opts)
	if findCheck(t, r, "tool.python3").Status != Fail || findCheck(t, r, "tool.node").Status != Fail {
		t.Fatal("unsupported version passed")
	}
	ctx, cancel := context.WithCancel(context.Background())
	cancel()
	opts.Run = func(ctx context.Context, _ string, _ []string, _ []string) (CommandResult, error) {
		<-ctx.Done()
		return CommandResult{Code: -1}, ctx.Err()
	}
	d := doctor{opts: opts, values: map[string]string{"AI_HEALTH_CMD": "read-only-test-probe"}}
	d.ai(ctx)
	if findCheck(t, d.report, "ai.probe").Status != Fail {
		t.Fatal("canceled probe passed")
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
	opts.Run = func(context.Context, string, []string, []string) (CommandResult, error) {
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
