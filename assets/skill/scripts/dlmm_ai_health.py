#!/usr/bin/env python3
"""Read-only pre-dispatch inference probe. Run with Hermes' Python environment.

Exit 0 allows Hermes to own the batch; any failure selects the deterministic
pipeline before sending a webhook. This is not an acknowledgement of a pick.
"""
import argparse
import json
import os
from pathlib import Path
import sys
import urllib.request


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None  # Never forward provider credentials to a redirect target.


def probe(runtime, model, opener=None):
    if runtime.get("api_mode") != "chat_completions":
        raise ValueError("probe requires chat_completions")
    request = urllib.request.Request(
        runtime["base_url"].rstrip("/") + "/chat/completions",
        data=json.dumps({
            "model": model,
            "messages": [{"role": "user", "content": "Call health_check now."}],
            "tools": [{"type": "function", "function": {
                "name": "health_check", "description": "Read-only availability check",
                "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
            }}],
            "tool_choice": {"type": "function", "function": {"name": "health_check"}},
            "max_tokens": 64, "stream": False,
        }).encode(),
        headers={"Content-Type": "application/json",
                 "Authorization": "Bearer " + runtime["api_key"]},
    )
    opener = opener or urllib.request.build_opener(NoRedirect)
    with opener.open(request, timeout=15) as response:
        data = json.loads(response.read(1_000_000))
    if data.get("error"):
        return False
    choices = data.get("choices") or []
    if not choices:
        return False
    calls = choices[0].get("message", {}).get("tool_calls") or []
    return any(call.get("function", {}).get("name") == "health_check"
               and json.loads(call["function"].get("arguments", "null")) == {}
               for call in calls)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--hermes-root", required=True)
    parser.add_argument("--route", default="dlmm-signal")
    args = parser.parse_args()
    profile = Path(args.profile).resolve()
    os.environ["HERMES_HOME"] = str(profile)
    sys.path.insert(0, str(Path(args.hermes_root).resolve()))
    try:
        from dotenv import load_dotenv
        load_dotenv(profile / ".env", override=True)
        from hermes_cli.config import load_config
        from hermes_cli.runtime_provider import resolve_runtime_provider
        config = load_config()
        route = json.loads((profile / "webhook_subscriptions.json").read_text())[args.route]
        if not route.get("enabled", True) or route.get("deliver_only"):
            raise ValueError("AI route disabled")
        model_cfg = config["model"]
        model = route.get("model") or model_cfg["default"]
        # Current Hermes webhook adapter uses the profile default. A mismatch
        # must not claim that a different model's availability proves health.
        if model != model_cfg["default"]:
            raise ValueError("route/profile model mismatch")
        runtime = resolve_runtime_provider(requested=model_cfg.get("provider"), target_model=model)
        healthy = probe(runtime, model)
        print("AI probe healthy" if healthy else "AI probe unavailable")
        return 0 if healthy else 1
    except Exception as exc:
        # HTTP bodies, URLs and resolver errors can contain credentials.
        print("AI probe unavailable: " + type(exc).__name__)
        return 1


if __name__ == "__main__":
    sys.exit(main())
