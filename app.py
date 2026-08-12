import streamlit as st
import pandas as pd
from datetime import datetime, timezone, timedelta

# --- Configuração ---
st.set_page_config(page_title="Premium Wines - Galpão", layout="wide")

# --- Dados Originais (Sua Estrutura) ---
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
st.sidebar.title("Navegação")
menu = st.sidebar.radio("Ir para:", ["Home", "Cadastrar", "Separar Pedido"])

if menu == "Home":
    st.title("Estoque Atual")
    # Exibe exatamente como na sua imagem
    st.table(pd.DataFrame(st.session_state.estoque))

elif menu == "Cadastrar":
    st.title("Cadastrar Vinho")
    st.write("Funcionalidade de cadastro original.")
    # (Adicione aqui seu formulário original se necessário)

elif menu == "Separar Pedido":
    st.title("Separar Pedido")
    
    # Lista para conferência
    df_pedido = pd.DataFrame([
        {"nome": "la consulta malbec", "qtd_pedido": 5, "caixas_descidas": 0},
        {"nome": "Quereu Carmenere", "qtd_pedido": 2, "caixas_descidas": 0}
    ])
    
    st.write("Confira as caixas descidas abaixo:")
    df_conferencia = st.data_editor(df_pedido)
    
    if st.button("Gerar Romaneio"):
        # Hora de Brasília (GMT-3)
        hora_br = datetime.now(timezone(timedelta(hours=-3))).strftime('%d/%m/%Y %H:%M')
        
        texto_romaneio = f"ROMANEIO - PREMIUM WINES\nData: {hora_br}\n\n"
        for _, row in df_conferencia.iterrows():
            texto_romaneio += f"Produto: {row['nome']} | Pedido: {row['qtd_pedido']} | Descidas: {row['caixas_descidas']}\n"
        
        st.download_button("📥 Baixar Romaneio (.txt)", texto_romaneio, "romaneio_final.txt")
        st.success(f"Romaneio gerado: {hora_br}")
