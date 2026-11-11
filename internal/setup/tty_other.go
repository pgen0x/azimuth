//go:build !linux && !darwin

package setup

import (
	"errors"
	"os"
)

func isTerminal(*os.File) bool { return false }

func readNoEcho(*os.File) ([]byte, error) {
	return nil, errors.New("hidden secret entry is not supported on this platform; use the --*-file flags")
}
