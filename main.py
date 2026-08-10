import os
import logging
from contextlib import asynccontextmanager

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request, Response, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from api.database import get_db, init_db
from api.models import User, QuizProgress, Badge, QuizAttempt, ChatMessage
from api.auth import hash_password, verify_password, set_session_cookie, clear_session_cookie, get_current_user
from api.schemas import (
    RegisterRequest, LoginRequest, UserOut,
    AnswerSubmission, QuizFinish, QuizAttemptOut,
    ChatMessageOut,
)
from api.rate_limit import (
    check_rate_limit, record_event,
    photo_bucket, login_bucket, register_bucket, chat_bucket,
)
from api.rag import init_rag
from api.ai import analyze_image_with_gemini, NO_TEXT_SIGNAL, AIServiceError
from api.agent import run_scam_agent, CHATBOT_SYSTEM_PROMPT, IMAGE_CONTENT_MARKER
from api.quiz import QUIZ_BANK, BADGE_MAP

# Konfigurasi Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("backend.log", encoding="utf-8"), logging.StreamHandler()]
)
logger = logging.getLogger("familysecure_backend")


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_rag()
    init_db()
    logger.info("Backend FamilySecure siap berjalan.")

    yield

    logger.info("Backend dimatikan.")

app = FastAPI(title="FamilySecure API", lifespan=lifespan)

ALLOWED_ORIGINS = [o.strip() for o in os.environ.get("ALLOWED_ORIGINS", "").split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=bool(ALLOWED_ORIGINS),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Batas ukuran unggahan foto dan tipe berkas yang diizinkan
MAX_UPLOAD_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB
ALLOWED_IMAGE_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def _client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


# =====================================================================
# AUTH ENDPOINTS
# =====================================================================
@app.post("/api/auth/register", response_model=UserOut)
async def register(payload: RegisterRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    ip = _client_ip(request)
    if check_rate_limit(register_bucket, ip, max_count=5, window_seconds=3600):
        raise HTTPException(status_code=429, detail="Terlalu banyak percobaan pendaftaran. Coba lagi nanti.")
    record_event(register_bucket, ip)

    email = payload.email.lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="Email sudah terdaftar.")

    user = User(email=email, name=payload.name, hashed_password=hash_password(payload.password))
    db.add(user)
    db.flush()

    for topic_key in QUIZ_BANK:
        for level in ("dasar", "lanjutan"):
            db.add(QuizProgress(user_id=user.id, topic=topic_key, level=level))

    db.commit()
    db.refresh(user)

    set_session_cookie(response, user.id)
    return user


@app.post("/api/auth/login", response_model=UserOut)
async def login(payload: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)):
    email = payload.email.lower()
    if check_rate_limit(login_bucket, email, max_count=10, window_seconds=600):
        raise HTTPException(status_code=429, detail="Terlalu banyak percobaan masuk. Coba lagi dalam 10 menit.")

    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        record_event(login_bucket, email)
        raise HTTPException(status_code=401, detail="Email atau kata sandi salah.")

    set_session_cookie(response, user.id)
    return user


@app.post("/api/auth/logout")
async def logout(response: Response):
    clear_session_cookie(response)
    return {"status": "ok"}


@app.get("/api/auth/me", response_model=UserOut)
async def me(current_user: User = Depends(get_current_user)):
    return current_user


# =====================================================================
# ENDPOINTS KUIS
# =====================================================================
@app.get("/api/topics")
async def get_topics():
    topics = [{"key": k, "title": v["title"]} for k, v in QUIZ_BANK.items()]
    return topics


@app.get("/api/quiz/{topic}/{level}")
async def get_quiz(
    topic: str, level: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if topic not in QUIZ_BANK or level not in QUIZ_BANK[topic]:
        raise HTTPException(status_code=404, detail="Topik/level tidak ditemukan")

    if level != "dasar":
        dasar_progress = db.query(QuizProgress).filter_by(
            user_id=current_user.id, topic=topic, level="dasar"
        ).first()
        if not (dasar_progress and dasar_progress.passed):
            raise HTTPException(status_code=403, detail="Level masih terkunci. Selesaikan level Dasar terlebih dahulu.")

    questions = QUIZ_BANK[topic][level]
    safe_questions = [{"question": q["question"], "options": q["options"]} for q in questions]

    return {
        "title": QUIZ_BANK[topic]["title"],
        "questions": safe_questions
    }


@app.post("/api/quiz/answer")
async def check_answer(submission: AnswerSubmission, current_user: User = Depends(get_current_user)):
    topic, level, idx, letter = submission.topic, submission.level, submission.index, submission.letter
    if topic not in QUIZ_BANK or level not in QUIZ_BANK[topic]:
        raise HTTPException(status_code=404, detail="Data kuis tidak valid")

    questions = QUIZ_BANK[topic][level]
    if idx < 0 or idx >= len(questions):
        raise HTTPException(status_code=400, detail="Indeks soal tidak valid")

    q = questions[idx]
    is_correct = (letter.upper() == q["correct"].upper())

    return {
        "correct": is_correct,
        "explanation": q["explanation"],
        "correct_letter": q["correct"]
    }


@app.post("/api/quiz/finish")
async def finish_quiz(
    finish_data: QuizFinish,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    topic, level = finish_data.topic, finish_data.level
    if topic not in QUIZ_BANK or level not in QUIZ_BANK[topic]:
        raise HTTPException(status_code=404, detail="Topik/level tidak ditemukan")

    pct = int((finish_data.correct_count / finish_data.total) * 100)
    passed = pct >= 80

    progress = db.query(QuizProgress).filter_by(
        user_id=current_user.id, topic=topic, level=level
    ).first()
    if progress is None:
        progress = QuizProgress(user_id=current_user.id, topic=topic, level=level)
        db.add(progress)

    progress.attempts += 1
    if pct > progress.best_score:
        progress.best_score = pct
    if passed:
        progress.passed = True

    # Gamifikasi
    current_user.total_score += finish_data.correct_count * 10
    if passed and finish_data.correct_count == finish_data.total:
        current_user.total_score += 15  # Bonus sempurna

    badge_earned = None
    badge_name = BADGE_MAP.get((topic, level))
    if passed and badge_name:
        existing_badge = db.query(Badge).filter_by(user_id=current_user.id, name=badge_name).first()
        if not existing_badge:
            db.add(Badge(user_id=current_user.id, name=badge_name))
            badge_earned = badge_name

    db.add(QuizAttempt(
        user_id=current_user.id, topic=topic, level=level,
        score_percent=pct, passed=passed,
    ))

    db.commit()

    return {
        "percent": pct,
        "passed": passed,
        "unlocked_next": passed and level == "dasar",
        "badge_earned": badge_earned
    }


# =====================================================================
# CHAT
# =====================================================================
@app.post("/api/chat")
async def chat(
    message: str = Form(""),
    file: UploadFile | None = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    user_message = message.strip()
    has_image = file is not None and bool(file.filename)

    if not user_message and not has_image:
        raise HTTPException(status_code=400, detail="Pesan atau foto harus diisi.")

    key = str(current_user.id)
    if has_image:
        bucket, max_count, window, limit_detail = (
            photo_bucket, 5, 600, "Batas pemeriksaan foto tercapai. Silakan coba lagi dalam 10 menit."
        )
    else:
        bucket, max_count, window, limit_detail = (
            chat_bucket, 30, 600, "Terlalu banyak pesan chat. Coba lagi beberapa saat lagi."
        )
    if check_rate_limit(bucket, key, max_count=max_count, window_seconds=window):
        raise HTTPException(status_code=429, detail=limit_detail)
    record_event(bucket, key)

    status = None
    combined_message = user_message
    stored_user_content = user_message

    if has_image:
        file_ext = os.path.splitext(file.filename or "")[1].lower()
        if file.content_type not in ALLOWED_IMAGE_CONTENT_TYPES or file_ext not in ALLOWED_IMAGE_EXTENSIONS:
            raise HTTPException(status_code=400, detail="Mohon unggah file gambar dengan format JPG, PNG, atau WEBP.")

        image_bytes = await file.read()
        if len(image_bytes) > MAX_UPLOAD_SIZE_BYTES:
            raise HTTPException(status_code=413, detail="Ukuran file terlalu besar. Maksimum 5 MB.")
        if not image_bytes:
            raise HTTPException(status_code=400, detail="File gambar kosong atau tidak valid.")

        try:
            extracted_text = analyze_image_with_gemini(image_bytes)
        except AIServiceError as e:
            logger.error(f"Analisis gambar gagal: {e}")
            raise HTTPException(
                status_code=503,
                detail="Layanan analisis AI sedang tidak tersedia atau sibuk. Silakan coba lagi dalam beberapa saat."
            )

        stored_user_content = ("📷 " + user_message) if user_message else "📷 [Foto diunggah]"

        if extracted_text == NO_TEXT_SIGNAL and not user_message:
            status = "no_content"
            reply = (
                "Gambar ini tidak mengandung teks percakapan atau pesan yang perlu dianalisis. "
                "Silakan unggah tangkapan layar percakapan, SMS, atau pesan WhatsApp yang mencurigakan."
            )
            db.add(ChatMessage(user_id=current_user.id, role="user", content=stored_user_content, has_image=True, status=status))
            db.add(ChatMessage(user_id=current_user.id, role="model", content=reply))
            db.commit()
            return {"reply": reply, "status": status, "suggested_quiz": None, "official_contact": None}

        if extracted_text != NO_TEXT_SIGNAL:
            combined_message = f"{IMAGE_CONTENT_MARKER} {extracted_text}"
            if user_message:
                combined_message += f"\n\nPesan pengguna: {user_message}"

    recent = (
        db.query(ChatMessage)
        .filter_by(user_id=current_user.id)
        .order_by(ChatMessage.created_at.desc())
        .limit(40)
        .all()
    )
    history = [{"role": m.role, "content": m.content} for m in reversed(recent)]

    try:
        result = run_scam_agent(CHATBOT_SYSTEM_PROMPT, combined_message, history=history)
    except AIServiceError as e:
        logger.error(f"Agent chat gagal: {e}")
        raise HTTPException(
            status_code=503,
            detail="Layanan chatbot sedang tidak tersedia atau sibuk. Silakan coba lagi dalam beberapa saat."
        )

    reply = result["reply"]
    if has_image:
        status = "danger" if result["matched_scenario"] else "uncertain"

    db.add(ChatMessage(user_id=current_user.id, role="user", content=stored_user_content, has_image=has_image, status=status))
    db.add(ChatMessage(user_id=current_user.id, role="model", content=reply))
    db.commit()

    return {
        "reply": reply, "status": status,
        "suggested_quiz": result["suggested_quiz"], "official_contact": result["official_contact"],
    }


@app.delete("/api/chat/history")
async def clear_chat(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.query(ChatMessage).filter_by(user_id=current_user.id).delete()
    db.commit()
    return {"status": "ok", "message": "Riwayat chat dihapus."}


# =====================================================================
# DASHBOARD
# =====================================================================
@app.get("/api/dashboard")
async def get_dashboard(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    progress_rows = db.query(QuizProgress).filter_by(user_id=current_user.id).all()
    progress = {}
    for row in progress_rows:
        progress.setdefault(row.topic, {})[row.level] = {
            "attempts": row.attempts,
            "best_score": row.best_score,
            "passed": row.passed,
        }

    badges = [b.name for b in db.query(Badge).filter_by(user_id=current_user.id).all()]
    meta = {k: v["title"] for k, v in QUIZ_BANK.items()}

    return {
        "user_record": {
            "name": current_user.name,
            "total_score": current_user.total_score,
            "badges": badges,
            "progress": progress,
        },
        "topics_meta": meta,
    }


# =====================================================================
# HISTORY
# =====================================================================
@app.get("/api/history/quiz", response_model=list[QuizAttemptOut])
async def history_quiz(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return (
        db.query(QuizAttempt)
        .filter_by(user_id=current_user.id)
        .order_by(QuizAttempt.created_at.desc())
        .limit(50)
        .all()
    )


@app.get("/api/history/chat", response_model=list[ChatMessageOut])
async def history_chat(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return (
        db.query(ChatMessage)
        .filter_by(user_id=current_user.id)
        .order_by(ChatMessage.created_at.asc())
        .limit(200)
        .all()
    )


# =====================================================================
# SERVE FRONTEND (STATIC FILES)
# =====================================================================
if os.path.exists("frontend"):
    app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
else:
    logger.warning("Folder 'frontend' tidak ditemukan. Mode headless aktif.")
