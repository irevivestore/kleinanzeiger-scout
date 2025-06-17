import streamlit as st
import scraper
import db

st.set_page_config(page_title="Kleinanzeigen Scout", layout="wide")

# Sidebar
st.sidebar.title("Navigation")
seite = st.sidebar.radio("Seite wählen", ["Aktive Anzeigen", "Archivierte Anzeigen", "Suche starten"])

# Globale Einstellungen
if "config" not in st.session_state:
    st.session_state.config = {
        "verkaufspreis": 600,
        "wunsch_marge": 100,
        "reparaturkosten": {
            "display": 50,
            "akku": 30,
            "kamera": 40
        }
    }

# Suche starten
if seite == "Suche starten":
    st.header("Neue Suche starten")

    modell = st.text_input("iPhone Modell", "iPhone 14 Pro")
    min_price = st.number_input("Minimaler Preis", 0, 5000, 100)
    max_price = st.number_input("Maximaler Preis", 0, 5000, 350)
    nur_versand = st.checkbox("Nur Angebote mit Versand", value=True)

    if st.button("Jetzt suchen"):
        with st.spinner("Suche läuft..."):
            resultate = scraper.scrapeAds(
                modell=modell,
                min_price=min_price,
                max_price=max_price,
                nur_versand=nur_versand,
                nur_angebote=True,
                debug=False,
                config=st.session_state.config
            )
        st.success(f"{len(resultate)} neue Anzeigen gefunden.")

# Aktive Anzeigen
if seite == "Aktive Anzeigen":
    st.header("Aktive Anzeigen")
    daten = db.getAllActiveAdverts()

    if not daten:
        st.info("Keine aktiven Anzeigen gefunden.")
    else:
        for eintrag in daten:
            with st.expander(f"{eintrag['title']} ({eintrag.get('priceDisplay', eintrag['price'])} €)", expanded=False):
                col1, col2 = st.columns([1, 3])

                with col1:
                    if eintrag["image"]:
                        st.image(eintrag["image"], width=150)
                    st.write(f"**Preis:** {eintrag.get('priceDisplay', eintrag['price'])} €")
                    st.write(f"**Bewertung:** :{eintrag.get('bewertung', 'neutral')}:")
                    st.write(f"**Reparaturkosten:** {eintrag.get('reparaturkosten', 0)} €")
                    st.write(f"[Zur Anzeige]({eintrag['link']})", unsafe_allow_html=True)

                    if st.button("Archivieren", key=f"archiv_{eintrag['id']}"):
                        db.archiveAdvert(eintrag["id"], archived=True)
                        st.experimental_rerun()

                with col2:
                    st.write(eintrag.get("beschreibung", "Keine Beschreibung vorhanden."))

# Archivierte Anzeigen
if seite == "Archivierte Anzeigen":
    st.header("Archivierte Anzeigen")
    daten = db.getArchivedAdvertsForModel(modell="iPhone 14 Pro")  # Du kannst das Modell hier dynamisch setzen

    if not daten:
        st.info("Keine archivierten Anzeigen vorhanden.")
    else:
        for eintrag in daten:
            with st.expander(f"{eintrag['title']} ({eintrag.get('priceDisplay', eintrag['price'])} €)", expanded=False):
                col1, col2 = st.columns([1, 3])

                with col1:
                    if eintrag["image"]:
                        st.image(eintrag["image"], width=150)
                    st.write(f"**Preis:** {eintrag.get('priceDisplay', eintrag['price'])} €")
                    st.write(f"**Bewertung:** :{eintrag.get('bewertung', 'neutral')}:")
                    st.write(f"**Reparaturkosten:** {eintrag.get('reparaturkosten', 0)} €")
                    st.write(f"[Zur Anzeige]({eintrag['link']})", unsafe_allow_html=True)

                with col2:
                    st.write(eintrag.get("beschreibung", "Keine Beschreibung vorhanden."))
