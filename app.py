import os
import re
import json
import shutil
import html
import unicodedata
from datetime import datetime, timezone, timedelta
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# ============================================================
# DEPENDÊNCIAS OPCIONAIS
# ============================================================

try:
    import cv2
    import numpy as np
    OPENCV_DISPONIVEL = True
except ImportError:
    OPENCV_DISPONIVEL = False

try:
    import qrcode
    QRCODE_DISPONIVEL = True
except ImportError:
    QRCODE_DISPONIVEL = False


# ============================================================
# CONFIGURAÇÃO
# ============================================================

st.set_page_config(
    page_title="Premium Wines - Galpão",
    page_icon="🍷",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root {
        --wine-bg: #0D0D0F;
        --wine-panel: #151518;
        --wine-panel-2: #1B1B1F;
        --wine-border: #2A2A30;
        --wine-burgundy: #6E1730;
        --wine-burgundy-2: #3E0D1A;
        --wine-gold: #D6AE63;
        --wine-text: #F7F3EE;
        --wine-muted: #A9A4A0;
        --wine-success: #66C38A;
        --wine-danger: #E06D73;
    }

    html, body, [class*="css"] { font-family: Inter, "Segoe UI", sans-serif; }
    .stApp {
        background:
            radial-gradient(circle at 88% 8%, rgba(110,23,48,.22), transparent 30%),
            linear-gradient(135deg, #0B0B0D 0%, #111114 55%, #0B0B0D 100%);
        color: var(--wine-text);
        overscroll-behavior-y: none;
    }

    .block-container { max-width: 1500px; padding-top: 1.3rem; padding-bottom: 3rem; }
    footer, #MainMenu, [data-testid="stStatusWidget"] { visibility: hidden; }

    /* SIDEBAR */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #111114 0%, #181014 100%);
        border-right: 1px solid #2B2226;
    }
    [data-testid="stSidebar"] > div:first-child { padding-top: 1rem; }
    .sidebar-brand {
        padding: 10px 8px 18px 8px;
        border-bottom: 1px solid #30272B;
        margin-bottom: 12px;
    }
    .sidebar-brand .brand-title { color: #F8F2EA; font-weight: 850; font-size: 1.05rem; letter-spacing: .08em; }
    .sidebar-brand .brand-sub { color: var(--wine-gold); font-size: .72rem; letter-spacing: .18em; margin-top: 3px; }
    .sidebar-section { color:#847B76; font-size:.68rem; font-weight:800; letter-spacing:.13em; margin:18px 6px 7px; text-transform:uppercase; }
    [data-testid="stSidebar"] .stButton > button {
        background: transparent !important;
        border: 1px solid transparent !important;
        color: #C8C0BC !important;
        text-align: left !important;
        justify-content: flex-start !important;
        padding: .62rem .75rem !important;
        border-radius: 10px !important;
        box-shadow: none !important;
        min-height: 42px;
    }
    [data-testid="stSidebar"] .stButton > button:hover {
        background: rgba(110,23,48,.22) !important;
        border-color: rgba(214,174,99,.22) !important;
        color: #FFF !important;
    }

    /* TÍTULOS E TEXTOS */
    h1, h2, h3, h4 { color: var(--wine-text) !important; }
    p, .stMarkdown, [data-testid="stCaptionContainer"] { color: #D9D2CD; }
    label { color: #D7CFC9 !important; font-weight: 700 !important; font-size: .9rem !important; }
    hr { border-color: #2B2B31 !important; }

    /* INPUTS */
    [data-baseweb="input"] > div, [data-baseweb="select"] > div,
    [data-baseweb="textarea"] > div, .stTextInput input, .stNumberInput input,
    .stTextArea textarea {
        background: #17171B !important;
        color: #F7F3EE !important;
        border-color: #35353C !important;
        border-radius: 10px !important;
    }
    input, textarea { color: #F7F3EE !important; }
    [data-baseweb="select"] span { color: #F7F3EE !important; }

    /* BOTÕES */
    .stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {
        background: linear-gradient(135deg, #751A35, #541125) !important;
        color: #FFF !important;
        border-radius: 11px !important;
        font-weight: 750 !important;
        border: 1px solid #8C2944 !important;
        padding: .68rem 1rem !important;
        width: 100%;
        box-shadow: 0 8px 22px rgba(59,10,26,.18);
        transition: all .18s ease;
    }
    .stButton > button:hover, .stDownloadButton > button:hover, .stFormSubmitButton > button:hover {
        transform: translateY(-1px);
        border-color: var(--wine-gold) !important;
        box-shadow: 0 10px 28px rgba(0,0,0,.25);
    }

    /* CARDS E COMPONENTES */
    .wine-card, .qr-card, .wine-item {
        background: linear-gradient(180deg, #19191D, #141417);
        color: #F4EFEA;
        border-radius: 14px;
        border: 1px solid #2D2D33;
        box-shadow: 0 10px 28px rgba(0,0,0,.18);
    }
    .wine-card { padding: 17px; margin-bottom: 12px; }
    .qr-card { padding: 20px; margin-bottom: 15px; text-align:center; }
    .wine-item { padding: 13px; margin-bottom:8px; border-left: 4px solid var(--wine-gold); }
    .wine-title { color: var(--wine-gold); font-size:1.08rem; font-weight:800; }
    .pallet-header {
        background: linear-gradient(135deg, #6E1730, #340B17);
        color: white;
        border: 1px solid #8A2943;
        border-radius: 15px;
        padding: 18px;
        margin-bottom: 15px;
        box-shadow: 0 12px 30px rgba(49,8,20,.25);
    }
    [data-testid="stMetric"] {
        background: linear-gradient(180deg, #18181C, #121215);
        border: 1px solid #2B2B31;
        border-radius: 14px;
        padding: 14px 16px;
    }
    [data-testid="stMetricValue"] { color: var(--wine-gold) !important; font-weight: 850; }
    [data-testid="stMetricLabel"] { color: #BEB5B0 !important; }

    /* ALERTAS */
    [data-testid="stAlert"] { border-radius: 12px; background: #18181C; border: 1px solid #33333A; }

    /* TABS */
    [data-baseweb="tab-list"] { gap: 8px; background: transparent; }
    [data-baseweb="tab"] { background:#17171B; border-radius:10px; color:#CFC7C2; padding:.6rem .9rem; }
    [aria-selected="true"][data-baseweb="tab"] { background:#6E1730 !important; color:white !important; }

    /* DATAFRAME */
    [data-testid="stDataFrame"] { border:1px solid #2D2D33; border-radius:12px; overflow:hidden; }

    /* LOGIN */
    .login-shell { max-width: 470px; margin: 2.2rem auto 1rem auto; text-align:center; }
    .login-logo {
        width: 78px; height: 78px; border-radius: 24px; margin: 0 auto 14px;
        display:flex; align-items:center; justify-content:center;
        background: radial-gradient(circle at 30% 30%, #8C2944, #4B0D1D 70%);
        border: 1px solid rgba(214,174,99,.45); color:#FFF; font-size:2.2rem;
        box-shadow:0 18px 44px rgba(64,10,27,.35);
    }
    .login-title { font-size: 1.85rem; font-weight: 900; letter-spacing:.04em; color:#F8F2EA; }
    .login-title span { color: var(--wine-gold); }
    .login-subtitle { color:#AFA7A2; margin-top:5px; margin-bottom:18px; }
    .login-card {
        background: linear-gradient(180deg, rgba(26,26,30,.97), rgba(18,18,21,.97));
        border: 1px solid #302D31; border-radius:18px; padding:20px 22px 10px;
        box-shadow: 0 24px 70px rgba(0,0,0,.35);
    }

    /* TOPBAR */
    .topbar {
        display:flex; align-items:center; justify-content:space-between; gap:16px;
        background: linear-gradient(90deg, rgba(25,25,29,.94), rgba(21,17,20,.94));
        border:1px solid #2D292C; border-radius:15px; padding:12px 16px; margin-bottom:18px;
    }
    .topbar-brand { font-weight:900; letter-spacing:.06em; color:#F8F2EA; }
    .topbar-brand span { color:var(--wine-gold); }
    .topbar-user { color:#B9B0AB; font-size:.84rem; text-align:right; }

    /* HOME */
    .hero-wine {
        position:relative; overflow:hidden; border-radius:20px; padding:34px 36px; margin-bottom:18px;
        background:
          radial-gradient(circle at 82% 50%, rgba(214,174,99,.12), transparent 22%),
          radial-gradient(circle at 72% 45%, rgba(119,23,49,.55), transparent 35%),
          linear-gradient(120deg, #191317 0%, #251119 55%, #111114 100%);
        border:1px solid #3A2830; min-height:190px;
        box-shadow: 0 18px 50px rgba(0,0,0,.25);
    }
    .hero-wine:after {
        content:"🍷"; position:absolute; right:6%; top:8%; font-size:8.5rem; opacity:.18;
        filter: drop-shadow(0 10px 18px rgba(0,0,0,.45)); transform: rotate(5deg);
    }
    .hero-kicker { color:var(--wine-gold); text-transform:uppercase; letter-spacing:.16em; font-size:.74rem; font-weight:850; }
    .hero-title { color:#FFF; font-size:2rem; font-weight:900; margin:.45rem 0 .35rem; max-width:760px; }
    .hero-sub { color:#C1B7B1; font-size:.94rem; max-width:720px; }
    .section-title { margin:22px 0 10px; color:#9A918C; font-size:.72rem; font-weight:850; letter-spacing:.14em; text-transform:uppercase; }
    .action-card {
        min-height:112px; padding:16px; border-radius:15px;
        background:linear-gradient(180deg,#19191D,#131316); border:1px solid #2D2D33;
        box-shadow:0 10px 24px rgba(0,0,0,.16); margin-bottom:6px;
    }
    .action-icon { font-size:1.45rem; margin-bottom:7px; }
    .action-title { color:#F5EFEA; font-size:.98rem; font-weight:800; }
    .action-desc { color:#918983; font-size:.77rem; margin-top:3px; line-height:1.35; }


    /* ========================================================
       TELAS INTERNAS — MESMA IDENTIDADE PREMIUM DA HOME
       ======================================================== */
    .page-hero {
        position:relative; overflow:hidden; border-radius:18px; padding:22px 24px;
        margin:2px 0 18px; background:
          radial-gradient(circle at 90% 20%, rgba(214,174,99,.10), transparent 25%),
          linear-gradient(125deg, #201218 0%, #17171B 62%, #111114 100%);
        border:1px solid #3B2830; box-shadow:0 16px 38px rgba(0,0,0,.22);
    }
    .page-hero:after { content:"🍷"; position:absolute; right:24px; top:8px; font-size:4.5rem; opacity:.08; }
    .page-kicker { color:var(--wine-gold); text-transform:uppercase; letter-spacing:.15em; font-size:.68rem; font-weight:850; }
    .page-title { color:#FFF; font-size:1.45rem; font-weight:900; margin-top:6px; line-height:1.2; }
    .page-desc { color:#AFA6A0; font-size:.86rem; margin-top:6px; max-width:900px; line-height:1.45; }

    /* formulários e blocos */
    [data-testid="stForm"] {
        background:linear-gradient(180deg, rgba(25,25,29,.98), rgba(18,18,21,.98));
        border:1px solid #302D33; border-radius:16px; padding:18px;
        box-shadow:0 12px 30px rgba(0,0,0,.14);
    }
    [data-testid="stExpander"] {
        background:linear-gradient(180deg,#19191D,#141417); border:1px solid #2E2E34 !important;
        border-radius:13px !important; overflow:hidden; box-shadow:0 8px 22px rgba(0,0,0,.10);
    }
    [data-testid="stExpander"] summary { color:#F3ECE7 !important; font-weight:760 !important; }
    [data-testid="stFileUploader"] section {
        background:#151519 !important; border:1px dashed #56424A !important; border-radius:13px !important;
    }
    [data-testid="stFileUploader"] section:hover { border-color:var(--wine-gold) !important; }
    [data-testid="stFileUploader"] small, [data-testid="stFileUploader"] span { color:#BEB5B0 !important; }
    [data-testid="stCameraInput"] { background:#151519; border-radius:14px; padding:8px; border:1px solid #2E2E34; }

    /* rádios, toggles e checkboxes */
    [role="radiogroup"] { background:#141417; border:1px solid #29292F; border-radius:12px; padding:8px 10px; }
    [data-testid="stCheckbox"] label, [data-testid="stRadio"] label { color:#D8D0CB !important; }

    /* tabela/data editor */
    [data-testid="stDataFrame"], [data-testid="stDataEditor"] {
        background:#151519; border:1px solid #2E2E34 !important; border-radius:14px !important;
        box-shadow:0 10px 25px rgba(0,0,0,.12);
    }

    /* popovers/select dropdowns */
    [data-baseweb="popover"] > div, [role="listbox"] { background:#1B1B1F !important; color:#F7F3EE !important; }
    [role="option"] { color:#E8E0DB !important; }
    [role="option"]:hover { background:#35121E !important; }

    /* infos/avisos mais integrados ao tema */
    [data-testid="stNotification"] { background:#17171B !important; border-color:#34343A !important; }
    .premium-info {
        background:linear-gradient(135deg, rgba(110,23,48,.16), rgba(214,174,99,.05));
        border:1px solid #49313A; border-left:4px solid var(--wine-gold); border-radius:13px;
        padding:14px 16px; margin:10px 0 16px; color:#D8D0CB;
    }
    .premium-panel {
        background:linear-gradient(180deg,#19191D,#141417); border:1px solid #2E2E34;
        border-radius:15px; padding:17px; margin:10px 0 15px; box-shadow:0 10px 28px rgba(0,0,0,.14);
    }
    .premium-panel-title { color:var(--wine-gold); font-weight:850; font-size:1rem; margin-bottom:5px; }
    .premium-muted { color:#9F9792; font-size:.82rem; }

    /* títulos Streamlit internos */
    .stMarkdown h3 { color:#F4EFEA !important; font-size:1.08rem !important; margin-top:1rem !important; }
    .stMarkdown h4 { color:var(--wine-gold) !important; }

    /* links */
    a { color:var(--wine-gold) !important; }

    @media (max-width: 800px) {
        .page-hero { padding:18px 16px; }
        .page-title { font-size:1.2rem; padding-right:38px; }
        .page-hero:after { font-size:3.2rem; right:10px; top:14px; }
    }

    @media (max-width: 800px) {
        .block-container { padding-left: .8rem; padding-right:.8rem; padding-top:.8rem; }
        .hero-wine { padding:24px 20px; min-height:160px; }
        .hero-title { font-size:1.55rem; padding-right:50px; }
        .hero-wine:after { font-size:5rem; right:2%; top:18%; }
        .topbar-user { display:none; }
    }

    @media print {
        .no-print, [data-testid="stSidebar"] { display:none !important; }
        .stApp { background:white !important; color:black !important; }
        .qr-card { page-break-inside: avoid; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================
# ARQUIVOS
# ============================================================

NOME_ARQUIVO = "estoque_galpao_pro.json"
ARQUIVO_USUARIOS = "usuarios_galpao.json"
ARQUIVO_LOGS = "logs_auditoria.json"
ARQUIVO_PEDIDOS = "pedidos_matriz.json"
ARQUIVO_PALLETS = "pallets_galpao.json"

PASTA_BACKUP = "backups_estoque"
PASTA_FOTOS = "fotos_vinhos"
PASTA_QR = "qr_pallets"

SENHA_DEV = "1980"
SENHA_DIVERGENCIA = "2026"


# ============================================================
# CRIAÇÃO DE PASTAS
# ============================================================

os.makedirs(PASTA_BACKUP, exist_ok=True)
os.makedirs(PASTA_FOTOS, exist_ok=True)
os.makedirs(PASTA_QR, exist_ok=True)


# ============================================================
# LISTAS
# ============================================================

LISTA_CORREDORES = [
    f"Corredor {i:02d}"
    for i in range(1, 26)
]

LISTA_PALLETS = [
    f"Pallet {i:02d}"
    for i in range(1, 21)
]

LISTA_LOCAIS_TIPO = [
    "Pallet",
    "Prateleira"
]

LISTA_NUMEROS_LOCAL = [
    f"Item {i:02d}"
    for i in range(1, 26)
]

LISTA_LADOS = [
    "Direito",
    "Esquerdo",
    "Centro / Único"
]

OPCOES_CAIXA = [
    "Caixa com 12 garrafas",
    "Caixa com 6 garrafas",
    "Caixa com 3 garrafas",
    "Caixa com 2 garrafas",
    "Garrafa Avulsa (1 un)",
    "Outra quantidade"
]


# ============================================================
# HORÁRIO
# ============================================================

def obter_horario_brasilia():
    fuso_brasilia = timezone(timedelta(hours=-3))
    return datetime.now(fuso_brasilia)


def obter_saudacao():
    hora = obter_horario_brasilia().hour

    if 0 <= hora < 12:
        return "Bom dia"
    elif 12 <= hora < 18:
        return "Boa tarde"
    else:
        return "Boa noite"


# ============================================================
# BACKUP
# ============================================================

def realizar_backup(nome):
    if os.path.exists(nome):
        ts = obter_horario_brasilia().strftime("%Y%m%d_%H%M%S")

        shutil.copy(
            nome,
            os.path.join(
                PASTA_BACKUP,
                f"backup_{ts}_{nome}"
            )
        )


# ============================================================
# ESTOQUE
# ============================================================

def carregar_dados():
    """Carrega o estoque sem criar vinhos de exemplo automaticamente."""
    estoque = []

    if os.path.exists(NOME_ARQUIVO):
        try:
            with open(NOME_ARQUIVO, "r", encoding="utf-8") as f:
                dados = json.load(f)
                if isinstance(dados, list):
                    estoque = dados
        except Exception:
            estoque = []

    # Remove o registro de demonstração antigo que versões anteriores
    # recriavam quando o último vinho real era apagado.
    estoque_limpo = []
    for vinho in estoque:
        registro_demo_campana = (
            str(vinho.get("nome", "")).strip().lower() == "campana merlot"
            and str(vinho.get("safra", "")).strip() == "2024"
            and str(vinho.get("codigo_barras", "")).strip() == "7891008116632"
            and str(vinho.get("localizacao", "")).strip() == "Corredor 01 - Pallet Item 01"
        )
        if not registro_demo_campana:
            estoque_limpo.append(vinho)

    # Se o arquivo estiver vazio, o estoque permanece realmente vazio.
    return sorted(
        estoque_limpo,
        key=lambda x: x.get("nome", "").lower()
    )


def salvar_dados(estoque):

    estoque_ordenado = sorted(
        estoque,
        key=lambda x: x.get("nome", "").lower()
    )

    with open(
        NOME_ARQUIVO,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            estoque_ordenado,
            f,
            ensure_ascii=False,
            indent=4
        )

    realizar_backup(NOME_ARQUIVO)

    st.session_state.estoque = estoque_ordenado


# ============================================================
# USUÁRIOS
# ============================================================

def carregar_usuarios():
    usuarios = []

    if os.path.exists(ARQUIVO_USUARIOS):
        try:
            with open(ARQUIVO_USUARIOS, "r", encoding="utf-8") as f:
                usuarios = json.load(f)
        except Exception:
            usuarios = []

    # Primeiro acesso: mantém o administrador principal padrão do sistema.
    if not usuarios:
        usuarios = [
            {
                "nome": "Vagner Souza",
                "cargo": "Administrador Principal",
                "senha": "1980",
                "status": "Aprovado",
                "aprovado_por": "Sistema"
            }
        ]

    # Compatibilidade com cadastros antigos.
    alterado = False
    for usuario in usuarios:
        if usuario.get("cargo") == "Administrador":
            usuario["cargo"] = "Administrador Principal"
            alterado = True
        if "status" not in usuario:
            usuario["status"] = "Aprovado"
            alterado = True
        if "aprovado_por" not in usuario:
            usuario["aprovado_por"] = "Cadastro antigo"
            alterado = True

    if alterado:
        salvar_usuarios(usuarios)

    return usuarios


def salvar_usuarios(usuarios):

    with open(
        ARQUIVO_USUARIOS,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            usuarios,
            f,
            ensure_ascii=False,
            indent=4
        )


# ============================================================
# LOGS
# ============================================================

def carregar_logs():

    if os.path.exists(ARQUIVO_LOGS):

        try:

            with open(
                ARQUIVO_LOGS,
                "r",
                encoding="utf-8"
            ) as f:

                return json.load(f)

        except Exception:
            pass

    return []


def registrar_log(
    usuario,
    acao,
    detalhes
):

    logs = carregar_logs()

    logs.insert(
        0,
        {
            "data_hora":
                obter_horario_brasilia().strftime(
                    "%d/%m/%Y %H:%M:%S"
                ),
            "usuario": usuario,
            "acao": acao,
            "detalhes": detalhes
        }
    )

    with open(
        ARQUIVO_LOGS,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            logs,
            f,
            ensure_ascii=False,
            indent=4
        )


# ============================================================
# PEDIDOS
# ============================================================

def carregar_pedidos():

    pedidos = []

    if os.path.exists(ARQUIVO_PEDIDOS):

        try:

            with open(
                ARQUIVO_PEDIDOS,
                "r",
                encoding="utf-8"
            ) as f:

                pedidos = json.load(f)

        except Exception:
            pass

    for p in pedidos:

        if "itens" in p:

            for item in p["itens"]:

                if "qtd_separada" not in item:
                    item["qtd_separada"] = 0

                if "divergencia" not in item:
                    item["divergencia"] = 0

                if "autorizado_divergencia" not in item:
                    item["autorizado_divergencia"] = False

                if "separado" not in item:
                    item["separado"] = False

    return pedidos


def salvar_pedidos(pedidos):

    with open(
        ARQUIVO_PEDIDOS,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            pedidos,
            f,
            ensure_ascii=False,
            indent=4
        )


# ============================================================
# SINCRONIZA ESTOQUE COM PEDIDOS
# ============================================================

def sincronizar_estoque_com_pedidos(pedidos, estoque):
    """Pedidos não devem criar ou recriar itens no cadastro de estoque.

    O estoque é administrado somente por Cadastro, Edição e movimentação
    de localização/pallet. Assim, excluir um vinho do estoque é definitivo
    e uma lista de pedido antiga não faz o vinho reaparecer.
    """
    return estoque


# ============================================================
# INTERPRETAR PEDIDO
# ============================================================

def interpretar_linha_pedido(
    texto_linha
):

    texto = texto_linha.strip()

    safra = ""
    quantidade = 1

    anos = re.findall(
        r"\b(20\d{2})\b",
        texto
    )

    if anos:

        safra = anos[0]
        texto_limpo = texto.replace(
            safra,
            ""
        )

    else:
        texto_limpo = texto

    match_qtd = re.search(
        r"(?:/|\bcaixas?|\bqt[d]?\.?)\s*(\d+)",
        texto_limpo,
        re.IGNORECASE
    )

    if match_qtd:

        quantidade = int(
            match_qtd.group(1)
        )

        texto_limpo = texto_limpo.replace(
            match_qtd.group(0),
            ""
        )

    else:

        numeros_soltos = re.findall(
            r"\b(\d+)\b",
            texto_limpo
        )

        if numeros_soltos:

            quantidade = int(
                numeros_soltos[-1]
            )

            texto_limpo = texto_limpo.replace(
                numeros_soltos[-1],
                ""
            )

    texto_limpo = re.sub(
        r"\bcaixas?\b",
        "",
        texto_limpo,
        flags=re.IGNORECASE
    )

    nome = re.sub(
        r"[/\|\-\–]+",
        "",
        texto_limpo
    ).strip().title()

    return {
        "nome": nome,
        "safra": safra,
        "quantidade": quantidade,
        "separado": False,
        "qtd_separada": 0,
        "divergencia": 0,
        "autorizado_divergencia": False
    }


# ============================================================
# ARQUIVO DE PEDIDO
# ============================================================

def extrair_pedidos_de_arquivo(arq):

    itens = []

    ext = arq.name.split(".")[-1].lower()

    try:

        if ext in ["xlsx", "xls"]:

            df = pd.read_excel(arq)

            for _, row in df.iterrows():

                nome_bruto = str(
                    row.get(
                        "Nome",
                        row.iloc[0]
                        if len(row) > 0
                        else ""
                    )
                ).strip()

                if nome_bruto and nome_bruto != "Nan":

                    safra_col = str(
                        row.get(
                            "Safra",
                            row.iloc[1]
                            if len(row) > 1
                            else ""
                        )
                    ).strip()

                    qtd_col = row.get(
                        "Quantidade",
                        row.iloc[2]
                        if len(row) > 2
                        else 1
                    )

                    try:
                        qtd = int(qtd_col)
                    except Exception:
                        qtd = 1

                    itens.append(
                        {
                            "nome":
                                nome_bruto.title(),

                            "safra":
                                safra_col
                                if safra_col != "Nan"
                                else "",

                            "quantidade":
                                qtd,

                            "separado":
                                False,

                            "qtd_separada":
                                0,

                            "divergencia":
                                0,

                            "autorizado_divergencia":
                                False
                        }
                    )

        elif ext == "txt":

            linhas = [
                l.strip()
                for l in
                arq.getvalue()
                .decode("utf-8")
                .split("\n")
                if l.strip()
            ]

            for l in linhas:

                itens.append(
                    interpretar_linha_pedido(l)
                )

    except Exception:
        pass

    return itens


# ============================================================
# PALLETS
# ============================================================

def gerar_id_pallet(
    corredor,
    pallet,
    lado
):

    c = re.search(
        r"(\d+)",
        corredor
    )

    p = re.search(
        r"(\d+)",
        pallet
    )

    numero_c = (
        c.group(1).zfill(2)
        if c
        else "00"
    )

    numero_p = (
        p.group(1).zfill(2)
        if p
        else "00"
    )

    if lado == "Direito":
        lado_codigo = "D"

    elif lado == "Esquerdo":
        lado_codigo = "E"

    else:
        lado_codigo = "C"

    return f"C{numero_c}-P{numero_p}-{lado_codigo}"


def carregar_pallets():

    if os.path.exists(ARQUIVO_PALLETS):

        try:

            with open(
                ARQUIVO_PALLETS,
                "r",
                encoding="utf-8"
            ) as f:

                pallets = json.load(f)

        except Exception:

            pallets = []

    else:

        pallets = []

    # Garante estrutura correta
    for pallet in pallets:

        if "id" not in pallet:
            pallet["id"] = ""

        if "vinhos" not in pallet:
            pallet["vinhos"] = []

    return pallets


def salvar_pallets(pallets):

    with open(
        ARQUIVO_PALLETS,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            pallets,
            f,
            ensure_ascii=False,
            indent=4
        )

    st.session_state.pallets = pallets


def obter_pallet(
    pallets,
    pallet_id
):

    return next(
        (
            p
            for p in pallets
            if p.get("id") == pallet_id
        ),
        None
    )


def criar_ou_atualizar_pallet(
    corredor,
    pallet_nome,
    lado,
    pallets
):

    pallet_id = gerar_id_pallet(
        corredor,
        pallet_nome,
        lado
    )

    existente = obter_pallet(
        pallets,
        pallet_id
    )

    if existente:
        return existente

    novo = {
        "id": pallet_id,
        "corredor": corredor,
        "pallet": pallet_nome,
        "lado": lado,
        "vinhos": []
    }

    pallets.append(novo)

    return novo



# ============================================================
# SINCRONIZAÇÃO DE LOCALIZAÇÃO / FOTOS
# ============================================================

def _numero_de_texto(valor, padrao="01"):
    match = re.search(r"(\d+)", str(valor or ""))
    return match.group(1).zfill(2) if match else padrao


def decompor_localizacao_vinho(vinho):
    """Converte a localização salva nos campos usados no formulário."""
    localizacao = str(vinho.get("localizacao", "") or "")

    corredor_match = re.search(r"Corredor\s*(\d+)", localizacao, re.IGNORECASE)
    corredor = (
        f"Corredor {corredor_match.group(1).zfill(2)}"
        if corredor_match else LISTA_CORREDORES[0]
    )

    if re.search(r"Prateleira", localizacao, re.IGNORECASE):
        local_tipo = "Prateleira"
    else:
        local_tipo = "Pallet"

    item_match = re.search(
        r"(?:Pallet|Prateleira)(?:\s+Item)?\s*(\d+)",
        localizacao,
        re.IGNORECASE,
    )
    numero_item = (
        f"Item {item_match.group(1).zfill(2)}"
        if item_match else LISTA_NUMEROS_LOCAL[0]
    )

    lado = vinho.get("lado", LISTA_LADOS[0])
    if lado not in LISTA_LADOS:
        lado = LISTA_LADOS[0]

    return corredor, local_tipo, numero_item, lado


def nome_pallet_por_item(numero_item):
    return f"Pallet {_numero_de_texto(numero_item)}"


def localizacao_por_campos(corredor, local_tipo, numero_item):
    return f"{corredor} - {local_tipo} {numero_item}"


def remover_vinho_de_todos_pallets(nome, safra=None):
    nome_ref = str(nome or "").strip().lower()
    safra_ref = None if safra is None else str(safra or "").strip()
    alterado = False

    for pallet in st.session_state.get("pallets", []):
        vinhos_antes = pallet.get("vinhos", [])
        vinhos_depois = []

        for item in vinhos_antes:
            mesmo_nome = str(item.get("nome", "")).strip().lower() == nome_ref
            mesma_safra = (
                safra_ref is None
                or str(item.get("safra", "")).strip() == safra_ref
            )
            if mesmo_nome and mesma_safra:
                alterado = True
            else:
                vinhos_depois.append(item)

        pallet["vinhos"] = vinhos_depois

    if alterado:
        salvar_pallets(st.session_state.pallets)


def sincronizar_vinho_com_pallet(vinho, corredor, pallet_nome, lado, nome_antigo=None):
    """Move o vinho para um único pallet e atualiza estoque + cadastro de pallets."""
    nome_atual = str(vinho.get("nome", "")).strip()
    safra_atual = str(vinho.get("safra", "")).strip()

    remover_vinho_de_todos_pallets(nome_antigo or nome_atual)
    if nome_antigo and nome_antigo != nome_atual:
        remover_vinho_de_todos_pallets(nome_atual)

    pallet_obj = criar_ou_atualizar_pallet(
        corredor,
        pallet_nome,
        lado,
        st.session_state.pallets,
    )
    pallet_obj.setdefault("vinhos", []).append({
        "nome": nome_atual,
        "safra": safra_atual,
    })

    numero = _numero_de_texto(pallet_nome)
    vinho["localizacao"] = f"{corredor} - Pallet Item {numero}"
    vinho["lado"] = lado

    salvar_pallets(st.session_state.pallets)
    salvar_dados(st.session_state.estoque)


def salvar_foto_vinho(arquivo, nome_vinho, foto_atual=""):
    if arquivo is None:
        return foto_atual or ""

    extensao = Path(arquivo.name).suffix.lower()
    if extensao not in [".jpg", ".jpeg", ".png", ".webp"]:
        return foto_atual or ""

    nome_seguro = re.sub(r"[^a-zA-Z0-9_-]+", "_", nome_vinho.strip())[:60]
    timestamp = obter_horario_brasilia().strftime("%Y%m%d_%H%M%S_%f")
    caminho = os.path.join(PASTA_FOTOS, f"{nome_seguro}_{timestamp}{extensao}")

    with open(caminho, "wb") as f:
        f.write(arquivo.getbuffer())

    return caminho


def item_pedido_por_vinho(vinho, quantidade=1):
    return {
        "nome": vinho.get("nome", ""),
        "safra": vinho.get("safra", ""),
        "quantidade": int(quantidade),
        "separado": False,
        "qtd_separada": 0,
        "divergencia": 0,
        "autorizado_divergencia": False,
    }


def adicionar_codigo_lista_pedido(codigo, quantidade=1):
    codigo = str(codigo or "").strip()
    if not codigo:
        return False, "Informe ou leia um código de barras."

    vinho = next(
        (
            v for v in st.session_state.estoque
            if str(v.get("codigo_barras", "")).strip() == codigo
        ),
        None,
    )

    if not vinho:
        return False, f"Código {codigo} não encontrado no cadastro de vinhos."

    lista = st.session_state.setdefault("itens_pedido_scanner", [])
    existente = next(
        (
            item for item in lista
            if item.get("nome") == vinho.get("nome")
            and str(item.get("safra", "")) == str(vinho.get("safra", ""))
        ),
        None,
    )

    if existente:
        existente["quantidade"] = int(existente.get("quantidade", 0)) + int(quantidade)
    else:
        lista.append(item_pedido_por_vinho(vinho, quantidade))

    return True, f"{vinho.get('nome', '')} incluído na lista."


def normalizar_nome_vinho(texto):
    texto = str(texto or "").strip().lower()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = re.sub(r"[^a-z0-9]+", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()


def localizar_vinho_cadastrado(nome, safra=""):
    nome_norm = normalizar_nome_vinho(nome)
    safra = str(safra or "").strip()

    candidatos = [
        v for v in st.session_state.estoque
        if normalizar_nome_vinho(v.get("nome", "")) == nome_norm
    ]

    if not candidatos:
        return None

    if safra:
        mesmo_ano = next(
            (v for v in candidatos if str(v.get("safra", "")).strip() == safra),
            None,
        )
        if mesmo_ano:
            return mesmo_ano

    return candidatos[0]


def validar_itens_pedido_no_estoque(itens):
    """Valida a lista antes de salvar. Pedido nunca cadastra vinho automaticamente."""
    validos = []
    nao_cadastrados = []

    for item in itens or []:
        vinho = localizar_vinho_cadastrado(
            item.get("nome", ""),
            item.get("safra", ""),
        )

        if not vinho:
            nao_cadastrados.append({
                "nome": item.get("nome", ""),
                "safra": item.get("safra", ""),
            })
            continue

        item_validado = dict(item)
        # Usa o nome oficial do cadastro para evitar variações na conferência.
        item_validado["nome"] = vinho.get("nome", item.get("nome", ""))
        if not str(item_validado.get("safra", "")).strip():
            item_validado["safra"] = vinho.get("safra", "")
        validos.append(item_validado)

    return validos, nao_cadastrados


# ============================================================
# QR CODE
# ============================================================

def gerar_qr_pallet(
    pallet_id,
    pallet=None
):

    if not QRCODE_DISPONIVEL:
        return None

    # O QR Code passa a carregar também as informações
    # dos vinhos que estão cadastrados naquele pallet.
    # Assim, um leitor comum de QR Code já consegue
    # mostrar nome e safra, sem depender do sistema.
    if pallet is None:
        pallet = obter_pallet(
            st.session_state.get("pallets", []),
            pallet_id
        )

    if pallet:
        linhas_qr = [
            "PREMIUM WINES",
            "INFORMACOES DO PALLET",
            f"Codigo: {pallet_id}",
            f"Corredor: {pallet.get('corredor', '')}",
            f"Pallet: {pallet.get('pallet', '')}",
            f"Lado: {pallet.get('lado', '')}",
            "",
            "VINHOS:"
        ]

        vinhos_qr = pallet.get("vinhos", [])

        if vinhos_qr:
            for indice, vinho in enumerate(vinhos_qr, start=1):
                nome = str(vinho.get("nome", "")).strip()
                safra = str(vinho.get("safra", "N/A")).strip() or "N/A"
                linhas_qr.append(
                    f"{indice}. {nome} | Safra: {safra}"
                )
        else:
            linhas_qr.append("Nenhum vinho cadastrado neste pallet.")

        conteudo_qr = "\n".join(linhas_qr)
    else:
        # Mantém compatibilidade com QR Codes antigos.
        conteudo_qr = pallet_id

    caminho = os.path.join(
        PASTA_QR,
        f"{pallet_id}.png"
    )

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4
    )

    qr.add_data(conteudo_qr)
    qr.make(fit=True)

    img = qr.make_image(
        fill_color="#7A1C2E",
        back_color="white"
    )

    img.save(caminho)

    return caminho


def extrair_id_do_qr(conteudo):
    """
    Aceita tanto o código antigo (C01-P01-D) quanto
    o novo conteúdo completo do QR Code.
    """
    texto = str(conteudo or "").strip()

    match = re.search(
        r"(?:Codigo|Código)\s*:\s*(C\d{2}-P\d{2}-[DEC])",
        texto,
        re.IGNORECASE
    )

    if match:
        return match.group(1).upper()

    match = re.search(
        r"\b(C\d{2}-P\d{2}-[DEC])\b",
        texto,
        re.IGNORECASE
    )

    if match:
        return match.group(1).upper()

    return texto.upper()


# ============================================================
# LEITOR QR CODE
# ============================================================

def componente_leitor_qr(
    chave_sessao
):

    html_code = f"""
    <div style="
        text-align:center;
        background:#17171B;
        padding:15px;
        border-radius:12px;
        border:1px solid #35353C;
    ">

        <div
            id="reader_{chave_sessao}"
            style="
                width:100%;
                max-width:400px;
                margin:auto;
                border-radius:8px;
                overflow:hidden;
            ">
        </div>

        <p
            id="resultado_{chave_sessao}"
            style="
                font-weight:bold;
                color:#D6AE63;
                margin-top:10px;
                font-size:1rem;
            ">
        </p>

    </div>

    <script src="https://unpkg.com/html5-qrcode"></script>

    <script>

    function onScanSuccess(
        decodedText,
        decodedResult
    ) {{

        document.getElementById(
            "resultado_{chave_sessao}"
        ).innerText =
            "✅ QR Code lido: " + decodedText;

        const url =
            new URL(
                window.parent.location.href
            );

        url.searchParams.set(
            'scanned_{chave_sessao}',
            decodedText
        );

        window.parent.history.replaceState(
            {{}},
            '',
            url
        );

        if (
            window.html5QrCode_{chave_sessao}
        ) {{

            window
                .html5QrCode_{chave_sessao}
                .stop()
                .catch(
                    err => {{}}
                );

        }}

    }}

    try {{

        const html5QrCode =
            new Html5Qrcode(
                "reader_{chave_sessao}"
            );

        window.html5QrCode_{chave_sessao} =
            html5QrCode;

        html5QrCode.start(

            {{ facingMode: "environment" }},

            {{
                fps: 10,
                qrbox: {{
                    width: 250,
                    height: 250
                }}
            }},

            onScanSuccess

        ).catch(
            err => {{}}
        );

    }} catch (e) {{}}

    </script>
    """

    components.html(
        html_code,
        height=420
    )



# ============================================================
# LEITOR DE CÓDIGO DE BARRAS PARA PEDIDOS
# ============================================================

def componente_leitor_codigo_barras(chave_sessao):
    html_code = f"""
    <div style="text-align:center;background:#17171B;padding:15px;border-radius:12px;border:1px solid #35353C;">
        <div id="barcode_{chave_sessao}" style="width:100%;max-width:440px;margin:auto;border-radius:8px;overflow:hidden;"></div>
        <p id="barcode_result_{chave_sessao}" style="font-weight:bold;color:#D6AE63;margin-top:10px;font-size:1rem;"></p>
    </div>

    <script src="https://unpkg.com/html5-qrcode"></script>
    <script>
    function onBarcodeSuccess(decodedText, decodedResult) {{
        document.getElementById("barcode_result_{chave_sessao}").innerText =
            "✅ Código lido: " + decodedText;

        const url = new URL(window.parent.location.href);
        url.searchParams.set('scanned_{chave_sessao}', decodedText);
        window.parent.history.replaceState({{}}, '', url);

        if (window.barcodeReader_{chave_sessao}) {{
            window.barcodeReader_{chave_sessao}.stop().catch(err => {{}});
        }}
        window.parent.location.reload();
    }}

    try {{
        const formatos = [
            Html5QrcodeSupportedFormats.EAN_13,
            Html5QrcodeSupportedFormats.EAN_8,
            Html5QrcodeSupportedFormats.CODE_128,
            Html5QrcodeSupportedFormats.CODE_39,
            Html5QrcodeSupportedFormats.UPC_A,
            Html5QrcodeSupportedFormats.UPC_E,
            Html5QrcodeSupportedFormats.ITF,
            Html5QrcodeSupportedFormats.QR_CODE
        ];

        const reader = new Html5Qrcode(
            "barcode_{chave_sessao}",
            {{ formatsToSupport: formatos, verbose: false }}
        );
        window.barcodeReader_{chave_sessao} = reader;
        reader.start(
            {{ facingMode: "environment" }},
            {{ fps: 10, qrbox: {{ width: 300, height: 160 }} }},
            onBarcodeSuccess
        ).catch(err => {{}});
    }} catch (e) {{}}
    </script>
    """

    components.html(html_code, height=360)


# ============================================================
# NAVEGAÇÃO PARA CADASTRO A PARTIR DO PEDIDO
# ============================================================

def abrir_cadastro_vinho_faltante(nome, safra=""):
    """Abre o cadastro já preenchido sem perder o pedido em andamento."""
    st.session_state.cadastro_vinho_prefill = {
        "nome": str(nome or "").strip(),
        "safra": str(safra or "").strip(),
    }
    st.session_state.retornar_apos_cadastro = "PedidosMatriz"
    st.session_state.menu_atual = "Cadastrar"


# ============================================================
# INICIALIZAÇÃO SESSION STATE
# ============================================================

if "usuarios" not in st.session_state:

    st.session_state.usuarios = (
        carregar_usuarios()
    )

st.session_state.estoque = (
    carregar_dados()
)

st.session_state.pedidos = (
    carregar_pedidos()
)

st.session_state.pallets = (
    carregar_pallets()
)

sincronizar_estoque_com_pedidos(
    st.session_state.pedidos,
    st.session_state.estoque
)

if "menu_atual" not in st.session_state:
    st.session_state.menu_atual = "🏠 Home"

if "termo_busca" not in st.session_state:
    st.session_state.termo_busca = ""

if "itens_pedido_scanner" not in st.session_state:
    st.session_state.itens_pedido_scanner = []

if "codigo_bipado_pedido" not in st.session_state:
    st.session_state.codigo_bipado_pedido = ""


# ============================================================
# TRATAMENTO DE QR SCANEADO
# ============================================================

qp = st.query_params

for key, val in list(qp.items()):

    if key.startswith("scanned_"):

        sess_key = key.replace(
            "scanned_",
            ""
        )

        valor_limpo = str(
            val
        ).strip()

        if sess_key == "leitor_pallet":

            st.session_state.qr_pallet_lido = (
                valor_limpo
            )

        elif sess_key == "checkout_camera":

            st.session_state.codigo_bipado_checkout = (
                valor_limpo
            )

        elif sess_key == "pedido_scanner":

            st.session_state.codigo_bipado_pedido = (
                valor_limpo
            )

        del st.query_params[key]

        st.rerun()


# ============================================================
# LOGIN
# ============================================================

user_url = qp.get("user", None)
cargo_url = qp.get("cargo", "Operador")

if (
    "usuario_logado" not in st.session_state
    or st.session_state.usuario_logado is None
):
    usuario_url_valido = next(
        (
            u for u in st.session_state.usuarios
            if u.get("nome", "").lower() == str(user_url or "").lower()
            and u.get("status", "Aprovado") == "Aprovado"
        ),
        None
    )

    if usuario_url_valido:
        st.session_state.usuario_logado = usuario_url_valido
    elif (
        str(user_url or "").lower() == "dev"
        and str(qp.get("auth", "")) == SENHA_DEV
    ):
        st.session_state.usuario_logado = {
            "nome": "Dev",
            "cargo": "Desenvolvedor",
            "status": "Aprovado"
        }
    else:
        st.session_state.usuario_logado = None


if st.session_state.usuario_logado is None:
    st.markdown("<style>[data-testid=\"stSidebar\"]{display:none!important;}</style>", unsafe_allow_html=True)
    st.markdown(
        """
        <div class="login-shell">
            <div class="login-logo">🍷</div>
            <div class="login-title">PREMIUM <span>WINES</span></div>
            <div class="login-subtitle">Gestão de Estoque & Expedição • Galpão</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    _, cc, _ = st.columns([1, 1.1, 1])
    with cc:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)
        tab1, tab2, tab3 = st.tabs(["🔑 Entrar", "👤 Criar Conta", "⚙️ Dev"])

        with tab1:
            st.caption("Acesse sua área de operação.")
            with st.form("l_form"):
                u = st.text_input("Usuário", placeholder="Digite seu usuário").strip().title()
                p = st.text_input("Senha", type="password", placeholder="Digite sua senha").strip()
                if st.form_submit_button("ENTRAR", use_container_width=True):
                    user = next(
                        (
                            x for x in st.session_state.usuarios
                            if x["nome"].lower() == u.lower()
                            and x["senha"] == p
                            and x.get("status", "Aprovado") == "Aprovado"
                        ),
                        None
                    )
                    if user:
                        st.session_state.usuario_logado = user
                        st.query_params["user"] = user["nome"]
                        st.query_params["cargo"] = user.get("cargo", "Operador")
                        st.rerun()
                    else:
                        st.error("Usuário, senha ou autorização inválidos.")

        with tab2:
            st.caption(
                "Administrador Principal precisa de aprovação do DEV. "
                "Usuário comum precisa de aprovação de um Administrador Principal."
            )
            admins_aprovados = [
                u for u in st.session_state.usuarios
                if u.get("cargo") == "Administrador Principal"
                and u.get("status", "Aprovado") == "Aprovado"
            ]
            with st.form("c_form"):
                n = st.text_input("Nome", placeholder="Nome para acesso").strip().title()
                s_conta = st.text_input("Senha", type="password", placeholder="Crie uma senha").strip()
                tipo_conta = st.selectbox(
                    "Tipo de conta",
                    ["Usuário Comum", "Administrador Principal"]
                )
                if st.form_submit_button("SOLICITAR CADASTRO", use_container_width=True):
                    if not n or not s_conta:
                        st.error("Preencha nome e senha.")
                    elif any(
                        u.get("nome", "").lower() == n.lower()
                        for u in st.session_state.usuarios
                    ):
                        st.error("Já existe uma conta ou solicitação com esse nome.")
                    elif tipo_conta == "Usuário Comum" and not admins_aprovados:
                        st.error(
                            "Ainda não existe Administrador Principal aprovado. "
                            "Um administrador precisa ser aprovado pelo DEV primeiro."
                        )
                    else:
                        cargo_novo = (
                            "Administrador Principal"
                            if tipo_conta == "Administrador Principal"
                            else "Operador"
                        )
                        novo = {
                            "nome": n,
                            "cargo": cargo_novo,
                            "senha": s_conta,
                            "status": "Pendente",
                            "aprovado_por": "",
                            "data_solicitacao": obter_horario_brasilia().strftime("%d/%m/%Y %H:%M:%S")
                        }
                        st.session_state.usuarios.append(novo)
                        salvar_usuarios(st.session_state.usuarios)
                        registrar_log(n, "Solicitou Cadastro", f"Tipo: {cargo_novo}")
                        if cargo_novo == "Administrador Principal":
                            st.success("Solicitação enviada ao DEV para aprovação.")
                        else:
                            st.success("Solicitação enviada a um Administrador Principal.")

        with tab3:
            st.caption("Área restrita do desenvolvedor.")
            with st.form("d_form"):
                sp = st.text_input("Senha Mestra", type="password")
                if st.form_submit_button("ACESSAR COMO DEV", use_container_width=True):
                    if sp == SENHA_DEV:
                        st.session_state.usuario_logado = {
                            "nome": "Dev", "cargo": "Desenvolvedor", "status": "Aprovado"
                        }
                        st.query_params["user"] = "Dev"
                        st.query_params["cargo"] = "Desenvolvedor"
                        st.query_params["auth"] = SENHA_DEV
                        st.rerun()
                    else:
                        st.error("Senha incorreta.")
        st.markdown('</div>', unsafe_allow_html=True)

    st.stop()




def render_page_header(icone, titulo, descricao, secao="Premium Wines • Galpão"):
    """Cabeçalho visual padrão para todas as telas internas."""
    st.markdown(
        f"""
        <div class="page-hero">
            <div class="page-kicker">{html.escape(secao)}</div>
            <div class="page-title">{icone} {html.escape(titulo)}</div>
            <div class="page-desc">{html.escape(descricao)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ============================================================
# CABEÇALHO + MENU LATERAL
# ============================================================

cargo_logado = st.session_state.usuario_logado.get("cargo", "Operador")
acesso_gestao = cargo_logado in ["Administrador Principal", "Desenvolvedor"]
usuario_nome = st.session_state.usuario_logado.get("nome", "Usuário")

# Menu lateral inspirado no mockup Premium Wines
with st.sidebar:
    st.markdown(
        """
        <div class="sidebar-brand">
            <div class="brand-title">🍷 PREMIUM WINES</div>
            <div class="brand-sub">GALPÃO • WMS</div>
        </div>
        """,
        unsafe_allow_html=True
    )

    if st.button("🏠  Início", use_container_width=True, key="nav_home"):
        st.session_state.menu_atual = "🏠 Home"; st.rerun()

    st.markdown('<div class="sidebar-section">Operação</div>', unsafe_allow_html=True)
    if st.button("📦  Checkout de Expedição", use_container_width=True, key="nav_checkout"):
        st.session_state.menu_atual = "PedidosMatriz"; st.rerun()
    if st.button("🏢  Painel da Matriz", use_container_width=True, key="nav_painel"):
        st.session_state.menu_atual = "PainelMatriz"; st.rerun()
    if st.button("🔎  Buscar / Filtros", use_container_width=True, key="nav_busca"):
        st.session_state.menu_atual = "Filtros"; st.rerun()

    st.markdown('<div class="sidebar-section">Estoque</div>', unsafe_allow_html=True)
    if st.button("🍷  Estoque Completo", use_container_width=True, key="nav_estoque"):
        st.session_state.menu_atual = "Estoque"; st.rerun()
    if st.button("📱  Ler QR do Pallet", use_container_width=True, key="nav_lerqr"):
        st.session_state.menu_atual = "LerQRPallet"; st.rerun()
    if st.button("🏷️  Gerar QR dos Pallets", use_container_width=True, key="nav_gerarqr"):
        st.session_state.menu_atual = "GerarQRPallets"; st.rerun()
    if st.button("➕  Cadastrar Vinho", use_container_width=True, key="nav_cadastrar"):
        st.session_state.menu_atual = "Cadastrar"; st.rerun()
    if st.button("✏️  Editar Vinho", use_container_width=True, key="nav_editar"):
        st.session_state.menu_atual = "Editar"; st.rerun()
    if st.button("🗂️  Gerenciar Pallets", use_container_width=True, key="nav_pallets"):
        st.session_state.menu_atual = "GerenciarPallets"; st.rerun()

    if acesso_gestao:
        st.markdown('<div class="sidebar-section">Administração</div>', unsafe_allow_html=True)
        if st.button("📋  Histórico", use_container_width=True, key="nav_historico"):
            st.session_state.menu_atual = "Historico"; st.rerun()
        if st.button("⚙️  Gerenciar Usuários", use_container_width=True, key="nav_usuarios"):
            st.session_state.menu_atual = "GerenciarUsuarios"; st.rerun()

    st.markdown('<div class="sidebar-section">Sessão</div>', unsafe_allow_html=True)
    st.caption(f"{usuario_nome} • {cargo_logado}")
    if st.button("🚪  Sair", use_container_width=True, key="nav_sair"):
        st.session_state.usuario_logado = None
        st.query_params.clear()
        st.session_state.menu_atual = "🏠 Home"
        st.rerun()

# Topbar compacta
col_top1, col_top2 = st.columns([5, 1.35])
with col_top1:
    st.markdown(
        f"""
        <div class="topbar">
            <div class="topbar-brand">🍷 PREMIUM <span>WINES</span></div>
            <div class="topbar-user">{html.escape(usuario_nome)}<br>{html.escape(cargo_logado)}</div>
        </div>
        """,
        unsafe_allow_html=True
    )
with col_top2:
    if st.session_state.menu_atual != "🏠 Home":
        if st.button("← Início", use_container_width=True, key="top_voltar"):
            st.session_state.menu_atual = "🏠 Home"
            st.rerun()


# ============================================================
# HOME
# ============================================================

if st.session_state.menu_atual == "🏠 Home":
    # Indicadores seguros para diferentes versões dos dados existentes
    total_vinhos = len(st.session_state.get("estoque", []))
    pallets_ocupados = sum(
        1 for p in st.session_state.get("pallets", [])
        if p.get("vinhos")
    )
    pedidos_pendentes = sum(
        1 for p in st.session_state.get("pedidos", [])
        if str(p.get("status", "Pendente")).lower() not in ["finalizado", "concluído", "concluido"]
    )
    divergencias = sum(
        1
        for p in st.session_state.get("pedidos", [])
        for item in p.get("itens", [])
        if int(item.get("divergencia", 0) or 0) != 0
    )

    st.markdown(
        f"""
        <div class="hero-wine">
            <div class="hero-kicker">Gestão de estoque & expedição</div>
            <div class="hero-title">{obter_saudacao()}, {html.escape(usuario_nome)}.</div>
            <div class="hero-sub">
                Controle o galpão, localize vinhos, confira pedidos e acompanhe pallets em um só lugar.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    m1, m2, m3, m4 = st.columns(4)
    with m1: st.metric("🍷 Vinhos cadastrados", total_vinhos)
    with m2: st.metric("📦 Pallets ocupados", pallets_ocupados)
    with m3: st.metric("📋 Pedidos pendentes", pedidos_pendentes)
    with m4: st.metric("⚠️ Divergências", divergencias)

    st.markdown('<div class="section-title">Operação</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown('<div class="action-card"><div class="action-icon">📦</div><div class="action-title">Checkout de Expedição</div><div class="action-desc">Separar, conferir e finalizar pedidos.</div></div>', unsafe_allow_html=True)
        if st.button("Abrir Checkout", use_container_width=True, key="home_checkout"):
            st.session_state.menu_atual = "PedidosMatriz"; st.rerun()
    with c2:
        st.markdown('<div class="action-card"><div class="action-icon">🏢</div><div class="action-title">Painel da Matriz</div><div class="action-desc">Visualizar pedidos recebidos e andamento.</div></div>', unsafe_allow_html=True)
        if st.button("Abrir Painel", use_container_width=True, key="home_painel"):
            st.session_state.menu_atual = "PainelMatriz"; st.rerun()
    with c3:
        st.markdown('<div class="action-card"><div class="action-icon">🔎</div><div class="action-title">Buscar / Filtros</div><div class="action-desc">Encontrar vinho, safra e localização rapidamente.</div></div>', unsafe_allow_html=True)
        if st.button("Buscar Vinhos", use_container_width=True, key="home_busca"):
            st.session_state.menu_atual = "Filtros"; st.rerun()

    st.markdown('<div class="section-title">Estoque & Localização</div>', unsafe_allow_html=True)
    c4, c5, c6 = st.columns(3)
    with c4:
        st.markdown('<div class="action-card"><div class="action-icon">🍷</div><div class="action-title">Estoque Completo</div><div class="action-desc">Consultar todos os vinhos cadastrados.</div></div>', unsafe_allow_html=True)
        if st.button("Ver Estoque", use_container_width=True, key="home_estoque"):
            st.session_state.menu_atual = "Estoque"; st.rerun()
    with c5:
        st.markdown('<div class="action-card"><div class="action-icon">📱</div><div class="action-title">QR do Pallet</div><div class="action-desc">Ler o pallet e visualizar os vinhos armazenados.</div></div>', unsafe_allow_html=True)
        if st.button("Ler QR", use_container_width=True, key="home_lerqr"):
            st.session_state.menu_atual = "LerQRPallet"; st.rerun()
    with c6:
        st.markdown('<div class="action-card"><div class="action-icon">🏷️</div><div class="action-title">Gerar QR</div><div class="action-desc">Criar etiquetas QR atualizadas para os pallets.</div></div>', unsafe_allow_html=True)
        if st.button("Gerar QR", use_container_width=True, key="home_gerarqr"):
            st.session_state.menu_atual = "GerarQRPallets"; st.rerun()

    st.markdown('<div class="section-title">Cadastro & Organização</div>', unsafe_allow_html=True)
    c7, c8, c9 = st.columns(3)
    with c7:
        st.markdown('<div class="action-card"><div class="action-icon">➕</div><div class="action-title">Cadastrar Vinho</div><div class="action-desc">Adicionar vinho, safra, código, foto e localização.</div></div>', unsafe_allow_html=True)
        if st.button("Novo Vinho", use_container_width=True, key="home_cadastrar"):
            st.session_state.menu_atual = "Cadastrar"; st.rerun()
    with c8:
        st.markdown('<div class="action-card"><div class="action-icon">✏️</div><div class="action-title">Editar Vinho</div><div class="action-desc">Atualizar cadastro, localização e informações.</div></div>', unsafe_allow_html=True)
        if st.button("Editar Cadastro", use_container_width=True, key="home_editar"):
            st.session_state.menu_atual = "Editar"; st.rerun()
    with c9:
        st.markdown('<div class="action-card"><div class="action-icon">🗂️</div><div class="action-title">Gerenciar Pallets</div><div class="action-desc">Organizar os vinhos nas posições físicas do galpão.</div></div>', unsafe_allow_html=True)
        if st.button("Gerenciar Pallets", use_container_width=True, key="home_pallets"):
            st.session_state.menu_atual = "GerenciarPallets"; st.rerun()

    if acesso_gestao:
        st.markdown('<div class="section-title">Administração</div>', unsafe_allow_html=True)
        a1, a2 = st.columns(2)
        with a1:
            st.markdown('<div class="action-card"><div class="action-icon">📋</div><div class="action-title">Histórico</div><div class="action-desc">Auditoria por usuário, data e movimentação.</div></div>', unsafe_allow_html=True)
            if st.button("Abrir Histórico", use_container_width=True, key="home_historico"):
                st.session_state.menu_atual = "Historico"; st.rerun()
        with a2:
            st.markdown('<div class="action-card"><div class="action-icon">⚙️</div><div class="action-title">Gerenciar Usuários</div><div class="action-desc">Aprovar contas e administrar permissões.</div></div>', unsafe_allow_html=True)
            if st.button("Gerenciar Usuários", use_container_width=True, key="home_usuarios"):
                st.session_state.menu_atual = "GerenciarUsuarios"; st.rerun()


# ============================================================
# LER QR PALLET
# ============================================================

elif st.session_state.menu_atual == "LerQRPallet":

    render_page_header("📱", "Leitura de QR Code do Pallet", "Aponte a câmera para a etiqueta do pallet e veja imediatamente os vinhos e safras cadastrados naquela posição.", "Estoque • Localização")

    st.markdown(
        """
        Aponte a câmera do celular para o
        QR Code colocado no pallet.
        <br>
        O sistema mostrará os vinhos e as
        respectivas safras.
        <br>
        <b>Quantidade não é controlada nesta função.</b>
        """,
        unsafe_allow_html=True
    )

    st.markdown("---")

    modo_leitura = st.radio(
        "Forma de leitura:",
        [
            "📷 Câmera do celular",
            "⌨️ Digitar código"
        ],
        horizontal=True
    )

    codigo_lido = ""

    if modo_leitura == "📷 Câmera do celular":

        componente_leitor_qr(
            "leitor_pallet"
        )

        codigo_lido = (
            st.session_state.get(
                "qr_pallet_lido",
                ""
            )
        )

    else:

        codigo_lido = st.text_input(
            "Digite o código do pallet",
            placeholder="Ex.: C01-P04-D"
        )

    if codigo_lido:

        # O QR novo contém localização + lista de vinhos.
        # Extraímos o código do pallet para localizar os dados
        # completos também no sistema.
        conteudo_qr_lido = str(
            codigo_lido
        ).strip()

        codigo_lido = extrair_id_do_qr(
            conteudo_qr_lido
        )

        pallet = obter_pallet(
            st.session_state.pallets,
            codigo_lido
        )

        if pallet:

            st.markdown(
                f"""
                <div class="pallet-header">

                    <div style="
                        font-size:0.9rem;
                        opacity:0.85;
                    ">
                    POSIÇÃO IDENTIFICADA
                    </div>

                    <div style="
                        font-size:1.6rem;
                        font-weight:700;
                    ">
                    📍 {html.escape(
                        pallet["corredor"]
                    )}
                    </div>

                    <div style="
                        font-size:1.2rem;
                    ">
                    {html.escape(
                        pallet["pallet"]
                    )}
                    &nbsp; | &nbsp;
                    {html.escape(
                        pallet["lado"]
                    )}
                    </div>

                    <div style="
                        margin-top:8px;
                        font-size:0.85rem;
                        opacity:0.8;
                    ">
                    Código: {html.escape(
                        pallet["id"]
                    )}
                    </div>

                </div>
                """,
                unsafe_allow_html=True
            )

            vinhos = pallet.get(
                "vinhos",
                []
            )

            st.markdown(
                "### 🍷 Vinhos neste pallet"
            )

            if not vinhos:

                st.info(
                    "Nenhum vinho cadastrado "
                    "neste pallet."
                )

            else:

                st.success(
                    f"{len(vinhos)} vinho(s) "
                    "cadastrado(s) nesta posição."
                )

                for vinho in vinhos:

                    st.markdown(
                        f"""
                        <div class="wine-item">

                            <div style="
                                color:#D6AE63;
                                font-size:1.05rem;
                                font-weight:700;
                            ">
                            🍷 {html.escape(
                                vinho.get(
                                    "nome",
                                    ""
                                )
                            )}
                            </div>

                            <div style="
                                color:#AFA6A0;
                                margin-top:3px;
                            ">
                            Safra:
                            <b>
                            {html.escape(
                                vinho.get(
                                    "safra",
                                    "N/A"
                                )
                            )}
                            </b>
                            </div>

                        </div>
                        """,
                        unsafe_allow_html=True
                    )

        else:

            st.error(
                f"O QR Code {codigo_lido} "
                "não está cadastrado no sistema."
            )

            st.info(
                "Entre em 'Gerenciar Pallets' "
                "para cadastrar esta posição."
            )


# ============================================================
# GERAR QR PALLETS
# ============================================================

elif st.session_state.menu_atual == "GerarQRPallets":

    render_page_header("🏷️", "Gerar QR Codes dos Pallets", "Gere etiquetas atualizadas para os pallets com os vinhos e safras cadastrados em cada posição.", "Estoque • Identificação")

    st.markdown(
        """
        Cada posição física do galpão possui
        um QR Code próprio.

        Exemplo:

        **Corredor 01 → Pallet 04 → Direito**

        O QR Code contém a posição e também
        a lista dos vinhos cadastrados no pallet,
        incluindo nome e safra.

        <b>Se os vinhos do pallet forem alterados,
        gere o QR Code novamente.</b>
        """
    )

    if not QRCODE_DISPONIVEL:

        st.error(
            "A biblioteca qrcode não está instalada."
        )

        st.code(
            "pip install qrcode[pil]"
        )

    else:

        col1, col2, col3 = st.columns(3)

        with col1:

            corredor_qr = st.selectbox(
                "Corredor",
                LISTA_CORREDORES,
                key="qr_corredor"
            )

        with col2:

            pallet_qr = st.selectbox(
                "Pallet",
                LISTA_PALLETS,
                key="qr_pallet"
            )

        with col3:

            lado_qr = st.selectbox(
                "Lado",
                LISTA_LADOS,
                key="qr_lado"
            )

        id_qr = gerar_id_pallet(
            corredor_qr,
            pallet_qr,
            lado_qr
        )

        # Prévia limpa da posição selecionada
        st.markdown("### 📦 Posição do Pallet")

        info1, info2, info3 = st.columns(3)

        with info1:
            st.markdown(f"**Corredor**\n\n{corredor_qr}")

        with info2:
            st.markdown(f"**Pallet**\n\n{pallet_qr}")

        with info3:
            st.markdown(f"**Lado**\n\n{lado_qr}")

        st.caption(f"Código da posição: {id_qr}")

        pallet_preview = obter_pallet(
            st.session_state.pallets,
            id_qr
        )

        st.markdown("### 🍷 Conteúdo que será gravado no QR Code")

        if pallet_preview:
            vinhos_preview = pallet_preview.get("vinhos", [])
        else:
            vinhos_preview = []

        if vinhos_preview:
            for numero, vinho_preview in enumerate(vinhos_preview, start=1):
                nome_preview = str(vinho_preview.get("nome", "")).strip() or "Vinho sem nome"
                safra_preview = str(vinho_preview.get("safra", "N/A")).strip() or "N/A"
                st.markdown(
                    f"**{numero}. {nome_preview}**  \n"
                    f"Safra: **{safra_preview}**"
                )
        else:
            st.info(
                "Nenhum vinho cadastrado nesta posição. O QR Code será criado "
                "com a identificação do pallet e da localização."
            )

        if st.button(
            "🏷️ Gerar QR Code",
            use_container_width=True
        ):

            pallet_obj = (
                criar_ou_atualizar_pallet(
                    corredor_qr,
                    pallet_qr,
                    lado_qr,
                    st.session_state.pallets
                )
            )

            salvar_pallets(
                st.session_state.pallets
            )

            caminho_qr = gerar_qr_pallet(
                id_qr,
                pallet_obj
            )

            registrar_log(
                st.session_state.usuario_logado[
                    "nome"
                ],
                "Gerou QR Code de Pallet",
                id_qr
            )

            st.success(
                f"QR Code {id_qr} gerado!"
            )

            st.image(
                caminho_qr,
                width=300
            )

            with open(
                caminho_qr,
                "rb"
            ) as f:

                st.download_button(
                    "⬇️ Baixar QR Code",
                    data=f,
                    file_name=f"{id_qr}.png",
                    mime="image/png",
                    use_container_width=True
                )

        st.markdown("---")

        st.markdown(
            "### 🖨️ Gerar todos os QR Codes"
        )

        st.info(
            "Isso gera as posições selecionadas. "
            "Você poderá baixar cada QR e imprimir "
            "para colocar fisicamente nos pallets."
        )

        col_a, col_b = st.columns(2)

        with col_a:

            corredor_lote = st.selectbox(
                "Corredor para lote",
                ["Todos"] + LISTA_CORREDORES,
                key="corredor_lote"
            )

        with col_b:

            lado_lote = st.selectbox(
                "Lado para lote",
                ["Todos"] + LISTA_LADOS,
                key="lado_lote"
            )

        if st.button(
            "🏷️ Preparar QR Codes em Lote",
            use_container_width=True
        ):

            if corredor_lote == "Todos":

                corredores_lote = (
                    LISTA_CORREDORES
                )

            else:

                corredores_lote = [
                    corredor_lote
                ]

            if lado_lote == "Todos":

                lados_lote = LISTA_LADOS

            else:

                lados_lote = [
                    lado_lote
                ]

            lista_gerada = []

            for corredor in corredores_lote:

                for pallet_nome in LISTA_PALLETS:

                    for lado in lados_lote:

                        pid = gerar_id_pallet(
                            corredor,
                            pallet_nome,
                            lado
                        )

                        pallet_obj_lote = criar_ou_atualizar_pallet(
                            corredor,
                            pallet_nome,
                            lado,
                            st.session_state.pallets
                        )

                        caminho = gerar_qr_pallet(
                            pid,
                            pallet_obj_lote
                        )

                        lista_gerada.append(
                            (
                                pid,
                                corredor,
                                pallet_nome,
                                lado,
                                caminho
                            )
                        )

            salvar_pallets(
                st.session_state.pallets
            )

            st.success(
                f"{len(lista_gerada)} QR Codes "
                "preparados com sucesso."
            )

            st.markdown(
                "### QR Codes"
            )

            for (
                pid,
                corredor,
                pallet_nome,
                lado,
                caminho
            ) in lista_gerada:

                pallet_gerado = obter_pallet(
                    st.session_state.pallets,
                    pid
                )

                qtd_vinhos_gerado = len(
                    pallet_gerado.get("vinhos", [])
                ) if pallet_gerado else 0

                with st.expander(
                    f"{pid} — {corredor} | {pallet_nome} | {lado}"
                ):

                    st.caption(
                        f"🍷 {qtd_vinhos_gerado} vinho(s) "
                        "incluído(s) no QR Code"
                    )

                    st.image(
                        caminho,
                        width=220
                    )

                    with open(
                        caminho,
                        "rb"
                    ) as f:

                        st.download_button(
                            "⬇️ Baixar",
                            data=f,
                            file_name=f"{pid}.png",
                            mime="image/png",
                            key=f"download_{pid}"
                        )


# ============================================================
# GERENCIAR PALLETS
# ============================================================

elif st.session_state.menu_atual == "GerenciarPallets":

    render_page_header("🗂️", "Gerenciar Pallets e Vinhos", "Organize os vinhos por corredor, pallet e lado. As movimentações atualizam a localização em todo o sistema.", "Estoque • Organização")

    st.info(
        "Ao mover um vinho por aqui, a localização também é atualizada "
        "automaticamente na Busca, no Estoque Completo e no cadastro do vinho."
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        corredor_gp = st.selectbox("Corredor", LISTA_CORREDORES, key="gp_corredor")
    with col2:
        pallet_gp = st.selectbox("Pallet", LISTA_PALLETS, key="gp_pallet")
    with col3:
        lado_gp = st.selectbox("Lado", LISTA_LADOS, key="gp_lado")

    id_gp = gerar_id_pallet(corredor_gp, pallet_gp, lado_gp)
    pallet_atual = obter_pallet(st.session_state.pallets, id_gp)
    if not pallet_atual:
        pallet_atual = criar_ou_atualizar_pallet(
            corredor_gp, pallet_gp, lado_gp, st.session_state.pallets
        )
        salvar_pallets(st.session_state.pallets)

    st.markdown(
        f"""
        <div class="pallet-header">
            <div style="font-size:0.85rem;">POSIÇÃO SELECIONADA</div>
            <div style="font-size:1.5rem;font-weight:700;">{corredor_gp} | {pallet_gp}</div>
            <div>Lado: <b>{lado_gp}</b></div>
            <div style="margin-top:6px;font-size:0.85rem;">QR: {id_gp}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.session_state.estoque:
        opcoes = list(range(len(st.session_state.estoque)))
        indice_vinho = st.selectbox(
            "Selecione o vinho para mover para este pallet",
            [None] + opcoes,
            format_func=lambda i: "-- Selecionar --" if i is None else (
                f"{st.session_state.estoque[i].get('nome','')} — "
                f"Safra {st.session_state.estoque[i].get('safra','N/A')}"
            ),
            key="gp_vinho_indice",
        )

        if indice_vinho is not None:
            vinho_obj = st.session_state.estoque[indice_vinho]
            st.caption(
                f"Localização atual: {vinho_obj.get('localizacao','Sem localização')} "
                f"| {vinho_obj.get('lado','')}"
            )

            if st.button("📦 Mover vinho para este pallet", use_container_width=True):
                sincronizar_vinho_com_pallet(
                    vinho_obj,
                    corredor_gp,
                    pallet_gp,
                    lado_gp,
                )
                registrar_log(
                    st.session_state.usuario_logado["nome"],
                    "Moveu Vinho de Pallet",
                    f"{vinho_obj.get('nome','')} -> {id_gp}",
                )
                st.success("Vinho movido e localização atualizada em todo o sistema!")
                st.rerun()

    st.markdown("---")
    st.markdown("### 🍷 Vinhos atualmente neste pallet")
    vinhos_pallet = pallet_atual.get("vinhos", [])

    if not vinhos_pallet:
        st.info("Nenhum vinho cadastrado neste pallet.")
    else:
        for indice, vinho in enumerate(list(vinhos_pallet)):
            col_a, col_b = st.columns([5, 1])
            with col_a:
                st.markdown(
                    f"""
                    <div class="wine-item">
                    <b>🍷 {html.escape(vinho.get('nome',''))}</b><br>
                    Safra: <b>{html.escape(str(vinho.get('safra','N/A')))}</b>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            with col_b:
                if st.button("🗑️", key=f"remover_{id_gp}_{indice}"):
                    removido = vinhos_pallet.pop(indice)
                    salvar_pallets(st.session_state.pallets)

                    estoque_vinho = next(
                        (
                            v for v in st.session_state.estoque
                            if v.get("nome") == removido.get("nome")
                            and str(v.get("safra", "")) == str(removido.get("safra", ""))
                            and corredor_gp in str(v.get("localizacao", ""))
                            and _numero_de_texto(pallet_gp) in str(v.get("localizacao", ""))
                        ),
                        None,
                    )
                    if estoque_vinho:
                        estoque_vinho["localizacao"] = "Sem localização"
                        estoque_vinho["lado"] = ""
                        salvar_dados(st.session_state.estoque)

                    registrar_log(
                        st.session_state.usuario_logado["nome"],
                        "Removeu Vinho do Pallet",
                        f"{id_gp} - {removido.get('nome','')}",
                    )
                    st.rerun()


# ============================================================
# PAINEL MATRIZ
# ============================================================

elif st.session_state.menu_atual == "PainelMatriz":

    render_page_header("🏢", "Painel da Matriz", "Acompanhe pedidos, quantidades separadas, status e divergências em tempo real.", "Operação • Acompanhamento")

    st.markdown(
        "Aqui a Matriz visualiza em tempo real "
        "todos os pedidos salvos, finalizados "
        "e as divergências."
    )

    if not st.session_state.pedidos:

        st.info(
            "Nenhum pedido registrado no sistema."
        )

    else:

        for p in st.session_state.pedidos:

            status_col = (
                "#2E7D32"
                if p.get("status")
                == "Concluído / Expedido"
                else "#7A1C2E"
            )

            st.markdown(
                f"""
                <div style="
                    background:linear-gradient(180deg,#19191D,#141417);
                    padding:15px;
                    border-radius:14px;
                    border:1px solid #2E2E34;
                    margin-bottom:15px;
                ">

                <b>
                Mapa / Pedido Nº
                {html.escape(str(p["id"]))}
                </b>

                |

                Data:
                {html.escape(str(p["data"]))}

                |

                Status:
                <b style="color:{status_col};">
                {html.escape(
                    str(
                        p.get(
                            "status",
                            "Pendente"
                        )
                    )
                )}
                </b>

                </div>
                """,
                unsafe_allow_html=True
            )

            df_itens = []

            for item in p["itens"]:

                dif = item.get(
                    "divergencia",
                    0
                )

                if dif > 0:

                    dif_str = (
                        f"({dif:+d}) ⚠️ Excedente"
                    )

                elif dif < 0:

                    dif_str = (
                        f"({dif}) ⚠️ Falta"
                    )

                else:

                    dif_str = (
                        "(0) Correto"
                    )

                df_itens.append(
                    {
                        "Produto":
                            item["nome"],

                        "Safra":
                            item.get(
                                "safra",
                                "N/A"
                            ),

                        "Qtd Pedida":
                            item["quantidade"],

                        "Qtd Separada":
                            item.get(
                                "qtd_separada",
                                0
                            ),

                        "Divergência":
                            dif_str
                    }
                )

            st.dataframe(
                pd.DataFrame(df_itens),
                use_container_width=True
            )

            st.markdown("---")


# ============================================================
# PEDIDOS MATRIZ
# ============================================================

elif st.session_state.menu_atual == "PedidosMatriz":

    render_page_header("📦", "Checkout de Expedição", "Crie pedidos, faça a separação, confira por código de barras e trate divergências antes da expedição.", "Operação • Separação")

    aba_ped1, aba_ped2 = st.tabs(
        [
            "📋 Enviar / Cadastrar / Excluir Pedidos",
            "🔍 Conferência (Checkout de Expedição)"
        ]
    )

    with aba_ped1:

        st.markdown("### 📝 Montar novo pedido")
        st.caption(
            "Você pode enviar um arquivo, digitar os itens ou montar a lista andando "
            "pelos corredores e lendo o código de barras dos vinhos."
        )

        rascunho_pendente = st.session_state.get("rascunho_pedido_pendente")
        if rascunho_pendente:
            st.success(
                "✅ Seu pedido em andamento foi preservado enquanto você cadastrava o vinho."
            )
            c_ret1, c_ret2 = st.columns([3, 1])
            with c_ret1:
                st.caption(
                    f"Pedido: {rascunho_pendente.get('id', '')} • "
                    f"{len(rascunho_pendente.get('itens', []))} item(ns) guardado(s)."
                )
            with c_ret2:
                if st.button(
                    "▶️ Retomar pedido",
                    key="retomar_rascunho_pedido",
                    use_container_width=True,
                ):
                    st.session_state.id_novo_pedido = rascunho_pendente.get("id", "")
                    st.session_state.modo_novo_pedido = rascunho_pendente.get(
                        "modo", "⌨️ Digitar manualmente"
                    )
                    st.session_state.itens_pedido_retomados = [
                        dict(item) for item in rascunho_pendente.get("itens", [])
                    ]
                    st.rerun()

        proximo_numero = len(st.session_state.pedidos) + 1
        id_sugerido = f"123{proximo_numero:03d}"
        id_pedido = st.text_input(
            "Código de Barras / Identificação do Mapa",
            value=id_sugerido,
            key="id_novo_pedido",
        )

        modo_novo_pedido = st.radio(
            "Como deseja adicionar os vinhos?",
            [
                "📄 Enviar arquivo",
                "⌨️ Digitar manualmente",
                "📷 Leitor de código de barras",
            ],
            horizontal=True,
            key="modo_novo_pedido",
        )

        itens_novos = None

        # Ao voltar do cadastro, o pedido preservado pode ser retomado sem reconstruir a lista.
        if "itens_pedido_retomados" in st.session_state:
            itens_retomados = st.session_state.pop("itens_pedido_retomados")
            itens_novos = [dict(item) for item in itens_retomados]
            st.info("🔄 Retomando o pedido que estava em andamento...")

        if modo_novo_pedido == "📄 Enviar arquivo":
            arq_pedido = st.file_uploader(
                "Arquivo de Pedido (Excel ou TXT)",
                type=["xlsx", "xls", "txt"],
                key="arquivo_novo_pedido",
            )
            if st.button("💾 Salvar Pedido do Arquivo", use_container_width=True):
                itens_novos = (
                    extrair_pedidos_de_arquivo(arq_pedido)
                    if arq_pedido is not None else []
                )

        elif modo_novo_pedido == "⌨️ Digitar manualmente":
            texto_manual_pedido = st.text_area(
                "Digite um item por linha",
                placeholder="Ex.: Faleria Pinot Noir Reserva 2023 / 1 Caixa",
                key="texto_manual_novo_pedido",
            )
            if st.button("💾 Salvar Pedido Digitado", use_container_width=True):
                itens_novos = []
                for linha in texto_manual_pedido.split("\n"):
                    if linha.strip():
                        itens_novos.append(interpretar_linha_pedido(linha))

        else:
            st.success(
                "📷 Modo corredor: aponte a câmera para o código de barras da garrafa. "
                "O vinho será incluído na lista do pedido."
            )

            componente_leitor_codigo_barras("pedido_scanner")

            codigo_camera = st.session_state.get("codigo_bipado_pedido", "").strip()
            if codigo_camera:
                sucesso, mensagem = adicionar_codigo_lista_pedido(codigo_camera, 1)
                st.session_state.codigo_bipado_pedido = ""
                if sucesso:
                    st.toast(mensagem, icon="✅")
                    st.rerun()
                else:
                    st.error(mensagem)

            col_cod, col_qtd, col_add = st.columns([2, 1, 1])
            with col_cod:
                codigo_manual_scanner = st.text_input(
                    "Ou bipe/digite o código",
                    key="codigo_manual_lista_pedido",
                )
            with col_qtd:
                qtd_scanner = st.number_input(
                    "Quantidade",
                    min_value=1,
                    value=1,
                    step=1,
                    key="qtd_lista_pedido",
                )
            with col_add:
                st.write("")
                st.write("")
                if st.button("➕ Adicionar", use_container_width=True):
                    sucesso, mensagem = adicionar_codigo_lista_pedido(
                        codigo_manual_scanner,
                        qtd_scanner,
                    )
                    if sucesso:
                        st.success(mensagem)
                        st.rerun()
                    else:
                        st.error(mensagem)

            lista_scanner = st.session_state.itens_pedido_scanner
            st.markdown("#### 🛒 Lista montada pelo leitor")

            if not lista_scanner:
                st.info("A lista ainda está vazia. Leia o primeiro vinho.")
            else:
                for idx, item in enumerate(list(lista_scanner)):
                    c_info, c_del = st.columns([6, 1])
                    with c_info:
                        st.markdown(
                            f"**{idx + 1}. {item.get('nome','')}** — "
                            f"Safra {item.get('safra','N/A')} — "
                            f"Qtd: **{item.get('quantidade',1)}**"
                        )
                    with c_del:
                        if st.button("🗑️", key=f"del_item_scanner_{idx}"):
                            lista_scanner.pop(idx)
                            st.rerun()

                c_limpar, c_salvar = st.columns(2)
                with c_limpar:
                    if st.button("🧹 Limpar lista", use_container_width=True):
                        st.session_state.itens_pedido_scanner = []
                        st.rerun()
                with c_salvar:
                    if st.button("💾 Salvar Pedido da Lista", use_container_width=True):
                        itens_novos = [dict(item) for item in lista_scanner]

        if itens_novos is not None:
            if not str(id_pedido).strip():
                st.error("Informe a identificação do pedido.")
            elif not itens_novos:
                st.error("Nenhum item foi adicionado ao pedido.")
            else:
                itens_validados, nao_cadastrados = validar_itens_pedido_no_estoque(
                    itens_novos
                )

                if nao_cadastrados:
                    # Preserva o pedido em andamento antes de abrir o cadastro do vinho.
                    # Isso evita perder a lista digitada/importada ou montada pelo leitor.
                    st.session_state.rascunho_pedido_pendente = {
                        "id": str(id_pedido).strip(),
                        "modo": modo_novo_pedido,
                        "itens": [dict(item) for item in itens_novos],
                    }

                    st.error(
                        "❌ O pedido não pode ser salvo porque existem vinhos que "
                        "não estão cadastrados no galpão."
                    )
                    st.warning(
                        "Clique no nome do vinho para abrir o cadastro. O pedido ficará "
                        "guardado e, depois de cadastrar, você voltará para esta tela."
                    )

                    for indice_faltante, faltante in enumerate(nao_cadastrados):
                        nome_faltante = str(
                            faltante.get("nome", "Vinho sem nome")
                        ).strip()
                        safra_faltante = str(faltante.get("safra", "")).strip()
                        texto_botao = f"➕ Cadastrar {nome_faltante}"
                        if safra_faltante:
                            texto_botao += f" — Safra {safra_faltante}"

                        st.button(
                            texto_botao,
                            key=f"cadastrar_faltante_{indice_faltante}_{nome_faltante}",
                            use_container_width=True,
                            on_click=abrir_cadastro_vinho_faltante,
                            args=(nome_faltante, safra_faltante),
                        )
                else:
                    novo_registro_pedido = {
                        "id": str(id_pedido).strip(),
                        "data": obter_horario_brasilia().strftime("%d/%m/%Y %H:%M"),
                        "itens": itens_validados,
                        "status": "Pendente",
                    }
                    st.session_state.pedidos.append(novo_registro_pedido)
                    salvar_pedidos(st.session_state.pedidos)
                    sincronizar_estoque_com_pedidos(
                        st.session_state.pedidos,
                        st.session_state.estoque,
                    )
                    registrar_log(
                        st.session_state.usuario_logado["nome"],
                        "Cadastrou Pedido",
                        str(id_pedido).strip(),
                    )
                    if modo_novo_pedido == "📷 Leitor de código de barras":
                        st.session_state.itens_pedido_scanner = []
                    st.session_state.pop("rascunho_pedido_pendente", None)
                    st.success("Pedido salvo no sistema!")
                    st.rerun()

        st.markdown("---")
        st.markdown("### 🗑️ Excluir pedidos cadastrados")

        if st.session_state.pedidos:
            lista_ids_pedidos = [p["id"] for p in st.session_state.pedidos]
            mapas_para_excluir = st.multiselect(
                "Selecione os pedidos",
                lista_ids_pedidos,
                key="pedidos_para_excluir",
            )
            if st.button("🗑️ Excluir Pedidos Selecionados"):
                st.session_state.pedidos = [
                    p for p in st.session_state.pedidos
                    if p["id"] not in mapas_para_excluir
                ]
                salvar_pedidos(st.session_state.pedidos)
                registrar_log(
                    st.session_state.usuario_logado["nome"],
                    "Exclusão de Pedidos Antigos",
                    str(mapas_para_excluir),
                )
                st.success("Pedidos excluídos!")
                st.rerun()
        else:
            st.info("Nenhum pedido cadastrado.")

    with aba_ped2:

        if not st.session_state.pedidos:

            st.warning(
                "Nenhum pedido cadastrado."
            )

        else:

            mapas_disponiveis = [
                p["id"]
                for p
                in st.session_state.pedidos
            ]

            mapa_selecionado_id = (
                st.selectbox(
                    "Código de Barras Mapa",
                    mapas_disponiveis
                )
            )

            pedido_ativo = next(
                (
                    p
                    for p
                    in st.session_state.pedidos
                    if p["id"]
                    == mapa_selecionado_id
                ),
                None
            )

            if pedido_ativo:

                status_atual = (
                    pedido_ativo.get(
                        "status",
                        "Pendente"
                    )
                )

                cor_status = (
                    "#2E7D32"
                    if status_atual
                    == "Concluído / Expedido"
                    else "#7A1C2E"
                )

                st.markdown(
                    f"""
                    <div style="
                        background:linear-gradient(180deg,#19191D,#141417);
                        padding:12px;
                        border-radius:12px;
                        border:1px solid #2E2E34;
                        margin-bottom:15px;
                    ">

                    <b>
                    Conferência do Mapa
                    cod.
                    {html.escape(
                        pedido_ativo["id"]
                    )}
                    </b>

                    |

                    Status:

                    <b style="
                        color:{cor_status};
                    ">
                    {html.escape(
                        status_atual
                    )}
                    </b>

                    </div>
                    """,
                    unsafe_allow_html=True
                )

                modo_leitura = st.radio(
                    "Forma de Leitura:",
                    [
                        "⌨️ Seleção / Pistola USB",
                        "📷 Câmera do Celular"
                    ],
                    horizontal=True
                )

                codigo_capturado = ""

                if (
                    modo_leitura
                    == "📷 Câmera do Celular"
                ):

                    componente_leitor_qr(
                        "checkout_camera"
                    )

                    codigo_capturado = (
                        st.session_state.get(
                            "codigo_bipado_checkout",
                            ""
                        )
                    )

                itens_pendentes_lista = [
                    i["nome"]
                    for i
                    in pedido_ativo["itens"]
                    if not i.get(
                        "separado",
                        False
                    )
                ]

                col_b1, col_b2, col_b3 = (
                    st.columns(
                        [2, 1, 1]
                    )
                )

                with col_b1:

                    if (
                        modo_leitura
                        == "📷 Câmera do Celular"
                    ):

                        cod_barras_input = (
                            st.text_input(
                                "*Código de Barras ou Nome",
                                value=codigo_capturado,
                                key="input_bipagem_checkout"
                            )
                        )

                    else:

                        if itens_pendentes_lista:

                            opcao = st.selectbox(
                                "*Selecione o Vinho",
                                [
                                    "-- Selecione ou Digite --"
                                ]
                                + itens_pendentes_lista,
                                key="select_vinho_checkout"
                            )

                            if (
                                opcao
                                != "-- Selecione ou Digite --"
                            ):

                                cod_barras_input = (
                                    opcao
                                )

                            else:

                                cod_barras_input = (
                                    st.text_input(
                                        "*Ou digite/bipe o Código",
                                        key="input_bipagem_checkout"
                                    )
                                )

                        else:

                            cod_barras_input = (
                                st.text_input(
                                    "*Código de Barras ou Nome",
                                    key="input_bipagem_checkout"
                                )
                            )

                with col_b2:

                    qtd_input = st.number_input(
                        "*Qtd",
                        min_value=1,
                        value=1,
                        key="input_qtd_checkout"
                    )

                with col_b3:

                    st.write("")

                    btn_conferir = st.button(
                        "Conferir",
                        use_container_width=True
                    )

                if (
                    btn_conferir
                    and cod_barras_input
                ):

                    encontrou = False

                    qtd_real_informada = int(
                        qtd_input
                    )

                    for item in (
                        pedido_ativo["itens"]
                    ):

                        if (
                            item.get(
                                "separado",
                                False
                            )
                            and
                            item.get(
                                "divergencia",
                                0
                            ) == 0
                        ):

                            continue

                        vinho_no_estoque = next(
                            (
                                v
                                for v
                                in st.session_state.estoque
                                if
                                v["nome"].lower()
                                in item["nome"].lower()
                                or
                                v.get(
                                    "codigo_barras"
                                )
                                == cod_barras_input
                            ),
                            None
                        )

                        match_nome = (
                            cod_barras_input.lower()
                            in item["nome"].lower()
                        )

                        match_bc = (
                            vinho_no_estoque
                            and
                            vinho_no_estoque.get(
                                "codigo_barras"
                            )
                            == cod_barras_input
                        )

                        if (
                            match_nome
                            or match_bc
                        ):

                            encontrou = True

                            item[
                                "qtd_separada"
                            ] = qtd_real_informada

                            item[
                                "divergencia"
                            ] = (
                                item[
                                    "qtd_separada"
                                ]
                                -
                                item[
                                    "quantidade"
                                ]
                            )

                            if (
                                item[
                                    "divergencia"
                                ] == 0
                            ):

                                item[
                                    "autorizado_divergencia"
                                ] = True

                                item[
                                    "separado"
                                ] = True

                            else:

                                item[
                                    "autorizado_divergencia"
                                ] = False

                                item[
                                    "separado"
                                ] = False

                                st.warning(
                                    "⚠️ Quantidade divergente. "
                                    "O item foi bloqueado."
                                )

                            break

                    if encontrou:

                        if (
                            "codigo_bipado_checkout"
                            in st.session_state
                        ):

                            st.session_state.codigo_bipado_checkout = ""

                        salvar_pedidos(
                            st.session_state.pedidos
                        )

                        st.rerun()

                    else:

                        st.error(
                            "Produto não encontrado "
                            "neste mapa."
                        )

                itens_com_divergencia = [
                    i
                    for i
                    in pedido_ativo["itens"]
                    if
                    i.get(
                        "divergencia",
                        0
                    ) != 0
                    and
                    not i.get(
                        "autorizado_divergencia",
                        False
                    )
                ]

                if itens_com_divergencia:

                    st.markdown("---")

                    st.error(
                        "🔒 Existem itens divergentes "
                        "aguardando correção ou liberação."
                    )

                    for it_div in (
                        itens_com_divergencia
                    ):

                        with st.form(
                            f"form_senha_item_{it_div['nome']}"
                        ):

                            st.markdown(
                                f"""
                                **Item:**
                                {it_div["nome"]}
                                |
                                Pedido:
                                {it_div["quantidade"]}
                                |
                                Conferido:
                                {it_div["qtd_separada"]}
                                |
                                Divergência:
                                {it_div["divergencia"]:+d}
                                """
                            )

                            senha_item = (
                                st.text_input(
                                    "Senha de liberação",
                                    type="password",
                                    key=f"pass_{it_div['nome']}"
                                )
                            )

                            # IMPORTANTE: este é o primeiro submit do formulário.
                            # Assim, pressionar ENTER no campo da senha executa
                            # "Autorizar com Divergência", e nunca corrige a quantidade.
                            autorizar = st.form_submit_button(
                                "🔓 Autorizar Com Divergência",
                                use_container_width=True
                            )

                            corrigir = st.form_submit_button(
                                "🔄 Corrigir para Qtd Pedida",
                                use_container_width=True
                            )

                            if autorizar:

                                if senha_item == SENHA_DIVERGENCIA:

                                    it_div[
                                        "autorizado_divergencia"
                                    ] = True

                                    it_div[
                                        "separado"
                                    ] = True

                                    salvar_pedidos(
                                        st.session_state.pedidos
                                    )

                                    registrar_log(
                                        st.session_state.usuario_logado[
                                            "nome"
                                        ],
                                        "Liberou Divergência Item",
                                        (
                                            f"{it_div['nome']} | "
                                            f"Pedido: {it_div['quantidade']} | "
                                            f"Conferido: {it_div['qtd_separada']} | "
                                            f"Divergência: {it_div['divergencia']:+d}"
                                        )
                                    )

                                    st.rerun()

                                else:

                                    st.error(
                                        "Senha incorreta."
                                    )

                            if corrigir:

                                it_div[
                                    "qtd_separada"
                                ] = it_div[
                                    "quantidade"
                                ]

                                it_div[
                                    "divergencia"
                                ] = 0

                                it_div[
                                    "autorizado_divergencia"
                                ] = True

                                it_div[
                                    "separado"
                                ] = True

                                salvar_pedidos(
                                    st.session_state.pedidos
                                )

                                registrar_log(
                                    st.session_state.usuario_logado[
                                        "nome"
                                    ],
                                    "Corrigiu Divergência para Qtd Pedida",
                                    it_div["nome"]
                                )

                                st.rerun()

                st.markdown("---")

                col_esq, col_dir = st.columns(2)

                with col_esq:

                    st.markdown(
                        "<h4 style='color:#D6AE63;'>PRODUTOS A CONFERIR</h4>",
                        unsafe_allow_html=True
                    )

                    pendentes = [
                        i
                        for i
                        in pedido_ativo["itens"]
                        if not i.get(
                            "separado",
                            False
                        )
                    ]

                    if not pendentes:

                        st.success(
                            "🎉 Todos conferidos!"
                        )

                    for item in pendentes:

                        st.markdown(
                            f"""
                            <div class="wine-card">

                            <b>
                            {html.escape(
                                item["nome"]
                            )}
                            </b>

                            <br>

                            Safra:
                            {html.escape(
                                item.get(
                                    "safra",
                                    "N/A"
                                )
                            )}

                            <br>

                            Qtd Pedida:
                            <b>
                            {item["quantidade"]}
                            </b>

                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                with col_dir:

                    st.markdown(
                        "<h4 style='color:#2E7D32;'>PRODUTOS JÁ CONFERIDOS</h4>",
                        unsafe_allow_html=True
                    )

                    conferidos = [
                        i
                        for i
                        in pedido_ativo["itens"]
                        if i.get(
                            "separado",
                            False
                        )
                    ]

                    if not conferidos:

                        st.info(
                            "Nenhum produto conferido."
                        )

                    for item in conferidos:

                        st.markdown(
                            f"""
                            <div class="wine-card">

                            <b>
                            {html.escape(
                                item["nome"]
                            )}
                            </b>

                            <br>

                            Safra:
                            {html.escape(
                                item.get(
                                    "safra",
                                    "N/A"
                                )
                            )}

                            <br>

                            Separada:
                            <b>
                            {item.get(
                                "qtd_separada",
                                0
                            )}
                            </b>

                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                st.markdown("---")

                todos_conferidos = all(
                    i.get(
                        "separado",
                        False
                    )
                    for i
                    in pedido_ativo["itens"]
                )

                todas_divergencias_ok = all(
                    i.get(
                        "autorizado_divergencia",
                        False
                    )
                    for i
                    in pedido_ativo["itens"]
                    if i.get(
                        "divergencia",
                        0
                    ) != 0
                )

                if (
                    todos_conferidos
                    and
                    todas_divergencias_ok
                ):

                    if st.button(
                        "🚀 Concluir e Finalizar Expedição",
                        use_container_width=True
                    ):

                        pedido_ativo[
                            "status"
                        ] = "Concluído / Expedido"

                        salvar_pedidos(
                            st.session_state.pedidos
                        )

                        registrar_log(
                            st.session_state.usuario_logado[
                                "nome"
                            ],
                            "Finalizou Expedição Mapa",
                            pedido_ativo["id"]
                        )

                        st.success(
                            "🎉 Expedição concluída!"
                        )

                        st.rerun()

                else:

                    st.warning(
                        "⚠️ Todos os itens precisam "
                        "ser conferidos."
                    )


# ============================================================
# FILTROS
# ============================================================

elif st.session_state.menu_atual == "Filtros":

    render_page_header("🔍", "Buscar e Filtrar Vinhos", "Localize rapidamente vinhos por nome, tipo, safra e dados do cadastro.", "Estoque • Consulta")

    col_f1, col_f2 = st.columns(2)

    with col_f1:

        termo = st.text_input(
            "Pesquisar por nome, tipo ou safra:",
            value=st.session_state.termo_busca
        )

    with col_f2:

        tipo_filtro = st.selectbox(
            "Filtrar por Tipo:",
            [
                "Todos",
                "Tinto",
                "Branco",
                "Rosé",
                "Espumante",
                "Fortificado"
            ]
        )

    resultados = []

    for v in st.session_state.estoque:

        match_termo = (
            termo.lower()
            in v["nome"].lower()
            or
            termo.lower()
            in v.get(
                "safra",
                ""
            ).lower()
            or
            termo.lower()
            in v.get(
                "tipo",
                ""
            ).lower()
        )

        match_tipo = (
            tipo_filtro == "Todos"
            or
            v.get("tipo")
            == tipo_filtro
        )

        if (
            match_termo
            and match_tipo
        ):

            resultados.append(v)

    st.markdown(
        f"**Total de vinhos encontrados:** "
        f"{len(resultados)}"
    )

    st.markdown("---")

    if not resultados:

        st.info(
            "Nenhum vinho encontrado."
        )

    else:

        for vinho in resultados:

            st.markdown(
                f"""
                <div class="wine-card">

                <div class="wine-title">
                🍷 {html.escape(vinho["nome"])}
                ({html.escape(vinho.get("safra","N/A"))})
                </div>

                <p>
                <b>Tipo:</b>
                {html.escape(vinho.get("tipo","Tinto"))}

                |

                <b>Caixa:</b>
                {html.escape(vinho.get("caixa","N/A"))}
                </p>

                <p>
                <b>Localização:</b>
                📍 {html.escape(vinho["localizacao"])}

                ({html.escape(vinho.get("lado","N/A"))})
                </p>

                <p>
                <b>Cód. Barras:</b>
                {html.escape(
                    vinho.get(
                        "codigo_barras",
                        "Não cadastrado"
                    )
                )}
                </p>

                </div>
                """,
                unsafe_allow_html=True
            )


# ============================================================
# ESTOQUE
# ============================================================

elif st.session_state.menu_atual == "Estoque":

    render_page_header("🍷", "Estoque Completo do Galpão", "Consulte todo o inventário com safra, localização, caixa e código de barras.", "Estoque • Inventário")

    if not st.session_state.estoque:

        st.info(
            "Estoque vazio."
        )

    else:

        df_estoque = pd.DataFrame(
            [
                {
                    "Nome":
                        v["nome"],

                    "Tipo":
                        v.get(
                            "tipo",
                            "Tinto"
                        ),

                    "Safra":
                        v.get(
                            "safra",
                            ""
                        ),

                    "Localização":
                        v["localizacao"],

                    "Lado":
                        v.get(
                            "lado",
                            ""
                        ),

                    "Caixa":
                        v.get(
                            "caixa",
                            ""
                        ),

                    "Cód. Barras":
                        v.get(
                            "codigo_barras",
                            ""
                        )
                }
                for v
                in st.session_state.estoque
            ]
        )

        st.dataframe(
            df_estoque,
            use_container_width=True
        )


# ============================================================
# CADASTRAR VINHO
# ============================================================

elif st.session_state.menu_atual == "Cadastrar":

    render_page_header("➕", "Cadastrar Novo Vinho", "Cadastre nome, safra, tipo, localização, caixa, código de barras e foto do vinho.", "Cadastro • Novo item")

    cadastro_prefill = st.session_state.get("cadastro_vinho_prefill", {})
    veio_de_pedido = st.session_state.get("retornar_apos_cadastro") == "PedidosMatriz"

    if veio_de_pedido:
        st.info(
            "📋 Você veio de um pedido em andamento. Ao salvar este vinho, "
            "o sistema voltará automaticamente para o pedido."
        )

    with st.form("form_cadastrar_vinho"):
        nome = st.text_input(
            "*Nome do Vinho",
            value=str(cadastro_prefill.get("nome", "")),
        ).strip().title()
        tipo = st.selectbox(
            "Tipo de Vinho",
            ["Tinto", "Branco", "Rosé", "Espumante", "Fortificado"],
        )
        safra = st.text_input(
            "Safra (Ex: 2023)",
            value=str(cadastro_prefill.get("safra", "")),
        ).strip()

        col_l1, col_l2, col_l3, col_l4 = st.columns(4)
        with col_l1:
            corredor = st.selectbox("Corredor", LISTA_CORREDORES)
        with col_l2:
            local_tipo = st.selectbox("Tipo Local", LISTA_LOCAIS_TIPO)
        with col_l3:
            num_local = st.selectbox("Número Item", LISTA_NUMEROS_LOCAL)
        with col_l4:
            lado = st.selectbox("Lado", LISTA_LADOS)

        caixa = st.selectbox("Embalagem / Caixa", OPCOES_CAIXA)
        codigo_barras = st.text_input("Código de Barras (Opcional)").strip()
        foto_upload = st.file_uploader(
            "📷 Imagem do vinho (opcional)",
            type=["jpg", "jpeg", "png", "webp"],
            key="foto_cadastro_vinho",
        )

        if st.form_submit_button("💾 Salvar Novo Vinho"):
            if not nome:
                st.error("Informe o nome do vinho.")
            else:
                foto_path = salvar_foto_vinho(foto_upload, nome)
                localizacao_completa = localizacao_por_campos(
                    corredor, local_tipo, num_local
                )
                novo_vinho = {
                    "nome": nome,
                    "tipo": tipo,
                    "safra": safra,
                    "localizacao": localizacao_completa,
                    "lado": lado,
                    "caixa": caixa,
                    "codigo_barras": codigo_barras,
                    "foto": foto_path,
                }
                st.session_state.estoque.append(novo_vinho)
                salvar_dados(st.session_state.estoque)

                if local_tipo == "Pallet":
                    sincronizar_vinho_com_pallet(
                        novo_vinho,
                        corredor,
                        nome_pallet_por_item(num_local),
                        lado,
                    )

                registrar_log(
                    st.session_state.usuario_logado["nome"],
                    "Cadastrou Vinho",
                    nome,
                )
                st.success(f"Vinho '{nome}' cadastrado!")

                destino_retorno = st.session_state.pop(
                    "retornar_apos_cadastro", None
                )
                st.session_state.pop("cadastro_vinho_prefill", None)

                if destino_retorno == "PedidosMatriz":
                    st.session_state.menu_atual = "PedidosMatriz"

                st.rerun()


# ============================================================
# EDITAR VINHO
# ============================================================

elif st.session_state.menu_atual == "Editar":

    render_page_header("✏️", "Editar ou Remover Vinho", "Atualize informações, altere a localização física ou remova um vinho do estoque com segurança.", "Cadastro • Manutenção")
    st.caption("Agora você pode editar também corredor, pallet/prateleira, lado e imagem.")

    if not st.session_state.estoque:
        st.info("Nenhum vinho para editar.")
    else:
        indices = list(range(len(st.session_state.estoque)))
        indice_escolhido = st.selectbox(
            "Selecione o Vinho:",
            indices,
            format_func=lambda i: (
                f"{st.session_state.estoque[i].get('nome','')} — "
                f"Safra {st.session_state.estoque[i].get('safra','N/A')}"
            ),
        )
        vinho_obj = st.session_state.estoque[indice_escolhido]
        nome_original = vinho_obj.get("nome", "")

        foto_atual = vinho_obj.get("foto", "")
        if foto_atual and os.path.exists(foto_atual):
            st.image(foto_atual, width=180, caption="Imagem atual")

        corredor_atual, tipo_local_atual, item_atual, lado_atual = (
            decompor_localizacao_vinho(vinho_obj)
        )

        with st.form("form_editar_vinho"):
            novo_nome = st.text_input(
                "Nome do Vinho", value=vinho_obj.get("nome", "")
            ).strip().title()

            tipos_op = ["Tinto", "Branco", "Rosé", "Espumante", "Fortificado"]
            tipo_atual = vinho_obj.get("tipo", "Tinto")
            novo_tipo = st.selectbox(
                "Tipo de Vinho",
                tipos_op,
                index=tipos_op.index(tipo_atual) if tipo_atual in tipos_op else 0,
            )
            nova_safra = st.text_input(
                "Safra", value=str(vinho_obj.get("safra", ""))
            ).strip()

            st.markdown("#### 📍 Localização")
            loc1, loc2, loc3, loc4 = st.columns(4)
            with loc1:
                novo_corredor = st.selectbox(
                    "Corredor",
                    LISTA_CORREDORES,
                    index=LISTA_CORREDORES.index(corredor_atual),
                )
            with loc2:
                novo_local_tipo = st.selectbox(
                    "Tipo Local",
                    LISTA_LOCAIS_TIPO,
                    index=LISTA_LOCAIS_TIPO.index(tipo_local_atual),
                )
            with loc3:
                novo_num_local = st.selectbox(
                    "Número Item",
                    LISTA_NUMEROS_LOCAL,
                    index=(
                        LISTA_NUMEROS_LOCAL.index(item_atual)
                        if item_atual in LISTA_NUMEROS_LOCAL else 0
                    ),
                )
            with loc4:
                novo_lado = st.selectbox(
                    "Lado",
                    LISTA_LADOS,
                    index=LISTA_LADOS.index(lado_atual) if lado_atual in LISTA_LADOS else 0,
                )

            caixa_atual = vinho_obj.get("caixa", OPCOES_CAIXA[0])
            nova_caixa = st.selectbox(
                "Embalagem / Caixa",
                OPCOES_CAIXA,
                index=OPCOES_CAIXA.index(caixa_atual) if caixa_atual in OPCOES_CAIXA else 0,
            )
            novo_cb = st.text_input(
                "Código de Barras", value=str(vinho_obj.get("codigo_barras", ""))
            ).strip()
            nova_foto_upload = st.file_uploader(
                "📷 Trocar / inserir imagem do vinho",
                type=["jpg", "jpeg", "png", "webp"],
                key=f"foto_editar_{indice_escolhido}",
            )

            col_e1, col_e2 = st.columns(2)
            with col_e1:
                btn_salvar_edicao = st.form_submit_button("💾 Salvar Alterações")
            with col_e2:
                btn_excluir_vinho = st.form_submit_button("🗑️ Excluir Vinho")

            if btn_salvar_edicao:
                vinho_obj["nome"] = novo_nome
                vinho_obj["tipo"] = novo_tipo
                vinho_obj["safra"] = nova_safra
                vinho_obj["caixa"] = nova_caixa
                vinho_obj["codigo_barras"] = novo_cb
                vinho_obj["foto"] = salvar_foto_vinho(
                    nova_foto_upload,
                    novo_nome,
                    foto_atual,
                )
                vinho_obj["localizacao"] = localizacao_por_campos(
                    novo_corredor,
                    novo_local_tipo,
                    novo_num_local,
                )
                vinho_obj["lado"] = novo_lado

                salvar_dados(st.session_state.estoque)

                remover_vinho_de_todos_pallets(nome_original)
                if novo_local_tipo == "Pallet":
                    sincronizar_vinho_com_pallet(
                        vinho_obj,
                        novo_corredor,
                        nome_pallet_por_item(novo_num_local),
                        novo_lado,
                        nome_antigo=nome_original,
                    )

                registrar_log(
                    st.session_state.usuario_logado["nome"],
                    "Editou Vinho",
                    novo_nome,
                )
                st.success("Alterações salvas e localização sincronizada!")
                st.rerun()

            if btn_excluir_vinho:
                remover_vinho_de_todos_pallets(nome_original)
                st.session_state.estoque.pop(indice_escolhido)
                salvar_dados(st.session_state.estoque)
                registrar_log(
                    st.session_state.usuario_logado["nome"],
                    "Excluiu Vinho",
                    nome_original,
                )
                st.success("Vinho excluído!")
                st.rerun()


# ============================================================
# HISTÓRICO
# ============================================================

elif st.session_state.menu_atual == "Historico":
    cargo_logado = st.session_state.usuario_logado.get("cargo", "Operador")

    if cargo_logado not in ["Administrador Principal", "Desenvolvedor"]:
        st.error("Acesso restrito ao Administrador Principal e ao DEV.")
    else:
        render_page_header("📋", "Histórico de Auditoria", "Consulte as ações registradas no sistema por usuário e período.", "Administração • Auditoria")
        logs = carregar_logs()

        if not logs:
            st.info("Nenhum registro de log encontrado.")
        else:
            st.markdown("### 🔎 Filtros")
            usuarios_log = sorted({
                str(log.get("usuario", "")).strip()
                for log in logs
                if str(log.get("usuario", "")).strip()
            })

            c_f1, c_f2 = st.columns(2)
            with c_f1:
                filtro_usuario = st.selectbox(
                    "Usuário",
                    ["Todos"] + usuarios_log,
                    key="hist_usuario"
                )

            datas_validas = []
            for log in logs:
                try:
                    datas_validas.append(
                        datetime.strptime(
                            str(log.get("data_hora", ""))[:10],
                            "%d/%m/%Y"
                        ).date()
                    )
                except Exception:
                    pass

            with c_f2:
                opcoes_data = ["Todas"] + [
                    d.strftime("%d/%m/%Y")
                    for d in sorted(set(datas_validas), reverse=True)
                ]
                filtro_data = st.selectbox(
                    "Data",
                    opcoes_data,
                    key="hist_data"
                )

            logs_filtrados = []
            for log in logs:
                if (
                    filtro_usuario != "Todos"
                    and log.get("usuario") != filtro_usuario
                ):
                    continue
                if (
                    filtro_data != "Todas"
                    and not str(log.get("data_hora", "")).startswith(filtro_data)
                ):
                    continue
                logs_filtrados.append(log)

            st.caption(f"{len(logs_filtrados)} registro(s) encontrado(s).")
            if logs_filtrados:
                df_logs = pd.DataFrame(logs_filtrados)
                ordem = [
                    c for c in ["data_hora", "usuario", "acao", "detalhes"]
                    if c in df_logs.columns
                ]
                df_logs = df_logs[ordem]
                df_logs = df_logs.rename(columns={
                    "data_hora": "Data / Hora",
                    "usuario": "Usuário",
                    "acao": "Ação",
                    "detalhes": "Detalhes"
                })
                st.dataframe(df_logs, use_container_width=True, hide_index=True)
            else:
                st.info("Nenhum registro encontrado com esses filtros.")


# ============================================================
# USUÁRIOS E AUTORIZAÇÕES
# ============================================================

elif st.session_state.menu_atual == "GerenciarUsuarios":
    cargo_logado = st.session_state.usuario_logado.get("cargo", "Operador")
    nome_logado = st.session_state.usuario_logado.get("nome", "")

    if cargo_logado not in ["Administrador Principal", "Desenvolvedor"]:
        st.error("Acesso restrito ao Administrador Principal e ao DEV.")
    else:
        render_page_header("⚙️", "Gerenciamento de Usuários", "Aprove solicitações, controle permissões e acompanhe os usuários autorizados do sistema.", "Administração • Acessos")

        def atualizar_status_usuario(nome_usuario, novo_status, aprovador):
            for usuario in st.session_state.usuarios:
                if usuario.get("nome") == nome_usuario:
                    usuario["status"] = novo_status
                    usuario["aprovado_por"] = aprovador
                    usuario["data_aprovacao"] = obter_horario_brasilia().strftime(
                        "%d/%m/%Y %H:%M:%S"
                    )
                    break
            salvar_usuarios(st.session_state.usuarios)
            registrar_log(
                aprovador,
                f"{novo_status} Cadastro",
                nome_usuario
            )

        if cargo_logado == "Desenvolvedor":
            aba_admins, aba_todos = st.tabs([
                "🛡️ Autorizar Administradores Principais",
                "👥 Todos os Usuários"
            ])

            with aba_admins:
                pendentes_admin = [
                    u for u in st.session_state.usuarios
                    if u.get("cargo") == "Administrador Principal"
                    and u.get("status") == "Pendente"
                ]

                if not pendentes_admin:
                    st.success("Nenhum Administrador Principal aguardando aprovação.")
                else:
                    for i, usuario in enumerate(pendentes_admin):
                        with st.container(border=True):
                            st.markdown(
                                f"**{html.escape(usuario.get('nome',''))}**  \n"
                                f"Solicitado em: {html.escape(usuario.get('data_solicitacao',''))}"
                            )
                            ca, cr = st.columns(2)
                            with ca:
                                if st.button(
                                    "✅ Aprovar Administrador",
                                    key=f"aprovar_admin_{i}",
                                    use_container_width=True
                                ):
                                    atualizar_status_usuario(
                                        usuario.get("nome"),
                                        "Aprovado",
                                        "Dev"
                                    )
                                    st.rerun()
                            with cr:
                                if st.button(
                                    "❌ Rejeitar",
                                    key=f"rejeitar_admin_{i}",
                                    use_container_width=True
                                ):
                                    atualizar_status_usuario(
                                        usuario.get("nome"),
                                        "Rejeitado",
                                        "Dev"
                                    )
                                    st.rerun()

            with aba_todos:
                dados_usuarios = [
                    {
                        "Nome": u.get("nome", ""),
                        "Cargo": u.get("cargo", "Operador"),
                        "Status": u.get("status", "Aprovado"),
                        "Aprovado por": u.get("aprovado_por", "")
                    }
                    for u in st.session_state.usuarios
                ]
                if dados_usuarios:
                    st.dataframe(
                        pd.DataFrame(dados_usuarios),
                        use_container_width=True,
                        hide_index=True
                    )

        else:
            st.markdown("### 👤 Autorizar Usuários Comuns")
            pendentes_operador = [
                u for u in st.session_state.usuarios
                if u.get("cargo") == "Operador"
                and u.get("status") == "Pendente"
            ]

            if not pendentes_operador:
                st.success("Nenhum usuário comum aguardando aprovação.")
            else:
                for i, usuario in enumerate(pendentes_operador):
                    with st.container(border=True):
                        st.markdown(
                            f"**{html.escape(usuario.get('nome',''))}**  \n"
                            f"Solicitado em: {html.escape(usuario.get('data_solicitacao',''))}"
                        )
                        ca, cr = st.columns(2)
                        with ca:
                            if st.button(
                                "✅ Aprovar Usuário",
                                key=f"aprovar_op_{i}",
                                use_container_width=True
                            ):
                                atualizar_status_usuario(
                                    usuario.get("nome"),
                                    "Aprovado",
                                    nome_logado
                                )
                                st.rerun()
                        with cr:
                            if st.button(
                                "❌ Rejeitar",
                                key=f"rejeitar_op_{i}",
                                use_container_width=True
                            ):
                                atualizar_status_usuario(
                                    usuario.get("nome"),
                                    "Rejeitado",
                                    nome_logado
                                )
                                st.rerun()

            st.markdown("---")
            st.markdown("### 👥 Usuários Comuns")
            operadores = [
                {
                    "Nome": u.get("nome", ""),
                    "Status": u.get("status", "Aprovado"),
                    "Aprovado por": u.get("aprovado_por", "")
                }
                for u in st.session_state.usuarios
                if u.get("cargo") == "Operador"
            ]
            if operadores:
                st.dataframe(
                    pd.DataFrame(operadores),
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("Nenhum usuário comum cadastrado.")

