import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import json

# --- Configurações Iniciais ---
st.set_page_config(page_title="Premium Wines - Galpão", layout="wide")

if "estoque" not in st.session_state:
    st.session_state.estoque = []

# --- Componente Leitor de Código de Barras (Estilo Banco) ---
def componente_leitor():
    html_code = """
    <div id="interactive" style="width: 100%; height: 250px; background: #000; position: relative; border-radius: 10px; overflow: hidden;">
        <div style="position: absolute; top: 50%; left: 0; width: 100%; height: 2px; background: red; box-shadow: 0 0 10px red;"></div>
    </div>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/quagga/0.12.1/quagga.min.js"></script>
    <script>
        Quagga.init({
            inputStream: { type: "LiveStream", target: document.querySelector('#interactive'), constraints: { facingMode: "environment" } },
            decoder: { readers: ["ean_reader", "code_128_reader"] }
        }, function(err) { if (!err) Quagga.start(); });
        Quagga.onDetected(function(data) {
            // Envia o código lido de volta para o Streamlit
            const input = window.parent.document.querySelector('input[type="text"]');
            if(input) {
                input.value = data.codeResult.code;
                input.dispatchEvent(new Event('input', { bubbles: true }));
            }
        });
    </script>
    """
    components.html(html_code, height=270)

# --- Navegação ---
st.sidebar.title("Navegação")
menu = st.sidebar.radio("Ir para:", ["Home", "Cadastrar", "Separar Pedido"])

# --- Abas do Aplicativo ---
if menu == "Home":
    st.title("🏠 Estoque Atual")
    if st.session_state.estoque:
        st.dataframe(pd.DataFrame(st.session_state.estoque), use_container_width=True)
    else:
        st.write("Estoque vazio.")

elif menu == "Cadastrar":
    st.title("➕ Cadastrar Vinho")
    col1, col2 = st.columns(2)
    
    with col1:
        nome = st.text_input("Nome do Vinho")
        cod_barras = st.text_input("Código de Barras (Escaneie ou Digite)")
        if st.button("Salvar Vinho"):
            st.session_state.estoque.append({"Nome": nome, "Código": cod_barras})
            st.success(f"Vinho {nome} cadastrado!")
            
    with col2:
        st.subheader("Scanner")
        componente_leitor()

elif menu == "Separar Pedido":
    st.title("📦 Separar Pedido")
    st.info("Aponte para o código de barras da caixa:")
    componente_leitor()
    
    # Campo para receber o código escaneado
    cod_lido = st.text_input("Código capturado pelo scanner:")
    
    if st.button("Gerar Romaneio Final"):
        if cod_lido:
            # Aqui geramos o arquivo para download
            conteudo_romaneio = f"ROMANEIO DE ENVIO\nData: 11/08/2026\nItem: {cod_lido}\nStatus: Conferido"
            st.download_button("📥 BAIXAR ROMANEIO .TXT", conteudo_romaneio, "romaneio.txt")
            st.success("Romaneio pronto para download!")
        else:
            st.error("Escaneie um código primeiro!")

st.sidebar.info("Premium Wines - Sistema de Galpão")
