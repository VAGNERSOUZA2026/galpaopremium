with aba_ped2:
        if not st.session_state.pedidos:
            st.warning("Nenhum pedido cadastrado no sistema. Cadastre na aba anterior.")
        else:
            mapas_disponiveis = [p['id'] for p in st.session_state.pedidos]
            
            c_top1, _ = st.columns([2, 2])
            with c_top1:
                mapa_selecionado_id = st.selectbox(
                    "🔍 Selecione o Pedido / Mapa para Conferir:", 
                    mapas_disponiveis, 
                    index=len(mapas_disponiveis) - 1
                )
            
            pedido_ativo = next((p for p in st.session_state.pedidos if p['id'] == mapa_selecionado_id), None)
            
            if pedido_ativo:
                status_atual = pedido_ativo.get('status', 'Pendente')
                cor_status = "#2E7D32" if status_atual == "Concluído / Expedido" else "#7A1C2E"
                
                st.markdown(f"""
                <div style='background: #FFF; padding: 10px; border-radius: 8px; border: 1px solid #E9ECEF; margin-bottom: 15px;'>
                    <b>Conferência do Mapa cod. {pedido_ativo['id']}</b> | Expedição Nº 41542 | Carga(s) Nº 114971<br>
                    Data/Carga: {pedido_ativo['data']} | Status: <b style='color: {cor_status};'>{status_atual}</b>
                </div>
                """, unsafe_allow_html=True)
                
                modo_leitura = st.radio("Forma de Leitura:", ["⌨️ Seleção / Pistola USB", "📷 Câmera do Celular"], horizontal=True)
                
                codigo_capturado = ""
                if modo_leitura == "📷 Câmera do Celular":
                    st.markdown("Aponte a câmera para o código de barras ou QR Code:")
                    componente_leitor_barcode("checkout_camera")
                    codigo_capturado = st.session_state.get("codigo_bipado_checkout", "")
                
                itens_pendentes_lista = [i['nome'] for i in pedido_ativo['itens'] if not i.get('separado', False)]
                
                # Envolvendo a conferência em um st.form para que o Enter não dispare sozinho
                with st.form(key=f"form_conferencia_{pedido_ativo['id']}"):
                    col_b1, col_b2, col_b3 = st.columns([2, 1, 1])
                    with col_b1:
                        if modo_leitura == "📷 Câmera do Celular":
                            cod_barras_input = st.text_input("*Código de Barras ou Nome", value=codigo_capturado)
                        else:
                            if itens_pendentes_lista:
                                opcao_selecionada_dropdown = st.selectbox("Selecione o Vinho da Lista", ["-- Selecione ou Digite --"] + itens_pendentes_lista)
                                if opcao_selecionada_dropdown != "-- Selecione ou Digite --":
                                    cod_barras_input = opcao_selecionada_dropdown
                                else:
                                    cod_barras_input = st.text_input("*Ou digite/bipe o Código de Barras", value="")
                            else:
                                cod_barras_input = st.text_input("*Código de Barras ou Nome", value="")
                    with col_b2:
                        qtd_input = st.number_input("*Qtd", min_value=1, value=1)
                    with col_b3:
                        st.write("")
                        btn_conferir = st.form_submit_button("Conferir", use_container_width=True)
                    
                    if btn_conferir:
                        if cod_barras_input and cod_barras_input != "-- Selecione ou Digite --":
                            encontrou = False
                            qtd_real_informada = int(qtd_input)
                            
                            for item in pedido_ativo['itens']:
                                if item.get('separado', False) and item.get('divergencia', 0) == 0:
                                    continue

                                vinho_no_estoque = next((v for v in st.session_state.estoque if v['nome'].lower() in item['nome'].lower() or v.get('codigo_barras') == cod_barras_input), None)
                                
                                match_nome = cod_barras_input.lower() in item['nome'].lower()
                                match_bc = vinho_no_estoque and vinho_no_estoque.get('codigo_barras') == cod_barras_input
                                
                                if match_nome or match_bc:
                                    encontrou = True
                                    item['qtd_separada'] = qtd_real_informada
                                    item['divergencia'] = item['qtd_separada'] - item['quantidade']
                                    
                                    if item['divergencia'] == 0:
                                        item['autorizado_divergencia'] = True
                                        item['separado'] = True
                                    else:
                                        item['autorizado_divergencia'] = False
                                        item['separado'] = False
                                        dif_tipo = "mais" if item['divergencia'] > 0 else "menos"
                                        st.warning(f"⚠️ Atenção! Quantidade separada ({item['qtd_separada']}) diverge para {dif_tipo} da pedida ({item['quantidade']}) para o item '{item['nome']}'.")
                                    break
                            
                            if encontrou:
                                if "codigo_bipado_checkout" in st.session_state:
                                    st.session_state.codigo_bipado_checkout = ""
                                salvar_pedidos(st.session_state.pedidos)
                                st.rerun()
                            else:
                                st.error("Produto não encontrado neste mapa ou já totalmente conferido.")
                        else:
                            st.error("Selecione ou informe um produto/código de barras válido.")
