package scanner

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"log"
	"os"
	"path/filepath"
	"time"

	"github.com/pgen0x/azimuth/internal/meteora"
)

// A stable five-minute cohort ID bounds repeated rejects without hiding gates.
// The outcome reader deduplicates IDs, including across process restarts.
func recordSolanaReject(mode string, pool meteora.Pool, candidate *meteora.Candidate, gate, reason string, evidence any) {
	file := os.Getenv("SOLANA_SHADOW_PATH")
	if file == "" {
		home, err := os.UserHomeDir()
		if err != nil {
			return
		}
		file = filepath.Join(home, ".local/state/azimuth/solana_rejects.jsonl")
	}
	now := time.Now().Unix()
	key, _ := json.Marshal([]any{mode, pool.PoolAddress, gate, now / 300})
	digest := sha256.Sum256(key)
	row := map[string]any{"id": hex.EncodeToString(digest[:]), "ts": now, "mode": mode, "pool": pool.PoolAddress, "gate": gate, "reason": reason, "snapshot": pool, "candidate": candidate, "evidence": evidence}
	data, err := json.Marshal(row)
	if err != nil {
		log.Printf("shadow: encode reject: %v", err)
		return
	}
	if err = os.MkdirAll(filepath.Dir(file), 0700); err != nil {
		log.Printf("shadow: mkdir: %v", err)
		return
	}
	f, err := os.OpenFile(file, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0600)
	if err != nil {
		log.Printf("shadow: open: %v", err)
		return
	}
	defer f.Close()
	if _, err = f.Write(append(data, '\n')); err != nil {
		log.Printf("shadow: write: %v", err)
	}
}
