from pydantic import BaseModel
from datetime import date
from typing import List, Optional

class ContractBase(BaseModel):
    contract_number: Optional[str] = None
    partner: str
    contract_date: Optional[date] = None
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

class ExpenseBase(BaseModel):
    amount: float
    date: date
    description: str = None

class ExpenseCreate(ExpenseBase):
    budget_id: int

class ExpenseResponse(ExpenseBase):
    id: int
    budget_id: int
    class Config:
        orm_mode = True

class BudgetBase(BaseModel):
    contract_number: Optional[str] = None
    initial_amount: float
    start_date: date
    end_date: date

class BudgetCreate(BudgetBase):
    pass

class BudgetResponse(BudgetBase):
    id: int
    expenses: List[ExpenseResponse] = []
    class Config:
        orm_mode = True

class InvoiceBase(BaseModel):
    invoice_number: str
    invoice_date: date
    contract_number: Optional[str] = None
    cost_center: str
    amount_net: float

class InvoiceCreate(InvoiceBase):
    pass

class InvoiceResponse(InvoiceBase):
    id: int
    amount_gross: float
    class Config:
        orm_mode = True
