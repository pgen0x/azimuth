#!/usr/bin/env python3
"""
audit_token.py — Solana token security audit using Binance Web3 API.
"""

import json
import math
import re
import sys
import uuid
import subprocess

def run_command(cmd):
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=12)
        return result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return "", str(e)

def percentage(value):
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
        return number if math.isfinite(number) and 0 <= number <= 100 else None
    except (ValueError, TypeError):
        return None

def main():
    if len(sys.argv) < 2:
        print("Usage: audit_token.py <MINT>")
        sys.exit(1)

    mint = sys.argv[1]
    if not re.fullmatch(r"[1-9A-HJ-NP-Za-km-z]{32,44}", mint):
        print(json.dumps({"verdict": "FAIL", "reason": "Invalid Solana mint address"}))
        sys.exit(1)
    request_id = str(uuid.uuid4())

    payload = {
        "binanceChainId": "CT_501",
        "contractAddress": mint,
        "requestId": request_id
    }

    cmd = f"""curl --max-time 10 -s --location 'https://web3.binance.com/bapi/defi/v1/public/wallet-direct/security/token/audit' \
--header 'Content-Type: application/json' \
--header 'source: agent' \
--header 'Accept-Encoding: identity' \
--header 'User-Agent: binance-web3/1.4 (Skill)' \
--data '{json.dumps(payload)}'"""

    out, err = run_command(cmd)
    if err:
        print(json.dumps({"verdict": "UNKNOWN", "reason": f"API Error: {err}"}))
        sys.exit(0)

    try:
        data = json.loads(out)
        if data.get("success") is not True:
            print(json.dumps({"verdict": "UNKNOWN", "reason": f"API returned success=false: {data.get('message')}"}))
            sys.exit(0)

        audit = data.get("data", {})
        if audit.get("hasResult") is not True or audit.get("isSupported") is not True:
             print(json.dumps({"verdict": "UNKNOWN", "reason": "Security audit not available/supported for this token."}))
             sys.exit(0)

        risk_level = audit.get("riskLevel")
        if type(risk_level) is not int or risk_level < 0:
            risk_level = None
        risk_enum = audit.get("riskLevelEnum")

        if risk_level is not None and risk_level >= 4:
            print(json.dumps({
                "verdict": "FAIL", 
                "reason": f"High risk detected (Level {risk_level}: {risk_enum})",
                "risk_level": risk_level,
                "risk_items": audit.get("riskItems", [])
            }))
        else:
            # Dev holding check — fetch token metrics from Binance pulse API
            dev_payload = json.dumps({"chainId": "CT_501", "contractAddress": mint, "limit": 1})
            dev_cmd = f"""curl --max-time 10 -s -X POST 'https://web3.binance.com/bapi/defi/v1/public/wallet-direct/buw/wallet/market/token/pulse/rank/list/ai' \
-H 'Content-Type: application/json' -H 'User-Agent: binance-web3/1.4 (Skill)' \
-d '{dev_payload}'"""
            dev_out, _ = run_command(dev_cmd)
            token_info = None
            dev_pct = top10_pct = None
            try:
                dev_data = json.loads(dev_out)
                token_list = dev_data.get("data", [])
                token_info = next((t for t in token_list if t.get("contractAddress") == mint), None)
                if token_info:
                    dev_pct = percentage(token_info.get("holdersDevPercent"))
                    top10_pct = percentage(token_info.get("holdersTop10Percent"))
                    if dev_pct is not None and dev_pct > 30:
                        print(json.dumps({"verdict": "FAIL", "reason": f"Dev holds {dev_pct:.1f}% of supply — rug risk"}))
                        sys.exit(0)
                    if top10_pct is not None and top10_pct > 95:
                        print(json.dumps({"verdict": "FAIL", "reason": f"Top 10 wallets hold {top10_pct:.1f}% — extreme concentration risk"}))
                        sys.exit(0)
            except Exception:
                pass  # skip dev check if API unavailable
            extra = audit.get("extraInfo") or {}
            print(json.dumps({
                "verdict": "PASS" if risk_level is not None else "UNKNOWN",
                "risk_level": risk_level,
                "risk_enum": risk_enum,
                "buy_tax": extra.get("buyTax"),
                "sell_tax": extra.get("sellTax"),
                "dev_pct": dev_pct,
                "top10_pct": top10_pct,
            }))

    except Exception as e:
        print(json.dumps({"verdict": "UNKNOWN", "reason": f"Parsing Error: {str(e)}"}))

if __name__ == "__main__":
    main()
