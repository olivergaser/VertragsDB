from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from .models import Contract, Base
from .database import engine, SessionLocal
from .schemas import ContractCreate, ContractResponse
from sqlalchemy.orm import Session
import os
import shutil
from datetime import datetime
from typing import List
from pydantic import BaseModel
from fastapi import Form 

# Pydantic-Modell für die direkte Eingabe (ohne "contract"-Wrapper)
class DirectContractCreate(BaseModel):
    partner: str
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
    partner: str = Form(...),
    start_date: str = Form(...),
    end_date: str = Form(...),
    notice_period: str = Form(...),
    amount: float = Form(...),
    category: str = Form(...),
    notes: str = Form(""),
    file: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    # Manuell ein ContractCreate-Objekt erstellen
    contract_data = ContractCreate(
        partner=partner,
        start_date=start_date,
        end_date=end_date,
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
        partner=contract_data.partner,
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
    partner: str = Form(...),
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

    contract.partner = partner
    contract.start_date = start_date
    contract.end_date = end_date
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
