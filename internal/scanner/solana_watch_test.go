package scanner

import (
	"github.com/pgen0x/azimuth/internal/meteora"
	"os"
	"path/filepath"
	"syscall"
	"testing"
)

func TestWatchBusyOrInvalidDoesNotWrite(t *testing.T) {
	path := filepath.Join(t.TempDir(), "watch.jsonl")
	t.Setenv("SOLANA_CANDIDATE_WATCH_PATH", path)
	c := &meteora.Candidate{Pool: "CqJVXBTY644ZBtPCkbaqV7Nu8Qzau2A4sChtpkvQQLLi", BaseMint: "EkFRff9a2jKztJHML1LG9FRmEkPJDR6XAYp3uCPdpump"}
	f, err := os.OpenFile(path, os.O_CREATE|os.O_WRONLY, 0600)
	if err != nil {
		t.Fatal(err)
	}
	defer f.Close()
	if err = syscall.Flock(int(f.Fd()), syscall.LOCK_EX|syscall.LOCK_NB); err != nil {
		t.Fatal(err)
	}
	recordSolanaWatch("pulse", []*meteora.Candidate{c})
	info, _ := f.Stat()
	if info.Size() != 0 {
		t.Fatal("wrote through lock")
	}
	syscall.Flock(int(f.Fd()), syscall.LOCK_UN)
	c.SolIsX = true
	recordSolanaWatch("pulse", []*meteora.Candidate{c, nil})
	info, _ = f.Stat()
	if info.Size() != 0 {
		t.Fatal("accepted unsupported geometry")
	}
	c.SolIsX = false
	t.Setenv("DRY_RUN", "true")
	recordSolanaWatch("pulse", []*meteora.Candidate{c})
	info, _ = f.Stat()
	if info.Size() != 0 {
		t.Fatal("recorded dry run")
	}
}
