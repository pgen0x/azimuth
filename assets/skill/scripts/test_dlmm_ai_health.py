import io
import json
import unittest

from dlmm_ai_health import probe


class ProbeTest(unittest.TestCase):
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
