//go:build linux

package setup

import (
	"fmt"
	"os"
	"strconv"
	"strings"
	"syscall"
)

const minDiskBytes = 1024 * 1024 * 1024
const minMemoryBytes = 512 * 1024 * 1024

func (d *doctor) resources() {
	var stat syscall.Statfs_t
	if err := syscall.Statfs(d.opts.RepoDir, &stat); err != nil {
		d.add("disk", Warn, "Cannot measure free disk space.", "Check filesystem availability.")
	} else {
		d.resource("disk", stat.Bavail*uint64(stat.Bsize), minDiskBytes, "Free at least 1 GiB on the repository filesystem.")
	}
	data, err := os.ReadFile("/proc/meminfo")
	if err != nil {
		d.add("memory", Warn, "MemAvailable is unavailable.", "Check available RAM; at least 512 MiB is recommended.")
		return
	}
	available, ok := memAvailable(string(data))
	if !ok {
		d.add("memory", Warn, "MemAvailable is unavailable.", "Use a Linux kernel exposing MemAvailable, or inspect available RAM manually.")
		return
	}
	d.resource("memory", available, minMemoryBytes, "Free at least 512 MiB of available memory.")
}

func memAvailable(data string) (uint64, bool) {
	for _, line := range strings.Split(data, "\n") {
		fields := strings.Fields(line)
		if len(fields) == 3 && fields[0] == "MemAvailable:" && fields[2] == "kB" {
			n, err := strconv.ParseUint(fields[1], 10, 64)
			return n * 1024, err == nil
		}
	}
	return 0, false
}

func (d *doctor) resource(name string, available, minimum uint64, hint string) {
	status := Pass
	if available < minimum {
		status = Warn
	} else {
		hint = ""
	}
	d.add(name, status, fmt.Sprintf("Available space %s the recommended threshold.", map[bool]string{true: "meets", false: "is below"}[available >= minimum]), hint)
}
