import os
import re
import json
import shutil
import html
import unicodedata
from io import BytesIO
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
    from PIL import Image, ImageDraw, ImageFont
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
    [data-testid="stExpander"] summary {
        color:#F3ECE7 !important;
        font-weight:760 !important;
        background:#29262B !important;
        border-radius:10px !important;
    }
    [data-testid="stExpander"] summary:hover { background:#34242B !important; }
    [data-testid="stExpander"] summary * { color:#F3ECE7 !important; }
    [data-testid="stExpander"] details[open] > summary {
        background:#32262C !important;
        border-bottom:1px solid #4A353D !important;
        border-radius:10px 10px 0 0 !important;
    }
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



    /* ========================================================
       CORREÇÕES VISUAIS — CAMPOS ESCUROS + TOPO SEM FAIXA BRANCA
       ======================================================== */

    /* Remove a barra branca nativa do Streamlit (Share / editar / GitHub)
       que estava cobrindo o cabeçalho Premium Wines. */
    header[data-testid="stHeader"],
    [data-testid="stHeader"],
    [data-testid="stToolbar"],
    [data-testid="stDecoration"],
    [data-testid="stMainMenu"],
    .stAppToolbar,
    .stDeployButton {
        display: none !important;
        visibility: hidden !important;
        height: 0 !important;
        min-height: 0 !important;
    }

    [data-testid="stAppViewContainer"] {
        background: transparent !important;
        padding-top: 0 !important;
    }

    [data-testid="stAppViewContainer"] > .main,
    [data-testid="stMain"] {
        padding-top: 0 !important;
        margin-top: 0 !important;
    }

    .block-container {
        padding-top: .75rem !important;
    }

    /* Fundo premium inspirado no mockup aprovado. A imagem fica escurecida
       pelas camadas de gradiente para não atrapalhar a leitura. */
    .stApp {
        background-image:
            linear-gradient(135deg, rgba(7,7,9,.94) 0%, rgba(14,10,12,.92) 52%, rgba(10,7,9,.95) 100%),
            radial-gradient(circle at 88% 8%, rgba(110,23,48,.28), transparent 33%),
            url("data:image/jpeg;base64,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") !important;
        background-size: cover !important;
        background-position: center center !important;
        background-attachment: fixed !important;
    }

    /* Imagem decorativa de barril/uvas nos destaques, sem encobrir texto. */
    .hero-wine, .page-hero {
        background-image:
            linear-gradient(90deg, rgba(24,13,17,.98) 0%, rgba(24,13,17,.92) 55%, rgba(15,12,14,.66) 100%),
            url("data:image/jpeg;base64,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") !important;
        background-size: cover !important;
        background-position: center right !important;
        background-repeat: no-repeat !important;
    }

    /* Selectbox / multiselect — evita caixa branca com texto branco. */
    [data-testid="stSelectbox"] div[data-baseweb="select"] > div,
    [data-testid="stMultiSelect"] div[data-baseweb="select"] > div {
        background-color: #17171B !important;
        color: #F7F3EE !important;
        border-color: #4A4045 !important;
        box-shadow: none !important;
    }

    [data-testid="stSelectbox"] div[data-baseweb="select"] *,
    [data-testid="stMultiSelect"] div[data-baseweb="select"] * {
        color: #F7F3EE !important;
        -webkit-text-fill-color: #F7F3EE !important;
    }

    [data-testid="stSelectbox"] input,
    [data-testid="stMultiSelect"] input,
    div[data-baseweb="select"] input {
        background: transparent !important;
        color: #F7F3EE !important;
        -webkit-text-fill-color: #F7F3EE !important;
        caret-color: #D6AE63 !important;
    }

    [data-testid="stSelectbox"] svg,
    [data-testid="stMultiSelect"] svg,
    div[data-baseweb="select"] svg {
        fill: #D6AE63 !important;
        color: #D6AE63 !important;
    }

    /* Menu suspenso dos selects. */
    div[data-baseweb="popover"],
    div[data-baseweb="popover"] > div,
    ul[role="listbox"],
    [role="listbox"] {
        background: #19191D !important;
        color: #F7F3EE !important;
        border-color: #3C3539 !important;
    }

    li[role="option"], [role="option"] {
        background: #19191D !important;
        color: #F7F3EE !important;
        -webkit-text-fill-color: #F7F3EE !important;
    }

    li[role="option"]:hover,
    [role="option"]:hover,
    [aria-selected="true"][role="option"] {
        background: #4A1022 !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }

    /* Upload de arquivo — o botão Upload/Selecionar arquivo não fica branco. */
    [data-testid="stFileUploader"] section,
    [data-testid="stFileUploaderDropzone"] {
        background: rgba(21,21,25,.96) !important;
        color: #EDE6E1 !important;
        border: 1px dashed #6A4D59 !important;
    }

    [data-testid="stFileUploader"] button {
        background: linear-gradient(135deg, #751A35, #541125) !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        border: 1px solid #8C2944 !important;
        border-radius: 10px !important;
        opacity: 1 !important;
    }

    [data-testid="stFileUploader"] button:hover {
        border-color: #D6AE63 !important;
        color: #FFFFFF !important;
    }

    [data-testid="stFileUploader"] * {
        color: #D8D0CB;
    }

    /* Number input — corrige os botões + e - que apareciam claros. */
    [data-testid="stNumberInput"] > div,
    [data-testid="stNumberInput"] div[data-baseweb="input"] > div {
        background: #17171B !important;
        border-color: #3A3A42 !important;
    }

    [data-testid="stNumberInput"] button {
        background: #242429 !important;
        color: #FFFFFF !important;
        border-color: #3A3A42 !important;
    }

    [data-testid="stNumberInput"] button:hover {
        background: #541125 !important;
        color: #FFFFFF !important;
    }

    [data-testid="stNumberInput"] button svg {
        fill: #D6AE63 !important;
        color: #D6AE63 !important;
    }

    /* Textos digitados permanecem visíveis inclusive em autofill/pesquisa. */
    .stTextInput input,
    .stNumberInput input,
    .stTextArea textarea,
    input[type="text"],
    input[type="password"],
    input[type="number"] {
        background-color: #17171B !important;
        color: #F7F3EE !important;
        -webkit-text-fill-color: #F7F3EE !important;
        caret-color: #D6AE63 !important;
    }

    input:-webkit-autofill,
    input:-webkit-autofill:hover,
    input:-webkit-autofill:focus {
        -webkit-text-fill-color: #F7F3EE !important;
        -webkit-box-shadow: 0 0 0 1000px #17171B inset !important;
        transition: background-color 9999s ease-out 0s;
    }

    /* Radio e checkbox sempre legíveis. */
    [data-testid="stRadio"] p,
    [data-testid="stCheckbox"] p {
        color: #E7DFDA !important;
    }

    /* Sidebar começa no topo real após remover o header nativo. */
    [data-testid="stSidebar"] {
        top: 0 !important;
        height: 100vh !important;
    }

    /* Evita que algum container interno herde branco do tema claro do navegador. */
    [data-testid="stVerticalBlockBorderWrapper"],
    [data-testid="stForm"],
    [data-testid="stExpander"] {
        color: #F7F3EE !important;
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

st.markdown(
    """
    <style>
    .stApp {
        background:
            radial-gradient(circle at 88% 8%, rgba(126,45,67,.20), transparent 31%),
            linear-gradient(135deg, #1A1518 0%, #211A1E 55%, #171316 100%) !important;
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #24161B 0%, #1C171A 100%) !important;
        border-right-color: #4A353D !important;
    }
    .topbar, .wine-card, .qr-card, .wine-item, .action-card,
    [data-testid="stMetric"], [data-testid="stForm"],
    [data-testid="stExpander"], .premium-panel {
        background: linear-gradient(180deg, #272125, #201A1E) !important;
        border-color: #4B3A41 !important;
    }
    [data-baseweb="input"] > div, [data-baseweb="select"] > div,
    [data-baseweb="textarea"] > div, .stTextInput input,
    .stNumberInput input, .stTextArea textarea {
        background: #241F22 !important;
        border-color: #5A474F !important;
    }
    [role="radiogroup"] {
        background: #211B1E !important;
        border-color: #4B3A41 !important;
    }
    p, .stMarkdown, [data-testid="stCaptionContainer"] { color: #E3DCD7 !important; }
    .action-desc, .premium-muted, .page-desc, .hero-sub { color: #C2B8B3 !important; }
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
    "Caixa com 24 garrafas",
    "Caixa com 12 garrafas",
    "Caixa com 6 garrafas",
    "Caixa com 3 garrafas",
    "Caixa com 2 garrafas",
    "Garrafa Avulsa (1 un)",
    "Outra quantidade"
]

LISTA_LITRAGENS = [
    "375 ml",
    "500 ml",
    "750 ml",
    "1 L",
    "1,5 L",
    "3 L",
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


def reconciliar_pallets_com_estoque(pallets, estoque):
    """
    Faz do estoque a fonte oficial do conteúdo dos pallets.

    Isso remove referências antigas de vinhos já apagados e garante que o QR
    mostre somente os vinhos que realmente existem no estoque e estão naquela
    posição/lado. Mantém as posições de pallet já criadas, mesmo quando vazias.
    """
    pallets = pallets if isinstance(pallets, list) else []
    estoque = estoque if isinstance(estoque, list) else []

    # Preserva as posições existentes, mas zera a lista de vinhos para
    # reconstruí-la a partir do cadastro atual do estoque.
    novos_pallets = []
    por_id = {}

    for p in pallets:
        if not isinstance(p, dict):
            continue
        novo = dict(p)
        novo.setdefault("id", "")
        novo.setdefault("corredor", "")
        novo.setdefault("pallet", "")
        novo.setdefault("lado", "")
        novo["vinhos"] = []
        novos_pallets.append(novo)
        if novo.get("id"):
            por_id[novo["id"]] = novo

    for vinho in estoque:
        if not isinstance(vinho, dict):
            continue

        localizacao = str(vinho.get("localizacao", "") or "")
        # Só entra em QR de pallet quando a localização for realmente um pallet.
        if "pallet" not in localizacao.lower():
            continue

        corredor_match = re.search(r"Corredor\s*(\d+)", localizacao, re.IGNORECASE)
        pallet_match = re.search(r"Pallet(?:\s+Item)?\s*(\d+)", localizacao, re.IGNORECASE)
        if not corredor_match or not pallet_match:
            continue

        corredor = f"Corredor {corredor_match.group(1).zfill(2)}"
        pallet_nome = f"Pallet {pallet_match.group(1).zfill(2)}"
        lado = str(vinho.get("lado", "") or "").strip() or "Centro / Único"
        if lado not in LISTA_LADOS:
            lado = "Centro / Único"

        pallet_id = gerar_id_pallet(corredor, pallet_nome, lado)
        pallet_obj = por_id.get(pallet_id)

        if pallet_obj is None:
            pallet_obj = {
                "id": pallet_id,
                "corredor": corredor,
                "pallet": pallet_nome,
                "lado": lado,
                "vinhos": [],
            }
            novos_pallets.append(pallet_obj)
            por_id[pallet_id] = pallet_obj

        item = {
            "nome": str(vinho.get("nome", "") or "").strip(),
            "safra": str(vinho.get("safra", "N/A") or "N/A").strip(),
        }
        if item["nome"] and item not in pallet_obj["vinhos"]:
            pallet_obj["vinhos"].append(item)

    # Ordena o conteúdo de cada pallet para deixar a prévia e o QR consistentes.
    for p in novos_pallets:
        p["vinhos"] = sorted(
            p.get("vinhos", []),
            key=lambda v: (str(v.get("nome", "")).lower(), str(v.get("safra", "")))
        )

    return novos_pallets


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


def adicionar_manual_lista_pedido(texto):
    texto = str(texto or "").strip()
    if not texto:
        return False, "Digite o nome do vinho antes de adicionar."

    linhas = [linha.strip() for linha in texto.split("\n") if linha.strip()]
    if not linhas:
        return False, "Digite pelo menos um vinho."

    lista = st.session_state.setdefault("itens_pedido_scanner", [])
    adicionados = 0

    for linha in linhas:
        item = interpretar_linha_pedido(linha)
        if not item.get("nome"):
            continue

        # Se já estiver cadastrado, usa nome/safra oficiais do estoque.
        vinho = localizar_vinho_cadastrado(item.get("nome", ""), item.get("safra", ""))
        novo_item = (
            item_pedido_por_vinho(vinho, item.get("quantidade", 1))
            if vinho
            else item
        )

        existente = next(
            (
                x for x in lista
                if normalizar_nome_vinho(x.get("nome", "")) == normalizar_nome_vinho(novo_item.get("nome", ""))
                and str(x.get("safra", "")).strip() == str(novo_item.get("safra", "")).strip()
            ),
            None,
        )

        if existente:
            existente["quantidade"] = int(existente.get("quantidade", 0)) + int(novo_item.get("quantidade", 1))
        else:
            lista.append(novo_item)
        adicionados += 1

    if not adicionados:
        return False, "Nenhum vinho válido foi informado."
    return True, f"{adicionados} item(ns) adicionado(s) à lista."


def callback_adicionar_manual_pedido():
    sucesso, mensagem = adicionar_manual_lista_pedido(
        st.session_state.get("texto_manual_novo_pedido", "")
    )
    st.session_state["mensagem_adicao_pedido"] = (sucesso, mensagem)
    if sucesso:
        # Callback executa antes da remontagem dos widgets: o campo volta vazio.
        st.session_state["texto_manual_novo_pedido"] = ""


def callback_adicionar_codigo_pedido():
    sucesso, mensagem = adicionar_codigo_lista_pedido(
        st.session_state.get("codigo_manual_lista_pedido", ""),
        st.session_state.get("qtd_lista_pedido", 1),
    )
    st.session_state["mensagem_adicao_pedido"] = (sucesso, mensagem)
    if sucesso:
        # Limpa o código e volta a quantidade para 1 após adicionar à lista.
        st.session_state["codigo_manual_lista_pedido"] = ""
        st.session_state["qtd_lista_pedido"] = 1


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

def url_publica_pallet(pallet_id):
    """Retorna a URL pública fixa usada nas etiquetas QR do galpão."""
    # Usar uma URL absoluta e fixa evita que o QR seja criado apenas com
    # o texto da posição quando o app estiver atrás do proxy do Streamlit.
    base_url = "https://galpaopremium-gwiywrdxssrwmzv9tdpeff.streamlit.app/"
    pallet_limpo = str(pallet_id or "").strip().upper()
    return f"{base_url}?pallet={pallet_limpo}&public=1"


def gerar_qr_pallet(
    pallet_id,
    pallet=None
):

    if not QRCODE_DISPONIVEL:
        return None

    # O QR Code grava uma URL pública que contém somente a identificação
    # da posição física do pallet. A página aberta consulta os vinhos atuais.
    conteudo_qr = url_publica_pallet(pallet_id)

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
        fill_color="black",
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


def dados_posicao_pallet_id(pallet_id):
    """Converte C01-P01-D em corredor, pallet e lado."""
    match = re.fullmatch(r"C(\d{2})-P(\d{2})-([DEC])", str(pallet_id or "").strip().upper())
    if not match:
        return None
    mapa_lado = {"D": "Direito", "E": "Esquerdo", "C": "Centro / Único"}
    return {
        "id": f"C{match.group(1)}-P{match.group(2)}-{match.group(3)}",
        "corredor": f"Corredor {match.group(1)}",
        "pallet": f"Pallet {match.group(2)}",
        "lado": mapa_lado[match.group(3)],
    }


def vinhos_atuais_da_posicao(pallet_id, estoque):
    """Consulta o estoque ao vivo para o QR público."""
    dados = dados_posicao_pallet_id(pallet_id)
    if not dados:
        return []
    encontrados = []
    for vinho in estoque or []:
        corredor, local_tipo, numero_item, lado = decompor_localizacao_vinho(vinho)
        if local_tipo != "Pallet":
            continue
        id_vinho = gerar_id_pallet(corredor, nome_pallet_por_item(numero_item), lado)
        if id_vinho == dados["id"]:
            encontrados.append({
                "nome": str(vinho.get("nome", "") or "").strip(),
                "safra": str(vinho.get("safra", "") or "N/A").strip(),
                "litragem": str(vinho.get("litragem", "") or "").strip(),
            })
    return sorted(encontrados, key=lambda v: (v.get("nome", "").lower(), v.get("safra", "")))


# ============================================================
# LEITOR QR CODE
# ============================================================

def componente_leitor_qr(chave_sessao, tela_retorno=None):
    """Leitor de QR de pallet. Ao ler, abre imediatamente a consulta da posição."""
    html_code = f"""
    <div style="text-align:center;background:#211B1E;padding:15px;border-radius:12px;border:1px solid #4A3A40;">
        <div id="reader_{chave_sessao}" style="width:100%;max-width:400px;margin:auto;border-radius:8px;overflow:hidden;"></div>
        <p id="resultado_{chave_sessao}" style="font-weight:bold;color:#E3BD72;margin-top:10px;font-size:1rem;"></p>
    </div>
    <script src="https://unpkg.com/html5-qrcode"></script>
    <script>
    let leituraConcluida_{chave_sessao} = false;
    function onScanSuccess(decodedText, decodedResult) {{
        if (leituraConcluida_{chave_sessao}) return;
        leituraConcluida_{chave_sessao} = true;
        document.getElementById("resultado_{chave_sessao}").innerText = "QR lido. Abrindo pallet...";

        const destino = new URL(window.parent.location.origin + window.parent.location.pathname);
        destino.searchParams.set('pallet', decodedText);
        destino.searchParams.set('public', '1');

        const abrir = () => {{ window.parent.location.href = destino.toString(); }};
        if (window.html5QrCode_{chave_sessao}) {{
            window.html5QrCode_{chave_sessao}.stop().then(abrir).catch(abrir);
        }} else {{
            abrir();
        }}
    }}
    try {{
        const html5QrCode = new Html5Qrcode("reader_{chave_sessao}");
        window.html5QrCode_{chave_sessao} = html5QrCode;
        html5QrCode.start(
            {{ facingMode: "environment" }},
            {{ fps: 10, qrbox: {{ width: 260, height: 260 }} }},
            onScanSuccess
        ).catch(err => {{
            document.getElementById("resultado_{chave_sessao}").innerText = "Não foi possível iniciar a câmera.";
        }});
    }} catch (e) {{}}
    </script>
    """
    components.html(html_code, height=420)


# ============================================================
# LEITOR DE CÓDIGO DE BARRAS PARA PEDIDOS
# ============================================================

def componente_leitor_codigo_barras(chave_sessao, tela_retorno=None):
    """Lê EAN/UPC/CODE/ITF e volta para a mesma tela do checkout/pedido."""
    tela_js = str(tela_retorno or "").replace('"', "")
    html_code = f"""
    <div style="text-align:center;background:#211B1E;padding:15px;border-radius:12px;border:1px solid #4A3A40;">
        <div id="barcode_{chave_sessao}" style="width:100%;max-width:440px;margin:auto;border-radius:8px;overflow:hidden;"></div>
        <p id="barcode_result_{chave_sessao}" style="font-weight:bold;color:#E3BD72;margin-top:10px;font-size:1rem;"></p>
    </div>
    <script src="https://unpkg.com/html5-qrcode"></script>
    <script>
    let leituraConcluida_{chave_sessao} = false;
    function onBarcodeSuccess(decodedText, decodedResult) {{
        if (leituraConcluida_{chave_sessao}) return;
        leituraConcluida_{chave_sessao} = true;
        document.getElementById("barcode_result_{chave_sessao}").innerText = "✅ Código lido: " + decodedText;
        const url = new URL(window.parent.location.href);
        url.searchParams.set('scanned_{chave_sessao}', decodedText);
        if ("{tela_js}") url.searchParams.set('screen', "{tela_js}");
        if ("{chave_sessao}" === "checkout_camera") url.searchParams.set('checkout', '1');
        const finalizar = () => {{ window.parent.location.href = url.toString(); }};
        if (window.barcodeReader_{chave_sessao}) {{
            window.barcodeReader_{chave_sessao}.stop().then(finalizar).catch(finalizar);
        }} else finalizar();
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
        const reader = new Html5Qrcode("barcode_{chave_sessao}", {{ formatsToSupport: formatos, verbose: false }});
        window.barcodeReader_{chave_sessao} = reader;
        reader.start(
            {{ facingMode: "environment" }},
            {{ fps: 12, qrbox: {{ width: 320, height: 170 }} }},
            onBarcodeSuccess
        ).catch(err => {{
            document.getElementById("barcode_result_{chave_sessao}").innerText = "Não foi possível iniciar a câmera.";
        }});
    }} catch (e) {{}}
    </script>
    """
    components.html(html_code, height=360)


def autofoco_campo_checkout():
    components.html(
        """
        <script>
        setTimeout(() => {
            try {
                const doc = window.parent.document;
                const inputs = Array.from(doc.querySelectorAll('input'));
                const alvo = inputs.find(el => {
                    const a = (el.getAttribute('aria-label') || '').toLowerCase();
                    return a.includes('digite/bipe') ||
                           a.includes('código de barras ou nome') ||
                           a.includes('codigo de barras ou nome');
                });
                if (alvo) { alvo.focus(); alvo.select(); }
            } catch (e) {}
        }, 250);
        </script>
        """,
        height=0,
    )


def instalar_atalhos_teclado():
    components.html(
        """
        <script>
        try {
            const win = window.parent;
            function voltarHome(e) {
                if (e.key === 'Escape' || e.key === 'Esc') {
                    e.preventDefault();
                    e.stopPropagation();
                    const url = new URL(win.location.href);
                    url.searchParams.set('screen', 'home');
                    url.searchParams.delete('checkout');
                    Array.from(url.searchParams.keys()).forEach(key => {
                        if (key.startsWith('scanned_')) url.searchParams.delete(key);
                    });
                    win.location.href = url.toString();
                }
            }
            // Captura ESC tanto quando o foco está no app quanto dentro deste componente.
            document.addEventListener('keydown', voltarHome, true);
            if (!win.__premiumWinesAtalhosInstalados) {
                win.__premiumWinesAtalhosInstalados = true;
                win.document.addEventListener('keydown', voltarHome, true);
            }
        } catch (e) {}
        </script>
        """,
        height=0,
    )
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

# O estoque é a fonte oficial do conteúdo dos pallets. Assim, ao apagar um
# vinho do estoque ele também desaparece automaticamente dos QR Codes/pallets.
_pallets_reconciliados = reconciliar_pallets_com_estoque(
    st.session_state.pallets,
    st.session_state.estoque,
)
if _pallets_reconciliados != st.session_state.pallets:
    st.session_state.pallets = _pallets_reconciliados
    with open(ARQUIVO_PALLETS, "w", encoding="utf-8") as _f_pallets:
        json.dump(st.session_state.pallets, _f_pallets, ensure_ascii=False, indent=4)

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

_screen_param = str(qp.get("screen", "") or "").strip()
if _screen_param:
    if _screen_param.lower() == "home":
        st.session_state.menu_atual = "🏠 Home"
    elif _screen_param == "PedidosMatriz":
        st.session_state.menu_atual = "PedidosMatriz"
    try:
        del st.query_params["screen"]
    except Exception:
        pass

if str(qp.get("checkout", "") or "") == "1":
    st.session_state["checkout_forcar_aba"] = True
    try:
        del st.query_params["checkout"]
    except Exception:
        pass

# ------------------------------------------------------------
# LEITOR PÚBLICO DE QR DO PALLET
# Permite escanear outro pallet sem voltar ao login/menu.
# ------------------------------------------------------------
_scan_publico = str(qp.get("scan_pallet", "") or "") == "1"
if _scan_publico:
    st.markdown(
        """
        <style>
        [data-testid='stSidebar']{display:none!important;}
        [data-testid='stHeader']{display:none!important;}
        .block-container{padding-top:1.2rem!important;max-width:900px!important;}
        .stApp{background:linear-gradient(135deg,#21181C,#2A2024)!important;}
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(
        """
        <div style="background:linear-gradient(135deg,#2B2024,#3A1823);border:1px solid #735063;border-radius:18px;padding:22px 24px;margin-bottom:18px;">
            <div style="font-size:1.45rem;font-weight:800;color:#F0C97A;">🍷 PREMIUM WINES</div>
            <div style="color:#E0D8D3;margin-top:3px;">Escanear pallet</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption("Aponte a câmera para o QR Code do próximo pallet.")
    components.html(
        """
        <div style="text-align:center;background:#272125;padding:14px;border-radius:14px;border:1px solid #534049;">
            <div id="reader_publico" style="width:100%;max-width:430px;margin:auto;border-radius:10px;overflow:hidden;"></div>
            <p id="resultado_publico" style="font-weight:700;color:#F0C97A;margin-top:10px;"></p>
        </div>
        <script src="https://unpkg.com/html5-qrcode"></script>
        <script>
        let concluiu = false;
        function sucesso(decodedText) {
            if (concluiu) return;
            concluiu = true;
            document.getElementById('resultado_publico').innerText = 'QR lido. Abrindo pallet...';
            const url = new URL(window.parent.location.href);
            url.search = '';
            url.searchParams.set('pallet', decodedText);
            url.searchParams.set('public', '1');
            const ir = () => { window.parent.location.href = url.toString(); };
            if (window.readerPublico) {
                window.readerPublico.stop().then(ir).catch(ir);
            } else { ir(); }
        }
        try {
            const reader = new Html5Qrcode('reader_publico');
            window.readerPublico = reader;
            reader.start(
                { facingMode: 'environment' },
                { fps: 10, qrbox: { width: 260, height: 260 } },
                sucesso
            ).catch(() => {
                document.getElementById('resultado_publico').innerText = 'Não foi possível iniciar a câmera.';
            });
        } catch (e) {}
        </script>
        """,
        height=500,
    )
    st.stop()

# ------------------------------------------------------------
# CONSULTA PÚBLICA DO PALLET PELO QR CODE
# Não exige login e é somente leitura.
# ------------------------------------------------------------
_pallet_publico_param = qp.get("pallet", None)
if _pallet_publico_param:
    _id_publico = extrair_id_do_qr(_pallet_publico_param)
    _dados_publicos = dados_posicao_pallet_id(_id_publico)
    _vinhos_pub = vinhos_atuais_da_posicao(_id_publico, st.session_state.estoque)

    components.html(
        """
        <script>
        try {
            const doc = window.parent.document;
            doc.querySelectorAll('link[rel="manifest"]').forEach(el => el.remove());
            doc.querySelectorAll('meta[name="mobile-web-app-capable"], meta[name="apple-mobile-web-app-capable"]').forEach(el => el.remove());
        } catch (e) {}
        </script>
        """,
        height=0,
    )

    st.markdown(
        """
        <style>
        [data-testid='stSidebar']{display:none!important;}
        [data-testid='stHeader']{display:none!important;}
        .block-container{padding-top:1.2rem!important;max-width:900px!important;}
        .stApp{background:linear-gradient(135deg,#21181C,#2A2024)!important;}
        </style>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div style="background:linear-gradient(135deg,#2B2024,#3A1823);border:1px solid #735063;border-radius:18px;padding:22px 24px;margin-bottom:18px;">
            <div style="font-size:1.45rem;font-weight:800;color:#F0C97A;">🍷 PREMIUM WINES</div>
            <div style="color:#E0D8D3;margin-top:3px;">Consulta do pallet</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if _dados_publicos:
        _corredor_pub = html.escape(_dados_publicos["corredor"])
        _pallet_nome_pub = html.escape(_dados_publicos["pallet"])
        _lado_pub = html.escape(_dados_publicos["lado"])
        st.markdown(
            f"""
            <div style="background:#272125;border:1px solid #534049;border-radius:16px;padding:18px 20px;margin-bottom:16px;">
                <div style="color:#F0C97A;font-size:1.15rem;font-weight:800;">📍 {_corredor_pub} • {_pallet_nome_pub} • {_lado_pub}</div>
                <div style="color:#D6CCC7;margin-top:6px;">{len(_vinhos_pub)} vinho(s) nesta posição</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if _vinhos_pub:
            st.markdown("### Vinhos nesta posição")
            for _i, _vinho in enumerate(_vinhos_pub, start=1):
                _nome = html.escape(str(_vinho.get("nome", "Vinho")))
                _safra = html.escape(str(_vinho.get("safra", "N/A")))
                _lit = html.escape(str(_vinho.get("litragem", "") or ""))
                _lit_html = f" • {_lit}" if _lit else ""
                st.markdown(
                    f"""
                    <div style="background:#272125;border:1px solid #534049;border-radius:12px;padding:14px 16px;margin:8px 0;">
                        <div style="font-weight:750;color:#F5F0EC;">{_i}. {_nome}</div>
                        <div style="color:#CFC4BE;margin-top:3px;">Safra: {_safra}{_lit_html}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.info("Nenhum vinho cadastrado nesta posição no momento.")
    else:
        st.error("QR Code de pallet inválido.")

    st.markdown("---")
    if st.button(
        "📷 Escanear outro pallet",
        key="btn_publico_escanear_outro_pallet",
        use_container_width=True,
    ):
        st.query_params.clear()
        st.query_params["scan_pallet"] = "1"
        st.rerun()
    st.stop()

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
            st.session_state.menu_atual = "PedidosMatriz"
            st.session_state["checkout_forcar_aba"] = True
            st.session_state["checkout_codigo_pendente"] = valor_limpo
            st.session_state["checkout_auto_conferir"] = True

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

instalar_atalhos_teclado()

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
    st.markdown('<div class="sidebar-section">Estoque</div>', unsafe_allow_html=True)
    if st.button("🍷  Estoque / Buscar", use_container_width=True, key="nav_estoque_busca"):
        st.session_state.menu_atual = "Filtros"; st.rerun()
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
    # Conta como pendente somente o que realmente estiver com status Pendente.
    # Pedidos já "Concluído / Expedido" não entram mais neste indicador.
    pedidos_pendentes = sum(
        1
        for p in st.session_state.get("pedidos", [])
        if normalizar_nome_vinho(str(p.get("status", "Pendente"))) == "pendente"
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
    c1, c2 = st.columns(2)
    with c1:
        st.markdown('<div class="action-card"><div class="action-icon">📦</div><div class="action-title">Checkout de Expedição</div><div class="action-desc">Separar, conferir e finalizar pedidos.</div></div>', unsafe_allow_html=True)
        if st.button("Abrir Checkout", use_container_width=True, key="home_checkout"):
            st.session_state.menu_atual = "PedidosMatriz"; st.rerun()
    with c2:
        st.markdown('<div class="action-card"><div class="action-icon">🏢</div><div class="action-title">Painel da Matriz</div><div class="action-desc">Visualizar pedidos recebidos e andamento.</div></div>', unsafe_allow_html=True)
        if st.button("Abrir Painel", use_container_width=True, key="home_painel"):
            st.session_state.menu_atual = "PainelMatriz"; st.rerun()

    st.markdown('<div class="section-title">Estoque & Localização</div>', unsafe_allow_html=True)
    c4, c5, c6 = st.columns(3)
    with c4:
        st.markdown('<div class="action-card"><div class="action-icon">🍷</div><div class="action-title">Estoque / Buscar</div><div class="action-desc">Consultar todo o estoque e localizar vinhos rapidamente.</div></div>', unsafe_allow_html=True)
        if st.button("Abrir Estoque", use_container_width=True, key="home_estoque_busca"):
            st.session_state.menu_atual = "Filtros"; st.rerun()
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

    # Se já existe resultado, escondemos a câmera para deixar a consulta limpa.
    codigo_ja_lido = str(st.session_state.get("qr_pallet_lido", "") or "").strip()

    if not codigo_ja_lido:
        modo_leitura = st.radio(
            "Forma de leitura:",
            ["📷 Câmera do celular", "⌨️ Digitar código"],
            horizontal=True,
            key="modo_leitura_qr_pallet",
        )

        codigo_lido = ""
        if modo_leitura == "📷 Câmera do celular":
            componente_leitor_qr("leitor_pallet", tela_retorno="LerQRPallet")
            codigo_lido = str(st.session_state.get("qr_pallet_lido", "") or "").strip()
        else:
            codigo_lido = st.text_input(
                "Digite o código do pallet",
                placeholder="Ex.: C01-P04-D",
                key="codigo_digitado_pallet",
            ).strip()
    else:
        codigo_lido = codigo_ja_lido

    if codigo_lido:
        # Aceita tanto o código C01-P01-D quanto a URL pública completa do QR.
        codigo_posicao = extrair_id_do_qr(codigo_lido)
        dados_posicao = dados_posicao_pallet_id(codigo_posicao)
        vinhos = vinhos_atuais_da_posicao(codigo_posicao, st.session_state.estoque)

        if dados_posicao:
            st.markdown(
                f"""
                <div class="pallet-header">
                    <div style="font-size:0.9rem;opacity:0.85;">POSIÇÃO IDENTIFICADA</div>
                    <div style="font-size:1.6rem;font-weight:700;">📍 {html.escape(dados_posicao['corredor'])}</div>
                    <div style="font-size:1.2rem;">{html.escape(dados_posicao['pallet'])} &nbsp; | &nbsp; {html.escape(dados_posicao['lado'])}</div>
                    <div style="margin-top:8px;font-size:0.85rem;opacity:0.8;">Código: {html.escape(dados_posicao['id'])}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.markdown("### 🍷 Vinhos neste pallet")
            if not vinhos:
                st.info("Nenhum vinho cadastrado neste pallet.")
            else:
                st.success(f"{len(vinhos)} vinho(s) cadastrado(s) nesta posição.")
                for vinho in vinhos:
                    lit = str(vinho.get("litragem", "") or "").strip()
                    lit_html = f" • {html.escape(lit)}" if lit else ""
                    st.markdown(
                        f"""
                        <div class="wine-item">
                            <div style="color:#D6AE63;font-size:1.05rem;font-weight:700;">🍷 {html.escape(vinho.get('nome',''))}</div>
                            <div style="color:#AFA6A0;margin-top:3px;">Safra: <b>{html.escape(vinho.get('safra','N/A'))}</b>{lit_html}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
        else:
            st.error(f"O QR Code {html.escape(str(codigo_lido))} não contém uma posição de pallet válida.")

        def _nova_leitura_pallet():
            st.session_state["qr_pallet_lido"] = ""
            st.session_state["modo_leitura_qr_pallet"] = "📷 Câmera do celular"
            st.session_state.pop("codigo_digitado_pallet", None)
            try:
                if "scanned_leitor_pallet" in st.query_params:
                    del st.query_params["scanned_leitor_pallet"]
            except Exception:
                pass

        st.markdown("---")
        st.button(
            "📷 Escanear outro pallet",
            key="btn_escanear_outro_pallet",
            use_container_width=True,
            on_click=_nova_leitura_pallet,
            help="Limpa este resultado e abre novamente a câmera para ler o próximo pallet.",
        )


# ============================================================
# GERAR QR PALLETS
# ============================================================

elif st.session_state.menu_atual == "GerarQRPallets":

    render_page_header("🏷️", "Gerar QR dos Pallets", "", "Estoque • Identificação")

    if not QRCODE_DISPONIVEL:
        st.error("A biblioteca qrcode não está instalada.")
        st.code("pip install qrcode[pil]")
    else:
        modo_qr = st.radio(
            "Modo de geração",
            ["Um pallet", "Vários pallets"],
            horizontal=True,
            key="modo_geracao_qr",
        )

        if modo_qr == "Um pallet":
            col1, col2, col3 = st.columns(3)
            with col1:
                corredor_qr = st.selectbox("Corredor", LISTA_CORREDORES, key="qr_corredor")
            with col2:
                pallet_qr = st.selectbox("Pallet", LISTA_PALLETS, key="qr_pallet")
            with col3:
                lado_qr = st.selectbox("Lado", LISTA_LADOS, key="qr_lado")

            id_qr = gerar_id_pallet(corredor_qr, pallet_qr, lado_qr)
            pallet_preview = obter_pallet(st.session_state.pallets, id_qr)
            vinhos_preview = pallet_preview.get("vinhos", []) if pallet_preview else []

            resumo = (
                '<div style="background:#17171b;border:1px solid #34343b;border-radius:14px;padding:18px 20px;margin:14px 0;">'
                f'<div style="font-size:1.05rem;font-weight:700;color:#f3c45b;">📍 {html.escape(corredor_qr)} • {html.escape(pallet_qr)} • {html.escape(lado_qr)}</div>'
                f'<div style="margin-top:6px;color:#c9c9cf;">{len(vinhos_preview)} vinho(s) nesta posição</div>'
                '</div>'
            )
            st.markdown(resumo, unsafe_allow_html=True)

            with st.expander("🍷 Ver vinhos deste pallet"):
                if vinhos_preview:
                    for numero, vinho_preview in enumerate(vinhos_preview, start=1):
                        nome_preview = str(vinho_preview.get("nome", "")).strip() or "Vinho sem nome"
                        safra_preview = str(vinho_preview.get("safra", "N/A")).strip() or "N/A"
                        st.markdown(f"**{numero}. {nome_preview}** — Safra **{safra_preview}**")
                else:
                    st.caption("Nenhum vinho cadastrado nesta posição no momento.")

            if st.button("🏷️ Gerar QR Code", use_container_width=True, key="gerar_qr_unico"):
                pallet_obj = criar_ou_atualizar_pallet(corredor_qr, pallet_qr, lado_qr, st.session_state.pallets)
                salvar_pallets(st.session_state.pallets)
                caminho_qr = gerar_qr_pallet(id_qr, pallet_obj)
                if caminho_qr and os.path.exists(caminho_qr):
                    registrar_log(st.session_state.usuario_logado.get("nome", "Usuário"), "Gerou QR Code de Pallet", f"Posição: {id_qr}")
                    st.success(f"QR Code {id_qr} gerado com sucesso.")
                    st.image(caminho_qr, width=280)
                    with open(caminho_qr, "rb") as arquivo_qr:
                        st.download_button("⬇️ Baixar QR Code", data=arquivo_qr.read(), file_name=f"QR_{id_qr}.png", mime="image/png", use_container_width=True, key=f"download_qr_{id_qr}")
                else:
                    st.error("Não foi possível gerar o QR Code.")

        else:
            st.markdown("### 🖨️ Gerar vários QR Codes")
            col1, col2 = st.columns(2)
            with col1:
                corredor_lote = st.selectbox("Corredor", LISTA_CORREDORES, key="qr_lote_corredor")
            with col2:
                lado_lote = st.selectbox("Lado", LISTA_LADOS, key="qr_lote_lado")

            numeros_pallets = [_numero_de_texto(p) or i + 1 for i, p in enumerate(LISTA_PALLETS)]
            minimo_pallet = min(numeros_pallets) if numeros_pallets else 1
            maximo_pallet = max(numeros_pallets) if numeros_pallets else 20

            cini, cfim = st.columns(2)
            with cini:
                pallet_inicio = st.number_input("Do pallet", min_value=int(minimo_pallet), max_value=int(maximo_pallet), value=int(minimo_pallet), step=1, key="qr_lote_inicio")
            with cfim:
                pallet_fim = st.number_input("Até o pallet", min_value=int(minimo_pallet), max_value=int(maximo_pallet), value=int(min(int(maximo_pallet), 20)), step=1, key="qr_lote_fim")

            if pallet_inicio > pallet_fim:
                st.warning("O pallet inicial precisa ser menor ou igual ao pallet final.")
            else:
                qtd_qrs = int(pallet_fim - pallet_inicio + 1)
                st.caption(f"Serão gerados {qtd_qrs} QR Codes em um arquivo A4 pronto para impressão.")

                if st.button("🖨️ Preparar QR Codes para imprimir", use_container_width=True, key="gerar_qr_lote"):
                    try:
                        # A4 em 150 DPI: 1240 x 1754 px. Grade 4x5 = 20 etiquetas por página.
                        page_w, page_h = 1240, 1754
                        cols, rows = 4, 5
                        cell_w, cell_h = page_w // cols, page_h // rows
                        margem = 16
                        qr_size = min(cell_w - 48, cell_h - 86)
                        paginas = []

                        try:
                            fonte = ImageFont.truetype("DejaVuSans-Bold.ttf", 24)
                            fonte_peq = ImageFont.truetype("DejaVuSans.ttf", 19)
                        except Exception:
                            fonte = ImageFont.load_default()
                            fonte_peq = ImageFont.load_default()

                        ids_gerados = []
                        pagina = Image.new("RGB", (page_w, page_h), "white")
                        draw = ImageDraw.Draw(pagina)
                        pos = 0

                        for numero in range(int(pallet_inicio), int(pallet_fim) + 1):
                            pallet_nome = f"Pallet {numero:02d}"
                            if pallet_nome not in LISTA_PALLETS:
                                continue

                            id_lote = gerar_id_pallet(corredor_lote, pallet_nome, lado_lote)
                            pallet_obj = criar_ou_atualizar_pallet(corredor_lote, pallet_nome, lado_lote, st.session_state.pallets)
                            caminho_qr = gerar_qr_pallet(id_lote, pallet_obj)
                            if not caminho_qr or not os.path.exists(caminho_qr):
                                continue

                            if pos > 0 and pos % (cols * rows) == 0:
                                paginas.append(pagina)
                                pagina = Image.new("RGB", (page_w, page_h), "white")
                                draw = ImageDraw.Draw(pagina)

                            idx_pagina = pos % (cols * rows)
                            linha = idx_pagina // cols
                            coluna = idx_pagina % cols
                            x0 = coluna * cell_w
                            y0 = linha * cell_h

                            # Contorno fino facilita recortar sem prejudicar o QR.
                            draw.rectangle([x0 + margem, y0 + margem, x0 + cell_w - margem, y0 + cell_h - margem], outline="black", width=1)

                            resample_nearest = getattr(getattr(Image, "Resampling", Image), "NEAREST", Image.NEAREST)
                            qr_img = Image.open(caminho_qr).convert("RGB").resize((qr_size, qr_size), resample_nearest)
                            qx = x0 + (cell_w - qr_size) // 2
                            qy = y0 + 20
                            pagina.paste(qr_img, (qx, qy))

                            texto1 = id_lote
                            texto2 = f"{corredor_lote} • {pallet_nome} • {lado_lote}"
                            b1 = draw.textbbox((0, 0), texto1, font=fonte)
                            b2 = draw.textbbox((0, 0), texto2, font=fonte_peq)
                            draw.text((x0 + (cell_w - (b1[2]-b1[0]))/2, y0 + qr_size + 28), texto1, fill="black", font=fonte)
                            draw.text((x0 + (cell_w - (b2[2]-b2[0]))/2, y0 + qr_size + 58), texto2, fill="black", font=fonte_peq)

                            ids_gerados.append(id_lote)
                            pos += 1

                        if pos % (cols * rows) != 0 or not paginas:
                            paginas.append(pagina)

                        salvar_pallets(st.session_state.pallets)

                        if not ids_gerados:
                            st.error("Nenhum QR Code pôde ser gerado para o intervalo informado.")
                        else:
                            pdf_buffer = BytesIO()
                            primeira = paginas[0].convert("RGB")
                            restantes = [pg.convert("RGB") for pg in paginas[1:]]
                            primeira.save(pdf_buffer, format="PDF", save_all=True, append_images=restantes, resolution=150.0)
                            pdf_bytes = pdf_buffer.getvalue()

                            registrar_log(
                                st.session_state.usuario_logado.get("nome", "Usuário"),
                                "Gerou QR Codes em lote",
                                f"{corredor_lote} | Pallets {int(pallet_inicio):02d} a {int(pallet_fim):02d} | {lado_lote} | {len(ids_gerados)} QR(s)",
                            )
                            st.success(f"{len(ids_gerados)} QR Codes preparados para impressão.")
                            st.download_button(
                                "⬇️ Baixar PDF para imprimir",
                                data=pdf_bytes,
                                file_name=f"QR_{corredor_lote.replace(' ', '_')}_P{int(pallet_inicio):02d}-P{int(pallet_fim):02d}_{lado_lote.replace(' / ', '_').replace(' ', '_')}.pdf",
                                mime="application/pdf",
                                use_container_width=True,
                                key="download_qr_lote_pdf",
                            )
                    except Exception as e:
                        st.error(f"Não foi possível preparar os QR Codes em lote: {e}")

elif st.session_state.menu_atual == "GerenciarPallets":

    render_page_header("🗂️", "Gerenciar Pallets e Vinhos", "Organize os vinhos por corredor, pallet e lado. As movimentações atualizam a localização em todo o sistema.", "Estoque • Organização")

    st.info(
        "Ao mover um vinho por aqui, a localização também é atualizada "
        "automaticamente no Estoque / Buscar e no cadastro do vinho."
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

    render_page_header(
        "🏢",
        "Painel da Matriz",
        "Filtre por número do pedido, data ou status e veja somente os pedidos que procura.",
        "Operação • Acompanhamento",
    )

    if not st.session_state.pedidos:
        st.info("Nenhum pedido registrado no sistema.")

    else:
        st.markdown("### 🔎 Localizar pedidos")
        st.caption(
            "Você pode usar apenas um filtro ou combinar vários. Ex.: somente Status = Pendente, somente uma data, ou o número 123002."
        )

        col_numero, col_data, col_status = st.columns([1.5, 1.25, 1.25])

        with col_numero:
            filtro_numero = st.text_input(
                "Número do pedido",
                placeholder="Ex.: 123002",
                key="filtro_numero_painel_matriz",
            ).strip()

        with col_data:
            filtro_data = st.text_input(
                "Data",
                placeholder="Ex.: 10/09/2026",
                key="filtro_data_painel_matriz",
            ).strip()

        with col_status:
            filtro_status_painel = st.selectbox(
                "Status",
                ["Escolher...", "Todos", "Pendente", "Concluído / Expedido", "Concluído com Divergência"],
                key="filtro_status_painel_matriz_v2",
            )

        # Um filtro já é suficiente para mostrar a lista. Não é necessário
        # preencher o número do pedido para pesquisar por status ou data.
        tem_filtro = bool(filtro_numero or filtro_data or filtro_status_painel != "Escolher...")

        if not tem_filtro:
            st.info("Escolha um status ou informe a data ou o número do pedido para mostrar a lista.")
        else:
            pedidos_filtrados = []
            termo_numero = normalizar_nome_vinho(filtro_numero) if filtro_numero else ""
            data_procurada = filtro_data.replace("-", "/").strip()

            for p in st.session_state.pedidos:
                status_p = str(p.get("status", "Pendente")).strip()
                status_norm = normalizar_nome_vinho(status_p)

                # Filtro por status
                if filtro_status_painel not in ["Escolher...", "Todos"]:
                    if status_norm != normalizar_nome_vinho(filtro_status_painel):
                        continue

                # Filtro por número do pedido
                if termo_numero:
                    id_pedido = normalizar_nome_vinho(str(p.get("id", "")))
                    if termo_numero not in id_pedido:
                        continue

                # Filtro por data. O pedido normalmente guarda "DD/MM/AAAA HH:MM".
                if data_procurada:
                    data_pedido = str(p.get("data", "")).strip()
                    data_pedido_norm = data_pedido.replace("-", "/")
                    if data_procurada not in data_pedido_norm:
                        continue

                pedidos_filtrados.append(p)

            if not pedidos_filtrados:
                st.warning("Nenhum pedido encontrado com os filtros selecionados.")
            else:
                st.success(f"{len(pedidos_filtrados)} pedido(s) encontrado(s).")

                # Lista compacta: cada pedido aparece fechado e só abre quando o usuário clicar.
                # Isso evita uma tela enorme quando há muitos resultados.
                for p in pedidos_filtrados:
                    status_p = str(p.get("status", "Pendente"))
                    pedido_id = str(p.get("id", ""))
                    pedido_data = str(p.get("data", ""))
                    total_itens = len(p.get("itens", []))

                    resumo = f"Pedido {pedido_id}  •  {pedido_data}  •  {status_p}  •  {total_itens} item(ns)"
                    with st.expander(resumo, expanded=False):
                        status_norm_p = normalizar_nome_vinho(status_p)
                        if status_norm_p == normalizar_nome_vinho("Concluído / Expedido"):
                            status_col = "#66C38A"
                        elif status_norm_p == normalizar_nome_vinho("Concluído com Divergência"):
                            status_col = "#F3C45B"
                        else:
                            status_col = "#E0A95A"

                        st.markdown(
                            f"""
                            <div style="
                                background:linear-gradient(180deg,#19191D,#141417);
                                padding:14px 16px;
                                border-radius:14px;
                                border:1px solid #2E2E34;
                                margin:2px 0 12px 0;
                            ">
                                <div style="font-size:1rem;font-weight:800;color:#F7F3EE;">
                                    Mapa / Pedido Nº {html.escape(pedido_id)}
                                </div>
                                <div style="margin-top:7px;color:#BDB4AE;font-size:.88rem;">
                                    Data: {html.escape(pedido_data)}
                                    &nbsp;&nbsp;•&nbsp;&nbsp;
                                    Status: <b style="color:{status_col};">{html.escape(status_p)}</b>
                                </div>
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                        df_itens = []
                        for item in p.get("itens", []):
                            dif = int(item.get("divergencia", 0) or 0)
                            if dif > 0:
                                dif_str = f"({dif:+d}) ⚠️ Excedente"
                            elif dif < 0:
                                dif_str = f"({dif}) ⚠️ Falta"
                            else:
                                dif_str = "(0) Correto"

                            df_itens.append({
                                "Produto": item.get("nome", ""),
                                "Safra": item.get("safra", "N/A"),
                                "Origem": "Fora da lista / Extra" if item.get("fora_lista", False) else "Pedido original",
                                "Qtd Pedida": item.get("quantidade", 0),
                                "Qtd Separada": item.get("qtd_separada", 0),
                                "Divergência": dif_str,
                            })

                        if df_itens:
                            st.dataframe(
                                pd.DataFrame(df_itens),
                                use_container_width=True,
                                hide_index=True,
                            )
                        else:
                            st.caption("Este pedido não possui itens cadastrados.")


# ============================================================
# PEDIDOS MATRIZ
# ============================================================

elif st.session_state.menu_atual == "PedidosMatriz":

    render_page_header("📦", "Checkout de Expedição", "Crie pedidos, faça a separação, confira por código de barras e trate divergências antes da expedição.", "Operação • Separação")

    _msg_pedido_salvo = st.session_state.pop("mensagem_pedido_salvo", None)
    if _msg_pedido_salvo:
        st.success(_msg_pedido_salvo)

    if st.session_state.pop("_limpar_pedido_apos_salvar", False):
        st.session_state.itens_pedido_scanner = []
        for _chave_limpar in [
            "id_novo_pedido", "modo_novo_pedido",
            "texto_manual_novo_pedido", "codigo_manual_lista_pedido",
            "qtd_lista_pedido", "mensagem_adicao_pedido", "itens_pedido_retomados",
        ]:
            st.session_state.pop(_chave_limpar, None)

    aba_ped1, aba_ped2 = st.tabs(
        [
            "📋 Enviar / Cadastrar / Excluir Pedidos",
            "🔍 Conferência (Checkout de Expedição)"
        ]
    )

    if st.session_state.get("checkout_forcar_aba"):
        components.html(
            """
            <script>
            setTimeout(() => {
                try {
                    const tabs = Array.from(window.parent.document.querySelectorAll('[data-baseweb="tab"]'));
                    const alvo = tabs.find(t => (t.innerText || '').toLowerCase().includes('conferência'));
                    if (alvo) alvo.click();
                } catch (e) {}
            }, 250);
            </script>
            """,
            height=0,
        )
        st.session_state["checkout_forcar_aba"] = False

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
            if "arquivo_pedido_versao" not in st.session_state:
                st.session_state.arquivo_pedido_versao = 0
            arq_pedido = st.file_uploader(
                "Arquivo de Pedido (Excel ou TXT)",
                type=["xlsx", "xls", "txt"],
                key=f"arquivo_novo_pedido_{st.session_state.arquivo_pedido_versao}",
            )
            if st.button("💾 Salvar Pedido do Arquivo", use_container_width=True):
                itens_novos = (
                    extrair_pedidos_de_arquivo(arq_pedido)
                    if arq_pedido is not None else []
                )

        elif modo_novo_pedido == "⌨️ Digitar manualmente":
            st.caption("Digite o vinho e clique em Adicionar. Depois de incluir na lista, o campo será limpo automaticamente.")
            st.text_area(
                "Digite o vinho",
                placeholder="Ex.: Faleria Pinot Noir Reserva 2023 / 1 Caixa",
                key="texto_manual_novo_pedido",
                height=90,
            )
            st.button(
                "➕ Adicionar à lista",
                use_container_width=True,
                key="btn_adicionar_manual_pedido",
                on_click=callback_adicionar_manual_pedido,
            )

            mensagem_pedido = st.session_state.pop("mensagem_adicao_pedido", None)
            if mensagem_pedido:
                sucesso_msg, texto_msg = mensagem_pedido
                if sucesso_msg:
                    st.success(texto_msg)
                else:
                    st.error(texto_msg)

            lista_manual = st.session_state.itens_pedido_scanner
            st.markdown("#### 🛒 Lista do pedido")
            if not lista_manual:
                st.info("A lista ainda está vazia. Adicione o primeiro vinho.")
            else:
                for idx, item in enumerate(list(lista_manual)):
                    c_info, c_del = st.columns([6, 1])
                    with c_info:
                        st.markdown(
                            f"**{idx + 1}. {item.get('nome','')}** — "
                            f"Safra {item.get('safra','N/A')} — "
                            f"Qtd: **{item.get('quantidade',1)}**"
                        )
                    with c_del:
                        if st.button("🗑️", key=f"del_item_manual_{idx}"):
                            lista_manual.pop(idx)
                            st.rerun()

                c_limpar, c_salvar = st.columns(2)
                with c_limpar:
                    if st.button("🧹 Limpar lista", key="limpar_lista_manual", use_container_width=True):
                        st.session_state.itens_pedido_scanner = []
                        st.rerun()
                with c_salvar:
                    if st.button("💾 Salvar Pedido da Lista", key="salvar_lista_manual", use_container_width=True):
                        itens_novos = [dict(item) for item in lista_manual]

        else:
            st.success(
                "📷 Modo corredor: aponte a câmera para o código de barras da garrafa. "
                "O vinho será incluído na lista do pedido."
            )

            componente_leitor_codigo_barras(
                "pedido_scanner",
                tela_retorno="PedidosMatriz",
            )

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
                st.button(
                    "➕ Adicionar",
                    use_container_width=True,
                    key="btn_adicionar_codigo_pedido",
                    on_click=callback_adicionar_codigo_pedido,
                )

            mensagem_pedido = st.session_state.pop("mensagem_adicao_pedido", None)
            if mensagem_pedido:
                sucesso_msg, texto_msg = mensagem_pedido
                if sucesso_msg:
                    st.success(texto_msg)
                else:
                    st.error(texto_msg)

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
            id_pedido_limpo = str(id_pedido).strip()
            pedido_id_existente = next(
                (p for p in st.session_state.pedidos if str(p.get("id", "")).strip() == id_pedido_limpo),
                None,
            )
            if not id_pedido_limpo:
                st.error("Informe a identificação do pedido.")
            elif pedido_id_existente is not None:
                st.error(
                    f"Já existe um pedido com o número {id_pedido_limpo}. "
                    "Para evitar duplicidade, o sistema não permite salvar outro pedido com o mesmo número."
                )
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
                    # Limpa completamente a montagem do pedido para impedir
                    # clique duplo/reenvio acidental do mesmo arquivo ou lista.
                    st.session_state.itens_pedido_scanner = []
                    st.session_state.arquivo_pedido_versao = int(
                        st.session_state.get("arquivo_pedido_versao", 0)
                    ) + 1
                    st.session_state["_limpar_pedido_apos_salvar"] = True
                    st.session_state.pop("rascunho_pedido_pendente", None)
                    st.session_state["mensagem_pedido_salvo"] = f"Pedido {id_pedido_limpo} salvo no sistema!"
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

            # No checkout exibimos somente pedidos que ainda precisam de conferência.
            # Assim que um pedido é finalizado, ele desaparece desta tela automaticamente.
            pedidos_pendentes_checkout = [
                p
                for p in st.session_state.pedidos
                if not normalizar_nome_vinho(str(p.get("status", "Pendente"))).startswith("concluido")
            ]

            mapas_disponiveis = [p["id"] for p in pedidos_pendentes_checkout]

            if not mapas_disponiveis:
                st.success("✅ Não há pedidos pendentes para conferência.")
                st.info("Quando um novo pedido for cadastrado, ele aparecerá aqui automaticamente.")
                st.stop()

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

                status_norm_atual = normalizar_nome_vinho(status_atual)
                if status_norm_atual == normalizar_nome_vinho("Concluído / Expedido"):
                    cor_status = "#2E7D32"
                elif status_norm_atual == normalizar_nome_vinho("Concluído com Divergência"):
                    cor_status = "#C58A18"
                else:
                    cor_status = "#7A1C2E"

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

                with st.expander("➕ Adicionar vinho extra / fora da lista", expanded=False):
                    st.caption(
                        "Use quando a matriz solicitar um vinho que não estava no pedido original. "
                        "Ele será acrescentado ao mesmo pedido e ficará identificado no Painel da Matriz como 'Fora da lista / Extra'."
                    )
                    col_extra1, col_extra2, col_extra3 = st.columns([2, 1, 1])
                    with col_extra1:
                        extra_busca = st.text_input(
                            "Nome ou código de barras do vinho extra",
                            key=f"extra_busca_{pedido_ativo['id']}",
                            placeholder="Digite o nome ou bipe o código",
                        ).strip()
                    with col_extra2:
                        extra_qtd = st.number_input(
                            "Quantidade extra", min_value=1, value=1, step=1,
                            key=f"extra_qtd_{pedido_ativo['id']}"
                        )
                    with col_extra3:
                        st.write("")
                        st.write("")
                        adicionar_extra = st.button(
                            "Adicionar extra",
                            key=f"btn_extra_{pedido_ativo['id']}",
                            use_container_width=True,
                        )

                    if adicionar_extra:
                        if not extra_busca:
                            st.error("Informe o nome ou o código de barras do vinho.")
                        else:
                            busca_norm = normalizar_nome_vinho(extra_busca)
                            vinho_extra = next(
                                (
                                    v for v in st.session_state.estoque
                                    if str(v.get("codigo_barras", "")).strip() == extra_busca
                                    or busca_norm == normalizar_nome_vinho(v.get("nome", ""))
                                ),
                                None,
                            )
                            if vinho_extra is None:
                                st.error("Este vinho não está cadastrado no estoque.")
                            else:
                                ja_no_pedido = next(
                                    (i for i in pedido_ativo.get("itens", [])
                                     if normalizar_nome_vinho(i.get("nome", "")) == normalizar_nome_vinho(vinho_extra.get("nome", ""))),
                                    None,
                                )
                                if ja_no_pedido is not None:
                                    st.warning(
                                        "Este vinho já faz parte do pedido. Se vier quantidade maior, "
                                        "faça a conferência com a quantidade real; o sistema registrará a divergência excedente."
                                    )
                                else:
                                    pedido_ativo.setdefault("itens", []).append({
                                        "nome": vinho_extra.get("nome", ""),
                                        "safra": vinho_extra.get("safra", ""),
                                        "quantidade": int(extra_qtd),
                                        "separado": False,
                                        "qtd_separada": 0,
                                        "divergencia": 0,
                                        "autorizado_divergencia": False,
                                        "fora_lista": True,
                                        "origem": "Extra solicitado durante checkout",
                                    })
                                    salvar_pedidos(st.session_state.pedidos)
                                    registrar_log(
                                        st.session_state.usuario_logado["nome"],
                                        "Adicionou item extra ao pedido",
                                        f"Pedido {pedido_ativo['id']} | {vinho_extra.get('nome','')} | Qtd {int(extra_qtd)}",
                                    )
                                    st.success("Vinho extra acrescentado ao mesmo pedido.")
                                    st.rerun()

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

                    componente_leitor_codigo_barras(
                        "checkout_camera",
                        tela_retorno="PedidosMatriz",
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

                                def _checkout_codigo_digitado():
                                    valor = str(
                                        st.session_state.get(
                                            "input_bipagem_checkout", ""
                                        )
                                    ).strip()
                                    if valor:
                                        # on_change é disparado tanto ao pressionar ENTER
                                        # quanto ao sair do campo com TAB/leitor USB.
                                        st.session_state["checkout_codigo_pendente"] = valor
                                        st.session_state["checkout_auto_conferir"] = True
                                        st.session_state["input_bipagem_checkout"] = ""

                                cod_barras_input = st.text_input(
                                    "*Ou digite/bipe o Código",
                                    key="input_bipagem_checkout",
                                    on_change=_checkout_codigo_digitado,
                                    help="Digite ou bipe o código e pressione Enter ou Tab para conferir."
                                )

                                if st.session_state.get("checkout_auto_conferir"):
                                    cod_barras_input = str(
                                        st.session_state.get(
                                            "checkout_codigo_pendente", ""
                                        )
                                    ).strip()

                        else:

                            def _checkout_codigo_digitado_sem_lista():
                                valor = str(
                                    st.session_state.get(
                                        "input_bipagem_checkout", ""
                                    )
                                ).strip()
                                if valor:
                                    st.session_state["checkout_codigo_pendente"] = valor
                                    st.session_state["checkout_auto_conferir"] = True
                                    st.session_state["input_bipagem_checkout"] = ""

                            cod_barras_input = st.text_input(
                                "*Código de Barras ou Nome",
                                key="input_bipagem_checkout",
                                on_change=_checkout_codigo_digitado_sem_lista,
                                help="Digite ou bipe o código e pressione Enter ou Tab para conferir."
                            )

                            if st.session_state.get("checkout_auto_conferir"):
                                cod_barras_input = str(
                                    st.session_state.get(
                                        "checkout_codigo_pendente", ""
                                    )
                                ).strip()

                if modo_leitura == "⌨️ Seleção / Pistola USB":
                    autofoco_campo_checkout()

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

                auto_conferir = bool(
                    st.session_state.get("checkout_auto_conferir", False)
                )

                if (
                    (btn_conferir or auto_conferir)
                    and cod_barras_input
                ):
                    # Consome o disparo automático antes de processar para não repetir
                    # a conferência em um rerun posterior.
                    st.session_state["checkout_auto_conferir"] = False
                    st.session_state["checkout_codigo_pendente"] = ""

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

                        possui_divergencia_final = any(
                            int(i.get("divergencia", 0) or 0) != 0
                            for i in pedido_ativo.get("itens", [])
                        )
                        pedido_ativo["status"] = (
                            "Concluído com Divergência"
                            if possui_divergencia_final
                            else "Concluído / Expedido"
                        )

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

                        if possui_divergencia_final:
                            st.success("✅ Expedição concluída com divergência registrada.")
                        else:
                            st.success("🎉 Expedição concluída!")

                        st.rerun()

                else:

                    st.warning(
                        "⚠️ Todos os itens precisam "
                        "ser conferidos."
                    )


# ============================================================
# FILTROS
# ============================================================

elif st.session_state.menu_atual in ["Filtros", "Estoque"]:

    render_page_header("🍷", "Estoque e Busca", "Consulte o estoque completo ou encontre um vinho rapidamente.", "Estoque • Consulta")

    col_f1, col_f2 = st.columns([2, 1])
    with col_f1:
        termo = st.text_input(
            "Pesquisar por nome, tipo, safra, localização ou código de barras",
            value=st.session_state.get("termo_busca", ""),
            key="estoque_busca_termo",
        )
    with col_f2:
        tipo_filtro = st.selectbox(
            "Tipo",
            ["Todos", "Tinto", "Branco", "Rosé", "Espumante", "Fortificado"],
            key="estoque_busca_tipo",
        )

    termo_norm = normalizar_nome_vinho(termo)
    resultados = []
    for v in st.session_state.estoque:
        campos = " ".join([
            str(v.get("nome", "")),
            str(v.get("tipo", "")),
            str(v.get("safra", "")),
            str(v.get("localizacao", "")),
            str(v.get("lado", "")),
            str(v.get("codigo_barras", "")),
        ])
        match_termo = not termo_norm or termo_norm in normalizar_nome_vinho(campos)
        match_tipo = tipo_filtro == "Todos" or v.get("tipo") == tipo_filtro
        if match_termo and match_tipo:
            resultados.append(v)

    st.markdown(f"**{len(resultados)} vinho(s) encontrado(s)**")

    if not resultados:
        st.info("Nenhum vinho encontrado.")
    else:
        df_estoque = pd.DataFrame([
            {
                "Nome": v.get("nome", ""),
                "Tipo": v.get("tipo", ""),
                "Safra": v.get("safra", ""),
                "Localização": v.get("localizacao", ""),
                "Lado": v.get("lado", ""),
                "Caixa": v.get("caixa", ""),
                "Litragem": v.get("litragem", ""),
                "Cód. Barras": v.get("codigo_barras", ""),
            }
            for v in resultados
        ])
        st.dataframe(df_estoque, use_container_width=True, hide_index=True)

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

    with st.form("form_cadastrar_vinho", clear_on_submit=True):
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

        col_cx1, col_cx2 = st.columns(2)
        with col_cx1:
            caixa = st.selectbox("Embalagem / Caixa", OPCOES_CAIXA)
        with col_cx2:
            litragem = st.selectbox("Litragem da Garrafa", LISTA_LITRAGENS)
        codigo_barras = st.text_input(
            "Código de Barras (Opcional)",
            help="Pode digitar ou bipar com a pistola USB.",
        ).strip()
        foto_upload = st.file_uploader(
            "📷 Imagem do vinho (opcional)",
            type=["jpg", "jpeg", "png", "webp"],
            key="foto_cadastro_vinho",
        )

        if st.form_submit_button("💾 Salvar Novo Vinho"):
            if not nome:
                st.error("Informe o nome do vinho.")
            else:
                duplicado_nome = next(
                    (
                        v for v in st.session_state.estoque
                        if normalizar_nome_vinho(v.get("nome", "")) == normalizar_nome_vinho(nome)
                        and str(v.get("safra", "")).strip() == str(safra).strip()
                    ),
                    None,
                )
                duplicado_codigo = (
                    next(
                        (
                            v for v in st.session_state.estoque
                            if codigo_barras and str(v.get("codigo_barras", "")).strip() == codigo_barras
                        ),
                        None,
                    )
                    if codigo_barras else None
                )
                if duplicado_nome:
                    st.error("Este vinho com a mesma safra já está cadastrado.")
                    st.stop()
                if duplicado_codigo:
                    st.error("Este código de barras já pertence a outro vinho cadastrado.")
                    st.stop()

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
                    "litragem": litragem,
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
            litragem_atual = vinho_obj.get("litragem", LISTA_LITRAGENS[2])
            col_ec1, col_ec2 = st.columns(2)
            with col_ec1:
                nova_caixa = st.selectbox(
                    "Embalagem / Caixa",
                    OPCOES_CAIXA,
                    index=OPCOES_CAIXA.index(caixa_atual) if caixa_atual in OPCOES_CAIXA else 0,
                )
            with col_ec2:
                nova_litragem = st.selectbox(
                    "Litragem da Garrafa",
                    LISTA_LITRAGENS,
                    index=LISTA_LITRAGENS.index(litragem_atual) if litragem_atual in LISTA_LITRAGENS else 2,
                )
            novo_cb = st.text_input(
                "Código de Barras", value=str(vinho_obj.get("codigo_barras", ""))
            ).strip()
            nova_foto_upload = st.file_uploader(
                "📷 Trocar / inserir imagem do vinho",
                type=["jpg", "jpeg", "png", "webp"],
                key=f"foto_editar_{indice_escolhido}",
            )

            senha_exclusao = st.text_input(
                "Senha para excluir este vinho",
                type="password",
                help="Use a mesma senha do usuário que está logado.",
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
                vinho_obj["litragem"] = nova_litragem
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
                nome_usuario_atual = st.session_state.usuario_logado.get("nome", "")
                cargo_usuario_atual = st.session_state.usuario_logado.get("cargo", "Operador")

                if cargo_usuario_atual == "Desenvolvedor":
                    senha_correta_exclusao = SENHA_DEV
                else:
                    usuario_atual = next(
                        (
                            u for u in st.session_state.usuarios
                            if str(u.get("nome", "")).lower() == str(nome_usuario_atual).lower()
                        ),
                        None,
                    )
                    senha_correta_exclusao = (
                        str(usuario_atual.get("senha", ""))
                        if usuario_atual else ""
                    )

                if not senha_exclusao:
                    st.error("Digite sua senha para confirmar a exclusão.")
                elif senha_exclusao != senha_correta_exclusao:
                    st.error("Senha incorreta. O vinho não foi excluído.")
                else:
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
