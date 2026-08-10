QUIZ_BANK = {
    "apk": {
        "title": "Modus File/APK Berbahaya",
        "dasar": [
            {
                "question": "Ibu menerima chat berisi file 'Paket_Anda.apk' dari nomor tak dikenal. Apa yang sebaiknya dilakukan?",
                "options": {"A": "Langsung buka dan instal", "B": "Hapus tanpa membuka", "C": "Teruskan ke grup keluarga", "D": "Simpan untuk dibuka nanti"},
                "correct": "B",
                "explanation": "Betul, file .apk dari orang tak dikenal sebaiknya langsung dihapus tanpa dibuka.",
            },
            {
                "question": "Kenapa file .apk dari chat berbahaya untuk dipasang di HP?",
                "options": {"A": "Bikin memori penuh", "B": "Bisa mengambil alih SMS & data pribadi", "C": "Tampilannya jelek", "D": "Tidak bisa dihapus"},
                "correct": "B",
                "explanation": "Tepat, file ini bisa diam-diam membaca SMS (termasuk OTP) dan data pribadi.",
            },
            {
                "question": "Bapak dapat 'undangan pernikahan digital' berbentuk file yang harus diinstal. Tindakan paling aman?",
                "options": {"A": "Instal saja", "B": "Tanya pengirim by telepon", "C": "Jangan diinstal, hapus", "D": "Kirim ke teman dulu"},
                "correct": "C",
                "explanation": "Benar, undangan asli tidak pernah berbentuk file yang harus diinstal.",
            },
        ],
        "lanjutan": [
            {
                "question": "Cara penipu menyamarkan file berbahaya di WhatsApp?",
                "options": {"A": "Ubah nama jadi 'Foto.jpg.apk'", "B": "Kirim lewat kertas fisik", "C": "Telepon tanpa file", "D": "Kirim lewat pos"},
                "correct": "A",
                "explanation": "Benar, penipu menyamarkan nama file agar terlihat seperti foto biasa.",
            },
            {
                "question": "Tanda penipuan APK yang terorganisir?",
                "options": {"A": "Dikirim massal dengan pesan sama", "B": "Dikirim keluarga dekat", "C": "Ukuran file kecil", "D": "File berwarna-warni"},
                "correct": "A",
                "explanation": "Tepat, pesan sama dikirim massal adalah ciri penipuan otomatis.",
            },
            {
                "question": "HP keluarga terlanjur terpasang aplikasi mencurigakan, ada transaksi aneh. Urutan tindakan tepat?",
                "options": {"A": "Hubungi bank blokir rekening, lalu reset HP", "B": "Tunggu beberapa hari", "C": "Ganti SIM saja", "D": "Matikan HP selamanya"},
                "correct": "A",
                "explanation": "Benar, amankan rekening dulu lewat bank, baru bersihkan HP.",
            },
        ],
    },
    "link": {
        "title": "Modus Link Palsu / Petugas Palsu",
        "dasar": [
            {
                "question": "Penelepon mengaku petugas bank minta kode OTP. Apa yang harus dilakukan?",
                "options": {"A": "Berikan kodenya", "B": "Tutup telepon, jangan beri kode", "C": "Beri sebagian kode", "D": "Minta telepon ulang besok"},
                "correct": "B",
                "explanation": "Benar sekali, kode OTP tidak boleh diberikan ke siapa pun.",
            },
            {
                "question": "SMS berisi link 'verifikasi akun bank agar tidak diblokir'. Tindakan paling aman?",
                "options": {"A": "Klik dan isi data segera", "B": "Abaikan, cek langsung lewat app resmi bank", "C": "Teruskan ke keluarga", "D": "Simpan link"},
                "correct": "B",
                "explanation": "Tepat, lebih aman cek langsung lewat aplikasi resmi bank.",
            },
            {
                "question": "Ciri khas link palsu penipu?",
                "options": {"A": "Beri waktu berpikir lama", "B": "Mendesak bertindak cepat", "C": "Minta bertemu di kantor bank", "D": "Tidak sebut nominal"},
                "correct": "B",
                "explanation": "Benar, tekanan waktu adalah taktik umum penipu.",
            },
        ],
        "lanjutan": [
            {
                "question": "Website mirip web bank asli tapi alamatnya sedikit berbeda. Artinya?",
                "options": {"A": "Kemungkinan besar tiruan/palsu", "B": "Wajar, bank ganti alamat", "C": "Tidak masalah", "D": "Tanda ada promo"},
                "correct": "A",
                "explanation": "Benar, perbedaan kecil pada alamat adalah tanda situs tiruan.",
            },
            {
                "question": "Media lain yang dipakai penipu 'CS bank palsu'?",
                "options": {"A": "Chat WhatsApp/Telegram mengaku CS resmi", "B": "Surat pos resmi", "C": "Papan pengumuman bank", "D": "Buku tabungan fisik"},
                "correct": "A",
                "explanation": "Tepat, chat aplikasi pesan mudah dipakai menyamar.",
            },
            {
                "question": "Sudah terlanjur isi data di link palsu. Tindakan pertama paling tepat?",
                "options": {"A": "Hubungi bank blokir akses & pantau mutasi", "B": "Tunggu beberapa minggu", "C": "Hapus riwayat chat saja", "D": "Tidak perlu tindakan"},
                "correct": "A",
                "explanation": "Tepat sekali, semakin cepat hubungi bank semakin kecil risiko kerugian.",
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
