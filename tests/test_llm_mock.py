# ĐTCL Coach v1.1 (2026-10-06) — kiểm thử lớp gọi AI (giả lập, không gọi mạng thật)
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import pytest  # noqa: E402

from core import coach, engine, llm  # noqa: E402


class Fake:
    def __init__(self, payload, code=200):
        self.status_code, self._p, self.text = code, payload, json.dumps(payload)

    def json(self):
        return self._p


def _state():
    return engine.GameState(units=["Azir", "Soraka"], parts=["NeedlesslyLargeRod"], stage=3, rnd=2, gold=30, level=6)


@pytest.fixture(params=["gemini", "anthropic", "openai"])
def online(monkeypatch, request):
    monkeypatch.setenv("LLM_PROVIDER", request.param)
    monkeypatch.setenv("GEMINI_API_KEY", "fake")
    calls = []

    def fake_post(url, json=None, headers=None, timeout=None, **kw):
        calls.append((url, json))
        text = "- Đi Đao Phủ Azir vì đã có Azir.\n- Giữ 50 vàng."
        if request.param == "gemini":
            return Fake({"candidates": [{"content": {"parts": [{"text": text}]}}]})
        if request.param == "anthropic":
            return Fake({"content": [{"type": "text", "text": text}]})
        return Fake({"choices": [{"message": {"content": text}}]})

    monkeypatch.setattr(llm.requests, "post", fake_post)
    return calls


def test_explain_online(online):
    st = _state()
    txt, used = coach.explain(st, engine.advise(st))
    assert used and "Azir" in txt
    sent = str(online[0][1])
    assert "Đội nên đi" in sent and "KHÔNG được đổi" in sent


def test_explain_offline(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "offline")
    st = _state()
    txt, used = coach.explain(st, engine.advise(st))
    assert not used and txt.startswith("- ")


def test_explain_falls_back_on_error(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "gemini")
    monkeypatch.setenv("GEMINI_API_KEY", "fake")
    monkeypatch.setattr(llm.requests, "post", lambda *a, **k: Fake({"error": "bad"}, 400))
    monkeypatch.setattr(llm.requests, "get", lambda *a, **k: Fake({"models": []}, 200))
    st = _state()
    txt, used = coach.explain(st, engine.advise(st))
    assert not used and "AI tạm lỗi" in txt


def test_parse_json_variants():
    assert llm.parse_json('```json\n{"a": 1}\n```') == {"a": 1}
    assert llm.parse_json('chữ thừa {"b": 2} chữ thừa') == {"b": 2}
    with pytest.raises(llm.LLMError):
        llm.parse_json("không có json")
