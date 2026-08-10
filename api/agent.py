import logging
import time

from api.ai import AIServiceError, GEMINI_LIB_AVAILABLE, _get_gemini_key, genai_client, _MAX_ATTEMPTS, _RETRY_DELAY_SECONDS
from api.rag import query_rag
from api.quiz import QUIZ_BANK

logger = logging.getLogger("familysecure_backend")


# Kontak resmi terverifikasi
OFFICIAL_CONTACTS = {
    "bca": {
        "nama": "Bank BCA", "telepon": "1500888 (Halo BCA)", "whatsapp": "08111500998",
        "website": "bca.co.id",
        "catatan": "Laporkan akun/situs palsu mengatasnamakan BCA lewat 'Lapor Bareng BCA' di layanan.bca.co.id",
    },
    "bri": {
        "nama": "Bank BRI", "telepon": "1500017 (BRI Contact) / 14017 (BRI Call)",
        "website": "bri.co.id",
        "catatan": "Laporkan penipuan transfer lewat aplikasi BRImo: Akun > Pusat Bantuan > Ajukan Pengaduan > Pelaporan Penipuan",
    },
    "bni": {"nama": "Bank BNI", "telepon": "1500046 (BNI Call)", "website": "bni.co.id"},
    "mandiri": {"nama": "Bank Mandiri", "telepon": "14000 (Mandiri Call)", "website": "bankmandiri.co.id"},
    "shopee": {
        "nama": "Shopee", "telepon": "1500702", "email": "help@support.shopee.com",
        "catatan": "Gunakan fitur 'Laporkan Pengguna' di aplikasi untuk akun/toko mencurigakan",
    },
    "tokopedia": {
        "nama": "Tokopedia", "website": "care.tokopedia.com",
        "catatan": "Hubungi lewat fitur Tokopedia Care di aplikasi atau care.tokopedia.com",
    },
}

# Saluran pelaporan resmi pemerintah
GENERAL_REPORTING_CHANNELS = {
    "cek_rekening": {
        "nama": "CekRekening.id (Kementerian Komdigi)", "website": "cekrekening.id",
        "catatan": "Cek atau laporkan nomor rekening/e-wallet yang diduga penipuan, sebelum atau sesudah transfer",
    },
    "patroli_siber": {
        "nama": "Patroli Siber (Kominfo/BSSN)", "website": "patrolisiber.id",
        "catatan": "Laporkan kejahatan siber secara umum",
    },
}


IMAGE_CONTENT_MARKER = "[Isi gambar yang diunggah pengguna]:"

CHATBOT_SYSTEM_PROMPT = f"""Kamu adalah FamilySecure Assistant, asisten literasi keamanan digital yang ramah dan sabar.
Tugasmu membantu keluarga Indonesia, terutama orang tua dan lansia, memahami ancaman digital dan cara melindungi diri.
Pengguna bisa mengetik pesan, mengunggah foto/screenshot, atau keduanya sekaligus dalam satu percakapan.

Kamu punya tiga tool:
- cari_skenario_penipuan: gunakan setiap kali pengguna menceritakan atau menanyakan pesan/situasi yang
  terdengar mencurigakan, untuk mengecek apakah itu cocok dengan modus penipuan yang diketahui. Jangan
  panggil untuk obrolan biasa yang tidak menyinggung situasi mencurigakan.
- cari_kontak_resmi: gunakan setelah mengidentifikasi modus penipuan yang melibatkan institusi tertentu
  (bank/e-commerce) ATAU pengguna sudah terlanjur dirugikan, untuk memberi saluran pelaporan/verifikasi
  yang BENAR-BENAR resmi — jangan pernah menyarankan nomor/link dari pesan yang sedang dicurigai.
- rekomendasikan_kuis: gunakan setelah kamu berhasil mengidentifikasi kategori modus penipuan yang jelas
  dari cari_skenario_penipuan, untuk menyarankan kuis terkait ke pengguna.

PENTING — jika pesan diawali "{IMAGE_CONTENT_MARKER}", itu adalah hasil pembacaan foto yang baru saja
diunggah pengguna untuk diperiksa. Untuk kasus ini, SELALU panggil cari_skenario_penipuan lebih dulu —
ini wajib, jangan langsung menjawab tanpa memeriksanya. Untuk pesan teks biasa tanpa penanda ini, panggil
tool hanya kalau memang menyinggung situasi mencurigakan.

CARA MENJAWAB:
- Bahasa Indonesia yang santun, hangat, dan mudah dimengerti oleh lansia.
- Hindari istilah teknis berlebihan (misalnya "phishing", "malware"). Jelaskan dengan bahasa awam.
- Maksimal 3-4 paragraf per jawaban, padat dan langsung ke inti.
- Kalau relevan, sebutkan kontak resmi dari cari_kontak_resmi secara konkret (nomor/website), jangan
  cuma bilang "hubungi bank Anda" tanpa detail.
- Jika ada pertanyaan di luar keamanan digital, balas dengan sopan bahwa kamu khusus di bidang ini.
- Akhiri dengan satu kalimat dorongan atau pengingat singkat."""


def cari_skenario_penipuan(kata_kunci: str) -> dict:
    """Mencari skenario penipuan yang cocok di database berdasarkan isi pesan yang dicurigai.

    Args:
        kata_kunci: Ringkasan atau kutipan pesan yang ingin dicek kecocokannya dengan modus
            penipuan yang sudah diketahui (contoh: file APK, link phishing, permintaan OTP).

    Returns:
        Dictionary berisi "ditemukan": True beserta judul, deskripsi, ciri-ciri, dan saran
        tindakan jika ada modus yang cocok, atau {"ditemukan": False} jika tidak ada yang cocok.
    """
    result = query_rag(kata_kunci)
    if not result:
        return {"ditemukan": False}
    return {
        "ditemukan": True,
        "judul": result["title"],
        "deskripsi": result["description"],
        "ciri_ciri": result.get("red_flags", []),
        "saran_tindakan": result["action"],
        "kategori_topik_kuis": result["category"],
    }


def cari_kontak_resmi(nama_institusi: str) -> dict:
    """Mencari kontak resmi (telepon/website) bank atau e-commerce yang SUDAH TERVERIFIKASI,
    untuk diarahkan ke pengguna sebagai saluran pelaporan/verifikasi yang aman.

    PENTING: nomor/link dari pesan yang sedang dicurigai TIDAK BOLEH pernah dipakai atau
    disarankan — hanya kontak yang dikembalikan tool ini yang aman direferensikan.

    Args:
        nama_institusi: nama bank/platform yang disebut pengguna. Gunakan salah satu kunci
            berikut jika cocok: "bca", "bri", "bni", "mandiri", "shopee", "tokopedia".
            Jika situasi tidak menyebut institusi spesifik (mis. modus sosial seperti
            "keluarga minta bantuan"), atau institusinya tidak ada di daftar itu, gunakan
            "umum" untuk mendapatkan saluran pelaporan resmi pemerintah yang berlaku umum.

    Returns:
        Dictionary "ditemukan": True beserta info kontak resmi jika ada di daftar
        terverifikasi, atau {"ditemukan": False} jika institusi tidak dikenali — dalam
        kasus ini JANGAN mengarang kontak, cukup sarankan pengguna memakai nomor yang
        tertera di kartu ATM atau aplikasi resmi mereka sendiri.
    """
    key = nama_institusi.strip().lower()
    if key in OFFICIAL_CONTACTS:
        return {"ditemukan": True, **OFFICIAL_CONTACTS[key]}
    if key in ("umum", "lainnya", "general", ""):
        return {"ditemukan": True, "nama": "Saluran Pelaporan Resmi Pemerintah", "saluran": GENERAL_REPORTING_CHANNELS}
    return {"ditemukan": False}


def rekomendasikan_kuis(topik: str) -> dict:
    """Mengambil info kuis edukasi yang tersedia untuk kategori modus penipuan tertentu.

    Args:
        topik: Kunci kategori topik. Gunakan "apk" untuk modus file/APK berbahaya, atau
            "link" untuk modus link palsu/petugas palsu. Kategori lain (mis. "sosial")
            belum memiliki kuis, jangan dipanggil untuk topik tersebut.

    Returns:
        Dictionary berisi "ditemukan": True beserta kunci topik dan judul kuis jika topik
        valid dan tersedia, atau {"ditemukan": False} jika topik tidak dikenali/tidak tersedia.
    """
    if topik in QUIZ_BANK:
        return {"ditemukan": True, "topik_key": topik, "judul_kuis": QUIZ_BANK[topik]["title"]}
    return {"ditemukan": False}


def _extract_tool_results(response) -> dict:
    matched_scenario = None
    suggested_quiz = None
    official_contact = None

    history = getattr(response, "automatic_function_calling_history", None) or []
    for content in history:
        for part in (content.parts or []):
            fr = getattr(part, "function_response", None)
            if fr is None:
                continue
            resp = (fr.response or {}).get("result") or {}
            if fr.name == "cari_skenario_penipuan" and resp.get("ditemukan"):
                matched_scenario = {
                    "title": resp.get("judul"),
                    "description": resp.get("deskripsi"),
                    "action": resp.get("saran_tindakan"),
                    "category": resp.get("kategori_topik_kuis"),
                }
            elif fr.name == "rekomendasikan_kuis" and resp.get("ditemukan"):
                suggested_quiz = {"topic_key": resp.get("topik_key"), "title": resp.get("judul_kuis")}
            elif fr.name == "cari_kontak_resmi" and resp.get("ditemukan"):
                official_contact = {k: v for k, v in resp.items() if k != "ditemukan"}

    return {"matched_scenario": matched_scenario, "suggested_quiz": suggested_quiz, "official_contact": official_contact}


def run_scam_agent(system_instruction: str, user_message: str, history: list | None = None) -> dict:
    api_key = _get_gemini_key()
    if not GEMINI_LIB_AVAILABLE or not api_key:
        raise AIServiceError("Layanan agent belum dikonfigurasi (GEMINI_API_KEY kosong).")

    from google.genai import types

    contents = []
    for msg in (history or [])[-8:]:
        role = "user" if msg.get("role") == "user" else "model"
        contents.append({"role": role, "parts": [{"text": msg.get("content", "")}]})
    contents.append({"role": "user", "parts": [{"text": user_message}]})

    client = genai_client.Client(api_key=api_key)
    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        tools=[cari_skenario_penipuan, cari_kontak_resmi, rekomendasikan_kuis],
        automatic_function_calling=types.AutomaticFunctionCallingConfig(maximum_remote_calls=4),
        temperature=0.3,
        max_output_tokens=500,
    )

    last_error = None
    for attempt in range(1, _MAX_ATTEMPTS + 1):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=contents,
                config=config,
            )
            reply = response.text.strip() if response and response.text else ""
            if not reply:
                raise AIServiceError("Agent mengembalikan respons kosong (kemungkinan diblokir filter keamanan).")
            result = _extract_tool_results(response)
            result["reply"] = reply
            return result
        except Exception as e:
            last_error = e
            logger.error(f"Error agent Gemini (percobaan {attempt}/{_MAX_ATTEMPTS}): {e}")
            if attempt < _MAX_ATTEMPTS:
                time.sleep(_RETRY_DELAY_SECONDS)

    raise AIServiceError(f"Agent gagal merespons setelah {_MAX_ATTEMPTS} percobaan: {last_error}")
