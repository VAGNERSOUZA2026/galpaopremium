import json
import os
import shutil
from datetime import datetime
import pandas as pd
import streamlit as st
import urllib.parse
from streamlit_javascript import st_javascript

# Importação segura do OpenCV
try:
    import cv2
    import numpy as np
    OPENCV_DISPONIVEL = True
except ImportError:
    OPENCV_DISPONIVEL = False

# Configuração da página
st.set_page_config(
    page_title="Premium Wines - Galpão",
    page_icon="imagem premium.jpeg",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Estilização CSS
st.markdown(
    """
    <style>
    .stApp { background: linear-gradient(135deg, #F8F9FA 0%, #E9ECEF 100%); color: #1A1A1A; font-family: 'Poppins', sans-serif; }
    [data-testid="stSidebar"] { display: none; }
    .wine-card { background-color: #FFFFFF; color: #1A1A1A; border-radius: 14px; padding: 16px; margin-bottom: 12px; border: 1px solid #E9ECEF; box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.03); }
    .wine-title { color: #7A1C2E; font-size: 1.1rem; font-weight: 700; margin-bottom: 4px; }
    .badge-pallet-grande { background-color: #7A1C2E; color: #FFFFFF; padding: 6px 14px; border-radius: 8px; font-weight: 700; font-size: 1rem; display: inline-block; box-shadow: 0px 2px 6px rgba(122, 28, 46, 0.2); }
    .badge-caixa-grande { background-color: #343A40; color: #FFFFFF; padding: 6px 14px; border-radius: 8px; font-weight: 700; font-size: 1rem; display: inline-block; box-shadow: 0px 2px 6px rgba(52, 58, 64, 0.2); }
    .stButton button { background-color: #7A1C2E !important; color: #FFFFFF !important; border-radius: 12px !important; font-weight: 600 !important; border: none !important; padding: 10px 16px !important; width: 100%; }
    </style>
    """, unsafe_allow_html=True
)

# Constantes e Configurações
NOME_ARQUIVO = "estoque_galpao_pro.json"
ARQUIVO_USUARIOS = "usuarios_galpao.json"
ARQUIVO_LOGS = "logs_auditoria.json"
PASTA_BACKUP = "backups_estoque"
if not os.path.exists(PASTA_BACKUP): os.makedirs(PASTA_BACKUP)

LISTA_CORREDORES = [f"Corredor {i:02d}" for i in range(1, 26)]
LISTA_PALLETS = [f"Pallet {i:02d}" for i in range(1, 26)]
LISTA_PRATELEIRAS = [f"Prateleira {i:02d}" for i in range(1, 6)]
LISTA_LADOS = ["Direito", "Esquerdo", "Centro / Único"]
OPCOES_CAIXA = ["Caixa com 12 garrafas", "Caixa com 6 garrafas", "Caixa com 3 garrafas", "Caixa com 2 garrafas", "Garrafa Avulsa (1 un)"]

# Funções auxiliares
def obter_saudacao():
    hora = datetime.now().hour
    if 0 <= hora < 12: return "Bom dia"
    elif 12 <= hora < 18: return "Boa tarde"
    else: return "Boa noite"

def realizar_backup(nome_arquivo):
    if os.path.exists(nome_arquivo):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        shutil.copy(nome_arquivo, os.path.join(PASTA_BACKUP, f"backup_{timestamp}_{nome_arquivo}"))

def salvar_dados(estoque):
    with open(NOME_ARQUIVO, "w", encoding="utf-8") as f: json.dump(estoque, f, ensure_ascii=False, indent=4)
    realizar_backup(NOME_ARQUIVO)

def buscar_por_voz():
    js_code = """
    window.SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    recognition.lang = 'pt-BR';
    recognition.start();
    return new Promise((resolve) => {
        recognition.onresult = (event) => { resolve(event.results[0][0].transcript); };
        recognition.onerror = (event) => { resolve(""); };
    });
    """
    return st_javascript(js_code)

# Inicialização de Estado
if "estoque" not in st.session_state: st.session_state.estoque = [] # Carregar do arquivo aqui
if "usuario_logado" not in st.session_state: st.session_state.usuario_logado = None
if "menu_atual" not in st.session_state: st.session_state.menu_atual = "🏠 Home"
if "termo_busca" not in st.session_state: st.session_state.termo_busca = ""

# --- LÓGICA DE NAVEGAÇÃO ---
if st.session_state.usuario_logado is None:
    # (Inserir aqui o código de login da mensagem anterior para poupar espaço)
    st.info("Por favor, faça login.")
    st.stop()

# --- MENUS ---
if st.session_state.menu_atual == "🏠 Home":
    st.markdown(f"## {obter_saudacao()}, {st.session_state.usuario_logado['nome']}!")
    if st.button("🔍 Buscar / Filtros"): st.session_state.menu_atual = "Filtros"; st.rerun()

elif st.session_state.menu_atual == "Filtros":
    st.subheader("🔍 Busca por Nome ou Voz")
    c_texto, c_voz = st.columns([4, 1])
    with c_texto:
        termo = st.text_input("Filtrar:", value=st.session_state.termo_busca)
    with c_voz:
        st.write("<br>", unsafe_allow_html=True)
        if st.button("🎙️ Voz"):
            resultado = buscar_por_voz()
            if resultado:
                st.session_state.termo_busca = resultado
                st.rerun()

    if termo:
        res = [v for v in st.session_state.estoque if termo.lower() in v.get("nome", "").lower()]
        for v in res:
            st.markdown(f"<div class='wine-card'>{v.get('nome')}</div>", unsafe_allow_html=True)

# ... Adicione os outros blocos (Scanner, Estoque, Cadastrar, etc) seguindo a estrutura lógica.
