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
