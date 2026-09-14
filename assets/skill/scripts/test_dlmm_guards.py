"""Offline replay: python3 assets/skill/scripts/test_dlmm_guards.py."""
import contextlib
import io
import json
from pathlib import Path
import tempfile
import textwrap
from types import SimpleNamespace
from unittest.mock import patch
import dlmm_monitor as monitor


def main():
    # Execute the production hold/indicator section, not a mirrored decision.
    source = Path(monitor.__file__).read_text()
    start = source.index("        close_reason, protected_risk_exit =")
    stop = source.index("        # Execute close if triggered", start)
    section = "for _ in [0]:\n" + textwrap.indent(textwrap.dedent(source[start:stop]), "    ")
    trailing = "Trailing Take-Profit hit (Peak: 2.79%, Current: 1.84%)"
    for mode in ("turnover", "pulse"):
        for pnl, h1, expected in [(1.84, 0, "Trailing"), (-3.38, None, "Downtrend"),
                                   (-3.38, -10, "Sustained"), (-9.23, -10, "Hard Stop-Loss")]:
            reason = "Hard Stop-Loss hit (-9.23%)" if pnl == -9.23 else trailing
            def forbidden(*args, **kwargs):
                raise AssertionError("Risk exit reached a discretionary veto")
            ns = dict(vars(monitor), close_reason=reason, meta={"mode": mode}, pnl_pct=pnl,
                      price_change_h1=h1, emergency_close=False, params={"INDICATORS_ENABLED": True},
                      cli=SimpleNamespace(report_only=False, no_enforce=True),
                      run_command=forbidden, check_local_indicators=forbidden)
            exec(compile(section, monitor.__file__, "exec"), ns)
            assert ns["protected_risk_exit"] and ns["close_reason"].startswith(expected)
    # Discretionary thesis-mode trailing still honors a rejecting indicator.
    ns.update(meta={"mode": "multiday"}, pnl_pct=1.84, close_reason=trailing,
              is_tight_tp_pos=False, pair="TEST", pool="pool", pos_addr="position", now=100,
              run_command=lambda *args, **kwargs: ("", "", 0),
              check_local_indicators=lambda *args: False)
    with contextlib.redirect_stdout(io.StringIO()):
        exec(compile(section, monitor.__file__, "exec"), ns)
    assert ns["close_reason"] is None
    assert monitor.protect_tight_exit("RUG velocity dump", "pulse", -20, -30, True) == ("RUG velocity dump", True)
    # Missing profit signal above the risk floor must not invent an exit.
    assert monitor.protect_tight_exit(None, "pulse", 0.2, None) == (None, False)
    with tempfile.TemporaryDirectory() as tmp:
        pos = "2G6rKc9ssZZxVagZpfKKfph8UARmAbh9GjpV9R3uxGGe"
        folder = Path(tmp) / "memories/dlmm_entries"
        folder.mkdir(parents=True)
        context = dict(position=pos, pool="pool", mode="turnover", strategy="turnover_rebalance",
                       recenter_of="root", deployed_at=100, size_sol=0.1)
        (folder / (pos + ".json")).write_text(json.dumps(context))
        with patch.object(monitor, "PROFILE_DIR", tmp):
            assert monitor.recover_position_metadata(pos, "pool") == context
    print("PERPSPAD exit precedence, discretionary holds and timeout provenance passed")


if __name__ == "__main__":
    main()
