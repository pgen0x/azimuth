package webhook

import (
	"crypto/hmac"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"io"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestDeliveryEvidence(t *testing.T) {
	for _, tc := range []struct {
		name, receipt, stage string
		status               int
	}{
		{"accepted", "accepted", "accepted", 202},
		{"duplicate", "duplicate", "accepted", 200},
		{"bad_receipt", "wrong-id", "http_unconfirmed", 202},
		{"rejected", "error", "http_rejected", 503},
	} {
		t.Run(tc.name, func(t *testing.T) {
			file := filepath.Join(t.TempDir(), "delivery.jsonl")
			t.Setenv("SOLANA_DELIVERY_PATH", file)
			calls := 0
			server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				calls++
				body, _ := io.ReadAll(r.Body)
				mac := hmac.New(sha256.New, []byte("secret"))
				mac.Write(body)
				if r.Header.Get("X-Webhook-Signature") != hex.EncodeToString(mac.Sum(nil)) {
					t.Error("HMAC changed")
				}
				id := r.Header.Get("X-Request-ID")
				if len(id) != 32 {
					t.Error("missing delivery ID")
				}
				prepared, err := os.ReadFile(file)
				if err != nil || !strings.Contains(string(prepared), id) {
					t.Error("request sent before persistence")
				}
				if tc.receipt == "wrong-id" {
					id = "other"
				}
				w.WriteHeader(tc.status)
				json.NewEncoder(w).Encode(map[string]string{"status": tc.receipt, "delivery_id": id})
			}))
			defer server.Close()
			err := New(server.URL, "secret").Send("meteora_pool_discovery", []map[string]string{{"pool": "P", "mode": "pulse"}}, 100)
			if (err != nil) != (tc.status >= 400) {
				t.Fatal("unexpected delivery result", err)
			}
			data, _ := os.ReadFile(file)
			lines := strings.Split(strings.TrimSpace(string(data)), "\n")
			if calls != 1 || len(lines) != 2 {
				t.Fatal("automatic resend or missing evidence", calls, len(lines))
			}
			var a, b map[string]any
			json.Unmarshal([]byte(lines[0]), &a)
			json.Unmarshal([]byte(lines[1]), &b)
			if a["stage"] != "prepared" || b["stage"] != tc.stage || a["delivery_id"] != b["delivery_id"] {
				t.Fatal(a, b)
			}
			if strings.Contains(string(data), "secret") || strings.Contains(string(data), server.URL) {
				t.Fatal("credentials/endpoint persisted")
			}
		})
	}
	// Fail before sending if no durable evidence can be written.
	t.Setenv("SOLANA_DELIVERY_PATH", t.TempDir())
	if err := New("http://127.0.0.1:1", "secret").Send("meteora_pool_discovery", nil, 100); err == nil || !strings.Contains(err.Error(), "persist webhook") {
		t.Fatal(err)
	}
}

type failedDeliveryTransport struct{ calls int }

func (f *failedDeliveryTransport) RoundTrip(r *http.Request) (*http.Response, error) {
	f.calls++
	return nil, errors.New("simulated connection failure")
}
func TestTransportFailureRetainsDeliveryEvidence(t *testing.T) {
	file := filepath.Join(t.TempDir(), "delivery.jsonl")
	t.Setenv("SOLANA_DELIVERY_PATH", file)
	transport := &failedDeliveryTransport{}
	forwarder := New("http://unused.test", "secret")
	forwarder.client.Transport = transport
	if err := forwarder.Send("meteora_pool_discovery", nil, 100); err == nil {
		t.Fatal("expected transport error")
	}
	data, _ := os.ReadFile(file)
	if transport.calls != 1 || !strings.Contains(string(data), "transport_unconfirmed") {
		t.Fatal("transport retried or uncertainty lost")
	}
}

func TestCompleteCandidatePayload(t *testing.T) {
	t.Setenv("SOLANA_DELIVERY_PATH", filepath.Join(t.TempDir(), "delivery.jsonl"))
	payload := []map[string]string{{"pool": "first", "data": strings.Repeat("x", 5000)}, {"pool": "last", "data": "complete"}}
	want, _ := json.Marshal(payload)
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		var sig Signal
		if err := json.NewDecoder(r.Body).Decode(&sig); err != nil {
			t.Fatal(err)
		}
		if sig.PayloadJSON != string(want) {
			t.Error("candidate JSON missing or truncated")
		}
		original, _ := json.Marshal(sig.Payload)
		if string(original) != sig.PayloadJSON {
			t.Error("structured and prompt candidates differ")
		}
		w.WriteHeader(202)
		json.NewEncoder(w).Encode(map[string]string{"status": "accepted", "delivery_id": r.Header.Get("X-Request-ID")})
	}))
	defer server.Close()
	if err := New(server.URL, "secret").Send("meteora_pool_discovery", payload, 100); err != nil {
		t.Fatal(err)
	}
}
