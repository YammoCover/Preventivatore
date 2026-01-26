import streamlit as st
import googlemaps
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from io import BytesIO

# --- CONFIGURAZIONE API ---
API_KEY = "AIzaSyDdtXwItbX0uGK9OjPLIbvuiaMsiIPeHBw"
gmaps = googlemaps.Client(key=API_KEY)

st.set_page_config(page_title="Preventivatore Pro", page_icon="📄", layout="wide")

# --- FUNZIONE GENERAZIONE PDF ---
def genera_pdf(partenza, destinazione, km, trasporto, piano, smalt, inst, totale, dettaglio_inst):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    w, h = A4

    # Intestazione
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, h - 50, "PREVENTIVO SERVIZI DI CONSEGNA")
    
    p.setFont("Helvetica", 10)
    p.line(50, h - 65, 550, h - 65)

    # Dettagli Indirizzi
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, h - 90, "Dettagli Percorso:")
    p.setFont("Helvetica", 10)
    p.drawString(50, h - 110, f"Da (Sede): {partenza}")
    p.drawString(50, h - 125, f"A (Cliente): {destinazione}")
    p.drawString(50, h - 140, f"Distanza Totale: {km:.2f} km")

    # Tabella Costi
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, h - 180, "Riepilogo Costi:")
    
    y = h - 205
    voci = [
        ("Trasporto", f"{trasporto:.2f} €"),
        ("Servizio al Piano", f"{piano:.2f} €"),
        ("Smaltimento RAEE", f"{smalt:.2f} €"),
        (f"Installazione ({dettaglio_inst})", f"{inst:.2f} €")
    ]

    p.setFont("Helvetica", 11)
    for voce, prezzo in voci:
        p.drawString(70, y, voce)
        p.drawRightString(500, y, prezzo)
        y -= 20

    # Totale
    p.line(50, y, 550, y)
    p.setFont("Helvetica-Bold", 14)
    p.drawString(70, y - 30, "TOTALE FINALE")
    p.drawRightString(500, y - 30, f"{totale:.2f} €")

    # Nota a piè di pagina
    p.setFont("Helvetica-Oblique", 8)
    p.drawString(50, 50, "Il presente preventivo ha validità 48 ore.")

    p.showPage()
    p.save()
    buffer.seek(0)
    return buffer

# --- INTERFACCIA STREAMLIT (Sintesi del precedente) ---
with st.sidebar:
    st.header("Sede")
    sede_partenza = st.text_input("Indirizzo Partenza", "Via del Commercio 1, Milano")

st.title("🚚 Preventivatore Professionale")
dest_input = st.text_input("📍 Indirizzo Cliente:")

if dest_input:
    try:
        res = gmaps.distance_matrix(sede_partenza, dest_input, mode='driving', language='it')
        dist_km = res['rows'][0]['elements'][0]['distance']['value'] / 1000
        addr_form = res['destination_addresses'][0]
        costo_trasp = 15.0 if dist_km <= 10 else dist_km * 1.50
        
        st.success(f"Destinazione: {addr_form} ({dist_km:.2f} km)")

        col1, col2, col3 = st.columns(3)
        with col1:
            p_scelta = st.radio("Piano:", ["Strada (0€)", "No Ascensore (+25€)", "Si Ascensore (+15€)"])
            c_piano = 25 if "No" in p_scelta else 15 if "Si" in p_scelta else 0
        with col2:
            s_scelta = st.radio("Smaltimento:", ["No (0€)", "Si (+15€)"])
            c_smalt = 15 if "Si" in s_scelta else 0
        with col3:
            cat_inst = st.selectbox("Installazione:", ["Nessuna", "Libera (30€)", "Incasso Frigo (70€)", "Incasso Lavastoviglie (60€)", "Incasso Forno (50€)"])
            prezzi = {"Nessuna":0, "Libera (30€)":30, "Incasso Frigo (70€)":70, "Incasso Lavastoviglie (60€)":60, "Incasso Forno (50€)":50}
            c_inst = prezzi[cat_inst]

        totale = costo_trasp + c_piano + c_smalt + c_inst
        st.divider()
        st.metric("TOTALE", f"{totale:.2f} €")

        # --- BOTTONE DI STAMPA PDF ---
        pdf_file = genera_pdf(sede_partenza, addr_form, dist_km, costo_trasp, c_piano, c_smalt, c_inst, totale, cat_inst)
        
        st.download_button(
            label="📥 Scarica Preventivo PDF",
            data=pdf_file,
            file_name=f"preventivo_{addr_form.replace(' ', '_')}.pdf",
            mime="application/pdf"
        )

    except:
        st.error("Inserisci un indirizzo valido")
