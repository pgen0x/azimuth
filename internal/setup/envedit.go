package setup

import (
	"bytes"
	"errors"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"regexp"
	"strings"
)

const maxEnvBytes = 1024 * 1024

// EnvDoc is a dotenv file edited line by line. Comments, ordering, blank lines
// and keys setup knows nothing about survive every edit, so re-running setup
// edits a config instead of regenerating it.
type EnvDoc struct {
	lines    []string
	appended bool
}

var (
	activeAssign    = regexp.MustCompile(`^\s*(export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=`)
	commentedAssign = regexp.MustCompile(`^#\s*([A-Za-z_][A-Za-z0-9_]*)=`)
	bareValue       = regexp.MustCompile(`^[A-Za-z0-9_./:,@%+=-]*$`)
)

// ParseEnvDoc accepts only text ParseEnv can read, so setup never rewrites a
// file the daemon would reject.
func ParseEnvDoc(data []byte) (*EnvDoc, error) {
	if len(data) > maxEnvBytes {
		return nil, errors.New("configuration file is too large")
	}
	if _, err := ParseEnv(bytes.NewReader(data)); err != nil {
		return nil, err
	}
	text := strings.TrimSuffix(string(data), "\n")
	if text == "" {
		return &EnvDoc{}, nil
	}
	return &EnvDoc{lines: strings.Split(text, "\n")}, nil
}

// ReadEnvDoc loads path. A missing file returns (nil, false, nil); a symlink or
// other non-regular file is refused, matching doctor's env.file check.
func ReadEnvDoc(path string) (*EnvDoc, bool, error) {
	info, err := os.Lstat(path)
	if errors.Is(err, os.ErrNotExist) {
		return nil, false, nil
	}
	if err != nil {
		return nil, false, errors.New("cannot inspect configuration file")
	}
	if !info.Mode().IsRegular() {
		return nil, true, errors.New("configuration must be a regular file, not a symlink")
	}
	f, err := os.Open(path)
	if err != nil {
		return nil, true, errors.New("cannot open configuration file")
	}
	defer f.Close()
	data, err := io.ReadAll(io.LimitReader(f, maxEnvBytes+1))
	if err != nil {
		return nil, true, errors.New("cannot read configuration file")
	}
	doc, err := ParseEnvDoc(data)
	if err != nil {
		return nil, true, fmt.Errorf("configuration file is not literal dotenv: %w", err)
	}
	return doc, true, nil
}

// Values returns the parsed assignments.
func (d *EnvDoc) Values() map[string]string {
	values, err := ParseEnv(bytes.NewReader(d.Bytes()))
	if err != nil {
		return map[string]string{}
	}
	return values
}

// FormatEnvValue renders a value both systemd EnvironmentFile and `set -a; . .env`
// read literally: bare when it is shell-safe, otherwise single-quoted. A value
// that cannot be represented that way is refused rather than escaped.
func FormatEnvValue(value string) (string, error) {
	if strings.ContainsAny(value, "\x00\r\n") {
		return "", errors.New("value contains a control character")
	}
	if bareValue.MatchString(value) {
		return value, nil
	}
	if strings.ContainsRune(value, '\'') {
		return "", errors.New("value contains a single quote")
	}
	return "'" + value + "'", nil
}

// Set assigns key. Every active assignment of key is rewritten in place; with
// none, the first commented template line (`#KEY=...`) is uncommented; failing
// that, the assignment is appended. Setting "" on an absent key is a no-op.
// Errors never contain the value.
func (d *EnvDoc) Set(key, value string) error {
	if !envName.MatchString(key) {
		return errors.New("invalid variable name")
	}
	rendered, err := FormatEnvValue(value)
	if err != nil {
		return fmt.Errorf("%s: %w", key, err)
	}
	found := false
	for i, line := range d.lines {
		m := activeAssign.FindStringSubmatch(line)
		if m != nil && m[2] == key {
			d.lines[i] = m[1] + key + "=" + rendered
			found = true
		}
	}
	if found || value == "" {
		return nil
	}
	for i, line := range d.lines {
		if m := commentedAssign.FindStringSubmatch(line); m != nil && m[1] == key {
			d.lines[i] = key + "=" + rendered
			return nil
		}
	}
	if !d.appended {
		if len(d.lines) > 0 && d.lines[len(d.lines)-1] != "" {
			d.lines = append(d.lines, "")
		}
		d.lines = append(d.lines, "# ─── Written by azimuth setup ───")
		d.appended = true
	}
	d.lines = append(d.lines, key+"="+rendered)
	return nil
}

// Bytes renders the document with a trailing newline.
func (d *EnvDoc) Bytes() []byte {
	if len(d.lines) == 0 {
		return nil
	}
	return []byte(strings.Join(d.lines, "\n") + "\n")
}

// WriteFile0600 replaces path atomically with a 0600 file: temp file in the
// same directory, fsync, rename. An existing symlink at path is refused so a
// write can never be redirected elsewhere.
func WriteFile0600(path string, data []byte) error {
	if info, err := os.Lstat(path); err == nil && !info.Mode().IsRegular() {
		return errors.New("refusing to replace a symlink or non-regular file")
	}
	dir := filepath.Dir(path)
	if err := os.MkdirAll(dir, 0o700); err != nil {
		return errors.New("cannot create configuration directory")
	}
	tmp, err := os.CreateTemp(dir, "."+filepath.Base(path)+".setup-*")
	if err != nil {
		return errors.New("cannot create temporary file")
	}
	name := tmp.Name()
	ok := false
	defer func() {
		if !ok {
			tmp.Close()
			os.Remove(name)
		}
	}()
	if err := tmp.Chmod(0o600); err != nil {
		return errors.New("cannot set file permissions")
	}
	if _, err := tmp.Write(data); err != nil {
		return errors.New("cannot write temporary file")
	}
	if err := tmp.Sync(); err != nil {
		return errors.New("cannot sync temporary file")
	}
	if err := tmp.Close(); err != nil {
		return errors.New("cannot close temporary file")
	}
	if err := os.Rename(name, path); err != nil {
		return errors.New("cannot replace configuration file")
	}
	ok = true
	return nil
}
