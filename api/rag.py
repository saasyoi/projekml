import logging
from typing import Optional

logger = logging.getLogger("familysecure_backend")

try:
    import chromadb
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False


SCAM_DATABASE = [
    # ─────────────── KATEGORI: APK / FILE BERBAHAYA ───────────────
    {
        "id": "apk_kurir",
        "title": "Modus File Kiriman Kurir Palsu",
        "category": "apk",
        "description": (
            "Pesan mengaku dari kurir ekspedisi (JNE, J&T, SiCepat, Pos Indonesia, dll) meminta korban "
            "membuka dan memasang file berekstensi .apk untuk melihat 'foto paket', 'resi pengiriman', atau "
            "'surat tilang'. File ini sebenarnya program jahat (malware) yang bisa membaca SMS OTP, "
            "mengakses kontak, dan menguras rekening bank korban secara diam-diam."
        ),
        "red_flags": [
            "Ada file .apk dikirim lewat WhatsApp atau Telegram",
            "Pengirim mengaku petugas JNE, J&T, SiCepat, kurir",
            "Diminta install aplikasi di luar Play Store",
            "Ada tekanan untuk segera dibuka",
        ],
        "action": (
            "Jangan pernah instal file .apk yang dikirim orang tak dikenal lewat chat, Pak/Bu. "
            "Langsung hapus pesannya dan tekan tombol Blokir + Laporkan di WhatsApp."
        ),
    },
    {
        "id": "apk_undangan_pernikahan",
        "title": "Modus Undangan Pernikahan Digital Palsu",
        "category": "apk",
        "description": (
            "Pesan berisi file .apk yang disamarkan sebagai 'undangan pernikahan digital'. "
            "Pengirim bisa mengaku teman atau saudara. Setelah diinstal, aplikasi ini diam-diam "
            "mencuri data perbankan, membaca SMS OTP, dan bisa membajak akun mobile banking."
        ),
        "red_flags": [
            "Undangan berbentuk file yang harus diinstal",
            "Pengirim tak dikenal mengaku teman lama atau kerabat",
            "File berekstensi .apk bukan link ke website",
        ],
        "action": (
            "Undangan asli tidak pernah berbentuk file .apk, Pak/Bu. "
            "Kalau ragu, tanya langsung ke orangnya lewat telepon. Kalau tidak kenal, langsung hapus saja."
        ),
    },
    {
        "id": "apk_surat_tilang",
        "title": "Modus Surat Tilang Polisi Palsu (APK)",
        "category": "apk",
        "description": (
            "Pesan mengaku dari pihak kepolisian atau BPKB/STNK, memberitahu korban 'kena tilang' "
            "atau ada dokumen kendaraan bermasalah. Korban diminta mengunduh dan membuka file .apk "
            "untuk melihat 'surat tilang digital'. File tersebut adalah malware pencuri data."
        ),
        "red_flags": [
            "Pesan tentang tilang atau masalah STNK/BPKB",
            "Ada file .apk yang harus diinstal untuk melihat detailnya",
            "Mengaku dari Polisi atau Satlantas",
        ],
        "action": (
            "Polisi tidak pernah mengirim surat tilang atau dokumen resmi lewat WhatsApp, Pak/Bu. "
            "Hapus pesannya dan jangan diinstal. Jika khawatir, hubungi kantor polisi terdekat secara langsung."
        ),
    },
    {
        "id": "apk_bantuan_sosial",
        "title": "Modus Notifikasi Bantuan Sosial Palsu (APK)",
        "category": "apk",
        "description": (
            "Pesan mengaku dari pemerintah (Kemensos, BPJS, BLT, dll) memberitahu korban mendapatkan "
            "bantuan sosial atau subsidi. Untuk mengklaimnya, korban diarahkan menginstal file .apk. "
            "Setelah terinstal, aplikasi mencuri data dan akses perbankan korban."
        ),
        "red_flags": [
            "Klaim mendapat bantuan dari pemerintah lewat WA",
            "Harus instal aplikasi untuk klaim bantuan",
            "Mengaku dari Kemensos, BPJS, atau program pemerintah",
        ],
        "action": (
            "Program bantuan pemerintah yang resmi tidak pernah disalurkan lewat WhatsApp dengan meminta instal aplikasi. "
            "Cek langsung ke kantor kelurahan atau website resmi pemerintah, Pak/Bu."
        ),
    },
    # ─────────────── KATEGORI: LINK / PHISHING ───────────────
    {
        "id": "cs_bank_palsu",
        "title": "Modus Petugas Customer Service Bank Palsu",
        "category": "link",
        "description": (
            "Seseorang menelepon atau mengirimi pesan mengaku petugas bank resmi (BRI, BCA, Mandiri, BNI, dll), "
            "menyampaikan akun korban 'bermasalah', 'akan diblokir', atau 'ada transaksi mencurigakan'. "
            "Korban kemudian diarahkan ke link palsu untuk mengisi data kartu, PIN, atau kode OTP. "
            "Link tersebut tampak mirip website bank tapi sebenarnya palsu."
        ),
        "red_flags": [
            "Diminta OTP, PIN, atau nomor kartu lewat telepon atau chat",
            "Link mirip nama bank tapi alamatnya mencurigakan",
            "Tekanan waktu: 'rekening diblokir dalam X menit'",
            "Menelepon dari nomor biasa (bukan nomor resmi bank)",
        ],
        "action": (
            "Bank asli TIDAK PERNAH meminta kode OTP, PIN, atau kata sandi lewat telepon atau chat, Pak/Bu. "
            "Tutup teleponnya dan hubungi call center resmi dari nomor yang tertera di kartu ATM atau website bank."
        ),
    },
    {
        "id": "phishing_marketplace",
        "title": "Modus Phishing Marketplace (Shopee/Tokopedia/Lazada)",
        "category": "link",
        "description": (
            "Pesan mengaku dari Shopee, Tokopedia, Lazada, atau marketplace lain, menyampaikan ada "
            "'masalah pesanan', 'refund yang perlu diklaim', atau 'akun yang bermasalah'. "
            "Korban diarahkan ke link palsu yang mirip tampilan aslinya untuk mengisi data login atau "
            "informasi kartu kredit/debit."
        ),
        "red_flags": [
            "Link ke website yang mirip Shopee/Tokopedia tapi alamat berbeda",
            "Klaim ada refund atau pesanan bermasalah lewat WA",
            "Diminta isi ulang data kartu atau password",
        ],
        "action": (
            "Jangan klik link dari chat, Pak/Bu. Selalu buka aplikasi Shopee/Tokopedia/Lazada langsung dari HP "
            "dan periksa notifikasi di sana. Refund asli diproses otomatis tanpa klik link apapun."
        ),
    },
    {
        "id": "hadiah_palsu",
        "title": "Modus Notifikasi Hadiah atau Undian Palsu",
        "category": "link",
        "description": (
            "Pesan memberitahu korban telah memenangkan hadiah besar (uang tunai, motor, HP, dll) "
            "dari program undian suatu merek terkenal atau platform digital. Untuk mengklaim hadiah, "
            "korban diminta mengisi data pribadi, membayar 'biaya administrasi', atau mengklik link tertentu."
        ),
        "red_flags": [
            "Klaim menang undian tanpa pernah mengikuti",
            "Diminta bayar biaya administrasi untuk ambil hadiah",
            "Link atau formulir pengisian data pribadi",
        ],
        "action": (
            "Hadiah asli tidak pernah meminta biaya di muka, Pak/Bu. "
            "Jika tampak mencurigakan, abaikan saja. Jangan isi data pribadi atau kirim uang apapun."
        ),
    },
    {
        "id": "pinjol_ilegal",
        "title": "Modus Pinjaman Online Ilegal",
        "category": "link",
        "description": (
            "Tawaran pinjaman uang cepat dengan syarat sangat mudah: tanpa jaminan, langsung cair, "
            "bunga 'rendah'. Biasanya disebarkan lewat SMS, WhatsApp, atau media sosial. "
            "Setelah korban terdaftar, pinjol ilegal menerapkan bunga dan denda sangat tinggi, "
            "mengakses kontak HP, lalu mengancam jika telat bayar."
        ),
        "red_flags": [
            "Tawaran pinjaman tanpa jaminan dan syarat mudah",
            "Dikirim lewat SMS atau WA dari nomor tidak dikenal",
            "Minta akses ke kontak/foto HP saat mendaftar",
        ],
        "action": (
            "Pinjaman resmi tidak pernah ditawarkan lewat SMS atau WA tanpa diminta, Pak/Bu. "
            "Pastikan pinjol terdaftar di OJK sebelum menggunakan. Cek daftarnya di ojk.go.id."
        ),
    },
    # ─────────────── KATEGORI: SOSIAL / MANIPULASI ───────────────
    {
        "id": "mama_minta_pulsa",
        "title": "Modus Anggota Keluarga Membutuhkan Bantuan",
        "category": "sosial",
        "description": (
            "Pesan dari nomor tidak dikenal mengaku sebagai anak, cucu, atau anggota keluarga dekat. "
            "Mengaku sedang dalam keadaan darurat (kecelakaan, ditangkap polisi, HP rusak, di rumah sakit) "
            "dan membutuhkan transfer uang segera. Korban yang panik sering langsung mengirim uang."
        ),
        "red_flags": [
            "Nomor tidak dikenal mengaku anggota keluarga",
            "Cerita darurat yang membutuhkan uang segera",
            "Minta dirahasiakan atau tidak cerita ke orang lain",
        ],
        "action": (
            "Tenang dulu, Pak/Bu. Sebelum transfer, hubungi langsung anggota keluarga tersebut lewat nomor lama "
            "yang sudah tersimpan. Penipu sering memanfaatkan kepanikan. Verifikasi dulu!"
        ),
    },
    {
        "id": "love_scam",
        "title": "Modus Penipuan Kenalan Online (Love Scam / Romance Scam)",
        "category": "sosial",
        "description": (
            "Seseorang berkenalan di media sosial, aplikasi kencan, atau game online, membangun hubungan "
            "emosional selama berminggu-minggu atau berbulan-bulan. Setelah korban percaya, "
            "pelaku mulai meminta uang dengan berbagai alasan: sakit, biaya perjalanan, bisnis, atau investasi."
        ),
        "red_flags": [
            "Kenalan online yang cepat akrab dan sangat perhatian",
            "Mengaku tinggal di luar negeri atau profesi bergengsi",
            "Belum pernah bertemu langsung tapi minta uang",
        ],
        "action": (
            "Hati-hati dengan kenalan online yang belum pernah bertemu tapi sudah minta uang, Pak/Bu. "
            "Jangan kirim uang ke orang yang belum dikenal secara langsung. Ceritakan ke keluarga terpercaya."
        ),
    },
    {
        "id": "akun_sosmed_dibajak",
        "title": "Modus Akun WhatsApp/Instagram Teman Dibajak",
        "category": "sosial",
        "description": (
            "Akun WhatsApp atau Instagram milik teman/keluarga dibajak oleh penipu. "
            "Penipu kemudian menghubungi kontak-kontaknya meminta pulsa, transfer uang, atau "
            "pinjaman mendesak dengan alasan darurat. Karena tampak dari orang yang dikenal, korban mudah percaya."
        ),
        "red_flags": [
            "Teman meminta pulsa atau transfer uang tiba-tiba",
            "Cara bicara berbeda dari biasanya",
            "Meminta dirahasiakan atau tidak memberi nomor untuk dihubungi",
        ],
        "action": (
            "Sebelum membantu, hubungi teman/keluarga tersebut melalui cara lain (telepon langsung, atau "
            "tanya lewat anggota keluarganya). Akun yang dibajak tidak bisa dikontrol oleh pemilik aslinya."
        ),
    },
    {
        "id": "investasi_bodong",
        "title": "Modus Investasi Bodong / Skema Ponzi",
        "category": "sosial",
        "description": (
            "Tawaran investasi dengan iming-iming keuntungan sangat besar dan cepat (misalnya: 'profit 30% per bulan', "
            "'uang berkembang 2x dalam seminggu'). Biasanya disebarkan lewat grup WhatsApp, media sosial, "
            "atau ajakan dari kenalan. Skema ini membayar anggota lama dengan uang anggota baru, hingga akhirnya collapse."
        ),
        "red_flags": [
            "Janji keuntungan sangat besar dalam waktu singkat",
            "Dapat komisi jika ajak orang lain bergabung",
            "Tidak jelas mekanisme investasinya",
            "Desakan untuk segera bergabung sebelum 'kuota penuh'",
        ],
        "action": (
            "Investasi yang menjanjikan keuntungan besar tanpa risiko hampir pasti penipuan, Pak/Bu. "
            "Konsultasikan dulu dengan keluarga atau orang yang paham keuangan. "
            "Pastikan investasi terdaftar dan diawasi OJK di ojk.go.id."
        ),
    },
]

_rag_collection = None


def init_rag():
    global _rag_collection
    if not CHROMADB_AVAILABLE:
        logger.warning("ChromaDB tidak terpasang, memakai fallback keyword search.")
        return
    try:
        client = chromadb.Client()
        collection = client.get_or_create_collection(name="scam_scenarios")
        # Reset koleksi agar tidak duplikat saat reload
        existing_ids = collection.get()["ids"]
        if existing_ids:
            collection.delete(ids=existing_ids)
        collection.add(
            ids=[i["id"] for i in SCAM_DATABASE],
            documents=[i["description"] + " " + " ".join(i.get("red_flags", []))
                       for i in SCAM_DATABASE],
            metadatas=[{"title": i["title"], "category": i["category"]} for i in SCAM_DATABASE],
        )
        _rag_collection = collection
        logger.info(f"RAG (ChromaDB) siap. Total entri: {len(SCAM_DATABASE)}")
    except Exception as e:
        logger.error(f"Gagal init ChromaDB: {e}")


def query_rag(text: str, top_k: int = 1) -> Optional[dict]:
    if not text:
        return None

    if _rag_collection is not None:
        try:
            result = _rag_collection.query(query_texts=[text], n_results=top_k)
            if result and result.get("ids") and result["ids"][0]:
                matched_id = result["ids"][0][0]
                for item in SCAM_DATABASE:
                    if item["id"] == matched_id:
                        return item
        except Exception as e:
            logger.error(f"Query ChromaDB gagal: {e}")

    # Fallback: keyword scoring
    text_lower = text.lower()
    best_match, best_score = None, 0
    for item in SCAM_DATABASE:
        score = sum(1 for w in item["description"].lower().split() if w in text_lower)
        score += sum(3 for flag in item.get("red_flags", [])
                     if any(w in text_lower for w in flag.lower().split()))
        if score > best_score:
            best_score, best_match = score, item
    return best_match if best_score >= 3 else None
