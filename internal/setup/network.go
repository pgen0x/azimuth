package setup

import (
	"bytes"
	"context"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strconv"
	"strings"
	"time"

	redis "github.com/redis/go-redis/v9"
)

type HTTPDoer interface {
	Do(*http.Request) (*http.Response, error)
}

func (d *doctor) redis(ctx context.Context) {
	addr := d.values["REDIS_ADDR"]
	if addr == "" {
		d.add("redis", Warn, "Redis is not configured; dedup is in memory.", "Set REDIS_ADDR for persistent dedup, or keep it empty for a single instance.")
		return
	}
	if (Variable{Name: "REDIS_ADDR", Kind: "hostport"}).Validate(addr) != nil {
		d.add("redis", Fail, "Redis address is invalid.", "Use host:port for REDIS_ADDR.")
		return
	}
	ctx, cancel := context.WithTimeout(ctx, d.opts.Timeout)
	defer cancel()
	rdb := redis.NewClient(&redis.Options{Addr: addr, Password: d.values["REDISCLI_AUTH"], DialTimeout: d.opts.Timeout, ReadTimeout: d.opts.Timeout, WriteTimeout: d.opts.Timeout, MaxRetries: -1, ContextTimeoutEnabled: true, DisableIndentity: true})
	defer rdb.Close()
	if err := rdb.Ping(ctx).Err(); err != nil {
		d.add("redis", Fail, "Redis PING or authentication failed.", "Check reachability and REDISCLI_AUTH; no data keys were read or written.")
		return
	}
	d.add("redis", Pass, "Redis authenticated PING succeeded.", "")
}

func (d *doctor) rpcCall(ctx context.Context, endpoint, method string, params any, target any) error {
	body, err := json.Marshal(map[string]any{"jsonrpc": "2.0", "id": 1, "method": method, "params": params})
	if err != nil {
		return fmt.Errorf("cannot build RPC request")
	}
	ctx, cancel := context.WithTimeout(ctx, d.opts.Timeout)
	defer cancel()
	req, err := http.NewRequestWithContext(ctx, http.MethodPost, endpoint, bytes.NewReader(body))
	if err != nil {
		return fmt.Errorf("invalid RPC endpoint")
	}
	req.Header.Set("Content-Type", "application/json")
	client := d.opts.HTTPClient
	if client == nil {
		client = &http.Client{Timeout: d.opts.Timeout, CheckRedirect: func(*http.Request, []*http.Request) error { return http.ErrUseLastResponse }}
	}
	res, err := client.Do(req)
	if err != nil {
		return fmt.Errorf("RPC transport failed")
	}
	defer res.Body.Close()
	if res.StatusCode != http.StatusOK {
		return fmt.Errorf("RPC HTTP status failed")
	}
	var envelope struct {
		Result json.RawMessage `json:"result"`
		Error  json.RawMessage `json:"error"`
		ID     int             `json:"id"`
	}
	if json.NewDecoder(io.LimitReader(res.Body, 1024*1024)).Decode(&envelope) != nil || envelope.ID != 1 || len(envelope.Result) == 0 || string(envelope.Result) == "null" || (len(envelope.Error) > 0 && string(envelope.Error) != "null") {
		return fmt.Errorf("RPC response failed")
	}
	if json.Unmarshal(envelope.Result, target) != nil {
		return fmt.Errorf("RPC result failed")
	}
	return nil
}

func (d *doctor) rpc(ctx context.Context) {
	endpoints := d.values["SOLANA_RPC_URLS"]
	if endpoints == "" {
		d.add("rpc", Warn, "No Solana RPC endpoint is configured in the selected file.", "Set SOLANA_RPC_URLS here; doctor does not read a profile .env.")
		d.walletSkipped()
		return
	}
	if (Variable{Name: "SOLANA_RPC_URLS", Kind: "urls"}).Validate(endpoints) != nil {
		d.add("rpc", Fail, "RPC endpoint list is invalid.", "Set SOLANA_RPC_URLS to comma-separated HTTP(S) URLs.")
		d.walletSkipped()
		return
	}
	var selected string
	for index, endpoint := range strings.Split(endpoints, ",") {
		endpoint = strings.TrimSpace(endpoint)
		start := time.Now()
		var health string
		if d.rpcCall(ctx, endpoint, "getHealth", []any{}, &health) != nil || health != "ok" {
			d.add("rpc."+strconv.Itoa(index+1), Fail, "RPC health request failed.", "Check endpoint availability, authentication and rate limits.")
			continue
		}
		d.add("rpc."+strconv.Itoa(index+1), Pass, fmt.Sprintf("Read-only health request completed in %d ms.", time.Since(start).Milliseconds()), "")
		if selected == "" {
			selected = endpoint
		}
	}
	pubkey := d.values["SOLANA_PUBLIC_KEY"]
	if selected == "" || pubkey == "" {
		d.walletSkipped()
		return
	}
	if !validPubkey(pubkey) {
		d.add("wallet.balance", Fail, "Public key format is invalid.", "Set a base58 Solana public key; no private key is needed.")
		return
	}
	var balance struct {
		Value *uint64 `json:"value"`
	}
	if d.rpcCall(ctx, selected, "getBalance", []any{pubkey, map[string]string{"commitment": "confirmed"}}, &balance) != nil || balance.Value == nil {
		d.add("wallet.balance", Fail, "Read-only wallet balance request failed.", "Check the public key and RPC availability.")
		return
	}
	if *balance.Value == 0 {
		d.add("wallet.balance", Warn, "Read-only balance check succeeded; wallet has no native gas funds.", "Fund the intended wallet before enabling live operation.")
		return
	}
	d.add("wallet.balance", Pass, "Read-only balance check succeeded; native gas funds are present.", "")
}

func (d *doctor) walletSkipped() {
	d.add("wallet.balance", Warn, "Balance could not be checked without a public key and healthy RPC.", "Set SOLANA_PUBLIC_KEY and SOLANA_RPC_URLS in the selected config; no key file is opened.")
}
