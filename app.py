[data-testid="stAlert"] p,
[data-testid="stAlert"] span {{
    color:var(--pw-text) !important;
    -webkit-text-fill-color:var(--pw-text) !important;
}}

/* Tabelas */
[data-testid="stDataFrame"],
[data-testid="stDataEditor"],
[data-testid="stTable"] {{
    background:#FFFFFF !important;
    border:1px solid var(--pw-line) !important;
    border-radius:14px !important;
    overflow:hidden !important;
    box-shadow:0 8px 24px rgba(67,42,49,.06) !important;
}}

/* Tabs internas */
div[data-baseweb="tab-list"] {{
    background:#F3EDE8 !important;
    border:1px solid var(--pw-line) !important;
    border-radius:12px !important;
    padding:4px !important;
}}
button[data-baseweb="tab"] {{
    border-radius:9px !important;
    color:#69575C !important;
}}
button[data-baseweb="tab"] *,
button[data-baseweb="tab"] p,
button[data-baseweb="tab"] span {{
    color:#69575C !important;
    -webkit-text-fill-color:#69575C !important;
    opacity:1 !important;
}}
button[data-baseweb="tab"][aria-selected="true"] {{
    background:#FFFFFF !important;
    box-shadow:0 4px 12px rgba(67,42,49,.08) !important;
}}
button[data-baseweb="tab"][aria-selected="true"] *,
button[data-baseweb="tab"][aria-selected="true"] p {{
    color:var(--pw-wine) !important;
    -webkit-text-fill-color:var(--pw-wine) !important;
    font-weight:800 !important;
}}

/* Responsivo */
@media(max-width:900px) {{
    .topbar-right-v8 .db-chip-v8 {{ display:none; }}
    .user-chip-v8 {{ min-width:auto; }}
    .page-hero:after {{ width:58px;height:58px; }}
    .hero-title {{ font-size:1.55rem !important; }}
}}
@media(max-width:640px) {{
    .topbar-sub-v8,.user-chip-v8 {{ display:none; }}
    .premium-topbar-v8 {{ min-height:60px !important; }}
    .hero-wine {{ padding:24px 20px !important; min-height:150px !important; }}
    .block-container {{ padding-left:.8rem !important;padding-right:.8rem !important; }}
}}
</style>
""", unsafe_allow_html=True)

# ============================================================
# V11 — SIDEBAR RESPONSIVA
# Desktop: fixa. Celular: comportamento nativo deslizante do Streamlit.
# ============================================================
st.markdown("""
<style>
@media (min-width: 901px) {
    header[data-testid="stHeader"], [data-testid="stHeader"] {
        display:none !important; visibility:hidden !important; height:0 !important; min-height:0 !important;
    }
    [data-testid="stSidebar"] {
        display:flex !important; visibility:visible !important; opacity:1 !important;
        transform:none !important; margin-left:0 !important; width:270px !important; min-width:270px !important;
        pointer-events:auto !important;
    }
    [data-testid="stSidebarCollapseButton"],
    [data-testid="stSidebarCollapsedControl"],
    [data-testid="collapsedControl"] { display:none !important; }
}

@media (max-width: 900px) {
    /* Restaura o cabeçalho nativo: é nele que o Streamlit coloca o botão do menu. */
    header[data-testid="stHeader"], [data-testid="stHeader"] {
        display:flex !important; visibility:visible !important; opacity:1 !important;
        height:52px !important; min-height:52px !important;
        background:rgba(250,248,245,.96) !important; border-bottom:1px solid #E3DAD4 !important;
        box-shadow:none !important; z-index:99990 !important;
    }
    [data-testid="stToolbar"], [data-testid="stDecoration"], [data-testid="stMainMenu"],
    .stAppToolbar, .stDeployButton { display:none !important; visibility:hidden !important; }

    /* Não definimos transform/aria-expanded: o próprio Streamlit controla o slide. */
    [data-testid="stSidebar"] {
        width:min(84vw,330px) !important; min-width:0 !important; max-width:330px !important;
        box-shadow:18px 0 38px rgba(31,7,16,.28) !important; z-index:99999 !important;
    }
    [data-testid="stSidebar"] .stButton > button {
        min-height:48px !important; touch-action:manipulation !important;
    }
    [data-testid="stSidebarCollapsedControl"], [data-testid="collapsedControl"],
    [data-testid="stSidebarCollapseButton"] {
        visibility:visible !important; opacity:1 !important; pointer-events:auto !important; z-index:100002 !important;
    }
}
</style>
""", unsafe_allow_html=True)


# ============================================================
# V11.2 — CORREÇÕES VISUAIS PONTUAIS
# Somente aparência/legibilidade. Não altera regras do sistema.
# ============================================================
st.markdown(r"""
<style>
/* 1) Logo do cabeçalho: nunca pode crescer além do tamanho padrão. */
.premium-topbar-v8 .topbar-logo-v8,
.topbar.premium-topbar-v8 img.topbar-logo-v8 {
    width:48px !important;
    height:48px !important;
    min-width:48px !important;
    min-height:48px !important;
    max-width:48px !important;
    max-height:48px !important;
    object-fit:cover !important;
    display:block !important;
    flex:0 0 48px !important;
    padding:2px !important;
    margin:0 !important;
    border-radius:13px !important;
}
.premium-topbar-v8 .topbar-left-v8 {
    display:flex !important;
    align-items:center !important;
    min-width:0 !important;
}
.premium-topbar-v8 {
    overflow:hidden !important;
}

/* 2) Texto dos botões bordô sempre branco, inclusive em reruns e divergências. */
.stButton > button,
.stDownloadButton > button,
.stFormSubmitButton > button {
    color:#FFFFFF !important;
    -webkit-text-fill-color:#FFFFFF !important;
}
.stButton > button *,
.stDownloadButton > button *,
.stFormSubmitButton > button * {
    color:#FFFFFF !important;
    -webkit-text-fill-color:#FFFFFF !important;
    opacity:1 !important;
}
.stButton > button:disabled *,
.stDownloadButton > button:disabled *,
.stFormSubmitButton > button:disabled * {
    color:#FFFFFF !important;
    -webkit-text-fill-color:#FFFFFF !important;
