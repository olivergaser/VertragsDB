from pydantic import BaseModel
from datetime import date

class ContractBase(BaseModel):
    partner: str
    start_date: date
    end_date: date
    notice_period: str
    amount: float
    category: str
    notes: str = None

class ContractCreate(ContractBase):
    pass

class ContractResponse(ContractBase):
    id: int
    document_path: str = None

    class Config:
        orm_mode = True
