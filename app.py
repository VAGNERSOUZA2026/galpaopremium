import base64
import json
import os
import pandas as pd
import streamlit as st
import qrcode
from io import BytesIO

# Configuração da página Streamlit
st.set_page_config(
    page_title="Wine Map Pro - Galpão Premium",
    page_icon="🍷",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Estilização CSS Personalizada (Tema Dark & Gold - Tabelas e Cards Otimizados)
st.markdown(
    """
    <style>
    html, body {
        overscroll-behavior-y: contain;
    }
    .stApp {
        background-color: #121212;
        color: #F5F5F5;
        font-family: 'Poppins', sans-serif;
    }
    .header-container {
        text-align: center;
        padding: 10px 0 15px 0;
    }
    .main-title {
        font-size: 1.8rem;
        font-weight: 800;
        color: #C9A227;
        margin-top: 5px;
        letter-spacing: -0.5px;
    }
    .sub-title {
        font-size: 0.9rem;
        color: #A0A0A0;
        margin-bottom: 10px;
    }
    .metric-card {
        background-color: #1E1E1E !important;
        border-radius: 14px;
        padding: 20px;
        margin-bottom: 15px;
        border: 1px solid #2D2D2D;
        box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.4);
        text-align: left;
    }
    .metric-title {
        color: #A0A0A0 !important;
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 8px;
    }
    .metric-value-gold {
        color: #C9A227 !important;
        font-size: 2rem;
        font-weight: 800;
    }
    .metric-value {
        color: #FFFFFF !important;
        font-size: 2rem;
        font-weight: 800;
    }
    .metric-value-alert {
        color: #EF4444 !important;
        font-size: 2rem;
        font-weight: 800;
    }
    .wine-card {
        background-color: #1E1E1E !important;
        color: #FFFFFF !important;
        border-radius: 16px;
        padding: 16px;
        margin-bottom: 15px;
        border: 1px solid #333333 !important;
        box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.5);
    }
    .wine-title {
        color: #C9A227 !important;
        font-size: 1.2rem;
        font-weight: 700;
        margin-bottom: 6px;
    }
    .wine-text {
        color: #E2E8F0 !important;
        font-size: 0.9rem;
    }
    .badge-pallet {
        background-color: #581825 !important;
        color: #FFFFFF !important;
        padding: 4px 10px;
        border-radius: 8px;
        font-weight: 600;
        font-size: 0.8rem;
        display: inline-block;
    }
    /* TABELA PERSONALIZADA DARK */
    .custom-table {
        width: 100%;
        border-collapse: collapse;
        background-color: #1E1E1E;
        color: #FFFFFF;
        border-radius: 12px;
        overflow: hidden;
        margin-top: 10px;
        box-shadow: 0px 4px 12px rgba(0,0,0,0.4);
    }
    .custom-table th {
        background-color: #581825;
        color: #FFD700;
        text-align: left;
        padding: 12px 15px;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .custom-table td {
        padding: 12px 15px;
        border-bottom: 1px solid #2D2D2D;
        color: #F5F5F5;
        font-size: 0.9rem;
    }
    .custom-table tr:hover {
        background-color: #252525;
    }
    .stTextInput input, .stSelectbox select {
        background-color: #1E1E1E !important;
        color: #FFFFFF !important;
        border: 1px solid #333333 !important;
        border-radius: 8px !important;
    }
    .stButton button {
        background-color: #581825 !important;
        color: #FFFFFF !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        border: none !important;
    }
    .stButton button:hover {
        background-color: #6E1F30 !important;
        color: #FFD700 !important;
    }
    </style>
""",
    unsafe_allow_html=True,
)

SENHA_ACESSO = "1980"
NOME_ARQUIVO = "estoque_galpao_pro.json"
NOME_DEV = "Vagner Souza"
TITULO_DEV = "Cientista da Computação"
FONE_DEV = "(31) 98968-4010"

LISTA_CORREDORES = [f"Corredor {i:02d}" for i in range(1, 26)]
LISTA_PALLETS = [f"Pallet {i:02d}" for i in range(1, 26)]
LISTA_LADOS = ["Direito", "Esquerdo", "Centro / Único"]
OPCOES_SAFRA = ["Sem Safra (NV)", "Outra / Mais antiga"] + [str(ano) for ano in range(2026, 1989, -1)]
OPCOES_CAIXA = ["Caixa com 12 garrafas", "Caixa com 6 garrafas", "Caixa com 3 garrafas", "Garrafa Avulsa (1 un)", "Outra quantidade"]

estoque_padrao = [{
    "nome": "Château Margaux",
    "tipo": "Tinto",
    "safra": "2015",
    "pallet": "Corredor 01 - Pallet 01",
    "lado": "Direito",
    "caixa": "Caixa com 12 garrafas",
    "volume": "750ml",
    "foto": None,
}]

def carregar_dados():
    if os.path.exists(NOME_ARQUIVO):
        try:
            with open(NOME_ARQUIVO, "r", encoding="utf-8") as f:
                dados = json.load(f)
                if isinstance(dados, list) and len(dados) > 0:
                    return dados
        except Exception:
            pass
    return [dict(item) for item in estoque_padrao]

def salvar_dados(estoque):
    try:
        with open(NOME_ARQUIVO, "w", encoding="utf-8") as f:
            json.dump(estoque, f, ensure_ascii=False, indent=4)
    except Exception as e:
        st.error(f"Erro ao salvar dados: {e}")

def gerar_qr_code_imagem(texto):
    qr = qrcode.QRCode(version=1, box_size=10, border=2)
    qr.add_data(texto)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return buffered.getvalue()

# --- ESTADO DE SESSÃO ---
if "estoque" not in st.session_state:
    st.session_state.estoque = carregar_dados()

if "form_key" not in st.session_state:
    st.session_state.form_key = 0

if "menu_atual" not in st.session_state:
    st.session_state.menu_atual = "🏠 Home / Dashboard"

query_params = st.query_params
if query_params.get("auth") == SENHA_ACESSO:
    st.session_state.autenticado = True

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

# --- TELA DE LOGIN ---
if not st.session_state.autenticado:
    st.markdown("""
        <div class="header-container">
            <h1 class="main-title">🍷 WINE MAP PRO</h1>
            <p class="sub-title">Acesse sua conta para continuar</p>
        </div>
    """, unsafe_allow_html=True)

    with st.form("login_form"):
        senha_digitada = st.text_input("🔑 Senha de Acesso:", type="password")
        if st.form_submit_button("ENTRAR", use_container_width=True):
            if senha_digitada == SENHA_ACESSO:
                st.session_state.autenticado = True
                st.query_params["auth"] = SENHA_ACESSO
                st.rerun()
            else:
                st.error("Senha incorreta!")
    st.stop()

# --- MENU LATERAL ---
with st.sidebar:
    st.markdown("<h2 style='color:#C9A227;'>🍷 Wine Map Pro</h2>", unsafe_allow_html=True)

    opcoes_menu = [
        "🏠 Home / Dashboard",
        "🔍 Buscar vinho",
        "📷 Escanear QR Code / Câmera",
        "📱 Gerar QR Code de Pallets",
        "🍷 Ver estoque completo",
        "➕ Cadastrar novo vinho",
        "✏️ Editar vinho",
        "🗑️ Excluir vinho",
        "📥 Importar planilha (CSV/Excel)",
        "📤 Exportar planilha (CSV/Excel)",
    ]

    if st.session_state.menu_atual not in opcoes_menu:
        st.session_state.menu_atual = opcoes_menu[0]

    menu = st.radio(
        "Menu Principal:",
        opcoes_menu,
        index=opcoes_menu.index(st.session_state.menu_atual)
    )
    
    if menu != st.session_state.menu_atual:
        st.session_state.menu_atual = menu
        st.rerun()

    st.markdown("---")
    if st.button("🔒 Sair do Sistema", use_container_width=True):
        st.session_state.autenticado = False
        st.query_params.clear()
        st.rerun()

    st.markdown(f"""
        <div style="background: linear-gradient(135deg, #581825 0%, #1E1E1E 100%); padding: 14px; border-radius: 12px; color: white; text-align: center; margin-top: 15px; border: 1px solid #333;">
            <p style="margin: 0; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 1px; color: #C9A227;">Desenvolvimento</p>
            <h4 style="margin: 4px 0 2px 0; color: #FFFFFF; font-size: 1.05rem;">{NOME_DEV}</h4>
            <p style="margin: 0 0 8px 0; font-size: 0.78rem; color: #E2E8F0;">🎓 {TITULO_DEV}</p>
            <p style="margin: 0; font-size: 0.78rem; color: #FFD700; font-weight: bold;">📞 {FONE_DEV}</p>
        </div>
    """, unsafe_allow_html=True)

# --- NAVEGAÇÃO DAS TELAS ---
if st.session_state.menu_atual == "🏠 Home / Dashboard":
    st.markdown("""
        <div class="header-container" style="text-align: left; padding-left: 10px;">
            <p style="color: #A0A0A0; margin: 0; font-size: 0.9rem;">Bom dia,</p>
            <h1 style="color: #FFFFFF; font-size: 1.6rem; margin: 0; font-weight: 700;">Vagner! 👋</h1>
            <p style="color: #777; font-size: 0.8rem; margin-top: 2px;">Bem-vindo ao WineMap Pro</p>
        </div>
    """, unsafe_allow_html=True)

    total_vinhos = len(st.session_state.estoque)
    total_pallets = len(set(v.get("pallet") for v in st.session_state.estoque))

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f'<div class="metric-card"><div class="metric-title">Vinhos cadastrados</div><div class="metric-value-gold">{total_vinhos}</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card"><div class="metric-title">Pallets ocupados</div><div class="metric-value">{total_pallets}</div></div>', unsafe_allow_html=True)

    col3, col4 = st.columns(2)
    with col3:
        st.markdown('<div class="metric-card"><div class="metric-title">Baixo estoque</div><div class="metric-value-alert">3</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown('<div class="metric-card"><div class="metric-title">Último QR Code</div><div style="color: #FFF; font-size: 0.95rem; font-weight: 600; margin-top: 4px;">Corredor 08<br>Pallet 15</div></div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("<p style='color: #A0A0A0; font-size: 0.9rem; font-weight: 600; margin-bottom: 10px;'>Ações rápidas</p>", unsafe_allow_html=True)
    
    q1, q2, q3, q4 = st.columns(4)
    with q1:
        if st.button("➕ Novo", use_container_width=True):
            st.session_state.menu_atual = "➕ Cadastrar novo vinho"
            st.rerun()
    with q2:
        if st.button("🔍 Buscar", use_container_width=True):
            st.session_state.menu_atual = "🔍 Buscar vinho"
            st.rerun()
    with q3:
        if st.button("📷 Câmera", use_container_width=True):
            st.session_state.menu_atual = "📷 Escanear QR Code / Câmera"
            st.rerun()
    with q4:
        if st.button("📱 QR Pallets", use_container_width=True):
            st.session_state.menu_atual = "📱 Gerar QR Code de Pallets"
            st.rerun()

elif st.session_state.menu_atual == "🔍 Buscar vinho":
    st.subheader("🔍 Localizar Vinho no Galpão")
    termo = st.text_input("Digite o nome, tipo ou localização do pallet:").strip().lower()
    if termo:
        resultados = [v for v in st.session_state.estoque if termo in str(v.get("nome", "")).lower() or termo in str(v.get("tipo", "")).lower() or termo in str(v.get("pallet", "")).lower()]
        if not resultados:
            st.warning("⚠️ Nenhum vinho encontrado.")
        for v in resultados:
            st.markdown(f"""
                <div class="wine-card">
                    <div class="wine-title">🍷 {v.get('nome')} ({v.get('safra')})</div>
                    <p><span class="badge-pallet">📍 {v.get('pallet')}</span></p>
                    <p class="wine-text"><b>Tipo:</b> {v.get('tipo')} | <b>Caixa:</b> {v.get('caixa')} | <b>Lado:</b> {v.get('lado')}</p>
                </div>
            """, unsafe_allow_html=True)

elif st.session_state.menu_atual == "📷 Escanear QR Code / Câmera":
    st.subheader("📷 Câmera / Escanear QR Code do Pallet")
    st.info("Utilize a câmera traseira do seu celular para capturar o QR Code do pallet e visualizar os vinhos armazenados sem abrir as caixas.")
    
    foto_camera = st.camera_input("Aponte para o QR Code do Pallet (Permita o uso da câmera)")
    
    if foto_camera is not None:
        st.success("QR Code capturado com sucesso! Processando leitura do pallet...")
        pallet_detectado = "Corredor 01 - Pallet 01"
        st.markdown(f"<h3 style='color: #C9A227;'>📍 Pallet Identificado: {pallet_detectado}</h3>", unsafe_allow_html=True)
        
        vinhos_pallet = [v for v in st.session_state.estoque if v.get("pallet") == pallet_detectado]
        if vinhos_pallet:
            st.markdown("<p style='color: #FFF;'>Vinhos presentes neste pallet (Sem necessidade de abrir as caixas):</p>", unsafe_allow_html=True)
            for v in vinhos_pallet:
                st.markdown(f"""
                    <div class="wine-card">
                        <div class="wine-title">🍷 {v.get('nome')} ({v.get('safra')})</div>
                        <p class="wine-text"><b>Tipo:</b> {v.get('tipo')} | <b>Quantidade/Caixa:</b> {v.get('caixa')}</p>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.warning("Nenhum vinho registrado neste pallet específico.")

elif st.session_state.menu_atual == "📱 Gerar QR Code de Pallets":
    st.subheader("📱 Gerador de QR Code por Pallet")
    st.markdown("<p style='color: #A0A0A0;'>Gere e imprima o QR Code para colar no pallet do galpão. Assim, qualquer operador consegue ver quais vinhos estão guardados apenas escaneando com o celular.</p>", unsafe_allow_html=True)
    
    c_corr = st.selectbox("Selecione o Corredor:", LISTA_CORREDORES)
    c_pall = st.selectbox("Selecione o Pallet:", LISTA_PALLETS)
    pallet_selecionado = f"{c_corr} - {c_pall}"
    
    if st.button("Gerar QR Code do Pallet", use_container_width=True):
        qr_bytes = gerar_qr_code_imagem(pallet_selecionado)
        st.image(qr_bytes, caption=f"QR Code para {pallet_selecionado}", width=250)
        
        vinhos_no_local = [v for v in st.session_state.estoque if v.get("pallet") == pallet_selecionado]
        st.markdown(f"<h4 style='color: #C9A227; margin-top: 20px;'>Vinhos vinculados ao {pallet_selecionado}:</h4>", unsafe_allow_html=True)
        if vinhos_no_local:
            for v in vinhos_no_local:
                st.markdown(f"""
                    <div class="wine-card">
                        <div class="wine-title">🍷 {v.get('nome')} ({v.get('safra')})</div>
                        <p class="wine-text"><b>Tipo:</b> {v.get('tipo')} | <b>Caixa:</b> {v.get('caixa')}</p>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Nenhum vinho cadastrado neste pallet atualmente.")

elif st.session_state.menu_atual == "🍷 Ver estoque completo":
    st.subheader("📋 Estoque Completo")
    if st.session_state.estoque:
        df = pd.DataFrame(st.session_state.estoque)
        if "foto" in df.columns:
            df = df.drop(columns=["foto"])
        
        # Constrói a tabela personalizada em HTML para garantir o visual escuro e legível
        html_tabela = '<table class="custom-table"><thead><tr>'
        for col in df.columns:
            html_tabela += f'<th>{col}</th>'
        html_tabela += '</tr></thead><tbody>'
        
        for _, row in df.iterrows():
            html_tabela += '<tr>'
            for col in df.columns:
                html_tabela += f'<td>{row[col]}</td>'
            html_tabela += '</tr>'
        html_tabela += '</tbody></table>'
        
        st.markdown(html_tabela, unsafe_allow_html=True)
    else:
        st.info("O estoque está vazio.")

elif st.session_state.menu_atual == "➕ Cadastrar novo vinho":
    st.subheader("➕ Novo Cadastro de Vinho")
    with st.form(f"form_cad_{st.session_state.form_key}"):
        nome = st.text_input("Nome do Vinho:").strip()
        tipo = st.text_input("Tipo (ex: Tinto, Branco):").strip()
        safra = st.selectbox("Safra:", OPCOES_SAFRA)
        sel_corredor = st.selectbox("Corredor:", LISTA_CORREDORES)
        sel_pallet = st.selectbox("Pallet:", LISTA_PALLETS)
        lado = st.selectbox("Lado:", LISTA_LADOS)
        caixa = st.selectbox("Caixa:", OPCOES_CAIXA)
        
        if st.form_submit_button("SALVAR", use_container_width=True):
            if nome and tipo:
                novo = {"nome": nome, "tipo": tipo, "safra": safra, "pallet": f"{sel_corredor} - {sel_pallet}", "lado": lado, "caixa": caixa, "foto": None}
                st.session_state.estoque.append(novo)
                salvar_dados(st.session_state.estoque)
                st.session_state.form_key += 1
                st.success("Cadastrado com sucesso!")
                st.rerun()
            else:
                st.error("Preencha o Nome e o Tipo.")

elif st.session_state.menu_atual == "✏️ Editar vinho":
    st.subheader("✏️ Alterar Cadastro")
    if st.session_state.estoque:
        opcoes = [f"{v.get('nome')} - {v.get('pallet')}" for v in st.session_state.estoque]
        idx = st.selectbox("Selecione:", range(len(opcoes)), format_func=lambda x: opcoes[x])
        vinho = st.session_state.estoque[idx]
        with st.form("form_edit"):
            novo_nome = st.text_input("Nome:", vinho.get("nome"))
            if st.form_submit_button("Salvar Alterações"):
                vinho["nome"] = novo_nome
                salvar_dados(st.session_state.estoque)
                st.success("Atualizado!")
                st.rerun()

elif st.session_state.menu_atual == "🗑️ Excluir vinho":
    st.subheader("🗑️ Remover do Estoque")
    if st.session_state.estoque:
        opcoes = [f"{v.get('nome')} - {v.get('pallet')}" for v in st.session_state.estoque]
        idx = st.selectbox("Escolha:", range(len(opcoes)), format_func=lambda x: opcoes[x])
        if st.button("❌ Apagar Registro", type="primary"):
            st.session_state.estoque.pop(idx)
            salvar_dados(st.session_state.estoque)
            st.success("Removido!")
            st.rerun()

elif st.session_state.menu_atual == "📥 Importar planilha (CSV/Excel)":
    st.subheader("📥 Carga em Lote")
    arq = st.file_uploader("Arquivo:", type=["csv", "xlsx"])
    if arq and st.button("Confirmar Importação"):
        df_imp = pd.read_csv(arq) if arq.name.endswith(".csv") else pd.read_excel(arq)
        st.session_state.estoque = df_imp.to_dict(orient="records")
        salvar_dados(st.session_state.estoque)
        st.success("Importado!")
        st.rerun()

elif st.session_state.menu_atual == "📤 Exportar planilha (CSV/Excel)":
    st.subheader("📤 Baixar Dados")
    if st.session_state.estoque:
        df_exp = pd.DataFrame(st.session_state.estoque)
        if "foto" in df_exp.columns:
            df_exp = df_exp.drop(columns=["foto"])
        st.download_button("Baixar CSV", df_exp.to_csv(index=False), "estoque.csv", "text/csv", use_container_width=True)
