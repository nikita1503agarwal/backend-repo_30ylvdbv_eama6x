import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Literal

from database import db, create_document, get_documents
from schemas import User, Profile, ChatMessage, Doubt, Flashcard, FlashcardItem, Quiz, QuizQuestion, StudyPlan, StudyTask, NoteSummary, SavedItem

app = FastAPI(title="Study Buddy API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Study Buddy Backend running"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    return response


# ---------- Auth & Profile (placeholder simple flows) ----------
class LoginRequest(BaseModel):
    provider: Literal["email", "phone", "google"] = "email"
    identifier: str
    name: Optional[str] = None


@app.post("/auth/login")
def login(req: LoginRequest):
    user = {
        "name": req.name or "Student",
        "email": req.identifier if req.provider == "email" else None,
        "phone": req.identifier if req.provider == "phone" else None,
        "provider": req.provider,
        "preferred_language": "English",
    }
    user_id = create_document("user", user)
    return {"user_id": user_id, "message": "Logged in"}


class ProfileSetup(BaseModel):
    user_id: str
    grade: Optional[str] = None
    subjects: List[str] = []
    study_goal: Optional[str] = None
    preferred_language: Optional[str] = "English"
    daily_study_minutes: int = 20


@app.post("/profile/setup")
def setup_profile(data: ProfileSetup):
    profile = {
        "user_id": data.user_id,
        "grade": data.grade,
        "subjects": data.subjects,
        "study_goal": data.study_goal,
        "daily_study_minutes": data.daily_study_minutes,
    }
    pid = create_document("profile", profile)
    return {"profile_id": pid}


# ---------- AI-lite utility generators (rule-based for demo) ----------
class ChatRequest(BaseModel):
    user_id: str
    message: str
    subject: Optional[str] = None
    action: Optional[Literal["simplify", "explain10", "flashcards", "quiz"]] = None


@app.post("/chat")
def chat(req: ChatRequest):
    # Very simple rule-based response for demo
    msg = req.message.strip()
    if req.action == "explain10":
        answer = f"Imagine you are 10: {msg} means we break it into super simple ideas and examples so it's easy to get."
    elif req.action == "simplify":
        answer = f"Simplified: {msg} in plain words with fewer steps."
    elif req.action == "flashcards":
        items = [
            {"question": f"What is: {msg}?", "answer": "Definition in 1-2 lines"},
            {"question": f"Why is {msg} important?", "answer": "Key reason"},
        ]
        fid = create_document("flashcard", {"user_id": req.user_id, "topic": msg, "items": items})
        return {"type": "flashcards", "flashcard_id": fid, "items": items}
    elif req.action == "quiz":
        questions = [
            {"question": f"Explain {msg} in one line", "type": "short"},
            {"question": f"Which is true about {msg}?", "type": "mcq", "options": ["A", "B", "C", "D"], "answer": "A"},
        ]
        qid = create_document("quiz", {"user_id": req.user_id, "topic": msg, "questions": questions})
        return {"type": "quiz", "quiz_id": qid, "questions": questions}
    else:
        answer = f"Answer for '{msg}': here's a clear explanation with steps where needed."

    did = create_document("doubt", {"user_id": req.user_id, "source": "text", "prompt": msg, "answer": answer})
    return {"type": "answer", "doubt_id": did, "answer": answer}


# ---------- Photo Doubt (mock OCR) ----------
@app.post("/photo-doubt")
def photo_doubt(user_id: str, file: UploadFile = File(...)):
    filename = file.filename or "image.jpg"
    # Mock OCR result
    ocr_text = f"Extracted text from {filename}"
    answer = f"Solution based on OCR: {ocr_text}. If unclear, please retake a brighter photo."
    did = create_document("doubt", {"user_id": user_id, "source": "image", "image_url": filename, "ocr_text": ocr_text, "answer": answer})
    return {"doubt_id": did, "ocr_text": ocr_text, "answer": answer}


# ---------- Flashcards Generator ----------
class FlashcardRequest(BaseModel):
    user_id: str
    subject: Optional[str] = None
    topic: Optional[str] = None
    text: Optional[str] = None
    count: int = 5


@app.post("/flashcards")
def generate_flashcards(req: FlashcardRequest):
    items = []
    for i in range(max(1, min(req.count, 20))):
        items.append({"question": f"Q{i+1} about {req.topic or 'topic'}", "answer": "Concise answer"})
    fid = create_document("flashcard", {"user_id": req.user_id, "subject": req.subject, "topic": req.topic, "items": items})
    return {"flashcard_id": fid, "items": items}


# ---------- Quiz Generator ----------
class QuizRequest(BaseModel):
    user_id: str
    topic: str
    count: Literal[5, 10] = 5


@app.post("/quiz")
def generate_quiz(req: QuizRequest):
    questions: List[dict] = []
    for i in range(req.count):
        if i % 2 == 0:
            questions.append({"question": f"MCQ on {req.topic} #{i+1}", "type": "mcq", "options": ["A", "B", "C", "D"], "answer": "A"})
        else:
            questions.append({"question": f"Short answer on {req.topic} #{i+1}", "type": "short"})
    qid = create_document("quiz", {"user_id": req.user_id, "topic": req.topic, "questions": questions})
    return {"quiz_id": qid, "questions": questions}


# ---------- Study Planner ----------
class PlanRequest(BaseModel):
    user_id: str
    exam_date: str
    daily_minutes: int
    subjects: List[str]


@app.post("/planner")
def create_plan(req: PlanRequest):
    # naive daily tasks distribution
    tasks: List[dict] = []
    per_day = max(1, req.daily_minutes // max(1, len(req.subjects)))
    for idx, subject in enumerate(req.subjects):
        tasks.append({"date": f"D+{idx+1}", "subject": subject, "topic": f"Core concepts {idx+1}", "minutes": per_day})
    pid = create_document("studyplan", {"user_id": req.user_id, "exam_date": req.exam_date, "daily_minutes": req.daily_minutes, "subjects": req.subjects, "tasks": tasks})
    return {"plan_id": pid, "tasks": tasks}


# ---------- Notes Summary ----------
class SummaryRequest(BaseModel):
    user_id: str
    subject: Optional[str] = None
    text: str


@app.post("/summary")
def summarize(req: SummaryRequest):
    bullets = ["Key point 1", "Key point 2", "Key point 3", "Key point 4", "Key point 5"]
    explanation = "Short explanation combining the key points in simple language."
    sid = create_document("notesummary", {"user_id": req.user_id, "subject": req.subject, "text": req.text, "bullets": bullets, "explanation": explanation})
    return {"summary_id": sid, "bullets": bullets, "explanation": explanation}


# ---------- Saved Library (list recent) ----------
@app.get("/library/{user_id}")
def library(user_id: str):
    recent_doubts = get_documents("doubt", {"user_id": user_id}, limit=10)
    recent_flash = get_documents("flashcard", {"user_id": user_id}, limit=10)
    recent_quiz = get_documents("quiz", {"user_id": user_id}, limit=10)
    recent_plans = get_documents("studyplan", {"user_id": user_id}, limit=5)
    recent_summaries = get_documents("notesummary", {"user_id": user_id}, limit=10)
    return {
        "recent_doubts": recent_doubts,
        "flashcards": recent_flash,
        "quizzes": recent_quiz,
        "plans": recent_plans,
        "summaries": recent_summaries,
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
