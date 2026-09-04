import streamlit as st
import pandas as pd
from datetime import datetime
import json
import os

# Configuração da Página
st.set_page_config(
    page_title="Premium Wines - Galpão",
    page_icon="🍷",
    layout="wide"
)

# Constantes e Arquivos de Persistência
ARQUIVO_ESTOQUE = "estoque_vinhos.json"
ARQUIVO_PEDIDOS = "pedidos_galpao.json"
ARQUIVO_LOGS = "logs_auditoria.json"

# --- FUNÇÕES AUXILIARES E PERSISTÊNCIA ---

def obter_horario_brasilia():
    # Retorna o horário atual (simulado ou local)
    return datetime.now()

def carregar_dados(arquivo, padrao):
    if os.path.exists(arquivo):
        try:
            with open(arquivo, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return padrao
    return padrao

def salvar_dados(arquivo, dados):
    with open(arquivo, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)

def registrar_log(usuario, acao, detalhe=""):
    logs = carregar_dados(ARQUIVO_LOGS, [])
    logs.append({
        "data": obter_horario_brasilia().strftime("%d/%m/%Y %H:%M:%S"),
        "usuario": usuario,
        "acao": acao,
        "detalhe": detalhe
    })
    salvar_dados(ARQUIVO_LOGS, logs)

def sincronizar_estoque_com_pedidos(pedidos, estoque):
    # Lógica opcional para recalcular o estoque se necessário
    pass

# --- INICIALIZAÇÃO DO SESSION STATE ---
if "estoque" not in st.session_state:
    st.session_state.estoque = carregar_dados(ARQUIVO_ESTOQUE, [
        {"codigo_barras": "7891001", "nome": "Château Margaux", "safra": "2015", "corredor": "A1", "quantidade": 50},
        {"codigo_barras": "7891002", "nome": "Barolo DOCG", "safra": "2018", "corredor": "B2", "quantidade": 30},
        {"codigo_barras": "7891003", "nome": "Malbec Reserva", "safra": "2020", "corredor": "C3", "quantidade": 100}
    ])

if "pedidos" not in st.session_state:
    st.session_state.pedidos = carregar_dados(ARQUIVO_PEDIDOS, [])

if "usuario_logado" not in st.session_state:
    st.session_state.usuario_logado = {"nome": "Operador Galpão", "cargo": "Conferente"}

if "itens_pedido_temp" not in st.session_state:
    st.session_state.itens_pedido_temp = []

# --- COMPONENTE DE LEITOR DE CÂMERA (Fictício/Simulado) ---
def componente_leitor_barcode(chave):
    # Espaço reservado para input de bipagem por câmera ou leitor bluetooth focado
    pass

# --- INTERFACE PRINCIPAL ---

st.title("🍷 Premium Wines - Sistema de Galpão")
st.markdown(f"**Usuário:** {st.session_state.usuario_logado['nome']} ({st.session_state.usuario_logado['cargo']})")

# Abas de Navegação do Sistema
abas = st.tabs([
    "📦 Cadastrar Pedido", 
    "📋 Conferir Pedidos (Mapa)", 
    "🔍 Filtros / Estoque", 
    "➕ Cadastrar Vinho", 
    "📊 Auditoria / Logs"
])

# ==========================================
# ABA 1: CADASTRAR PEDIDO (COM AS 3 OPÇÕES)
# ==========================================
with abas[0]:
    st.subheader("📦 Cadastrar Novo Pedido / Mapa de Separação")
    
    id_pedido = st.text_input("*Código de Barras ou Número do Mapa / Pedido:").strip()
    
    st.markdown("---")
    st.markdown("#### 📥 Escolha a forma de adicionar os itens ao pedido:")
    
    modo_cadastro_pedido = st.radio(
        "Método de Entrada:", 
        ["⌨️ Bipar / Digitar Código ou Nome", "📂 Enviar Arquivo (PDF / Excel / TXT)", "✍️ Inserção Manual por Lista"],
        horizontal=True
    )
    
    itens_novos = []

    # OPÇÃO 1: BIPAR / DIGITAR
    if modo_cadastro_pedido == "⌨️ Bipar / Digitar Código ou Nome":
        st.markdown("Utilize o leitor USB ou digite o nome/código do vinho para compor o pedido item a item.")
        
        componente_leitor_barcode("cadastro_pedido_camera")
        codigo_cam = st.session_state.get("codigo_bipado_cadastro_pedido", "")
        
        col_cp1, col_cp2, col_cp3 = st.columns([2, 1, 1])
        with col_cp1:
            entrada_bipagem = st.text_input("Código de Barras ou Nome do Vinho", value=codigo_cam, key="input_bip_cad_pedido")
        with col_cp2:
            qtd_bipada = st.number_input("Quantidade", min_value=1, value=1, key="qtd_cad_pedido")
        with col_cp3:
            st.write("")
            btn_adicionar_item = st.button("Adicionar à Lista", use_container_width=True)
            
        if btn_adicionar_item and entrada_bipagem:
            vinho_encontrado = next((v for v in st.session_state.estoque if v['nome'].lower() in entrada_bipagem.lower() or v.get('codigo_barras') == entrada_bipagem), None)
            
            nome_item = vinho_encontrado['nome'] if vinho_encontrado else entrada_bipagem.title()
            safra_item = vinho_encontrado.get('safra', 'N/A') if vinho_encontrado else 'N/A'
            
            st.session_state.itens_pedido_temp.append({
                "nome": nome_item,
                "safra": safra_item,
                "quantidade": qtd_bipada,
                "separado": False,
                "qtd_separada": 0,
                "divergencia": 0,
                "autorizado_divergencia": True
            })
            st.success(f"Item '{nome_item}' ({qtd_bipada} un) adicionado à lista temporária!")
            st.rerun()
            
        if st.session_state.itens_pedido_temp:
            st.markdown("##### Itens adicionados a este pedido:")
            for idx, it in enumerate(st.session_state.itens_pedido_temp):
                c1, c2, c3 = st.columns([3, 1, 1])
                with c1:
                    st.write(f"- **{it['nome']}** (Safra: {it['safra']})")
                with c2:
                    st.write(f"Qtd: **{it['quantidade']}**")
                with c3:
                    if st.button("❌ Remover", key=f"rm_item_{idx}"):
                        st.session_state.itens_pedido_temp.pop(idx)
                        st.rerun()
            
            itens_novos = st.session_state.itens_pedido_temp

    # OPÇÃO 2: ENVIAR ARQUIVO
    elif modo_cadastro_pedido == "📂 Enviar Arquivo (PDF / Excel / TXT)":
        st.markdown("Envie o arquivo do mapa/pedido fornecido pelo sistema (suporta Excel, CSV ou TXT).")
        arquivo_pedido = st.file_uploader("Selecione o arquivo do pedido", type=["xlsx", "csv", "txt"])
        
        if arquivo_pedido is not None:
            try:
                if arquivo_pedido.name.endswith('.xlsx'):
                    df_arq = pd.read_excel(arquivo_pedido)
                    for _, row in df_arq.iterrows():
                        itens_novos.append({
                            "nome": str(row.get('Produto', row.get('Nome', 'Vinho Desconhecido'))),
                            "safra": str(row.get('Safra', 'N/A')),
                            "quantidade": int(row.get('Quantidade', row.get('Qtd', 1))),
                            "separado": False,
                            "qtd_separada": 0,
                            "divergencia": 0,
                            "autorizado_divergencia": True
                        })
                    st.success(f"Arquivo Excel carregado com {len(itens_novos)} itens.")
                elif arquivo_pedido.name.endswith('.csv'):
                    df_arq = pd.read_csv(arquivo_pedido)
                    for _, row in df_arq.iterrows():
                        itens_novos.append({
                            "nome": str(row.get('Produto', 'Vinho Desconhecido')),
                            "safra": str(row.get('Safra', 'N/A')),
                            "quantidade": int(row.get('Quantidade', 1)),
                            "separado": False,
                            "qtd_separada": 0,
                            "divergencia": 0,
                            "autorizado_divergencia": True
                        })
                    st.success(f"Arquivo CSV carregado com {len(itens_novos)} itens.")
                else:
                    st.info("Arquivo de texto enviado com sucesso.")
            except Exception as e:
                st.error(f"Erro ao processar o arquivo: {e}")
                
        if itens_novos:
            st.markdown("##### Prévia dos itens lidos do arquivo:")
            df_preview = pd.DataFrame(itens_novos)
            st.dataframe(df_preview, use_container_width=True)

    # OPÇÃO 3: INSERÇÃO MANUAL POR LISTA
    else:
        st.markdown("Selecione os vinhos diretamente do estoque cadastrado no galpão para compor o pedido.")
        
        if st.session_state.estoque:
            opcoes_estoque = [v['nome'] for v in st.session_state.estoque]
            vinhos_selecionados_manual = st.multiselect("Selecione os rótulos do pedido:", opcoes_estoque)
            
            if vinhos_selecionados_manual:
                st.markdown("Defina a quantidade para cada vinho selecionado:")
                quantidades_manuais = {}
                for v_nome in vinhos_selecionados_manual:
                    quantidades_manuais[v_nome] = st.number_input(f"Quantidade para '{v_nome}':", min_value=1, value=1, key=f"qtd_man_{v_nome}")
                    
                for v_nome in vinhos_selecionados_manual:
                    vinho_obj = next((v for v in st.session_state.estoque if v['nome'] == v_nome), {})
                    itens_novos.append({
                        "nome": v_nome,
                        "safra": vinho_obj.get('safra', 'N/A'),
                        "quantidade": quantidades_manuais[v_nome],
                        "separado": False,
                        "qtd_separada": 0,
                        "divergencia": 0,
                        "autorizado_divergencia": True
                    })
        else:
            st.warning("Não há vinhos cadastrados no estoque para seleção manual.")

    st.markdown("---")

    # Botão de Salvamento Final
    if st.button("💾 Salvar Pedido / Mapa Completo", use_container_width=True):
        if id_pedido and itens_novos:
            novo_registro_pedido = {
                "id": str(id_pedido).strip(),
                "data": obter_horario_brasilia().strftime("%d/%m/%Y %H:%M"),
                "itens": itens_novos,
                "status": "Pendente"
            }
            st.session_state.pedidos.append(novo_registro_pedido)
            salvar_dados(ARQUIVO_PEDIDOS, st.session_state.pedidos)
            registrar_log(st.session_state.usuario_logado['nome'], "Novo Pedido Cadastrado", str(id_pedido))
            
            st.session_state.itens_pedido_temp = []
            st.success(f"Pedido / Mapa {id_pedido} cadastrado e salvo com sucesso!")
            st.rerun()
        else:
            st.error("Preencha o código/número do pedido e adicione ao menos um item válido.")

# ==========================================
# ABA 2: CONFERIR PEDIDOS (MAPA)
# ==========================================
with abas[1]:
    st.subheader("📋 Conferência de Pedidos por Mapa")
    
    if not st.session_state.pedidos:
        st.info("Nenhum pedido cadastrado no momento.")
    else:
        ids_pedidos = [p['id'] for p in st.session_state.pedidos]
        pedido_selecionado_id = st.selectbox("Selecione o Pedido para Conferência:", ids_pedidos)
        
        pedido_atual = next((p for p in st.session_state.pedidos if p['id'] == pedido_selecionado_id), None)
        
        if pedido_atual:
            st.write(f"**Status Atual:** {pedido_atual['status']} | **Data:** {pedido_atual['data']}")
            
            st.markdown("#### Itens do Pedido:")
            for i, item in enumerate(pedido_atual['itens']):
                col_i1, col_i2, col_i3 = st.columns([3, 1, 1])
                with col_i1:
                    st.text(f"{item['nome']} (Safra: {item['safra']})")
                with col_i2:
                    st.text(f"Qtd Pedida: {item['quantidade']}")
                with col_i3:
                    status_item = "✅ Conferido" if item.get('separado', False) else "⏳Pendente"
                    st.text(status_item)
            
            # Senha de divergência e fechamento
            senha_conf = st.text_input("Senha de Conferência/Divergência (Ex: 2026):", type="password", key="pwd_conf")
            
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                if st.button("Finalizar Conferência do Pedido", use_container_width=True):
                    if senha_conf == "2026":
                        pedido_atual['status'] = "Concluído"
                        salvar_dados(ARQUIVO_PEDIDOS, st.session_state.pedidos)
                        registrar_log(st.session_state.usuario_logado['nome'], "Conclusão de Pedido", pedido_atual['id'])
                        st.success("Pedido conferido e finalizado com sucesso!")
                        st.rerun()
                    else:
                        st.error("Senha de liberação incorreta.")

# ==========================================
# ABA 3: FILTROS / ESTOQUE
# ==========================================
with abas[2]:
    st.subheader("🔍 Consulta de Estoque Completo")
    if st.session_state.estoque:
        df_estoque = pd.DataFrame(st.session_state.estoque)
        st.dataframe(df_estoque, use_container_width=True)
    else:
        st.info("Estoque vazio.")

# ==========================================
# ABA 4: CADASTRAR VINHO
# ==========================================
with abas[3]:
    st.subheader("➕ Cadastro de Novo Rótulo no Estoque")
    with st.form("form_cad_vinho"):
        cb = st.text_input("Código de Barras")
        nome = st.text_input("Nome do Vinho")
        safra = st.text_input("Safra")
        corredor = st.text_input("Corredor / Posição")
        qtd = st.number_input("Quantidade Inicial", min_value=0, value=10)
        
        submitted = st.form_submit_button("Salvar Vinho")
        if submitted and nome:
            st.session_state.estoque.append({
                "codigo_barras": cb,
                "nome": nome,
                "safra": safra,
                "corredor": corredor,
                "quantidade": qtd
            })
            salvar_dados(ARQUIVO_ESTOQUE, st.session_state.estoque)
            registrar_log(st.session_state.usuario_logado['nome'], "Cadastro de Vinho", nome)
            st.success(f"Vinho '{nome}' cadastrado com sucesso!")
            st.rerun()

# ==========================================
# ABA 5: AUDITORIA / LOGS
# ==========================================
with abas[4]:
    st.subheader("📊 Histórico de Auditoria e Logs")
    logs = carregar_dados(ARQUIVO_LOGS, [])
    if logs:
        df_logs = pd.DataFrame(logs)
        st.dataframe(df_logs, use_container_width=True)
    else:
        st.info("Nenhum log registrado ainda.")
