package setup

import (
	"bufio"
	"fmt"
	"io"
	"regexp"
	"strings"
)

var envName = regexp.MustCompile(`^[A-Za-z_][A-Za-z0-9_]*$`)

// ParseEnv reads literal dotenv assignments without executing shell expressions.
// Unknown keys are retained for future configuration edits.
func ParseEnv(r io.Reader) (map[string]string, error) {
	values := map[string]string{}
	s := bufio.NewScanner(r)
	s.Buffer(make([]byte, 4096), 1024*1024)
	line := 0
	for s.Scan() {
		line++
		text := strings.TrimSpace(s.Text())
		if text == "" || strings.HasPrefix(text, "#") {
			continue
		}
		text = strings.TrimPrefix(text, "export ")
		key, value, ok := strings.Cut(text, "=")
		key = strings.TrimSpace(key)
		value = strings.TrimSpace(value)
		if !ok || !envName.MatchString(key) {
			return nil, fmt.Errorf("invalid env assignment on line %d", line)
		}
		if strings.HasPrefix(value, "\"") || strings.HasPrefix(value, "'") {
			quote := value[0]
			end := -1
			var literal strings.Builder
			for i := 1; i < len(value); i++ {
				if value[i] == quote {
					end = i
					break
				}
				if quote == '"' && value[i] == '\\' && i+1 < len(value) && (value[i+1] == '"' || value[i+1] == '\\') {
					i++
				}
				literal.WriteByte(value[i])
			}
			if end < 0 {
				return nil, fmt.Errorf("unclosed env quote on line %d", line)
			}
			tail := strings.TrimSpace(value[end+1:])
			if tail != "" && !strings.HasPrefix(tail, "#") {
				return nil, fmt.Errorf("invalid env suffix on line %d", line)
			}
			value = literal.String()
		} else if i := strings.Index(value, " #"); i >= 0 {
			value = strings.TrimSpace(value[:i])
		}
		if strings.ContainsAny(value, "\x00\r\n") {
			return nil, fmt.Errorf("invalid env value on line %d", line)
		}
		values[key] = value
	}
	if s.Err() != nil {
		return nil, fmt.Errorf("cannot read env assignments")
	}
	return values, nil
}
