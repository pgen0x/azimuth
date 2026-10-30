package main

import (
	"encoding/hex"
	"net/http"
	"net/http/httptest"
	"net/url"
	"strings"
	"sync"
	"testing"
	"time"
)

const testPassword = "correct horse battery staple"

var (
	testHashOnce sync.Once
	testHash     string
)

// fixtureHash uses the minimum accepted iteration count to keep tests fast.
func fixtureHash(t *testing.T) string {
	testHashOnce.Do(func() {
		h, err := hashPassword(testPassword, minIterations)
		if err != nil {
			t.Fatal(err)
		}
		testHash = h
	})
	return testHash
}

// signIn configures auth on s and returns a valid session cookie.
func signIn(t *testing.T, s *server) *http.Cookie {
	t.Helper()
	s.auth = newAuth(fixtureHash(t), true)
	token := s.auth.login(testPassword)
	if token == "" {
		t.Fatal("fixture login failed")
	}
	return &http.Cookie{Name: sessionCookie, Value: token}
}

func do(s *server, method, path string, form url.Values, cookie *http.Cookie, headers map[string]string) *httptest.ResponseRecorder {
	var body *strings.Reader
	if form != nil {
		body = strings.NewReader(form.Encode())
	} else {
		body = strings.NewReader("")
	}
	r := httptest.NewRequest(method, path, body)
	r.Host = "127.0.0.1:8798"
	if form != nil {
		r.Header.Set("Content-Type", "application/x-www-form-urlencoded")
	}
	if cookie != nil {
		r.AddCookie(cookie)
	}
	for k, v := range headers {
		r.Header.Set(k, v)
	}
	w := httptest.NewRecorder()
	s.ServeHTTP(w, r)
	return w
}

func TestPBKDF2Vectors(t *testing.T) {
	// Published PBKDF2-HMAC-SHA256 vectors (password "password", salt "salt", 32-byte key).
	for iterations, want := range map[int]string{
		1:    "120fb6cffcf8b32c43e7225256c4f837a86548c92ccc35480805987cb70be17b",
		2:    "ae4d0c95af6b46d32d0adff928f06dd02a303f8ef3c251dfd6e2d85a95474c43",
		4096: "c5e478d59288c841aa530db6845c4c8d962893a001ce4e11a4963873aa98134a",
	} {
		if got := hex.EncodeToString(pbkdf2SHA256([]byte("password"), []byte("salt"), iterations, 32)); got != want {
			t.Fatalf("%d iterations: %s", iterations, got)
		}
	}
}

func TestHashFormatAndVerify(t *testing.T) {
	h := fixtureHash(t)
	if !strings.HasPrefix(h, "pbkdf2-sha256:100000:") || strings.Contains(h, testPassword) || strings.ContainsAny(h, "$ ") {
		t.Fatalf("unexpected hash shape: %s", h)
	}
	parsed, err := parsePasswordHash(h)
	if err != nil || !parsed.verify(testPassword) || parsed.verify(testPassword+" ") || parsed.verify("") {
		t.Fatal("verify mismatch")
	}
	other, _ := hashPassword(testPassword, minIterations)
	if other == h {
		t.Fatal("salt is not random")
	}
	for _, bad := range []string{"", "plaintext", "pbkdf2-sha256:1000:" + strings.SplitN(h, ":", 3)[2], "pbkdf2-sha256:x:a:b", "scrypt:100000:a:b", h + ":extra"} {
		if _, err := parsePasswordHash(bad); err == nil {
			t.Fatalf("accepted %q", bad)
		}
	}
	if _, err := hashPassword("", minIterations); err == nil {
		t.Fatal("empty password hashed")
	}
	if p, _ := readPassword(strings.NewReader("pw with spaces \r\nsecond line")); p != "pw with spaces " {
		t.Fatalf("readPassword: %q", p)
	}
}

func TestLoginGateFailsClosed(t *testing.T) {
	data := object{"collected_at": 1, "nav": object{"native_sol": 1.0}}
	for _, a := range []*auth{nil, newAuth("", false), newAuth("", true), newAuth("pbkdf2-sha256:5:short:key", true)} {
		s := &server{data: data, auth: a}
		if w := do(s, "GET", "/api/overview", nil, nil, nil); w.Code != 401 || strings.Contains(w.Body.String(), "native_sol") {
			t.Fatalf("api without session: %d %s", w.Code, w.Body.String())
		}
		if w := do(s, "GET", "/", nil, nil, nil); w.Code != 303 || w.Header().Get("Location") != "/login" {
			t.Fatalf("page without session: %d", w.Code)
		}
		w := do(s, "GET", "/login", nil, nil, nil)
		if w.Code != 503 || !strings.Contains(w.Body.String(), "DASHBOARD_PASSWORD_HASH") && !strings.Contains(w.Body.String(), "No password configuration") {
			t.Fatalf("locked login page: %d %s", w.Code, w.Body.String())
		}
		if w := do(s, "POST", "/login", url.Values{"password": {testPassword}}, nil, nil); w.Code != 503 || w.Header().Get("Set-Cookie") != "" {
			t.Fatalf("locked login accepted: %d", w.Code)
		}
	}
	// Static assets of the login page stay public; nothing else does.
	s := &server{data: data, auth: newAuth("", false)}
	for path, kind := range map[string]string{"/favicon.svg": "image/svg+xml", "/ui.css": "text/css; charset=utf-8"} {
		if w := do(s, "GET", path, nil, nil, nil); w.Code != 200 || w.Header().Get("Content-Type") != kind {
			t.Fatalf("%s: %d", path, w.Code)
		}
	}
	if w := do(s, "GET", "/api/capital", nil, &http.Cookie{Name: sessionCookie, Value: strings.Repeat("a", 64)}, nil); w.Code != 401 {
		t.Fatalf("forged cookie: %d", w.Code)
	}
}

func TestLoginSessionLogout(t *testing.T) {
	s := &server{data: object{"collected_at": 1, "nav": object{"native_sol": 1.0}}, auth: newAuth(fixtureHash(t), true)}
	if w := do(s, "GET", "/login", nil, nil, nil); w.Code != 200 || !strings.Contains(w.Body.String(), `type="password"`) {
		t.Fatalf("login page: %d", w.Code)
	}
	if w := do(s, "POST", "/login", url.Values{"password": {"wrong"}}, nil, nil); w.Code != 401 || w.Header().Get("Set-Cookie") != "" || strings.Contains(w.Body.String(), "wrong") {
		t.Fatalf("wrong password: %d", w.Code)
	}
	if w := do(s, "POST", "/login", url.Values{"password": {testPassword}}, nil, map[string]string{"Origin": "http://evil.example"}); w.Code != 403 {
		t.Fatalf("cross-site login: %d", w.Code)
	}
	if w := do(s, "POST", "/login", url.Values{"password": {testPassword}}, nil, map[string]string{"Sec-Fetch-Site": "cross-site"}); w.Code != 403 {
		t.Fatalf("cross-site fetch login: %d", w.Code)
	}
	if w := do(s, "GET", "/login", nil, nil, nil); w.Header().Get("Referrer-Policy") != "same-origin" {
		t.Fatal("no-referrer would make the browser send Origin: null and refuse its own login")
	}
	w := do(s, "POST", "/login", url.Values{"password": {testPassword}}, nil, map[string]string{"Origin": "http://127.0.0.1:8798", "Sec-Fetch-Site": "same-origin"})
	if w.Code != 303 || w.Header().Get("Location") != "/" {
		t.Fatalf("login: %d", w.Code)
	}
	cookies := w.Result().Cookies()
	if len(cookies) != 1 || !cookies[0].HttpOnly || cookies[0].SameSite != http.SameSiteStrictMode || len(cookies[0].Value) != 64 || cookies[0].Path != "/" {
		t.Fatalf("cookie attributes: %+v", cookies)
	}
	cookie := cookies[0]
	if w := do(s, "GET", "/api/overview", nil, cookie, nil); w.Code != 200 || !strings.Contains(w.Body.String(), "native_sol") {
		t.Fatalf("api with session: %d", w.Code)
	}
	if w := do(s, "GET", "/", nil, cookie, nil); w.Code != 200 || !strings.Contains(w.Body.String(), "azimuth") {
		t.Fatalf("page with session: %d", w.Code)
	}
	if w := do(s, "GET", "/login", nil, cookie, nil); w.Code != 303 {
		t.Fatalf("login while signed in: %d", w.Code)
	}
	if w := do(s, "GET", "/logout", nil, cookie, nil); w.Code != 405 {
		t.Fatalf("logout via GET: %d", w.Code)
	}
	w = do(s, "POST", "/logout", nil, cookie, nil)
	if w.Code != 303 || w.Header().Get("Location") != "/login" || w.Result().Cookies()[0].MaxAge >= 0 {
		t.Fatalf("logout: %d", w.Code)
	}
	if w := do(s, "GET", "/api/overview", nil, cookie, nil); w.Code != 401 {
		t.Fatalf("session survived logout: %d", w.Code)
	}
}

func TestSessionExpiryAndRateLimit(t *testing.T) {
	clock := time.Unix(1_800_000_000, 0)
	a := newAuth(fixtureHash(t), true)
	a.now = func() time.Time { return clock }
	token := a.login(testPassword)
	if !a.valid(token) {
		t.Fatal("fresh session invalid")
	}
	clock = clock.Add(sessionTTL)
	if a.valid(token) {
		t.Fatal("expired session accepted")
	}
	for i := 0; i < maxFailures; i++ {
		if a.login("nope") != "" {
			t.Fatal("wrong password accepted")
		}
	}
	if a.lockedFor() <= 0 || a.login(testPassword) != "" {
		t.Fatal("rate limit did not lock out the correct password")
	}
	s := &server{auth: a}
	if w := do(s, "POST", "/login", url.Values{"password": {testPassword}}, nil, nil); w.Code != 429 || !strings.Contains(w.Body.String(), "paused") {
		t.Fatalf("locked POST: %d", w.Code)
	}
	clock = clock.Add(failWindow)
	if a.lockedFor() != 0 || a.login(testPassword) == "" {
		t.Fatal("lockout did not expire")
	}
	for i := 0; i < maxSessions+5; i++ {
		a.login(testPassword)
	}
	if len(a.sessions) > maxSessions {
		t.Fatalf("sessions unbounded: %d", len(a.sessions))
	}
}

func TestZoneValidation(t *testing.T) {
	for in, want := range map[string]string{
		"UTC": "UTC", "Asia/Jakarta": "Asia/Jakarta", "America/Sao_Paulo": "America/Sao_Paulo",
		"America/Argentina/Buenos_Aires": "America/Argentina/Buenos_Aires", "Etc/GMT+5": "Etc/GMT+5",
		"Local": "", "../../etc/passwd": "", "Mars/Olympus": "", "Asia/Jakarta\n": "", "/etc/localtime": "", strings.Repeat("A", 70): "",
	} {
		if got := validZone(in); got != want {
			t.Fatalf("%q: %q", in, got)
		}
	}
	if tz, fb := requestZone(""); tz != "UTC" || fb {
		t.Fatal("missing zone must be UTC without fallback")
	}
	if tz, fb := requestZone("Nope/Zone"); tz != "UTC" || !fb {
		t.Fatal("invalid zone must fall back to UTC visibly")
	}
	s := &server{data: object{"collected_at": 1, "by_tz": object{
		"UTC":               object{"north_star": object{"tz": "UTC"}, "realized": object{"tz": "UTC"}},
		"America/Sao_Paulo": object{"north_star": object{"tz": "America/Sao_Paulo"}, "realized": object{"tz": "America/Sao_Paulo"}},
	}, "live": object{"dust": object{"runs": 1}}}}
	cookie := signIn(t, s)
	w := do(s, "GET", "/api/capital?tz=America/Sao_Paulo", nil, cookie, nil)
	if !strings.Contains(w.Body.String(), `"north_star":{"tz":"America/Sao_Paulo"}`) || !strings.Contains(w.Body.String(), `"tz":"America/Sao_Paulo","tz_error":"","tz_fallback":false`) {
		t.Fatalf("capital zone: %s", w.Body.String())
	}
	w = do(s, "GET", "/api/live?tz=America/Sao_Paulo", nil, cookie, nil)
	if !strings.Contains(w.Body.String(), `"live":{"dust":{"runs":1},"realized":{"tz":"America/Sao_Paulo"}}`) {
		t.Fatalf("live zone: %s", w.Body.String())
	}
	if got := s.zoneList(); len(got) != 2 || got[1] != "America/Sao_Paulo" {
		t.Fatalf("zone not retained for refresh: %v", got)
	}
	if _, nested := s.data["live"].(object)["realized"]; nested {
		t.Fatal("request mutated the cached snapshot")
	}
	for i := 0; i < maxZones+3; i++ {
		s.useZone("Etc/GMT+" + string(rune('1'+i)))
	}
	if len(s.zoneList()) != maxZones {
		t.Fatalf("zone set unbounded: %v", s.zoneList())
	}
}
