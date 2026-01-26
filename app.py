import streamlit as st
import googlemaps
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO
from PIL import Image
import os

# --- CONFIGURAZIONE API ---
API_KEY = st.secrets["MAPS_KEY"]
gmaps = googlemaps.Client(key=API_KEY)

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Yammo - Preventivatore", page_icon="🚚", layout="centered")

# --- DATABASE SEDI YAMMO ---
SEDI_YAMMO = {
    "Yammo Cassino": "Viale Dante 116, Cassino",
    "Yammo Isernia": "Corso Garibaldi 307, Isernia",
    "Yammo Frosinone": "Via Aldo Moro 207, Frosinone",
    "Yammo Sinergy": "Via Casilina 8, Marzano Appio",
    "Yammo Vairano": "Via Abruzzi 13, Vairano Scalo"
}

# --- FUNZIONE GENERAZIONE PDF ---
def genera_pdf(sede_nome, partenza, destinazione, km, trasporto, piano, smalt, inst, totale, dettaglio_inst, operatore):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    w, h = A4

    # Logo nel PDF (se presente nella cartella)
    try:
        p.drawImage("logo_yammo.png", 50, h - 80, width=120, preserveAspectRatio=True, mask='auto')
    except:
        p.setFont("Helvetica-Bold", 20)
        p.drawString(50, h - 50, "YAMMO.IT")

    p.setFont("Helvetica", 10)
    p.drawRightString(540, h - 40, f"Operatore: {operatore}")
    p.drawRightString(540, h - 55, f"Sede: {sede_nome}")
    p.line(50, h - 90, 540, h - 90)

    # Dettagli Percorso
    p.setFont("Helvetica-Bold", 11)
    p.drawString(50, h - 120, "RIEPILOGO LOGISTICA")
    p.setFont("Helvetica", 10)
    p.drawString(50, h - 140, f"Punto Vendita: {partenza}")
    p.drawString(50, h - 155, f"Destinazione Cliente: {destinazione}")
    p.drawString(50, h - 170, f"Distanza Calcolata: {km:.2f} km")

    # Tabella Servizi
    p.line(50, h - 190, 540, h - 190)
    p.setFont("Helvetica-Bold", 11)
    p.drawString(50, h - 210, "DESCRIZIONE SERVIZI")
    
    y = h - 240
    voci = [
        ("Trasporto (Tariffa Yammo 2026)", f"{trasporto:.2f} €"),
        ("Consegna al Piano", f"{piano:.2f} €"),
        ("Smaltimento Usato (RAEE)", f"{smalt:.2f} €"),
        (f"Installazione: {dettaglio_inst}", f"{inst:.2f} €")
    ]

    p.setFont("Helvetica", 11)
    for voce, prezzo in voci:
        p.drawString(60, y, voce)
        p.drawRightString(500, y, prezzo)
        y -= 25

    # Totale
    p.line(50, y, 540, y)
    p.setFont("Helvetica-Bold", 14)
    p.drawString(60, y - 40, "TOTALE PREVENTIVO")
    p.drawRightString(500, y - 40, f"{totale:.2f} €")

    p.setFont("Helvetica-Oblique", 8)
    p.drawString(50, 50, "Preventivo generato tramite portale Yammo.it - Valido per 48 ore.")

    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer

# --- INTERFACCIA WEB ---
# Mostra Logo in alto
try:
    logo = Image.open("logo_yammo.png")
    st.image(logo, width=300)
except:
    st.title("YAMMO.IT")

st.write("### Accendi la tecnologia - Gestore Consegne")

# 1. CAMPO OPERATORE E SEDE
col_op, col_sede = st.columns(2)
with col_op:
    operatore_nome = st.text_input("👤 Nome Operatore:", placeholder="Es. Mario Rossi")
with col_sede:
    nome_sede_scelta = st.selectbox("🏢 Sede Yammo:", list(SEDI_YAMMO.keys()))
    indirizzo_partenza = SEDI_YAMMO[nome_sede_scelta]

# 2. DESTINAZIONE
st.divider()
dest_input = st.text_input("📍 Inserisci l'indirizzo del cliente:", placeholder="Via, Civico, Città")

if dest_input:
    try:
        res = gmaps.distance_matrix(indirizzo_partenza, dest_input, mode='driving', language='it')
        dist_metri = res['rows'][0]['elements'][0]['distance']['value']
        dist_km = dist_metri / 1000
        addr_formattato = res['destination_addresses'][0]
        
        st.success(f"Destinazione: **{addr_formattato}**")

        costo_trasporto = 15.0 if dist_km <= 10 else dist_km * 1.50

        # 3. OPZIONI
        st.divider()
        c1, c2 = st.columns(2)
        with c1:
            scelta_p = st.radio("🏠 Consegna:", ["Piano strada (0€)", "Senza ascensore (+25€)", "Con ascensore (+15€)"])
            costo_piano = 25 if "Senza" in scelta_p else 15 if "Con" in scelta_p else 0
        with c2:
            scelta_s = st.radio("♻️ Smaltimento:", ["Nessuno / Strada (0€)", "Ritiro al piano (+15€)"])
            costo_smalt = 15 if "piano" in scelta_s else 0

        # 4. INSTALLAZIONI
        st.divider()
        cat_inst = st.selectbox("🛠️ Installazione:", ["Nessuna", "Libera Installazione", "Televisori", "Incasso", "Piani Cottura"])
        
        costo_inst = 0.0
        label_inst = "Nessuna"

        if cat_inst == "Libera Installazione":
            serv = st.selectbox("Prodotto:", ["Frigo", "Lavatrice", "Asciugatrice", "Lavastoviglie", "Cucina"])
            costo_inst, label_inst = 30.0, f"{serv} Libera"
        elif cat_inst == "Televisori":
            serv = st.selectbox("Servizio TV:", ["Installazione base (15€)", "Installazione + Staffa (40€)"])
            costo_inst, label_inst = (15.0 if "base" in serv else 40.0), serv
        elif cat_inst == "Incasso":
            serv = st.selectbox("Apparecchio:", ["Frigorifero (70€)", "Lavastoviglie (60€)", "Forno (50€)"])
            prezzi = {"Frigorifero (70€)": 70, "Lavastoviglie (60€)": 60, "Forno (50€)": 50}
            costo_inst, label_inst = prezzi[serv], f"Incasso {serv}"
        elif cat_inst == "Piani Cottura":
            serv = st.selectbox("Tipo:", ["Metano (60€)", "GPL + Kit Ugelli (70€)", "Induzione (60€)"])
            prezzi = {"Metano (60€)": 60, "GPL + Kit Ugelli (70€)": 70, "Induzione (60€)": 60}
            costo_inst, label_inst = prezzi[serv], f"Piano {serv}"

        # 5. TOTALE E PDF
        st.divider()
        totale = costo_trasporto + costo_piano + costo_smalt + costo_inst
        
        col_res1, col_res2 = st.columns([2,1])
        with col_res1:
            st.metric("TOTALE DA PAGARE", f"{totale:.2f} €", delta=f"{dist_km:.1f} km percorsi")
        
        with col_res2:
            pdf_file = genera_pdf(nome_sede_scelta, indirizzo_partenza, addr_formattato, dist_km, costo_trasporto, costo_piano, costo_smalt, costo_inst, totale, label_inst, operatore_nome)
            st.download_button(
                label="📥 Scarica Preventivo",
                data=pdf_file,
                file_name=f"Preventivo_Yammo_{operatore_nome}.pdf",
                mime="application/pdf"
            )

    except:
        st.warning("In attesa di un indirizzo di destinazione valido...")

