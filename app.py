import streamlit as st
from datetime import datetime
from utils import load_data, save_rating, archive_advert, get_archived_adverts_for_model

# Seiteneinstellungen
st.set_page_config(
    page_title="Kleinanzeigen-Scout",
    layout="wide",
    page_icon="📱"
)

# Design-Farben
BACKGROUND_COLOR = "#F4F4F4"
PRIMARY_COLOR = "#4B6FFF"
SECONDARY_COLOR = "#00D1B2"
CARD_BORDER_RADIUS = "15px"
CARD_SHADOW = "0 4px 12px rgba(0, 0, 0, 0.06)"

# Custom CSS für modernes Design
st.markdown(f"""
    <style>
        html, body, [class*="css"] {{
            background-color: {BACKGROUND_COLOR};
        }}
        .advert-card {{
            background-color: white;
            border-radius: {CARD_BORDER_RADIUS};
            padding: 1rem;
            margin-bottom: 1.5rem;
            box-shadow: {CARD_SHADOW};
        }}
        .advert-title {{
            font-size: 1.3rem;
            font-weight: bold;
            color: {PRIMARY_COLOR};
        }}
        .advert-price {{
            font-size: 1.1rem;
            color: #222;
            margin-bottom: 0.5rem;
        }}
        .button-archive {{
            background-color: {SECONDARY_COLOR};
            color: white;
            border: none;
            border-radius: 8px;
            padding: 6px 14px;
            margin-right: 10px;
            cursor: pointer;
        }}
        .image-thumbnail {{
            width: 100%;
            border-radius: 12px;
            margin-bottom: 0.7rem;
            cursor: pointer;
        }}
    </style>
""", unsafe_allow_html=True)

# Navigation
seite = st.sidebar.radio("Navigation", ["Anzeigen", "Archiv"])

# Modell-Auswahl
modell = st.sidebar.selectbox("📱 Modell auswählen", ["iPhone 14 Pro", "iPhone 13", "iPhone 12", "iPhone X"])

if seite == "Anzeigen":
    daten = load_data(modell)
    if not daten:
        st.info("ℹ️ Es sind noch keine Anzeigen für dieses Modell verfügbar.")
    else:
        for eintrag in daten:
            with st.container():
                st.markdown('<div class="advert-card">', unsafe_allow_html=True)

                col1, col2 = st.columns([1, 2])
                with col1:
                    if eintrag["bilder_liste"]:
                        st.image(eintrag["bilder_liste"][0], use_column_width=True, caption="Bild öffnen für Galerie")
                        if st.button("🔍 Galerie ansehen", key=f"gallery_{eintrag['id']}"):
                            with st.expander("📸 Weitere Bilder"):
                                st.image(eintrag["bilder_liste"], use_column_width=True)
                    else:
                        st.write("Kein Bild verfügbar.")

                with col2:
                    st.markdown(f"<div class='advert-title'>{eintrag['title']}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='advert-price'>{eintrag['price']} €</div>", unsafe_allow_html=True)
                    st.markdown(f"📍 **Ort:** {eintrag.get('ort', 'Unbekannt')}  \n"
                                f"🔗 [Zur Anzeige]({eintrag['link']})", unsafe_allow_html=True)
                    
                    with st.expander("📄 Beschreibung einblenden"):
                        st.markdown(eintrag["description"])

                    # Bewertung setzen
                    defekt = st.selectbox("Defekt:", ["", "Display", "Akku", "Face-ID", "Kein Defekt"], key=f"defekt_{eintrag['id']}")
                    zustand = st.selectbox("Zustand:", ["", "Wie neu", "Gut", "Akzeptabel", "Schlecht"], key=f"zustand_{eintrag['id']}")

                    if st.button("💾 Bewertung speichern", key=f"save_{eintrag['id']}"):
                        save_rating(eintrag["id"], defekt, zustand)
                        st.success("✅ Bewertung gespeichert!")

                    if st.button("🗃️ Archivieren", key=f"archive_{eintrag['id']}"):
                        archive_advert(eintrag["id"])
                        st.success("📦 Anzeige archiviert!")

                st.markdown("</div>", unsafe_allow_html=True)

elif seite == "Archiv":
    st.title("📦 Archivierte Anzeigen")
    archivierte = get_archived_adverts_for_model(modell)
    if not archivierte:
        st.info("ℹ️ Keine archivierten Anzeigen.")
    else:
        for anzeige in archivierte:
            with st.container():
                st.markdown('<div class="advert-card">', unsafe_allow_html=True)

                col1, col2 = st.columns([1, 2])
                with col1:
                    if anzeige["bilder_liste"]:
                        st.image(anzeige["bilder_liste"][0], use_column_width=True)
                        with st.expander("📸 Weitere Bilder"):
                            st.image(anzeige["bilder_liste"], use_column_width=True)
                    else:
                        st.write("Kein Bild verfügbar.")

                with col2:
                    st.markdown(f"<div class='advert-title'>{anzeige['title']}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='advert-price'>{anzeige['price']} €</div>", unsafe_allow_html=True)
                    st.markdown(f"📍 **Ort:** {anzeige.get('ort', 'Unbekannt')}  \n"
                                f"🔗 [Zur Anzeige]({anzeige['link']})", unsafe_allow_html=True)
                    with st.expander("📄 Beschreibung einblenden"):
                        st.markdown(anzeige["description"])

                st.markdown("</div>", unsafe_allow_html=True)
