// STATE
const API = '';   // same-origin; if running separately, set to 'http://localhost:8000'

const state = {
  user: null, // { id, email, name, total_score } — populated after login/register/session check
  lang: 'id',
  chatHistoryLoaded: false,
  pendingAttachment: null, // File object staged for the next chat message, or null
  // Quiz
  currentTopic: null,
  currentLevel: null,
  questions: [],
  currentIndex: 0,
  correctCount: 0,
  answered: false,
};

// I18N
const I18N = {
  en: {
    meta: {
      title: 'FamilySecure – Family Digital Security Assistant',
      description: 'FamilySecure – Digital security literacy assistant for families. Check suspicious messages and test your security knowledge with an interactive quiz.',
    },
    nav: { points: 'points', logoutTitle: 'Log out' },
    hero: {
      badge: '🛡️ Family Digital Security',
      title: 'Protect Your Family from <em>Digital Fraud</em>',
      subtitle: "Check suspicious messages or photos in seconds, and test your family's digital security awareness together.",
      ctaPrimary: 'Get Started',
      ctaSecondary: 'Security Tips',
    },
    setup: {
      inputLabel: 'Your Name',
      inputPlaceholder: 'e.g., Budi Santoso',
      nameRequired: 'Please enter your name to continue.',
    },
    auth: {
      tabRegister: 'Create Account',
      tabLogin: 'Log In',
      registerTitle: 'Create an Account',
      registerDesc: 'Your account stores your quiz progress, chat history, and photo check history on our server.',
      loginTitle: 'Welcome Back',
      loginDesc: 'Log in to continue your learning progress.',
      emailLabel: 'Email',
      emailPlaceholder: 'you@example.com',
      passwordLabel: 'Password',
      passwordHint: 'At least 8 characters',
      registerSubmit: 'Create Account →',
      loginSubmit: 'Log In →',
      emailRequired: 'Please enter a valid email address.',
      passwordTooShort: 'Password must be at least 8 characters.',
      registerFailed: 'Registration failed. Please try again.',
      loginFailed: 'Login failed. Please try again.',
      loggedOut: 'You have been logged out.',
      passwordSaveHint: "Remember this email and password — you'll need them to log in again next time.",
      needHelpNote: 'Not sure what to do? Ask a family member to help you register the first time.',
      showPasswordAria: 'Show password',
      hidePasswordAria: 'Hide password',
    },
    history: {
      quizTitle: 'Quiz Attempt History',
      chatTitle: 'Conversation History',
      empty: 'No activity yet.',
    },
    home: {
      sectionLabel: 'Main Features',
      cardQuizTitle: 'Digital Security Quiz',
      cardQuizDesc: 'Test your knowledge with an interactive quiz. Earn points and badges for each level you complete.',
      cardChatTitle: 'Ask & Check a Message',
      cardChatDesc: 'Describe a suspicious situation, upload a screenshot, or both in the same conversation — our AI assistant will help either way.',
      cardScoreTitle: 'Score & Achievements',
      cardScoreDesc: 'Review your learning progress, earned badges, and quiz results by topic.',
      emergencyTitle: 'Already clicked a suspicious link or installed a file?',
      emergencyDesc: '<strong>Contact your bank immediately</strong> to block your account. Emergency numbers are usually printed on your ATM card or mobile banking app.',
      topicFallbackDesc: 'Select a quiz level for this topic to test your knowledge.',
    },
    check: {
      safeTag: '✓ No Message Text Found',
      dangerTag: '⚠️ Potential Danger Detected',
      uncertainTag: '❓ No Known Pattern Matched',
    },
    quiz: {
      topicHeader: '🎓 Choose a Quiz Topic',
      topicIntro: 'Choose a topic to study. Each topic has two levels — complete the Basic level first to unlock the Advanced level.',
      levelPanelPrefix: '🎓',
      levelAvailable: 'Available',
      levelUnlocked: 'Unlocked ✓',
      levelLocked: '🔒 Locked',
      levelBasicTitle: '🌱 Basic Level',
      levelBasicDesc: '3 multiple-choice questions. Score at least 80% to unlock the Advanced level.',
      levelAdvancedTitle: '🚀 Advanced Level',
      levelAdvancedUnlockedDesc: '3 advanced questions. Test your knowledge further.',
      levelAdvancedLockedDesc: 'Complete the Basic level with a score of 80% or higher to unlock.',
      loadingProgress: 'Checking progress...',
      loadingQuestions: 'Loading questions...',
      loadQuestionsFailed: 'Failed to load questions',
      questionOf: (idx, total) => `Question ${idx} of ${total}`,
      correctCount: (n) => `${n} correct`,
      checkingAnswer: 'Checking answer...',
      answerCheckFailed: 'Failed to check answer',
      nextQuestion: 'Next Question →',
      finishQuiz: 'Finish & See Result ✓',
      savingResult: 'Saving result...',
      saveResultFailed: 'Failed to save result',
      resultScoreLabel: 'Score',
      passedTitle: '🎉 Congratulations, You Passed!',
      passedSubtitle: (pct) => `Your score of ${pct}% exceeds the passing threshold (80%). Well done!`,
      unlockedNextSuffix: ' The Advanced level is now unlocked.',
      failedTitle: 'Not Passed Yet — Keep Trying!',
      failedSubtitle: (pct) => `Your score is ${pct}%. A minimum of 80% is required to pass. Review the material and try again.`,
      newBadge: '🏅 New Badge: ',
      newBadgeToast: 'New badge earned! ',
      retryPassed: '🔄 Play Again',
      retryFailed: '🔄 Try Again',
      chooseAnotherTopic: 'Choose Another Topic',
      viewScore: 'View Score',
      confirmQuit: 'Are you sure you want to exit the quiz? Progress on this question will not be saved.',
    },
    score: {
      learningProgress: 'Learning Progress',
      totalPoints: 'Total Points',
      badgesEarned: 'Badges Earned',
      backToMenu: '← Back to Menu',
      loadingScore: 'Loading score data...',
      loadScoreFailed: 'Failed to load score data',
      noBadges: 'No badges yet. Complete a quiz to earn your first badge!',
      bestScore: (pct, attempts) => `${pct}% best · ${attempts} attempt(s)`,
    },
    chat: {
      header: '💬 Ask the FamilySecure Assistant',
      online: '● Online',
      clearTitle: 'Clear chat history',
      welcome1: "Hello! I'm the FamilySecure assistant.",
      welcome2: "Describe a message or situation you find suspicious, and I'll help explain whether it may be harmful.",
      suggestion1: 'Fake courier APK file?',
      suggestion1Query: 'What is the fake courier APK scam?',
      suggestion2: 'Suspicious bank link',
      suggestion2Query: 'I received an SMS with a bank verification link, is it safe?',
      suggestion3: 'What is a romance scam?',
      suggestion3Query: 'What is a romance scam?',
      suggestion4: 'Friend asking for phone credit',
      suggestion4Query: 'A friend is asking for phone credit via WhatsApp, what should I do?',
      inputPlaceholder: 'Type a message or describe a suspicious situation...',
      loginRequired: 'Please log in first.',
      errorFallback: 'Sorry, something went wrong. Please try again shortly.',
      historyCleared: 'Chat history cleared',
      tryQuizCta: '🎓 Try this quiz:',
      attachPhotoTitle: 'Attach a photo',
      removeAttachmentAria: 'Remove attachment',
      dropHint: 'Drop your photo here',
      notAnImage: 'Please drop an image file (JPG, PNG, or WEBP).',
    },
    tips: {
      sectionLabel: 'Quick Tips',
      tip1Title: 'Never Install APK Files from Chat',
      tip1Desc: 'Legitimate apps are only downloaded from Google Play Store or the App Store. An .apk file sent via WhatsApp is almost always malicious.',
      tip2Title: 'OTP Codes Are Strictly Confidential',
      tip2Desc: 'Never share an OTP code with anyone — including someone claiming to be a bank officer, police officer, or government official.',
      tip3Title: 'Verify the Link Address',
      tip3Desc: '"mandiri-online.verify.xyz" is very different from "bankmandiri.co.id" — always confirm the address before clicking.',
      tip4Title: 'Urgency Is a Warning Sign',
      tip4Desc: 'Scammers always create a false sense of urgency. "Your account will be blocked in 30 minutes!" is an intimidation tactic, not a fact.',
    },
    footer: {
      tagline: 'FamilySecure · Family Digital Security Literacy Assistant',
    },
    spinner: { default: 'Processing...' },
  },
  id: {
    meta: {
      title: 'FamilySecure – Asisten Keamanan Digital Keluarga',
      description: 'FamilySecure – Asisten literasi keamanan digital untuk keluarga. Periksa pesan mencurigakan dan uji wawasan Anda dengan kuis interaktif.',
    },
    nav: { points: 'poin', logoutTitle: 'Keluar' },
    hero: {
      badge: '🛡️ Keamanan Digital Keluarga',
      title: 'Lindungi Keluarga dari <em>Penipuan Digital</em>',
      subtitle: 'Periksa pesan atau foto mencurigakan dalam hitungan detik, dan uji wawasan keamanan digital keluarga Anda.',
      ctaPrimary: 'Mulai Sekarang',
      ctaSecondary: 'Tips Keamanan',
    },
    setup: {
      inputLabel: 'Nama Anda',
      inputPlaceholder: 'Contoh: Budi Santoso',
      nameRequired: 'Mohon masukkan nama Anda untuk melanjutkan.',
    },
    auth: {
      tabRegister: 'Buat Akun',
      tabLogin: 'Masuk',
      registerTitle: 'Buat Akun Baru',
      registerDesc: 'Akun Anda menyimpan progres kuis, riwayat chat, dan riwayat pemeriksaan foto di server kami.',
      loginTitle: 'Selamat Datang Kembali',
      loginDesc: 'Masuk untuk melanjutkan progres belajar Anda.',
      emailLabel: 'Email',
      emailPlaceholder: 'anda@contoh.com',
      passwordLabel: 'Kata Sandi',
      passwordHint: 'Minimal 8 karakter',
      registerSubmit: 'Buat Akun →',
      loginSubmit: 'Masuk →',
      emailRequired: 'Mohon masukkan alamat email yang valid.',
      passwordTooShort: 'Kata sandi minimal 8 karakter.',
      registerFailed: 'Pendaftaran gagal. Silakan coba lagi.',
      loginFailed: 'Gagal masuk. Silakan coba lagi.',
      loggedOut: 'Anda telah keluar.',
      passwordSaveHint: 'Simpan baik-baik email dan kata sandi ini — Anda akan memakainya lagi untuk masuk berikutnya.',
      needHelpNote: 'Bingung cara pakainya? Minta bantuan anggota keluarga untuk mendaftar pertama kali.',
      showPasswordAria: 'Tampilkan kata sandi',
      hidePasswordAria: 'Sembunyikan kata sandi',
    },
    history: {
      quizTitle: 'Riwayat Kuis',
      chatTitle: 'Riwayat Percakapan',
      empty: 'Belum ada aktivitas.',
    },
    home: {
      sectionLabel: 'Fitur Utama',
      cardQuizTitle: 'Kuis Keamanan Digital',
      cardQuizDesc: 'Uji wawasan Anda dengan kuis interaktif. Kumpulkan poin dan raih lencana untuk setiap level yang diselesaikan.',
      cardChatTitle: 'Tanya & Periksa Pesan',
      cardChatDesc: 'Ceritakan situasi mencurigakan, unggah tangkapan layar, atau keduanya sekaligus dalam satu percakapan — asisten AI kami siap membantu.',
      cardScoreTitle: 'Skor & Pencapaian',
      cardScoreDesc: 'Lihat progres belajar, lencana yang diraih, dan rekap hasil kuis per topik.',
      emergencyTitle: 'Sudah terlanjur mengklik tautan atau memasang berkas mencurigakan?',
      emergencyDesc: '<strong>Segera hubungi bank Anda</strong> untuk memblokir akun. Nomor darurat biasanya tertera pada kartu ATM atau aplikasi mobile banking.',
      topicFallbackDesc: 'Pilih level kuis untuk topik ini dan uji wawasan Anda.',
    },
    check: {
      safeTag: '✓ Tidak Ada Teks Pesan',
      dangerTag: '⚠️ Terindikasi Bahaya',
      uncertainTag: '❓ Pola Tidak Dikenali',
    },
    quiz: {
      topicHeader: '🎓 Pilih Topik Kuis',
      topicIntro: 'Pilih topik yang ingin Anda pelajari. Setiap topik memiliki 2 level — selesaikan level Dasar terlebih dahulu untuk membuka level Lanjutan.',
      levelPanelPrefix: '🎓',
      levelAvailable: 'Tersedia',
      levelUnlocked: 'Terbuka ✓',
      levelLocked: '🔒 Terkunci',
      levelBasicTitle: '🌱 Level Dasar',
      levelBasicDesc: '3 soal pilihan ganda. Nilai minimal 80% untuk membuka level Lanjutan.',
      levelAdvancedTitle: '🚀 Level Lanjutan',
      levelAdvancedUnlockedDesc: '3 soal tingkat lanjut. Uji kemampuan Anda lebih dalam.',
      levelAdvancedLockedDesc: 'Selesaikan Level Dasar dengan nilai ≥ 80% untuk membuka.',
      loadingProgress: 'Memeriksa progres...',
      loadingQuestions: 'Memuat soal...',
      loadQuestionsFailed: 'Gagal memuat soal',
      questionOf: (idx, total) => `Soal ${idx} dari ${total}`,
      correctCount: (n) => `${n} benar`,
      checkingAnswer: 'Memeriksa jawaban...',
      answerCheckFailed: 'Gagal memeriksa jawaban',
      nextQuestion: 'Soal Berikutnya →',
      finishQuiz: 'Selesai & Lihat Hasil ✓',
      savingResult: 'Menyimpan hasil...',
      saveResultFailed: 'Gagal menyimpan hasil',
      resultScoreLabel: 'Nilai',
      passedTitle: '🎉 Selamat, Anda Lulus!',
      passedSubtitle: (pct) => `Nilai ${pct}% telah melampaui batas kelulusan (80%). Kerja bagus!`,
      unlockedNextSuffix: ' Level Lanjutan kini terbuka untuk Anda.',
      failedTitle: 'Belum Lulus, Jangan Menyerah',
      failedSubtitle: (pct) => `Nilai ${pct}%. Dibutuhkan minimal 80% untuk lulus. Pelajari kembali materi dan coba lagi.`,
      newBadge: '🏅 Lencana Baru: ',
      newBadgeToast: 'Lencana baru diraih! ',
      retryPassed: '🔄 Main Lagi',
      retryFailed: '🔄 Coba Lagi',
      chooseAnotherTopic: 'Pilih Topik Lain',
      viewScore: 'Lihat Skor',
      confirmQuit: 'Yakin ingin keluar dari kuis? Progres soal ini tidak akan disimpan.',
    },
    score: {
      learningProgress: 'Progres Belajar',
      totalPoints: 'Total Poin',
      badgesEarned: 'Lencana yang Diraih',
      backToMenu: '← Kembali ke Menu',
      loadingScore: 'Memuat data skor...',
      loadScoreFailed: 'Gagal memuat data skor',
      noBadges: 'Belum ada lencana. Selesaikan kuis untuk meraih lencana pertama Anda.',
      bestScore: (pct, attempts) => `${pct}% terbaik · ${attempts}x percobaan`,
    },
    chat: {
      header: '💬 Tanya Asisten FamilySecure',
      online: '● Online',
      clearTitle: 'Hapus riwayat chat',
      welcome1: 'Halo, saya asisten FamilySecure.',
      welcome2: 'Anda dapat menceritakan pesan atau situasi yang dicurigai, dan saya akan membantu menjelaskan apakah situasi tersebut berbahaya.',
      suggestion1: 'APK kurir palsu?',
      suggestion1Query: 'Apa itu penipuan APK kurir?',
      suggestion2: 'Tautan bank mencurigakan',
      suggestion2Query: 'Saya menerima SMS berisi tautan verifikasi bank, apakah aman?',
      suggestion3: 'Apa itu love scam?',
      suggestion3Query: 'Apa itu love scam?',
      suggestion4: 'Teman minta pulsa',
      suggestion4Query: 'Teman saya meminta pulsa lewat WhatsApp, apa yang sebaiknya saya lakukan?',
      inputPlaceholder: 'Ketik pesan atau ceritakan situasi yang mencurigakan...',
      loginRequired: 'Silakan masuk terlebih dahulu.',
      errorFallback: 'Maaf, terjadi gangguan. Silakan coba lagi sebentar.',
      historyCleared: 'Riwayat chat dihapus',
      tryQuizCta: '🎓 Coba kuis ini:',
      attachPhotoTitle: 'Lampirkan foto',
      removeAttachmentAria: 'Hapus lampiran',
      dropHint: 'Lepaskan foto Anda di sini',
      notAnImage: 'Mohon lepaskan file gambar (JPG, PNG, atau WEBP).',
    },
    tips: {
      sectionLabel: 'Tips Cepat',
      tip1Title: 'Jangan Instal APK dari Chat',
      tip1Desc: 'Aplikasi resmi hanya diunduh dari Google Play Store atau App Store. File .apk yang dikirim via WhatsApp hampir selalu berbahaya.',
      tip2Title: 'OTP Bersifat Rahasia',
      tip2Desc: 'Kode OTP tidak boleh diberikan kepada siapa pun — termasuk yang mengaku sebagai petugas bank, polisi, atau pejabat pemerintah.',
      tip3Title: 'Periksa Alamat Tautan',
      tip3Desc: '"mandiri-online.verifikasi.xyz" berbeda jauh dari "bankmandiri.co.id" — selalu pastikan alamat sebelum mengklik.',
      tip4Title: 'Tekanan Waktu = Tanda Bahaya',
      tip4Desc: 'Penipu selalu menciptakan rasa urgensi. "Rekening akan diblokir dalam 30 menit!" adalah taktik intimidasi, bukan fakta.',
    },
    footer: {
      tagline: 'FamilySecure · Asisten Literasi Keamanan Digital Keluarga',
    },
    spinner: { default: 'Sedang memproses...' },
  },
};

function t(key, ...args) {
  const parts = key.split('.');
  let node = I18N[state.lang];
  for (const p of parts) {
    node = node?.[p];
  }
  if (typeof node === 'function') return node(...args);
  return node ?? key;
}

// INIT
document.addEventListener('DOMContentLoaded', async () => {
  const savedLang = localStorage.getItem('fs_lang');
  state.lang = savedLang === 'en' ? 'en' : 'id';
  applyLanguage(state.lang);

  await checkSession();

  // Hero CTA
  document.getElementById('hero-cta-btn').addEventListener('click', () => {
    document.getElementById('hero-section').classList.add('hidden');
    document.getElementById('setup-section').classList.remove('hidden');
    switchAuthTab('register');
  });

  // Auth forms
  document.getElementById('register-form').addEventListener('submit', e => { e.preventDefault(); handleRegister(); });
  document.getElementById('login-form').addEventListener('submit', e => { e.preventDefault(); handleLogin(); });

  setupChatDragDrop();
});

// LANGUAGE TOGGLE
function toggleLanguage() {
  state.lang = state.lang === 'id' ? 'en' : 'id';
  localStorage.setItem('fs_lang', state.lang);
  applyLanguage(state.lang);

  if (!document.getElementById('app-section').classList.contains('hidden')) {
    buildTopicList();
    if (!document.getElementById('score-panel').classList.contains('hidden')) {
      loadScorePanel();
    }
  }
}

function applyLanguage(lang) {
  document.documentElement.lang = lang;
  document.title = t('meta.title');
  const metaDesc = document.getElementById('meta-description');
  if (metaDesc) metaDesc.setAttribute('content', t('meta.description'));

  document.getElementById('lang-toggle-label').textContent = lang === 'id' ? 'EN' : 'ID';

  document.querySelectorAll('[data-i18n]').forEach(el => {
    el.textContent = t(el.getAttribute('data-i18n'));
  });
  document.querySelectorAll('[data-i18n-html]').forEach(el => {
    el.innerHTML = t(el.getAttribute('data-i18n-html'));
  });
  document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
    el.setAttribute('placeholder', t(el.getAttribute('data-i18n-placeholder')));
  });
  document.querySelectorAll('[data-i18n-title]').forEach(el => {
    el.setAttribute('title', t(el.getAttribute('data-i18n-title')));
  });
  document.querySelectorAll('[data-i18n-aria-label]').forEach(el => {
    el.setAttribute('aria-label', t(el.getAttribute('data-i18n-aria-label')));
  });
}

// AUTH
async function checkSession() {
  try {
    const res = await fetch(`${API}/api/auth/me`);
    if (res.ok) {
      state.user = await res.json();
      enterApp();
    }
  } catch (e) { /* not logged in — show the landing page */ }
}

function switchAuthTab(tab) {
  const isLogin = tab === 'login';
  document.getElementById('login-form').classList.toggle('hidden', !isLogin);
  document.getElementById('register-form').classList.toggle('hidden', isLogin);
  document.getElementById('tab-login-btn').classList.toggle('active', isLogin);
  document.getElementById('tab-register-btn').classList.toggle('active', !isLogin);
}

function togglePasswordVisibility(inputId, btn) {
  const input = document.getElementById(inputId);
  const willShow = input.type === 'password';
  input.type = willShow ? 'text' : 'password';
  btn.textContent = willShow ? '🙈' : '👁️';
  btn.setAttribute('aria-label', willShow ? t('auth.hidePasswordAria') : t('auth.showPasswordAria'));
}

async function handleRegister() {
  const name = document.getElementById('register-name').value.trim();
  const email = document.getElementById('register-email').value.trim();
  const password = document.getElementById('register-password').value;

  if (!name) { toast(t('setup.nameRequired'), 'warning'); return; }
  if (!email || !email.includes('@')) { toast(t('auth.emailRequired'), 'warning'); return; }
  if (password.length < 8) { toast(t('auth.passwordTooShort'), 'warning'); return; }

  try {
    const res = await fetch(`${API}/api/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, email, password }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || t('auth.registerFailed'));

    state.user = data;
    document.getElementById('setup-section').classList.add('hidden');
    enterApp();
  } catch (err) {
    toast(err.message || t('auth.registerFailed'), 'error');
  }
}

async function handleLogin() {
  const email = document.getElementById('login-email').value.trim();
  const password = document.getElementById('login-password').value;

  if (!email || !email.includes('@')) { toast(t('auth.emailRequired'), 'warning'); return; }
  if (!password) { toast(t('auth.loginFailed'), 'warning'); return; }

  try {
    const res = await fetch(`${API}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || t('auth.loginFailed'));

    state.user = data;
    document.getElementById('setup-section').classList.add('hidden');
    enterApp();
  } catch (err) {
    toast(err.message || t('auth.loginFailed'), 'error');
  }
}

async function logout() {
  try {
    await fetch(`${API}/api/auth/logout`, { method: 'POST' });
  } catch (e) { /* ignore */ }

  state.user = null;
  state.chatHistoryLoaded = false;
  document.getElementById('app-section').classList.add('hidden');
  document.getElementById('nav-user-area').classList.add('hidden');
  document.getElementById('setup-section').classList.add('hidden');
  document.getElementById('hero-section').classList.remove('hidden');
  toast(t('auth.loggedOut'), 'info');
}

function enterApp() {
  document.getElementById('hero-section').classList.add('hidden');
  document.getElementById('setup-section').classList.add('hidden');
  document.getElementById('app-section').classList.remove('hidden');
  document.getElementById('nav-user-area').classList.remove('hidden');
  document.getElementById('nav-score-value').textContent = state.user.total_score;
  buildTopicList();
}

// NAVIGATION HELPERS
const PANELS = ['quiz-panel', 'score-panel', 'chat-panel'];

function showHome() {
  document.getElementById('home-view').classList.remove('hidden');
  PANELS.forEach(p => document.getElementById(p).classList.add('hidden'));
  showView('quiz-topic-view', null);
}

function showPanel(panelId) {
  document.getElementById('home-view').classList.add('hidden');
  PANELS.forEach(p => {
    const el = document.getElementById(p);
    if (p === panelId) el.classList.remove('hidden');
    else el.classList.add('hidden');
  });

  if (panelId === 'score-panel') loadScorePanel();
  if (panelId === 'quiz-panel') {
    showView('quiz-topic-view', null);
  }
  if (panelId === 'chat-panel') loadChatHistoryIntoPanel();
}

function showView(showId, hideId) {
  const quizSubViews = [
    'quiz-topic-view', 'quiz-level-view', 'quiz-qa-view', 'quiz-result-view'
  ];
  quizSubViews.forEach(id => {
    const el = document.getElementById(id);
    if (el) el.classList.toggle('hidden', id !== showId);
  });
}

// CHAT ATTACHMENTS
function handleAttachmentSelected(file) {
  if (!file) return;
  state.pendingAttachment = file;

  const reader = new FileReader();
  reader.onload = ev => { document.getElementById('chat-attachment-thumb').src = ev.target.result; };
  reader.readAsDataURL(file);

  document.getElementById('chat-attachment-name').textContent = file.name;
  document.getElementById('chat-attachment-preview').classList.remove('hidden');
}

function removeAttachment() {
  state.pendingAttachment = null;
  document.getElementById('chat-file-input').value = '';
  document.getElementById('chat-attachment-preview').classList.add('hidden');
}

function setupChatDragDrop() {
  const wrapper = document.getElementById('chat-panel-wrapper');
  const overlay = document.getElementById('chat-drop-overlay');
  if (!wrapper || !overlay) return;

  let dragDepth = 0; // tracks nested dragenter/dragleave across child elements

  wrapper.addEventListener('dragenter', e => {
    e.preventDefault();
    dragDepth++;
    overlay.classList.add('active');
  });
  wrapper.addEventListener('dragover', e => e.preventDefault());
  wrapper.addEventListener('dragleave', e => {
    e.preventDefault();
    dragDepth = Math.max(0, dragDepth - 1);
    if (dragDepth === 0) overlay.classList.remove('active');
  });
  wrapper.addEventListener('drop', e => {
    e.preventDefault();
    dragDepth = 0;
    overlay.classList.remove('active');
    const file = e.dataTransfer.files && e.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) {
      handleAttachmentSelected(file);
    } else if (file) {
      toast(t('chat.notAnImage'), 'warning');
    }
  });
}

function renderContactInfoHtml(contact) {
  if (!contact) return '';
  const renderOne = (c) => {
    const lines = [];
    if (c.nama) lines.push(`<strong>${escapeHtml(c.nama)}</strong>`);
    if (c.telepon) lines.push(`📞 ${escapeHtml(c.telepon)}`);
    if (c.whatsapp) lines.push(`💬 WhatsApp: ${escapeHtml(c.whatsapp)}`);
    if (c.website) lines.push(`🌐 <a href="https://${escapeHtml(c.website)}" target="_blank" rel="noopener noreferrer">${escapeHtml(c.website)}</a>`);
    if (c.email) lines.push(`✉️ ${escapeHtml(c.email)}`);
    if (c.catatan) lines.push(`<span class="official-contact-note">${escapeHtml(c.catatan)}</span>`);
    return `<div class="official-contact-item">${lines.join('<br>')}</div>`;
  };

  if (contact.saluran) {
    const items = Object.values(contact.saluran).map(renderOne).join('');
    return `<div class="official-contact-box"><div class="official-contact-title">📞 ${escapeHtml(contact.nama)}</div>${items}</div>`;
  }
  return `<div class="official-contact-box">${renderOne(contact)}</div>`;
}

// QUIZ — TOPIC & LEVEL SELECTION
async function buildTopicList() {
  try {
    const res    = await fetch(`${API}/api/topics`);
    const topics = await res.json();
    const list   = document.getElementById('topic-list');
    list.innerHTML = '';

    const iconMap = { apk: '📦', link: '🔗' };

    topics.forEach(t_ => {
      const card = document.createElement('div');
      card.className = 'module-card animate-in';
      card.innerHTML = `
        <div class="module-icon">${iconMap[t_.key] || '📋'}</div>
        <div>
          <h3>${t_.title}</h3>
          <p>${t('home.topicFallbackDesc')}</p>
        </div>
        <div class="module-arrow">→</div>`;
      card.addEventListener('click', () => selectTopic(t_.key, t_.title));
      list.appendChild(card);
    });
  } catch (e) {
    console.error('Failed to load topics:', e);
  }
}

async function selectTopic(topicKey, topicTitle) {
  state.currentTopic = topicKey;
  document.getElementById('level-panel-title').textContent = t('quiz.levelPanelPrefix') + ' ' + topicTitle;

  showSpinner(t('quiz.loadingProgress'));
  let userRecord = null;
  try {
    const res  = await fetch(`${API}/api/dashboard`);
    const data = await res.json();
    userRecord = data.user_record;
  } catch (e) { /* ignore */ } finally { hideSpinner(); }

  const topicProgress = userRecord?.progress?.[topicKey] || {};
  const dasarPassed   = topicProgress?.dasar?.passed || false;

  const grid = document.getElementById('level-grid');
  grid.innerHTML = `
    <div class="level-card" onclick="startQuiz('${topicKey}','dasar')">
      <span class="level-badge">${t('quiz.levelAvailable')}</span>
      <h4>${t('quiz.levelBasicTitle')}</h4>
      <p>${t('quiz.levelBasicDesc')}</p>
    </div>
    <div class="level-card ${dasarPassed ? '' : 'locked'}" ${dasarPassed ? `onclick="startQuiz('${topicKey}','lanjutan')"` : ''}>
      <span class="level-badge">${dasarPassed ? t('quiz.levelUnlocked') : t('quiz.levelLocked')}</span>
      <h4>${t('quiz.levelAdvancedTitle')}</h4>
      <p>${dasarPassed ? t('quiz.levelAdvancedUnlockedDesc') : t('quiz.levelAdvancedLockedDesc')}</p>
    </div>`;

  showView('quiz-level-view', 'quiz-topic-view');
}

// QUIZ — Q&A ENGINE
async function startQuiz(topic, level) {
  showSpinner(t('quiz.loadingQuestions'));
  try {
    const res  = await fetch(`${API}/api/quiz/${topic}/${level}`);
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail);

    state.currentTopic  = topic;
    state.currentLevel  = level;
    state.questions     = data.questions;
    state.currentIndex  = 0;
    state.correctCount  = 0;
    state.answered      = false;

    document.getElementById('qa-panel-title').textContent =
      (level === 'dasar' ? t('quiz.levelBasicTitle') : t('quiz.levelAdvancedTitle')) + ' — ' + data.title;

    showView('quiz-qa-view', null);
    renderQuestion();
  } catch (err) {
    toast(err.message || t('quiz.loadQuestionsFailed'), 'error');
  } finally {
    hideSpinner();
  }
}

function renderQuestion() {
  const q     = state.questions[state.currentIndex];
  const total = state.questions.length;
  const idx   = state.currentIndex;

  document.getElementById('progress-text').textContent = t('quiz.questionOf', idx + 1, total);
  document.getElementById('score-text').textContent     = t('quiz.correctCount', state.correctCount);
  document.getElementById('progress-fill').style.width  = `${(idx / total) * 100}%`;

  document.getElementById('quiz-question-text').textContent = q.question;

  const optionsEl = document.getElementById('quiz-options');
  optionsEl.innerHTML = '';
  Object.entries(q.options).forEach(([letter, text]) => {
    const btn = document.createElement('button');
    btn.className = 'option-btn';
    btn.id = `opt-${letter}`;
    btn.innerHTML = `<span class="option-letter">${letter}</span><span>${text}</span>`;
    btn.addEventListener('click', () => submitAnswer(letter));
    optionsEl.appendChild(btn);
  });

  const fb = document.getElementById('quiz-feedback');
  fb.style.display = 'none';
  fb.className = 'quiz-feedback';
  document.getElementById('next-btn').classList.add('hidden');
  state.answered = false;
}

async function submitAnswer(letter) {
  if (state.answered) return;
  state.answered = true;

  document.querySelectorAll('.option-btn').forEach(b => b.disabled = true);

  showSpinner(t('quiz.checkingAnswer'));
  try {
    const res  = await fetch(`${API}/api/quiz/answer`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        topic:   state.currentTopic,
        level:   state.currentLevel,
        index:   state.currentIndex,
        letter:  letter,
      }),
    });
    const data = await res.json();

    const selectedBtn = document.getElementById(`opt-${letter}`);
    const correctBtn  = document.getElementById(`opt-${data.correct_letter}`);

    if (data.correct) {
      selectedBtn.classList.add('correct');
      state.correctCount++;
      document.getElementById('score-text').textContent = t('quiz.correctCount', state.correctCount);
    } else {
      selectedBtn.classList.add('wrong');
      if (correctBtn) correctBtn.classList.add('correct');
    }

    const fb = document.getElementById('quiz-feedback');
    fb.className = `quiz-feedback ${data.correct ? 'correct' : 'wrong'}`;
    fb.textContent = data.explanation;
    fb.style.display = 'block';

    const nextBtn = document.getElementById('next-btn');
    const isLast  = state.currentIndex >= state.questions.length - 1;
    nextBtn.textContent = isLast ? t('quiz.finishQuiz') : t('quiz.nextQuestion');
    nextBtn.classList.remove('hidden');

  } catch (err) {
    toast(t('quiz.answerCheckFailed'), 'error');
    state.answered = false;
  } finally {
    hideSpinner();
  }
}

async function nextQuestion() {
  const isLast = state.currentIndex >= state.questions.length - 1;
  if (isLast) {
    await finishQuiz();
  } else {
    state.currentIndex++;
    renderQuestion();
  }
}

async function finishQuiz() {
  showSpinner(t('quiz.savingResult'));
  try {
    const res  = await fetch(`${API}/api/quiz/finish`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        topic:         state.currentTopic,
        level:         state.currentLevel,
        correct_count: state.correctCount,
        total:         state.questions.length,
      }),
    });
    const data = await res.json();

    showView('quiz-result-view', null);
    renderResult(data);
    refreshNavScore();
  } catch (err) {
    toast(t('quiz.saveResultFailed'), 'error');
  } finally {
    hideSpinner();
  }
}

function renderResult(data) {
  const pct    = data.percent;
  const passed = data.passed;

  const circleEl = document.getElementById('circle-fill');
  const circum   = 2 * Math.PI * 50; // r=50
  const offset   = circum - (pct / 100) * circum;
  const circle   = document.getElementById('score-circle');

  document.getElementById('result-score-num').textContent = pct + '%';
  circle.classList.toggle('low', !passed);

  setTimeout(() => {
    circleEl.style.strokeDashoffset = offset;
  }, 100);

  if (passed) {
    document.getElementById('result-title').textContent   = t('quiz.passedTitle');
    document.getElementById('result-subtitle').textContent =
      t('quiz.passedSubtitle', pct) + (data.unlocked_next ? t('quiz.unlockedNextSuffix') : '');
  } else {
    document.getElementById('result-title').textContent   = t('quiz.failedTitle');
    document.getElementById('result-subtitle').textContent = t('quiz.failedSubtitle', pct);
  }

  const badgeEl = document.getElementById('badge-earned-display');
  if (data.badge_earned) {
    badgeEl.textContent = t('quiz.newBadge') + data.badge_earned;
    badgeEl.classList.remove('hidden');
    toast(t('quiz.newBadgeToast') + data.badge_earned, 'success');
  } else {
    badgeEl.classList.add('hidden');
  }

  document.getElementById('retry-btn').textContent = passed ? t('quiz.retryPassed') : t('quiz.retryFailed');
}

function retryQuiz() {
  startQuiz(state.currentTopic, state.currentLevel);
}

function confirmQuitQuiz() {
  if (state.answered !== undefined && state.currentIndex > 0) {
    if (!confirm(t('quiz.confirmQuit'))) return;
  }
  showView('quiz-level-view', null);
}

// SCORE PANEL
async function loadScorePanel() {
  showSpinner(t('score.loadingScore'));
  try {
    const res  = await fetch(`${API}/api/dashboard`);
    const data = await res.json();
    renderScorePanel(data);
    await loadHistoryPanels();
  } catch (e) {
    toast(t('score.loadScoreFailed'), 'error');
  } finally {
    hideSpinner();
  }
}

function renderScorePanel(data) {
  const rec  = data.user_record;
  const meta = data.topics_meta;

  document.getElementById('score-panel-name').textContent  = rec.name;
  document.getElementById('score-panel-total').textContent = rec.total_score;
  document.getElementById('nav-score-value').textContent   = rec.total_score;

  const grid = document.getElementById('topic-progress-grid');
  grid.innerHTML = '';
  Object.entries(meta).forEach(([key, title]) => {
    const tp  = rec.progress?.[key] || {};
    const card = document.createElement('div');
    card.className = 'topic-progress-card animate-in';
    card.innerHTML = `
      <h4>${title}</h4>
      <div class="level-progress">
        ${renderLevelProgress(t('quiz.levelBasicTitle').replace(/^[^A-Za-z]*/, ''), tp.dasar)}
        ${renderLevelProgress(t('quiz.levelAdvancedTitle').replace(/^[^A-Za-z]*/, ''), tp.lanjutan)}
      </div>`;
    grid.appendChild(card);
  });

  const badgesList = document.getElementById('badges-list');
  if (rec.badges && rec.badges.length) {
    badgesList.innerHTML = rec.badges
      .map(b => `<span class="badge-chip">${b}</span>`)
      .join('');
  } else {
    badgesList.innerHTML = `<p class="no-badges">${t('score.noBadges')}</p>`;
  }
}

function renderLevelProgress(label, lp) {
  if (!lp) return '';
  const pct    = lp.best_score || 0;
  const passed = lp.passed;
  return `
    <div class="level-progress-item">
      <div class="level-progress-header">
        <span class="level-progress-name">${label} ${passed ? '✓' : ''}</span>
        <span class="level-progress-score">${t('score.bestScore', pct, lp.attempts)}</span>
      </div>
      <div class="mini-bar">
        <div class="mini-bar-fill ${passed ? 'passed' : 'failed'}" style="width:${pct}%"></div>
      </div>
    </div>`;
}

async function refreshNavScore() {
  try {
    const res  = await fetch(`${API}/api/dashboard`);
    const data = await res.json();
    document.getElementById('nav-score-value').textContent = data.user_record.total_score;
  } catch (e) { /* silent */ }
}

// HISTORY
function formatDateTime(iso) {
  try {
    return new Date(iso).toLocaleString(state.lang === 'id' ? 'id-ID' : 'en-US', {
      dateStyle: 'medium', timeStyle: 'short',
    });
  } catch (e) { return iso; }
}

async function loadHistoryPanels() {
  try {
    const [quizRes, chatRes] = await Promise.all([
      fetch(`${API}/api/history/quiz`),
      fetch(`${API}/api/history/chat`),
    ]);
    const [quizData, chatData] = await Promise.all([quizRes.json(), chatRes.json()]);
    renderQuizHistory(quizData);
    renderChatHistorySummary(chatData);
  } catch (e) {
    console.error('Failed to load history:', e);
  }
}

function renderQuizHistory(items) {
  const el = document.getElementById('history-quiz-list');
  if (!items.length) { el.innerHTML = `<p class="no-badges">${t('history.empty')}</p>`; return; }
  el.innerHTML = items.map(it => {
    const levelLabel = (it.level === 'dasar' ? t('quiz.levelBasicTitle') : t('quiz.levelAdvancedTitle')).replace(/^[^A-Za-z]*/, '');
    return `
      <div class="history-item">
        <span class="history-item-label">${it.topic.toUpperCase()} · ${levelLabel}</span>
        <span class="history-badge ${it.passed ? 'pass' : 'fail'}">${it.score_percent}%</span>
        <span class="history-time">${formatDateTime(it.created_at)}</span>
      </div>`;
  }).join('');
}

function renderChatHistorySummary(items) {
  const el = document.getElementById('history-chat-list');
  if (!items.length) { el.innerHTML = `<p class="no-badges">${t('history.empty')}</p>`; return; }
  const badgeClass = { danger: 'fail', uncertain: 'uncertain', no_content: 'pass' };
  const badgeLabel = { danger: t('check.dangerTag'), uncertain: t('check.uncertainTag'), no_content: t('check.safeTag') };
  const recent = items.slice(-15);
  el.innerHTML = recent.map(it => {
    const preview = it.content.length > 80 ? it.content.slice(0, 80) + '…' : it.content;
    const statusBadge = (it.has_image && it.status)
      ? `<span class="history-badge ${badgeClass[it.status] || 'pass'}">${badgeLabel[it.status] || it.status}</span>`
      : '';
    return `
      <div class="history-item">
        <span class="history-item-label">${it.role === 'user' ? '🧑' : '🛡️'} ${escapeHtml(preview)}</span>
        ${statusBadge}
        <span class="history-time">${formatDateTime(it.created_at)}</span>
      </div>`;
  }).join('');
}

async function loadChatHistoryIntoPanel() {
  if (state.chatHistoryLoaded) return;
  state.chatHistoryLoaded = true;
  try {
    const res = await fetch(`${API}/api/history/chat`);
    const data = await res.json();
    data.forEach(m => appendBubble(m.role === 'user' ? 'user' : 'bot', m.content, m.has_image ? m.status : null));
  } catch (e) { /* ignore */ }
}

// SPINNER & TOAST
function showSpinner(text) {
  document.getElementById('spinner-text').textContent = text || t('spinner.default');
  document.getElementById('spinner-overlay').classList.add('active');
}
function hideSpinner() {
  document.getElementById('spinner-overlay').classList.remove('active');
}

function toast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  const el = document.createElement('div');
  const icons = { success: '✓', error: '✕', warning: '⚠️', info: 'ℹ️' };
  el.className = `toast ${type}`;
  el.textContent = (icons[type] || '') + ' ' + message;
  container.appendChild(el);
  setTimeout(() => {
    el.style.opacity = '0';
    el.style.transform = 'translateX(20px)';
    el.style.transition = 'all .3s ease';
    setTimeout(() => el.remove(), 300);
  }, 4000);
}

// CHATBOT

function renderStatusTagHtml(status) {
  if (!status) return '';
  const cls = status === 'danger' ? 'danger' : status === 'uncertain' ? 'uncertain' : 'safe';
  const label = status === 'danger' ? t('check.dangerTag') : status === 'uncertain' ? t('check.uncertainTag') : t('check.safeTag');
  return `<span class="bubble-status-tag ${cls}">${escapeHtml(label)}</span><br>`;
}

function prependStatusTag(bubbleEl, status) {
  if (!bubbleEl || !status) return;
  const content = bubbleEl.querySelector('.bubble-content');
  if (content) content.insertAdjacentHTML('afterbegin', renderStatusTagHtml(status));
}

function appendBubble(role, text, statusTag) {
  const container = document.getElementById('chat-messages');
  const div = document.createElement('div');
  div.className = `chat-bubble ${role}`;
  const tagHtml = renderStatusTagHtml(statusTag);

  if (role === 'bot') {
    div.innerHTML = `
      <div class="bubble-avatar">🛡️</div>
      <div class="bubble-content">${tagHtml}<p>${escapeHtml(text).replace(/\n/g, '<br>')}</p></div>`;
  } else {
    div.innerHTML = `<div class="bubble-content user-bubble">${tagHtml}<p>${escapeHtml(text).replace(/\n/g, '<br>')}</p></div>`;
  }

  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
  return div;
}

function appendUserBubbleLive(message, attachment) {
  const container = document.getElementById('chat-messages');
  const div = document.createElement('div');
  div.className = 'chat-bubble user';
  const imgHtml = attachment ? `<img class="chat-bubble-photo" src="${URL.createObjectURL(attachment)}" alt="Attached photo" />` : '';
  const textHtml = message ? `<p>${escapeHtml(message).replace(/\n/g, '<br>')}</p>` : '';
  div.innerHTML = `<div class="bubble-content user-bubble">${imgHtml}${textHtml}</div>`;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
  return div;
}

function appendTyping() {
  const container = document.getElementById('chat-messages');
  const div = document.createElement('div');
  div.className = 'chat-bubble bot typing-indicator-wrap';
  div.id = 'typing-indicator';
  div.innerHTML = `
    <div class="bubble-avatar">🛡️</div>
    <div class="bubble-content"><span class="typing-dots"><span></span><span></span><span></span></span></div>`;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
  return div;
}

function removeTyping() {
  const el = document.getElementById('typing-indicator');
  if (el) el.remove();
}

function escapeHtml(text) {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

async function sendChat() {
  const inputEl    = document.getElementById('chat-input');
  const sendBtn    = document.getElementById('chat-send-btn');
  const message    = inputEl.value.trim();
  const attachment = state.pendingAttachment;

  if (!message && !attachment) return;
  if (!state.user) { toast(t('chat.loginRequired'), 'warning'); return; }

  const userBubbleEl = appendUserBubbleLive(message, attachment);
  inputEl.value = '';
  inputEl.style.height = 'auto';
  removeAttachment();
  sendBtn.disabled = true;

  appendTyping();

  try {
    const formData = new FormData();
    formData.append('message', message);
    if (attachment) formData.append('file', attachment);

    const res  = await fetch(`${API}/api/chat`, { method: 'POST', body: formData });
    const data = await res.json();

    removeTyping();
    if (!res.ok) throw new Error(data.detail || 'Request failed');

    if (data.status) prependStatusTag(userBubbleEl, data.status);
    appendBubble('bot', data.reply);
    if (data.official_contact) appendOfficialContact(data.official_contact);
    if (data.suggested_quiz) appendQuizSuggestion(data.suggested_quiz);
  } catch (err) {
    removeTyping();
    appendBubble('bot', t('chat.errorFallback'));
    toast(err.message, 'error');
  } finally {
    sendBtn.disabled = false;
    inputEl.focus();
  }
}

function appendOfficialContact(contact) {
  const container = document.getElementById('chat-messages');
  const div = document.createElement('div');
  div.className = 'chat-bubble bot';
  div.innerHTML = `
    <div class="bubble-avatar">🛡️</div>
    <div class="bubble-content">${renderContactInfoHtml(contact)}</div>`;
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

function appendQuizSuggestion(suggestedQuiz) {
  const container = document.getElementById('chat-messages');
  const div = document.createElement('div');
  div.className = 'chat-bubble bot';
  div.innerHTML = `
    <div class="bubble-avatar">🛡️</div>
    <div class="bubble-content">
      <div class="chat-suggestions">
        <button class="suggestion-chip">
          ${escapeHtml(t('chat.tryQuizCta'))} ${escapeHtml(suggestedQuiz.title)}
        </button>
      </div>
    </div>`;
  const btn = div.querySelector('button');
  btn.addEventListener('click', () => {
    showPanel('quiz-panel');
    selectTopic(suggestedQuiz.topic_key, suggestedQuiz.title);
  });
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
}

function sendSuggestion(text) {
  const inputEl = document.getElementById('chat-input');
  inputEl.value = text;
  sendChat();
}

async function clearChat() {
  if (!state.user) return;
  try {
    await fetch(`${API}/api/chat/history`, { method: 'DELETE' });
  } catch (e) { /* ignore */ }

  const container = document.getElementById('chat-messages');
  [...container.children].forEach(el => {
    if (el.id !== 'chat-welcome') el.remove();
  });
  state.chatHistoryLoaded = true; // avoid re-loading now-deleted history on next panel open
  toast(t('chat.historyCleared'), 'info');
}

// Auto-resize textarea
document.addEventListener('DOMContentLoaded', () => {
  const chatInput = document.getElementById('chat-input');
  if (chatInput) {
    chatInput.addEventListener('input', () => {
      chatInput.style.height = 'auto';
      chatInput.style.height = Math.min(chatInput.scrollHeight, 120) + 'px';
    });
    chatInput.addEventListener('keydown', e => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendChat();
      }
    });
  }
});
