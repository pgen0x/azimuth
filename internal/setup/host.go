package setup

import (
	"context"
	"debug/elf"
	"debug/macho"
	"debug/pe"
	"fmt"
	"os"
	"os/user"
	"path/filepath"
	"runtime"
	"strings"
)

func (d *doctor) services(ctx context.Context) {
	units := []struct {
		name    string
		running bool
	}{{"azimuth.service", true}, {"azimuth-sol-monitor.service", true}, {"azimuth-rh-monitor.service", false}}
	for _, optional := range []string{"azimuth-dashboard.service", "azimuth-alerts.timer", "azimuth-sol-markers.timer", "azimuth-sol-retention.timer", "azimuth-sol-rent.timer", "azimuth-sol-accounting.timer", "azimuth-sol-shadow.timer", "azimuth-sol-candidate-paper.timer", "azimuth-sol-net-experiment.timer", "azimuth-sol-price-path.timer"} {
		// Opt-in units are checked when installed; absence is expected.
		if _, err := os.Stat(filepath.Join(d.opts.HomeDir, ".config", "systemd", "user", optional)); err == nil {
			units = append(units, struct {
				name    string
				running bool
			}{optional, true})
		}
	}
	for _, u := range units {
		res, err := d.command(ctx, d.opts.Timeout, "systemctl", "--user", "show", u.name, "--property=LoadState", "--property=ActiveState", "--property=UnitFileState")
		state := map[string]string{}
		for _, line := range strings.Split(res.Output, "\n") {
			k, v, ok := strings.Cut(line, "=")
			if ok {
				state[k] = v
			}
		}
		if err != nil || res.Code != 0 || state["LoadState"] != "loaded" {
			d.add("unit."+u.name, Warn, "User unit is missing or the user service manager is unavailable.", "Install the user units with install.sh; use systemctl --user on a systemd host.")
			continue
		}
		if u.running && (state["ActiveState"] != "active" || state["UnitFileState"] != "enabled") {
			d.add("unit."+u.name, Warn, "User unit is installed but is not both active and enabled.", "Review configuration, then enable and start "+u.name+" when ready.")
			continue
		}
		d.add("unit."+u.name, Pass, "User unit matches its expected installation state.", "")
	}
	usr, err := user.Current()
	if err != nil {
		d.add("linger", Warn, "Cannot determine the local user.", "Check loginctl show-user for Linger=yes.")
		return
	}
	res, err := d.command(ctx, d.opts.Timeout, "loginctl", "show-user", usr.Uid, "--property=Linger", "--value")
	if err != nil || res.Code != 0 || strings.TrimSpace(res.Output) != "yes" {
		d.add("linger", Warn, "User linger is disabled or unavailable.", "Run loginctl enable-linger for the intended user to keep user services running after logout.")
	} else {
		d.add("linger", Pass, "User linger is enabled.", "")
	}
}

func (d *doctor) skill() {
	link := filepath.Join(d.opts.ProfileDir, "skills", "solana-dlmm", "scripts")
	info, err := os.Lstat(link)
	if err != nil || info.Mode()&os.ModeSymlink == 0 {
		d.add("profile.skill", Warn, "Profile scripts symlink is missing.", "Run install.sh with the intended profile path.")
		return
	}
	target, err := filepath.EvalSymlinks(link)
	want, wantErr := filepath.EvalSymlinks(filepath.Join(d.opts.RepoDir, "assets", "skill", "scripts"))
	if err != nil || wantErr != nil || target != want {
		d.add("profile.skill", Fail, "Profile scripts symlink does not point to this repository's scripts.", "Reinstall the skill from this checkout; copied directories will become stale.")
		return
	}
	d.add("profile.skill", Pass, "Profile scripts symlink points into this checkout.", "")
}

func (d *doctor) binaries() {
	type executable struct{ name, path string }
	paths := []executable{
		{"azimuth", filepath.Join(d.opts.RepoDir, "azimuth")},
		{"azimuth-dashboard", filepath.Join(d.opts.HomeDir, ".local", "bin", "azimuth-dashboard")},
	}
	for i, path := range d.opts.BinaryPaths {
		paths = append(paths, executable{fmt.Sprintf("extra.%d", i+1), path})
	}
	for _, name := range []string{"go", "python3", "node", "hermes"} {
		if p, err := d.opts.LookPath(name); err == nil {
			paths = append(paths, executable{name, p})
		}
	}
	if d.opts.HermesPython != "" {
		paths = append(paths, executable{"hermes-python", d.opts.HermesPython})
	}
	for _, exe := range paths {
		name, path := "binary."+exe.name, exe.path
		if _, err := os.Stat(path); err != nil {
			d.add(name, Warn, "Binary is not installed.", "Build or install the optional binary for this host.")
			continue
		}
		arches, osName, err := binaryArchitectures(path)
		if err != nil {
			d.add(name, Warn, "Cannot inspect executable architecture.", "Install a native executable or a script with a valid shebang.")
			continue
		}
		if osName == "script" {
			d.add(name, Pass, "Script uses an interpreter; interpreter binaries are checked separately.", "")
			continue
		}
		match := false
		for _, arch := range arches {
			if arch == runtime.GOARCH {
				match = true
			}
		}
		if !match || osName != runtime.GOOS {
			d.add(name, Fail, "Installed executable targets a different OS or architecture.", "Rebuild on this host or install a release matching its OS/architecture.")
			continue
		}
		d.add(name, Pass, "Executable architecture matches the host.", "")
	}
}

func binaryArchitectures(path string) ([]string, string, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, "", err
	}
	defer f.Close()
	var header [4]byte
	n, _ := f.ReadAt(header[:], 0)
	if n >= 2 && string(header[:2]) == "#!" {
		return nil, "script", nil
	}
	if e, err := elf.NewFile(f); err == nil {
		defer e.Close()
		arch := map[elf.Machine]string{elf.EM_X86_64: "amd64", elf.EM_386: "386", elf.EM_AARCH64: "arm64", elf.EM_ARM: "arm", elf.EM_RISCV: "riscv64", elf.EM_PPC64: "ppc64", elf.EM_S390: "s390x"}[e.Machine]
		if arch == "ppc64" && e.ByteOrder.String() == "LittleEndian" {
			arch = "ppc64le"
		}
		return []string{arch}, "linux", nil
	}
	if e, err := macho.NewFile(f); err == nil {
		defer e.Close()
		return []string{machoArch(e.Cpu)}, "darwin", nil
	}
	if e, err := macho.NewFatFile(f); err == nil {
		defer e.Close()
		var arches []string
		for _, a := range e.Arches {
			arches = append(arches, machoArch(a.Cpu))
		}
		return arches, "darwin", nil
	}
	if e, err := pe.NewFile(f); err == nil {
		defer e.Close()
		return []string{map[uint16]string{pe.IMAGE_FILE_MACHINE_AMD64: "amd64", pe.IMAGE_FILE_MACHINE_ARM64: "arm64", pe.IMAGE_FILE_MACHINE_I386: "386", pe.IMAGE_FILE_MACHINE_ARMNT: "arm"}[e.Machine]}, "windows", nil
	}
	return nil, "", fmt.Errorf("unsupported executable format")
}

func machoArch(cpu macho.Cpu) string {
	return map[macho.Cpu]string{macho.CpuAmd64: "amd64", macho.CpuArm64: "arm64", macho.Cpu386: "386", macho.CpuArm: "arm"}[cpu]
}
