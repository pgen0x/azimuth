// Package setup provides local installation diagnostics and configuration metadata.
package setup

import (
	_ "embed"
	"encoding/json"
	"fmt"
	"math"
	"math/big"
	"net"
	"net/url"
	"regexp"
	"strconv"
	"strings"
	"time"
)

// Variable describes an environment setting shared by setup front ends.
type Variable struct {
	Name        string   `json:"name"`
	Group       string   `json:"group"`
	Description string   `json:"description"`
	Required    bool     `json:"required"`
	Secret      bool     `json:"secret"`
	Default     string   `json:"default"`
	Kind        string   `json:"kind"`
	Modes       []string `json:"modes"`
	Choices     []string `json:"choices,omitempty"`
	Commented   bool     `json:"commented,omitempty"`
	Example     string   `json:"example,omitempty"`
}

//go:embed schema.json
var schemaData []byte

// Schema returns a fresh copy so callers cannot mutate shared metadata.
func Schema() []Variable {
	var fields []Variable
	if err := json.Unmarshal(schemaData, &fields); err != nil {
		panic("invalid embedded setup schema")
	}
	return fields
}

func applies(v Variable, modes []string) bool {
	for _, m := range v.Modes {
		if m == "all" {
			return true
		}
		for _, active := range modes {
			if active == m {
				return true
			}
		}
	}
	return false
}

// ConfigIssue contains only schema-owned text, never caller-supplied values.
type ConfigIssue struct {
	Name    string
	Message string
	Hint    string
}

// ValidateConfig checks supplied values and required fields for the active modes.
// Unknown keys are allowed so setup can preserve settings owned by other tools.
func ValidateConfig(values map[string]string, modes []string) []ConfigIssue {
	var issues []ConfigIssue
	for _, v := range Schema() {
		value := values[v.Name]
		if v.Required && applies(v, modes) && (strings.TrimSpace(value) == "" || value == "dlmm-signal-secret-change-me") {
			issues = append(issues, ConfigIssue{v.Name, "Required setting is missing or still a placeholder.", "Set " + v.Name + " for the selected routing mode."})
		} else if v.Validate(value) != nil {
			issues = append(issues, ConfigIssue{v.Name, "Setting does not match the schema.", "Use a valid " + v.Kind + " for " + v.Name + "."})
		}
	}
	return issues
}

// Validate never includes a supplied value in an error, including non-secret values.
func (v Variable) Validate(value string) error {
	bad := func() error { return fmt.Errorf("%s: expected %s", v.Name, v.Kind) }
	if value == "" {
		return nil
	}
	switch v.Kind {
	case "string", "command":
		if strings.ContainsAny(value, "\x00\r\n") || (v.Kind == "command" && len(strings.Fields(value)) == 0) {
			return bad()
		}
	case "bool":
		if _, err := strconv.ParseBool(value); err != nil {
			return bad()
		}
	case "int":
		if _, err := strconv.ParseInt(value, 10, 64); err != nil {
			return bad()
		}
	case "float":
		n, err := strconv.ParseFloat(value, 64)
		if err != nil || math.IsNaN(n) || math.IsInf(n, 0) {
			return bad()
		}
	case "duration":
		n, err := time.ParseDuration(value)
		if err != nil || n <= 0 {
			return bad()
		}
	case "url", "urls":
		for _, part := range strings.Split(value, ",") {
			if v.Kind == "url" && strings.Contains(value, ",") {
				return bad()
			}
			u, err := url.Parse(strings.TrimSpace(part))
			if err != nil || (u.Scheme != "http" && u.Scheme != "https") || u.Hostname() == "" || u.Fragment != "" {
				return bad()
			}
		}
	case "hostport":
		host, port, err := net.SplitHostPort(value)
		n, parseErr := strconv.Atoi(port)
		if err != nil || parseErr != nil || host == "" || n < 1 || n > 65535 {
			return bad()
		}
	case "pubkey":
		if !validPubkey(value) {
			return bad()
		}
	case "evm-address":
		if !regexp.MustCompile(`^0x[0-9a-fA-F]{40}$`).MatchString(value) {
			return bad()
		}
	case "enum", "enums":
		parts := []string{value}
		if v.Kind == "enums" {
			parts = strings.Split(value, ",")
		}
		for _, part := range parts {
			found := false
			for _, choice := range v.Choices {
				if strings.TrimSpace(part) == choice {
					found = true
				}
			}
			if !found {
				return bad()
			}
		}
	default:
		return bad()
	}
	return nil
}

func validPubkey(s string) bool {
	if len(s) < 32 || len(s) > 44 {
		return false
	}
	n := new(big.Int)
	for _, r := range s {
		d := strings.IndexRune("123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz", r)
		if d < 0 {
			return false
		}
		n.Mul(n, big.NewInt(58))
		n.Add(n, big.NewInt(int64(d)))
	}
	return len(n.Bytes())+len(s)-len(strings.TrimLeft(s, "1")) == 32
}

// ActiveModes derives the routing mode without changing runtime configuration.
func ActiveModes(values map[string]string) []string {
	route := "webhook"
	if values["DEPLOY_CMD"] != "" {
		route = "deterministic"
	}
	if values["AI_HEALTH_CMD"] != "" {
		route = "ai"
	}
	modes := []string{"solana", route}
	for _, name := range []string{"ROBINHOOD_ENABLED", "ROBINHOOD_MATURE", "ROBINHOOD_LADDER", "ROBINHOOD_STOCK_LADDER", "ROBINHOOD_PULSE_LADDER", "ROBINHOOD_TURNOVER"} {
		if b, _ := strconv.ParseBool(values[name]); b {
			modes = append(modes, "robinhood")
			break
		}
	}
	return modes
}
