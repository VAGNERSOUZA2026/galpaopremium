import json
import os
import shutil # Para backups
from datetime import datetime
import pandas as pd
import streamlit as st
import urllib.parse
from streamlit_javascript import st_javascript # Necessário instalar: pip install streamlit-javascript

# --- CONFIGURAÇÃO DE BACKUP ---
PASTA_BACKUP = "backups_estoque"
if not os.path.exists(PASTA_BACKUP):
    os.makedirs(PASTA_BACKUP)

def realizar_backup(nome_arquivo):
    if os.path.exists(nome_arquivo):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        shutil.copy(nome_arquivo, os.path.join(PASTA_BACKUP, f"backup_{timestamp}_{nome_arquivo}"))

# --- FUNÇÃO DE BUSCA POR VOZ (BROWSER API) ---
def buscar_por_voz():
    js_code = """
    window.SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    recognition.lang = 'pt-BR';
    recognition.start();
    return new Promise((resolve) => {
        recognition.onresult = (event) => {
            resolve(event.results[0][0].transcript);
        };
    });
    """
    return st_javascript(js_code)

# (O restante do código permanece o mesmo, mas ajustamos as funções de salvar)

def salvar_dados(estoque):
    with open(NOME_ARQUIVO, "w", encoding="utf-8") as f: 
        json.dump(estoque, f, ensure_ascii=False, indent=4)
    realizar_backup(NOME_ARQUIVO) # Chamada do Backup Automático

# --- AJUSTE NA TELA DE FILTROS ---
elif st.session_state.menu_atual == "Filtros":
    st.subheader("🔍 Busca por Nome ou Voz")
    
    col_b1, col_b2 = st.columns([4, 1])
    with col_b1:
        termo = st.text_input("Filtrar por Nome:").strip().lower()
    with col_b2:
        st.write("<br>", unsafe_allow_html=True)
        if st.button("🎙️ Voz"):
            resultado_voz = buscar_por_voz()
            if resultado_voz:
                termo = resultado_voz.lower()
                st.info(f"Você disse: {termo}")
