st.markdown(
    """
    <style>
    /* Fundo Geral */
    .stApp {
        background-color: #121212;
        color: #FFFFFF;
        font-family: 'Poppins', sans-serif;
    }

    /* Cards Estilo Wine Map Pro */
    .wine-card {
        background-color: #1E1E1E;
        border: 1px solid #333333;
        border-radius: 16px;
        padding: 16px;
        margin-bottom: 12px;
        box-shadow: 0px 4px 15px rgba(0,0,0,0.3);
    }

    /* Botão Principal Estilo Wine Map */
    div.stButton > button {
        background-color: #581825 !important;
        color: #FFFFFF !important;
        border-radius: 12px !important;
        border: none !important;
        font-weight: 600 !important;
        transition: 0.3s !important;
    }
    div.stButton > button:hover {
        background-color: #7A1C2E !important;
        border: 1px solid #C9A227 !important;
    }

    /* Cabeçalhos */
    h1, h2, h3 { color: #FFFFFF !important; }
    
    /* Inputs */
    .stTextInput > div > div > input, .stSelectbox > div > div {
        background-color: #1E1E1E !important;
        color: white !important;
        border: 1px solid #333333 !important;
        border-radius: 8px !important;
    }
    
    /* Remover sidebar se não for usar */
    [data-testid="stSidebar"] { display: none; }
    </style>
    """, unsafe_allow_html=True
)
