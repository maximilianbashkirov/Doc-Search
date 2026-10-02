from datetime import datetime
from sqlalchemy import String, DateTime, Text, ARRAY
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

class Base(DeclarativeBase):
    pass

class DocumentModel(Base):
    __tablename__ = "documents"

    # первичный ключ
    id: Mapped[str] = mapped_column(String, primary_key=True)
    
    # список рубрик
    rubrics: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)
    
    # текстовое поле
    text: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Дата создания документа
    created_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
