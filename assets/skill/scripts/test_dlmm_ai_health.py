import io
import json
import unittest

from dlmm_ai_health import probe


class ProbeTest(unittest.TestCase):
    def test_actual_tool_response_required_and_model_preserved(self):
        runtime = {"api_mode": "chat_completions", "base_url": "http://router.test/v1", "api_key": "test"}
        good = {"choices": [{"message": {"tool_calls": [{"function": {
            "name": "health_check", "arguments": "{}"}}]}}]}

        class Opener:
            def __init__(self, response):
                self.response = response

            def open(inner, req, timeout):
                self.assertEqual(json.loads(req.data)["model"], "markt")
                self.assertEqual(req.full_url, "http://router.test/v1/chat/completions")
                self.assertEqual(timeout, 15)
                return io.BytesIO(json.dumps(inner.response).encode())

        self.assertTrue(probe(runtime, "markt", Opener(good)))
        for response in ({}, {"error": "quota"}, {"choices": [{"message": {"content": "OK"}}]}):
            self.assertFalse(probe(runtime, "markt", Opener(response)))


if __name__ == "__main__":
    unittest.main()
