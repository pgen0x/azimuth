package setup

import (
	"context"
	"flag"
	"fmt"
	"io"
	"time"
)

// RunDoctorCLI owns only argument parsing and rendering; diagnostics live in Doctor.
func RunDoctorCLI(ctx context.Context, args []string, out, errOut io.Writer) int {
	return runDoctorCLI(ctx, args, out, errOut, Doctor)
}

func runDoctorCLI(ctx context.Context, args []string, out, errOut io.Writer, diagnose func(context.Context, DoctorOptions) Report) int {
	flags := flag.NewFlagSet("azimuth doctor", flag.ContinueOnError)
	flags.SetOutput(io.Discard)
	var opts DoctorOptions
	asJSON := flags.Bool("json", false, "emit a JSON report")
	flags.StringVar(&opts.RepoDir, "repo", ".", "repository root")
	flags.StringVar(&opts.EnvFile, "env-file", "", "literal dotenv file (default: <repo>/.env)")
	flags.StringVar(&opts.ProfileDir, "profile", "", "profile to inspect (default: ~/.hermes/profiles/dlmm; no profile secrets are read)")
	flags.StringVar(&opts.HermesRoot, "hermes-root", "", "Hermes source checkout containing its bundled venv")
	flags.StringVar(&opts.HermesPython, "hermes-python", "", "Hermes bundled Python executable")
	flags.DurationVar(&opts.Timeout, "timeout", 5*time.Second, "timeout per command or network check (AI probe uses 65s)")
	if err := flags.Parse(args); err != nil {
		if err == flag.ErrHelp {
			fmt.Fprintln(out, "Usage: azimuth doctor [--json] [--repo DIR] [--env-file FILE] [--profile DIR]")
			flags.SetOutput(out)
			flags.PrintDefaults()
			fmt.Fprintln(out, "Exit codes: 0 all PASS; 1 any FAIL; 2 WARN without FAIL. Read-only; no transactions or service changes.")
			return 0
		}
		fmt.Fprintln(errOut, "Invalid doctor arguments. Use azimuth doctor --help.")
		return 1
	}
	if flags.NArg() != 0 || opts.Timeout <= 0 {
		fmt.Fprintln(errOut, "Doctor requires flag arguments and a positive timeout.")
		return 1
	}
	report := diagnose(ctx, opts)
	if err := report.Write(out, *asJSON); err != nil {
		fmt.Fprintln(errOut, "Cannot write doctor report.")
		return 1
	}
	return report.ExitCode()
}
