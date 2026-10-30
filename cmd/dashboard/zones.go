package main

import (
	"context"
	"encoding/json"
	"os/exec"
	"regexp"
	"strconv"
	"time"
	_ "time/tzdata" // zone validation must not depend on the host's zoneinfo
)

// Daily series are bucketed by the viewer's IANA zone (?tz=), never a hard-coded one.
// Every timestamp in the API stays a UTC epoch; only day keys depend on the zone.
const maxZones = 6

var zoneName = regexp.MustCompile(`^[A-Za-z][A-Za-z0-9_+-]*(/[A-Za-z0-9_+-]+){0,2}$`)

// validZone returns the canonical zone name, or "" when the value is not a usable IANA zone.
func validZone(tz string) string {
	if tz == "UTC" {
		return tz
	}
	if len(tz) > 64 || !zoneName.MatchString(tz) || tz == "Local" {
		return ""
	}
	loc, err := time.LoadLocation(tz)
	if err != nil {
		return ""
	}
	return loc.String()
}

// requestZone reads ?tz=; missing means UTC, invalid means UTC plus a visible fallback flag.
func requestZone(query string) (tz string, fallback bool) {
	if query == "" {
		return "UTC", false
	}
	if tz = validZone(query); tz == "" {
		return "UTC", true
	}
	return tz, false
}

// zoneList is the set the background refresh recomputes: UTC plus recently requested zones.
func (s *server) zoneList() []string {
	s.mu.RLock()
	defer s.mu.RUnlock()
	return append([]string{"UTC"}, s.zones...)
}

// useZone marks a zone as recently used, evicting the least recent beyond maxZones.
func (s *server) useZone(tz string) {
	if tz == "UTC" {
		return
	}
	s.mu.Lock()
	defer s.mu.Unlock()
	kept := []string{}
	for _, z := range s.zones {
		if z != tz {
			kept = append(kept, z)
		}
	}
	kept = append(kept, tz)
	if len(kept) > maxZones-1 {
		kept = kept[len(kept)-(maxZones-1):]
	}
	s.zones = kept
}

// daily returns the day-bucketed panels for tz, computing them once on first use.
func (s *server) daily(data object, tz string) (object, string) {
	if panels := zonePanels(data, tz); panels != nil {
		s.useZone(tz)
		return panels, ""
	}
	if s.profile == "" {
		return nil, "No day-bucketed evidence for this time zone"
	}
	s.zoneMu.Lock()
	defer s.zoneMu.Unlock()
	s.mu.RLock()
	current := s.data
	s.mu.RUnlock()
	if panels := zonePanels(current, tz); panels != nil {
		s.useZone(tz)
		return panels, ""
	}
	ctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
	defer cancel()
	output, err := exec.CommandContext(ctx, "python3", "-c", collector, s.profile, s.state, strconv.FormatInt(s.since, 10), tz, "daily").Output()
	var fresh object
	if err == nil {
		err = json.Unmarshal(output, &fresh)
	}
	panels := zonePanels(fresh, tz)
	if err != nil || panels == nil {
		return nil, "Day buckets for this time zone could not be computed"
	}
	s.useZone(tz)
	s.mu.Lock()
	if s.data != nil {
		// Copy-on-write: readers may hold the previous snapshot.
		next := make(object, len(s.data))
		for k, v := range s.data {
			next[k] = v
		}
		byTZ := object{}
		if old, ok := s.data["by_tz"].(map[string]any); ok {
			for k, v := range old {
				byTZ[k] = v
			}
		}
		byTZ[tz] = panels
		next["by_tz"] = byTZ
		s.data = next
	}
	s.mu.Unlock()
	return panels, ""
}

func zonePanels(data object, tz string) object {
	byTZ, _ := data["by_tz"].(map[string]any)
	panels, _ := byTZ[tz].(map[string]any)
	return panels
}

// logLines reads the Robinhood log length: default 200, at most 1000 (the collector keeps 1000).
func logLines(query string) (int, bool) {
	if query == "" {
		return 200, true
	}
	n, err := strconv.Atoi(query)
	return n, err == nil && n >= 1 && n <= 1000
}

// robinhoodView copies the cached snapshot section (never mutating it), trims the log to n lines
// and adds the closes bucketed in the viewer's zone.
func robinhoodView(data, panels object, n int) object {
	view := object{"closes": panels["robinhood"]}
	if section, ok := data["robinhood"].(map[string]any); ok {
		for k, v := range section {
			view[k] = v
		}
		if logs, ok := section["logs"].([]any); ok {
			total := len(logs)
			if n < total {
				logs = logs[:n]
			}
			view["logs"] = logs
			view["logs_retained"] = total
		}
	}
	view["log_limit"] = n
	return view
}
