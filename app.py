with aba_ped2:
        st.subheader("🔍 Checkout Estilo WMS - Conferência de Pedidos")
        
        if not st.session_state.pedidos:
            st.info("Nenhum pedido cadastrado no sistema.")
        else:
            # Seleção do pedido ativo
            ids_pedidos = [p['id'] for p in st.session_state.pedidos]
            pedido_id_sel = st.selectbox("Selecione o Número do Pedido / Mapa para Conferência:", ids_pedidos, key="sel_pedido_wms")
            
            pedido_ativo = next((p for p in st.session_state.pedidos if p['id'] == pedido_id_sel), None)
            
            if pedido_ativo:
                st.markdown(f"**Status Atual:** `{pedido_ativo.get('status', 'Pendente')}` | **Data:** {pedido_ativo.get('data', 'N/A')}")
                st.markdown("---")
                
                # Leitor de código de barras rápido para o WMS
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

                # Processamento se houver código bipado pela câmera
                if codigo_lido:
                    # Tenta achar o vinho pelo código de barras no estoque geral
                    vinho_encontrado = next((v for v in st.session_state.estoque if v.get('codigo_barras') == codigo_lido), None)
                    if vinho_encontrado:
                        nome_vinho_lido = vinho_encontrado['nome']
                        # Procura no pedido ativo
                        item_pedido = next((i for i in pedido_ativo['itens'] if i['nome'].lower() == nome_vinho_lido.lower()), None)
                        if item_pedido:
                            item_pedido['qtd_separada'] = item_pedido.get('qtd_separada', 0) + 1
                            item_pedido['divergencia'] = item_pedido['qtd_separada'] - item_pedido['quantidade']
                            if item_pedido['qtd_separada'] >= item_pedido['quantidade']:
                                item_pedido['separado'] = True
                                item_pedido['autorizado_divergencia'] = True
                            salvar_pedidos(st.session_state.pedidos)
                            registrar_log(st.session_state.usuario_logado['nome'], "Bipou Item WMS", f"{nome_vinho_lido} (+1)")
                            st.success(f"➕ 1 unidade de '{nome_vinho_lido}' conferida via código de barras!")
                            st.session_state.codigo_bipado_checkout = ""
                            st.rerun()
                        else:
                            st.error(f"⚠️ O vinho '{nome_vinho_lido}' não pertence a este pedido!")
                    else:
                        st.error(f"⚠️ Código de barras '{codigo_lido}' não encontrado no cadastro do galpão.")
                    st.session_state.codigo_bipado_checkout = ""

                # Processamento da baixa manual
                if btn_dar_baixa_manual and vinho_busca:
                    nome_selecionado = vinho_busca.split(" (Ped:")[0]
                    item_pedido = next((i for i in pedido_ativo['itens'] if i['nome'].lower() == nome_selecionado.lower()), None)
                    if item_pedido:
                        item_pedido['qtd_separada'] = item_pedido.get('qtd_separada', 0) + qtd_informada
                        item_pedido['divergencia'] = item_pedido['qtd_separada'] - item_pedido['quantidade']
                        if item_pedido['qtd_separada'] >= item_pedido['quantidade']:
                            item_pedido['separado'] = True
                            item_pedido['autorizado_divergencia'] = True
                        salvar_pedidos(st.session_state.pedidos)
                        registrar_log(st.session_state.usuario_logado['nome'], "Baixa Manual WMS", f"{nome_selecionado} ({qtd_informada} un)")
                        st.success(f"Adicionadas {qtd_informada} unidades para '{nome_selecionado}'!")
                        st.rerun()

                st.markdown("---")
                
                # ==================== LAYOUT WMS (2 COLUNAS) ====================
                col_esq, col_dir = st.columns(2)
                
                with col_esq:
                    st.markdown("### 📦 Itens Pendentes / Faltantes")
                    itens_pendentes = [i for i in pedido_ativo['itens'] if not i.get('separado', False) or i.get('divergencia', 0) < 0]
                    
                    if not itens_pendentes:
                        st.success("🎉 Todos os itens do pedido foram separados!")
                    else:
                        for it in itens_pendentes:
                            falta = it['quantidade'] - it.get('qtd_separada', 0)
                            st.markdown(f"""
                            <div class='wine-card' style='border-left: 5px solid #d9534f;'>
                                <div class='wine-title'>🍷 {it['nome']} ({it.get('safra', 'N/A')})</div>
                                <b>Pedida:</b> {it['quantidade']} un | <b>Separada:</b> {it.get('qtd_separada', 0)} un<br>
                                <b style='color: #d9534f;'>Pendente:</b> {max(0, falta)} un
                            </div>
                            """, unsafe_allow_html=True)

                with col_dir:
                    st.markdown("### ✅ Itens Conferidos / Separados")
                    itens_conferidos = [i for i in pedido_ativo['itens'] if i.get('separado', False) or i.get('qtd_separada', 0) > 0]
                    
                    if not itens_conferidos:
                        st.info("Nenhum item conferido até o momento.")
                    else:
                        for it in itens_conferidos:
                            st.markdown(f"""
                            <div class='wine-card' style='border-left: 5px solid #28a745;'>
                                <div class='wine-title'>🍷 {it['nome']} ({it.get('safra', 'N/A')})</div>
                                <b>Pedida:</b> {it['quantidade']} un | <b style='color: #28a745;'>Separada:</b> {it.get('qtd_separada', 0)} un<br>
                                <b>Status:</b> Conferido com sucesso ✔️
                            </div>
                            """, unsafe_allow_html=True)

                # Botão para finalizar o pedido completo
                st.markdown("---")
                if st.button("🏁 Concluir e Finalizar Expedição deste Pedido", use_container_width=True):
                    pedido_ativo['status'] = "Concluído / Expedido"
                    salvar_pedidos(st.session_state.pedidos)
                    registrar_log(st.session_state.usuario_logado['nome'], "Finalizou Expedição WMS", pedido_ativo['id'])
                    st.success(f"Pedido {pedido_ativo['id']} concluído com sucesso!")
                    st.rerun()
