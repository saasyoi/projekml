from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from api.ai import AIServiceError
from api.agent import _extract_tool_results, run_scam_agent


def _fake_function_response(name, response):
    part = SimpleNamespace(function_response=SimpleNamespace(name=name, response={"result": response}))
    return SimpleNamespace(parts=[part])


def _fake_response(text="Balasan aman.", history=None):
    return SimpleNamespace(text=text, automatic_function_calling_history=history or [])


def test_extract_tool_results_no_tool_calls():
    result = _extract_tool_results(_fake_response(history=[]))
    assert result == {"matched_scenario": None, "suggested_quiz": None, "official_contact": None}


def test_extract_tool_results_scenario_matched():
    history = [_fake_function_response("cari_skenario_penipuan", {
        "ditemukan": True, "judul": "Modus APK Kurir", "deskripsi": "...",
        "saran_tindakan": "Jangan diinstal.", "kategori_topik_kuis": "apk",
    })]
    result = _extract_tool_results(_fake_response(history=history))
    assert result["matched_scenario"]["title"] == "Modus APK Kurir"
    assert result["matched_scenario"]["category"] == "apk"
    assert result["suggested_quiz"] is None
    assert result["official_contact"] is None


def test_extract_tool_results_scenario_not_found_stays_none():
    history = [_fake_function_response("cari_skenario_penipuan", {"ditemukan": False})]
    result = _extract_tool_results(_fake_response(history=history))
    assert result["matched_scenario"] is None


def test_extract_tool_results_quiz_and_contact_together():
    history = [
        _fake_function_response("cari_kontak_resmi", {"ditemukan": True, "nama": "Bank BCA", "telepon": "1500888"}),
        _fake_function_response("rekomendasikan_kuis", {"ditemukan": True, "topik_key": "link", "judul_kuis": "Waspada Link Palsu"}),
    ]
    result = _extract_tool_results(_fake_response(history=history))
    assert result["official_contact"]["nama"] == "Bank BCA"
    assert result["suggested_quiz"]["topic_key"] == "link"


def _mock_client(response=None, side_effect=None):
    client = MagicMock()
    if side_effect is not None:
        client.models.generate_content.side_effect = side_effect
    else:
        client.models.generate_content.return_value = response
    return client


def test_run_scam_agent_happy_path_returns_reply_and_tool_results():
    history = [_fake_function_response("cari_kontak_resmi", {"ditemukan": True, "nama": "Bank BCA"})]
    fake_client = _mock_client(response=_fake_response(text="Hati-hati, Pak/Bu.", history=history))

    with patch("api.agent._get_gemini_key", return_value="fake-key"), \
         patch("api.agent.GEMINI_LIB_AVAILABLE", True), \
         patch("api.agent.genai_client.Client", return_value=fake_client):
        result = run_scam_agent("system prompt", "ada yang minta OTP saya")

    assert result["reply"] == "Hati-hati, Pak/Bu."
    assert result["official_contact"]["nama"] == "Bank BCA"


def test_run_scam_agent_raises_without_api_key():
    with patch("api.agent._get_gemini_key", return_value=""):
        with pytest.raises(AIServiceError):
            run_scam_agent("system prompt", "halo")


def test_run_scam_agent_raises_on_empty_reply_after_retries():
    fake_client = _mock_client(response=_fake_response(text=""))

    with patch("api.agent._get_gemini_key", return_value="fake-key"), \
         patch("api.agent.GEMINI_LIB_AVAILABLE", True), \
         patch("api.agent.genai_client.Client", return_value=fake_client), \
         patch("api.agent._RETRY_DELAY_SECONDS", 0):
        with pytest.raises(AIServiceError):
            run_scam_agent("system prompt", "halo")

    assert fake_client.models.generate_content.call_count == 2  # _MAX_ATTEMPTS


def test_run_scam_agent_raises_after_repeated_exceptions():
    fake_client = _mock_client(side_effect=RuntimeError("Gemini sedang down"))

    with patch("api.agent._get_gemini_key", return_value="fake-key"), \
         patch("api.agent.GEMINI_LIB_AVAILABLE", True), \
         patch("api.agent.genai_client.Client", return_value=fake_client), \
         patch("api.agent._RETRY_DELAY_SECONDS", 0):
        with pytest.raises(AIServiceError):
            run_scam_agent("system prompt", "halo")

    assert fake_client.models.generate_content.call_count == 2
