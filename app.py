import streamlit as st
import googlemaps

# --- CONFIGURAZIONE API ---
# Se metti l'app online, ti spiegherò come nascondere questa chiave nei "Secrets"
API_KEY = "AIzaSyDdtXwItbX0uGK9OjPLIbvuiaMsiIPeHBw"
gmaps = googlemaps.Client(key=API_KEY)

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Preventivatore Servizi", page_icon="🚚", layout="wide")

# --- CSS PERSONALIZZATO PER RENDERLO PIÙ BELLO ---
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

st.title("🚚 Calcolatore Consegne e Installazioni")

# --- 1. CONFIGURAZIONE SEDE DI PARTENZA (Sidebar) ---
with st.sidebar:
    st.header("Configurazione Sede")
    sede_partenza_input = st.text_input("📍 Indirizzo Sede di Partenza:", "Via del Commercio 1, Milano")
    st.info("La partenza viene usata come punto zero per il calcolo dei KM.")

# --- 2. DESTINAZIONE ---
st.subheader("📍 Destinazione Cliente")
dest_input = st.text_input("Inserisci l'indirizzo del cliente (es. Via Roma 10, Torino):")

dist_km = 0.0
costo_trasporto = 0.0

if dest_input:
    try:
        # Calcolo distanza tramite Google Maps
        res = gmaps.distance_matrix(sede_partenza_input, dest_input, mode='driving', language='it')
        
        if res['rows'][0]['elements'][0]['status'] == 'OK':
            dist_metri = res['rows'][0]['elements'][0]['distance']['value']
            dist_km = dist_metri / 1000
            addr_formattato = res['destination_addresses'][0]
            
            st.success(f"Destinazione confermata: **{addr_formattato}**")
            
            # Logica Tariffe KM (Tua richiesta: <10km 15€, poi 1.50€/km)
            if dist_km <= 10:
                costo_trasporto = 15.0
            else:
                costo_trasporto = dist_km * 1.50
                
            st.write(f"📏 Distanza calcolata: **{dist_km:.2f} km**")
        else:
            st.error("Non è stato possibile calcolare il percorso stradale.")
    except Exception as e:
        st.error(f"Errore durante il calcolo: {e}")

st.divider()

# --- 3. SERVIZI AL PIANO E SMALTIMENTO ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("📦 Consegna al Piano")
    scelta_piano = st.radio(
        "Seleziona tipologia:",
        ["Piano strada (0€)", "Al piano SENZA ascensore (+25€)", "Al piano CON ascensore (+15€)"]
    )
    costo_piano = 25 if "SENZA" in scelta_piano else 15 if "CON" in scelta_piano else 0

with col2:
    st.subheader("♻️ Smaltimento Usato")
    scelta_smalt = st.radio(
        "Ritiro vecchio apparecchio:",
        ["Nessuno / Piano strada (0€)", "Ritiro al piano (+15€)"]
    )
    costo_smalt = 15 if "Ritiro al piano" in scelta_smalt else 0

st.divider()

# --- 4. INSTALLAZIONI ---
st.subheader("🛠️ Servizi di Installazione")
cat_inst = st.selectbox("Seleziona categoria:", ["Nessuna", "Libera Installazione", "Televisori", "Incasso", "Piani Cottura"])

costo_inst = 0.0
dettaglio_inst = ""

if cat_inst == "Libera Installazione":
    serv_lib = st.selectbox("Elettrodomestico:", ["Frigo", "Lavatrice", "Asciugatrice", "Lavastoviglie", "Cucina"])
    costo_inst = 30.0
    dettaglio_inst = f"Montaggio {serv_lib} Libera installazione"

elif cat_inst == "Televisori":
    serv_tv = st.selectbox("Servizio TV:", ["Installazione base (15€)", "Installazione + Montaggio Staffa (40€)"])
    costo_inst = 15.0 if "base" in serv_tv else 40.0
    dettaglio_inst = serv_tv

elif cat_inst == "Incasso":
    serv_inc = st.selectbox("Apparecchio da incasso:", ["Frigorifero (70€)", "Lavastoviglie (60€)", "Forno (50€)"])
    prezzi_inc = {"Frigorifero (70€)": 70, "Lavastoviglie (60€)": 60, "Forno (50€)": 50}
    costo_inst = prezzi_inc[serv_inc]
    dettaglio_inst = f"Incasso {serv_inc}"

elif cat_inst == "Piani Cottura":
    serv_piano = st.selectbox("Tipo Piano Cottura:", ["Metano (60€)", "GPL + Kit Ugelli (70€)", "Induzione (60€)"])
    prezzi_pc = {"Metano (60€)": 60, "GPL + Kit Ugelli (70€)": 70, "Induzione (60€)": 60}
    costo_inst = prezzi_pc[serv_piano]
    dettaglio_inst = f"Installazione {serv_piano}"

# --- 5. RIEPILOGO E TOTALE ---
st.divider()
totale = costo_trasporto + costo_piano + costo_smalt + costo_inst

c1, c2, c3, c4 = st.columns(4)
c1.metric("Trasporto", f"{costo_trasporto:.2f} €")
c2.metric("Piano", f"{costo_piano:.2f} €")
c3.metric("Smaltimento", f"{costo_smalt:.2f} €")
c4.metric("Installazione", f"{costo_inst:.2f} €")

st.markdown(f"### 💰 TOTALE PREVENTIVO: **{totale:.2f} €**")

# Pulsante per copiare il preventivo
if st.button("📄 Genera Riepilogo per Cliente"):
    riepilogo = f"""
    *PREVENTIVO CONSEGNA E SERVIZI*
    ---
    Partenza: {sede_partenza_input}
    Destinazione: {dest_input}
    Km: {dist_km:.2f}
    ---
    - Trasporto: {costo_trasporto:.2f}€
    - Consegna: {scelta_piano}
    - Smaltimento: {scelta_smalt}
    - Installazione: {dettaglio_inst if dettaglio_inst else 'No'} ({costo_inst:.2f}€)
    ---
    *TOTALE: {totale:.2f}€*
    """
    st.text_area("Copia questo testo:", riepilogo, height=200)

