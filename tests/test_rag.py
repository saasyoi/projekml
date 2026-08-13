from api.rag import query_rag, SCAM_DATABASE


def test_matches_known_apk_scam():
    result = query_rag("saya dapat file apk undangan pernikahan dari nomor tidak dikenal")
    assert result is not None
    assert result["category"] == "apk"


def test_matches_known_otp_phishing():
    result = query_rag(
        "ada penelepon mengaku petugas customer service bank, bilang rekening saya "
        "bermasalah dan akan diblokir, lalu diminta kode otp pin nomor kartu lewat telepon"
    )
    assert result is not None
    assert result["id"] == "cs_bank_palsu"


def test_no_match_for_unrelated_text():
    result = query_rag("halo apa kabar semoga hari ini menyenangkan")
    assert result is None


def test_empty_text_returns_none():
    assert query_rag("") is None
    assert query_rag(None) is None


def test_every_entry_has_required_fields():
    for item in SCAM_DATABASE:
        assert item["id"]
        assert item["title"]
        assert item["category"] in ("apk", "link", "sosial")
        assert item["description"]
        assert item["action"]
