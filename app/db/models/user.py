"""
User and ChatHistory models.
"""
import uuid
from sqlalchemy import String, Boolean, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base, TimestampMixin

class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True, index=True)
    username: Mapped[str | None] = mapped_column(String(64), unique=True, nullable=True, index=True)
    display_name: Mapped[str | None] = mapped_column(String(128))
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    role: Mapped[str] = mapped_column(String(32), default="free", nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    def __repr__(self) -> str:
        return f"<User {self.id[:8]} {self.username or self.email or 'anon'}>"


class ChatHistory(Base, TimestampMixin):
    __tablename__ = "chat_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    message: Mapped[str] = mapped_column(Text, nullable=False)
    response: Mapped[str] = mapped_column(Text, nullable=False)
    pii_detected: Mapped[int] = mapped_column(default=0)
    
    user: Mapped["User"] = relationship("User")