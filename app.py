import streamlit as st
import googlemaps
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO

# --- CONFIGURAZIONE API ---
API_KEY = "INSERISCI_QUI_LA_TUA_CHIAVE"
gmaps = googlemaps.Client(key=API_KEY)

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Yammo - Preventivatore Consegne", page_icon="🚚", layout="centered")

# --- DATABASE SEDI YAMMO ---
SEDI_YAMMO = {
    "Yammo Cassino": "Viale Dante 116, Cassino",
    "Yammo Isernia": "Corso Garibaldi 307, Isernia",
    "Yammo Frosinone": "Via Aldo Moro 207, Frosinone",
    "Yammo Sinergy": "Via Casilina 8, Marzano Appio",
    "Yammo Vairano": "Via Abruzzi 13, Vairano Scalo"
}

# --- FUNZIONE GENERAZIONE PDF ---
def genera_pdf(sede_nome, partenza, destinazione, km, trasporto, piano, smalt, inst, totale, dettaglio_inst):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    w, h = A4

    # Intestazione con Nome Sede
    p.setFont("Helvetica-Bold", 20)
    p.drawString(50, h - 50, f"{sede_nome}")
    
    p.setFont("Helvetica", 10)
    p.drawString(50, h - 70, "PREVENTIVO SERVIZI DI CONSEGNA E INSTALLAZIONE")
    p.line(50, h - 80, 540, h - 80)

    # Dettagli Percorso
    p.setFont("Helvetica-Bold", 11)
    p.drawString(50, h - 110, "RIEPILOGO LOGISTICA")
    p.setFont("Helvetica", 10)
    p.drawString(50, h - 130, f"Punto Vendita: {partenza}")
    p.drawString(50, h - 145, f"Destinazione Cliente: {destinazione}")
    p.drawString(50, h - 160, f"Distanza Calcolata: {km:.2f} km")

    # Tabella Servizi
    p.line(50, h - 180, 540, h - 180)
    p.setFont("Helvetica-Bold", 11)
    p.drawString(50, h - 200, "DESCRIZIONE SERVIZI")
    
    y = h - 230
    voci = [
        ("Trasporto (Fisso 15€ < 10km, poi 1.50€/km)", f"{trasporto:.2f} €"),
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

    # Nota Legale
    p.setFont("Helvetica-Oblique", 8)
    p.drawString(50, 50, "Documento ad uso interno. I prezzi indicati sono comprensivi di IVA.")

    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer

# --- INTERFACCIA UTENTE ---
st.title("🚚 Yammo - Preventivi Consegne")

# 1. SELEZIONE SEDE
st.subheader("🏢 Seleziona Punto Vendita")
nome_sede_scelta = st.selectbox("Sede di partenza:", list(SEDI_YAMMO.keys()))
indirizzo_partenza = SEDI_YAMMO[nome_sede_scelta]
st.info(f"📍 Sede: {indirizzo_partenza}")

# 2. DESTINAZIONE
st.divider()
st.subheader("👤 Destinazione Cliente")
dest_input = st.text_input("Inserisci l'indirizzo del cliente:")

if dest_input:
    try:
        # Calcolo KM
        res = gmaps.distance_matrix(indirizzo_partenza, dest_input, mode='driving', language='it')
        dist_metri = res['rows'][0]['elements'][0]['distance']['value']
        dist_km = dist_metri / 1000
        addr_formattato = res['destination_addresses'][0]
        
        st.success(f"Destinazione: **{addr_formattato}** ({dist_km:.2f} km)")

        # Logica Tariffe
        costo_trasporto = 15.0 if dist_km <= 10 else dist_km * 1.50

        # 3. OPZIONI CONSEGNA E SMALTIMENTO
        st.divider()
        c1, c2 = st.columns(2)
        with c1:
            scelta_p = st.radio("Consegna:", ["Piano strada (0€)", "Senza ascensore (+25€)", "Con ascensore (+15€)"])
            costo_piano = 25 if "Senza" in scelta_p else 15 if "Con" in scelta_p else 0
        with c2:
            scelta_s = st.radio("Smaltimento:", ["Nessuno / Strada (0€)", "Ritiro al piano (+15€)"])
            costo_smalt = 15 if "piano" in scelta_s else 0

        # 4. INSTALLAZIONI
        st.divider()
        cat_inst = st.selectbox("Installazione:", ["Nessuna", "Libera Installazione", "Televisori", "Incasso", "Piani Cottura"])
        
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
        st.metric("TOTALE FINALE", f"{totale:.2f} €")

        pdf_file = genera_pdf(nome_sede_scelta, indirizzo_partenza, addr_formattato, dist_km, costo_trasporto, costo_piano, costo_smalt, costo_inst, totale, label_inst)
        
        st.download_button(
            label=f"📥 Scarica PDF Preventivo ({nome_sede_scelta})",
            data=pdf_file,
            file_name=f"Yammo_Preventivo_{nome_sede_scelta.replace(' ', '_')}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

    except Exception:
        st.error("Inserisci un indirizzo valido per calcolare il percorso.")
