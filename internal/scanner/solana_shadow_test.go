package scanner

import (
	"encoding/json"
	"github.com/pgen0x/azimuth/internal/meteora"
	"os"
	"path/filepath"
	"testing"
)

func TestRejectedCandidateEvidence(t *testing.T) {
	file := filepath.Join(t.TempDir(), "rejects.jsonl")
	t.Setenv("SOLANA_SHADOW_PATH", file)
	p := meteora.Pool{PoolAddress: "pool", PoolPrice: 0.12, ActiveTVL: 5000}
	recordSolanaReject("turnover", p, &meteora.Candidate{BaseMint: "mint"}, "momentum", "5m below floor", map[string]float64{"m5": -9})
	data, err := os.ReadFile(file)
	if err != nil {
		t.Fatal(err)
	}
	var row map[string]any
	if err = json.Unmarshal(data, &row); err != nil {
		t.Fatal(err)
	}
	if row["gate"] != "momentum" || row["reason"] != "5m below floor" || row["id"] == "" || row["snapshot"].(map[string]any)["pool_price"] != 0.12 {
		t.Fatalf("lost rejection evidence: %s", data)
	}
}
