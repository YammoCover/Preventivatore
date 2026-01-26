import streamlit as st
import googlemaps
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO

# --- CONFIGURAZIONE API ---
API_KEY = "AIzaSyDdtXwItbX0uGK9OjPLIbvuiaMsiIPeHBw"
gmaps = googlemaps.Client(key=API_KEY)

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Preventivatore Pro 2026", page_icon="🚚", layout="centered")

# --- FUNZIONE GENERAZIONE PDF ---
def genera_pdf(partenza, destinazione, km, trasporto, piano, smalt, inst, totale, dettaglio_inst):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    w, h = A4

    # Intestazione
    p.setFont("Helvetica-Bold", 18)
    p.drawString(50, h - 50, "PREVENTIVO CONSEGNA E SERVIZI")
    
    p.setFont("Helvetica", 10)
    p.drawString(50, h - 70, "Documento generato dal sistema gestionale negozi")
    p.line(50, h - 80, 540, h - 80)

    # Sezione Indirizzi
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, h - 110, "DETTAGLI TRASPORTO")
    p.setFont("Helvetica", 11)
    p.drawString(50, h - 130, f"Punto di Partenza: {partenza}")
    p.drawString(50, h - 145, f"Destinazione: {destinazione}")
    p.drawString(50, h - 160, f"Distanza Totale: {km:.2f} km")

    # Tabella Costi
    p.line(50, h - 180, 540, h - 180)
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, h - 200, "DETTAGLIO SERVIZI")
    
    y = h - 230
    voci = [
        ("Costo Trasporto (Fisso 15€ < 10km, poi 1.50€/km)", f"{trasporto:.2f} €"),
        ("Consegna al Piano", f"{piano:.2f} €"),
        ("Smaltimento RAEE (Ritiro usato)", f"{smalt:.2f} €"),
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
    p.drawString(60, y - 40, "TOTALE FINALE (IVA Inclusa)")
    p.drawRightString(500, y - 40, f"{totale:.2f} €")

    # Footer
    p.setFont("Helvetica-Oblique", 9)
    p.drawString(50, 50, "Questo preventivo non costituisce fattura. I prezzi possono variare in base a difficoltà impreviste.")

    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer

# --- INTERFACCIA UTENTE ---
st.title("🚚 Preventivatore Consegne & Montaggi")

# 1. SEDE DI PARTENZA
with st.expander("⚙️ Configurazione Sede di Partenza", expanded=True):
    sede_partenza = st.text_input("Indirizzo del Negozio:", "Via del Commercio 1, Milano")

# 2. DESTINAZIONE
st.subheader("📍 Destinazione Cliente")
dest_input = st.text_input("Inserisci indirizzo del cliente:")

if dest_input:
    try:
        # Calcolo KM con Google
        res = gmaps.distance_matrix(sede_partenza, dest_input, mode='driving', language='it')
        dist_metri = res['rows'][0]['elements'][0]['distance']['value']
        dist_km = dist_metri / 1000
        addr_formattato = res['destination_addresses'][0]
        
        st.info(f"📍 Destinazione rilevata: **{addr_formattato}** ({dist_km:.2f} km)")

        # Logica Prezzo Trasporto (Tua richiesta: 15€ fisso fino a 10km, poi 1.50€/km)
        costo_trasporto = 15.0 if dist_km <= 10 else dist_km * 1.50

        # 3. OPZIONI CONSEGNA E SMALTIMENTO
        st.divider()
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Servizio al Piano**")
            scelta_p = st.selectbox("Piano di consegna:", ["Piano strada (0€)", "Senza ascensore (+25€)", "Con ascensore (+15€)"])
            costo_piano = 25 if "Senza" in scelta_p else 15 if "Con" in scelta_p else 0
        
        with col2:
            st.write("**Smaltimento RAEE**")
            scelta_s = st.selectbox("Ritiro usato:", ["Nessuno / Piano strada (0€)", "Ritiro al piano (+15€)"])
            costo_smalt = 15 if "al piano" in scelta_s else 0

        # 4. INSTALLAZIONI
        st.divider()
        st.write("**Servizi di Installazione**")
        cat_inst = st.selectbox("Seleziona categoria:", ["Nessuna", "Libera Installazione", "Televisori", "Incasso", "Piani Cottura"])

        costo_inst = 0.0
        label_inst = "Nessuna"

        if cat_inst == "Libera Installazione":
            serv = st.selectbox("Apparecchio:", ["Frigo", "Lavatrice", "Asciugatrice", "Lavastoviglie", "Cucina"])
            costo_inst, label_inst = 30.0, f"{serv} (Libera)"
        elif cat_inst == "Televisori":
            serv = st.selectbox("Servizio:", ["Solo Installazione (15€)", "Installazione + Staffa (40€)"])
            costo_inst, label_inst = (15.0 if "base" in serv else 40.0), f"TV ({serv})"
        elif cat_inst == "Incasso":
            serv = st.selectbox("Apparecchio:", ["Frigorifero (70€)", "Lavastoviglie (60€)", "Forno (50€)"])
            prezzi = {"Frigorifero (70€)": 70, "Lavastoviglie (60€)": 60, "Forno (50€)": 50}
            costo_inst, label_inst = prezzi[serv], f"Incasso {serv}"
        elif cat_inst == "Piani Cottura":
            serv = st.selectbox("Tipo:", ["Metano (60€)", "GPL + Kit Ugelli (70€)", "Induzione (60€)"])
            prezzi = {"Metano (60€)": 60, "GPL + Kit Ugelli (70€)": 70, "Induzione (60€)": 60}
            costo_inst, label_inst = prezzi[serv], f"Piano {serv}"

        # 5. RIEPILOGO FINALE
        st.divider()
        totale = costo_trasporto + costo_piano + costo_smalt + costo_inst
        
        st.metric(label="TOTALE PREVENTIVO", value=f"{totale:.2f} €")

        # GENERAZIONE PDF
        pdf_file = genera_pdf(sede_partenza, addr_formattato, dist_km, costo_trasporto, costo_piano, costo_smalt, costo_inst, totale, label_inst)
        
        st.download_button(
            label="📄 Scarica Preventivo Stampabile (PDF)",
            data=pdf_file,
            file_name=f"preventivo_{addr_formattato[:15]}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

    except Exception as e:
        st.error(f"⚠️ Errore: {e}. Controlla gli indirizzi o la chiave API.")
