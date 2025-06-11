import streamlit as st
import db
import datetime

st.set_page_config(layout="wide")

st.title("📱 Kleinanzeigen Analyzer")

# --- Seitenleiste ---
st.sidebar.header("⚙️ Erweiterte Bewertungsparameter")
modell = st.sidebar.selectbox("Modell auswählen", ["iPhone 14 Pro", "iPhone 13", "iPhone 12"])
verkaufspreis = st.sidebar.number_input("Verkaufspreis (€)", min_value=0, value=500)
wunsch_marge = st.sidebar.number_input("Gewünschte Marge (€)", min_value=0, value=100)

# Reparaturkosten als Dict eingeben
st.sidebar.markdown("**Reparaturkosten pro Defekt:**")
defekt_keys = ["Akku", "Display", "Kratzer", "FaceID", "Lautsprecher"]
defekt_kosten = {}
for key in defekt_keys:
    defekt_kosten[key] = st.sidebar.number_input(f"{key}", min_value=0, value=50 if key != "Display" else 150, key=f"rep_{key}")

# Konfiguration speichern
if st.sidebar.button("💾 Konfiguration speichern"):
    db.save_config(modell, verkaufspreis, wunsch_marge, defekt_kosten)
    st.sidebar.success("Konfiguration gespeichert")

# Konfiguration laden (zur Sicherheit beim Start)
config = db.load_config(modell)
if config:
    verkaufspreis = config["verkaufspreis"]
    wunsch_marge = config["wunsch_marge"]
    defekt_kosten = config["reparaturkosten"]

# --- Anzeigen laden ---
anzeigen = db.get_all_adverts_for_model(modell)
st.subheader(f"🔍 Gefundene Anzeigen für: {modell} ({len(anzeigen)})")

for ad in anzeigen:
    with st.container():
        cols = st.columns([1, 2, 2, 2])

        with cols[0]:
            st.image(ad["image"], width=120)
            st.markdown(f"[🔗 Zur Anzeige]({ad['link']})", unsafe_allow_html=True)

        with cols[1]:
            st.markdown(f"**{ad['title']}**")
            st.markdown(f"**Preis:** {ad['price']} €")
            st.markdown(f"**Versand:** {'✅' if ad['versand'] else '❌'}")
            created = datetime.datetime.fromisoformat(ad["created_at"]).strftime("%d.%m.%Y %H:%M")
            updated = datetime.datetime.fromisoformat(ad["updated_at"]).strftime("%d.%m.%Y %H:%M")
            st.caption(f"Erfasst: {created} | Aktualisiert: {updated}")

        with cols[2]:
            with st.expander("📄 Beschreibung anzeigen"):
                st.markdown(ad["beschreibung"] or "(Keine Beschreibung)")

            # Dropdown für manuelle Defekte (Mehrfachauswahl)
            aktuelle_auswahl = eval(ad["man_defekt"] or "[]")
            neue_auswahl = st.multiselect(
                "🛠️ Defekte auswählen",
                defekt_kosten.keys(),
                default=aktuelle_auswahl,
                key=f"defekt_{ad['id']}"
            )

            # Speichern Button
            if neue_auswahl != aktuelle_auswahl:
                db.update_manual_defekt(ad["id"], repr(neue_auswahl))
                st.success("Defektauswahl gespeichert")

        with cols[3]:
            # Bewertung basierend auf manueller Defektauswahl
            gesamt_reparatur = sum(defekt_kosten.get(defekt, 0) for defekt in neue_auswahl)
            max_einkaufspreis = verkaufspreis - wunsch_marge - gesamt_reparatur
            differenz = ad["price"] - max_einkaufspreis

            st.metric("Max. Einkaufspreis", f"{max_einkaufspreis} €")
            st.metric("Differenz", f"{differenz:+} €", delta_color="inverse")

            if differenz <= 0:
                st.success("✅ Lohnenswert")
            else:
                st.error("❌ Zu teuer")
