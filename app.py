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
ARQUIVO_USUARIOS = "usuarios_galpao.json"

# --- FUNÇÕES AUXILIARES E PERSISTÊNCIA ---

def obter_horario_brasilia():
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

if "usuarios" not in st.session_state:
    st.session_state.usuarios = carregar_dados(ARQUIVO_USUARIOS, [
        {"nome": "João Silva", "cargo": "Conferente", "pin": "1234"},
        {"nome": "Dev", "cargo": "Desenvolvedor", "pin": "2026"}
    ])

if "usuario_logado" not in st.session_state:
    st.session_state.usuario_logado = st.session_state.usuarios[1]

if "pagina_atual" not in st.session_state:
    st.session_state.pagina_atual = "Home"

if "itens_pedido_temp" not in st.session_state:
    st.session_state.itens_pedido_temp = []

# --- CABEÇALHO SUPERIOR FIXO ---
col_h1, col_h2 = st.columns([5, 1])
with col_h1:
    st.markdown(f"🍷 **PREMIUM WINES** | Usuário: **{st.session_state.usuario_logado['nome']}** ({st.session_state.usuario_logado['cargo']})")
with col_h2:
    if st.session_state.pagina_atual != "Home":
        if st.button("🚪 Voltar", use_container_width=True):
            st.session_state.pagina_atual = "Home"
            st.rerun()

st.markdown("---")

# ==========================================
# TELA INICIAL (HOME COM OS BOTÕES EM GRID)
# ==========================================
if st.session_state.pagina_atual == "Home":
    st.markdown("<h3 style='text-align: center;'>Boa noite,</h3>", unsafe_allow_html=True)
    st.markdown(f"<h1 style='text-align: center;'>{st.session_state.usuario_logado['nome']}! 👋</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>Separação de Vinho Galpão - Escolha a opção abaixo:</p>", unsafe_allow_html=True)
    st.write("")
    
    # Linha 1 de Botões
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("📦 Checkout de Expedição", use_container_width=True):
            st.session_state.pagina_atual = "Checkout de Expedição"
            st.rerun()
    with c2:
        if st.button("🏢 Painel da Matriz", use_container_width=True):
            st.session_state.pagina_atual = "Painel da Matriz"
            st.rerun()
    with c3:
        if st.button("🔍 Buscar / Filtros", use_container_width=True):
            st.session_state.pagina_atual = "Buscar / Filtros"
            st.rerun()
            
    # Linha 2 de Botões
    c4, c5, c6 = st.columns(3)
    with c4:
        if st.button("📋 Mapa de Separação", use_container_width=True):
            st.session_state.pagina_atual = "Mapa de Separação"
            st.rerun()
    with c5:
        if st.button("🍷 Estoque Completo", use_container_width=True):
            st.session_state.pagina_atual = "Estoque Completo"
            st.rerun()
    with c6:
        if st.button("➕ Cadastrar Vinho", use_container_width=True):
            st.session_state.pagina_atual = "Cadastrar Vinho"
            st.rerun()
            
    # Linha 3 de Botões
    c7, c8, c9 = st.columns(3)
    with c7:
        if st.button("✏️ Editar Vinho", use_container_width=True):
            st.session_state.pagina_atual = "Editar Vinho"
            st.rerun()
    with c8:
        if st.button("📊 Histórico", use_container_width=True):
            st.session_state.pagina_atual = "Histórico"
            st.rerun()
    with c9:
        if st.button("⚙️ Gerenciar Contas", use_container_width=True):
            st.session_state.pagina_atual = "Gerenciar Contas"
            st.rerun()

# ==========================================
# 1. CHECKOUT DE EXPEDIÇÃO (CADASTRO COM 3 OPÇÕES)
# ==========================================
elif st.session_state.pagina_atual == "Checkout de Expedição":
    st.subheader("📦 Checkout de Expedição / Cadastrar Novo Pedido")
    
    id_pedido = st.text_input("*Código de Barras ou Número do Mapa / Pedido:").strip()
    
    st.markdown("---")
    st.markdown("#### 📥 Escolha a forma de adicionar os itens ao pedido:")
    
    modo_cadastro_pedido = st.radio(
        "Método de Entrada:", 
        ["⌨️ Bipar / Digitar Código ou Nome", "📂 Enviar Arquivo (PDF / Excel / TXT)", "✍️ Inserção Manual por Lista"],
        horizontal=True
    )
    
    itens_novos = []

    # OPÇÃO 1: BIPAR / DIGITAR CÓDIGO OU NOME
    if modo_cadastro_pedido == "⌨️ Bipar / Digitar Código ou Nome":
        st.markdown("Utilize o leitor USB ou digite o nome/código do vinho para compor o pedido item a item.")
        
        col_cp1, col_cp2, col_cp3 = st.columns([2, 1, 1])
        with col_cp1:
            entrada_bipagem = st.text_input("Código de Barras ou Nome do Vinho", key="input_bip_cad_pedido")
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
# 2. PAINEL DA MATRIZ
# ==========================================
elif st.session_state.pagina_atual == "Painel da Matriz":
    st.subheader("🏢 Painel da Matriz / Visão Geral dos Pedidos")
    if st.session_state.pedidos:
        df_pedidos_geral = pd.DataFrame([{
            "ID Pedido": p['id'],
            "Data": p['data'],
            "Status": p['status'],
            "Total Itens": len(p['itens'])
        } for p in st.session_state.pedidos])
        st.dataframe(df_pedidos_geral, use_container_width=True)
    else:
        st.info("Nenhum pedido registrado no painel.")

# ==========================================
# 3. BUSCAR / FILTROS
# ==========================================
elif st.session_state.pagina_atual == "Buscar / Filtros":
    st.subheader("🔍 Buscar e Filtrar Estoque")
    if st.session_state.estoque:
        termo_busca = st.text_input("Filtrar por Nome ou Código de Barras:")
        df_estoque = pd.DataFrame(st.session_state.estoque)
        if termo_busca:
            df_estoque = df_estoque[
                df_estoque['nome'].str.contains(termo_busca, case=False, na=False) | 
                df_estoque['codigo_barras'].str.contains(termo_busca, case=False, na=False)
            ]
        st.dataframe(df_estoque, use_container_width=True)
    else:
        st.info("Estoque vazio.")

# ==========================================
# 4. MAPA DE SEPARAÇÃO
# ==========================================
elif st.session_state.pagina_atual == "Mapa de Separação":
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
                    status_item = "✅ Conferido" if item.get('separado', False) else "⏳ Pendente"
                    if st.button(status_item, key=f"conf_item_{pedido_atual['id']}_{i}"):
                        item['separado'] = not item.get('separado', False)
                        salvar_dados(ARQUIVO_PEDIDOS, st.session_state.pedidos)
                        st.rerun()
            
            st.markdown("---")
            senha_conf = st.text_input("Senha de Conferência/Divergência (Ex: 2026):", type="password", key="pwd_conf")
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
# 5. ESTOQUE COMPLETO
# ==========================================
elif st.session_state.pagina_atual == "Estoque Completo":
    st.subheader("🍷 Estoque Completo do Galpão")
    if st.session_state.estoque:
        st.dataframe(pd.DataFrame(st.session_state.estoque), use_container_width=True)
    else:
        st.info("O estoque está vazio.")

# ==========================================
# 6. CADASTRAR VINHO
# ==========================================
elif st.session_state.pagina_atual == "Cadastrar Vinho":
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
# 7. EDITAR VINHO
# ==========================================
elif st.session_state.pagina_atual == "Editar Vinho":
    st.subheader("✏️ Gerenciar / Editar Estoque")
    if st.session_state.estoque:
        vinho_nomes = [v['nome'] for v in st.session_state.estoque]
        vinho_escolhido = st.selectbox("Selecione o Vinho para Editar/Excluir", vinho_nomes)
        v_obj = next((v for v in st.session_state.estoque if v['nome'] == vinho_escolhido), None)
        
        if v_obj:
            with st.form("form_edit_vinho"):
                novo_cb = st.text_input("Código de Barras", value=v_obj.get('codigo_barras', ''))
                novo_nome = st.text_input("Nome", value=v_obj.get('nome', ''))
                nova_safra = st.text_input("Safra", value=v_obj.get('safra', ''))
                novo_corredor = st.text_input("Corredor", value=v_obj.get('corredor', ''))
                nova_qtd = st.number_input("Quantidade", min_value=0, value=int(v_obj.get('quantidade', 0)))
                
                col_e1, col_e2 = st.columns(2)
                with col_e1:
                    btn_atualizar = st.form_submit_button("Salvar Alterações")
                with col_e2:
                    btn_excluir = st.form_submit_button("Excluir Vinho")
                    
                if btn_atualizar:
                    v_obj['codigo_barras'] = novo_cb
                    v_obj['nome'] = novo_nome
                    v_obj['safra'] = nova_safra
                    v_obj['corredor'] = novo_corredor
                    v_obj['quantidade'] = nova_qtd
                    salvar_dados(ARQUIVO_ESTOQUE, st.session_state.estoque)
                    registrar_log(st.session_state.usuario_logado['nome'], "Edição de Vinho", novo_nome)
                    st.success("Alterações salvas com sucesso!")
                    st.rerun()
                if btn_excluir:
                    st.session_state.estoque.remove(v_obj)
                    salvar_dados(ARQUIVO_ESTOQUE, st.session_state.estoque)
                    registrar_log(st.session_state.usuario_logado['nome'], "Exclusão de Vinho", vinho_escolhido)
                    st.warning("Vinho excluído do estoque!")
                    st.rerun()
    else:
        st.info("Nenhum vinho para gerenciar.")

# ==========================================
# 8. HISTÓRICO
# ==========================================
elif st.session_state.pagina_atual == "Histórico":
    st.subheader("📊 Histórico de Auditoria e Logs")
    logs = carregar_dados(ARQUIVO_LOGS, [])
    if logs:
        st.dataframe(pd.DataFrame(logs), use_container_width=True)
    else:
        st.info("Nenhum log registrado ainda.")

# ==========================================
# 9. GERENCIAR CONTAS
# ==========================================
elif st.session_state.pagina_atual == "Gerenciar Contas":
    st.subheader("👥 Gerenciamento de Usuários")
    nomes_usuarios = [u['nome'] for u in st.session_state.usuarios]
    usuario_selecionado = st.selectbox("Selecionar Usuário Ativo:", nomes_usuarios)
    
    if st.button("Definir como Usuário Atual"):
        obj_u = next((u for u in st.session_state.usuarios if u['nome'] == usuario_selecionado), None)
        if obj_u:
            st.session_state.usuario_logado = obj_u
            st.success(f"Usuário alterado para {obj_u['nome']} ({obj_u['cargo']})")
            st.rerun()
