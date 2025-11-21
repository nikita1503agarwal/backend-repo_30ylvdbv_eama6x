"""
Database Schemas for Study App

Each Pydantic model corresponds to a MongoDB collection. The collection
name is the lowercase of the class name.
"""

from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Literal, Dict, Any
from datetime import datetime


class User(BaseModel):
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    provider: Literal["email", "phone", "google"] = "email"
    preferred_language: Literal["Hindi", "English", "Hinglish"] = "English"


class Profile(BaseModel):
    user_id: str
    grade: Optional[str] = None
    subjects: List[str] = []
    study_goal: Optional[Literal["exam", "homework", "preparation"]] = None
    daily_study_minutes: int = 20
    badges: List[str] = []


class ChatMessage(BaseModel):
    user_id: str
    role: Literal["user", "assistant"]
    content: str
    subject: Optional[str] = None
    quick_action: Optional[Literal["simplify", "explain10", "flashcards", "quiz"]] = None


class Doubt(BaseModel):
    user_id: str
    source: Literal["text", "image"] = "text"
    prompt: Optional[str] = None
    image_url: Optional[str] = None
    ocr_text: Optional[str] = None
    answer: Optional[str] = None
    clarity: Optional[Literal["good", "unclear"]] = None


class FlashcardItem(BaseModel):
    question: str
    answer: str


class Flashcard(BaseModel):
    user_id: str
    subject: Optional[str] = None
    topic: Optional[str] = None
    items: List[FlashcardItem]


class QuizQuestion(BaseModel):
    question: str
    type: Literal["mcq", "short"] = "mcq"
    options: Optional[List[str]] = None
    answer: Optional[str] = None


class Quiz(BaseModel):
    user_id: str
    topic: str
    questions: List[QuizQuestion]
    score: Optional[int] = None


class StudyTask(BaseModel):
    date: str
    subject: Optional[str] = None
    topic: str
    minutes: int


class StudyPlan(BaseModel):
    user_id: str
    exam_date: str
    daily_minutes: int
    subjects: List[str]
    tasks: List[StudyTask]


class NoteSummary(BaseModel):
    user_id: str
    subject: Optional[str] = None
    text: str
    bullets: List[str]
    explanation: str


class SavedItem(BaseModel):
    user_id: str
    type: Literal["chat", "flashcards", "quiz", "plan", "doubt", "summary"]
    ref_id: Optional[str] = None
    meta: Dict[str, Any] = {}
