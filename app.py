import streamlit as st
from db import init_db, get_all_adverts_for_model, load_config, save_config, update_manual_defekt

# Initialisiere Datenbank (Tabellen erstellen, falls nicht vorhanden)
init_db()

st.set_page_config(page_title="Kleinanzeigen Analyzer", layout="wide")

st.title("📱 Kleinanzeigen Analyzer")

# Modellauswahl
modell = st.selectbox("iPhone-Modell auswählen", ["iPhone 14 Pro", "iPhone 13", "iPhone 12", "iPhone 11"])

# Debug-Modus
debug = st.checkbox("🔍 Debug-Modus aktivieren")

# Filter für Nur-Angebote mit Versand
nur_versand = st.checkbox("Nur Angebote mit Versand anzeigen")

# Anzeigen laden
anzeigen = get_all_adverts_for_model(modell)
if nur_versand:
    anzeigen = [a for a in anzeigen if a["versand"]]

if not anzeigen:
    st.info("Keine passenden Anzeigen gefunden.")
    st.stop()

# Konfiguration laden oder neu definieren
config = load_config(modell)

with st.expander("⚙️ Bewertungsparameter laden oder anpassen", expanded=False):
    if config:
        verkaufspreis = st.number_input("📈 Erwarteter Verkaufspreis (€)", value=config["verkaufspreis"])
        wunsch_marge = st.number_input("💰 Wunsch-Marge (€)", value=config["wunsch_marge"])
        reparaturkosten = config["reparaturkosten"]
    else:
        verkaufspreis = st.number_input("📈 Erwarteter Verkaufspreis (€)", value=450)
        wunsch_marge = st.number_input("💰 Wunsch-Marge (€)", value=100)
        reparaturkosten = {}

    st.markdown("🛠️ Reparaturkosten (Defektname → Preis in €):")
    raw_input = st.text_area("Format: display=150,battery=120,back=90", value=",".join(f"{k}={v}" for k, v in reparaturkosten.items()))
    try:
        reparaturkosten = {k.strip(): int(v.strip()) for k, v in (x.split("=") for x in raw_input.split(","))}
        save_config(modell, verkaufspreis, wunsch_marge, reparaturkosten)
        st.success("Bewertungsparameter gespeichert.")
    except:
        st.warning("❌ Formatfehler beim Speichern der Reparaturkosten.")

# Bewertungslogik
def berechne_bewertung(preis, reparatur_typ):
    rep_kosten = reparaturkosten.get(reparatur_typ, 0)
    restwert = verkaufspreis - rep_kosten - wunsch_marge
    return preis <= restwert

# Anzeigen-Übersicht
st.header(f"Anzeigen für {modell} ({len(anzeigen)} Treffer)")
for ad in anzeigen:
    with st.expander(f"{ad['title']} – {ad['price']} €", expanded=False):
        col1, col2 = st.columns([1, 3])

        with col1:
            st.image(ad["image"], use_column_width=True)

        with col2:
            st.markdown(f"**Preis:** {ad['price']} €")
            st.markdown(f"**Versand:** {'✅' if ad['versand'] else '❌'}")
            st.markdown(f"[🔗 Zur Anzeige]({ad['link']})")

            # Beschreibung anzeigen
            with st.expander("📝 Beschreibung"):
                st.write(ad["beschreibung"])

            # Dropdown zur manuellen Defektauswahl
            defektauswahl = st.selectbox(
                "Manueller Defekt:",
                options=["", *reparaturkosten.keys()],
                index=0 if ad["man_defekt"] == "" else list(reparaturkosten.keys()).index(ad["man_defekt"]) + 1,
                key=f"defekt_{ad['id']}"
            )

            # Bei Änderung speichern und neu laden
            if defektauswahl != ad["man_defekt"]:
                update_manual_defekt(ad["id"], defektauswahl)
                st.rerun()

            # Bewertung anzeigen
            if defektauswahl:
                if berechne_bewertung(ad["price"], defektauswahl):
                    st.markdown("✅ **Kaufpreis ist wirtschaftlich sinnvoll**")
                else:
                    st.markdown("❌ **Zu teuer für gewünschte Marge**")
            else:
                st.info("Bitte einen Defekt auswählen, um eine Bewertung zu sehen.")

        if debug:
            st.code(ad)

