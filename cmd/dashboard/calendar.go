package main

import (
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"math"
	"net/http"
	"regexp"
	"strconv"
	"sync"
	"time"
)

// The capital calendar reads one month per request (?month=YYYY-MM), so any month back to the
// first NAV row can be shown without widening the cached snapshot. Each month costs ~32 bounded
// NAV lookups in a collector run; results are cached per zone and month.
var monthParam = regexp.MustCompile(`^(\d{4})-(0[1-9]|1[0-2])$`)

const (
	monthCacheMax   = 48
	monthPastTTL    = time.Hour  // a closed month only changes if the journal is rewritten
	monthCurrentTTL = slowPeriod // the current month moves with the slow panels
	monthDeadline   = 20 * time.Second
	minMonthYear    = 2020
)

type monthEntry struct {
	at   time.Time
	ttl  time.Duration
	data object
}

// SOL/USD for the calendar's USD view: one keyless server-side request, cached, fail-soft.
// The browser never calls a third party (CSP default-src 'self').
const (
	solMint      = "So11111111111111111111111111111111111111112"
	priceURL     = "https://lite-api.jup.ag/price/v3?ids=" + solMint
	priceTTL     = 5 * time.Minute
	priceFailTTL = time.Minute
	priceTimeout = 5 * time.Second
)

type priceState struct {
	mu     sync.Mutex
	usd    float64 // 0 = no good price
	at     time.Time
	failAt time.Time
	err    string
}

func (s *server) clock() time.Time {
	if s.now != nil {
		return s.now()
	}
	return time.Now()
}

// parseMonth returns the requested month ("" = the current month in loc) or an error for
// malformed input and months outside [minMonthYear-01, current month].
func parseMonth(query string, now time.Time, loc *time.Location) (string, error) {
	current := now.In(loc).Format("2006-01")
	if query == "" {
		return current, nil
	}
	m := monthParam.FindStringSubmatch(query)
	if m == nil {
		return "", errors.New("invalid month: use YYYY-MM")
	}
	if y, _ := strconv.Atoi(m[1]); y < minMonthYear || query > current {
		return "", fmt.Errorf("month out of range: %d-01 to %s", minMonthYear, current)
	}
	return query, nil
}

func (s *server) serveMonth(w http.ResponseWriter, r *http.Request) {
	tz, fallback := requestZone(r.URL.Query().Get("tz"))
	loc, err := time.LoadLocation(tz)
	if err != nil {
		tz, fallback, loc = "UTC", true, time.UTC
	}
	now := s.clock()
	month, err := parseMonth(r.URL.Query().Get("month"), now, loc)
	if err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}
	entry, ok := s.cachedMonth(tz+"|"+month, now)
	if !ok {
		// One collector run at a time: a burst of month clicks must not fan out into processes.
		s.monthRun.Lock()
		if entry, ok = s.cachedMonth(tz+"|"+month, now); !ok {
			ctx, cancel := context.WithTimeout(r.Context(), monthDeadline)
			data, cerr := s.collect(ctx, "month "+month, []string{tz})
			cancel()
			if cerr == nil && data["north_star"] != nil {
				ttl := monthPastTTL
				if month == now.In(loc).Format("2006-01") {
					ttl = monthCurrentTTL
				}
				entry, ok = monthEntry{at: now, ttl: ttl, data: data}, true
				s.storeMonth(tz+"|"+month, entry)
			}
		}
		s.monthRun.Unlock()
	}
	if !ok {
		http.Error(w, "Month could not be collected", http.StatusServiceUnavailable)
		return
	}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(object{"north_star": entry.data["north_star"], "collected_at": entry.data["collected_at"], "month": month, "tz": tz, "tz_fallback": fallback})
}

func (s *server) cachedMonth(key string, now time.Time) (monthEntry, bool) {
	s.monthMu.Lock()
	defer s.monthMu.Unlock()
	e, ok := s.months[key]
	if !ok || now.Sub(e.at) >= e.ttl {
		return monthEntry{}, false
	}
	return e, true
}

func (s *server) storeMonth(key string, e monthEntry) {
	s.monthMu.Lock()
	defer s.monthMu.Unlock()
	if s.months == nil {
		s.months = map[string]monthEntry{}
	}
	s.months[key] = e
	for len(s.months) > monthCacheMax {
		oldest := ""
		for k, v := range s.months {
			if oldest == "" || v.at.Before(s.months[oldest].at) {
				oldest = k
			}
		}
		delete(s.months, oldest)
	}
}

// servePrice answers 200 in every case: {"usd": n, "status": "ok"} or {"usd": null,
// "status": "unavailable"}. The calendar disables its USD view on the latter.
func (s *server) servePrice(w http.ResponseWriter, r *http.Request) {
	now := s.clock()
	p := &s.price
	p.mu.Lock()
	fresh := p.usd > 0 && now.Sub(p.at) < priceTTL
	if !fresh && (p.failAt.IsZero() || now.Sub(p.failAt) >= priceFailTTL) {
		fetch := s.fetchPrice
		if fetch == nil {
			fetch = fetchSOLPrice
		}
		ctx, cancel := context.WithTimeout(r.Context(), priceTimeout)
		usd, err := fetch(ctx)
		cancel()
		if err == nil && usd > 0 && !math.IsInf(usd, 0) {
			p.usd, p.at, p.err = usd, now, ""
			fresh = true
		} else {
			p.failAt, p.err = now, "SOL/USD price unavailable"
		}
	}
	value := object{"usd": nil, "status": "unavailable", "error": p.err, "source": "jupiter", "basis": "Current SOL/USD, applied to every day: not a historical price."}
	if fresh {
		value["usd"], value["status"], value["fetched_at"], value["error"] = p.usd, "ok", p.at.Unix(), ""
	}
	p.mu.Unlock()
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(value)
}

// fetchSOLPrice reads Jupiter's keyless price endpoint with a generic User-Agent.
func fetchSOLPrice(ctx context.Context) (float64, error) {
	req, err := http.NewRequestWithContext(ctx, "GET", priceURL, nil)
	if err != nil {
		return 0, err
	}
	req.Header.Set("User-Agent", "azimuth-dashboard")
	req.Header.Set("Accept", "application/json")
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return 0, err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return 0, fmt.Errorf("price status %d", resp.StatusCode)
	}
	return parseSOLPrice(io.LimitReader(resp.Body, 64*1024))
}

func parseSOLPrice(body io.Reader) (float64, error) {
	var payload map[string]struct {
		USDPrice float64 `json:"usdPrice"`
	}
	if err := json.NewDecoder(body).Decode(&payload); err != nil {
		return 0, err
	}
	usd := payload[solMint].USDPrice
	if !(usd > 0) || math.IsInf(usd, 0) {
		return 0, errors.New("no SOL price in response")
	}
	return usd, nil
}
