package setup

import (
	"bufio"
	"context"
	"fmt"
	"io"
	"net"
	"strconv"
	"strings"
	"testing"
	"time"
)

// The fixture rejects every Redis command except handshake, auth and PING.
func redisFixture(t *testing.T) (string, <-chan []string) {
	t.Helper()
	ln, err := net.Listen("tcp", "127.0.0.1:0")
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { ln.Close() })
	done := make(chan []string, 1)
	go func() {
		conn, err := ln.Accept()
		if err != nil {
			done <- nil
			return
		}
		defer conn.Close()
		conn.SetDeadline(time.Now().Add(2 * time.Second))
		r := bufio.NewReader(conn)
		var commands []string
		authenticated := false
		defer func() { done <- commands }()
		for {
			line, err := r.ReadString('\n')
			if err != nil {
				return
			}
			n, err := strconv.Atoi(strings.TrimSpace(strings.TrimPrefix(line, "*")))
			if err != nil || n < 1 || n > 10 {
				return
			}
			args := make([]string, n)
			for i := range args {
				header, e := r.ReadString('\n')
				if e != nil {
					return
				}
				size, e := strconv.Atoi(strings.TrimSpace(strings.TrimPrefix(header, "$")))
				if e != nil || size < 0 || size > 4096 {
					return
				}
				buf := make([]byte, size+2)
				if _, e = io.ReadFull(r, buf); e != nil {
					return
				}
				args[i] = string(buf[:size])
			}
			name := strings.ToLower(args[0])
			commands = append(commands, name)
			switch name {
			case "hello":
				fmt.Fprint(conn, "-ERR unknown command 'hello'\r\n")
			case "auth":
				if len(args) == 2 && args[1] == "test-only-redis-password" {
					authenticated = true
					fmt.Fprint(conn, "+OK\r\n")
				} else {
					fmt.Fprint(conn, "-WRONGPASS invalid credentials\r\n")
				}
			case "ping":
				if authenticated {
					fmt.Fprint(conn, "+PONG\r\n")
				} else {
					fmt.Fprint(conn, "-NOAUTH Authentication required\r\n")
				}
			default:
				t.Errorf("unexpected Redis command: %s", name)
				fmt.Fprint(conn, "-ERR read-only fixture\r\n")
			}
		}
	}()
	return ln.Addr().String(), done
}

func TestRedisAuthenticatedReadOnlyPing(t *testing.T) {
	for _, password := range []string{"test-only-redis-password", "wrong-test-password", ""} {
		addr, done := redisFixture(t)
		d := doctor{opts: DoctorOptions{Timeout: time.Second}, values: map[string]string{"REDIS_ADDR": addr, "REDISCLI_AUTH": password}}
		d.redis(context.Background())
		want := Fail
		if password == "test-only-redis-password" {
			want = Pass
		}
		if findCheck(t, d.report, "redis").Status != want {
			t.Fatal("Redis auth result mismatch")
		}
		commands := <-done
		if len(commands) == 0 {
			t.Fatal("Redis was not contacted")
		}
		if password == "test-only-redis-password" && commands[len(commands)-1] != "ping" {
			t.Fatal("successful auth did not PING")
		}
	}
}
