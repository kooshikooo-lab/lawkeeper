"""Tests for ai_review.py's call_model() retry behavior.

Mocks the network boundary (real API calls cost money and depend on live
rate-limit conditions). Covers the 2026-08-20 real-world finding: Kimi/
Moonshot signals the same shared-pool-congestion condition inside a 200
response body ("high demand", "please try again") instead of an HTTP 429,
same underlying condition as OpenRouter's own free-tier 429s, different
provider wording -- both must trigger the same retry-with-backoff path.
"""
from types import SimpleNamespace
from unittest.mock import patch

from conftest import load_script

ai_review = load_script("ai_review.py")


def _fake_response(status_code, text, json_body=None):
    r = SimpleNamespace(status_code=status_code, text=text)
    r.json = lambda: json_body if json_body is not None else {}
    return r


class TestSoftRateLimitRetry:
    def test_soft_rate_limit_text_in_200_triggers_retry(self, monkeypatch):
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
        ok_body = {"choices": [{"message": {"content": "real answer"}}], "usage": {}}
        responses = [
            _fake_response(200, "Server is at high demand, please try again shortly."),
            _fake_response(200, "ok", json_body=ok_body),
        ]
        with patch.object(ai_review.time, "sleep") as mock_sleep, \
             patch.object(ai_review.requests, "post", side_effect=responses) as mock_post:
            result = ai_review.call_model("some/model:free", "hello", max_retries=3)
        assert result == "real answer"
        assert mock_post.call_count == 2
        mock_sleep.assert_called_once()

    def test_real_429_still_retries_as_before(self, monkeypatch):
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
        ok_body = {"choices": [{"message": {"content": "real answer"}}], "usage": {}}
        responses = [
            _fake_response(429, "rate limited"),
            _fake_response(200, "ok", json_body=ok_body),
        ]
        with patch.object(ai_review.time, "sleep"), \
             patch.object(ai_review.requests, "post", side_effect=responses) as mock_post:
            result = ai_review.call_model("some/model:free", "hello", max_retries=3)
        assert result == "real answer"
        assert mock_post.call_count == 2

    def test_exhausted_retries_on_soft_limit_raises_with_real_body(self, monkeypatch):
        monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
        # Every attempt is a 200 that still reads as congested -- the loop
        # exhausts max_retries and falls through with the last (200) resp,
        # whose body has no "choices" key, so this must surface a real
        # RuntimeError naming what was actually missing, not a bare KeyError.
        responses = [_fake_response(200, "please try again later") for _ in range(2)]
        with patch.object(ai_review.time, "sleep"), \
             patch.object(ai_review.requests, "post", side_effect=responses):
            try:
                ai_review.call_model("some/model:free", "hello", max_retries=2)
                assert False, "expected RuntimeError"
            except RuntimeError as exc:
                assert "choices" in str(exc)
