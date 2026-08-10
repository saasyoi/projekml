import os
import time
import logging

logger = logging.getLogger("familysecure_backend")


class AIServiceError(Exception):
    pass


_MAX_ATTEMPTS = 2
_RETRY_DELAY_SECONDS = 1.5

try:
    from google import genai as genai_client
    GEMINI_LIB_AVAILABLE = True
except ImportError:
    GEMINI_LIB_AVAILABLE = False
    logger.warning("Library 'google-genai' tidak ditemukan. Fitur AI tidak aktif.")

def _get_gemini_key() -> str:
    return os.environ.get("GEMINI_API_KEY", "")


NO_TEXT_SIGNAL = "NO_TEXT_FOUND"


def analyze_image_with_gemini(image_bytes: bytes) -> str:
    api_key = _get_gemini_key()
    if not GEMINI_LIB_AVAILABLE or not api_key:
        raise AIServiceError("Layanan analisis gambar belum dikonfigurasi (GEMINI_API_KEY kosong).")

    from google.genai import types
    client = genai_client.Client(api_key=api_key)

    last_error = None
    for attempt in range(1, _MAX_ATTEMPTS + 1):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    "Kamu adalah asisten pengidentifikasi penipuan (scam) untuk keluarga Indonesia.\n"
                    "Tugasmu HANYA menganalisis gambar yang berisi teks percakapan atau SMS.\n\n"
                    "LANGKAH 1: Periksa apakah gambar ini berisi teks percakapan, SMS, WhatsApp, email, "
                    "notifikasi, atau pesan teks apapun.\n"
                    "- Jika TIDAK ada teks percakapan (misalnya: foto orang, pemandangan, makanan, selfie, dll), "
                    "balas hanya dengan satu kata persis: NO_TEXT_FOUND\n"
                    "- Jika ADA teks percakapan, tuliskan ulang teks pentingnya, lalu identifikasi apakah ada "
                    "ciri-ciri penipuan (file .apk, permintaan OTP, ancaman blokir rekening, link mencurigakan, "
                    "klaim hadiah, dll). Jangan berikan saran, cukup laporkan temuan secara ringkas dalam Bahasa Indonesia.",
                    types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"),
                ],
                config={"temperature": 0},
            )
            text = response.text.strip() if response and response.text else ""
            if not text:
                raise AIServiceError("Model AI mengembalikan respons kosong (kemungkinan diblokir filter keamanan).")
            return text
        except Exception as e:
            last_error = e
            logger.error(f"Error Gemini (analisis gambar, percobaan {attempt}/{_MAX_ATTEMPTS}): {e}")
            if attempt < _MAX_ATTEMPTS:
                time.sleep(_RETRY_DELAY_SECONDS)

    raise AIServiceError(f"Analisis gambar gagal setelah {_MAX_ATTEMPTS} percobaan: {last_error}")
