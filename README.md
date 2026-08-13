# FamilySecure

Asisten keamanan digital untuk membantu keluarga mengenali penipuan online. Pengguna bisa menceritakan situasi mencurigakan, mengunggah screenshot pesan, atau keduanya sekaligus dalam satu percakapan, lalu mendapat analisis dari AI dan bisa mengasah wawasan lewat kuis interaktif.

**Live demo**: https://projekml.onrender.com

## Fitur

- Chat dengan asisten AI yang bisa membaca teks maupun foto/screenshot
- Deteksi modus penipuan berbasis AI (Gemini) dengan pendekatan tool-use agent
- Rekomendasi kontak resmi (bank, e-commerce, pelaporan pemerintah) saat relevan
- Kuis keamanan digital dengan sistem level dan lencana
- Riwayat chat & kuis, dashboard progres
- Login email/password
- Bilingual (Indonesia / English)

## Cara Kerja AI

1. Pesan atau hasil baca foto dikirim ke Gemini bersama beberapa "tool" (fungsi) yang bisa dipanggil model itu sendiri: cari skenario penipuan di basis data, cari kontak resmi, atau sarankan kuis terkait.
2. Model yang memutuskan sendiri tool mana yang perlu dipakai berdasarkan isi pesan, lalu merangkai jawaban akhir dalam bahasa natural.
3. Basis data skenario penipuan dicari menggunakan pendekatan RAG (Retrieval-Augmented Generation) agar jawaban tetap berpijak pada modus yang sudah terverifikasi, bukan sekadar karangan model.

## Komponen Deterministik vs LLM-assisted

Supaya jelas bagian mana yang perilakunya bisa diprediksi/diuji secara pasti, dan bagian mana yang keluarannya bergantung pada model bahasa:

**Deterministik (logika biasa, hasilnya selalu sama untuk input yang sama, ada unit test-nya):**
- Autentikasi: hash/verifikasi password (bcrypt), pembuatan & validasi JWT (`api/auth.py`)
- Rate limiting berbasis time-window (`api/rate_limit.py`)
- Validasi input (Pydantic schema, `api/schemas.py`)
- Logika kuis: penilaian jawaban, syarat lulus level, pemberian lencana (`api/quiz.py`, endpoint `/api/quiz/*`)
- Pencarian skenario penipuan via keyword scoring, dipakai sebagai fallback RAG (`api/rag.py`, fungsi `query_rag`)
- Lookup kontak resmi bank/e-commerce — hasilnya selalu dari data statis yang sudah diverifikasi manual, model AI tidak pernah mengarang nomor/link (`api/agent.py`, `OFFICIAL_CONTACTS`)

**LLM-assisted (memanggil Gemini, keluarannya bisa bervariasi, diuji secara fungsional lewat tool contract bukan output persis):**
- Analisis isi chat & foto/screenshot (OCR + reasoning) — `api/ai.py`, `api/agent.py`
- Keputusan tool mana yang dipanggil (cari skenario, cari kontak resmi, rekomendasi kuis) saat menjawab user — model yang memutuskan sendiri berdasarkan isi pesan (function calling / automatic tool-use di `google-genai`)
- Redaksi jawaban akhir dalam bahasa natural ke user

Yang diuji di `tests/`: seluruh jalur deterministik (auth, rate limit, validasi skema, logika kuis, RAG fallback) diuji langsung lewat pytest. Untuk bagian yang memanggil Gemini, yang diuji adalah *tool function*-nya sendiri (`cari_kontak_resmi`, `rekomendasikan_kuis` di `tests/test_agent_tools.py`) — memastikan tool tidak pernah mengarang data — bukan output akhir model, karena itu memang tidak deterministik.

## Testing & CI

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

GitHub Actions (`.github/workflows/ci.yml`) menjalankan compile check, import check, JS syntax check, HTML balance check, pytest, dan boot smoke test di setiap push/PR ke `main`.

## Tech Stack

- **Backend**: FastAPI (Python), SQLAlchemy, PostgreSQL
- **AI**: Google Gemini 2.5 Flash (multimodal, dengan function calling)
- **Auth**: JWT via httpOnly cookie, bcrypt untuk hash password
- **Frontend**: HTML/CSS/JavaScript
- **Deployment**: Render (app) + Neon (database)

## Menjalankan Secara Lokal

```bash
pip install -r requirements.txt
cp .env.example .env   # isi GEMINI_API_KEY dan SECRET_KEY
uvicorn main:app --reload
```

Buka `http://localhost:8000`.

## Struktur Proyek

```
main.py            # endpoint API (auth, kuis, chat)
api/agent.py        # agent AI dengan tool-use
api/models.py        # skema database
api/rag.py          # basis data skenario penipuan
frontend/           # halaman web
```
