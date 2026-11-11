//go:build !linux

package setup

func (d *doctor) resources() {
	d.add("disk", Warn, "Disk check is supported on Linux.", "Check at least 1 GiB free on the repository filesystem.")
	d.add("memory", Warn, "MemAvailable check is supported on Linux.", "Check at least 512 MiB available memory.")
}
