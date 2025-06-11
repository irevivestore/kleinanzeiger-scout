import streamlit as st
from db import load_all_ads
from datetime import datetime

st.set_page_config(page_title="Kleinanzeigen Analyzer", layout="wide")

st.title("📱 Kleinanzeigen Analyzer – Anzeigenübersicht")

# Benutzerkonfiguration
verkaufspreis = st.session_state.get("verkaufspreis", 600)
wunsch_marge = st.session_state.get("wunsch_marge", 100)
reparaturkosten_dict = st.session_state.get("reparaturkosten", {
    "Display": 100,
    "Akku": 50,
    "Face ID": 80
})

st.markdown(f"**Verkaufspreis:** {verkaufspreis} € | **Gewünschte Marge:** {wunsch_marge} €")

alle_anzeigen = load_all_ads()

if not alle_anzeigen:
    st.info("Es wurden noch keine Anzeigen gespeichert.")
else:
    for ad in alle_anzeigen:
        with st.expander(f"{ad['title']} – {ad['price']} €"):
            col1, col2 = st.columns([1, 2])
            with col1:
                st.image(ad["image"], width=150)
                st.markdown(f"[🌐 Zur Anzeige]({ad['link']})", unsafe_allow_html=True)
                st.markdown(f"📅 Erstellt: {ad['created_at']}  \n♻️ Aktualisiert: {ad['updated_at']}")

            with col2:
                st.markdown(f"**Beschreibung:**")
                st.text_area("",
                             value=ad.get("beschreibung", ""),
                             height=150,
                             key=f"desc_{ad['id']}",
                             disabled=True)

                defektauswahl = st.multiselect(
                    "🛠️ Manuelle Defekte auswählen:",
                    options=list(reparaturkosten_dict.keys()),
                    default=[],
                    key=f"defekte_{ad['id']}"
                )

                manuelle_rep_kosten = sum(reparaturkosten_dict.get(d, 0) for d in defektauswahl)
                max_ek = verkaufspreis - wunsch_marge - manuelle_rep_kosten

                if ad["price"] <= max_ek:
                    bewertung = "✅ **GRÜN** (geeignet)"
                elif ad["price"] <= max_ek + wunsch_marge * 0.1:
                    bewertung = "🟦 **BLAU** (Grenzfall)"
                else:
                    bewertung = "❌ **ROT** (zu teuer)"

                st.markdown("---")
                st.markdown(f"💰 **Preis:** {ad['price']} €")
                st.markdown(f"🛠️ **Reparaturkosten (manuell):** {manuelle_rep_kosten} €")
                st.markdown(f"📉 **Max. Einkaufspreis:** {max_ek} €")
                st.markdown(f"🎯 **Bewertung:** {bewertung}")
