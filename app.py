import streamlit as st
import pandas as pd
import uuid

# --- CONFIGURATION ---
st.set_page_config(page_title="Vote Keyce 2026", layout="wide")

# --- INITIALISATION ---
if 'candidats' not in st.session_state:
    st.session_state.candidats = []
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
    if not st.session_state.candidats:
        st.info("Le vote n'a pas encore commencé.")
    else:
        cols = st.columns(len(st.session_state.candidats))
        for idx, cand in enumerate(st.session_state.candidats):
            with cols[idx]:
                st.image(cand['photo'], use_container_width=True)
                st.subheader(cand['nom'])
                st.caption(cand['desc'])
        
        st.divider()
        choix = st.selectbox("Choisissez votre candidat", [c['nom'] for c in st.session_state.candidats])
        token_saisi = st.text_input("Entrez votre Jeton")

        if st.button("Valider le vote"):
            if token_saisi in st.session_state.tokens and st.session_state.tokens[token_saisi]:
                for c in st.session_state.candidats:
                    if c['nom'] == choix:
                        c['votes'] += 1
                        st.session_state.tokens[token_saisi] = False
                        st.balloons()
                        st.success("Vote pris en compte !")
                        break
            else:
                st.error("Jeton invalide.")

# --- 3. ESPACE ADMIN ---
else:
    st.title("⚙️ Administration")
    if st.text_input("Mot de passe", type="password") == "admin123":
        
        # Titre et Candidats
        st.session_state.titre_vote = st.text_input("Nom du vote", value=st.session_state.titre_vote)
        
        with st.expander("Ajouter un candidat"):
            n = st.text_input("Nom")
            d = st.text_area("Description")
            p = st.file_uploader("Photo", type=['jpg', 'png'])
            if st.button("Ajouter"):
                st.session_state.candidats.append({"nom":n, "desc":d, "photo":p.read(), "votes":0})
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
                # Formatage avec des zéros (ex: MATA001)
                m_genere = f"{prefixe}{i:03d}" 
                st.session_state.matricules_autorises[m_genere] = True
            st.success(f"Matricules de {prefixe}{int(debut):03d} à {prefixe}{int(fin):03d} ajoutés !")

        st.write(f"Nombre total de matricules autorisés : {len(st.session_state.matricules_autorises)}")
        
        # Résultats
        st.divider()
        if st.session_state.candidats:
            st.subheader("📊 Résultats")
            res_df = pd.DataFrame(st.session_state.candidats)
            st.table(res_df[['nom', 'votes']])
