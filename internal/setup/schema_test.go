package setup

import (
	"fmt"
	"os"
	"regexp"
	"strings"
	"testing"
)

func TestSchemaMatchesExample(t *testing.T) {
	data, err := os.ReadFile("../../.env.example")
	if err != nil {
		t.Fatal(err)
	}
	assignment := regexp.MustCompile(`^(#\s*)?([A-Z][A-Z0-9_]*)=(.*)$`)
	schema := map[string]Variable{}
	for _, v := range Schema() {
		if _, ok := schema[v.Name]; ok {
			t.Fatalf("duplicate schema field %s", v.Name)
		}
		if v.Description == "" || v.Group == "" || len(v.Modes) == 0 {
			t.Fatalf("missing metadata for %s", v.Name)
		}
		if err := v.Validate(v.Default); err != nil {
			t.Fatal(err)
		}
		schema[v.Name] = v
	}
	seen := map[string]bool{}
	for _, line := range strings.Split(string(data), "\n") {
		m := assignment.FindStringSubmatch(line)
		if m == nil {
			continue
		}
		name, value := m[2], strings.TrimSpace(m[3])
		if len(m[1]) > 1 {
			value = regexp.MustCompile(`\s{2,}`).Split(value, 2)[0]
		}
		if seen[name] {
			t.Fatalf("duplicate example assignment %s", name)
		}
		seen[name] = true
		v, ok := schema[name]
		if !ok {
			t.Fatalf("example field missing from schema: %s", name)
		}
		commented := m[1] != ""
		if v.Commented != commented {
			t.Errorf("%s: commented state drift", name)
		}
		want := v.Default
		if commented {
			want = v.Example
		}
		if want != value {
			t.Errorf("%s: example default drift", name)
		}
		if commented && v.Kind != "command" && name != "DASHBOARD_PASSWORD_HASH" && v.Default != value {
			t.Errorf("%s: optional default drift", name)
		}
	}
	for name := range schema {
		if !seen[name] {
			t.Errorf("schema field missing from example: %s", name)
		}
	}
}

func TestValidateConfigModesAndRedaction(t *testing.T) {
	for _, tt := range []struct {
		name    string
		values  map[string]string
		missing []string
	}{
		{"webhook", map[string]string{}, []string{"HERMES_WEBHOOK_URL", "HERMES_WEBHOOK_SECRET"}},
		{"deterministic", map[string]string{"DEPLOY_CMD": "python3 pipeline.py"}, []string{"SOLANA_PUBLIC_KEY", "SOLANA_RPC_URLS"}},
		{"ai", map[string]string{"AI_HEALTH_CMD": "python probe.py"}, []string{"DEPLOY_CMD", "SOLANA_PUBLIC_KEY", "SOLANA_RPC_URLS", "HERMES_WEBHOOK_URL", "HERMES_WEBHOOK_SECRET"}},
	} {
		t.Run(tt.name, func(t *testing.T) {
			issues := ValidateConfig(tt.values, ActiveModes(tt.values))
			found := map[string]bool{}
			for _, issue := range issues {
				found[issue.Name] = true
			}
			for _, name := range tt.missing {
				if !found[name] {
					t.Errorf("missing requirement: %s", name)
				}
			}
		})
	}
	secret := "test-secret-do-not-echo"
	issues := ValidateConfig(map[string]string{"HERMES_WEBHOOK_URL": secret, "POLL_INTERVAL": secret, "UNKNOWN_SETTING": secret}, []string{"webhook"})
	if strings.Contains(fmt.Sprint(issues), secret) {
		t.Fatal("validator echoed a configured value")
	}
	for _, issue := range issues {
		if issue.Name == "UNKNOWN_SETTING" {
			t.Fatal("unknown key rejected")
		}
	}
	copy := Schema()
	copy[0].Name = "changed"
	copy[0].Modes[0] = "changed"
	if Schema()[0].Name == "changed" || Schema()[0].Modes[0] == "changed" {
		t.Fatal("schema was mutable across callers")
	}
}

func TestVariableValidators(t *testing.T) {
	for _, tt := range []struct {
		kind, good, bad string
		choices         []string
	}{
		{"bool", "true", "maybe", nil}, {"int", "12", "1.2", nil}, {"float", "-1.5", "NaN", nil},
		{"duration", "3s", "0s", nil}, {"url", "https://example.invalid/rpc", "file:///tmp/config", nil},
		{"urls", "https://example.invalid/a,https://example.invalid/b", "https://example.invalid,", nil},
		{"hostport", "127.0.0.1:6379", "127.0.0.1:99999", nil},
		{"enum", "a", "c", []string{"a", "b"}}, {"enums", "a,b", "a,c", []string{"a", "b"}},
		{"string", "literal", "invalid\x00", nil}, {"command", "python3 probe.py", "invalid\n", nil},
	} {
		t.Run(tt.kind, func(t *testing.T) {
			v := Variable{Name: "TEST", Kind: tt.kind, Choices: tt.choices}
			if v.Validate(tt.good) != nil {
				t.Fatal("valid value rejected")
			}
			if v.Validate(tt.bad) == nil {
				t.Fatal("invalid value accepted")
			}
		})
	}
	if !validPubkey(fakePubkey()) || validPubkey(strings.Repeat("0", 32)) || validPubkey(strings.Repeat("2", 32)) {
		t.Fatal("pubkey byte-length validation failed")
	}
}

func TestParseEnvLiterals(t *testing.T) {
	input := "# comment\nexport DRY_RUN=true\nEMPTY=\nA='literal # value' # tail\nB=\"two words\"\nC=value # comment\nUNKNOWN=$(touch should-not-exist)\nA='last wins'\n"
	values, err := ParseEnv(strings.NewReader(input))
	if err != nil {
		t.Fatal(err)
	}
	if values["A"] != "last wins" || values["B"] != "two words" || values["C"] != "value" || values["UNKNOWN"] != "$(touch should-not-exist)" {
		t.Fatal("literal parsing failed")
	}
	quoted, err := ParseEnv(strings.NewReader(`SECRET="literal \"quote\" and \\ slash"`))
	if err != nil || quoted["SECRET"] != `literal "quote" and \ slash` {
		t.Fatal("escaped quoted value was not parsed literally")
	}
	for _, bad := range []string{"SECRET-with-invalid-name=value", "SECRET='unclosed", "SECRET=\"quoted\" unexpected", "no assignment", "SECRET=bad\x00value", strings.Repeat("x", 1024*1024+1)} {
		_, err := ParseEnv(strings.NewReader(bad))
		if err == nil {
			t.Fatal("invalid env accepted")
		}
		if strings.Contains(err.Error(), "SECRET") || strings.Contains(err.Error(), "bad\x00value") {
			t.Fatal("parser echoed input")
		}
	}
}
