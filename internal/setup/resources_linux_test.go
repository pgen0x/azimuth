//go:build linux

package setup

import "testing"

func TestMemAvailableAndResourceThresholds(t *testing.T) {
	n, ok := memAvailable("MemFree: 1 kB\nMemAvailable: 524288 kB\n")
	if !ok || n != minMemoryBytes {
		t.Fatal("must use MemAvailable rather than MemFree")
	}
	for _, data := range []string{"MemFree: 1024 kB", "MemAvailable: invalid kB", "MemAvailable: 1 MB"} {
		if _, ok := memAvailable(data); ok {
			t.Fatal("invalid memory value accepted")
		}
	}
	d := doctor{}
	d.resource("disk", minDiskBytes-1, minDiskBytes, "Free space.")
	d.resource("memory", minMemoryBytes, minMemoryBytes, "Free RAM.")
	if findCheck(t, d.report, "disk").Status != Warn || findCheck(t, d.report, "memory").Status != Pass {
		t.Fatal("threshold boundary mismatch")
	}
}
