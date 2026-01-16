#!/bin/bash

# Warnung ausgeben
echo "⚠️  ACHTUNG: Dieses Skript setzt die gesamte Anwendung zurück!"
echo "Alle Daten in der Datenbank und alle hochgeladenen Dokumente werden unwiderruflich gelöscht."
echo "Die Datenbank wird basierend auf dem aktuellen Code (models.py) neu erstellt."

# Sicherheitsabfrage
read -p "Möchten Sie wirklich fortfahren? (j/n) " -n 1 -r
echo    # Neue Zeile
if [[ ! $REPLY =~ ^[Jj]$ ]]
then
    echo "Vorgang abgebrochen."
    exit 1
fi

echo "1. Stoppe Docker-Container..."
docker-compose down

echo "2. Lösche Datenbank-Datei (contracts.db)..."
rm -f data/contracts.db

echo "3. Lösche hochgeladene Dokumente..."
# Löscht den Inhalt von documents/, behält aber den Ordner
rm -rf data/documents/*

echo "4. Starte Anwendung neu (Rebuild)..."
docker-compose up -d --build

echo "✅ Reset erfolgreich! Die Anwendung ist nun leer und auf dem neuesten Stand."
