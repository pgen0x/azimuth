// Command azimuth is a standalone daemon that continuously watches
// the Meteora pool-discovery API, screens pools with the same gates the DLMM
// pipeline skill uses, and forwards each newly-qualifying pool to a Hermes agent
// webhook. The agent then reviews the signal and decides whether to open a
// concentrated-liquidity position.
package main

import (
	"context"
	"flag"
	"fmt"
	"log"
	"os"
	"os/signal"
	"syscall"

	"github.com/pgen0x/azimuth/internal/config"
	"github.com/pgen0x/azimuth/internal/scanner"
)

// Version follows Semantic Versioning (semver.org). Bumped automatically by
// release-please from conventional commits — see CONTRIBUTING.md. Release
// builds also override it via -ldflags "-X main.Version=..." (GoReleaser).
var Version = "2.6.1" // x-release-please-version

func main() {
	showVersion := flag.Bool("version", false, "print version and exit")
	flag.Parse()
	if *showVersion {
		fmt.Println("azimuth " + Version)
		return
	}

	log.SetFlags(log.LstdFlags | log.LUTC)
	log.Printf("azimuth %s starting", Version)
	cfg := config.Load()

	ctx, cancel := context.WithCancel(context.Background())
	defer cancel()

	go func() {
		ch := make(chan os.Signal, 1)
		signal.Notify(ch, syscall.SIGINT, syscall.SIGTERM)
		<-ch
		log.Println("shutdown signal received")
		cancel()
	}()

	scanner.New(cfg).Run(ctx)
}
