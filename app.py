import streamlit as st
import googlemaps
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO
from PIL import Image

# --- CONFIGURAZIONE API ---
try:
    API_KEY = st.secrets["MAPS_KEY"]
    gmaps = googlemaps.Client(key=API_KEY)
except:
    st.error("Chiave API non trovata nei Secrets.")

# --- DATABASE SEDI YAMMO ---
SEDI_YAMMO = {
    "Yammo Cassino": "Viale Dante 116, Cassino",
    "Yammo Isernia": "Corso Garibaldi 307, Isernia",
    "Yammo Frosinone": "Via Aldo Moro 207, Frosinone",
    "Yammo Sinergy": "Via Casilina 8, Marzano Appio",
    "Yammo Vairano": "Via Abruzzi 13, Vairano Scalo"
}

# --- FUNZIONE GENERAZIONE PDF ---
def genera_ricevuta_completa(d):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    w, h = A4

    # PAGINA 1: PREVENTIVO
    try:
        p.drawImage("logo_yammo.png", 50, h - 75, width=150, preserveAspectRatio=True, mask='auto')
    except:
        p.setFont("Helvetica-Bold", 18)
        p.drawString(50, h - 50, "YAMMO.IT")

    p.setFont("Helvetica", 10)
    p.drawRightString(540, h - 40, f"Operatore: {d['operatore']}")
    p.drawRightString(540, h - 55, f"Sede: {d['sede_nome']}")
    p.line(50, h - 85, 540, h - 85)

    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, h - 110, "RIEPILOGO COSTI CONSEGNA E SERVIZI")
    
    p.setFont("Helvetica", 11)
    p.drawString(50, h - 135, f"Destinatario: {d['nome']} {d['cognome']}")
    p.drawString(50, h - 150, f"Indirizzo: {d['destinazione']}")
    
    y = h - 180
    voci = [
        (f"Trasporto ({d['km']:.2f} km)", f"{d['c_trasporto']:.2f} €"),
        ("Servizio al Piano", f"{d['c_piano']:.2f} €"),
        ("Smaltimento RAEE", f"{d['c_smalt']:.2f} €"),
        (f"Installazione: {d['label_inst']}", f"{d['c_inst']:.2f} €")
    ]
    for voce, prezzo in voci:
        p.drawString(60, y, voce)
        p.drawRightString(500, y, prezzo)
        y -= 25

    p.line(50, y, 540, y)
    p.setFont("Helvetica-Bold", 12)
    p.drawString(60, y - 30, "TOTALE SERVIZI")
    p.drawRightString(500, y - 30, f"{d['totale']:.2f} €")
    
    p.showPage()

    # PAGINA 2: MODULO DI CONSEGNA
    p.setFont("Helvetica-Bold", 16)
    p.drawCentredString(w/2, h - 50, "MODULO DI CONSEGNA")
    
    p.rect(50, h - 170, 490, 100)
    p.setFont("Helvetica-Bold", 10)
    p.drawString(60, h - 85, "DATI DEL DESTINATARIO")
    p.setFont("Helvetica", 10)
    p.drawString(60, h - 105, f"Nome/Cognome: {d['nome']} {d['cognome']}")
    p.drawString(60, h - 120, f"Telefono: {d['telefono']}")
    p.drawString(60, h - 135, f"Indirizzo: {d['destinazione']}")
    
    p.rect(50, h - 230, 490, 50)
    p.setFont("Helvetica-Bold", 11)
    p.drawString(60, h - 195, f"STATO PAGAMENTO: {d['stato_pagamento'].upper()}")
    p.setFont("Helvetica", 10)
    p.drawString(60, h - 215, f"Acconto versato: {d['acconto']:.2f} €")
    p.drawRightString(530, h - 215, f"SALDO AL CORRIERE: {d['saldo']:.2f} €")

    p.setFont("Helvetica-Bold", 10)
    p.drawString(50, h - 260, "CONDIZIONI DI TRASPORTO E CLAUSOLE")
    cl = [
        ("Verifica della Merce", "Il destinatario è tenuto a verificare l'integrità della merce al momento della consegna."),
        ("Riserva di Controllo", "Qualora la merce non sia verificabile subito, firmare con riserva specifica."),
        ("Accettazione", "La firma costituisce accettazione della merce senza riserve.")
    ]
    curr_y = h - 285
    for tit, txt in cl:
        p.setFont("Helvetica-Bold", 9)
        p.drawString(50, curr_y, tit)
        p.setFont("Helvetica", 8)
        p.drawString(180, curr_y, txt)
        curr_y -= 25

    # Note per il corriere
    p.rect(50, 120, 490, 80)
    p.setFont("Helvetica-Bold", 10)

