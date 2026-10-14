import io
import json
import unittest
import urllib.error

from dlmm_ai_health import probe, configured_probe_models, probe_configured_route


class ProbeTest(unittest.TestCase):
    def test_only_configured_same_endpoint_fallbacks_reuse_credentials(self):
        runtime = {"base_url": "http://router.test/v1/"}
        fallbacks = [
            {"provider": "custom", "model": "backup", "base_url": "http://router.test/v1"},
            {"provider": "custom", "model": "foreign", "base_url": "http://other.test/v1"},
            {"provider": "custom", "model": "other-key", "base_url": "http://router.test/v1", "api_key": "other"},
            {"provider": "other", "model": "other-provider", "base_url": "http://router.test/v1"},
            {"provider": "custom", "model": "implicit-endpoint"},
            {"provider": "custom", "model": "markt", "base_url": "http://router.test/v1"},
            None,
        ]
        config = {"model": {"provider": "custom"}, "fallback_providers": fallbacks}
        self.assertEqual(configured_probe_models(config, runtime, "markt"), ["markt", "backup"])
        config["model"]["provider"] = "other"
        self.assertEqual(configured_probe_models(config, runtime, "markt"), ["markt"])

    def test_primary_failure_uses_fallback_with_remaining_deadline(self):
        runtime = {"api_mode": "chat_completions", "base_url": "http://router.test/v1", "api_key": "test"}
        calls = []
        class Opener:
            def open(inner, req, timeout):
                calls.append((json.loads(req.data)["model"], timeout))
                if len(calls) == 1:
                    raise urllib.error.HTTPError(req.full_url, 400, "unavailable", {}, None)
                return io.BytesIO(b'{"choices":[{"message":{"content":"OK"}}]}')
        ticks = iter([0, 0, 12])
        self.assertTrue(probe_configured_route(runtime, ["markt", "backup"], Opener(), lambda: next(ticks)))
        self.assertEqual(calls, [("markt", 60), ("backup", 48)])

    def test_deadline_exhaustion_never_starts_fallback(self):
        runtime = {"api_mode": "chat_completions", "base_url": "http://router.test/v1", "api_key": "test"}
        calls = []
        class Opener:
            def open(inner, req, timeout):
                calls.append(json.loads(req.data)["model"])
                raise TimeoutError()
        ticks = iter([0, 0, 60])
        with self.assertRaises(TimeoutError):
            probe_configured_route(runtime, ["markt", "backup"], Opener(), lambda: next(ticks))
        self.assertEqual(calls, ["markt"])

    def test_healthy_primary_stops_and_failed_chain_preserves_http_status(self):
        runtime = {"api_mode": "chat_completions", "base_url": "http://router.test/v1", "api_key": "test"}
        calls = []
        class Opener:
            def open(inner, req, timeout):
                calls.append(json.loads(req.data)["model"])
                return io.BytesIO(b'{"choices":[{"message":{"content":"OK"}}]}')
        self.assertTrue(probe_configured_route(runtime, ["markt", "backup"], Opener()))
        self.assertEqual(calls, ["markt"])
        class Failed:
            def open(inner, req, timeout):
                raise urllib.error.HTTPError(req.full_url, 429, "limited", {}, None)
        with self.assertRaises(urllib.error.HTTPError) as caught:
            probe_configured_route(runtime, ["markt", "backup"], Failed())
        self.assertEqual(caught.exception.code, 429)

    def test_availability_probe_and_model_preserved(self):
        runtime = {"api_mode": "chat_completions", "base_url": "http://router.test/v1", "api_key": "test"}
        good = {"choices": [{"message": {"tool_calls": [{"function": {
            "name": "health_check", "arguments": "{}"}}]}}]}

        class Opener:
            def __init__(self, response):
                self.response = response

            def open(inner, req, timeout):
                body = json.loads(req.data)
                self.assertEqual(body["model"], "markt")
                self.assertNotIn("tools", body)
                self.assertNotIn("tool_choice", body)
                self.assertEqual(body["messages"], [{"role": "user", "content": "Reply with OK."}])
                self.assertEqual(body["max_tokens"], 64)
                self.assertEqual(req.full_url, "http://router.test/v1/chat/completions")
                self.assertEqual(timeout, 60)
                return io.BytesIO(json.dumps(inner.response).encode())

        self.assertTrue(probe(runtime, "markt", Opener(good)))
        # 9router's valid Opus response adds a reason despite the no-args schema.
        # Rejecting this healthy tool call previously forced deterministic entry.
        good["choices"][0]["message"]["tool_calls"][0]["function"]["arguments"] = '{"reason":"User requested immediate health check"}'
        self.assertTrue(probe(runtime, "markt", Opener(good)))
        for arguments in ('null', '[]', '"text"', 'broken'):
            good["choices"][0]["message"]["tool_calls"][0]["function"]["arguments"] = arguments
            self.assertFalse(probe(runtime, "markt", Opener(good)))
        for response in ({}, {"error": "quota"}):
            self.assertFalse(probe(runtime, "markt", Opener(response)))
        self.assertTrue(probe(runtime, "markt", Opener(
            {"choices": [{"message": {"content": "OK"}}]})))
        self.assertFalse(probe(runtime, "markt", Opener(
            {"choices": [{"message": {"content": "   "}}]})))
        # The low-token availability probe can stop during valid reasoning.
        self.assertTrue(probe(runtime, "markt", Opener(
            {"choices": [{"finish_reason": "length", "message": {
                "content": "", "reasoning_content": "Need to reply concisely."}}]})))
        for reasoning in (None, "   ", {}, []):
            self.assertFalse(probe(runtime, "markt", Opener(
                {"choices": [{"message": {"content": "", "reasoning_content": reasoning}}]})))



if __name__ == "__main__":
    unittest.main()
