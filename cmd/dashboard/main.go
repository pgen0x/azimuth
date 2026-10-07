// Dashboard serves cached local evidence and bounded, read-only Redis observations.
package main

import (
	"bufio"
	"context"
	_ "embed"
	"encoding/json"
	"flag"
	"fmt"
	"log"
	"net"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"sort"
	"strconv"
	"strings"
	"sync"
	"time"

	"github.com/redis/go-redis/v9"
)

//go:embed index.html
var page []byte

//go:embed collect.py
var collector string

type object = map[string]any

type server struct {
	mu             sync.RWMutex
	data           object
	failure        string
	profile, state string
	redis          *redis.Client
	dedup          string
}

var identifier = regexp.MustCompile(`^[A-Za-z0-9_.:-]{1,150}$`)

func (s *server) refresh() {
	ctx, cancel := context.WithTimeout(context.Background(), 20*time.Second)
	defer cancel()
	output, err := exec.CommandContext(ctx, "python3", "-c", collector, s.profile, s.state).Output()
	var data object
	if err == nil {
		err = json.Unmarshal(output, &data)
	}
	if err != nil {
		s.mu.Lock()
		s.failure = "Local collection failed; last successful snapshot retained"
		s.mu.Unlock()
		return
	}
	data["redis"] = s.redisSnapshot(ctx, data)
	s.mu.Lock()
	s.data = data
	s.failure = ""
	s.mu.Unlock()
}

func (s *server) redisSnapshot(ctx context.Context, data object) object {
	if s.redis == nil {
		return object{"status": "disabled", "observed_at": time.Now().Unix()}
	}
	ctx, cancel := context.WithTimeout(ctx, 3*time.Second)
	defer cancel()
	keys := map[string]bool{"sol:dlmm:capacity:wallet": true, "sol:dlmm:capacity:pulse": true, "sol:dlmm:capacity:turnover": true}
	// ponytail: bounded recent candidates; use an indexed collector for historical Redis coverage.
	rows, _ := data["journal"].([]any)
	for i, row := range rows {
		if i >= 100 {
			break
		}
		r, _ := row.(map[string]any)
		e, _ := r["evidence"].(map[string]any)
		for _, k := range []string{"pool", "base_mint", "base_symbol"} {
			v, _ := e[k].(string)
			if c, ok := e["candidate"].(map[string]any); ok && v == "" {
				v, _ = c[k].(string)
			}
			if !identifier.MatchString(v) {
				continue
			}
			switch k {
			case "pool":
				keys["sol:dlmm:cooldown:pool:"+v] = true
				for _, mode := range []string{"pulse", "turnover"} {
					keys[s.dedup+":"+mode+":"+v] = true
				}
			case "base_mint":
				keys["sol:dlmm:cooldown:mint:"+v] = true
			case "base_symbol":
				keys["sol:dlmm:cooldown:"+strings.ToUpper(v)] = true
			}
		}
	}
	count, err := s.redis.SCard(ctx, "sol:dlmm:active_positions").Result()
	if err != nil {
		return object{"status": "unavailable", "observed_at": time.Now().Unix()}
	}
	positions, _, err := s.redis.SScan(ctx, "sol:dlmm:active_positions", 0, "", 100).Result()
	if err != nil {
		return object{"status": "unavailable", "observed_at": time.Now().Unix()}
	}
	if len(positions) > 100 {
		positions = positions[:100]
	}
	for _, p := range positions {
		if identifier.MatchString(p) {
			keys["sol:dlmm:position:"+p] = true
		}
	}
	names := make([]string, 0, len(keys))
	for k := range keys {
		names = append(names, k)
	}
	sort.Strings(names)
	if len(names) > 400 {
		names = names[:400]
	}
	pipe := s.redis.Pipeline()
	ttls := make(map[string]*redis.DurationCmd)
	values := make(map[string]*redis.StringCmd)
	for _, k := range names {
		ttls[k] = pipe.TTL(ctx, k)
		values[k] = pipe.GetRange(ctx, k, 0, 8191)
	}
	_, err = pipe.Exec(ctx)
	result := make([]object, 0, len(names))
	for _, k := range names {
		row := object{"key": k, "ttl_seconds": nil, "value": nil}
		if ttl, e := ttls[k].Result(); e == nil {
			if ttl < 0 {
				row["ttl_seconds"] = int64(ttl)
			} else {
				row["ttl_seconds"] = ttl.Seconds()
			}
		}
		if raw, e := values[k].Result(); e == nil && raw != "" {
			if strings.HasPrefix(k, "sol:dlmm:position:") {
				var p object
				if json.Unmarshal([]byte(raw), &p) == nil {
					safe := object{}
					for _, f := range []string{"position", "pool", "mode", "base_mint", "base_symbol", "deposit_sol", "size_sol", "strategy", "deployed_at", "tx_hash", "orphan", "created_at", "updated_at", "root_chain_id", "entry_id"} {
						safe[f] = p[f]
					}
					row["value"] = safe
				}
			}
			// Capacity/cooldown/dedup values can contain arbitrary upstream errors; TTL suffices.
		}
		result = append(result, row)
	}
	status := "ok"
	if err != nil {
		status = "partial"
	}
	return object{"status": status, "observed_at": time.Now().Unix(), "active_position_count": count, "position_sample_count": len(positions), "rows": result, "scope": "Fixed capacity keys, one bounded active-position SSCAN, recent-candidate cooldown/dedup TTLs; missing key=-2, no expiry=-1. Not a full inventory."}
}

func (s *server) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	host, _, err := net.SplitHostPort(r.Host)
	if err != nil {
		host = r.Host
	}
	if host != "localhost" && net.ParseIP(host) != nil && !net.ParseIP(host).IsLoopback() || host != "localhost" && net.ParseIP(host) == nil {
		http.Error(w, "localhost only", http.StatusForbidden)
		return
	}
	w.Header().Set("Cache-Control", "no-store")
	w.Header().Set("X-Content-Type-Options", "nosniff")
	w.Header().Set("Content-Security-Policy", "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; frame-ancestors 'none'; base-uri 'none'")
	if r.Method != "GET" && r.Method != "HEAD" {
		w.Header().Set("Allow", "GET, HEAD")
		http.Error(w, "read only", 405)
		return
	}
	if r.URL.Path == "/" {
		w.Header().Set("Content-Type", "text/html; charset=utf-8")
		w.Write(page)
		return
	}
	s.mu.RLock()
	data := s.data
	failure := s.failure
	s.mu.RUnlock()
	if data == nil {
		http.Error(w, "Waiting for first local snapshot", 503)
		return
	}
	var value any
	switch r.URL.Path {
	case "/api/overview":
		value = object{"collected_at": data["collected_at"], "collection_error": failure, "nav": data["nav"], "services": data["services"], "sources": data["sources"]}
	case "/api/evaluation":
		value = object{"report": data["evaluation"], "source": data["evaluation_source"], "errors": data["report_errors"], "collected_at": data["collected_at"]}
	case "/api/hermes":
		value = data["hermes"]
	case "/api/redis":
		value = data["redis"]
	case "/api/journal":
		offset, err := strconv.Atoi(r.URL.Query().Get("offset"))
		if r.URL.Query().Get("offset") == "" {
			offset = 0
			err = nil
		}
		if err != nil || offset < 0 || offset > 100000 {
			http.Error(w, "invalid offset", 400)
			return
		}
		query := strings.ToLower(r.URL.Query().Get("q"))
		stage := r.URL.Query().Get("stage")
		if len(query) > 200 {
			http.Error(w, "query too long", 400)
			return
		}
		matched := []any{}
		rows, _ := data["journal"].([]any)
		for _, row := range rows {
			e, _ := row.(map[string]any)
			b, _ := json.Marshal(e)
			if (stage == "" || e["stage"] == stage) && (query == "" || strings.Contains(strings.ToLower(string(b)), query)) {
				matched = append(matched, row)
			}
		}
		total := len(matched)
		if offset > total {
			offset = total
		}
		end := offset + 50
		if end > total {
			end = total
		}
		value = object{"rows": matched[offset:end], "total_in_retained_tail": total, "offset": offset, "limit": 50, "collected_at": data["collected_at"], "scope": "Bounded source tails; correlations require shared delivery_id, entry_id, root_chain_id, position or signature. Pool/time similarity is not execution proof."}
	default:
		http.NotFound(w, r)
		return
	}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(value)
}

// Only these Redis settings are read; trading/model configuration is never loaded.
func redisSettings(path string) map[string]string {
	values := map[string]string{}
	f, err := os.Open(path)
	if err == nil {
		defer f.Close()
		scan := bufio.NewScanner(f)
		for scan.Scan() {
			line := strings.TrimSpace(strings.TrimPrefix(scan.Text(), "export "))
			key, value, ok := strings.Cut(line, "=")
			key = strings.TrimSpace(key)
			if ok && (key == "REDIS_ADDR" || key == "REDISCLI_AUTH" || key == "REDIS_SEEN_KEY") {
				values[key] = strings.Trim(strings.TrimSpace(value), "\"'")
			}
		}
	}
	for _, key := range []string{"REDIS_ADDR", "REDISCLI_AUTH", "REDIS_SEEN_KEY"} {
		if value, ok := os.LookupEnv(key); ok {
			values[key] = value
		}
	}
	return values
}

func main() {
	home, _ := os.UserHomeDir()
	addr := flag.String("listen", "127.0.0.1:8787", "loopback address")
	profile := flag.String("profile", filepath.Join(home, ".hermes/profiles/solanza"), "profile directory")
	state := flag.String("state", filepath.Join(home, ".local/state/azimuth"), "persisted state directory")
	redisAddr := flag.String("redis", "", "Redis address override; use disabled to disable")
	envFile := flag.String("env-file", ".env", "read only REDIS_ADDR, REDISCLI_AUTH and REDIS_SEEN_KEY")
	dedup := flag.String("dedup-prefix", "", "scanner REDIS_SEEN_KEY override")
	flag.Parse()
	host, _, err := net.SplitHostPort(*addr)
	if err != nil || net.ParseIP(host) == nil || !net.ParseIP(host).IsLoopback() {
		log.Fatal("listen must use a loopback IP")
	}
	settings := redisSettings(*envFile)
	if *redisAddr == "" {
		*redisAddr = settings["REDIS_ADDR"]
	}
	if *dedup == "" {
		*dedup = settings["REDIS_SEEN_KEY"]
	}
	if *dedup == "" {
		*dedup = "dlmm:signal:seen_pools"
	}
	s := &server{profile: *profile, state: *state, dedup: *dedup}
	if *redisAddr != "" && *redisAddr != "disabled" {
		s.redis = redis.NewClient(&redis.Options{Addr: *redisAddr, Password: settings["REDISCLI_AUTH"], MaxRetries: -1, DialTimeout: time.Second, ReadTimeout: time.Second})
		defer s.redis.Close()
	}
	s.refresh()
	go func() {
		for range time.Tick(30 * time.Second) {
			s.refresh()
		}
	}()
	fmt.Printf("Azimuth dashboard: http://%s (read only)\n", *addr)
	log.Fatal((&http.Server{Addr: *addr, Handler: s, ReadHeaderTimeout: 5 * time.Second, WriteTimeout: 10 * time.Second, IdleTimeout: 60 * time.Second}).ListenAndServe())
}
