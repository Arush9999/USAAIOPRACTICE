from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class SignupIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    display_name: str = Field(min_length=1, max_length=80)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class AuthOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class AttemptIn(BaseModel):
    public_id: str
    submitted: str
    hints_used: int = Field(default=0, ge=0)


class SettingsIn(BaseModel):
    display_name: str | None = Field(default=None, max_length=80)
    weekly_hours: int | None = Field(default=None, ge=1, le=40)
    theme: Literal["light", "dark", "system"] | None = None


class ProjectCompleteIn(BaseModel):
    completed: bool = True
    last_code: str = ""


class TestStartIn(BaseModel):
    mode: str = "practice"
    round: int | None = Field(default=None, ge=1, le=2)
    difficulty: Literal["easy", "medium", "hard", "mixed"] = "mixed"
    count: int = Field(default=10, ge=1, le=100)
    timed: bool = False
    time_limit_sec: int = Field(default=0, ge=0, le=86400)


class TestSubmitIn(BaseModel):
    answers: dict[str, str]


class TutorMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str = Field(min_length=1, max_length=12000)


class TutorChatIn(BaseModel):
    messages: list[TutorMessage] = Field(min_length=1, max_length=30)
    topic_slug: str | None = None
