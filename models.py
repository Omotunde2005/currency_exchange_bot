from sqlalchemy import Boolean, Column, Integer, String
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    chat_id = Column(Integer, unique=True, nullable=False)
    base_currency = Column(String, unique=False, nullable=False)
    currency_pairs = Column(String, unique=False, nullable=False)
    receive_updates = Column(Boolean, nullable=False, unique=False, default=False)