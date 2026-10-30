package main

import (
	"bufio"
	"crypto/hmac"
	"crypto/rand"
	"crypto/sha256"
	"crypto/subtle"
	"encoding/base64"
	"encoding/binary"
	"encoding/hex"
	"errors"
	"fmt"
	"io"
	"net/http"
	"strconv"
	"strings"
	"sync"
	"time"
)

// Password hashing is PBKDF2-HMAC-SHA256 built on the standard library. The module
// targets Go 1.22, where crypto/pbkdf2 does not exist, and adding x/crypto (scrypt,
// argon2id) would raise the module's Go version and dependency set for one call.
// Format: pbkdf2-sha256:<iterations>:<salt b64url>:<key b64url>. ':' separators keep the
// value free of '$', so it survives shells and systemd EnvironmentFile unquoted.
const (
	hashScheme     = "pbkdf2-sha256"
	hashIterations = 600000 // OWASP 2023 recommendation for PBKDF2-HMAC-SHA256
	minIterations  = 100000
	maxIterations  = 10000000
	sessionCookie  = "azimuth_session"
	sessionTTL     = 12 * time.Hour
	maxSessions    = 32
	failWindow     = 10 * time.Minute
	maxFailures    = 5
)

func pbkdf2SHA256(password, salt []byte, iterations, keyLen int) []byte {
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

type passwordHash struct {
	iterations int
	salt, key  []byte
}

func hashPassword(password string, iterations int) (string, error) {
	if password == "" {
		return "", errors.New("empty password")
	}
	salt := make([]byte, 16)
	if _, err := rand.Read(salt); err != nil {
		return "", err
	}
	key := pbkdf2SHA256([]byte(password), salt, iterations, 32)
	enc := base64.RawURLEncoding
	return fmt.Sprintf("%s:%d:%s:%s", hashScheme, iterations, enc.EncodeToString(salt), enc.EncodeToString(key)), nil
}

func parsePasswordHash(value string) (*passwordHash, error) {
	parts := strings.Split(strings.TrimSpace(value), ":")
	if len(parts) != 4 || parts[0] != hashScheme {
		return nil, errors.New("expected pbkdf2-sha256:<iterations>:<salt>:<key>")
	}
	n, err := strconv.Atoi(parts[1])
	if err != nil || n < minIterations || n > maxIterations {
		return nil, fmt.Errorf("iterations must be %d..%d", minIterations, maxIterations)
	}
	salt, err1 := base64.RawURLEncoding.DecodeString(parts[2])
	key, err2 := base64.RawURLEncoding.DecodeString(parts[3])
	if err1 != nil || err2 != nil || len(salt) < 16 || len(key) != 32 {
		return nil, errors.New("salt or key is malformed")
	}
	return &passwordHash{iterations: n, salt: salt, key: key}, nil
}

func (h *passwordHash) verify(password string) bool {
	got := pbkdf2SHA256([]byte(password), h.salt, h.iterations, len(h.key))
	return subtle.ConstantTimeCompare(got, h.key) == 1
}

// readPassword takes the first stdin line, dropping only the line ending.
func readPassword(r io.Reader) (string, error) {
	line, err := bufio.NewReader(r).ReadString('\n')
	if err != nil && err != io.EOF {
		return "", err
	}
	return strings.TrimRight(line, "\r\n"), nil
}

// auth holds in-memory sessions; a restart logs everyone out by design.
type auth struct {
	mu       sync.Mutex
	verifyMu sync.Mutex // one PBKDF2 at a time bounds CPU under a login flood
	hash     *passwordHash
	problem  string // non-empty: locked, the login page says why
	sessions map[string]time.Time
	failures []time.Time
	now      func() time.Time
}

func newAuth(env string, set bool) *auth {
	a := &auth{sessions: map[string]time.Time{}, now: time.Now}
	switch h, err := parsePasswordHash(env); {
	case !set || strings.TrimSpace(env) == "":
		a.problem = "DASHBOARD_PASSWORD_HASH is not set. The dashboard refuses to serve data until a password hash is configured."
	case err != nil:
		a.problem = "DASHBOARD_PASSWORD_HASH is invalid (" + err.Error() + "). The dashboard refuses to serve data."
	default:
		a.hash = h
	}
	return a
}

// lockedFor reports how long logins stay refused after too many recent failures.
func (a *auth) lockedFor() time.Duration {
	a.mu.Lock()
	defer a.mu.Unlock()
	now := a.now()
	kept := a.failures[:0]
	for _, t := range a.failures {
		if now.Sub(t) < failWindow {
			kept = append(kept, t)
		}
	}
	a.failures = kept
	if len(kept) < maxFailures {
		return 0
	}
	return failWindow - now.Sub(kept[len(kept)-maxFailures])
}

// login returns a new session token, or "" on a refused attempt.
func (a *auth) login(password string) string {
	if a.hash == nil || a.lockedFor() > 0 {
		return ""
	}
	a.verifyMu.Lock()
	ok := a.hash.verify(password)
	a.verifyMu.Unlock()
	a.mu.Lock()
	defer a.mu.Unlock()
	now := a.now()
	if !ok {
		a.failures = append(a.failures, now)
		return ""
	}
	a.failures = nil
	raw := make([]byte, 32)
	if _, err := rand.Read(raw); err != nil {
		return ""
	}
	token := hex.EncodeToString(raw)
	for k, exp := range a.sessions {
		if !now.Before(exp) {
			delete(a.sessions, k)
		}
	}
	for len(a.sessions) >= maxSessions {
		oldest := ""
		for k, exp := range a.sessions {
			if oldest == "" || exp.Before(a.sessions[oldest]) {
				oldest = k
			}
		}
		delete(a.sessions, oldest)
	}
	a.sessions[sessionKey(token)] = now.Add(sessionTTL)
	return token
}

// Sessions are stored by digest so process memory never holds a usable cookie.
func sessionKey(token string) string {
	sum := sha256.Sum256([]byte(token))
	return hex.EncodeToString(sum[:])
}

func (a *auth) valid(token string) bool {
	if a.hash == nil || len(token) != 64 {
		return false
	}
	a.mu.Lock()
	defer a.mu.Unlock()
	key := sessionKey(token)
	exp, ok := a.sessions[key]
	if ok && !a.now().Before(exp) {
		delete(a.sessions, key)
		return false
	}
	return ok
}

func (a *auth) logout(token string) {
	a.mu.Lock()
	delete(a.sessions, sessionKey(token))
	a.mu.Unlock()
}

func (s *server) signedIn(r *http.Request) bool {
	c, err := r.Cookie(sessionCookie)
	return err == nil && s.auth != nil && s.auth.valid(c.Value)
}

// sameOrigin rejects cross-site form posts in addition to the SameSite=Strict cookie.
func sameOrigin(r *http.Request) bool {
	if site := r.Header.Get("Sec-Fetch-Site"); site != "" && site != "same-origin" && site != "none" {
		return false
	}
	origin := r.Header.Get("Origin")
	return origin == "" || origin == "http://"+r.Host
}

type loginView struct {
	Problem, Message string
	Locked           bool
}

func renderLogin(w http.ResponseWriter, status int, view loginView) {
	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	w.WriteHeader(status)
	loginPage.Execute(w, view)
}

func (s *server) serveLogin(w http.ResponseWriter, r *http.Request) {
	a := s.auth
	if a == nil {
		a = &auth{problem: "No password configuration loaded. The dashboard refuses to serve data."}
	}
	switch r.Method {
	case "GET", "HEAD":
		if a.problem != "" {
			renderLogin(w, http.StatusServiceUnavailable, loginView{Problem: a.problem})
			return
		}
		if s.signedIn(r) {
			http.Redirect(w, r, "/", http.StatusSeeOther)
			return
		}
		if wait := a.lockedFor(); wait > 0 {
			renderLogin(w, http.StatusTooManyRequests, loginView{Message: lockMessage(wait), Locked: true})
			return
		}
		renderLogin(w, http.StatusOK, loginView{})
	case "POST":
		if !sameOrigin(r) {
			http.Error(w, "cross-site login refused", http.StatusForbidden)
			return
		}
		if a.problem != "" {
			renderLogin(w, http.StatusServiceUnavailable, loginView{Problem: a.problem})
			return
		}
		if wait := a.lockedFor(); wait > 0 {
			renderLogin(w, http.StatusTooManyRequests, loginView{Message: lockMessage(wait), Locked: true})
			return
		}
		r.Body = http.MaxBytesReader(w, r.Body, 4096)
		if err := r.ParseForm(); err != nil {
			renderLogin(w, http.StatusBadRequest, loginView{Message: "The form could not be read. Try again."})
			return
		}
		token := a.login(r.PostForm.Get("password"))
		if token == "" {
			if wait := a.lockedFor(); wait > 0 {
				renderLogin(w, http.StatusTooManyRequests, loginView{Message: lockMessage(wait), Locked: true})
				return
			}
			renderLogin(w, http.StatusUnauthorized, loginView{Message: "That password did not match. Check it and try again."})
			return
		}
		http.SetCookie(w, &http.Cookie{Name: sessionCookie, Value: token, Path: "/", MaxAge: int(sessionTTL.Seconds()), HttpOnly: true, SameSite: http.SameSiteStrictMode})
		http.Redirect(w, r, "/", http.StatusSeeOther)
	default:
		w.Header().Set("Allow", "GET, HEAD, POST")
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
	}
}

func lockMessage(wait time.Duration) string {
	minutes := int(wait.Minutes()) + 1
	return fmt.Sprintf("Too many failed attempts. Sign-in is paused for about %d min.", minutes)
}

func (s *server) serveLogout(w http.ResponseWriter, r *http.Request) {
	if r.Method != "POST" {
		w.Header().Set("Allow", "POST")
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}
	if !sameOrigin(r) {
		http.Error(w, "cross-site logout refused", http.StatusForbidden)
		return
	}
	if c, err := r.Cookie(sessionCookie); err == nil && s.auth != nil {
		s.auth.logout(c.Value)
	}
	http.SetCookie(w, &http.Cookie{Name: sessionCookie, Value: "", Path: "/", MaxAge: -1, HttpOnly: true, SameSite: http.SameSiteStrictMode})
	http.Redirect(w, r, "/login", http.StatusSeeOther)
}
