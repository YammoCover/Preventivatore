import streamlit as st
import googlemaps
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO
from PIL import Image

# --- CONFIGURAZIONE API ---
# Assicurati di aver impostato MAPS_KEY nei Secrets di Streamlit Cloud
try:
    API_KEY = st.secrets["MAPS_KEY"]
    gmaps = googlemaps.Client(key=API_KEY)
except:
    st.error("Chiave API non trovata. Impostala nei Secrets come MAPS_KEY.")

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
        p.drawImage("logo yammo sito white.png", 50, h - 75, width=150, preserveAspectRatio=True, mask='auto')
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
    
    # Box Dati
    p.rect(50, h - 170, 490, 100)
    p.setFont("Helvetica-Bold", 10)
    p.drawString(60, h - 85, "DATI DEL DESTINATARIO")
    p.setFont("Helvetica", 10)
    p.drawString(60, h - 105, f"Nome/Cognome: {d['nome']} {d['cognome']}")
    p.drawString(60, h - 120, f"Telefono: {d['telefono']}")
    p.drawString(60, h - 135, f"Indirizzo: {d['destinazione']}")
    
    # Stato Pagamento
    p.rect(50, h - 230, 490, 50)
    p.setFont("Helvetica-Bold", 11)
    p.drawString(60, h - 195, f"STATO PAGAMENTO: {d['stato_pagamento'].upper()}")
    p.setFont("Helvetica", 10)
    p.drawString(60, h - 215, f"Acconto versato: {d['acconto']:.2f} €")
    p.setFont("Helvetica-Bold", 11)
    p.drawRightString(530, h - 215, f"SALDO DA PAGARE AL CORRIERE: {d['saldo']:.2f} €")

    # Clausole (Immagine fornita)
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

    p.rect(50, 120, 490, 80)
    p.drawString(60, 185, "NOTE PER IL CORRIERE:")
    
    p.drawString(50, 80, "DATA: ____/____/_______")
    p.drawString(50, 40, "Firma Corriere: _________________")
    p.drawString(340, 40, "Firma Cliente: _________________")

    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer

# --- INTERFACCIA STREAMLIT ---
try:
    st.image("logo yammo sito white.png", width=300)
except:
    st.title("YAMMO.IT")

# Sidebar per dati fissi
with st.sidebar:
    st.header("👤 Operatore")
    op_nome = st.text_input("Nome Operatore")
    sede_scelta = st.selectbox("🏢 Sede Yammo", list(SEDI_YAMMO.keys()))
    partenza_addr = SEDI_YAMMO[sede_scelta]

st.subheader("📝 Dati Cliente e Destinazione")
c_n, c_c = st.columns(2)
with c_n: nome_cl = st.text_input("Nome")
with c_c: cognome_cl = st.text_input("Cognome")
tel_cl = st.text_input("Telefono")
dest_addr = st.text_input("📍 Indirizzo di Consegna (Via, Civico, Città)")

st.divider()

# Calcolo Km e Servizi
if dest_addr:
    try:
        res = gmaps.distance_matrix(partenza_addr, dest_addr, mode='driving', language='it')
        dist_km = res['rows'][0]['elements'][0]['distance']['value'] / 1000
        costo_trasp = 15.0 if dist_km <= 10 else dist_km * 1.50
        
        st.success(f"Distanza calcolata: {dist_km:.2f} km")

        col1, col2 = st.columns(2)
        with col1:
            st.write("**Opzioni Consegna**")
            p_sel = st.radio("Piano:", ["Strada (0€)", "No Ascensore (+25€)", "Si Ascensore (+15€)"])
            c_piano = 25 if "No" in p_sel else 15 if "Si" in p_sel else 0
            
            st.write("**Installazione**")
            inst_cat = st.selectbox("Tipo:", ["Nessuna", "Libera (30€)", "Incasso Frigo (70€)", "Incasso Lavastoviglie (60€)", "Incasso Forno (50€)", "TV base (15€)", "TV + Staffa (40€)", "Piano Metano/Induzione (60€)", "Piano GPL (70€)"])
            # Dizionario prezzi rapido
            prezzi_mappa = {"Nessuna":0, "Libera (30€)":30, "Incasso Frigo (70€)":70, "Incasso Lavastoviglie (60€)":60, "Incasso Forno (50€)":50, "TV base (15€)":15, "TV + Staffa (40€)":40, "Piano Metano/Induzione (60€)":60, "Piano GPL (70€)":70}
            c_inst = prezzi_mappa.get(inst_cat, 0)

        with col2:
            st.write("**Smaltimento**")
            s_sel = st.radio("Ritiro RAEE:", ["No (0€)", "Al piano (+15€)"])
            c_smalt = 15 if "piano" in s_sel.lower() else 0
            
            st.write("**Pagamento**")
            pag_stato = st.selectbox("Stato:", ["Da Pagare", "Acconto Versato", "Saldato in Negozio"])
            totale_servizi = costo_trasp + c_piano + c_smalt + c_inst
            acconto = st.number_input("Acconto versato (€):", min_value=0.0, value=0.0, step=5.0)
            saldo = totale_servizi - acconto

        st.divider()
        st.metric("SALDO DA PAGARE AL CORRIERE", f"{saldo:.2f} €", delta=f"Totale servizi: {totale_servizi:.2f}€", delta_color="inverse")

        # Preparazione dati per PDF
        dati_pdf = {
            "operatore": op_nome, "sede_nome": sede_scelta, "nome": nome_cl, "cognome": cognome_cl,
            "telefono": tel_cl, "destinazione": dest_addr, "km": dist_km, "c_trasporto": costo_trasp,
            "c_piano": costo_piano, "c_smalt": c_smalt, "c_inst": c_inst, "label_inst": inst_cat,
            "totale": totale_servizi, "acconto": acconto, "saldo": saldo, "stato_pagamento": pag_stato
        }

        if st.download_button(label="🖨️ SCARICA MODULO E RICEVUTA", data=genera_ricevuta_completa(dati_pdf), file_name=f"Yammo_{cognome_cl}.pdf", mime="application/pdf", use_container_width=True):
            st.balloons()
            
    except Exception as e:
        st.error(f"Errore nel calcolo. Verifica l'indirizzo. Dettaglio: {e}")
else:
    st.info("💡 Inserisci l'indirizzo per attivare il calcolo del preventivo e dei servizi.")
