import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

st.set_page_config(page_title="Premium Wines - Galpão", layout="wide")

# --- CSS Profissional ---
st.markdown("""
    <style>
    .stApp { background: #f4f4f9; }
    .scanner-box { border: 2px solid #7A1C2E; border-radius: 10px; padding: 10px; background: white; }
    </style>
""", unsafe_allow_html=True)

# --- Gerenciamento de Estado ---
if "estoque" not in st.session_state: st.session_state.estoque = []

# --- LEITOR HTML5-QRCODE (Muito mais eficiente) ---
def componente_leitor_avancado(key):
    html = f"""
    <div id="reader-{key}" style="width: 100%; height: 300px;"></div>
    <script src="https://unpkg.com/html5-qrcode"></script>
    <script>
        function onScanSuccess(decodedText, decodedResult) {{
            window.parent.postMessage({{type: 'barcode', key: '{key}', value: decodedText}}, '*');
        }}
        let html5QrcodeScanner = new Html5QrcodeScanner("reader-{key}", {{ fps: 10, qrbox: 250 }});
        html5QrcodeScanner.render(onScanSuccess);
    </script>
    """
    components.html(html, height=350)
    
    # Captura a mensagem do JS
    msg = st.experimental_get_query_params().get("barcode_msg")
    return None

# --- Navegação ---
menu = st.sidebar.radio("Navegação", ["Home", "Cadastrar", "Separar Pedido"])

if menu == "Home":
    st.title("Estoque Atual")
    if st.session_state.estoque:
        st.dataframe(pd.DataFrame(st.session_state.estoque), use_container_width=True)
    else:
        st.write("Estoque vazio.")

elif menu == "Cadastrar":
    st.title("Cadastrar Vinho")
    nome = st.text_input("Nome do Vinho")
    # Campo que receberá o valor do leitor via JS (usando Session State)
    if "cod_escaneado" not in st.session_state: st.session_state.cod_escaneado = ""
    
    cod_barras = st.text_input("Código de Barras", value=st.session_state.cod_escaneado)
    
    st.subheader("Scanner (Aponte para o código)")
    componente_leitor_avancado("cad_1")
    
    if st.button("Salvar Vinho"):
        st.session_state.estoque.append({"Nome": nome, "Código": cod_barras})
        st.success("Vinho cadastrado!")
        st.session_state.cod_escaneado = ""

elif menu == "Separar Pedido":
    st.title("Separar Pedido")
    componente_leitor_avancado("sep_1")
    
    if st.button("Gerar Romaneio"):
        conteudo = "ROMANEIO DE ENVIO\nData: 11/08/2026\nStatus: Conferido"
        st.download_button("📥 BAIXAR ROMANEIO .TXT", conteudo, "romaneio.txt")
