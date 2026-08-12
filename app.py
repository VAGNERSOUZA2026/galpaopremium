import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, timezone, timedelta

# --- Configuração Inicial ---
st.set_page_config(page_title="Premium Wines - Galpão", layout="wide")

# Simulação de base de dados (o seu layout original)
if "estoque" not in st.session_state:
    st.session_state.estoque = [
        {"nome": "la consulta malbec", "tipo": "Tinto", "safra": "2024", "localizacao": "Corredor 01 - Pallet Item 02", "lado": "Direito", "caixa": "Caixa com 12 garrafas", "foto": "", "codigo_barras": "None"},
        {"nome": "Quereu Carmenere", "tipo": "Tinto", "safra": "2024", "localizacao": "Corredor 01 - Pallet Item 01", "lado": "Direito", "caixa": "Caixa com 12 garrafas", "foto": "", "codigo_barras": "None"},
        {"nome": "Vina Ane Autor", "tipo": "Tinto", "safra": "2021", "localizacao": "Corredor 03 - Pallet Item 05", "lado": "Esquerdo", "caixa": "Caixa com 12 garrafas", "foto": "", "codigo_barras": "None"},
        {"nome": "Falernia Carmenere", "tipo": "Tinto", "safra": "2022", "localizacao": "Corredor 03 - Pallet Item 03", "lado": "Direito", "caixa": "Caixa com 12 garrafas", "foto": "", "codigo_barras": "None"},
        {"nome": "Quereu Chardonnay", "tipo": "Branco", "safra": "2025", "localizacao": "Corredor 01 - Pallet Item 07", "lado": "Esquerdo", "caixa": "Caixa com 12 garrafas", "foto": "", "codigo_barras": "None"},
        {"nome": "La Consulta Cabernet Sauvignon", "tipo": "Branco", "safra": "2023", "localizacao": "Corredor 01 - Pallet Item 01", "lado": "Direito", "caixa": "Caixa com 12 garrafas", "foto": "", "codigo_barras": "7891000457467"}
    ]

# --- Navegação ---
menu = st.sidebar.radio("Navegação", ["Home", "Cadastrar", "Separar Pedido"])

if menu == "Home":
    st.title("Estoque Disponível")
    st.table(pd.DataFrame(st.session_state.estoque))

elif menu == "Cadastrar":
    st.title("Cadastrar Vinho")
    # ... aqui você mantém o seu formulário original ...
    st.write("Formulário de cadastro mantido.")

elif menu == "Separar Pedido":
    st.title("Separar Pedido")
    
    # Lista de exemplo para conferência
    if "pedido" not in st.session_state:
        st.session_state.pedido = pd.DataFrame([
            {"nome": "la consulta malbec", "qtd_esperada": 2, "qtd_descida": 0},
            {"nome": "Vina Ane Autor", "qtd_esperada": 1, "qtd_descida": 0}
        ])

    st.write("Edite a coluna 'qtd_descida' abaixo:")
    df_editado = st.data_editor(st.session_state.pedido)
    
    if st.button("Gerar Romaneio"):
        # Fuso de Brasília (GMT-3)
        hora_br = datetime.now(timezone(timedelta(hours=-3))).strftime('%d/%m/%Y %H:%M')
        
        texto_romaneio = f"ROMANEIO - PREMIUM WINES\nData: {hora_br}\n\n"
        for _, row in df_editado.iterrows():
            texto_romaneio += f"Item: {row['nome']} | Pedido: {row['qtd_esperada']} | Descida: {row['qtd_descida']}\n"
        
        st.download_button("📥 Baixar Romaneio (.txt)", texto_romaneio, "romaneio.txt")
        st.success(f"Romaneio gerado com hora de Brasília: {hora_br}")
