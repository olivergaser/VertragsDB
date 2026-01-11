from sqlalchemy import Column, Integer, String, Date, Float, Text, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

class Contract(Base):
    __tablename__ = "contracts"

    id = Column(Integer, primary_key=True, index=True)
    contract_number = Column(String, index=True, nullable=True)
    partner = Column(String, index=True)
    start_date = Column(Date)
    end_date = Column(Date)
    notice_period = Column(String)
    amount = Column(Float)
    category = Column(String)
    document_path = Column(String)
    notes = Column(Text)

class Budget(Base):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, index=True)
    contract_number = Column(String, index=True, nullable=True)
    initial_amount = Column(Float)
    start_date = Column(Date)
    end_date = Column(Date)
    
    expenses = relationship("Expense", back_populates="budget")

class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    budget_id = Column(Integer, ForeignKey("budgets.id"))
    amount = Column(Float)
    date = Column(Date)
    description = Column(String, nullable=True)

    budget = relationship("Budget", back_populates="expenses")
