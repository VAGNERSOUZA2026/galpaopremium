import streamlit as st
import json
import os
import shutil
from datetime import datetime
import pandas as pd
import urllib.parse
from streamlit_javascript import st_javascript

# Importação para ler arquivos
import openpyxl
from docx import Document

# 1. Configuração da página (deve ser a primeira chamada do Streamlit)
st.set_page_config(
    page_title="Premium Wines - Galpão",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# 2. Estilização CSS Dark Mode (Wine Map Pro Style)
st.markdown(
    """
    <style>
    /* Fundo Geral */
    .stApp {
        background-color: #121212 !important;
        color: #FFFFFF !important;
        font-family: 'Poppins', sans-serif;
    }

    /* Cards Estilo Wine Map Pro */
    .wine-card {
        background-color: #1E1E1E !important;
        border: 1px solid #333333 !important;
        border-radius: 16px !important;
        padding: 16px !important;
        margin-bottom: 12px !important;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.3) !important;
    }

    /* Botões */
    div.stButton > button {
        background-color: #581825 !important;
        color: #FFFFFF !important;
        border-radius: 12px !important;
        border: none !important;
        font-weight: 600 !important;
    }
    
    /* Títulos */
    h1, h2, h3 { color: #FFFFFF !important; }
    
    /* Inputs */
    .stTextInput > div > div > input {
        background-color: #1E1E1E !important;
        color: white !important;
        border: 1px solid #333333 !important;
    }
    </style>
    """, unsafe_allow_html=True
)

# --- O RESTO DO SEU CÓDIGO CONTINUA AQUI ---
# (Certifique-se de que a lógica de banco de dados, funções, 
# autenticação e as telas (if/elif) estejam abaixo disso)

# Exemplo de como usar o card nas telas:
# st.markdown('<div class="wine-card"><h3>Bem-vindo ao Wine Map Pro</h3></div>', unsafe_allow_html=True)

# ... resto da sua lógica ...
