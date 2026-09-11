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
    

    /* ========================================================
       VISUAL MOCKUP PREMIUM — ADEGA / VINHEDO / BORDÔ / DOURADO
       Mantém toda a lógica do sistema; altera somente apresentação.
       ======================================================== */
    [data-testid="stAppViewContainer"] > .main {
        background:
          linear-gradient(rgba(7,8,9,.88), rgba(7,8,9,.94)),
          url("data:image/jpeg;base64,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") center top / cover fixed no-repeat !important;
    }
    [data-testid="stSidebar"] {
        background:
          radial-gradient(circle at 10% 15%, rgba(126,25,48,.28), transparent 35%),
          linear-gradient(180deg,#17090e 0%,#0d0b0d 55%,#16080d 100%) !important;
        border-right:1px solid rgba(214,174,99,.38) !important;
        box-shadow:12px 0 40px rgba(0,0,0,.28);
    }
    .sidebar-brand {
        padding:18px 10px 22px !important;
        border-bottom:1px solid rgba(214,174,99,.35) !important;
    }
    .sidebar-brand .brand-title {font-family:Georgia,serif;font-size:1.18rem!important;color:#fff8eb!important;}
    .sidebar-brand .brand-sub {color:#e0b760!important;}
    [data-testid="stSidebar"] .stButton > button:hover {
        background:linear-gradient(90deg,#8f1738,#5b1026)!important;
        border-color:#d6ae63!important;
        transform:translateX(2px);
    }
    .topbar {
        background:linear-gradient(90deg,rgba(20,16,18,.97),rgba(76,10,29,.95))!important;
        border:1px solid rgba(214,174,99,.24)!important;
        box-shadow:0 10px 28px rgba(0,0,0,.25)!important;
    }
    .hero-wine {
        min-height:215px!important;
        padding:30px 34px!important;
        background:
          linear-gradient(90deg,rgba(5,7,8,.92) 0%,rgba(7,7,8,.62) 45%,rgba(20,6,10,.25) 100%),
          url("data:image/jpeg;base64,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") center 46% / cover no-repeat!important;
        border:1px solid rgba(214,174,99,.48)!important;
        box-shadow:0 18px 45px rgba(0,0,0,.34)!important;
    }
    .hero-wine:after {content:""!important;}
    .hero-title {font-family:Georgia,serif!important;font-size:2.55rem!important;text-shadow:0 3px 14px #000;}
    .hero-sub {font-size:1rem!important;color:#f0e5da!important;text-shadow:0 2px 8px #000;}
    .hero-kicker {color:#efc66f!important;}
    [data-testid="stMetric"] {
        background:linear-gradient(145deg,rgba(91,13,35,.90),rgba(24,22,24,.96))!important;
        border:1px solid rgba(214,174,99,.34)!important;
        border-radius:15px!important;
        padding:16px 18px!important;
        min-height:110px;
        box-shadow:0 12px 30px rgba(0,0,0,.22)!important;
    }
    [data-testid="stMetricValue"] {font-family:Georgia,serif!important;color:#fff1d3!important;}
    .section-title {color:#e8b95c!important;font-size:.78rem!important;display:flex;align-items:center;gap:10px;}
    .section-title:after {content:"";height:1px;flex:1;background:linear-gradient(90deg,#d6ae63,transparent);}
    .action-card {
        min-height:118px!important;
        background:linear-gradient(145deg,rgba(76,14,31,.90),rgba(25,22,24,.96))!important;
        border:1px solid rgba(214,174,99,.26)!important;
        box-shadow:0 12px 30px rgba(0,0,0,.22)!important;
        transition:.18s ease;
    }
    .action-card:hover {transform:translateY(-2px);border-color:#d6ae63!important;}
    .action-icon {color:#efbd63!important;}
    .page-hero {
        background:
          linear-gradient(90deg,rgba(31,8,15,.93),rgba(13,13,15,.78)),
          url("data:image/jpeg;base64,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") center / cover no-repeat!important;
        border:1px solid rgba(214,174,99,.38)!important;
    }
    .page-hero:after {content:""!important;}
    [data-testid="stForm"], [data-testid="stExpander"], .premium-panel {
        backdrop-filter:blur(8px);
        background:linear-gradient(145deg,rgba(22,21,23,.94),rgba(15,12,14,.96))!important;
        border-color:rgba(214,174,99,.22)!important;
    }
    .stButton > button {
        background:linear-gradient(90deg,#8b1738,#6e1730)!important;
        border:1px solid rgba(214,174,99,.38)!important;
        color:#fff7ef!important;
    }
    .stButton > button:hover {border-color:#efc66f!important;box-shadow:0 8px 22px rgba(110,23,48,.30)!important;}
    .login-shell {
        padding-top:5vh!important;
        text-shadow:0 3px 14px #000;
    }
    .login-title {font-family:Georgia,serif!important;font-size:2.15rem!important;letter-spacing:.06em!important;}
    .login-card {
        background:linear-gradient(160deg,rgba(12,12,13,.94),rgba(28,10,16,.94))!important;
        border:1px solid rgba(214,174,99,.48)!important;
        box-shadow:0 24px 70px rgba(0,0,0,.55)!important;
        backdrop-filter:blur(12px);
    }
    @media(max-width:800px) {
      .hero-wine {min-height:175px!important;padding:22px 18px!important;}
      .hero-title {font-size:1.75rem!important;}
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
    return f"{base_url}?pallet={pallet_limpo}"


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

# ------------------------------------------------------------
# CONSULTA PÚBLICA DO PALLET PELO QR CODE
# Não exige login e é somente leitura.
# ------------------------------------------------------------
_pallet_publico_param = qp.get("pallet", None)
if _pallet_publico_param:
    _id_publico = extrair_id_do_qr(_pallet_publico_param)
    _pallet_publico = obter_pallet(st.session_state.pallets, _id_publico)

    st.markdown(
        "<style>[data-testid='stSidebar']{display:none!important;} [data-testid='stHeader']{display:none!important;} .block-container{padding-top:1.4rem!important;max-width:900px!important;}</style>",
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div style="background:linear-gradient(135deg,#17171b,#241016);border:1px solid #4b2830;border-radius:18px;padding:22px 24px;margin-bottom:18px;">
            <div style="font-size:1.45rem;font-weight:800;color:#f3c45b;">🍷 PREMIUM WINES</div>
            <div style="color:#c9c9cf;margin-top:3px;">Consulta de posição do galpão</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if _pallet_publico:
        _corredor_pub = html.escape(str(_pallet_publico.get("corredor", "")))
        _pallet_nome_pub = html.escape(str(_pallet_publico.get("pallet", "")))
        _lado_pub = html.escape(str(_pallet_publico.get("lado", "")))
        _vinhos_pub = _pallet_publico.get("vinhos", []) or []

        st.markdown(
            f"""
            <div style="background:#17171b;border:1px solid #34343b;border-radius:16px;padding:18px 20px;margin-bottom:16px;">
                <div style="color:#f3c45b;font-size:1.15rem;font-weight:800;">📍 {_corredor_pub} • {_pallet_nome_pub} • {_lado_pub}</div>
                <div style="color:#c9c9cf;margin-top:6px;">{len(_vinhos_pub)} vinho(s) nesta posição</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if _vinhos_pub:
            st.markdown("### Vinhos nesta posição")
            for _i, _vinho in enumerate(_vinhos_pub, start=1):
                _nome = html.escape(str(_vinho.get("nome", "Vinho")))
                _safra = html.escape(str(_vinho.get("safra", "N/A")))
                st.markdown(
                    f"""
                    <div style="background:#17171b;border:1px solid #34343b;border-radius:12px;padding:14px 16px;margin:8px 0;">
                        <div style="font-weight:750;color:#f0f0f3;">{_i}. {_nome}</div>
                        <div style="color:#b9b9c0;margin-top:3px;">Safra: {_safra}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.info("Nenhum vinho cadastrado nesta posição no momento.")
    else:
        st.error("Esta posição de pallet não foi encontrada no sistema.")

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

    st.markdown(
        """
        Aponte a câmera do celular para o
        QR Code colocado no pallet.
        <br>
        O sistema mostrará os vinhos e as
        respectivas safras cadastrados atualmente nessa posição.
        <br>
        A etiqueta do pallet é fixa: se os vinhos mudarem, não é necessário trocar o QR Code.
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

        # A etiqueta identifica a posição. QR Codes antigos que continham
        # texto extra também continuam funcionando: extraímos apenas o ID
        # e consultamos os dados atuais do pallet no sistema.
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
                ["Escolher...", "Todos", "Pendente", "Concluído / Expedido"],
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
                        status_col = (
                            "#66C38A"
                            if normalizar_nome_vinho(status_p) == normalizar_nome_vinho("Concluído / Expedido")
                            else "#E0A95A"
                        )

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

            # No checkout exibimos somente pedidos que ainda precisam de conferência.
            # Assim que um pedido é finalizado, ele desaparece desta tela automaticamente.
            pedidos_pendentes_checkout = [
                p
                for p in st.session_state.pedidos
                if p.get("status", "Pendente") != "Concluído / Expedido"
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

