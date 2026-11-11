package setup

import (
	"bytes"
	"crypto/ed25519"
	"crypto/rand"
	"encoding/json"
	"errors"
	"math/big"
	"strings"
)

const base58Alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

func base58Encode(b []byte) string {
	n := new(big.Int).SetBytes(b)
	mod, base := new(big.Int), big.NewInt(58)
	var out []byte
	for n.Sign() > 0 {
		n.DivMod(n, base, mod)
		out = append(out, base58Alphabet[mod.Int64()])
	}
	for _, c := range b {
		if c != 0 {
			break
		}
		out = append(out, '1')
	}
	for i, j := 0, len(out)-1; i < j; i, j = i+1, j-1 {
		out[i], out[j] = out[j], out[i]
	}
	return string(out)
}

func base58Decode(s string) ([]byte, error) {
	n := new(big.Int)
	for _, r := range s {
		d := strings.IndexRune(base58Alphabet, r)
		if d < 0 {
			return nil, errors.New("not base58")
		}
		n.Mul(n, big.NewInt(58))
		n.Add(n, big.NewInt(int64(d)))
	}
	zeros := len(s) - len(strings.TrimLeft(s, "1"))
	return append(make([]byte, zeros), n.Bytes()...), nil
}

// Wallet is a Solana ed25519 keypair. The private half is the 64-byte secret
// key in the base58 form dlmm_executor.js reads from SOLANA_PRIVATE_KEY.
type Wallet struct {
	PublicKey  string
	privateKey string
}

// Secret returns the base58 private key. Callers must never log or print it.
func (w Wallet) Secret() string { return w.privateKey }

// String keeps an accidental %v of a Wallet from printing the private key.
func (w Wallet) String() string { return "wallet(" + w.PublicKey + ")" }

// GoString covers %#v the same way.
func (w Wallet) GoString() string { return w.String() }

// GenerateWallet creates a fresh keypair from crypto/rand.
func GenerateWallet() (Wallet, error) {
	pub, priv, err := ed25519.GenerateKey(rand.Reader)
	if err != nil {
		return Wallet{}, errors.New("cannot generate keypair")
	}
	defer clear(priv)
	return Wallet{PublicKey: base58Encode(pub), privateKey: base58Encode(priv)}, nil
}

// ParsePrivateKey accepts a base58 64-byte secret key, a base58 32-byte seed, or
// a solana-keygen JSON byte array. A 64-byte key must carry the public half its
// seed derives. Errors never contain the input.
func ParsePrivateKey(input []byte) (Wallet, error) {
	bad := errors.New("private key is not a valid Solana keypair (base58 or solana-keygen JSON array)")
	text := strings.TrimSpace(string(input))
	var raw []byte
	if strings.HasPrefix(text, "[") {
		var nums []int
		if json.Unmarshal([]byte(text), &nums) != nil {
			return Wallet{}, bad
		}
		raw = make([]byte, len(nums))
		for i, n := range nums {
			if n < 0 || n > 255 {
				return Wallet{}, bad
			}
			raw[i] = byte(n)
		}
		clear(nums)
	} else {
		var err error
		if raw, err = base58Decode(text); err != nil {
			return Wallet{}, bad
		}
	}
	defer clear(raw)
	var priv ed25519.PrivateKey
	switch len(raw) {
	case ed25519.SeedSize:
		priv = ed25519.NewKeyFromSeed(raw)
	case ed25519.PrivateKeySize:
		priv = ed25519.NewKeyFromSeed(raw[:32])
		if !bytes.Equal(priv[32:], raw[32:]) {
			clear(priv)
			return Wallet{}, errors.New("private key's public half does not match its seed")
		}
	default:
		return Wallet{}, bad
	}
	defer clear(priv)
	return Wallet{PublicKey: base58Encode(priv[32:]), privateKey: base58Encode(priv)}, nil
}
