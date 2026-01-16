from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from .models import Contract, Base, Budget, Expense, Invoice
from .database import engine, SessionLocal
from .schemas import ContractCreate, ContractResponse, BudgetCreate, BudgetResponse, ExpenseCreate, ExpenseResponse, InvoiceCreate, InvoiceResponse
from sqlalchemy.orm import Session, joinedload
import os
import shutil
from datetime import datetime
from typing import List
from pydantic import BaseModel
from fastapi import Form 

# Pydantic-Modell für die direkte Eingabe (ohne "contract"-Wrapper)
class DirectContractCreate(BaseModel):
    partner: str
    contract_number: str = None
    start_date: str
    end_date: str
    notice_period: str
    amount: float
    category: str
    notes: str = None
Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Healthcheck-Endpoint für Docker
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

DOCUMENT_DIR = "/app/data/documents"  # ✅ Korrekt im Container

os.makedirs(DOCUMENT_DIR, exist_ok=True)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/contracts/", response_model=ContractResponse)
async def create_contract(
    # Daten direkt entgegenehmen (kein "contract"-Wrapper)
    contract_number: str = Form(None),
    partner: str = Form(...),
    contract_date: str = Form(None),
    start_date: str = Form(...),
    end_date: str = Form(...),
    notice_period: str = Form(...),
    amount: float = Form(...),
    category: str = Form(...),
    notes: str = Form(""),
    file: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    # Parse date strings to date objects
    try:
        parsed_contract_date = datetime.strptime(contract_date, "%Y-%m-%d").date() if contract_date else None
        parsed_start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        parsed_end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    # Manuell ein ContractCreate-Objekt erstellen
    contract_data = ContractCreate(
        contract_number=contract_number,
        partner=partner,
        contract_date=parsed_contract_date,
        start_date=parsed_start_date,
        end_date=parsed_end_date,
        notice_period=notice_period,
        amount=amount,
        category=category,
        notes=notes
    )

    # Rest der Logik bleibt gleich
    document_path = None
    if file:
        os.makedirs(DOCUMENT_DIR, exist_ok=True)
        file_ext = file.filename.split(".")[-1]
        filename = f"contract_{datetime.now().strftime('%Y%m%d%H%M%S')}.{file_ext}"
        document_path = os.path.join(DOCUMENT_DIR, filename)
        with open(document_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

    db_contract = Contract(
        contract_number=contract_data.contract_number,
        partner=contract_data.partner,
        contract_date=contract_data.contract_date,
        start_date=contract_data.start_date,
        end_date=contract_data.end_date,
        notice_period=contract_data.notice_period,
        amount=contract_data.amount,
        category=contract_data.category,
        document_path=document_path,
        notes=contract_data.notes
    )
    db.add(db_contract)
    db.commit()
    db.refresh(db_contract)
    return db_contract

@app.get("/contracts/", response_model=List[ContractResponse])
async def get_contracts(db: Session = Depends(get_db)):
    return db.query(Contract).all()

@app.get("/contracts/{contract_id}", response_model=ContractResponse)
async def get_contract(contract_id: int, db: Session = Depends(get_db)):
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    return contract

@app.put("/contracts/{contract_id}", response_model=ContractResponse)
async def update_contract(
    contract_id: int,
    contract_number: str = Form(None),
    partner: str = Form(...),
    contract_date: str = Form(None),
    start_date: str = Form(...),
    end_date: str = Form(...),
    notice_period: str = Form(...),
    amount: float = Form(...),
    category: str = Form(...),
    notes: str = Form(""),
    file: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    # Parse date strings to date objects
    try:
        parsed_contract_date = datetime.strptime(contract_date, "%Y-%m-%d").date() if contract_date else None
        parsed_start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        parsed_end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")

    contract.contract_number = contract_number
    contract.partner = partner
    contract.contract_date = parsed_contract_date
    contract.start_date = parsed_start_date
    contract.end_date = parsed_end_date
    contract.notice_period = notice_period
    contract.amount = amount
    contract.category = category
    contract.notes = notes

    if file:
        # Altes Dokument löschen, falls vorhanden (optional, hier nicht implementiert um Datenverlust zu vermeiden)
        # Neues speichern
        os.makedirs(DOCUMENT_DIR, exist_ok=True)
        file_ext = file.filename.split(".")[-1]
        filename = f"contract_{contract_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{file_ext}"
        document_path = os.path.join(DOCUMENT_DIR, filename)
        with open(document_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        contract.document_path = document_path

    db.commit()
    db.refresh(contract)
    return contract

@app.delete("/contracts/{contract_id}")
async def delete_contract(contract_id: int, db: Session = Depends(get_db)):
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    db.delete(contract)
    db.commit()
    return {"message": "Contract deleted successfully"}

@app.get("/contracts/{contract_id}/document")
async def get_contract_document(contract_id: int, db: Session = Depends(get_db)):
    contract = db.query(Contract).filter(Contract.id == contract_id).first()
    if not contract:
        raise HTTPException(status_code=404, detail="Contract not found")
    if not contract.document_path or not os.path.exists(contract.document_path):
        raise HTTPException(status_code=404, detail="Document not found")
    
    return FileResponse(contract.document_path, filename=os.path.basename(contract.document_path))

@app.post("/budgets/", response_model=BudgetResponse)
async def create_budget(budget: BudgetCreate, db: Session = Depends(get_db)):
    db_budget = Budget(**budget.dict())
    db.add(db_budget)
    db.commit()
    db.refresh(db_budget)
    return db_budget

@app.get("/budgets/", response_model=List[BudgetResponse])
async def get_budgets(db: Session = Depends(get_db)):
    return db.query(Budget).options(joinedload(Budget.expenses)).all()

@app.get("/budgets/{budget_id}", response_model=BudgetResponse)
async def get_budget(budget_id: int, db: Session = Depends(get_db)):
    budget = db.query(Budget).options(joinedload(Budget.expenses)).filter(Budget.id == budget_id).first()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    return budget

@app.put("/budgets/{budget_id}", response_model=BudgetResponse)
async def update_budget(budget_id: int, budget: BudgetCreate, db: Session = Depends(get_db)):
    db_budget = db.query(Budget).filter(Budget.id == budget_id).first()
    if not db_budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    
    db_budget.contract_number = budget.contract_number
    db_budget.initial_amount = budget.initial_amount
    db_budget.start_date = budget.start_date
    db_budget.end_date = budget.end_date
    
    db.commit()
    db.refresh(db_budget)
    return db_budget

@app.delete("/budgets/{budget_id}")
async def delete_budget(budget_id: int, db: Session = Depends(get_db)):
    budget = db.query(Budget).filter(Budget.id == budget_id).first()
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    # Lösche zuerst alle zugehörigen Ausgaben
    db.query(Expense).filter(Expense.budget_id == budget_id).delete()
    db.delete(budget)
    db.commit()
    return {"message": "Budget deleted successfully"}

@app.post("/expenses/", response_model=ExpenseResponse)
async def create_expense(expense: ExpenseCreate, db: Session = Depends(get_db)):
    db_expense = Expense(**expense.dict())
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)
    return db_expense

@app.post("/invoices/", response_model=InvoiceResponse)
async def create_invoice(invoice: InvoiceCreate, db: Session = Depends(get_db)):
    amount_gross = invoice.amount_net * 1.19  # Calculate gross (19% VAT)
    db_invoice = Invoice(
        **invoice.dict(),
        amount_gross=amount_gross
    )
    db.add(db_invoice)
    db.commit()
    db.refresh(db_invoice)
    return db_invoice

@app.get("/invoices/", response_model=List[InvoiceResponse])
async def get_invoices(db: Session = Depends(get_db)):
    return db.query(Invoice).all()

@app.delete("/invoices/{invoice_id}")
async def delete_invoice(invoice_id: int, db: Session = Depends(get_db)):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
    db.delete(invoice)
    db.commit()
    return {"message": "Invoice deleted successfully"}
