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
    st.error("Chiave API non configurata correttamente.")

# --- DATABASE SEDI ---
SEDI_YAMMO = {
    "Yammo Cassino": "Viale Dante 116, Cassino",
    "Yammo Isernia": "Corso Garibaldi 307, Isernia",
    "Yammo Frosinone": "Via Aldo Moro 207, Frosinone",
    "Yammo Sinergy": "Via Casilina 8, Marzano Appio",
    "Yammo Vairano": "Via Abruzzi 13, Vairano Scalo"
}

# --- FUNZIONE PDF ---
def genera_ricevuta_completa(d):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    w, h = A4
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
    p.drawString(50, h - 110, "RIEPILOGO ORDINE E SERVIZI")
    p.setFont("Helvetica", 11)
    p.drawString(50, h - 135, f"Cliente: {d['nome']} {d['cognome']}")
    p.drawString(50, h - 150, f"Destinatario: {d['destinazione']}")
    y = h - 180
    voci = [
        (f"Prodotto: {d['prodotto_nome']}", f"{d['prezzo_prodotto']:.2f} €"),
        (f"Trasporto ({d['km']:.2f} km)", f"{d['c_trasporto']:.2f} €"),
        ("Servizio al Piano", f"{d['c_piano']:.2f} €"),
        ("Smaltimento RAEE", f"{d['c_smalt']:.2f} €"),
        (f"Installazione: {d['label_inst']}", f"{d['c_inst']:.2f} €")
    ]
    for voce, prezzo in voci:
        p.drawString(60, y, voce); p.drawRightString(500, y, prezzo); y -= 20
    p.line(50, y, 540, y)
    p.setFont("Helvetica-Bold", 12)
    p.drawString(60, y - 25, "TOTALE COMPLESSIVO")
    p.drawRightString(500, y - 25, f"{d['totale_lordo']:.2f} €")
    p.showPage()
    p.setFont("Helvetica-Bold", 16)
    p.drawCentredString(w/2, h - 50, "MODULO DI CONSEGNA")
    p.rect(50, h - 170, 490, 100)
    p.setFont("Helvetica-Bold", 10); p.drawString(60, h - 85, "DATI DEL DESTINATARIO")
    p.setFont("Helvetica", 10); p.drawString(60, h - 105, f"Nome/Cognome: {d['nome']} {d['cognome']}")
    p.drawString(60, h - 120, f"Telefono: {d['telefono']}")
    p.drawString(60, h - 135, f"Indirizzo: {d['destinazione']}")
    p.setFillColorRGB(0.95, 0.95, 0.95); p.rect(50, h - 235, 490, 55, fill=1); p.setFillColorRGB(0, 0, 0)
    p.setFont("Helvetica-Bold", 12); p.drawString(60, h - 200, "DA INCASSARE ALLA CONSEGNA:")
    p.drawRightString(530, h - 200, f"{d['saldo_finale']:.2f} €")
    p.setFont("Helvetica-Bold", 10); p.drawString(50, h - 265, "CONDIZIONI E CLAUSOLE")
    cl = [("Verifica Merce", "Controllare l'integrità del prodotto al momento della consegna."), ("Riserva", "Firmare con riserva specifica se l'imballo è danneggiato."), ("Accettazione", "La firma costituisce piena accettazione della merce.")]
    curr_y = h - 290
    for tit, txt in cl:
        p.setFont("Helvetica-Bold", 9); p.drawString(50, curr_y, tit)
        p.setFont("Helvetica", 8); p.drawString(160, curr_y, txt); curr_y -= 20
    p.rect(50, 120, 490, 80); p.setFont("Helvetica-Bold", 10); p.drawString(60, 185, "NOTE PER IL CORRIERE:")
    p.setFont("Helvetica", 9); text_note = p.beginText(60, 170); text_note.textLines(d['note']); p.drawText(text_note)
    p.setFont("Helvetica", 10); p.drawString(50, 80, "DATA: ____/____/_______"); p.drawString(50, 40, "Firma Corriere: _________________"); p.drawString(340, 40, "Firma Cliente: _________________")
    p.showPage(); p.save(); buffer.seek(0)
    return buffer

# --- INTERFACCIA ---
with st.sidebar:
    try:
        st.image("logo yammo sito white.png", width=200)
    except:
        st.title("YAMMO")
    op_nome = st.text_input("Nome Operatore", value="Operatore Yammo")
    sede_scelta = st.selectbox("🏢 Sede Yammo", list(SEDI_YAMMO.keys()))
    partenza_addr = SEDI_YAMMO[sede_scelta]

st.header("🚚 Preventivatore Yammo Logistica")

# --- FASE 1: PREVENTIVO KM ---
st.subheader("1. Calcolo Spese di Trasporto")
dest_addr = st.text_input("📍 Inserisci indirizzo cliente:")

# Variabili di stato
dist_km = 0.0
costo_trasp = 0.0

if dest_addr:
    try:
        res = gmaps.distance_matrix(partenza_addr, dest_addr, mode='driving', language='it')
        dist_km = res['rows'][0]['elements'][0]['distance']['value'] / 1000
        costo_trasp = 15.0 if dist_km <= 10 else dist_km * 1.50
        
        # MOSTRA SEMPRE I KM QUI
        st.info(f"📏 Distanza: **{dist_km:.2f} km** | Costo Trasporto: **{costo_trasp:.2f} €**")

        col1, col2 = st.columns(2)
        with col1:
            p_sel = st.radio("🏠 Piano:", ["Strada (0€)", "Al Piano, Senza Ascensore (+25€)", "Al Piano, Con Ascensore (+15€)"])
            c_piano = 25.0 if "No" in p_sel else 15.0 if "Si" in p_sel else 0.0
            
            inst_cat = st.selectbox("🛠️ Installazione:", ["Nessuna", "Libera (30€)", "Incasso Frigo (70€)", "Incasso Lavastoviglie (60€)", "Incasso Forno (50€)", "TV base (15€)", "TV + Staffa (40€)", "Piano Metano/Induzione (60€)", "Piano GPL (70€)"])
            prezzi_mappa = {"Nessuna":0, "Libera (30€)":30, "Incasso Frigo (70€)":70, "Incasso Lavastoviglie (60€)":60, "Incasso Forno (50€)":50, "TV base (15€)":15, "TV + Staffa (40€)":40, "Piano Metano/Induzione (60€)":60, "Piano GPL (70€)":70}
            c_inst = float(prezzi_mappa.get(inst_cat, 0))

        with col2:
            s_sel = st.radio("♻️ Ritiro RAEE:", ["No", ,"Si, su strada", "Al piano (+15€)"])
            c_smalt = 15.0 if "piano" in s_sel.lower() else 0.0
            
            totale_servizi = costo_trasp + c_piano + c_smalt + c_inst
            st.metric("TOTALE SERVIZI", f"{totale_servizi:.2f} €")

        st.divider()
        conferma_vendita = st.checkbox("✅ Procedi con i dati del Prodotto e Modulo Consegna")

        if conferma_vendita:
            st.subheader("2. Dati Prodotto e Cliente")
            c_cl1, c_cl2 = st.columns(2)
            with c_cl1:
                nome_cl = st.text_input("Nome")
                cognome_cl = st.text_input("Cognome")
                tel_cl = st.text_input("Telefono")
            with c_cl2:
                prod_nome = st.text_input("Prodotto")
                prezzo_prod = st.number_input("Prezzo Prodotto (€)", min_value=0.0, step=10.0)
            
            tipo_pag = st.selectbox("Stato Pagamento:", ["Acconto Versato", "Saldato in Negozio"])
            totale_lordo = prezzo_prod + totale_servizi
            
            if tipo_pag == "Saldato in Negozio":
                acconto = totale_lordo
                saldo_finale = 0.0
            else:
                acconto = st.number_input("Acconto (€):", min_value=0.0, max_value=totale_lordo, value=0.0)
                saldo_finale = totale_lordo - acconto

            st.metric("SALDO DA INCASSARE", f"{saldo_finale:.2f} €")
            note_libere = st.text_area("Note Corriere")

            d_pdf = {
                "operatore": op_nome, "sede_nome": sede_scelta, "nome": nome_cl, "cognome": cognome_cl,
                "telefono": tel_cl, "destinazione": dest_addr, "km": dist_km, "c_trasporto": costo_trasp,
                "c_piano": c_piano, "c_smalt": c_smalt, "c_inst": c_inst, "label_inst": inst_cat,
                "prodotto_nome": prod_nome, "prezzo_prodotto": prezzo_prod,
                "totale_lordo": totale_lordo, "acconto": acconto, "saldo_finale": saldo_finale, "note": note_libere
            }

            st.download_button("🖨️ STAMPA MODULO", data=genera_ricevuta_completa(d_pdf), file_name=f"Yammo_{cognome_cl}.pdf", mime="application/pdf", use_container_width=True)
                
    except Exception as e:
        st.error("Errore nel calcolo. Controlla l'indirizzo.")
else:
    st.info("💡 Inserisci l'indirizzo per vedere i km e il costo.")

