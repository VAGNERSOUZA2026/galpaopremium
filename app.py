import json
import os
import shutil
from datetime import datetime, timezone, timedelta
import pandas as pd
import streamlit as st
import urllib.parse

# Configuração da página idêntica à original
st.set_page_config(
    page_title="Premium Wines - Galpão",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Estilo original
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #F8F9FA 0%, #E9ECEF 100%); color: #1A1A1A; }
    label { color: #7A1C2E !important; font-weight: 700 !important; }
    .stButton button { background-color: #7A1C2E !important; color: #FFFFFF !important; }
    </style>
""", unsafe_allow_html=True)

# Estado inicial completo
if "estoque" not in st.session_state:
    st.session_state.estoque = [
        {"nome": "la consulta malbec", "tipo": "Tinto", "safra": "2024", "localizacao": "Corredor 01 - Pallet Item 02", "lado": "Direito", "caixa": "Caixa com 12 garrafas", "foto": "", "codigo_barras": "None"},
        {"nome": "Quereu Carmenere", "tipo": "Tinto", "safra": "2024", "localizacao": "Corredor 01 - Pallet Item 01", "lado": "Direito", "caixa": "Caixa com 12 garrafas", "foto": "", "codigo_barras": "None"},
        {"nome": "Vina Ane Autor", "tipo": "Tinto", "safra": "2021", "localizacao": "Corredor 03 - Pallet Item 05", "lado": "Esquerdo", "caixa": "Caixa com 12 garrafas", "foto": "", "codigo_barras": "None"},
        {"nome": "Falernia Carmenere", "tipo": "Tinto", "safra": "2022", "localizacao": "Corredor 03 - Pallet Item 03", "lado": "Direito", "caixa": "Caixa com 12 garrafas", "foto": "", "codigo_barras": "None"},
        {"nome": "Quereu Chardonnay", "tipo": "Branco", "safra": "2025", "localizacao": "Corredor 01 - Pallet Item 07", "lado": "Esquerdo", "caixa": "Caixa com 12 garrafas", "foto": "", "codigo_barras": "None"},
        {"nome": "La Consulta Cabernet Sauvignon", "tipo": "Branco", "safra": "2023", "localizacao": "Corredor 01 - Pallet Item 01", "lado": "Direito", "caixa": "Caixa com 12 garrafas", "foto": "", "codigo_barras": "7891000457467"}
    ]

# Navegação lateral
menu = st.sidebar.radio("Navegação", ["Home", "Cadastrar", "Separar Pedido"])

if menu == "Home":
    st.title("Estoque Disponível")
    st.table(pd.DataFrame(st.session_state.estoque))

elif menu == "Cadastrar":
    st.title("Cadastrar Vinho")
    with st.form("cad_form"):
        nome = st.text_input("Nome")
        tipo = st.selectbox("Tipo", ["Tinto", "Branco", "Rosé", "Espumante"])
        safra = st.text_input("Safra")
        local = st.text_input("Localização")
        if st.form_submit_button("Salvar"):
            st.session_state.estoque.append({"nome": nome, "tipo": tipo, "safra": safra, "localizacao": local, "lado": "Direito", "caixa": "Caixa", "foto": "", "codigo_barras": "None"})
            st.success("Salvo!")

elif menu == "Separar Pedido":
    st.title("Separar Pedido")
    
    # Exibe a lista para conferência
    df_pedido = pd.DataFrame([
        {"nome": "la consulta malbec", "qtd_pedido": 5, "caixas_descidas": 0},
        {"nome": "Quereu Carmenere", "qtd_pedido": 2, "caixas_descidas": 0}
    ])
    
    st.write("### Conferência de Caixas")
    df_editado = st.data_editor(df_pedido, use_container_width=True)
    
    if st.button("Gerar Romaneio Final"):
        # Fuso horário de Brasília forçado
        fuso_br = timezone(timedelta(hours=-3))
        hora_br = datetime.now(fuso_br).strftime('%d/%m/%Y %H:%M')
        
        texto = f"ROMANEIO PREMIUM WINES\nData: {hora_br}\n\n"
        for _, row in df_editado.iterrows():
            texto += f"Item: {row['nome']} | Pedido: {row['qtd_pedido']} | Descidas: {row['caixas_descidas']}\n"
        
        st.download_button("📥 BAIXAR ROMANEIO .TXT", texto, "romaneio.txt")
        st.success(f"Romaneio gerado com hora de Brasília: {hora_br}")
