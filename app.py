import streamlit as st
import pandas as pd
import uuid
from streamlit_gsheets import GSheetsConnection # Ajout de la connexion

# --- CONFIGURATION ---
st.set_page_config(page_title="Vote Keyce 2026", layout="wide")

# --- CONNEXION BASE DE DONNÉES (Google Sheets) ---
conn = st.connection("gsheets", type=GSheetsConnection)

# Fonction pour lire les données depuis Sheets
def load_data():
    try:
        return conn.read(worksheet="Candidats", ttl=0)
    except:
        # Si la feuille est vide, on crée une structure de base
        return pd.DataFrame(columns=["nom", "desc", "votes"])

# --- INITIALISATION ---
# On garde le session_state pour les jetons et matricules (sécurité temporaire)
if 'tokens' not in st.session_state:
    st.session_state.tokens = {} 
if 'matricules_autorises' not in st.session_state:
    st.session_state.matricules_autorises = {} 
if 'titre_vote' not in st.session_state:
    st.session_state.titre_vote = "Election Master Keyce 2026"

# --- NAVIGATION ---
menu = st.sidebar.radio("Navigation", ["Récupérer mon Jeton", "Voter", "Espace Admin"])

# --- 1. RÉCUPÉRER MON JETON ---
if menu == "Récupérer mon Jeton":
    st.title("🎟️ Obtenir mon droit de vote")
    nom_user = st.text_input("Nom complet")
    mat_user = st.text_input("Numéro Matricule (ex: MATA001)").upper().strip()

    if st.button("Générer mon jeton"):
        if mat_user in st.session_state.matricules_autorises:
            if st.session_state.matricules_autorises[mat_user]: 
                nouveau_token = str(uuid.uuid4()).upper()[:8]
                st.session_state.tokens[nouveau_token] = True
                st.session_state.matricules_autorises[mat_user] = False # Désactive le matricule
                
                st.success(f"Félicitations {nom_user} ! Voici votre jeton unique :")
                st.code(nouveau_token)
                st.warning("⚠️ Notez ce code. Vous ne pourrez plus le récupérer ensuite !")
            else:
                st.error("Ce matricule a déjà été utilisé pour générer un jeton.")
        else:
            st.error("Matricule non autorisé. Vérifiez l'orthographe ou contactez l'admin.")

# --- 2. VOTER ---
elif menu == "Voter":
    st.title(f"🗳️ {st.session_state.titre_vote}")
    
    # Chargement depuis Google Sheets
    df_candidats = load_data()
    
    if df_candidats.empty:
        st.info("Le vote n'a pas encore commencé.")
    else:
        # Affichage des candidats (dynamique depuis Sheets)
        cols = st.columns(len(df_candidats))
        for idx, row in df_candidats.iterrows():
            with cols[idx]:
                # Note: La gestion des photos binaires dans Sheets est complexe, 
                # ici on affiche le nom et la desc.
                st.subheader(row['nom'])
                st.caption(row['desc'])
        
        st.divider()
        choix = st.selectbox("Choisissez votre candidat", df_candidats['nom'].tolist())
        token_saisi = st.text_input("Entrez votre Jeton")

        if st.button("Valider le vote"):
            if token_saisi in st.session_state.tokens and st.session_state.tokens[token_saisi]:
                # MISE À JOUR DANS GOOGLE SHEETS
                df_candidats.loc[df_candidats["nom"] == choix, "votes"] += 1
                conn.update(worksheet="Candidats", data=df_candidats)
                
                st.session_state.tokens[token_saisi] = False
                st.balloons()
                st.success(f"Vote pour {choix} pris en compte et enregistré dans la base !")
            else:
                st.error("Jeton invalide.")

# --- 3. ESPACE ADMIN ---
else:
    st.title("⚙️ Administration")
    if st.text_input("Mot de passe", type="password") == "admin123":
        
        st.session_state.titre_vote = st.text_input("Nom du vote", value=st.session_state.titre_vote)
        
        with st.expander("Ajouter un candidat"):
            n = st.text_input("Nom")
            d = st.text_area("Description")
            if st.button("Ajouter"):
                # SAUVEGARDE DANS GOOGLE SHEETS
                df_actuel = load_data()
                nouveau = pd.DataFrame([{"nom": n, "desc": d, "votes": 0}])
                df_final = pd.concat([df_actuel, nouveau], ignore_index=True)
                conn.update(worksheet="Candidats", data=df_final)
                st.success(f"Candidat {n} ajouté à la base de données !")
                st.rerun()

        # GÉNÉRATEUR AUTOMATIQUE DE MATRICULES
        st.divider()
        st.subheader("🎓 Générateur de Matricules en masse")
        col1, col2, col3 = st.columns(3)
        prefixe = col1.text_input("Préfixe (ex: MATA)", value="MATA")
        debut = col2.number_input("Début (Nombre)", value=1, step=1)
        fin = col3.number_input("Fin (Nombre)", value=100, step=1)

        if st.button("Générer la liste des matricules"):
            for i in range(int(debut), int(fin) + 1):
                m_genere = f"{prefixe}{i:03d}" 
                st.session_state.matricules_autorises[m_genere] = True
            st.success(f"Matricules de {prefixe}{int(debut):03d} à {prefixe}{int(fin):03d} ajoutés !")

        st.write(f"Nombre total de matricules autorisés : {len(st.session_state.matricules_autorises)}")
        
        # Résultats (Lecture directe depuis Sheets)
        st.divider()
        df_resultats = load_data()
        if not df_resultats.empty:
            st.subheader("📊 Résultats en temps réel (Base de données)")
            st.table(df_resultats[['nom', 'votes']])
