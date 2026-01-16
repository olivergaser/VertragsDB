import streamlit as st
import requests
from datetime import datetime
import os
import time
from requests.exceptions import ConnectionError
from loguru import logger
import plotly.graph_objects as go

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
                logger.info("Backend ist bereit!")
                return True
        except ConnectionError:
            logger.info("Warte auf Backend...")
            time.sleep(retry_interval)
    return False

if not wait_for_backend():
    st.error("Backend nicht erreichbar! Bitte starte die Container neu.")
    st.stop()

if "editing_contract" not in st.session_state:
    st.session_state.editing_contract = None
if "editing_budget" not in st.session_state:
    st.session_state.editing_budget = None

def render_create_contract():
    st.header("➕ Neuen Vertrag erfassen")
    with st.form("new_contract"):
        contract_number = st.text_input("Vertragsnummer", placeholder="z. B. 'V-2026-001'")
        partner = st.text_input("Vertragspartner", placeholder="z. B. 'Max Mustermann GmbH'")
        col1, col2, col3 = st.columns(3)
        with col1:
            contract_date = st.date_input("Vertragsdatum", value=None, format="DD.MM.YYYY")
        with col2:
            start_date = st.date_input("Startdatum", datetime.now().date(), format="DD.MM.YYYY")
        with col3:
            end_date = st.date_input("Enddatum", datetime.now().date(), format="DD.MM.YYYY")
        notice_period = st.text_input("Kündigungsfrist", placeholder="z. B. '3 Monate'")
        amount = st.number_input("Betrag (€)", min_value=0.0, value=0.0)
        category = st.selectbox(
            "Kategorie",
            ["Abonnement", "Dienstleistung", "Kaufvertrag", "Wartungsvertrag", "Sonstiges"]
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
                    "contract_number": contract_number,
                    "partner": partner,
                    "contract_date": contract_date.strftime("%Y-%m-%d") if contract_date else None,
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
    
    try:
        contract_date_val = datetime.strptime(contract['contract_date'], "%Y-%m-%d").date() if contract.get('contract_date') else None
    except:
        contract_date_val = None

    if contract.get("document_path"):
        st.markdown("### 📄 Aktuelles Dokument")
        # Extrahiere Dateinamen aus dem Pfad
        file_name = os.path.basename(contract['document_path'])
        
        # Button zum Herunterladen (ruft Backend-Endpoint auf)
        try:
            doc_response = requests.get(f"{BACKEND_URL}/contracts/{contract['id']}/document")
            if doc_response.status_code == 200:
                st.download_button(
                    label=f"📥 Download {file_name}",
                    data=doc_response.content,
                    file_name=file_name,
                    mime="application/pdf" if file_name.lower().endswith(".pdf") else "application/octet-stream"
                )
            else:
                st.warning("⚠️ Dokument nicht gefunden (Dateisystem).")
        except Exception as e:
            st.error(f"Fehler beim Laden des Dokuments: {e}")

    with st.form("edit_contract"):
        contract_number = st.text_input("Vertragsnummer", value=contract.get("contract_number", "") or "")
        partner = st.text_input("Vertragspartner", value=contract['partner'])
        col1, col2, col3 = st.columns(3)
        with col1:
            contract_date = st.date_input("Vertragsdatum", value=contract_date_val, format="DD.MM.YYYY")
        with col2:
            start_date = st.date_input("Startdatum", value=start_date_val, format="DD.MM.YYYY")
        with col3:
            end_date = st.date_input("Enddatum", value=end_date_val, format="DD.MM.YYYY")
        notice_period = st.text_input("Kündigungsfrist", value=contract['notice_period'])
        amount = st.number_input("Betrag (€)", min_value=0.0, value=float(contract['amount']))
        
        # Kategorie Index finden
        categories = ["Abonnement", "Dienstleistung", "Kaufvertrag", "Wartungsvertrag", "Sonstiges"]

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
                "contract_number": contract_number,
                "partner": partner,
                "contract_date": contract_date.strftime("%Y-%m-%d") if contract_date else None,
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
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Zurück zur Übersicht"):
            st.session_state.editing_contract = None
            st.rerun()
    with col2:
        if st.button("🗑️ Vertrag löschen", type="primary"):
            response = requests.delete(f"{BACKEND_URL}/contracts/{contract['id']}")
            if response.status_code == 200:
                st.success("✅ Vertrag gelöscht!")
                st.session_state.editing_contract = None
                st.rerun()
            else:
                st.error(f"❌ Fehler: {response.text}")

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
                col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
                with col1:
                    st.write(f"**{contract['partner']}** ({contract['category']})")
                with col2:
                     # Datum formatieren
                    start = datetime.strptime(contract['start_date'], "%Y-%m-%d").strftime("%d.%m.%Y")
                    end = datetime.strptime(contract['end_date'], "%Y-%m-%d").strftime("%d.%m.%Y")
                    c_date = datetime.strptime(contract['contract_date'], "%Y-%m-%d").strftime("%d.%m.%Y") if contract.get('contract_date') else "-"
                    st.write(f"{start} - {end} (V: {c_date})")
                with col3:
                    if st.button("✏️ Bearbeiten", key=f"edit_{contract['id']}"):
                        st.session_state.editing_contract = contract
                        st.rerun()
                with col4:
                    if st.button("🗑️ Löschen", key=f"delete_{contract['id']}", type="secondary"):
                        response = requests.delete(f"{BACKEND_URL}/contracts/{contract['id']}")
                        if response.status_code == 200:
                            st.success("✅ Vertrag gelöscht!")
                            st.rerun()
                        else:
                            st.error(f"❌ Fehler: {response.text}")
                st.markdown("---")
    else:
        st.error("Fehler beim Laden der Verträge.")

def render_create_budget():
    st.header("➕ Neues Budget erstellen")
    with st.form("new_budget"):
        contract_number = st.text_input("Vertragsnummer (optional)", placeholder="z. B. 'V-2026-001'")
        initial_amount = st.number_input("Ausgangswert (€)", min_value=0.0, value=0.0, step=100.0)
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Beginn", datetime.now().date(), format="DD.MM.YYYY")
        with col2:
            end_date = st.date_input("Ende", datetime.now().date(), format="DD.MM.YYYY")
        
        submitted = st.form_submit_button("Budget erstellen")
        if submitted:
            if not initial_amount or not start_date or not end_date:
                st.error("Bitte fülle alle Pflichtfelder aus!")
            else:
                data = {
                    "contract_number": contract_number if contract_number else None,
                    "initial_amount": initial_amount,
                    "start_date": start_date.strftime("%Y-%m-%d"),
                    "end_date": end_date.strftime("%Y-%m-%d"),
                }
                response = requests.post(f"{BACKEND_URL}/budgets/", json=data)
                if response.status_code == 200:
                    st.success("✅ Budget erfolgreich erstellt!")
                    st.rerun()
                else:
                    st.error(f"❌ Fehler: {response.text}")

def render_edit_budget(budget):
    st.header("✏️ Budget bearbeiten")
    
    # Datum parsen
    try:
        start_date_val = datetime.strptime(budget['start_date'], "%Y-%m-%d").date()
        end_date_val = datetime.strptime(budget['end_date'], "%Y-%m-%d").date()
    except:
        start_date_val = datetime.now().date()
        end_date_val = datetime.now().date()
    
    with st.form("edit_budget"):
        contract_number = st.text_input("Vertragsnummer (optional)", value=budget.get('contract_number', '') or '')
        initial_amount = st.number_input("Ausgangswert (€)", min_value=0.0, value=float(budget['initial_amount']), step=100.0)
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Beginn", value=start_date_val, format="DD.MM.YYYY")
        with col2:
            end_date = st.date_input("Ende", value=end_date_val, format="DD.MM.YYYY")
        
        submitted = st.form_submit_button("Änderungen speichern")
        if submitted:
            data = {
                "contract_number": contract_number if contract_number else None,
                "initial_amount": initial_amount,
                "start_date": start_date.strftime("%Y-%m-%d"),
                "end_date": end_date.strftime("%Y-%m-%d"),
            }
            response = requests.put(f"{BACKEND_URL}/budgets/{budget['id']}", json=data)
            if response.status_code == 200:
                st.success("✅ Änderungen gespeichert!")
                # Budget neu laden
                budget_response = requests.get(f"{BACKEND_URL}/budgets/{budget['id']}")
                if budget_response.status_code == 200:
                    st.session_state.editing_budget = budget_response.json()
                    st.rerun()
            else:
                st.error(f"❌ Fehler: {response.text}")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Zurück zu Details"):
            # Budget neu laden
            budget_response = requests.get(f"{BACKEND_URL}/budgets/{budget['id']}")
            if budget_response.status_code == 200:
                st.session_state.editing_budget = budget_response.json()
                st.rerun()
    with col2:
        if st.button("🗑️ Budget löschen", type="primary"):
            response = requests.delete(f"{BACKEND_URL}/budgets/{budget['id']}")
            if response.status_code == 200:
                st.success("✅ Budget gelöscht!")
                st.session_state.editing_budget = None
                st.rerun()
            else:
                st.error(f"❌ Fehler: {response.text}")

def render_budget_detail(budget, edit_mode=False):
    if edit_mode:
        render_edit_budget(budget)
        return
    
    st.header(f"💰 Budget-Details")
    
    # Budget-Informationen
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Ausgangswert", f"{budget['initial_amount']:.2f} €")
    with col2:
        start = datetime.strptime(budget['start_date'], "%Y-%m-%d").strftime("%d.%m.%Y")
        end = datetime.strptime(budget['end_date'], "%Y-%m-%d").strftime("%d.%m.%Y")
        st.write(f"**Zeitraum:** {start} - {end}")
    with col3:
        if budget.get('contract_number'):
            st.write(f"**Vertragsnummer:** {budget['contract_number']}")
    
    st.markdown("---")
    
    # Berechne verbrauchtes und verbleibendes Budget
    expenses = budget.get('expenses', [])
    total_spent = sum(exp['amount'] for exp in expenses)
    remaining = budget['initial_amount'] - total_spent
    
    # Tortengrafik
    st.subheader("📊 Budget-Übersicht")
    
    if total_spent > 0:
        fig = go.Figure(data=[go.Pie(
            labels=['Verbraucht', 'Verfügbar'],
            values=[total_spent, max(0, remaining)],
            hole=.4,
            marker_colors=['#ff6b6b', '#51cf66']
        )])
        fig.update_layout(
            title_text=f"Budget-Status: {remaining:.2f} € verfügbar",
            showlegend=True
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Noch keine Ausgaben erfasst.")
    
    # Metriken
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Verbraucht", f"{total_spent:.2f} €")
    with col2:
        st.metric("Verfügbar", f"{remaining:.2f} €")
    with col3:
        percentage = (total_spent / budget['initial_amount'] * 100) if budget['initial_amount'] > 0 else 0
        st.metric("Verbraucht %", f"{percentage:.1f}%")
    
    st.markdown("---")
    
    # Ausgaben erfassen
    st.subheader("➕ Neue Ausgabe erfassen")
    with st.form("new_expense"):
        col1, col2 = st.columns(2)
        with col1:
            expense_amount = st.number_input("Betrag (€)", min_value=0.0, value=0.0, step=10.0)
        with col2:
            expense_date = st.date_input("Datum", datetime.now().date(), format="DD.MM.YYYY")
        description = st.text_input("Beschreibung", placeholder="z. B. 'Rechnung #123'")
        
        submitted = st.form_submit_button("Ausgabe hinzufügen")
        if submitted:
            if expense_amount <= 0:
                st.error("Betrag muss größer als 0 sein!")
            else:
                data = {
                    "budget_id": budget['id'],
                    "amount": expense_amount,
                    "date": expense_date.strftime("%Y-%m-%d"),
                    "description": description if description else None,
                }
                response = requests.post(f"{BACKEND_URL}/expenses/", json=data)
                if response.status_code == 200:
                    st.success("✅ Ausgabe erfolgreich erfasst!")
                    st.rerun()
                else:
                    st.error(f"❌ Fehler: {response.text}")
    
    # Ausgaben-Liste
    if expenses:
        st.subheader("📋 Erfasste Ausgaben")
        for exp in sorted(expenses, key=lambda x: x['date'], reverse=True):
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                exp_date = datetime.strptime(exp['date'], "%Y-%m-%d").strftime("%d.%m.%Y")
                st.write(f"**{exp_date}**")
            with col2:
                desc = exp.get('description', 'Keine Beschreibung')
                st.write(desc)
            with col3:
                st.write(f"**{exp['amount']:.2f} €**")
            st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Zurück zur Übersicht"):
            st.session_state.editing_budget = None
            st.rerun()
    with col2:
        if st.button("✏️ Budget bearbeiten"):
            st.session_state.editing_budget = budget
            render_budget_detail(budget, edit_mode=True)
            st.rerun()
    with col3:
        if st.button("🗑️ Budget löschen", type="primary"):
            response = requests.delete(f"{BACKEND_URL}/budgets/{budget['id']}")
            if response.status_code == 200:
                st.success("✅ Budget gelöscht!")
                st.session_state.editing_budget = None
                st.rerun()
            else:
                st.error(f"❌ Fehler: {response.text}")

def render_budget_overview():
    st.header("💰 Budget-Übersicht")
    
    if st.session_state.editing_budget:
        render_budget_detail(st.session_state.editing_budget)
        return
    
    response = requests.get(f"{BACKEND_URL}/budgets/")
    if response.status_code == 200:
        budgets = response.json()
        if not budgets:
            st.info("Keine Budgets vorhanden.")
        else:
            for budget in budgets:
                expenses = budget.get('expenses', [])
                total_spent = sum(exp['amount'] for exp in expenses)
                remaining = budget['initial_amount'] - total_spent
                
                col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 1, 1])
                with col1:
                    contract_info = f" ({budget['contract_number']})" if budget.get('contract_number') else ""
                    st.write(f"**Budget{contract_info}**")
                with col2:
                    start = datetime.strptime(budget['start_date'], "%Y-%m-%d").strftime("%d.%m.%Y")
                    end = datetime.strptime(budget['end_date'], "%Y-%m-%d").strftime("%d.%m.%Y")
                    st.write(f"{start} - {end}")
                with col3:
                    st.write(f"Verfügbar: **{remaining:.2f} €** / {budget['initial_amount']:.2f} €")
                with col4:
                    if st.button("📊 Details", key=f"budget_{budget['id']}"):
                        st.session_state.editing_budget = budget
                        st.rerun()
                with col5:
                    if st.button("🗑️ Löschen", key=f"delete_budget_{budget['id']}", type="secondary"):
                        response = requests.delete(f"{BACKEND_URL}/budgets/{budget['id']}")
                        if response.status_code == 200:
                            st.success("✅ Budget gelöscht!")
                            st.rerun()
                        else:
                            st.error(f"❌ Fehler: {response.text}")
                st.markdown("---")
    else:
        st.error("Fehler beim Laden der Budgets.")

def render_create_invoice():
    st.header("➕ Neue Rechnung erfassen")
    with st.form("new_invoice"):
        invoice_number = st.text_input("Rechnungsnummer", placeholder="z. B. 'R-2026-001'")
        invoice_date = st.date_input("Rechnungsdatum", datetime.now().date(), format="DD.MM.YYYY")
        contract_number = st.text_input("Vertragsnummer (optional)", placeholder="z. B. 'V-2026-001'")
        cost_center = st.text_input("Kostenstelle", placeholder="z. B. 'KST-100'")
        amount_net = st.number_input("Summe Netto (€)", min_value=0.0, value=0.0, step=10.0)
        
        # Vorschau Brutto (nur visuell, Berechnung erfolgt im Backend auch nochmal zur Sicherheit)
        st.write(f"Voraussichtliche Summe Brutto (19%): **{amount_net * 1.19:.2f} €**")

        submitted = st.form_submit_button("Rechnung speichern")
        if submitted:
            if not invoice_number or not invoice_date or not cost_center:
                st.error("Bitte fülle alle Pflichtfelder aus!")
            else:
                data = {
                    "invoice_number": invoice_number,
                    "invoice_date": invoice_date.strftime("%Y-%m-%d"),
                    "contract_number": contract_number if contract_number else None,
                    "cost_center": cost_center,
                    "amount_net": amount_net
                }
                response = requests.post(f"{BACKEND_URL}/invoices/", json=data)
                if response.status_code == 200:
                    st.success("✅ Rechnung erfolgreich gespeichert!")
                else:
                    st.error(f"❌ Fehler: {response.text}")

def render_invoice_overview():
    st.header("🧾 Rechnungsübersicht")
    
    response = requests.get(f"{BACKEND_URL}/invoices/")
    if response.status_code == 200:
        invoices = response.json()
        if not invoices:
            st.info("Keine Rechnungen vorhanden.")
        else:
            for invoice in invoices:
                col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 1])
                with col1:
                    st.write(f"**{invoice['invoice_number']}**")
                    if invoice.get('contract_number'):
                        st.caption(f"Ref: {invoice['contract_number']}")
                with col2:
                    st.write(datetime.strptime(invoice['invoice_date'], "%Y-%m-%d").strftime("%d.%m.%Y"))
                with col3:
                   st.write(invoice['cost_center'])
                with col4:
                    st.write(f"{invoice['amount_net']:.2f} € Netto")
                    st.write(f"**{invoice['amount_gross']:.2f} € Brutto**")
                with col5:
                    if st.button("🗑️", key=f"delete_inv_{invoice['id']}", type="secondary", help="Löschen"):
                        response = requests.delete(f"{BACKEND_URL}/invoices/{invoice['id']}")
                        if response.status_code == 200:
                            st.success("Gelöscht!")
                            st.rerun()
                        else:
                            st.error(f"Fehler: {response.text}")
                st.markdown("---")
    else:
        st.error("Fehler beim Laden der Rechnungen.")

# Main Layout
st.title("📄 Vertragsarchiv")

page = st.sidebar.radio("Navigation", ["Verträge - Übersicht", "Verträge - Neu", "Budgets - Übersicht", "Budgets - Neu", "Rechnungen - Übersicht", "Rechnungen - Neu"])

if page == "Verträge - Übersicht":
    if st.session_state.editing_budget:
        st.session_state.editing_budget = None
    render_overview()
elif page == "Verträge - Neu":
    # Wenn man auf "Neuer Vertrag" klickt, Editier-Modus verlassen
    if st.session_state.editing_contract:
        st.session_state.editing_contract = None
    if st.session_state.editing_budget:
        st.session_state.editing_budget = None
    render_create_contract()
elif page == "Budgets - Übersicht":
    if st.session_state.editing_contract:
        st.session_state.editing_contract = None
    render_budget_overview()
elif page == "Budgets - Neu":
    if st.session_state.editing_contract:
        st.session_state.editing_contract = None
    if st.session_state.editing_budget:
        st.session_state.editing_budget = None
    render_create_budget()
elif page == "Rechnungen - Übersicht":
    render_invoice_overview()
elif page == "Rechnungen - Neu":
    render_create_invoice()
