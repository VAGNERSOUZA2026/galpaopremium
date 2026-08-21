elif st.session_state.menu_atual == "PedidosMatriz":
    st.subheader("📦 Checkout de Expedição e Mapa de Separação (WMS)")
    
    aba_ped1, aba_ped2 = st.tabs(["📋 Enviar/Novo Pedido", "🔍 Conferência WMS (Checkout)"])
    
    with aba_ped1:
        st.markdown("Envie a lista enviada pela matriz (Excel ou TXT) ou cadastre o mapa manualmente.")
        proximo_numero = len(st.session_state.pedidos) + 1
        id_sugerido = f"123{proximo_numero:03d}"
        
        with st.form("form_novo_pedido"):
            id_pedido = st.text_input("Número do Mapa / Pedido (Ex: 1234552)", value=id_sugerido)
            arq_pedido = st.file_uploader("Arquivo de Pedido (Excel ou TXT)", type=["xlsx", "xls", "txt"])
            texto_manual_pedido = st.text_area("Ou digite os itens (Ex: Faleria Pinot Noir Reserva 23 / 1 Caixa)")
            
            if st.form_submit_button("💾 Salvar Pedido no Sistema"):
                itens_novos = []
                if arq_pedido is not None:
                    itens_novos = extrair_pedidos_de_arquivo(arq_pedido)
                if texto_manual_pedido.strip():
                    for linha in texto_manual_pedido.split("\n"):
                        if linha.strip():
                            itens_novos.append(interpretar_linha_pedido(linha))
                
                if itens_novos:
                    novo_registro_pedido = {
                        "id": str(id_pedido).strip(),
                        "data": obter_horario_brasilia().strftime("%d/%m/%Y %H:%M"),
                        "itens": itens_novos,
                        "status": "Pendente"
                    }
                    st.session_state.pedidos.append(novo_registro_pedido)
                    salvar_pedidos(st.session_state.pedidos)
                    registrar_log(st.session_state.usuario_logado['nome'], "Novo Pedido Matriz", str(id_pedido))
                    st.success(f"Pedido / Mapa {id_pedido} cadastrado com sucesso!")
                    st.rerun()
                else:
                    st.error("Adicione ao menos um item ou arquivo válido.")

    with aba_ped2:
        st.markdown("### Conferência de Expedição por Código de Barras")
        
        if not st.session_state.pedidos:
            st.warning("Nenhum pedido cadastrado no sistema.")
        else:
            mapas_disponiveis = [p['id'] for p in st.session_state.pedidos]
            mapa_selecionado_id = st.selectbox("Código de Barras Mapa (Selecione ou Digite)", mapas_disponiveis)
            
            pedido_ativo = next((p for p in st.session_state.pedidos if p['id'] == mapa_selecionado_id), None)
            
            if pedido_ativo:
                st.markdown(f"""
                <div style='background: #FFF; padding: 10px; border-radius: 8px; border: 1px solid #E9ECEF; margin-bottom: 15px;'>
                    <b>Conferência do Mapa cod. {pedido_ativo['id']}</b><br>
                    Data/Carga: {pedido_ativo['data']} | Status: <b>{pedido_ativo.get('status', 'Pendente')}</b>
                </div>
                """, unsafe_allow_html=True)
                
                col_b1, col_b2, col_b3 = st.columns([2, 1, 1])
                with col_b1:
                    cod_barras_input = st.text_input("*Código de Barras ou Nome do Vinho", key="input_bipagem_wms")
                with col_b2:
                    qtd_input = st.number_input("*Qtd", min_value=1, value=1, key="input_qtd_wms")
                with col_b3:
                    st.write("")
                    btn_conferir = st.button("Conferir", use_container_width=True)
                
                if btn_conferir and cod_barras_input:
                    encontrou = False
                    for item in pedido_ativo['itens']:
                        vinho_no_estoque = next((v for v in st.session_state.estoque if v['nome'].lower() in item['nome'].lower() or v.get('codigo_barras') == cod_barras_input), None)
                        
                        match_nome = cod_barras_input.lower() in item['nome'].lower()
                        match_bc = vinho_no_estoque and vinho_no_estoque.get('codigo_barras') == cod_barras_input
                        
                        if match_nome or match_bc:
                            item['qtd_separada'] = item.get('qtd_separada', 0) + qtd_input
                            if item['qtd_separada'] >= item['quantidade']:
                                item['separado'] = True
                            encontrou = True
                            break
                    
                    if encontrou:
                        salvar_pedidos(st.session_state.pedidos)
                        st.success("Quantidade conferida com sucesso!")
                        st.rerun()
                    else:
                        st.error("Produto não encontrado neste mapa ou código inválido.")

                st.markdown("---")
                
                col_esq, col_dir = st.columns(2)
                
                with col_esq:
                    st.markdown("<h4 style='color: #7A1C2E;'>PRODUTOS A CONFERIR</h4>", unsafe_allow_html=True)
                    pendentes = [i for i in pedido_ativo['itens'] if not i.get('separado', False)]
                    if not pendentes:
                        st.success("🎉 Todos os produtos deste mapa foram conferidos!")
                    for idx, item in enumerate(pendentes):
                        st.markdown(f"""
                        <div style='background: #FFF; padding: 10px; border-radius: 8px; margin-bottom: 8px; border-left: 4px solid #7A1C2E;'>
                            <b>{item['nome']}</b> (Safra: {item.get('safra', 'N/A')})<br>
                            Qtd Pedida: <b>{item['quantidade']}</b> | Separada: {item.get('qtd_separada', 0)}
                        </div>
                        """, unsafe_allow_html=True)
                        
                with col_dir:
                    st.markdown("<h4 style='color: #2E7D32;'>PRODUTOS CONFERIDOS</h4>", unsafe_allow_html=True)
                    conferidos = [i for i in pedido_ativo['itens'] if i.get('separado', False)]
                    if not conferidos:
                        st.info("Nenhum produto conferido ainda.")
                    for idx, item in enumerate(conferidos):
                        st.markdown(f"""
                        <div style='background: #F1F8E9; padding: 10px; border-radius: 8px; margin-bottom: 8px; border-left: 4px solid #2E7D32;'>
                            ✅ <b>{item['nome']}</b> ({item.get('safra', 'N/A')}) - {item.get('qtd_separada', 0)} unidade(s) conferida(s)
                        </div>
                        """, unsafe_allow_html=True)
