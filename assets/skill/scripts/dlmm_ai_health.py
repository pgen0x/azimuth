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
import urllib.error


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
            # One available tool: required preserves the tool-call check while
            # supporting providers whose tool_choice accepts only a string.
            "tool_choice": "required",
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
    for call in calls:
        function = call.get("function", {})
        if function.get("name") != "health_check":
            continue
        try:
            arguments = json.loads(function.get("arguments", "null"))
        except (TypeError, ValueError):
            continue
        # This tool is never executed. Extra arguments such as {"reason": ...}
        # still prove inference is available; exact schema conformance is not
        # a provider availability check.
        if isinstance(arguments, dict):
            return True
    return False


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", required=True)
    parser.add_argument("--hermes-root", required=True)
    parser.add_argument("--route", default="dlmm-signal")
    args = parser.parse_args()
    profile = Path(args.profile).resolve()
    os.environ["HERMES_HOME"] = str(profile)
    sys.path.insert(0, str(Path(args.hermes_root).resolve()))
    stage = "config"
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
        stage = "inference"
        healthy = probe(runtime, model)
        print("AI probe healthy" if healthy else "AI probe unavailable")
        return 0 if healthy else 13
    except urllib.error.HTTPError as exc:
        print("AI probe HTTP status: " + str(exc.code))
        return 10 if exc.code == 429 else 15 if exc.code in (401, 403) else 11
    except TimeoutError:
        print("AI probe timeout")
        return 12
    except urllib.error.URLError as exc:
        print("AI probe connection failed")
        return 12 if isinstance(exc.reason, TimeoutError) else 16
    except Exception as exc:
        # HTTP bodies, URLs and resolver errors can contain credentials.
        print("AI probe unavailable: " + type(exc).__name__)
        return 14 if stage == "config" else 13


if __name__ == "__main__":
    sys.exit(main())
