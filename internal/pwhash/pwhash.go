// Package pwhash implements the dashboard's PBKDF2-HMAC-SHA256 password hash.
//
// It lives outside cmd/dashboard so `azimuth setup` can write the same
// DASHBOARD_PASSWORD_HASH value the dashboard verifies. The module targets
// Go 1.22, where crypto/pbkdf2 does not exist, and adding x/crypto (scrypt,
// argon2id) would raise the module's Go version and dependency set for one call.
// Format: pbkdf2-sha256:<iterations>:<salt b64url>:<key b64url>. ':' separators
// keep the value free of '$', so it survives shells and systemd EnvironmentFile
// unquoted.
package pwhash

import (
	"crypto/hmac"
	"crypto/rand"
	"crypto/sha256"
	"crypto/subtle"
	"encoding/base64"
	"encoding/binary"
	"errors"
	"fmt"
	"strconv"
	"strings"
)

const (
	Scheme            = "pbkdf2-sha256"
	DefaultIterations = 600000 // OWASP 2023 recommendation for PBKDF2-HMAC-SHA256
	MinIterations     = 100000
	MaxIterations     = 10000000
)

// PBKDF2SHA256 is RFC 8018 PBKDF2 with HMAC-SHA256.
func PBKDF2SHA256(password, salt []byte, iterations, keyLen int) []byte {
	prf := hmac.New(sha256.New, password)
	out := make([]byte, 0, keyLen)
	var counter [4]byte
	for block := uint32(1); len(out) < keyLen; block++ {
		prf.Reset()
		prf.Write(salt)
		binary.BigEndian.PutUint32(counter[:], block)
		prf.Write(counter[:])
		u := prf.Sum(nil)
		t := append([]byte(nil), u...)
		for i := 1; i < iterations; i++ {
			prf.Reset()
			prf.Write(u)
			u = prf.Sum(u[:0])
			for j := range t {
				t[j] ^= u[j]
			}
		}
		out = append(out, t...)
	}
	return out[:keyLen]
}

// Hash returns a new salted hash string for password.
func Hash(password string, iterations int) (string, error) {
	if password == "" {
		return "", errors.New("empty password")
	}
	salt := make([]byte, 16)
	if _, err := rand.Read(salt); err != nil {
		return "", err
	}
	key := PBKDF2SHA256([]byte(password), salt, iterations, 32)
	enc := base64.RawURLEncoding
	return fmt.Sprintf("%s:%d:%s:%s", Scheme, iterations, enc.EncodeToString(salt), enc.EncodeToString(key)), nil
}

// Parsed is a decoded hash string.
type Parsed struct {
	iterations int
	salt, key  []byte
}

// Parse decodes and bounds-checks a hash string.
func Parse(value string) (*Parsed, error) {
	parts := strings.Split(strings.TrimSpace(value), ":")
	if len(parts) != 4 || parts[0] != Scheme {
		return nil, errors.New("expected pbkdf2-sha256:<iterations>:<salt>:<key>")
	}
	n, err := strconv.Atoi(parts[1])
	if err != nil || n < MinIterations || n > MaxIterations {
		return nil, fmt.Errorf("iterations must be %d..%d", MinIterations, MaxIterations)
	}
	salt, err1 := base64.RawURLEncoding.DecodeString(parts[2])
	key, err2 := base64.RawURLEncoding.DecodeString(parts[3])
	if err1 != nil || err2 != nil || len(salt) < 16 || len(key) != 32 {
		return nil, errors.New("salt or key is malformed")
	}
	return &Parsed{iterations: n, salt: salt, key: key}, nil
}

// Verify compares in constant time.
func (h *Parsed) Verify(password string) bool {
	got := PBKDF2SHA256([]byte(password), h.salt, h.iterations, len(h.key))
	return subtle.ConstantTimeCompare(got, h.key) == 1
}
