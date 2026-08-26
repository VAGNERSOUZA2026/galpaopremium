import streamlit as st

# Exemplo de função auxiliar (caso já não estejam no seu escopo global)
def salvar_pedidos(pedidos):
    # Lógica para salvar no arquivo JSON/banco
    pass

def registrar_log(usuario, acao, detalhes):
    # Lógica de registro de auditoria
    pass

def sincronizar_estoque_com_pedidos(pedidos, estoque):
    # Sincronização opcional
    pass

def componente_leitor_barcode(key):
    # Componente de câmera ou input de código de barras
    pass

# ==========================================================
# ESTRUTURA DE ABAS PARA OS PEDIDOS
# ==========================================================
st.markdown("## 📦 Gestão de Pedidos e Expedição WMS")

# Criação correta das abas para evitar o NameError
aba_ped1, aba_ped2 = st.tabs(["📋 Cadastro de Pedidos", "🔍 Checkout WMS (Conferência)"])

# ----------------------------------------------------------
# ABA 1: CADASTRO DE PEDIDOS
# ----------------------------------------------------------
with aba_ped1:
    st.subheader("📝 Cadastrar Novo Pedido / Mapa")
    
    id_pedido = st.text_input("Número do Pedido / Identificação:", key="input_id_pedido")
    
    st.markdown("#### Itens do Pedido")
    # Aqui entraria a sua lógica de inserção de itens (via texto, arquivo ou seleção)
    # Exemplo simulado de itens novos obtidos no cadastro:
    itens_novos = st.session_state.get("temp_itens_cadastro", [])
    
    # Exemplo de input rápido para teste se não houver lista dinâmica:
    col_cad1, col_cad2 = st.columns(2)
    with col_cad1:
        vinho_cad = st.text_input("Nome do Vinho:", key="cad_vinho_nome")
    with col_cad2:
        qtd_cad = st.number_input("Quantidade:", min_value=1, value=1, key="cad_vinho_qtd")
        
    if st.button("➕ Adicionar Item à Lista do Pedido"):
        if vinho_cad:
            if "temp_itens_cadastro" not in st.session_state:
                st.session_state.temp_itens_cadastro = []
            st.session_state.temp_itens_cadastro.append({
                "nome": vinho_cad,
                "quantidade": qtd_cad,
                "qtd_separada": 0,
                "separado": False,
                "divergencia": -qtd_cad
            })
            st.success(f"Item '{vinho_cad}' adicionado temporariamente!")
            st.rerun()

    if "temp_itens_cadastro" in st.session_state and st.session_state.temp_itens_cadastro:
        st.write("Itens adicionados para este pedido:")
        for idx, it in enumerate(st.session_state.temp_itens_cadastro):
            st.write(f"- {it['nome']} ({it['quantidade']} un)")
            
        if st.button("💾 Salvar Pedido Definitivamente", type="primary"):
            if not id_pedido:
                st.error("Informe o número de identificação do pedido.")
            else:
                if "pedidos" not in st.session_state:
                    st.session_state.pedidos = []
                    
                ids_existentes = [p['id'] for p in st.session_state.pedidos]
                if id_pedido in ids_existentes:
                    st.error(f"O ID de pedido '{id_pedido}' já existe.")
                else:
                    novo_pedido = {
                        "id": id_pedido,
                        "status": "Pendente",
                        "itens": st.session_state.temp_itens_cadastro
                    }
                    st.session_state.pedidos.append(novo_pedido)
                    salvar_pedidos(st.session_state.pedidos)
                    registrar_log(st.session_state.get("usuario_logado", {}).get("nome", "Admin"), "Cadastrou Pedido", id_pedido)
                    
                    # Limpa temporários
                    st.session_state.temp_itens_cadastro = []
                    st.success(f"Pedido Nº {id_pedido} cadastrado com sucesso!")
                    st.rerun()


# ----------------------------------------------------------
# ABA 2: CHECKOUT ESTILO WMS (DUAS COLUNAS)
# ----------------------------------------------------------
with aba_ped2:
    st.subheader("🔍 Checkout Estilo WMS - Conferência de Pedidos")
    
    if "pedidos" not in st.session_state or not st.session_state.pedidos:
        st.info("Nenhum pedido cadastrado no sistema.")
    else:
        # Seleção do pedido ativo
        ids_pedidos = [p['id'] for p in st.session_state.pedidos]
        pedido_id_sel = st.selectbox("Selecione o Número do Pedido / Mapa para Conferência:", ids_pedidos, key="sel_pedido_wms")
        
        pedido_ativo = next((p for p in st.session_state.pedidos if p['id'] == pedido_id_sel), None)
        
        if pedido_ativo:
            st.markdown(f"**Status Atual:** `{pedido_ativo.get('status', 'Pendente')}`")
            st.markdown("---")
            
            # Leitor e Ações Manuais
            col_leitor, col_busca_manual = st.columns([1, 1])
            with col_leitor:
                st.markdown("📷 **Leitor de Câmera (WMS)**")
                componente_leitor_barcode("checkout_camera")
                codigo_lido = st.session_state.get("codigo_bipado_checkout", "")
            
            with col_busca_manual:
                st.markdown("⌨️ **Busca / Confirmação Manual**")
                vinho_busca = st.selectbox(
                    "Selecione o vinho para dar baixa:", 
                    [f"{i['nome']} (Ped: {i['quantidade']} un)" for i in pedido_ativo['itens']],
                    key="select_vinho_wms"
                )
                qtd_informada = st.number_input("Quantidade a conferir:", min_value=1, value=1, key="qtd_wms_manual")
                btn_dar_baixa_manual = st.button("✅ Confirmar Separação Manual", use_container_width=True)

            # Processamento de baixa manual
            if btn_dar_baixa_manual and vinho_busca:
                nome_selecionado = vinho_busca.split(" (Ped:")[0]
                item_pedido = next((i for i in pedido_ativo['itens'] if i['nome'].lower() == nome_selecionado.lower()), None)
                if item_pedido:
                    item_pedido['qtd_separada'] = item_pedido.get('qtd_separada', 0) + qtd_informada
                    item_pedido['divergencia'] = item_pedido['qtd_separada'] - item_pedido['quantidade']
                    if item_pedido['qtd_separada'] >= item_pedido['quantidade']:
                        item_pedido['separado'] = True
                    
                    salvar_pedidos(st.session_state.pedidos)
                    registrar_log(st.session_state.get("usuario_logado", {}).get("nome", "Admin"), "Baixa Manual WMS", f"{nome_selecionado} ({qtd_informada} un)")
                    st.success(f"Adicionadas {qtd_informada} unidades para '{nome_selecionado}'!")
                    st.rerun()

            st.markdown("---")
            
            # ==================== LAYOUT WMS (2 COLUNAS) ====================
            col_esq, col_dir = st.columns(2)
            
            with col_esq:
                st.markdown("### 📦 Itens Pendentes / Faltantes")
                # Filtra itens que ainda não foram totalmente separados
                itens_pendentes = [i for i in pedido_ativo['itens'] if not i.get('separado', False) and i.get('qtd_separada', 0) < i['quantidade']]
                
                if not itens_pendentes:
                    st.success("🎉 Todos os itens deste pedido foram separados!")
                else:
                    for it in itens_pendentes:
                        falta = it['quantidade'] - it.get('qtd_separada', 0)
                        st.markdown(f"""
                        <div style='padding: 10px; margin-bottom: 8px; border-radius: 5px; background-color: #f9f9f9; border-left: 5px solid #d9534f;'>
                            <b>🍷 {it['nome']}</b><br>
                            Pedida: {it['quantidade']} un | Separada: {it.get('qtd_separada', 0)} un<br>
                            <b style='color: #d9534f;'>Pendente: {max(0, falta)} un</b>
                        </div>
                        """, unsafe_allow_html=True)

            with col_dir:
                st.markdown("### ✅ Itens Conferidos / Separados")
                # Filtra itens que possuem alguma quantidade conferida ou separada
                itens_conferidos = [i for i in pedido_ativo['itens'] if i.get('separado', False) or i.get('qtd_separada', 0) > 0]
                
                if not itens_conferidos:
                    st.info("Nenhum item conferido até o momento.")
                else:
                    for it in itens_conferidos:
                        st.markdown(f"""
                        <div style='padding: 10px; margin-bottom: 8px; border-radius: 5px; background-color: #f9f9f9; border-left: 5px solid #28a745;'>
                            <b>🍷 {it['nome']}</b><br>
                            Pedida: {it['quantidade']} un | <b style='color: #28a745;'>Separada: {it.get('qtd_separada', 0)} un</b><br>
                            Status: Conferido ✔️
                        </div>
                        """, unsafe_allow_html=True)

            # Botão de conclusão do pedido
            st.markdown("---")
            if st.button("🏁 Concluir e Finalizar Expedição deste Pedido", use_container_width=True):
                pedido_ativo['status'] = "Concluído / Expedido"
                salvar_pedidos(st.session_state.pedidos)
                registrar_log(st.session_state.get("usuario_logado", {}).get("nome", "Admin"), "Finalizou Expedição WMS", pedido_ativo['id'])
                st.success(f"Pedido {pedido_ativo['id']} concluído com sucesso!")
                st.rerun()
