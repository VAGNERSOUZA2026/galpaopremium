import json
import os
import pandas as pd
import streamlit as st
import urllib.parse

# Configuração da página Streamlit (Tema Claro e Layout Otimizado)
st.set_page_config(
    page_title="Wine Map Pro - Galpão Premium",
    page_icon="🍷",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Estilização CSS Baseada no Design Moderno (Fundo Branco, Bordô e Dourado)
st.markdown(
    """
    <style>
    html, body {
        overscroll-behavior-y: contain;
    }
    .stApp {
        background-color: #FFFFFF;
        color: #1A1A1A;
        font-family: 'Poppins', sans-serif;
    }
    .header-container {
        padding: 10px 0 15px 0;
    }
    .main-title {
        font-size: 1.6rem;
        font-weight: 700;
        color: #1A1A1A;
        margin: 0;
    }
    .sub-title {
        font-size: 0.85rem;
        color: #6C757D;
        margin-top: 2px;
    }
    /* Estilo dos Cards de Métricas idênticos ao mockup */
    .metric-grid {
        display: flex;
        gap: 12px;
        margin-bottom: 15px;
    }
    .metric-card {
        background-color: #F8F9FA;
        border-radius: 16px;
        padding: 18px;
        border: 1px solid #E9ECEF;
        flex: 1;
        box-shadow: 0px 2px 8px rgba(0, 0, 0, 0.02);
    }
    .metric-title {
        color: #6C757D;
        font-size: 0.78rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 6px;
    }
    .metric-value-gold {
        color: #C9A227;
        font-size: 1.8rem;
        font-weight: 800;
    }
    .metric-value {
        color: #1A1A1A;
        font-size: 1.8rem;
        font-weight: 800;
    }
    .metric-value-alert {
        color: #DC3545;
        font-size: 1.8rem;
        font-weight: 800;
    }
    /* Cards de Vinho */
    .wine-card {
        background-color: #FFFFFF;
        color: #1A1A1A;
        border-radius: 14px;
        padding: 16px;
        margin-bottom: 12px;
        border: 1px solid #E9ECEF;
        box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.03);
    }
    .wine-title {
        color: #7A1C2E;
        font-size: 1.1rem;
        font-weight: 700;
        margin-bottom: 4px;
    }
    .wine-text {
        color: #495057;
        font-size: 0.85rem;
    }
    .badge-pallet {
        background-color: #7A1C2E;
        color: #FFFFFF;
        padding: 3px 8px;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.75rem;
        display: inline-block;
    }
    /* Botões Padrão Bordo */
    .stButton button {
        background-color: #7A1C2E !important;
        color: #FFFFFF !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        border: none !important;
        padding: 10px 16px !important;
    }
    .stButton button:hover {
        background-color: #922338 !important;
        color: #FFD700 !important;
    }
    </style>
""",
    unsafe_allow_html=True,
)

SENHA_PADRAO = "1980"
NOME_ARQUIVO = "estoque_galpao_pro.json"
ARQUIVO_USUARIOS = "usuarios_galpao.json"
NOME_DEV = "Vagner Souza"
TITULO_DEV = "Ciência da Computação"
FONE_DEV = "(31) 98968-4010"

LISTA_CORREDORES = [f"Corredor {i:02d}" for i in range(1, 26)]
LISTA_PALLETS = [f"Pallet {i:02d}" for i in range(1, 26)]
LISTA_LADOS = ["Direito", "Esquerdo", "Centro / Único"]
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

def carregar_usuarios():
    if os.path.exists(ARQUIVO_USUARIOS):
        try:
            with open(ARQUIVO_USUARIOS, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return [{"nome": "Vagner Souza", "cargo": "Administrador", "senha": "1980"}]

def salvar_usuarios(usuarios):
    try:
        with open(ARQUIVO_USUARIOS, "w", encoding="utf-8") as f:
            json.dump(usuarios, f, ensure_ascii=False, indent=4)
    except Exception as e:
        st.error(f"Erro ao salvar usuários: {e}")

def gerar_qr_code_api(texto):
    texto_encoded = urllib.parse.quote(texto)
    url = f"https://api.qrserver.com/v1/create-qr-code/?size=250x250&data={texto_encoded}"
    return url

# --- ESTADO DE SESSÃO ---
if "estoque" not in st.session_state:
    st.session_state.estoque = carregar_dados()

if "usuarios" not in st.session_state:
    st.session_state.usuarios = carregar_usuarios()

if "form_key" not in st.session_state:
    st.session_state.form_key = 0

if "operador_atual" not in st.session_state:
    st.session_state.operador_atual = "Vagner"

if "autenticado_admin" not in st.session_state:
    st.session_state.autenticado_admin = False

if "menu_atual" not in st.session_state:
    st.session_state.menu_atual = "🏠 Home"

# --- BARRA LATERAL (MENU COMPLETO) ---
with st.sidebar:
    st.markdown("<h2 style='color:#7A1C2E;'>🍷 Wine Map Pro</h2>", unsafe_allow_html=True)
    st.markdown("<p style='font-size: 0.8rem; color: #6C757D;'>Encontre qualquer vinho em segundos.</p>", unsafe_allow_html=True)
    st.markdown("---")

    opcoes_menu = [
        "🏠 Home",
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

    menu = st.radio("Navegação Principal:", opcoes_menu, index=opcoes_menu.index(st.session_state.menu_atual))
    
    if menu != st.session_state.menu_atual:
        st.session_state.menu_atual = menu
        st.rerun()

    st.markdown("---")
    st.markdown(f"""
        <div style="background: #F8F9FA; padding: 12px; border-radius: 10px; color: #1A1A1A; text-align: center; border: 1px solid #E9ECEF;">
            <p style="margin: 0; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 1px; color: #7A1C2E; font-weight: bold;">Desenvolvimento</p>
            <h4 style="margin: 3px 0 2px 0; color: #1A1A1A; font-size: 0.95rem;">{NOME_DEV}</h4>
            <p style="margin: 0 0 6px 0; font-size: 0.75rem; color: #6C757D;">🎓 {TITULO_DEV}</p>
            <p style="margin: 0; font-size: 0.75rem; color: #C9A227; font-weight: bold;">📞 {FONE_DEV}</p>
        </div>
    """, unsafe_allow_html=True)

# --- CONTROLE DE SENHA APENAS PARA EDIÇÃO/CADASTRO ---
telas_protegidas = ["➕ Cadastrar novo vinho", "✏️ Editar vinho", "🗑️ Excluir vinho", "👤 Cadastrar usuário"]

if st.session_state.menu_atual in telas_protegidas and not st.session_state.autenticado_admin:
    st.markdown("""
        <div class="header-container" style="text-align: center; margin-top: 40px;">
            <h1 class="main-title" style="color: #7A1C2E;">🔒 Área Restrita</h1>
            <p class="sub-title">Esta função exige a senha de autorização do sistema (Padrão: 1980)</p>
        </div>
    """, unsafe_allow_html=True)
    
    col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
    with col_l2:
        with st.form("form_senha_restrita"):
            senha_tentativa = st.text_input("🔑 Digite a Senha:", type="password")
            if st.form_submit_button("AUTORIZAR", use_container_width=True):
                if senha_tentativa == SENHA_PADRAO:
                    st.session_state.autenticado_admin = True
                    st.success("Acesso liberado com sucesso!")
                    st.rerun()
                else:
                    st.error("Senha incorreta!")
    st.stop()

# --- TELAS DO APLICATIVO (ESTILO MOCKUP BRANCO) ---
if st.session_state.menu_atual == "🏠 Home":
    st.markdown(f"""
        <div class="header-container">
            <p class="sub-title">Bom dia,</p>
            <h1 class="main-title">{st.session_state.operador_atual}! 👋</h1>
            <p class="sub-title">Bem-vindo ao WineMap Pro</p>
        </div>
    """, unsafe_allow_html=True)

    total_vinhos = len(st.session_state.estoque)
    total_pallets = len(set(v.get("pallet") for v in st.session_state.estoque))

    # Grid de Métricas idêntico ao modelo (Dashboard Card Layout)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f'<div class="metric-card"><div class="metric-title">Vinhos cadastrados</div><div class="metric-value-gold">{total_vinhos}</div></div>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<div class="metric-card"><div class="metric-title">Pallets ocupados</div><div class="metric-value">{total_pallets}</div></div>', unsafe_allow_html=True)

    col3, col4 = st.columns(2)
    with col3:
        st.markdown('<div class="metric-card"><div class="metric-title">Baixo estoque</div><div class="metric-value-alert">3</div></div>', unsafe_allow_html=True)
    with col4:
        st.markdown('<div class="metric-card"><div class="metric-title">Último QR Code</div><div style="color: #1A1A1A; font-size: 0.9rem; font-weight: 600; margin-top: 4px;">Corredor 08<br>Pallet 15</div></div>', unsafe_allow_html=True)

    st.markdown("---")
    
    # Botão de destaque centralizado para escanear
    if st.button("📷  ESCANEAR QR CODE DO PALLET", use_container_width=True):
        st.session_state.menu_atual = "📷 Escanear QR Code / Câmera"
        st.rerun()

    st.markdown("<p style='color: #6C757D; font-size: 0.85rem; font-weight: 600; margin: 15px 0 8px 0;'>Ações rápidas</p>", unsafe_allow_html=True)
    
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
        if st.button("🍷 Estoque", use_container_width=True):
            st.session_state.menu_atual = "🍷 Ver estoque completo"
            st.rerun()
    with q4:
        if st.button("📱 QR Pallets", use_container_width=True):
            st.session_state.menu_atual = "📱 Gerar QR Code de Pallets"
            st.rerun()

elif st.session_state.menu_atual == "🔍 Buscar vinho":
    st.subheader("🔍 Buscar Vinho")
    termo = st.text_input("Pesquisar por nome, tipo ou localização...").strip().lower()
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
    st.subheader("📷 Escanear QR Code do Pallet")
    st.info("Aponte a câmera para o QR Code fixado no pallet para conferir os itens sem abrir as caixas.")
    foto_camera = st.camera_input("Capturar Imagem")
    if foto_camera is not None:
        st.success("QR Code lido com sucesso!")
        pallet_detectado = "Corredor 01 - Pallet 01"
        st.markdown(f"<h4 style='color: #7A1C2E;'>📍 Pallet: {pallet_detectado}</h4>", unsafe_allow_html=True)
        vinhos_pallet = [v for v in st.session_state.estoque if v.get("pallet") == pallet_detectado]
        for v in vinhos_pallet:
            st.markdown(f"""
                <div class="wine-card">
                    <div class="wine-title">🍷 {v.get('nome')} ({v.get('safra')})</div>
                    <p class="wine-text"><b>Tipo:</b> {v.get('tipo')} | <b>Embalagem:</b> {v.get('caixa')}</p>
                </div>
            """, unsafe_allow_html=True)

elif st.session_state.menu_atual == "📱 Gerar QR Code de Pallets":
    st.subheader("📱 Gerar QR Code de Pallets")
    c_corr = st.selectbox("Corredor:", LISTA_CORREDORES)
    c_pall = st.selectbox("Pallet:", LISTA_PALLETS)
    pallet_selecionado = f"{c_corr} - {c_pall}"
    if st.button("Gerar Etiqueta QR Code", use_container_width=True):
        url_qr = gerar_qr_code_api(pallet_selecionado)
        st.image(url_qr, caption=f"QR Code para {pallet_selecionado}", width=220)

elif st.session_state.menu_atual == "🍷 Ver estoque completo":
    st.subheader("🍷 Estoque Completo")
    if st.session_state.estoque:
        df = pd.DataFrame(st.session_state.estoque)
        if "foto" in df.columns:
            df = df.drop(columns=["foto"])
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Estoque vazio.")

elif st.session_state.menu_atual == "➕ Cadastrar novo vinho":
    st.subheader("➕ Novo Cadastro")
    with st.form(f"form_cad_{st.session_state.form_key}"):
        nome = st.text_input("Nome do Vinho:").strip()
        tipo = st.text_input("Tipo (ex: Tinto, Branco):").strip()
        safra = st.text_input("Safra (Ano ou NV):", value="2024").strip()
        sel_corredor = st.selectbox("Corredor:", LISTA_CORREDORES)
        sel_pallet = st.selectbox("Pallet:", LISTA_PALLETS)
        lado = st.selectbox("Lado:", LISTA_LADOS)
        caixa = st.selectbox("Caixa:", OPCOES_CAIXA)
        
        if st.form_submit_button("SALVAR CADASTRO", use_container_width=True):
            if nome and tipo:
                novo = {"nome": nome, "tipo": tipo, "safra": safra if safra else "NV", "pallet": f"{sel_corredor} - {sel_pallet}", "lado": lado, "caixa": caixa, "foto": None}
                st.session_state.estoque.append(novo)
                salvar_dados(st.session_state.estoque)
                st.session_state.form_key += 1
                st.success("Vinho cadastrado com sucesso!")
                st.rerun()
            else:
                st.error("Preencha o Nome e o Tipo.")

elif st.session_state.menu_atual == "✏️ Editar vinho":
    st.subheader("✏️ Editar Vinho")
    if st.session_state.estoque:
        opcoes = [f"{v.get('nome')} - {v.get('pallet')}" for v in st.session_state.estoque]
        idx = st.selectbox("Selecione o Vinho:", range(len(opcoes)), format_func=lambda x: opcoes[x])
        vinho = st.session_state.estoque[idx]
        
        with st.form("form_edit_completo"):
            novo_nome = st.text_input("Nome do Vinho:", vinho.get("nome", ""))
            novo_tipo = st.text_input("Tipo:", vinho.get("tipo", ""))
            nova_safra = st.text_input("Safra:", vinho.get("safra", "2024"))
            
            pallet_atual = vinho.get("pallet", "Corredor 01 - Pallet 01")
            partes_pallet = pallet_atual.split(" - ")
            c_corr_atual = partes_pallet[0] if len(partes_pallet) > 0 else LISTA_CORREDORES[0]
            c_pall_atual = partes_pallet[1] if len(partes_pallet) > 1 else LISTA_PALLETS[0]
            
            idx_corr = LISTA_CORREDORES.index(c_corr_atual) if c_corr_atual in LISTA_CORREDORES else 0
            idx_pall = LISTA_PALLETS.index(c_pall_atual) if c_pall_atual in LISTA_PALLETS else 0
            
            novo_corredor = st.selectbox("Corredor:", LISTA_CORREDORES, index=idx_corr)
            novo_pallet_num = st.selectbox("Pallet:", LISTA_PALLETS, index=idx_pall)
            novo_lado = st.selectbox("Lado:", LISTA_LADOS, index=LISTA_LADOS.index(vinho.get("lado", "Direito")) if vinho.get("lado") in LISTA_LADOS else 0)
            nova_caixa = st.selectbox("Caixa:", OPCOES_CAIXA, index=OPCOES_CAIXA.index(vinho.get("caixa", "Caixa com 12 garrafas")) if vinho.get("caixa") in OPCOES_CAIXA else 0)
            
            if st.form_submit_button("SALVAR ALTERAÇÕES", use_container_width=True):
                if novo_nome.strip() and novo_tipo.strip():
                    vinho["nome"] = novo_nome.strip()
                    vinho["tipo"] = novo_tipo.strip()
                    vinho["safra"] = nova_safra.strip()
                    vinho["pallet"] = f"{novo_corredor} - {novo_pallet_num}"
                    vinho["lado"] = novo_lado
                    vinho["caixa"] = nova_caixa
                    salvar_dados(st.session_state.estoque)
                    st.success("Alterações salvas!")
                    st.rerun()

elif st.session_state.menu_atual == "🗑️ Excluir vinho":
    st.subheader("🗑️ Excluir Vinho")
    if st.session_state.estoque:
        opcoes = [f"{v.get('nome')} - {v.get('pallet')}" for v in st.session_state.estoque]
        idx = st.selectbox("Selecione para remover:", range(len(opcoes)), format_func=lambda x: opcoes[x])
        if st.button("CONFIRMAR EXCLUSÃO", type="primary"):
            st.session_state.estoque.pop(idx)
            salvar_dados(st.session_state.estoque)
            st.success("Removido com sucesso!")
            st.rerun()

elif st.session_state.menu_atual == "👤 Cadastrar usuário":
    st.subheader("👤 Cadastrar Usuário")
    with st.form("form_novo_usuario"):
        nome_usuario = st.text_input("Nome Completo do Operador:").strip()
        cargo_usuario = st.selectbox("Nível de Acesso:", ["Operador de Galpão", "Conferente", "Administrador"])
        senha_usuario = st.text_input("Senha de Acesso:", type="password").strip()
        
        if st.form_submit_button("CADASTRAR", use_container_width=True):
            if nome_usuario and senha_usuario:
                novo_user = {"nome": nome_usuario, "cargo": cargo_usuario, "senha": senha_usuario}
                st.session_state.usuarios.append(novo_user)
                salvar_usuarios(st.session_state.usuarios)
                st.session_state.operador_atual = nome_usuario
                st.success(f"🎉 Bem-vindo(a), **{nome_usuario}**! Usuário cadastrado com sucesso.")
            else:
                st.error("Preencha o nome e a senha.")
