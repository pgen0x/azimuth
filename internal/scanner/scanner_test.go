package scanner

import (
	"context"
	"errors"
	"testing"
	"time"

	"github.com/pgen0x/azimuth/internal/config"
	"github.com/pgen0x/azimuth/internal/deploy"
	"github.com/pgen0x/azimuth/internal/robinhood"
)

// fakeRunner stands in for the node executors. The deploy path's ORDERING is what
// these tests pin down, so what matters is how often each call happens, not what
// a real executor would answer.
type fakeRunner struct {
	enabled  bool
	bal      robinhood.Balances
	balErr   error
	balCalls int
	inv      robinhood.Inventory
	invErr   error
	deployed int
}

func (f *fakeRunner) Enabled() bool { return f.enabled }

func (f *fakeRunner) Inventory(context.Context) (robinhood.Inventory, error) {
	if f.invErr != nil {
		return robinhood.Inventory{}, f.invErr
	}
	if f.inv.ByToken == nil {
		f.inv.ByToken = map[string]int{}
	}
	return f.inv, nil
}

func (f *fakeRunner) Balance(context.Context) (robinhood.Balances, error) {
	f.balCalls++
	if f.balErr != nil {
		return robinhood.Balances{}, f.balErr
	}
	return f.bal, nil
}

func (f *fakeRunner) Deploy(context.Context, string, float64, float64, float64, string, string) (string, error) {
	f.deployed++
	return "🚀 DEPLOYED", nil
}

// countEntryTiming swaps the package's entry-timing hook for a counter and
// restores it. Every call it records is one GeckoTerminal OHLCV request the live
// daemon would have spent out of a ~10/minute budget.
func countEntryTiming(t *testing.T, confirmed bool) *int {
	t.Helper()
	n := 0
	entryTiming = func(string) (bool, string, bool) {
		n++
		return confirmed, "stub", true
	}
	t.Cleanup(func() { entryTiming = robinhood.EntryTimingConfirm })
	return &n
}

func wethCandidate(pool, symbol string) *robinhood.Candidate {
	return &robinhood.Candidate{
		Chain: "robinhood", Protocol: "v3", Pool: pool,
		BaseSymbol: symbol, BaseAddress: "0xbase" + symbol,
		QuoteAddress: "0x4200000000000000000000000000000000000006",
		QuoteSymbol:  "WETH", Score: 100,
	}
}

// newTestScanner wires the fields robinhoodDeploy actually touches. dep is real
// but command-less: the success path pipes its outcome to REPORT_CMD, and a nil
// runner there would panic on a test that got far enough to deploy — which is
// precisely the test worth keeping honest.
func newTestScanner(v3 rhRunner) *Scanner {
	return &Scanner{
		cfg:     testConfig(),
		dep:     deploy.New("", "", time.Minute),
		rhDep:   v3,
		rhDepV4: &fakeRunner{},
	}
}

func testConfig() config.Config {
	return config.Config{
		RobinhoodMaxOpenPositions: 8,
		RobinhoodIndicatorGate:    true,
		RobinhoodMinGasEth:        0.0002,
		RobinhoodDeployStrategy:   "weth_ladder",
		RobinhoodSize: robinhood.SizeParams{
			Reserve: 0.002, Pct: 0.45, Floor: 0.003, Ceil: 0.05,
		},
	}
}

// The point of reading the wallet first: a mode whose quote asset cannot fund the
// floor must cost ZERO entry-timing requests. Before the reorder this batch spent
// one GeckoTerminal call per candidate to reach a skip that was already certain —
// every cycle, forever, since nothing about an empty wallet changes on its own.
func TestUnfundableBatchSpendsNoEntryTimingRequests(t *testing.T) {
	calls := countEntryTiming(t, true)
	// Gas is fine; the LP asset is not. 0.0025 WETH minus the 0.002 reserve is
	// below the 0.003 floor, so ComputeDeployAmount leaves nothing to spend.
	v3 := &fakeRunner{enabled: true, bal: robinhood.Balances{ETH: 0.01, WETH: 0.0025}}
	s := newTestScanner(v3)

	s.robinhoodDeploy(context.Background(), "rh-ladder", []*robinhood.Candidate{
		wethCandidate("0xpool1aaaaaaaaaa", "AAA"),
		wethCandidate("0xpool2bbbbbbbbbb", "BBB"),
		wethCandidate("0xpool3cccccccccc", "CCC"),
	})

	if *calls != 0 {
		t.Fatalf("an unfundable batch must not walk the entry-timing gate, made %d request(s)", *calls)
	}
	if v3.deployed != 0 {
		t.Fatalf("nothing was affordable, yet %d deploy(s) fired", v3.deployed)
	}
	// One read for the one protocol present — not one per candidate.
	if v3.balCalls != 1 {
		t.Fatalf("balance should be read once per protocol, got %d reads", v3.balCalls)
	}
}

// rh-turnover's entry SHAPE is part of its thesis, so it must not be reachable
// from ROBINHOOD_DEPLOY_STRATEGY. This has been got wrong twice in one day: the
// mode shipped as `balanced_tight` on 2026-08-07, which pre-swaps half the
// commit into the memecoin — the exposure that lost 15.04%/trade and the exact
// thing a churn screen must not buy. The config here is deliberately set to
// weth_ladder (the ladder default) so the test fails if the pin is ever dropped
// and the mode silently inherits it.
func TestTurnoverPinsOneSidedStrategy(t *testing.T) {
	s := newTestScanner(&fakeRunner{enabled: true})
	bal := robinhood.Balances{ETH: 0.01, WETH: 1}

	c := wethCandidate("0xpool1aaaaaaaaaa", "AAA")
	c.Mode = robinhood.Turnover.Mode
	if got := s.sizeFor(c, bal).strategy; got != "weth_below" {
		t.Errorf("rh-turnover strategy = %q, want weth_below (one rung, holds no token)", got)
	}

	// Every other mode still inherits the configured strategy — the pin is
	// turnover's alone, not a global override.
	other := wethCandidate("0xpool2bbbbbbbbbb", "BBB")
	other.Mode = robinhood.Ladder.Mode
	if got := s.sizeFor(other, bal).strategy; got != "weth_ladder" {
		t.Errorf("rh-ladder strategy = %q, want the configured weth_ladder", got)
	}
}

// Too little gas is the other unfundable shape: the wallet can be WETH-rich and
// still unable to pay for the mint, and that answer is just as independent of
// which candidate wins.
func TestGasFloorSkipsBeforeEntryTiming(t *testing.T) {
	calls := countEntryTiming(t, true)
	v3 := &fakeRunner{enabled: true, bal: robinhood.Balances{ETH: 0.00001, WETH: 1}}
	s := newTestScanner(v3)

	s.robinhoodDeploy(context.Background(), "rh-ladder", []*robinhood.Candidate{
		wethCandidate("0xpool1aaaaaaaaaa", "AAA"),
	})

	if *calls != 0 {
		t.Fatalf("a gas-starved wallet must not walk the entry-timing gate, made %d request(s)", *calls)
	}
	if v3.deployed != 0 {
		t.Fatal("deployed without gas for the mint")
	}
}

// The reorder must not have cost the funded path anything: a fundable batch still
// walks the gate and still deploys.
func TestFundableBatchStillWalksAndDeploys(t *testing.T) {
	calls := countEntryTiming(t, true)
	v3 := &fakeRunner{enabled: true, bal: robinhood.Balances{ETH: 0.01, WETH: 1}}
	s := newTestScanner(v3)

	s.robinhoodDeploy(context.Background(), "rh-ladder", []*robinhood.Candidate{
		wethCandidate("0xpool1aaaaaaaaaa", "AAA"),
		wethCandidate("0xpool2bbbbbbbbbb", "BBB"),
	})

	// The walk stops at the first confirmed candidate: one request, not two.
	if *calls != 1 {
		t.Fatalf("want one entry-timing request for the winning candidate, got %d", *calls)
	}
	if v3.deployed != 1 {
		t.Fatalf("want exactly one deploy, got %d", v3.deployed)
	}
}

// An unreadable balance still fails CLOSED, and now fails closed EARLIER. The
// repo's convention is that missing data passes; the wallet read is the
// deliberate exception, because guessing a size is how you overspend or mint dust.
func TestUnreadableBalanceFailsClosedWithoutWalking(t *testing.T) {
	calls := countEntryTiming(t, true)
	v3 := &fakeRunner{enabled: true, balErr: errors.New("executor timeout")}
	s := newTestScanner(v3)

	s.robinhoodDeploy(context.Background(), "rh-ladder", []*robinhood.Candidate{
		wethCandidate("0xpool1aaaaaaaaaa", "AAA"),
	})

	if *calls != 0 {
		t.Fatalf("an unknown balance must stop the cycle before the gate, made %d request(s)", *calls)
	}
	if v3.deployed != 0 {
		t.Fatal("deployed on a balance we could not read")
	}
}
