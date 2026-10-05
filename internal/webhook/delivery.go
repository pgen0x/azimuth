package webhook

import (
	"encoding/json"
	"log"
	"os"
	"path/filepath"
	"time"
)

// Local delivery evidence contains the public signal, never URL/HMAC/credentials.
// It is not a replay queue: an accepted or uncertain turn retains its dedup lock.
func recordDelivery(row map[string]any) error {
	file := os.Getenv("SOLANA_DELIVERY_PATH")
	if file == "" {
		home, err := os.UserHomeDir()
		if err != nil {
			return err
		}
		file = filepath.Join(home, ".local/state/azimuth/solana_deliveries.jsonl")
	}
	row["observed_at"] = time.Now().Unix()
	data, err := json.Marshal(row)
	if err != nil {
		return err
	}
	if err = os.MkdirAll(filepath.Dir(file), 0700); err != nil {
		return err
	}
	f, err := os.OpenFile(file, os.O_APPEND|os.O_CREATE|os.O_WRONLY, 0600)
	if err != nil {
		return err
	}
	defer f.Close()
	if _, err = f.Write(append(data, '\n')); err != nil {
		return err
	}
	return f.Sync()
}

func logDeliveryResult(id, stage string, status int) {
	if err := recordDelivery(map[string]any{"delivery_id": id, "stage": stage, "http_status": status}); err != nil {
		log.Printf("webhook: delivery %s outcome persistence failed; reconciliation required", id)
	}
	log.Printf("webhook: delivery_id=%s stage=%s http_status=%d", id, stage, status)
}
