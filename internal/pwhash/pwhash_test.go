package pwhash

import "testing"

func TestHashRoundTrip(t *testing.T) {
	h, err := Hash("correct horse battery", MinIterations)
	if err != nil {
		t.Fatal(err)
	}
	p, err := Parse(h)
	if err != nil || !p.Verify("correct horse battery") || p.Verify("wrong") {
		t.Fatal("round trip failed")
	}
	if _, err := Hash("", MinIterations); err == nil {
		t.Fatal("empty password hashed")
	}
}
