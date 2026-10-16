package scanner

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"os"
	"path/filepath"
	"regexp"
	"syscall"
	"time"

	"github.com/pgen0x/azimuth/internal/meteora"
)

var watchAddress = regexp.MustCompile(`^[1-9A-HJ-NP-Za-km-z]{32,44}$`)

// Record discovery identities before routing. This is neither admission nor a
// rejection. Failure must not delay entry; collector RPC budgets stay unchanged.
func recordSolanaWatch(mode string, batch []*meteora.Candidate) {
	if os.Getenv("DRY_RUN") == "true" {
		return
	}
	switch mode {
	case "turnover", "pulse", "casual", "multiday":
	default:
		return
	}
	stamp := time.Now().Unix()
	seen := map[string]bool{}
	data := []byte{}
	for _, c := range batch {
		if c == nil || c.SolIsX || !watchAddress.MatchString(c.Pool) || !watchAddress.MatchString(c.BaseMint) || c.BaseMint == meteora.SolMint || seen[c.Pool] {
			continue
		}
		seen[c.Pool] = true
		key, _ := json.Marshal([]any{mode, c.Pool, stamp})
		digest := sha256.Sum256(key)
		row := map[string]any{"id": "watch:" + hex.EncodeToString(digest[:]), "ts": stamp, "pool": c.Pool, "mode": mode, "source": "scanner_before_routing", "candidate": map[string]any{"base_mint": c.BaseMint, "sol_is_x": false}}
		encoded, err := json.Marshal(row)
		if err != nil {
			continue
		}
		data = append(data, encoded...)
		data = append(data, '\n')
		if len(seen) >= 64 {
			break
		}
	}
	if len(data) == 0 {
		return
	}
	file := os.Getenv("SOLANA_CANDIDATE_WATCH_PATH")
	if file == "" {
		rejects := os.Getenv("SOLANA_SHADOW_PATH")
		if rejects == "" {
			home, err := os.UserHomeDir()
			if err != nil {
				return
			}
			rejects = filepath.Join(home, ".local/state/azimuth/solana_rejects.jsonl")
		}
		file = filepath.Join(filepath.Dir(rejects), "solana_candidate_watch.jsonl")
	}
	if os.MkdirAll(filepath.Dir(file), 0700) != nil {
		return
	}
	f, err := os.OpenFile(file, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0600)
	if err != nil {
		return
	}
	defer f.Close()
	if syscall.Flock(int(f.Fd()), syscall.LOCK_EX|syscall.LOCK_NB) != nil {
		return
	}
	defer syscall.Flock(int(f.Fd()), syscall.LOCK_UN)
	_, _ = f.Write(data)
}
