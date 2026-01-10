from sqlalchemy import Column, Integer, String, Date, Float, Text
from .database import Base

class Contract(Base):
    __tablename__ = "contracts"

    id = Column(Integer, primary_key=True, index=True)
    partner = Column(String, index=True)
    start_date = Column(Date)
    end_date = Column(Date)
    notice_period = Column(String)
    amount = Column(Float)
    category = Column(String)
    document_path = Column(String)
    notes = Column(Text)
