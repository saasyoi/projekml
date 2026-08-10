"""
=================================================================================
BOT TELEGRAM "ASISTEN LITERASI KEAMANAN DIGITAL KELUARGA"
=================================================================================
Dibuat untuk mahasiswa Rekayasa Kriptografi / Secure Software Development.

Fokus desain:
1. Zero-Typing Interaction  -> semua navigasi utama pakai InlineKeyboardMarkup
2. Visual Hierarchy         -> MarkdownV2 + emoji penanda + paragraf pendek
3. Warm & Panic-Free Tone   -> bahasa santun, tanpa jargon teknis
4. Meaningful Gamification  -> scaffolding kuis (unlock 80%), badge keluarga

Dependensi (install dulu sebelum run):
    pip install python-telegram-bot==21.* requests google-generativeai chromadb

Environment variables yang perlu diset (jangan hardcode token di kode!):
    TELEGRAM_BOT_TOKEN   -> token dari @BotFather
    DEEPSEEK_API_KEY     -> untuk triase teks hemat biaya (DeepSeek V3.2)
    GEMINI_API_KEY       -> untuk OCR/vision screenshot (Gemini Pro Vision)

Cara jalan:
    export TELEGRAM_BOT_TOKEN="xxxx"
    export DEEPSEEK_API_KEY="xxxx"
    export GEMINI_API_KEY="xxxx"
    python bot.py
=================================================================================
"""

import os
import re
import json
import logging
import logging.handlers
import io
import time
from datetime import datetime

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# ---------------------------------------------------------------------------
# Dependensi opsional (AI & RAG). Dibungkus try/except supaya bot TETAP BISA
# JALAN (mode demo/tanpa API key) walaupun library/koneksi belum siap.
# Ini penting untuk mahasiswa yang mungkin belum sempat setup semua API.
# ---------------------------------------------------------------------------
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

try:
    from google import genai as genai_client  # SDK baru (google-genai), pengganti google-generativeai yg sudah deprecated
    GEMINI_LIB_AVAILABLE = True
except ImportError:
    GEMINI_LIB_AVAILABLE = False

try:
    import chromadb
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False


# =================================================================================
# 1. KONFIGURASI & INISIALISASI
# =================================================================================

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

logger = logging.getLogger("asisten_literasi_keluarga")
logger.setLevel(logging.INFO)

# Handler 1: tampil di terminal (buat development)
_console_handler = logging.StreamHandler()
_console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
logger.addHandler(_console_handler)

# Handler 2: simpan ke file dengan rotasi otomatis (maks 5MB x 5 file backup)
# Supaya kalau bot dipakai publik, kamu tetap bisa audit error yang terjadi
# semalam tanpa harus terus buka terminal.
_file_handler = logging.handlers.RotatingFileHandler(
    os.path.join(LOG_DIR, "bot.log"), maxBytes=5 * 1024 * 1024, backupCount=5, encoding="utf-8"
)
_file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
logger.addHandler(_file_handler)

# --- Token & API Key (ambil dari environment variable, JANGAN hardcode) ---
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# Endpoint & nama model. DeepSeek pakai skema kompatibel OpenAI.
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"
DEEPSEEK_MODEL_NAME = "deepseek-chat"          # sesuaikan dgn versi V3.2 yg tersedia di akun

# Catatan: cek nama model Gemini Vision terbaru di dokumentasi resmi Google AI
# sebelum deploy, karena penamaan model bisa berubah.
GEMINI_MODEL_NAME = "gemini-2.0-flash"

# --- File penyimpanan state gamifikasi (mock "database" lokal berbasis JSON) ---
DB_FILE = "user_data.json"

# --- Ambang kelulusan kuis untuk membuka level berikutnya ---
PASSING_SCORE_PERCENT = 80

# --- Rate limiting untuk fitur cek gambar (mencegah 1 orang spam & jebol kuota API) ---
RATE_LIMIT_MAX_PHOTOS = 5       # maksimal 5 kali cek foto...
RATE_LIMIT_WINDOW_SECONDS = 600  # ...per 10 menit, per pengguna

# Menyimpan riwayat waktu request foto tiap user (in-memory, cukup untuk skala kecil-menengah)
_photo_request_log: dict[int, list[float]] = {}


def is_rate_limited(user_id: int) -> bool:
    """
    Mengecek apakah pengguna sudah melebihi batas jumlah cek foto dalam jendela waktu tertentu.
    Ini mencegah satu pengguna (sengaja/tidak sengaja) menghabiskan kuota API Gemini/DeepSeek
    yang berdampak ke SEMUA pengguna lain.
    """
    now = time.time()
    history = _photo_request_log.get(user_id, [])
    # Buang catatan yang sudah di luar jendela waktu
    history = [t for t in history if now - t < RATE_LIMIT_WINDOW_SECONDS]
    _photo_request_log[user_id] = history
    return len(history) >= RATE_LIMIT_MAX_PHOTOS


def record_photo_request(user_id: int) -> None:
    """Mencatat satu kali permintaan cek foto untuk keperluan rate limiting."""
    _photo_request_log.setdefault(user_id, []).append(time.time())


def call_with_retry(func, *args, max_retries: int = 2, backoff_seconds: float = 1.5, **kwargs):
    """
    Menjalankan sebuah fungsi dengan retry otomatis jika terjadi exception.
    Berguna untuk memanggil API eksternal (Gemini/DeepSeek) yang kadang gagal
    sesaat karena jaringan tidak stabil, bukan karena error permanen.
    Delay antar percobaan naik bertahap (1.5s, 3s, ...) agar tidak membombardir API.
    """
    last_error = None
    for attempt in range(1, max_retries + 2):  # +1 percobaan awal + max_retries pengulangan
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_error = e
            if attempt <= max_retries:
                logger.warning(f"Percobaan {attempt} gagal ({func.__name__}): {e}. Mencoba lagi...")
                time.sleep(backoff_seconds * attempt)
            else:
                logger.error(f"Semua percobaan gagal untuk {func.__name__}: {e}")
    raise last_error


# =================================================================================
# 2. UTILITAS: MARKDOWNV2 ESCAPE (wajib, kalau tidak bot akan error/crash)
# =================================================================================

_MDV2_SPECIAL_CHARS = r"_*[]()~`>#+-=|{}.!"


def escape_md(text: str) -> str:
    """
    Meng-escape karakter spesial MarkdownV2 Telegram agar teks dinamis
    (nama pengguna, skor, hasil AI, dsb) tidak membuat pesan gagal terkirim.
    """
    if text is None:
        return ""
    text = str(text)
    for ch in _MDV2_SPECIAL_CHARS:
        text = text.replace(ch, "\\" + ch)
    return text


async def safe_reply(update_or_query, text, reply_markup=None):
    """
    Wrapper aman untuk mengirim/mengedit pesan dengan MarkdownV2.
    Kalau parsing markdown gagal (mis. ada karakter yg lolos escape),
    bot akan fallback ke plain text supaya TIDAK CRASH di depan pengguna.
    """
    try:
        if hasattr(update_or_query, "message") and update_or_query.message:
            await update_or_query.message.reply_text(
                text, parse_mode=ParseMode.MARKDOWN_V2, reply_markup=reply_markup
            )
        else:
            await update_or_query.edit_message_text(
                text, parse_mode=ParseMode.MARKDOWN_V2, reply_markup=reply_markup
            )
    except Exception as e:
        logger.warning(f"Gagal kirim dgn MarkdownV2, fallback ke plain text: {e}")
        plain = re.sub(r"\\(.)", r"\1", text)  # buang backslash escape
        try:
            if hasattr(update_or_query, "message") and update_or_query.message:
                await update_or_query.message.reply_text(plain, reply_markup=reply_markup)
            else:
                await update_or_query.edit_message_text(plain, reply_markup=reply_markup)
        except Exception as e2:
            logger.error(f"Gagal total mengirim pesan: {e2}")


# =================================================================================
# 3. GAMIFIKASI: "DATABASE" JSON LOKAL (skor, badge, progres unlock)
# =================================================================================

def _default_user_record(name: str = "") -> dict:
    """Struktur default satu pengguna baru."""
    return {
        "name": name,
        "total_score": 0,
        "badges": [],
        "progress": {
            "apk": {
                "dasar": {"attempts": 0, "best_score": 0, "passed": False},
                "lanjutan": {"attempts": 0, "best_score": 0, "passed": False},
            },
            "link": {
                "dasar": {"attempts": 0, "best_score": 0, "passed": False},
                "lanjutan": {"attempts": 0, "best_score": 0, "passed": False},
            },
        },
    }


def load_db() -> dict:
    """Membaca file JSON. Aman terhadap file rusak/tidak ada/kosong."""
    if not os.path.exists(DB_FILE):
        return {}
    try:
        with open(DB_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return {}
            return json.loads(content)
    except (json.JSONDecodeError, OSError) as e:
        logger.error(f"user_data.json rusak, membuat backup & reset. Detail: {e}")
        try:
            os.rename(DB_FILE, DB_FILE + ".corrupt_backup")
        except OSError:
            pass
        return {}


def save_db(db: dict) -> None:
    """Menulis file JSON dengan aman (tulis ke file sementara dulu)."""
    tmp_file = DB_FILE + ".tmp"
    try:
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(db, f, ensure_ascii=False, indent=2)
        os.replace(tmp_file, DB_FILE)
    except OSError as e:
        logger.error(f"Gagal menyimpan database pengguna: {e}")


def get_user(db: dict, user_id: int, name: str = "") -> dict:
    """Mengambil record pengguna, membuat baru jika belum ada."""
    key = str(user_id)
    if key not in db:
        db[key] = _default_user_record(name)
    elif name and not db[key].get("name"):
        db[key]["name"] = name
    return db[key]


def is_level_unlocked(user_record: dict, topic: str, level: str) -> bool:
    """Level 'dasar' selalu terbuka. Level 'lanjutan' butuh 'dasar' lulus >=80%."""
    if level == "dasar":
        return True
    return user_record["progress"][topic]["dasar"]["passed"]


# =================================================================================
# 4. SIMULASI RAG LOKAL: DATABASE SKENARIO PENIPUAN (mock, dipakai ChromaDB)
# =================================================================================

SCAM_DATABASE = [
    {
        "id": "apk_kurir",
        "title": "Modus File Kiriman Kurir Palsu",
        "category": "apk",
        "description": (
            "Pesan mengaku dari kurir ekspedisi (JNE, J&T, SiCepat, dll) meminta korban "
            "membuka dan memasang file berekstensi .apk untuk melihat 'foto paket' atau "
            "'surat tilang'. File ini sebenarnya program jahat yang bisa membaca SMS OTP, "
            "kontak, dan menguras rekening korban."
        ),
        "red_flags": [
            "Ada file berakhiran .apk dikirim lewat WhatsApp",
            "Diminta install aplikasi di luar Play Store",
            "Ada paksaan buru-buru buka filenya",
        ],
        "action": (
            "Jangan pernah install file .apk yang dikirim orang tak dikenal lewat chat ya, "
            "Pak/Bu. Langsung hapus pesannya, dan tekan tombol Blokir + Laporkan di WhatsApp."
        ),
    },
    {
        "id": "undangan_pernikahan",
        "title": "Modus Undangan Pernikahan Digital Palsu",
        "category": "apk",
        "description": (
            "Pesan berisi link atau file .apk yang disamarkan sebagai 'undangan pernikahan "
            "digital'. Begitu dibuka/instal, aplikasi tersebut diam-diam mencuri data pribadi "
            "dan mengakses SMS untuk membajak akun perbankan atau m-banking korban."
        ),
        "red_flags": [
            "Pengirim tidak dikenal, tapi mengaku 'teman lama' atau 'saudara'",
            "Undangan berbentuk file, bukan link ke Instagram/website resmi",
            "Diminta 'klik dan install agar bisa lihat undangannya'",
        ],
        "action": (
            "Undangan pernikahan asli tidak pernah berbentuk file .apk, Pak/Bu. Kalau ragu, "
            "jangan dibuka. Langsung hapus saja pesannya, aman lebih penting daripada sungkan."
        ),
    },
    {
        "id": "cs_bank_palsu",
        "title": "Modus Petugas Customer Service Bank Palsu",
        "category": "link",
        "description": (
            "Seseorang menghubungi lewat telepon/chat mengaku petugas bank, menyampaikan akun "
            "korban 'bermasalah' atau 'kena upgrade', lalu mengarahkan ke sebuah link untuk "
            "mengisi data kartu, PIN, atau kode OTP. Link tersebut sebenarnya halaman tiruan "
            "untuk mencuri data perbankan."
        ),
        "red_flags": [
            "Diminta memberi kode OTP/PIN lewat telepon atau chat",
            "Link yang dikirim mirip nama bank tapi alamatnya aneh",
            "Ada tekanan waktu ('harus sekarang atau rekening diblokir')",
        ],
        "action": (
            "Bank asli TIDAK PERNAH meminta kode OTP atau PIN lewat telepon/chat, Pak/Bu. "
            "Tutup saja teleponnya, dan kalau mau memastikan, hubungi call center resmi bank "
            "dari nomor yang tertera di kartu ATM atau aplikasi resminya."
        ),
    },
]

_rag_collection = None  # akan diisi saat init_rag() dipanggil


def init_rag():
    """
    Inisialisasi 'RAG sederhana' memakai ChromaDB in-memory.
    Jika ChromaDB tidak tersedia, sistem otomatis pakai fallback keyword-matching
    supaya bot tetap bisa merespons walau tanpa vector database.
    """
    global _rag_collection
    if not CHROMADB_AVAILABLE:
        logger.warning("ChromaDB tidak terpasang, memakai fallback pencarian kata kunci.")
        return
    try:
        client = chromadb.Client()  # in-memory, cocok untuk demo/skala kecil
        collection = client.get_or_create_collection(name="scam_scenarios")
        collection.add(
            ids=[item["id"] for item in SCAM_DATABASE],
            documents=[item["description"] for item in SCAM_DATABASE],
            metadatas=[
                {"title": item["title"], "category": item["category"]}
                for item in SCAM_DATABASE
            ],
        )
        _rag_collection = collection
        logger.info("RAG (ChromaDB in-memory) berhasil diinisialisasi.")
    except Exception as e:
        logger.error(f"Gagal inisialisasi ChromaDB, fallback ke keyword search: {e}")
        _rag_collection = None


def query_rag(text: str) -> dict:
    """
    Mencari skenario penipuan paling relevan berdasarkan teks hasil OCR/ekstraksi.
    Mengembalikan salah satu entri SCAM_DATABASE (dict), atau None jika tidak ada teks.
    """
    if not text:
        return None

    if _rag_collection is not None:
        try:
            result = _rag_collection.query(query_texts=[text], n_results=1)
            if result and result.get("ids") and result["ids"][0]:
                matched_id = result["ids"][0][0]
                for item in SCAM_DATABASE:
                    if item["id"] == matched_id:
                        return item
        except Exception as e:
            logger.error(f"Query ChromaDB gagal, fallback keyword search: {e}")

    # --- Fallback sederhana: keyword overlap scoring ---
    text_lower = text.lower()
    best_match, best_score = None, 0
    for item in SCAM_DATABASE:
        score = sum(1 for word in item["description"].lower().split() if word in text_lower)
        score += sum(3 for flag in item["red_flags"] if any(w in text_lower for w in flag.lower().split()))
        if score > best_score:
            best_score, best_match = score, item
    return best_match


# =================================================================================
# 5. INTEGRASI AI: GEMINI VISION (OCR screenshot) & DEEPSEEK (triase teks)
# =================================================================================

def analyze_image_with_gemini(image_bytes: bytes) -> str:
    """
    Mengirim gambar ke Gemini Vision untuk diekstrak isi chat/SMS-nya.
    Mengembalikan teks hasil ekstraksi, atau string kosong jika gagal.
    """
    if not GEMINI_LIB_AVAILABLE or not GEMINI_API_KEY:
        logger.warning("Gemini belum dikonfigurasi, memakai mode demo (teks kosong).")
        return ""

    def _call():
        client = genai_client.Client(api_key=GEMINI_API_KEY)
        prompt = (
            "Ekstrak seluruh teks percakapan/SMS yang terlihat pada gambar screenshot ini. "
            "Tuliskan apa adanya tanpa komentar tambahan, fokus pada isi pesan dan nama pengirim."
        )
        response = client.models.generate_content(
            model=GEMINI_MODEL_NAME,
            contents=[
                prompt,
                {"inline_data": {"mime_type": "image/jpeg", "data": image_bytes}},
            ],
        )
        return (response.text or "").strip()

    try:
        # Retry otomatis 2x kalau gagal karena jaringan/quota sesaat (429, timeout, dsb)
        return call_with_retry(_call, max_retries=2, backoff_seconds=2.0)
    except Exception as e:
        logger.error(f"Gagal memproses gambar dengan Gemini setelah retry: {e}")
        return ""


def triage_text_with_deepseek(extracted_text: str, matched_scenario: dict) -> str:
    """
    Memakai DeepSeek (model hemat biaya) untuk menyusun penjelasan akhir yang
    ramah dan menenangkan berdasarkan teks hasil OCR + skenario RAG yang cocok.
    Jika API tidak tersedia, kembalikan penjelasan default dari database skenario.
    """
    default_explanation = (
        matched_scenario["action"] if matched_scenario else
        "Belum bisa memastikan jenis modusnya, tapi kalau ada permintaan mencurigakan "
        "sebaiknya jangan diklik atau ditanggapi dulu ya, Pak/Bu."
    )

    if not REQUESTS_AVAILABLE or not DEEPSEEK_API_KEY:
        logger.warning("DeepSeek belum dikonfigurasi, memakai penjelasan default.")
        return default_explanation

    system_prompt = (
        "Kamu adalah asisten keamanan digital keluarga yang sangat santun dan menenangkan. "
        "Balas dalam Bahasa Indonesia yang sederhana untuk orang tua/lansia. "
        "JANGAN memakai istilah teknis seperti 'phishing', 'malware', 'metadata', 'vector'. "
        "Langsung berikan penjelasan singkat kenapa ini berbahaya, dan instruksi tindakan "
        "konkret dalam 2-3 kalimat pendek. Gunakan sapaan 'Bapak/Ibu'."
    )
    user_prompt = (
        f"Isi pesan yang dicurigai:\n{extracted_text}\n\n"
        f"Referensi jenis modus yang mirip: {matched_scenario['title'] if matched_scenario else 'tidak diketahui'}"
    )

    try:
        response = requests.post(
            DEEPSEEK_API_URL,
            headers={
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "model": DEEPSEEK_MODEL_NAME,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "max_tokens": 300,
                "temperature": 0.4,
            },
            timeout=20,
        )
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"].strip()
        return content if content else default_explanation
    except Exception as e:
        logger.error(f"Gagal memanggil DeepSeek, memakai penjelasan default: {e}")
        return default_explanation


# =================================================================================
# 6. BANK SOAL KUIS (2 tingkat: dasar & lanjutan, per topik)
# =================================================================================

QUIZ_BANK = {
    "apk": {
        "title": "Modus File/APK Berbahaya",
        "dasar": [
            {
                "question": "Ibu menerima chat WhatsApp berisi file bernama 'Paket_Anda.apk' dari nomor tak dikenal. Apa yang sebaiknya dilakukan?",
                "options": {
                    "A": "Langsung buka dan instal filenya",
                    "B": "Hapus pesan tanpa membuka filenya",
                    "C": "Teruskan ke grup keluarga dulu",
                    "D": "Simpan filenya untuk dibuka nanti",
                },
                "correct": "B",
                "explanation": "Betul, file .apk dari orang tak dikenal sebaiknya langsung dihapus tanpa dibuka. Ini cara paling aman.",
            },
            {
                "question": "Kenapa file berekstensi .apk dari chat berbahaya untuk dipasang di HP?",
                "options": {
                    "A": "Karena bikin memori HP penuh saja",
                    "B": "Karena bisa mengambil alih SMS dan data pribadi",
                    "C": "Karena tampilannya jelek",
                    "D": "Karena tidak bisa dihapus",
                },
                "correct": "B",
                "explanation": "Tepat sekali. File semacam ini bisa diam-diam membaca SMS (termasuk kode OTP) dan data pribadi lainnya.",
            },
            {
                "question": "Bapak dapat pesan 'undangan pernikahan digital' berbentuk file yang harus diinstal. Apa tindakan paling aman?",
                "options": {
                    "A": "Instal saja, siapa tahu penting",
                    "B": "Tanya dulu ke pengirim by telepon",
                    "C": "Jangan diinstal, hapus pesannya",
                    "D": "Kirim ke teman untuk dicoba dulu",
                },
                "correct": "C",
                "explanation": "Benar. Undangan asli tidak pernah berbentuk file yang harus diinstal. Lebih aman langsung dihapus.",
            },
            {
                "question": "Setelah tidak sengaja memasang file mencurigakan, langkah pertama yang sebaiknya dilakukan adalah?",
                "options": {
                    "A": "Diamkan saja, mungkin tidak apa-apa",
                    "B": "Aktifkan mode pesawat lalu minta bantuan keluarga/ahli",
                    "C": "Restart HP berkali-kali",
                    "D": "Ganti nomor WhatsApp",
                },
                "correct": "B",
                "explanation": "Tepat. Mengaktifkan mode pesawat memutus akses internet aplikasi jahat, lalu segera minta bantuan orang yang paham teknologi.",
            },
        ],
        "lanjutan": [
            {
                "question": "Selain file .apk, cara lain modus penipu menyamarkan file berbahaya di WhatsApp adalah?",
                "options": {
                    "A": "Mengubah nama file jadi 'Foto.jpg.apk'",
                    "B": "Mengirim lewat kertas fisik",
                    "C": "Menelepon langsung tanpa file",
                    "D": "Mengirim melalui pos",
                },
                "correct": "A",
                "explanation": "Benar, penipu sering menyamarkan nama file agar terlihat seperti foto biasa, padahal tetap file aplikasi berbahaya.",
            },
            {
                "question": "Apa tanda tambahan bahwa sebuah file APK yang dikirim adalah bagian dari penipuan terorganisir?",
                "options": {
                    "A": "Dikirim satu per satu ke banyak nomor berbeda dengan pesan yang sama",
                    "B": "Dikirim oleh keluarga dekat yang sudah dikenal lama",
                    "C": "Ukuran filenya sangat kecil",
                    "D": "Filenya berwarna-warni",
                },
                "correct": "A",
                "explanation": "Tepat, pesan yang sama dikirim massal ke banyak nomor adalah ciri khas penipuan otomatis/terorganisir.",
            },
            {
                "question": "Jika HP keluarga sudah terlanjur terpasang aplikasi mencurigakan dan mulai ada transaksi aneh di rekening, urutan tindakan yang paling tepat adalah?",
                "options": {
                    "A": "Hubungi bank untuk blokir rekening, lalu hapus aplikasi & reset HP",
                    "B": "Tunggu beberapa hari untuk lihat perkembangan",
                    "C": "Ganti sim card saja",
                    "D": "Matikan HP selamanya",
                },
                "correct": "A",
                "explanation": "Benar, prioritas pertama adalah mengamankan rekening lewat bank, baru membersihkan HP dari aplikasi berbahaya.",
            },
            {
                "question": "Mengapa memasang aplikasi hanya dari Play Store/App Store resmi jauh lebih aman?",
                "options": {
                    "A": "Karena semua aplikasi di sana sudah melalui proses pemeriksaan keamanan",
                    "B": "Karena aplikasinya lebih murah",
                    "C": "Karena ukurannya lebih kecil",
                    "D": "Karena tidak perlu koneksi internet",
                },
                "correct": "A",
                "explanation": "Tepat, toko aplikasi resmi memiliki proses pemeriksaan yang membuat aplikasi berbahaya lebih sulit lolos dibanding file kiriman langsung.",
            },
        ],
    },
    "link": {
        "title": "Modus Link Palsu / Petugas Palsu",
        "dasar": [
            {
                "question": "Seseorang menelepon mengaku petugas bank dan meminta kode OTP yang baru saja Ibu terima. Apa yang harus dilakukan?",
                "options": {
                    "A": "Berikan kodenya karena mengaku petugas bank",
                    "B": "Tutup telepon, jangan berikan kode apapun",
                    "C": "Berikan sebagian kodenya saja",
                    "D": "Minta petugas menelepon ulang besok",
                },
                "correct": "B",
                "explanation": "Benar sekali. Kode OTP tidak boleh diberikan kepada siapa pun, termasuk yang mengaku petugas bank. Petugas bank asli tidak pernah memintanya.",
            },
            {
                "question": "Bapak menerima SMS berisi link untuk 'verifikasi akun bank agar tidak diblokir'. Tindakan paling aman adalah?",
                "options": {
                    "A": "Klik link dan isi datanya segera",
                    "B": "Abaikan/hapus SMS, dan cek langsung lewat aplikasi resmi bank",
                    "C": "Teruskan link ke keluarga untuk dicoba",
                    "D": "Simpan link untuk dibuka nanti",
                },
                "correct": "B",
                "explanation": "Tepat. Lebih aman mengecek langsung lewat aplikasi/website resmi bank daripada mengklik link dari SMS yang belum jelas asalnya.",
            },
            {
                "question": "Ciri khas nomor rekening/link palsu yang sering dipakai penipu adalah?",
                "options": {
                    "A": "Selalu memberi waktu berpikir yang lama",
                    "B": "Mendesak untuk bertindak cepat karena 'akun akan diblokir'",
                    "C": "Meminta bertemu langsung di kantor bank",
                    "D": "Tidak pernah menyebut nominal uang",
                },
                "correct": "B",
                "explanation": "Benar, tekanan waktu ('harus sekarang!') adalah taktik umum penipu supaya korban tidak sempat berpikir jernih.",
            },
            {
                "question": "Jika ragu apakah sebuah telepon dari 'bank' itu asli atau tidak, langkah paling aman adalah?",
                "options": {
                    "A": "Percaya saja karena terdengar meyakinkan",
                    "B": "Tutup telepon, lalu hubungi call center resmi dari nomor di kartu ATM",
                    "C": "Transfer sedikit uang dulu untuk tes",
                    "D": "Minta nomor pribadi si penelepon",
                },
                "correct": "B",
                "explanation": "Tepat sekali. Selalu verifikasi lewat nomor resmi yang tertera di kartu ATM atau aplikasi bank, bukan nomor yang diberikan penelepon.",
            },
        ],
        "lanjutan": [
            {
                "question": "Sebuah website tampilannya mirip persis web bank asli, tapi alamatnya sedikit berbeda (mis. tambahan huruf/angka aneh). Apa artinya?",
                "options": {
                    "A": "Website tersebut kemungkinan besar tiruan/palsu",
                    "B": "Itu wajar, bank sering berganti alamat",
                    "C": "Tidak masalah selama tampilannya bagus",
                    "D": "Itu tandanya sedang ada promo",
                },
                "correct": "A",
                "explanation": "Benar, perbedaan kecil pada alamat website adalah tanda umum situs tiruan yang dibuat mirip aslinya.",
            },
            {
                "question": "Selain telepon dan SMS, media apa lagi yang sering dipakai penipu 'CS bank palsu'?",
                "options": {
                    "A": "Chat WhatsApp/Telegram mengaku CS resmi",
                    "B": "Surat pos resmi dari bank",
                    "C": "Papan pengumuman di kantor bank",
                    "D": "Buku tabungan fisik",
                },
                "correct": "A",
                "explanation": "Tepat, penipu banyak memanfaatkan chat WhatsApp/Telegram karena mudah menyamar dengan foto profil dan nama mirip bank asli.",
            },
            {
                "question": "Kenapa penipu sering menggunakan nama 'resmi' seperti 'CS_BankXYZ_Official' pada akun chat mereka?",
                "options": {
                    "A": "Supaya terlihat meyakinkan dan dipercaya korban",
                    "B": "Karena itu peraturan dari bank",
                    "C": "Karena nama tersebut lebih mudah diingat",
                    "D": "Tidak ada tujuan khusus",
                },
                "correct": "A",
                "explanation": "Benar, nama yang terlihat resmi adalah trik agar korban lengah dan percaya tanpa memverifikasi lebih dulu.",
            },
            {
                "question": "Setelah keluarga menyadari sudah terlanjur mengisi data di link palsu, tindakan pertama yang paling tepat adalah?",
                "options": {
                    "A": "Segera hubungi bank untuk blokir/ganti akses & pantau mutasi rekening",
                    "B": "Tunggu beberapa minggu untuk melihat efeknya",
                    "C": "Hapus riwayat chat saja",
                    "D": "Tidak perlu tindakan apa-apa",
                },
                "correct": "A",
                "explanation": "Tepat sekali, semakin cepat menghubungi bank untuk mengamankan akun, semakin kecil kemungkinan kerugian yang terjadi.",
            },
        ],
    },
}

BADGE_MAP = {
    ("apk", "dasar"): "🛡️ Pemula Waspada Modus APK",
    ("apk", "lanjutan"): "🛡️ Pelindung Chat Keluarga (APK)",
    ("link", "dasar"): "🛡️ Pemula Waspada Link Palsu",
    ("link", "lanjutan"): "🛡️ Pelindung Chat Keluarga (Link)",
}


# =================================================================================
# 7. KEYBOARD BUILDERS (semua navigasi utama = tombol, bukan ketikan)
# =================================================================================

def kb_main_menu() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton("🔍 Cek Pesan/Chat Mencurigakan", callback_data="menu_cek")],
        [InlineKeyboardButton("🎮 Mulai Kuis Keamanan", callback_data="menu_kuis")],
        [InlineKeyboardButton("🏆 Lihat Skor & Lencana Saya", callback_data="menu_skor")],
        [InlineKeyboardButton("❓ Bantuan", callback_data="menu_bantuan")],
    ]
    return InlineKeyboardMarkup(buttons)


def kb_back_to_menu() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Kembali ke Menu Utama", callback_data="back_menu")]])


def kb_topic_selection() -> InlineKeyboardMarkup:
    buttons = []
    for topic_key, topic_data in QUIZ_BANK.items():
        buttons.append([InlineKeyboardButton(f"📘 {topic_data['title']}", callback_data=f"topic_{topic_key}")])
    buttons.append([InlineKeyboardButton("⬅️ Kembali ke Menu Utama", callback_data="back_menu")])
    return InlineKeyboardMarkup(buttons)


def kb_level_selection(topic: str, user_record: dict) -> InlineKeyboardMarkup:
    dasar_label = "📗 Level Dasar"
    lanjutan_unlocked = is_level_unlocked(user_record, topic, "lanjutan")
    lanjutan_label = "📙 Level Lanjutan" if lanjutan_unlocked else "🔒 Level Lanjutan (selesaikan Dasar dulu)"

    buttons = [
        [InlineKeyboardButton(dasar_label, callback_data=f"level_{topic}_dasar")],
        [InlineKeyboardButton(
            lanjutan_label,
            callback_data=f"level_{topic}_lanjutan" if lanjutan_unlocked else "locked_level",
        )],
        [InlineKeyboardButton("⬅️ Pilih Topik Lain", callback_data="menu_kuis")],
    ]
    return InlineKeyboardMarkup(buttons)


def kb_answer_options(topic: str, level: str, index: int) -> InlineKeyboardMarkup:
    question = QUIZ_BANK[topic][level][index]
    buttons = []
    for letter, option_text in question["options"].items():
        label = f"{letter}. {option_text}"
        buttons.append([InlineKeyboardButton(label, callback_data=f"answer_{topic}_{level}_{index}_{letter}")])
    return InlineKeyboardMarkup(buttons)


def kb_next_question(topic: str, level: str, next_index: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("➡️ Lanjut ke Soal Berikutnya", callback_data=f"next_{topic}_{level}_{next_index}")]])


def kb_after_quiz() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton("🎮 Pilih Topik/Level Lain", callback_data="menu_kuis")],
        [InlineKeyboardButton("⬅️ Kembali ke Menu Utama", callback_data="back_menu")],
    ]
    return InlineKeyboardMarkup(buttons)


# =================================================================================
# 8. HANDLER: /start (Welcome Layout)
# =================================================================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Menampilkan salam pembuka hangat + menu utama berupa tombol."""
    user = update.effective_user
    db = load_db()
    get_user(db, user.id, name=user.first_name or "")
    save_db(db)

    nama = escape_md(user.first_name or "Bapak/Ibu")
    text = (
        f"Halo, {nama}\\! 👋\n\n"
        "Selamat datang di *Asisten Literasi Keamanan Digital Keluarga* 🛡️\n\n"
        "Saya di sini untuk membantu Bapak/Ibu mengenali dan menghindari "
        "penipuan digital yang sering menyasar keluarga kita, dengan cara "
        "yang mudah dan tidak bikin bingung\\.\n\n"
        "Cara pakainya gampang, tinggal pilih tombol di bawah ya, tidak perlu "
        "mengetik apa\\-apa 😊\n\n"
        "🔍 *Cek Pesan/Chat Mencurigakan* — kirim screenshot, saya periksakan\n"
        "🎮 *Mulai Kuis Keamanan* — belajar sambil main, dapat lencana\n"
        "🏆 *Lihat Skor & Lencana* — pantau progres belajar keluarga\n"
        "❓ *Bantuan* — kalau butuh penjelasan lagi\n\n"
        "Silakan pilih menu di bawah ini, Bapak/Ibu 👇"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN_V2, reply_markup=kb_main_menu())


# =================================================================================
# 9. HANDLER: MENU UTAMA (callback query router)
# =================================================================================

async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Router utama untuk semua tombol inline (menu, kuis, skor, bantuan)."""
    query = update.callback_query
    await query.answer()  # wajib, supaya tombol tidak terasa 'macet' di HP pengguna
    data = query.data
    user = update.effective_user

    try:
        if data == "back_menu":
            await show_main_menu(query, user)

        elif data == "menu_cek":
            await handle_menu_cek(query)

        elif data == "menu_kuis":
            await handle_menu_kuis(query)

        elif data == "menu_skor":
            await handle_menu_skor(query, user)

        elif data == "menu_bantuan":
            await handle_menu_bantuan(query)

        elif data == "locked_level":
            await query.answer(
                "Selesaikan dulu Level Dasar dengan nilai minimal 80, ya, supaya makin mantap dasarnya 💪",
                show_alert=True,
            )

        elif data.startswith("topic_"):
            topic = data.replace("topic_", "")
            await handle_topic_selected(query, user, topic)

        elif data.startswith("level_"):
            _, topic, level = data.split("_", 2)
            await start_quiz(query, context, topic, level)

        elif data.startswith("answer_"):
            _, topic, level, index_str, letter = data.split("_", 4)
            await handle_quiz_answer(query, context, user, topic, level, int(index_str), letter)

        elif data.startswith("next_"):
            _, topic, level, index_str = data.split("_", 3)
            await show_quiz_question(query, context, topic, level, int(index_str))

        else:
            logger.warning(f"Callback data tidak dikenali: {data}")

    except Exception as e:
        logger.error(f"Terjadi kesalahan pada menu_callback: {e}")
        await safe_reply(
            query,
            "Maaf ya, sepertinya ada sedikit kendala di sistem\\. Silakan coba tekan tombol menu di bawah lagi 🙏",
            reply_markup=kb_back_to_menu(),
        )


async def show_main_menu(query, user) -> None:
    nama = escape_md(user.first_name or "Bapak/Ibu")
    text = f"Baik, {nama}\\. Silakan pilih menu di bawah ini ya 👇"
    await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN_V2, reply_markup=kb_main_menu())


# =================================================================================
# 10. HANDLER: CEK PESAN MENCURIGAKAN (memandu user kirim screenshot)
# =================================================================================

async def handle_menu_cek(query) -> None:
    text = (
        "🔍 *Cek Pesan/Chat Mencurigakan*\n\n"
        "Silakan kirimkan *foto screenshot* dari chat, SMS, atau email yang "
        "membuat Bapak/Ibu merasa curiga ke sini ya\\.\n\n"
        "💡 Saya akan periksakan dulu, nanti hasilnya saya kirim dengan "
        "penjelasan sederhana dan langkah yang perlu dilakukan\\.\n\n"
        "Tidak perlu buru\\-buru, kirim saja fotonya kapan pun siap 😊"
    )
    await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN_V2, reply_markup=kb_back_to_menu())


async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Menangani screenshot yang dikirim pengguna:
    1) Unduh foto -> 2) OCR via Gemini Vision -> 3) Cari skenario mirip via RAG
    -> 4) Susun penjelasan ramah via DeepSeek -> 5) Balas terstruktur.
    Semua langkah dibungkus try/except agar TIDAK CRASH walau ada kegagalan API.

    CATATAN PRIVASI (penting untuk kepercayaan pengguna keluarga):
    Foto TIDAK PERNAH ditulis ke disk (tidak ada file yang tersimpan permanen).
    Byte gambar hanya ada di memori selama proses berjalan, lalu langsung
    dibuang begitu selesai diproses (lihat blok `finally` di bawah).
    """
    processing_msg = None
    image_bytes = None
    user_id = update.effective_user.id

    # --- Rate limiting: cegah 1 pengguna menghabiskan kuota API untuk semua orang ---
    if is_rate_limited(user_id):
        await update.message.reply_text(
            "Mohon maaf, Bapak/Ibu 🙏 Sudah beberapa kali memeriksa foto dalam waktu dekat ini\\.\n\n"
            "Untuk menjaga layanan tetap lancar bagi semua pengguna, mohon tunggu beberapa "
            "menit lagi sebelum mengirim foto berikutnya ya 😊",
            parse_mode=ParseMode.MARKDOWN_V2,
            reply_markup=kb_back_to_menu(),
        )
        logger.warning(f"Rate limit tercapai untuk user_id={user_id}")
        return

    try:
        record_photo_request(user_id)
        processing_msg = await update.message.reply_text(
            "Baik, foto sudah saya terima 📥\nSedang saya periksa dulu ya, mohon tunggu sebentar\\.\\.\\. 🔎",
            parse_mode=ParseMode.MARKDOWN_V2,
        )

        photo = update.message.photo[-1]  # ambil resolusi terbesar
        file = await context.bot.get_file(photo.file_id)
        image_bytearray = await file.download_as_bytearray()
        image_bytes = bytes(image_bytearray)

        extracted_text = analyze_image_with_gemini(image_bytes)
        matched_scenario = query_rag(extracted_text) if extracted_text else None
        friendly_explanation = triage_text_with_deepseek(extracted_text, matched_scenario)

        if matched_scenario:
            kategori = escape_md(matched_scenario["title"])
        else:
            kategori = "Belum teridentifikasi jenis modus spesifik"

        result_text = (
            "⚠️ *Hasil Pemeriksaan*\n\n"
            f"Kategori terdeteksi: *{kategori}*\n\n"
            f"💡 Penjelasan:\n{escape_md(friendly_explanation)}\n\n"
            "Kalau masih ragu atau butuh dibantu lebih lanjut, jangan sungkan "
            "kirim screenshot lain atau tanya ke keluarga terdekat yang paham "
            "teknologi ya, Pak/Bu 🙏\n\n"
            "🔒 _Foto ini tidak kami simpan, hanya diperiksa sesaat lalu langsung dihapus dari sistem\\._"
        )
        await processing_msg.edit_text(result_text, parse_mode=ParseMode.MARKDOWN_V2, reply_markup=kb_back_to_menu())

    except Exception as e:
        logger.error(f"Gagal memproses foto (user_id={user_id}): {e}")
        fallback_text = (
            "Mohon maaf, Bapak/Ibu 🙏 Sepertinya sistem sedang sedikit sibuk sehingga "
            "foto belum bisa diperiksa dengan sempurna\\.\n\n"
            "Sebagai langkah aman sementara: *jangan klik tombol/link apa pun* pada "
            "pesan tersebut, dan *jangan berikan kode OTP* kepada siapa pun\\.\n\n"
            "Silakan coba kirim ulang fotonya beberapa saat lagi ya 😊"
        )
        try:
            if processing_msg:
                await processing_msg.edit_text(fallback_text, parse_mode=ParseMode.MARKDOWN_V2, reply_markup=kb_back_to_menu())
            else:
                await update.message.reply_text(fallback_text, parse_mode=ParseMode.MARKDOWN_V2, reply_markup=kb_back_to_menu())
        except Exception:
            pass
    finally:
        # Jaminan privasi: buang referensi byte gambar dari memori sesegera mungkin,
        # apa pun hasilnya (sukses atau gagal). Tidak ada jejak file di disk sama sekali.
        image_bytes = None


# =================================================================================
# 11. HANDLER: SISTEM KUIS (Freedom of Choice, Scaffolding, Instant Feedback)
# =================================================================================

async def handle_menu_kuis(query) -> None:
    text = (
        "🎮 *Mulai Kuis Keamanan*\n\n"
        "Silakan pilih dulu topik yang ingin dipelajari, Bapak/Ibu 👇\n\n"
        "Setiap topik punya 2 tingkat: *Dasar* dan *Lanjutan*\\. Tingkat Lanjutan "
        "akan terbuka otomatis setelah nilai Dasar mencapai 80 ke atas 💪"
    )
    await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN_V2, reply_markup=kb_topic_selection())


async def handle_topic_selected(query, user, topic: str) -> None:
    if topic not in QUIZ_BANK:
        await query.answer("Topik tidak ditemukan.", show_alert=True)
        return

    db = load_db()
    user_record = get_user(db, user.id, name=user.first_name or "")
    save_db(db)

    topic_title = escape_md(QUIZ_BANK[topic]["title"])
    text = f"📘 *{topic_title}*\n\nSilakan pilih tingkat kesulitan yang ingin dicoba 👇"
    await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN_V2, reply_markup=kb_level_selection(topic, user_record))


async def start_quiz(query, context: ContextTypes.DEFAULT_TYPE, topic: str, level: str) -> None:
    """Menginisialisasi state kuis di context.user_data lalu menampilkan soal pertama."""
    if topic not in QUIZ_BANK or level not in QUIZ_BANK[topic]:
        await query.answer("Soal tidak ditemukan.", show_alert=True)
        return

    context.user_data["quiz"] = {
        "topic": topic,
        "level": level,
        "correct_count": 0,
        "total": len(QUIZ_BANK[topic][level]),
        "answered_current": False,
    }
    await show_quiz_question(query, context, topic, level, 0)


async def show_quiz_question(query, context: ContextTypes.DEFAULT_TYPE, topic: str, level: str, index: int) -> None:
    """Menampilkan satu soal kuis, atau menutup kuis jika soal sudah habis."""
    questions = QUIZ_BANK[topic][level]

    if index >= len(questions):
        await finish_quiz(query, context, topic, level)
        return

    context.user_data.setdefault("quiz", {})
    context.user_data["quiz"]["answered_current"] = False

    q = questions[index]
    topic_title = escape_md(QUIZ_BANK[topic]["title"])
    level_label = "Dasar" if level == "dasar" else "Lanjutan"
    progress_text = f"Soal {index + 1} dari {len(questions)}"

    text = (
        f"📘 *{topic_title}* — Level {level_label}\n"
        f"_{escape_md(progress_text)}_\n\n"
        f"{escape_md(q['question'])}"
    )
    await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN_V2, reply_markup=kb_answer_options(topic, level, index))


async def handle_quiz_answer(query, context: ContextTypes.DEFAULT_TYPE, user, topic: str, level: str, index: int, letter: str) -> None:
    """Memberi feedback instan (benar/salah + penjelasan edukatif hangat)."""
    quiz_state = context.user_data.get("quiz")
    # Guard: cegah double-submit / state hilang (mis. bot restart)
    if not quiz_state or quiz_state.get("answered_current"):
        await query.answer()
        return

    quiz_state["answered_current"] = True
    q = QUIZ_BANK[topic][level][index]
    is_correct = letter == q["correct"]

    if is_correct:
        quiz_state["correct_count"] += 1
        header = "✅ *Jawaban Benar\\!*"
    else:
        jawaban_benar = escape_md(f"{q['correct']}. {q['options'][q['correct']]}")
        header = f"❌ *Belum tepat\\.* Jawaban yang benar: {jawaban_benar}"

    explanation = escape_md(q["explanation"])
    text = f"{header}\n\n💡 {explanation}"

    next_index = index + 1
    is_last = next_index >= len(QUIZ_BANK[topic][level])
    button_label_markup = (
        InlineKeyboardMarkup([[InlineKeyboardButton("🏁 Lihat Hasil Akhir", callback_data=f"next_{topic}_{level}_{next_index}")]])
        if is_last else kb_next_question(topic, level, next_index)
    )

    await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN_V2, reply_markup=button_label_markup)


async def finish_quiz(query, context: ContextTypes.DEFAULT_TYPE, topic: str, level: str) -> None:
    """Menghitung skor akhir, menyimpan ke JSON, membuka level berikutnya jika lulus, dan merayakan."""
    quiz_state = context.user_data.get("quiz", {"correct_count": 0, "total": len(QUIZ_BANK[topic][level])})
    correct = quiz_state["correct_count"]
    total = quiz_state["total"]
    percent = round((correct / total) * 100) if total else 0
    passed = percent >= PASSING_SCORE_PERCENT

    user = query.from_user
    db = load_db()
    user_record = get_user(db, user.id, name=user.first_name or "")

    progress = user_record["progress"][topic][level]
    progress["attempts"] += 1
    progress["best_score"] = max(progress["best_score"], percent)
    just_unlocked_next = False

    if passed and not progress["passed"]:
        progress["passed"] = True
        badge = BADGE_MAP.get((topic, level))
        if badge and badge not in user_record["badges"]:
            user_record["badges"].append(badge)
        if level == "dasar":
            just_unlocked_next = True

    user_record["total_score"] += correct * 10  # bobot skor sederhana
    save_db(db)

    nama = escape_md(user.first_name or "Bapak/Ibu")
    topic_title = escape_md(QUIZ_BANK[topic]["title"])
    level_label = "Dasar" if level == "dasar" else "Lanjutan"

    text_parts = [
        f"🏁 *Hasil Kuis: {topic_title} — Level {level_label}*\n",
        f"Skor Bapak/Ibu: *{correct} dari {total} benar* \\({percent}%\\)\n",
    ]

    if passed:
        text_parts.append(f"🎉 Selamat, {nama}\\! Nilainya sudah bagus sekali 👏")
        badge = BADGE_MAP.get((topic, level))
        if badge:
            text_parts.append(f"Lencana baru didapat: *{escape_md(badge)}* 🏅")
        if just_unlocked_next:
            text_parts.append("Level *Lanjutan* untuk topik ini sekarang sudah terbuka, silakan dicoba juga ya 💪")
    else:
        text_parts.append(
            f"Belum mencapai nilai {PASSING_SCORE_PERCENT}, tidak apa\\-apa, {nama}\\. "
            "Boleh dicoba lagi kapan saja, setiap usaha belajar ini sudah sangat berarti "
            "untuk melindungi keluarga 🙏"
        )

    text = "\n".join(text_parts)
    context.user_data.pop("quiz", None)  # bersihkan state runtime
    await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN_V2, reply_markup=kb_after_quiz())


# =================================================================================
# 12. HANDLER: SKOR & BADGE, serta BANTUAN
# =================================================================================

async def handle_menu_skor(query, user) -> None:
    db = load_db()
    user_record = get_user(db, user.id, name=user.first_name or "")
    save_db(db)

    nama = escape_md(user.first_name or "Bapak/Ibu")
    total_score = user_record["total_score"]

    lines = [f"🏆 *Skor & Lencana {nama}*\n", f"Total poin terkumpul: *{total_score}*\n"]

    lines.append("*Progres Belajar:*")
    for topic_key, topic_data in QUIZ_BANK.items():
        title = escape_md(topic_data["title"])
        dasar = user_record["progress"][topic_key]["dasar"]
        lanjutan = user_record["progress"][topic_key]["lanjutan"]
        dasar_icon = "✅" if dasar["passed"] else "⬜"
        lanjutan_icon = "✅" if lanjutan["passed"] else ("🔒" if not dasar["passed"] else "⬜")
        lines.append(f"📘 {title}")
        lines.append(f"   {dasar_icon} Dasar \\(nilai terbaik: {dasar['best_score']}\\)")
        lines.append(f"   {lanjutan_icon} Lanjutan \\(nilai terbaik: {lanjutan['best_score']}\\)")

    if user_record["badges"]:
        lines.append("\n*Lencana yang dimiliki:*")
        for badge in user_record["badges"]:
            lines.append(f"🏅 {escape_md(badge)}")
    else:
        lines.append("\nBelum ada lencana, yuk coba kuisnya dulu 😊")

    text = "\n".join(lines)
    await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN_V2, reply_markup=kb_back_to_menu())


async def handle_menu_bantuan(query) -> None:
    text = (
        "❓ *Bantuan*\n\n"
        "Bot ini dibuat untuk membantu Bapak/Ibu mengenali penipuan digital "
        "yang sering menyasar keluarga, dengan cara yang santai dan mudah "
        "dipahami\\.\n\n"
        "🔍 *Cek Pesan* — kirim foto screenshot chat/SMS mencurigakan, nanti "
        "saya bantu periksa\\.\n"
        "🎮 *Kuis* — belajar sambil main dengan soal pilihan ganda, ada "
        "lencana kalau nilainya bagus\\.\n"
        "🏆 *Skor* — melihat progres belajar dan lencana yang sudah "
        "dikumpulkan\\.\n\n"
        "Semua bisa dilakukan cukup dengan menekan tombol, tidak perlu "
        "mengetik perintah apa pun 😊\n\n"
        "Kalau ada kendala, coba tekan tombol menu di bawah ini untuk "
        "kembali ke awal ya\\."
    )
    await query.edit_message_text(text, parse_mode=ParseMode.MARKDOWN_V2, reply_markup=kb_back_to_menu())


# =================================================================================
# 13. FALLBACK: PESAN TEKS BEBAS / DOKUMEN LAIN (panic-free redirect)
# =================================================================================

async def fallback_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Menangani teks bebas yang diketik pengguna (bukan command).
    Sesuai prinsip Zero-Typing Interaction, arahkan dengan lembut ke tombol menu,
    TANPA membuat pengguna merasa disalahkan.
    """
    text = (
        "Baik, terima kasih pesannya 😊\n\n"
        "Untuk memudahkan Bapak/Ibu, silakan gunakan tombol menu di bawah ini saja "
        "ya, tidak perlu mengetik\\."
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN_V2, reply_markup=kb_main_menu())


async def fallback_other_files_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Menangani dokumen/stiker/video yang bukan foto, agar bot tidak diam saja."""
    text = (
        "Mohon maaf, saat ini saya baru bisa memeriksa file dalam bentuk *foto/screenshot* "
        "ya, Pak/Bu 🙏\n\n"
        "Silakan kirim ulang dalam bentuk foto, atau tekan tombol di bawah untuk kembali "
        "ke menu\\."
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN_V2, reply_markup=kb_main_menu())


# =================================================================================
# 14. ERROR HANDLER GLOBAL (jaring pengaman terakhir agar bot tidak pernah crash total)
# =================================================================================

async def global_error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(f"Unhandled exception: {context.error}", exc_info=context.error)
    try:
        if isinstance(update, Update) and update.effective_message:
            await update.effective_message.reply_text(
                "Mohon maaf, Bapak/Ibu 🙏 Ada sedikit kendala teknis\\. Silakan coba lagi "
                "dengan menekan /start ya\\.",
                parse_mode=ParseMode.MARKDOWN_V2,
            )
    except Exception:
        pass


# =================================================================================
# 15. MAIN ENTRYPOINT
# =================================================================================

def validate_startup_config() -> bool:
    """
    Mengecek semua konfigurasi penting SEBELUM bot mulai jalan, dan mencetak
    ringkasan status yang jelas. Ini membantu mahasiswa langsung tahu bagian
    mana yang belum siap, alih-alih menebak-nebak dari error di tengah jalan.

    Return False hanya jika ada konfigurasi WAJIB yang hilang (token Telegram).
    Konfigurasi AI (Gemini/DeepSeek) bersifat opsional -> bot tetap jalan
    dengan mode fallback/demo kalau belum diisi.
    """
    logger.info("=" * 60)
    logger.info("MENGECEK KONFIGURASI SEBELUM BOT DIJALANKAN")
    logger.info("=" * 60)

    all_ok = True

    if not TELEGRAM_BOT_TOKEN:
        logger.error(
            "❌ TELEGRAM_BOT_TOKEN belum diset! Ini WAJIB. Jalankan: "
            "export TELEGRAM_BOT_TOKEN='token_anda' sebelum menjalankan bot ini."
        )
        all_ok = False
    else:
        logger.info("✅ TELEGRAM_BOT_TOKEN terdeteksi.")

    if not GEMINI_API_KEY or not GEMINI_LIB_AVAILABLE:
        logger.warning(
            "⚠️  GEMINI_API_KEY/library belum siap -> fitur cek screenshot akan memakai "
            "mode fallback (penjelasan default, tanpa OCR gambar sungguhan)."
        )
    else:
        logger.info("✅ Gemini (OCR screenshot) siap dipakai.")

    if not DEEPSEEK_API_KEY:
        logger.warning(
            "⚠️  DEEPSEEK_API_KEY belum diset -> penjelasan hasil cek screenshot akan "
            "memakai template default, bukan hasil susunan AI."
        )
    else:
        logger.info("✅ DeepSeek (triase teks) siap dipakai.")

    if not CHROMADB_AVAILABLE:
        logger.warning("⚠️  ChromaDB tidak terpasang -> RAG memakai fallback keyword search.")
    else:
        logger.info("✅ ChromaDB siap dipakai untuk RAG.")

    logger.info("=" * 60)
    return all_ok


def main() -> None:
    if not validate_startup_config():
        logger.error("Bot TIDAK dijalankan karena ada konfigurasi wajib yang hilang. Lihat pesan di atas.")
        return

    init_rag()

    application = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    # --- Registrasi handler ---
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CallbackQueryHandler(menu_callback))
    application.add_handler(MessageHandler(filters.PHOTO, photo_handler))
    application.add_handler(
        MessageHandler(filters.Document.ALL | filters.VIDEO | filters.Sticker.ALL, fallback_other_files_handler)
    )
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, fallback_text_handler))
    application.add_error_handler(global_error_handler)

    logger.info("Bot Asisten Literasi Keamanan Digital Keluarga mulai berjalan...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()