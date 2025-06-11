import streamlit as st
from db import init_db, get_all_adverts_for_model, load_config, update_manual_defekt

# Datenbank initialisieren
init_db()

# Modellauswahl
modell = st.selectbox("iPhone-Modell auswählen", ["iPhone 14 Pro", "iPhone 13", "iPhone 12", "iPhone 11"])
anzeigen = get_all_adverts_for_model(modell)

if not anzeigen:
    st.info("Keine Anzeigen für dieses Modell gefunden.")
    st.stop()

# Konfiguration laden
config = load_config(modell)
if config is None:
    st.warning("Keine Konfiguration für dieses Modell gefunden.")
    st.stop()

verkaufspreis = config["verkaufspreis"]
wunsch_marge = config["wunsch_marge"]
reparaturkosten = config["reparaturkosten"]

def berechne_bewertung(preis, reparatur_typ):
    rep_kosten = reparaturkosten.get(reparatur_typ, 0)
    restwert = verkaufspreis - rep_kosten - wunsch_marge
    return preis <= restwert

st.title(f"Anzeigen für {modell}")
for ad in anzeigen:
    with st.expander(f"{ad['title']} – {ad['price']} €", expanded=False):
        col1, col2 = st.columns([1, 3])

        with col1:
            st.image(ad["image"], use_column_width=True)

        with col2:
            st.markdown(f"**Preis:** {ad['price']} €")
            st.markdown(f"**Versand:** {'✅' if ad['versand'] else '❌'}")
            st.markdown(f"[Anzeigen-Link öffnen]({ad['link']})")

            # Beschreibung einklappbar
            with st.expander("📝 Beschreibung anzeigen"):
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
