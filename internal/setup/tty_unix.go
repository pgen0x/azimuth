//go:build linux || darwin

package setup

import (
	"bufio"
	"bytes"
	"errors"
	"os"
	"os/signal"
	"syscall"
	"unsafe"
)

func getTermios(fd uintptr) (syscall.Termios, error) {
	var t syscall.Termios
	if _, _, errno := syscall.Syscall(syscall.SYS_IOCTL, fd, uintptr(ioctlGetTermios), uintptr(unsafe.Pointer(&t))); errno != 0 {
		return t, errno
	}
	return t, nil
}

func setTermios(fd uintptr, t *syscall.Termios) error {
	if _, _, errno := syscall.Syscall(syscall.SYS_IOCTL, fd, uintptr(ioctlSetTermios), uintptr(unsafe.Pointer(t))); errno != 0 {
		return errno
	}
	return nil
}

// isTerminal reports whether f is a terminal.
func isTerminal(f *os.File) bool {
	_, err := getTermios(f.Fd())
	return err == nil
}

// readNoEcho reads one line from a terminal with echo off. It refuses a
// non-terminal, because then nothing guarantees the secret is not echoed or
// captured; automation passes secrets by file instead. Echo is restored on
// return and on SIGINT/SIGTERM.
func readNoEcho(f *os.File) ([]byte, error) {
	fd := f.Fd()
	old, err := getTermios(fd)
	if err != nil {
		return nil, errors.New("secret entry needs an interactive terminal; use the --*-file flags for automation")
	}
	quiet := old
	quiet.Lflag &^= syscall.ECHO
	quiet.Lflag |= syscall.ICANON | syscall.ISIG
	if err := setTermios(fd, &quiet); err != nil {
		return nil, errors.New("cannot disable terminal echo")
	}
	sigs := make(chan os.Signal, 1)
	done := make(chan struct{})
	signal.Notify(sigs, os.Interrupt, syscall.SIGTERM)
	go func() {
		select {
		case <-sigs:
			setTermios(fd, &old)
			os.Exit(130)
		case <-done:
		}
	}()
	defer func() {
		close(done)
		signal.Stop(sigs)
		setTermios(fd, &old)
	}()
	line, err := bufio.NewReaderSize(f, 4096).ReadSlice('\n')
	out := append([]byte(nil), bytes.TrimRight(line, "\r\n")...)
	clear(line)
	if err != nil && len(out) == 0 {
		return nil, errors.New("no secret entered")
	}
	return out, nil
}
