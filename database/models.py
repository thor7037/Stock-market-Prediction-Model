"""SQLAlchemy ORM models for market data."""

from sqlalchemy import Column, DateTime, Float, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class OHLCV(Base):
    __tablename__ = "ohlcv"

    id = Column(Integer, primary_key=True, autoincrement=True)
    symbol = Column(String, index=True, nullable=False)
    timestamp = Column(DateTime, index=True, nullable=False)
    open = Column(Float)
    high = Column(Float)
    low = Column(Float)
    close = Column(Float)
    volume = Column(Float)
