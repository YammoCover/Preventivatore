import streamlit as st
import googlemaps

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Preventivatore Consegne", page_icon="🚚")
st.title("🚚 Calcolatore Servizi e Consegne")

# --- API GOOGLE ---
API_KEY = "AIzaSyDdtXwItbX0uGK9OjPLIbvuiaMsiIPeHBw"
gmaps = googlemaps.Client(key=API_KEY)

# --- FUNZIONI DI CALCOLO ---
def calcola_trasporto(km):
    return 15.0 if km <= 10 else km * 1.5

# --- INTERFACCIA LATERALE (CONFIGURAZIONE) ---
st.sidebar.header("Punto di Partenza")
partenza = st.sidebar.text_input("Indirizzo Negozio", "Via del commercio 1, Milano")

# --- CORPO PRINCIPALE ---
st.subheader("1. Destinazione e Trasporto")
destinazione = st.text_input("Inserisci indirizzo del cliente:")

if destinazione:
    try:
        # Geocoding e Distanza
        res = gmaps.distance_matrix(partenza, destinazione, mode='driving')
        dist_km = res['rows'][0]['elements'][0]['distance']['value'] / 1000
        addr_formattato = res['rows'][0]['destination_addresses'][0]
        
        st.success(f"📍 Destinazione confermata: {addr_formattato}")
        costo_trasp = calcola_trasporto(dist_km)
        st.info(f"📏 Distanza: {dist_km:.2f} km | **Costo Trasporto: {costo_trasp:.2f}€**")
    except:
        st.error("Indirizzo non trovato o errore API.")
        dist_km, costo_trasp = 0, 0
else:
    dist_km, costo_trasp = 0, 0

st.divider()

# --- SERVIZI AL PIANO E SMALTIMENTO ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("2. Consegna")
    piano = st.radio("Tipo di consegna:", 
                    ["Piano Strada (0€)", "Al piano NO ascensore (+25€)", "Al piano CON ascensore (+15€)"])
    costo_piano = 25 if "NO" in piano else 15 if "CON" in piano else 0

with col2:
    st.subheader("3. Smaltimento")
    smalt = st.radio("Ritiro usato:", 
                    ["Nessuno / Piano Strada (0€)", "Ritiro al piano (+15€)"])
    costo_smalt = 15 if "piano" in smalt.lower() else 0

st.divider()

# --- INSTALLAZIONI ---
st.subheader("4. Installazioni")
servizio = st.selectbox("Seleziona il montaggio:", [
    "Nessuno (0€)",
    "Libera installazione (Frigo, Lavatrice, ecc.) (30€)",
    "TV - Solo installazione (15€)",
    "TV - Installazione + Staffa (40€)",
    "Incasso - Frigorifero (70€)",
    "Incasso - Lavastoviglie (60€)",
    "Incasso - Forno (50€)",
    "Piano Cottura - Metano (60€)",
    "Piano Cottura - GPL + Kit Ugelli (70€)",
    "Piano Cottura - Induzione (60€)"
])

# Mappatura prezzi
prezzi_inst = {
    "Nessuno (0€)": 0, "Libera installazione (Frigo, Lavatrice, ecc.) (30€)": 30,
    "TV - Solo installazione (15€)": 15, "TV - Installazione + Staffa (40€)": 40,
    "Incasso - Frigorifero (70€)": 70, "Incasso - Lavastoviglie (60€)": 60,
    "Incasso - Forno (50€)": 50, "Piano Cottura - Metano (60€)": 60,
    "Piano Cottura - GPL + Kit Ugelli (70€)": 70, "Piano Cottura - Induzione (60€)": 60
}
costo_inst = prezzi_inst[servizio]

# --- TOTALE FINALE ---
st.divider()
totale = costo_trasp + costo_piano + costo_smalt + costo_inst

st.metric(label="TOTALE PREVENTIVO", value=f"{totale:.2f} €")

if st.button("Genera Riepilogo Testuale"):
    st.code(f"""
    RIEPILOGO CONSEGNA:
    Destinazione: {destinazione}
    Km: {dist_km:.2f}
    ---
    Trasporto: {costo_trasp:.2f}€
    Piano: {costo_piano:.2f}€
    Smaltimento: {costo_smalt:.2f}€
    Installazione: {costo_inst:.2f}€
    ---
    TOTALE: {totale:.2f}€
    """)