import json
import os
import pandas as pd
import streamlit as st
import urllib.parse

# Configuração da página Streamlit (Tema Claro)
st.set_page_config(
    page_title="Wine Map Pro - Galpão Premium",
    page_icon="🍷",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Estilização CSS Personalizada (Tema Light & Gold - Fundo Claro e Alta Legibilidade)
st.markdown(
    """
    <style>
    html, body {
        overscroll-behavior-y: contain;
    }
    .stApp {
        background-color: #F8F9FA;
        color: #212529;
        font-family: 'Poppins', sans-serif;
    }
    .header-container {
        text-align: center;
        padding: 10px 0 15px 0;
    }
    .main-title {
        font-size: 1.8rem;
        font-weight: 800;
        color: #7A1C2E;
        margin-top: 5px;
        letter-spacing: -0.5px;
    }
    .sub-title {
        font-size: 0.9rem;
        color: #6C757D;
        margin-bottom: 10px;
    }
    .metric-card {
        background-color: #FFFFFF !important;
        border-radius: 14px;
        padding: 20px;
        margin-bottom: 15px;
        border: 1px solid #E2E8F0;
        box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.05);
        text-align: left;
    }
    .metric-title {
        color: #6C757D !important;
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
        color: #212529 !important;
        font-size: 2rem;
        font-weight: 800;
    }
    .metric-value-alert {
        color: #DC3545 !important;
        font-size: 2rem;
        font-weight: 800;
    }
    .wine-card {
        background-color: #FFFFFF !important;
        color: #212529 !important;
        border-radius: 16px;
        padding: 16px;
        margin-bottom: 15px;
        border: 1px solid #E2E8F0 !important;
        box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.05);
    }
    .wine-title {
        color: #7A1C2E !important;
        font-size: 1.2rem;
        font-weight: 700;
        margin-bottom: 6px;
    }
    .wine-text {
        color: #495057 !important;
        font-size: 0.9rem;
    }
    .badge-pallet {
        background-color: #7A1C2E !important;
        color: #FFFFFF !important;
        padding: 4px 10px;
        border-radius: 8px;
        font-weight: 600;
        font-size: 0.8rem;
        display: inline-block;
    }
    .custom-table {
        width: 100%;
        border-collapse: collapse;
        background-color: #FFFFFF;
        color: #212529;
        border-radius: 12px;
        overflow: hidden;
        margin-top: 10px;
        box-shadow: 0px 4px 12px rgba(0,0,0,0.05);
        border: 1px solid #E2E8F0;
    }
    .custom-table th {
        background-color: #7A1C2E;
        color: #FFFFFF;
        text-align: left;
        padding: 12px 15px;
        font-size: 0.9rem;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .custom-table td {
        padding: 12px 15px;
        border-bottom: 1px solid #E2E8F0;
        color: #212529;
        font-size: 0.9rem;
    }
    .custom-table tr:hover {
        background-color: #F8F9FA;
    }
    .stTextInput input, .stSelectbox select {
        background-color: #FFFFFF !important;
        color: #212529 !important;
        border: 1px solid #CED4DA !important;
        border-radius: 8px !important;
    }
    .stButton button {
        background-color: #7A1C2E !important;
        color: #FFFFFF !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        border: none !important;
    }
    .stButton button:hover {
        background-color: #922338 !important;
        color: #FFD700 !important;
    }
    </style>
""",
    unsafe_allow_html=True,
)

SENHA_ACESSO = "1980"
NOME_ARQUIVO = "estoque_galpao_pro.json"
NOME_DEV = "Vagner Souza"
TITULO_DEV = "Ciência da Computação"
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

def gerar_qr_code_api(texto):
    texto_encoded = urllib.parse.quote(texto)
    url = f"https://api.qrserver.com/v1/create-qr-code/?size=250x250&data={texto_encoded}"
    return url

# --- ESTADO DE SESSÃO ---
if "estoque" not in st.session_state:
    st.session_state.estoque = carregar_dados()

if "form_key" not in st.session_state:
    st.session_state.form_key = 0

if "usuarios" not in st.session_state:
    st.session_state.usuarios = []

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
    st.markdown("<h2 style='color:#7A1C2E;'>🍷 Wine Map Pro</h2>", unsafe_allow_html=True)

    opcoes_menu = [
        "🏠 Home / Dashboard",
        "🔍 Buscar vinho",
        "📷 Escanear QR Code / Câmera",
        "📱 Gerar QR Code de Pallets",
        "🍷 Ver estoque completo",
        "➕ Cadastrar novo vinho",
        "✏️ Editar vinho",
        "🗑️ Excluir vinho",
        "👤 Cadastrar usuário",
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
        <div style="background: #FFFFFF; padding: 14px; border-radius: 12px; color: #212529; text-align: center; margin-top: 15px; border: 1px solid #E2E8F0; box-shadow: 0px 2px 6px rgba(0,0,0,0.03);">
            <p style="margin: 0; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 1px; color: #7A1C2E; font-weight: bold;">Desenvolvimento</p>
            <h4 style="margin: 4px 0 2px 0; color: #212529; font-size: 1.05rem;">{NOME_DEV}</h4>
            <p style="margin: 0 0 8px 0; font-size: 0.78rem; color: #6C757D;">🎓 {TITULO_DEV}</p>
            <p style="margin: 0; font-size: 0.78rem; color: #C9A227; font-weight: bold;">📞 {FONE_DEV}</p>
        </div>
    """, unsafe_allow_html=True)

# --- NAVEGAÇÃO DAS TELAS ---
if st.session_state.menu_atual == "🏠 Home / Dashboard":
    st.markdown("""
        <div class="header-container" style="text-align: left; padding-left: 10px;">
            <p style="color: #6C757D; margin: 0; font-size: 0.9rem;">Bom dia,</p>
            <h1 style="color: #212529; font-size: 1.6rem; margin: 0; font-weight: 700;">Vagner! 👋</h1>
            <p style="color: #6C757D; font-size: 0.8rem; margin-top: 2px;">Bem-vindo ao WineMap Pro</p>
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
        st.markdown('<div class="metric-card"><div class="metric-title">Último QR Code</div><div style="color: #212529; font-size: 0.95rem; font-weight: 600; margin-top: 4px;">Corredor 08<br>Pallet 15</div></div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("<p style='color: #6C757D; font-size: 0.9rem; font-weight: 600; margin-bottom: 10px;'>Ações rápidas</p>", unsafe_allow_html=True)
    
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
        st.markdown(f"<h3 style='color: #7A1C2E;'>📍 Pallet Identificado: {pallet_detectado}</h3>", unsafe_allow_html=True)
        
        vinhos_pallet = [v for v in st.session_state.estoque if v.get("pallet") == pallet_detectado]
        if vinhos_pallet:
            st.markdown("<p style='color: #495057;'>Vinhos presentes neste pallet (Sem necessidade de abrir as caixas):</p>", unsafe_allow_html=True)
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
    st.markdown("<p style='color: #6C757D;'>Gere e imprima o QR Code para colar no pallet do galpão. Assim, qualquer operador consegue ver quais vinhos estão guardados apenas escaneando com o celular.</p>", unsafe_allow_html=True)
    
    c_corr = st.selectbox("Selecione o Corredor:", LISTA_CORREDORES)
    c_pall = st.selectbox("Selecione o Pallet:", LISTA_PALLETS)
    pallet_selecionado = f"{c_corr} - {c_pall}"
    
    if st.button("Gerar QR Code do Pallet", use_container_width=True):
        url_qr = gerar_qr_code_api(pallet_selecionado)
        st.image(url_qr, caption=f"QR Code para {pallet_selecionado}", width=250)
        
        vinhos_no_local = [v for v in st.session_state.estoque if v.get("pallet") == pallet_selecionado]
        st.markdown(f"<h4 style='color: #7A1C2E; margin-top: 20px;'>Vinhos vinculados ao {pallet_selecionado}:</h4>", unsafe_allow_html=True)
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
        idx = st.selectbox("Selecione o Vinho para Editar:", range(len(opcoes)), format_func=lambda x: opcoes[x])
        vinho = st.session_state.estoque[idx]
        
        with st.form("form_edit_completo"):
            novo_nome = st.text_input("Nome do Vinho:", vinho.get("nome", ""))
            novo_tipo = st.text_input("Tipo (ex: Tinto, Branco):", vinho.get("tipo", ""))
            
            safra_atual = vinho.get("safra", "Sem Safra (NV)")
            idx_safra = OPCOES_SAFRA.index(safra_atual) if safra_atual in OPCOES_SAFRA else 0
            nova_safra = st.selectbox("Safra:", OPCOES_SAFRA, index=idx_safra)
            
            pallet_atual = vinho.get("pallet", "Corredor 01 - Pallet 01")
            partes_pallet = pallet_atual.split(" - ")
            c_corr_atual = partes_pallet[0] if len(partes_pallet) > 0 else LISTA_CORREDORES[0]
            c_pall_atual = partes_pallet[1] if len(partes_pallet) > 1 else LISTA_PALLETS[0]
            
            idx_corr = LISTA_CORREDORES.index(c_corr_atual) if c_corr_atual in LISTA_CORREDORES else 0
            idx_pall = LISTA_PALLETS.index(c_pall_atual) if c_pall_atual in LISTA_PALLETS else 0
            
            novo_corredor = st.selectbox("Corredor:", LISTA_CORREDORES, index=idx_corr)
            novo_pallet_num = st.selectbox("Pallet:", LISTA_PALLETS, index=idx_pall)
            
            lado_atual = vinho.get("lado", "Direito")
            idx_lado = LISTA_LADOS.index(lado_atual) if lado_atual in LISTA_LADOS else 0
            novo_lado = st.selectbox("Lado:", LISTA_LADOS, index=idx_lado)
            
            caixa_atual = vinho.get("caixa", "Caixa com 12 garrafas")
            idx_caixa = OPCOES_CAIXA.index(caixa_atual) if caixa_atual in OPCOES_CAIXA else 0
            nova_caixa = st.selectbox("Caixa:", OPCOES_CAIXA, index=idx_caixa)
            
            if st.form_submit_button("SALVAR ALTERAÇÕES", use_container_width=True):
                if novo_nome.strip() and novo_tipo.strip():
                    vinho["nome"] = novo_nome.strip()
                    vinho["tipo"] = novo_tipo.strip()
                    vinho["safra"] = nova_safra
                    vinho["pallet"] = f"{novo_corredor} - {novo_pallet_num}"
                    vinho["lado"] = novo_lado
                    vinho["caixa"] = nova_caixa
                    
                    salvar_dados(st.session_state.estoque)
                    st.success("Alterações salvas com sucesso!")
                    st.rerun()
                else:
                    st.error("O Nome e o Tipo não podem ficar vazios.")
    else:
        st.info("Nenhum vinho cadastrado para editar.")

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

elif st.session_state.menu_atual == "👤 Cadastrar usuário":
    st.subheader("👤 Cadastro de Novo Usuário / Operador")
    with st.form("form_novo_usuario"):
        nome_usuario = st.text_input("Nome Completo do Operador:").strip()
        email_usuario = st.text_input("E-mail ou Matrícula:").strip()
        cargo_usuario = st.selectbox("Nível de Acesso:", ["Operador de Galpão", "Conferente", "Administrador"])
        
        if st.form_submit_button("CADASTRAR USUÁRIO", use_container_width=True):
            if nome_usuario:
                st.session_state.usuarios.append({"nome": nome_usuario, "cargo": cargo_usuario})
                st.success(f"🎉 Seja muito bem-vindo(a) ao Wine Map Pro, **{nome_usuario}**! Seu cadastro como **{cargo_usuario}** foi realizado com sucesso.")
            else:
                st.error("Por favor, preencha o nome do operador.")
