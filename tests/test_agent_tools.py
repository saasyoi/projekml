from api.agent import cari_kontak_resmi, rekomendasikan_kuis


def test_cari_kontak_resmi_known_bank():
    result = cari_kontak_resmi("bca")
    assert result["ditemukan"] is True
    assert "1500888" in result["telepon"]


def test_cari_kontak_resmi_case_insensitive():
    assert cari_kontak_resmi("BCA")["ditemukan"] is True
    assert cari_kontak_resmi("  bca  ")["ditemukan"] is True


def test_cari_kontak_resmi_unknown_institution_not_invented():
    result = cari_kontak_resmi("bank yang tidak pernah ada")
    assert result == {"ditemukan": False}


def test_cari_kontak_resmi_umum_returns_general_channels():
    result = cari_kontak_resmi("umum")
    assert result["ditemukan"] is True
    assert "cek_rekening" in result["saluran"]
    assert "patroli_siber" in result["saluran"]


def test_rekomendasikan_kuis_valid_topic():
    result = rekomendasikan_kuis("apk")
    assert result["ditemukan"] is True
    assert result["topik_key"] == "apk"


def test_rekomendasikan_kuis_invalid_topic():
    assert rekomendasikan_kuis("topik_tidak_ada") == {"ditemukan": False}
