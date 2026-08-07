import base64
import io
import json
import os
import urllib.parse
import pandas as pd
import streamlit as st
from PIL import Image

# Importações seguras para processamento de imagem e decodificação de QR Code
try:
    import cv2
    import numpy as np

    OPENCV_DISPONIVEL = True
except ImportError:
    OPENCV_DISPONIVEL = False

try:
    from pyzbar.pyzbar import decode as pyzbar_decode

    PYZBAR_DISPONIVEL = True
except ImportError:
    PYZBAR_DISPONIVEL = False

# 1. Configuração da página Streamlit
st.set_page_config(
    page_title="Wine Map Pro - Galpão Premium",
    page_icon="🍷",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# 2. Estilização CSS Personalizada (Tema Wine Map Pro - Dark & Gold)
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
    .wine-card {
        background-color: #1E1E1E;
        border-radius: 16px;
        padding: 16px;
        margin-bottom: 15px;
        border: 1px solid #2D2D2D;
        box-shadow: 0px 4px 12px rgba(0, 0, 0, 0.3);
    }
    .wine-title {
        color: #C9A227;
        font-size: 1.2rem;
        font-weight: 700;
        margin-bottom: 6px;
    }
    .badge-pallet {
        background-color: #581825;
        color: #FFFFFF;
        padding: 4px 10px;
        border-radius: 8px;
        font-weight: 600;
        font-size: 0.8rem;
        display: inline-block;
    }
    .badge-info {
        background-color: #2D2D2D;
        color: #E2E8F0;
        padding: 4px 8px;
        border-radius: 8px;
        font-size: 0.8rem;
        margin-left: 4px;
        display: inline-block;
    }
    /* Estilização de Inputs e Botões para combinar com o layout */
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
    @media print {
        .sidebar, .stButton, header, footer, .stSelectbox {
            display: none !important;
        }
    }
    </style>
""",
    unsafe_allow_html=True,
)

# --- CONFIGURAÇÕES DO GALPÃO ---
SENHA_ACESSO = "1980"
NOME_ARQUIVO = "estoque_galpao_pro.json"
URL_APLICATIVO = (
    "https://mapa-estoque-galpao-premium-vbewrgwbe5ktw8ptefwxmf.streamlit.app"
)

# DADOS DO DESENVOLVEDOR
NOME_DEV = "Vagner Souza"
TITULO_DEV = "Cientista da Computação"
FONE_DEV = "(31) 98968-4010"

LISTA_CORREDORES = [f"Corredor {i:02d}" for i in range(1, 26)]
LISTA_PALLETS = [f"Pallet {i:02d}" for i in range(1, 26)]
LISTA_LADOS = ["Direito", "Esquerdo", "Centro / Único"]

ANOS_SAFRA = [str(ano) for ano in range(2026, 1989, -1)]
OPCOES_SAFRA = ["Sem Safra (NV)", "Outra / Mais antiga"] + ANOS_SAFRA

OPCOES_CAIXA = [
    "Caixa com 12 garrafas",
    "Caixa com 6 garrafas",
    "Caixa com 3 garrafas",
    "Garrafa Avulsa (1 un)",
    "Outra quantidade",
]

OPCOES_PAIS = ["França", "Brasil", "Argentina", "Portugal", "Itália", "Espanha", "Chile", "Outros"]

estoque_padrao = [{
    "nome": "Château Margaux",
    "vinicola": "Château Margaux",
    "pais": "França",
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


def converter_imagem_base64(uploaded_file):
    if uploaded_file is not None:
        bytes_data = uploaded_file.getvalue()
        return base64.b64encode(bytes_data).decode("utf-8")
    return None


def calcular_hash_simples(img):
    img = img.convert("L").resize((8, 8), Image.Resampling.LANCZOS)
    pixels = list(img.getdata())
    media = sum(pixels) / len(pixels)
    return "".join(["1" if p > media else "0" for p in pixels])


def comparar_hashes(h1, h2):
    return sum(c1 != c2 for c1, c2 in zip(h1, h2))


# --- ESTADO DE SESSÃO ---
if "estoque" not in st.session_state:
    st.session_state.estoque = carregar_dados()

if "form_key" not in st.session_state:
    st.session_state.form_key = 0

query_params = st.query_params
auth_param = query_params.get("auth")
pallet_param = query_params.get("pallet")

if auth_param == SENHA_ACESSO:
    st.session_state.autenticado = True

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

# --- TELA DE LOGIN ---
if not st.session_state.autenticado:
    st.markdown(
        """
            <div class="header-container">
                <h1 class="main-title">🍷 WINE MAP PRO</h1>
                <p class="sub-title">Acesse sua conta para continuar</p>
            </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("login_form"):
        senha_digitada = st.text_input("🔑 Senha de Acesso:", type="password")
        btn_login = st.form_submit_button(
            "ENTRAR", use_container_width=True
        )

        if btn_login:
            if senha_digitada == SENHA_ACESSO:
                st.session_state.autenticado = True
                st.query_params["auth"] = SENHA_ACESSO
                st.success("Acesso Autorizado!")
                st.rerun()
            else:
                st.error("Senha incorreta!")
    st.stop()

# --- CONSULTA DIRETA VIA LINK DE QR CODE ---
if pallet_param:
    pallet_nome = urllib.parse.unquote_plus(pallet_param)
    st.markdown(
        f"""
    <div class="header-container">
        <h1 class="main-title">📍 DETALHES DO PALLET</h1>
        <p class="sub-title">Consultando: <b>{pallet_nome}</b></p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    vinhos_no_pallet = [
        v for v in st.session_state.estoque if v.get("pallet") == pallet_nome
    ]

    if vinhos_no_pallet:
        st.success(f"📦 Encontrado(s) {len(vinhos_no_pallet)} vinho(s) nesta posição:")
        for v in vinhos_no_pallet:
            c1, c2 = st.columns([3, 1])
            with c1:
                st.markdown(
                    f"""
                    <div class="wine-card">
                        <div class="wine-title">🍷 {v.get('nome')} ({v.get('safra')})</div>
                        <p><span class="badge-pallet">📍 {v.get('pallet')}</span> <span class="badge-info">Lado: {v.get('lado')}</span></p>
                        <p style="margin-top:8px; font-size:0.9rem; color: #CCC;"><b>Tipo:</b> {v.get('tipo')} | <b>País:</b> {v.get('pais', 'N/D')} | <b>Embalagem:</b> {v.get('caixa')}</p>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with c2:
                if v.get("foto"):
                    st.image(base64.b64decode(v.get("foto")), caption="Rótulo", width=90)
    else:
        st.warning(f"⚠️ Nenhum vinho cadastrado no **{pallet_nome}** até o momento.")

    if st.button("⬅️ Voltar ao Painel Principal", use_container_width=True):
        st.query_params.clear()
        st.query_params["auth"] = SENHA_ACESSO
        st.rerun()

    st.stop()

# --- MENU LATERAL ---
with st.sidebar:
    st.markdown(
        "<h2 style='color:#C9A227;'>🍷 Wine Map Pro</h2>", unsafe_allow_html=True
    )

    menu = st.radio(
        "Menu Principal:",
        [
            "🏠 Home / Dashboard",
            "🔍 Buscar vinho",
            "🍷 Ver estoque completo",
            "➕ Cadastrar novo vinho",
            "✏️ Editar vinho",
            "🗑️ Excluir vinho",
            "📥 Importar planilha (CSV/Excel)",
            "📤 Exportar planilha (CSV/Excel)",
        ],
    )
    st.markdown("---")

    if st.button("🔒 Sair do Sistema", use_container_width=True):
        st.session_state.autenticado = False
        st.query_params.clear()
        st.rerun()

    st.markdown(
        f"""
            <div style="
                background: linear-gradient(135deg, #581825 0%, #1E1E1E 100%);
                padding: 14px;
                border-radius: 12px;
                color: white;
                text-align: center;
                margin-top: 15px;
                box-shadow: 0 4px 10px rgba(0,0,0,0.3);
                border: 1px solid #333;
            ">
                <p style="margin: 0; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 1px; color: #C9A227;">
                    Desenvolvimento & Arq.
                </p>
                <h4 style="margin: 4px 0 2px 0; color: #FFFFFF; font-size: 1.05rem; font-weight: 700;">
                    {NOME_DEV}
                </h4>
                <p style="margin: 0 0 8px 0; font-size: 0.78rem; color: #E2E8F0; font-weight: 500;">
                    🎓 {TITULO_DEV}
                </p>
                <div style="border-top: 1px solid rgba(255,255,255,0.2); padding-top: 6px; margin-top: 6px;">
                    <p style="margin: 0; font-size: 0.78rem; color: #FFD700; font-weight: bold;">
                        📞 {FONE_DEV}
                    </p>
                </div>
            </div>
        """,
        unsafe_allow_html=True,
    )

# --- TELA HOME / DASHBOARD ---
if menu == "🏠 Home / Dashboard":
    st.markdown(
        """
        <div class="header-container">
            <h1 class="main-title">WINE MAP PRO</h1>
            <p class="sub-title">Painel de Controle em Tempo Real</p>
        </div>
    """,
        unsafe_allow_html=True,
    )

    total_vinhos = len(st.session_state.estoque)
    total_pallets = len(set(v.get("pallet") for v in st.session_state.estoque))

    col1, col2 = st.columns(2)
    with col1:
        st.metric(label="🍾 Vinhos Cadastrados", value=total_vinhos)
    with col2:
        st.metric(label="📦 Pallets Ocupados", value=total_pallets)

    st.markdown("---")
    st.subheader("🚀 Ações Rápidas")
    
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("➕ Novo Cadastro", use_container_width=True):
            st.rerun()
    with c2:
        if st.button("🔍 Buscar Vinho", use_container_width=True):
            st.rerun()
    with c3:
        if st.button("📋 Ver Estoque", use_container_width=True):
            st.rerun()

# --- BUSCAR VINHO ---
elif menu == "🔍 Buscar vinho":
    st.subheader("🔍 Localizar Vinho no Galpão")

    aba_texto, aba_foto = st.tabs(
        ["🔎 Buscar por Texto", "📸 Buscar por Foto do Rótulo"]
    )

    with aba_texto:
        c_tipo, c_busca = st.columns([1, 2])
        with c_tipo:
            sub_op = st.selectbox(
                "Filtrar por:",
                ["Por Nome", "Por Tipo", "Por Safra", "Por País", "Por Pallet"],
            )
        with c_busca:
            termo = st.text_input("Digite o termo de busca:").strip().lower()

        if termo:
            resultados = [
                v for v in st.session_state.estoque
                if termo in str(v.get(sub_op.split()[-1].lower(), "")).lower()
                or termo in str(v.get("nome", "")).lower()
            ]
            if not resultados:
                st.warning("⚠️ Nenhum vinho encontrado.")
            else:
                for v in resultados:
                    c1, c2 = st.columns([3, 1])
                    with c1:
                        st.markdown(
                            f"""
                            <div class="wine-card">
                                <div class="wine-title">🍷 {v.get('nome')} ({v.get('safra')})</div>
                                <p><span class="badge-pallet">📍 {v.get('pallet')}</span> <span class="badge-info">Lado: {v.get('lado')}</span></p>
                                <p style="margin-top:8px; font-size:0.9rem; color: #CCC;"><b>Tipo:</b> {v.get('tipo')} | <b>País:</b> {v.get('pais', 'N/D')} | <b>Caixa:</b> {v.get('caixa')}</p>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                    with c2:
                        if v.get("foto"):
                            st.image(base64.b64decode(v.get("foto")), caption="Rótulo", width=90)

    with aba_foto:
        st.write("Envie a foto do rótulo para correspondência visual:")
        foto_pesquisa = st.file_uploader(
            "Selecione a foto da garrafa:", type=["jpg", "jpeg", "png"]
        )

        if foto_pesquisa is not None:
            try:
                img_pesquisa = Image.open(foto_pesquisa)
                st.image(img_pesquisa, caption="Foto para Busca", width=150)
                hash_pesquisa = calcular_hash_simples(img_pesquisa)
                encontrados = []

                for item in st.session_state.estoque:
                    if item.get("foto"):
                        try:
                            bytes_banco = base64.b64decode(item["foto"])
                            img_banco = Image.open(io.BytesIO(bytes_banco))
                            hash_banco = calcular_hash_simples(img_banco)
                            dif = comparar_hashes(hash_pesquisa, hash_banco)
                            if dif <= 18:
                                encontrados.append((dif, item))
                        except Exception:
                            pass

                encontrados.sort(key=lambda x: x[0])
                st.markdown("---")
                if encontrados:
                    st.success(f"🎯 Encontrado(s) {len(encontrados)} resultado(s) parecido(s):")
                    for diff, v in encontrados:
                        c1, c2 = st.columns([3, 1])
                        with c1:
                            st.markdown(
                                f"""
                                <div class="wine-card">
                                    <div class="wine-title">🍷 {v.get('nome')}</div>
                                    <p><span class="badge-pallet">📍 {v.get('pallet')}</span> <span class="badge-info">Lado: {v.get('lado')}</span></p>
                                    <p style="margin-top:8px; font-size:0.9rem; color: #CCC;"><b>Safra:</b> {v.get('safra')} | <b>País:</b> {v.get('pais', 'N/D')}</p>
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )
                        with c2:
                            if v.get("foto"):
                                st.image(base64.b64decode(v.get("foto")), caption="Banco", width=90)
                else:
                    st.warning("⚠️ Nenhum vinho similar encontrado.")
            except Exception as e:
                st.error(f"Erro ao processar foto: {e}")

# --- ESTOQUE COMPLETO ---
elif menu == "🍷 Ver estoque completo":
    st.subheader("📋 Estoque Completo - Wine Map Pro")
    if st.session_state.estoque:
        df = pd.DataFrame(st.session_state.estoque)
        if "foto" in df.columns:
            df = df.drop(columns=["foto"])
        st.dataframe(df, use_container_width=True)

# --- CADASTRAR NOVO VINHO ---
elif menu == "➕ Cadastrar novo vinho":
    st.subheader("➕ Novo Cadastro de Vinho")

    with st.form(f"form_cadastrar_{st.session_state.form_key}"):
        nome = st.text_input("Nome do Vinho:").strip()
        
        c_vin, c_pai = st.columns(2)
        with c_vin:
            vinicola = st.text_input("Vinícola:").strip()
        with c_pai:
            pais = st.selectbox("País:", OPCOES_PAIS)

        c_tipo, c_safra = st.columns(2)
        with c_tipo:
            tipo = st.text_input("Tipo (ex: Tinto, Branco, Espumante):").strip()
        with c_safra:
            safra = st.selectbox("📅 Safra:", OPCOES_SAFRA)

        c_corr, c_pal, c_lad = st.columns(3)
        with c_corr:
            sel_corredor = st.selectbox("🛣️ Corredor:", LISTA_CORREDORES)
        with c_pal:
            sel_pallet = st.selectbox("📦 Pallet:", LISTA_PALLETS)
        with c_lad:
            lado = st.selectbox("↔️ Lado:", LISTA_LADOS)

        c_cx, c_vol = st.columns(2)
        with c_cx:
            caixa = st.selectbox("📦 Caixa / Quantidade:", OPCOES_CAIXA)
        with c_vol:
            volume = st.selectbox("🧪 Volume:", ["750ml", "375ml", "1500ml"])

        foto_upload = st.file_uploader(
            "📸 Adicionar foto do rótulo:", type=["jpg", "jpeg", "png"]
        )

        btn_salvar = st.form_submit_button(
            "SALVAR", use_container_width=True
        )

        if btn_salvar:
            pallet_final = f"{sel_corredor} - {sel_pallet}"
            if nome and tipo:
                foto_b64 = converter_imagem_base64(foto_upload)
                novo_vinho = {
                    "nome": nome,
                    "vinicola": vinicola,
                    "pais": pais,
                    "tipo": tipo,
                    "safra": safra,
                    "pallet": pallet_final,
                    "lado": lado,
                    "caixa": caixa,
                    "volume": volume,
                    "foto": foto_b64,
                }
                st.session_state.estoque.append(novo_vinho)
                salvar_dados(st.session_state.estoque)
                st.session_state.form_key += 1
                st.success(f"✅ '{nome}' cadastrado com sucesso!")
                st.rerun()
            else:
                st.error("⚠️ Preencha pelo menos o Nome e o Tipo.")

# --- EDITAR VINHO ---
elif menu == "✏️ Editar vinho":
    st.subheader("✏️ Alterar Cadastro")
    if st.session_state.estoque:
        opcoes = [
            f"{i + 1}. {v.get('nome')} - {v.get('pallet')}"
            for i, v in enumerate(st.session_state.estoque)
        ]
        idx = st.selectbox(
            "Selecione:", range(len(opcoes)), format_func=lambda x: opcoes[x]
        )
        vinho = st.session_state.estoque[idx]

        with st.form("form_edit"):
            novo_nome = st.text_input("Nome:", vinho.get("nome"))
            novo_pallet = st.text_input("Pallet:", vinho.get("pallet"))
            nova_caixa = st.selectbox("Caixa:", OPCOES_CAIXA)
            foto_nova = st.file_uploader("Atualizar Foto:", type=["jpg", "jpeg", "png"])

            if st.form_submit_button("💾 Salvar Alterações"):
                vinho["nome"] = novo_nome
                vinho["pallet"] = novo_pallet
                vinho["caixa"] = nova_caixa
                if foto_nova is not None:
                    vinho["foto"] = converter_imagem_base64(foto_nova)
                salvar_dados(st.session_state.estoque)
                st.success("Atualizado com sucesso!")
                st.rerun()

# --- EXCLUIR VINHO ---
elif menu == "🗑️ Excluir vinho":
    st.subheader("🗑️ Remover do Estoque")
    if st.session_state.estoque:
        opcoes = [
            f"{v.get('nome')} - {v.get('pallet')}"
            for v in st.session_state.estoque
        ]
        idx = st.selectbox(
            "Escolha para apagar:",
            range(len(opcoes)),
            format_func=lambda x: opcoes[x],
        )
        if st.button("❌ Apagar Registro", type="primary"):
            st.session_state.estoque.pop(idx)
            salvar_dados(st.session_state.estoque)
            st.success("Removido com sucesso!")
            st.rerun()

# --- IMPORTAR PLANILHA ---
elif menu == "📥 Importar planilha (CSV/Excel)":
    st.subheader("📥 Carga em Lote por Planilha")
    arquivo_planilha = st.file_uploader("Escolha o arquivo CSV ou Excel:", type=["csv", "xlsx"])
    substituir = st.checkbox("⚠️ Apagar o estoque atual e substituir por este arquivo.")

    if arquivo_planilha is not None:
        try:
            if arquivo_planilha.name.endswith(".csv"):
                df_import = pd.read_csv(arquivo_planilha)
            else:
                df_import = pd.read_excel(arquivo_planilha)

            st.dataframe(df_import.head(10), use_container_width=True)

            if st.button("🚀 Confirmar Importação", use_container_width=True):
                novos_itens = df_import.to_dict(orient="records")
                if substituir:
                    st.session_state.estoque = novos_itens
                else:
                    st.session_state.estoque.extend(novos_itens)
                salvar_dados(st.session_state.estoque)
                st.success("Dados importados com sucesso!")
                st.rerun()
        except Exception as e:
            st.error(f"Erro ao ler arquivo: {e}")

# --- EXPORTAR PLANILHA ---
elif menu == "📤 Exportar planilha (CSV/Excel)":
    st.subheader("📤 Baixar Dados do Estoque")
    if st.session_state.estoque:
        df_exp = pd.DataFrame(st.session_state.estoque)
        if "foto" in df_exp.columns:
            df_exp = df_exp.drop(columns=["foto"])
        
        csv_data = df_exp.to_csv(index=False, encoding="utf-8-sig")
        st.download_button(
            label="📥 Baixar arquivo CSV",
            data=csv_data,
            file_name="estoque_wine_map_pro.csv",
            mime="text/csv",
            use_container_width=True
        )
