import streamlit as st
import pandas as pd
import os
import json
import plotly.express as px
from datetime import date, datetime

# ==========================================
# 1. KONFIGURATION & DATEN
# ==========================================
st.set_page_config(page_title="Punktestatistik FP Cham", page_icon="🏆", layout="wide")

DB_FILE = "punktestatistik_datenbank.csv"
CONFIG_FILE = "config.json"
ADMIN_PASSWORD = "Gewichtheben-21" # <-- HIER KANNST DU DEIN PASSWORT ÄNDERN

# Standard-Konfiguration (wird beim allerersten Start genutzt)
DEFAULT_CONFIG = {
    "mitarbeiter": ["Daniel", "Lukas", "Carina", "Yvonne", "Anna"],
    "punkte_system": {
        "davon 24 Monate": 30.0,
        "davon 12 Monate": 25.0,
        "davon monatl. kündbar": 15.0,
        "VIP Abos heute": 5.0,
        "Basic Abos heute": 1.0,
        "24 Monate Umschreibung": 20.0,
        "VIP-Umschreibung": 5.0,
        "VIP-Kontakte": 15.0,
        "Promoleads": 15.0,
        "10er Karten-Leads": 15.0,
        "Google Bewertung gesammelt": 5.0,
        "Coaching-Termin": 5.0,
        "Feedbackbogen": 5.0,
        "Erfolgsberichte": 5.0,
        "Kürü": 10.0,
        "Add-on": 5.0,
        "§20 Kurs": 10.0,
        "DE nimmt ab": 10.0,
        "Personal Training (je Probetraining)": 10.0,
        "Personaltraining Umsatz (€)": 0.04,
        "Anwahlversuche Gesamt": 1.0,
        "davon erreicht": 0.0,
        "davon terminiert": 5.0,
        "davon nicht erreicht": 0.0,
        "Terminbestätigung": 5.0
    }
}

# ==========================================
# 2. HILFSFUNKTIONEN
# ==========================================
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    else:
        # Erstelle die Datei beim ersten Mal
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_CONFIG, f, indent=4)
        return DEFAULT_CONFIG

def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4)

def load_data():
    if os.path.exists(DB_FILE):
        return pd.read_csv(DB_FILE)
    else:
        return pd.DataFrame(columns=["Datum", "Mitarbeiter", "Tagespunkte"])

def save_entry(datum, mitarbeiter, eingaben, tagespunkte):
    df = load_data()
    mask = (df["Datum"] == str(datum)) & (df["Mitarbeiter"] == mitarbeiter)
    
    new_data = {"Datum": str(datum), "Mitarbeiter": mitarbeiter}
    new_data.update(eingaben)
    new_data["Tagespunkte"] = tagespunkte
    
    if mask.any():
        idx = df[mask].index[0]
        for key, val in new_data.items():
            df.at[idx, key] = val
        st.success(f"Eintrag für {mitarbeiter} am {datum} erfolgreich aktualisiert!")
    else:
        # pd.concat ist zukunftssicherer als append
        new_row_df = pd.DataFrame([new_data])
        df = pd.concat([df, new_row_df], ignore_index=True)
        st.success(f"Neuer Eintrag für {mitarbeiter} am {datum} erfolgreich gespeichert!")
        
    df.to_csv(DB_FILE, index=False)

# Session State für Admin-Login
if "admin_logged_in" not in st.session_state:
    st.session_state["admin_logged_in"] = False

# Konfiguration laden
config = load_config()
MITARBEITER = config["mitarbeiter"]
PUNKTE_SYSTEM = config["punkte_system"]

# ==========================================
# 3. BENUTZEROBERFLÄCHE (UI)
# ==========================================
st.title("🏆 Punktestatistik FP Cham")

tab1, tab2, tab3 = st.tabs(["📝 Tägliche Dateneingabe", "📊 Coole Statistiken", "⚙️ Admin-Bereich"])

# --- TAB 1: EINGABE ---
with tab1:
    st.header("Trage deine heutigen Erfolge ein")
    
    if not MITARBEITER:
        st.warning("Keine Mitarbeiter angelegt. Bitte gehe in den Admin-Bereich.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            selected_mitarbeiter = st.selectbox("Mitarbeiter auswählen", MITARBEITER)
        with col2:
            selected_date = st.date_input("Datum", value=date.today())
            
        st.markdown("---")
        st.subheader("Deine erreichten Ziele")
        
        with st.form("eingabe_form"):
            eingaben = {}
            cols = st.columns(3)
            
            for i, (kategorie, multiplikator) in enumerate(PUNKTE_SYSTEM.items()):
                col_idx = i % 3
                with cols[col_idx]:
                    if "€" in kategorie or "Umsatz" in kategorie:
                        eingaben[kategorie] = st.number_input(f"{kategorie} (Pkt: {multiplikator}/€)", min_value=0.0, step=10.0, format="%.2f")
                    else:
                        eingaben[kategorie] = st.number_input(f"{kategorie} (Pkt: {multiplikator})", min_value=0, step=1)
                        
            submit_button = st.form_submit_button(label="💾 Tagesergebnisse speichern")
            
            if submit_button:
                tagespunkte = sum(eingaben[kat] * mult for kat, mult in PUNKTE_SYSTEM.items())
                save_entry(selected_date, selected_mitarbeiter, eingaben, tagespunkte)
                st.info(f"Erreichte Punkte für diesen Tag: **{tagespunkte:.2f}**")

# --- TAB 2: STATISTIKEN ---
with tab2:
    st.header("Auswertungen & Leaderboard")
    df_stats = load_data()
    
    if df_stats.empty:
        st.warning("Noch keine Daten vorhanden.")
    else:
        df_stats["Datum"] = pd.to_datetime(df_stats["Datum"]).dt.date
        df_stats["Tagespunkte"] = pd.to_numeric(df_stats["Tagespunkte"])
        
        # Datumsfilter
        min_date = df_stats["Datum"].min()
        max_date = df_stats["Datum"].max()
        
        st.subheader("📅 Zeitraum auswählen")
        date_range = st.date_input("Von - Bis", value=(min_date, max_date), min_value=min_date, max_value=max_date)
        
        # Prüfen ob ein gültiger Zeitraum (Start und Ende) gewählt wurde
        if len(date_range) == 2:
            start_date, end_date = date_range
            # Daten filtern
            mask = (df_stats["Datum"] >= start_date) & (df_stats["Datum"] <= end_date)
            filtered_df = df_stats[mask]
            
            if filtered_df.empty:
                st.info("In diesem Zeitraum gibt es keine Einträge.")
            else:
                leaderboard = filtered_df.groupby("Mitarbeiter")["Tagespunkte"].sum().reset_index()
                leaderboard = leaderboard.sort_values(by="Tagespunkte", ascending=False)
                
                col_chart1, col_chart2 = st.columns([1, 2])
                with col_chart1:
                    st.subheader("🏆 Leaderboard")
                    st.dataframe(leaderboard.style.format({"Tagespunkte": "{:.2f}"}), hide_index=True, use_container_width=True)
                    
                with col_chart2:
                    st.subheader("📈 Punktevergleich")
                    fig_bar = px.bar(leaderboard, x="Mitarbeiter", y="Tagespunkte", 
                                     color="Mitarbeiter", text_auto=".2f",
                                     title=f"Gesamtpunkte ({start_date} bis {end_date})")
                    st.plotly_chart(fig_bar, use_container_width=True)
                    
                st.markdown("---")
                st.subheader("📉 Punkteverlauf über die Zeit")
                # Für den Linienchart sortieren
                filtered_df = filtered_df.sort_values(by="Datum")
                fig_line = px.line(filtered_df, x="Datum", y="Tagespunkte", color="Mitarbeiter", markers=True)
                st.plotly_chart(fig_line, use_container_width=True)

# --- TAB 3: ADMIN-BEREICH ---
with tab3:
    st.header("⚙️ Administrator-Bereich")
    
    # Login
    if not st.session_state["admin_logged_in"]:
        st.info("Bitte melde dich mit dem Passwort an, um Einstellungen zu ändern.")
        pwd_input = st.text_input("Passwort", type="password")
        if st.button("Login"):
            if pwd_input == ADMIN_PASSWORD:
                st.session_state["admin_logged_in"] = True
                st.rerun()
            else:
                st.error("Falsches Passwort!")
    
    # Admin-Dashboard (wenn eingeloggt)
    else:
        if st.button("🔓 Logout"):
            st.session_state["admin_logged_in"] = False
            st.rerun()
            
        st.markdown("---")
        
        col_admin1, col_admin2 = st.columns(2)
        
        # MITARBEITER VERWALTUNG
        with col_admin1:
            st.subheader("👤 Mitarbeiter verwalten")
            
            # Neuer Mitarbeiter
            new_ma = st.text_input("Neuen Mitarbeiter hinzufügen:")
            if st.button("Hinzufügen"):
                if new_ma and new_ma not in config["mitarbeiter"]:
                    config["mitarbeiter"].append(new_ma)
                    save_config(config)
                    st.success(f"{new_ma} hinzugefügt!")
                    st.rerun()
                    
            # Mitarbeiter löschen/archivieren
            st.write("Mitarbeiter entfernen (Archivieren):")
            ma_to_remove = st.selectbox("Wähle einen Mitarbeiter aus", ["- Bitte wählen -"] + config["mitarbeiter"])
            if st.button("❌ Auswählten Mitarbeiter entfernen"):
                if ma_to_remove != "- Bitte wählen -":
                    config["mitarbeiter"].remove(ma_to_remove)
                    save_config(config)
                    st.success(f"{ma_to_remove} wurde entfernt.")
                    st.rerun()

        # PUNKTESYSTEM VERWALTUNG
        with col_admin2:
            st.subheader("🎯 Punktesystem anpassen")
            
            # Neue Kategorie
            with st.expander("➕ Neues Ziel / Kategorie anlegen"):
                new_cat_name = st.text_input("Name des Ziels (z.B. Proteinshake verkauft)")
                new_cat_pts = st.number_input("Punkte dafür", min_value=0.0, step=0.5, value=1.0)
                if st.button("Ziel speichern"):
                    if new_cat_name:
                        config["punkte_system"][new_cat_name] = new_cat_pts
                        save_config(config)
                        st.success("Kategorie hinzugefügt!")
                        st.rerun()

            # Bestehende ändern/löschen
            st.write("Bestehende Ziele bearbeiten:")
            cat_to_edit = st.selectbox("Kategorie wählen", list(config["punkte_system"].keys()))
            
            if cat_to_edit:
                current_pts = float(config["punkte_system"][cat_to_edit])
                new_pts = st.number_input(f"Punkte für '{cat_to_edit}'", value=current_pts, step=0.5)
                
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("💾 Wert updaten"):
                        config["punkte_system"][cat_to_edit] = new_pts
                        save_config(config)
                        st.success("Aktualisiert!")
                        st.rerun()
                with col_btn2:
                    if st.button("🗑️ Kategorie löschen"):
                        del config["punkte_system"][cat_to_edit]
                        save_config(config)
                        st.warning("Kategorie gelöscht!")
                        st.rerun()