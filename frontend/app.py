import streamlit as st
import requests
from datetime import datetime
import os
import time
from requests.exceptions import ConnectionError

# Backend-URL aus Umgebungsvariable (wird von Docker gesetzt)
BACKEND_URL = os.getenv("BACKEND_URL", "http://0.0.0.0:8000")

# Warte, bis das Backend erreichbar ist
def wait_for_backend():
    max_retries = 30
    retry_interval = 2  # Sekunden
    for _ in range(max_retries):
        try:
            response = requests.get(f"{BACKEND_URL}/health")
            if response.status_code == 200:
                print("Backend ist bereit!")
                return True
        except ConnectionError:
            print("Warte auf Backend...")
            time.sleep(retry_interval)
    return False

if not wait_for_backend():
    st.error("Backend nicht erreichbar! Bitte starte die Container neu.")
    st.stop()

if "editing_contract" not in st.session_state:
    st.session_state.editing_contract = None

def render_create_contract():
    st.header("➕ Neuen Vertrag erfassen")
    with st.form("new_contract"):
        partner = st.text_input("Vertragspartner", placeholder="z. B. 'Max Mustermann GmbH'")
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Startdatum", datetime.now().date(), format="DD.MM.YYYY")
        with col2:
            end_date = st.date_input("Enddatum", datetime.now().date(), format="DD.MM.YYYY")
        notice_period = st.text_input("Kündigungsfrist", placeholder="z. B. '3 Monate'")
        amount = st.number_input("Betrag (€)", min_value=0.0, value=0.0)
        category = st.selectbox(
            "Kategorie",
            ["Miete", "Versicherung", "Dienstleistung", "Kaufvertrag", "Sonstiges"]
        )
        notes = st.text_area("Notizen", placeholder="Zusätzliche Informationen...")
        document = st.file_uploader(
            "Dokument hochladen (PDF/Word)",
            type=["pdf", "docx"],
            help="Max. 10MB"
        )

        submitted = st.form_submit_button("Vertrag speichern")
        if submitted:
            if not partner or not start_date or not end_date:
                st.error("Bitte fülle alle Pflichtfelder aus!")
            else:
                data = {
                    "partner": partner,
                    "start_date": start_date.strftime("%Y-%m-%d"),
                    "end_date": end_date.strftime("%Y-%m-%d"),
                    "notice_period": notice_period,
                    "amount": str(amount),
                    "category": category,
                    "notes": notes,
                }
                files = {"file": document} if document else None
                response = requests.post(f"{BACKEND_URL}/contracts/", data=data, files=files)
                if response.status_code == 200:
                    st.success("✅ Vertrag erfolgreich gespeichert!")
                else:
                    st.error(f"❌ Fehler: {response.text}")

def render_edit_contract(contract):
    st.header(f"✏️ Vertrag bearbeiten: {contract['partner']}")
    
    # Datum parsen
    try:
        start_date_val = datetime.strptime(contract['start_date'], "%Y-%m-%d").date()
        end_date_val = datetime.strptime(contract['end_date'], "%Y-%m-%d").date()
    except:
        start_date_val = datetime.now().date()
        end_date_val = datetime.now().date()

    with st.form("edit_contract"):
        partner = st.text_input("Vertragspartner", value=contract['partner'])
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Startdatum", value=start_date_val, format="DD.MM.YYYY")
        with col2:
            end_date = st.date_input("Enddatum", value=end_date_val, format="DD.MM.YYYY")
        notice_period = st.text_input("Kündigungsfrist", value=contract['notice_period'])
        amount = st.number_input("Betrag (€)", min_value=0.0, value=float(contract['amount']))
        
        # Kategorie Index finden
        categories = ["Miete", "Versicherung", "Dienstleistung", "Kaufvertrag", "Sonstiges"]
        cat_index = 0
        if contract['category'] in categories:
            cat_index = categories.index(contract['category'])
            
        category = st.selectbox("Kategorie", categories, index=cat_index)
        notes = st.text_area("Notizen", value=contract['notes'] or "")
        document = st.file_uploader(
            "Neues Dokument hochladen (überschreibt altes)",
            type=["pdf", "docx"],
            help="Max. 10MB"
        )

        submitted = st.form_submit_button("Änderungen speichern")
        if submitted:
            data = {
                "partner": partner,
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
                "notice_period": notice_period,
                "amount": str(amount),
                "category": category,
                "notes": notes,
            }
            files = {"file": document} if document else None
            response = requests.put(f"{BACKEND_URL}/contracts/{contract['id']}", data=data, files=files)
            if response.status_code == 200:
                st.success("✅ Änderungen gespeichert!")
                st.session_state.editing_contract = None # Zurück zur Übersicht
                st.rerun()
            else:
                st.error(f"❌ Fehler: {response.text}")
    
    if st.button("Zurück zur Übersicht"):
        st.session_state.editing_contract = None
        st.rerun()

def render_overview():
    st.header("📋 Vertragsübersicht")
    
    if st.session_state.editing_contract:
        render_edit_contract(st.session_state.editing_contract)
        return

    response = requests.get(f"{BACKEND_URL}/contracts/")
    if response.status_code == 200:
        contracts = response.json()
        if not contracts:
            st.info("Keine Verträge vorhanden.")
        else:
            for contract in contracts:
                col1, col2, col3 = st.columns([3, 2, 1])
                with col1:
                    st.write(f"**{contract['partner']}** ({contract['category']})")
                with col2:
                     # Datum formatieren
                    start = datetime.strptime(contract['start_date'], "%Y-%m-%d").strftime("%d.%m.%Y")
                    end = datetime.strptime(contract['end_date'], "%Y-%m-%d").strftime("%d.%m.%Y")
                    st.write(f"{start} - {end}")
                with col3:
                    if st.button("Bearbeiten", key=f"edit_{contract['id']}"):
                        st.session_state.editing_contract = contract
                        st.rerun()
                st.markdown("---")
    else:
        st.error("Fehler beim Laden der Verträge.")

# Main Layout
st.title("📄 Vertragsarchiv")

page = st.sidebar.radio("Navigation", ["Übersicht", "Neuer Vertrag"])

if page == "Übersicht":
    render_overview()
else:
    # Wenn man auf "Neuer Vertrag" klickt, Editier-Modus verlassen
    if st.session_state.editing_contract:
        st.session_state.editing_contract = None
    render_create_contract()
