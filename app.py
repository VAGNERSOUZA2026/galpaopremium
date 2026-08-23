with aba_ped2:
        # Filtra apenas os pedidos que ainda estão pendentes de conferência/expedição
        mapas_pendentes = [p for p in st.session_state.pedidos if p.get('status', 'Pendente') == "Pendente"]
        
        if not mapas_pendentes:
            st.success("🎉 Todos os pedidos cadastrados já foram conferidos e expedidos! Nenhum pedido pendente no momento.")
        else:
            mapas_disponiveis = [p['id'] for p in mapas_pendentes]
            
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
                                        st.warning(f"⚠️ Atenção! Quantidade separada ({item['qtd_separada']}) diverge para {dif_tipo} da pedida ({item['quantidade']}) para el item '{item['nome']}'.")
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

                itens_com_divergencia_nao_autorizados = [i for i in pedido_ativo['itens'] if i.get('divergencia', 0) != 0 and not i.get('autorizado_divergencia', False)]
                
                if itens_com_divergencia_nao_autorizados:
                    st.markdown("---")
                    st.error("🔒 Existem itens com quantidade incorreta / divergente aguardando correção ou liberação de senha (Senha: 2026):")
                    for it_div in itens_com_divergencia_nao_autorizados:
                        st.markdown(f"**Item:** {it_div['nome']} | Pedido: {it_div['quantidade']} | Separado: {it_div['qtd_separada']} (Divergência: {it_div['divergencia']:+d})")
                        
                        c_acao1, c_acao2 = st.columns(2)
                        with c_acao1:
                            if st.button("🔄 Corrigir para Qtd Pedida", key=f"corrigir_{it_div['nome']}_{pedido_ativo['id']}"):
                                it_div['qtd_separada'] = it_div['quantidade']
                                it_div['divergencia'] = 0
                                it_div['autorizado_divergencia'] = True
                                it_div['separado'] = True
                                salvar_pedidos(st.session_state.pedidos)
                                st.success(f"Quantidade de '{it_div['nome']}' corrigida com sucesso!")
                                st.rerun()
                                
                        senha_chave_input = f"pass_{it_div['nome']}_{pedido_ativo['id']}"
                        senha_item = st.text_input("Digite a senha de liberação de divergência (2026):", type="password", key=senha_chave_input)
                        
                        if st.button("Autorizar Com Divergência", key=f"btn_autorizar_{it_div['nome']}_{pedido_ativo['id']}"):
                            if senha_item == SENHA_DIVERGENCIA:
                                it_div['autorizado_divergencia'] = True
                                it_div['separado'] = True
                                salvar_pedidos(st.session_state.pedidos)
                                registrar_log(st.session_state.usuario_logado['nome'], "Liberou Divergência Item", it_div['nome'])
                                st.success(f"Divergência autorizada para '{it_div['nome']}'!")
                                st.rerun()
                            else:
                                st.error("Senha incorreta ou em branco. Digite 2026 e clique explicitamente no botão.")
                        st.markdown("---")

                with st.expander("➕ Inserção Manual Extra (Solicitação de Trajeto / Adicionar Vinho Não Listado)"):
                    with st.form(key=f"form_extra_{pedido_ativo['id']}"):
                        nome_extra = st.text_input("Nome do Vinho Extra").strip().title()
                        qtd_extra = st.number_input("Quantidade", min_value=1, value=1)
                        senha_extra = st.text_input("Senha de Liberação (2026)", type="password")
                        
                        btn_submit_extra = st.form_submit_button("Adicionar ao Pedido com Senha")
                        
                        if btn_submit_extra:
                            if nome_extra:
                                if senha_extra == SENHA_DIVERGENCIA:
                                    novo_item_extra = {
                                        "nome": nome_extra,
                                        "safra": "Extra",
                                        "quantidade": 0,
                                        "separado": True,
                                        "qtd_separada": int(qtd_extra),
                                        "divergencia": int(qtd_extra),
                                        "autorizado_divergencia": True
                                    }
                                    pedido_ativo['itens'].append(novo_item_extra)
                                    salvar_pedidos(st.session_state.pedidos)
                                    st.success("Vinho extra incluído e autorizado com sucesso!")
                                    st.rerun()
                                else:
                                    st.error("Senha incorreta para item extra. Digite 2026.")
                            else:
                                st.error("Informe o nome do vinho.")

                st.markdown("---")
                
                col_esq, col_dir = st.columns(2)
                
                with col_esq:
                    st.markdown("<h4 style='color: #7A1C2E;'>PRODUTOS A CONFERIR</h4>", unsafe_allow_html=True)
                    pendentes = [i for i in pedido_ativo['itens'] if not i.get('separado', False)]
                    if not pendentes:
                        st.success("🎉 Todos os produtos deste mapa foram conferidos!")
                    for item in pendentes:
                        st.markdown(f"""
                        <div style='background: #FFF; padding: 10px; border-radius: 8px; margin-bottom: 8px; border-left: 4px solid #7A1C2E;'>
                            <b>{item['nome']}</b> (Safra: {item.get('safra', 'N/A')})<br>
                            Qtd Pedida: <b>{item['quantidade']}</b> | Separada: {item.get('qtd_separada', 0)}
                        </div>
                        """, unsafe_allow_html=True)
                        
                with col_dir:
                    st.markdown("<h4 style='color: #2E7D32;'>PRODUTOS JÁ CONFERIDOS</h4>", unsafe_allow_html=True)
                    conferidos = [i for i in pedido_ativo['itens'] if i.get('separado', False)]
                    if not conferidos:
                        st.info("Nenhum produto conferido ainda.")
                    for item in conferidos:
                        dif = item.get('divergencia', 0)
                        if dif != 0:
                            dif_texto = f" | <span style='color: red;'>Divergência: {dif:+d}</span>"
                        else:
                            dif_texto = " | <span style='color: green;'>Correto</span>"
                            
                        st.markdown(f"""
                        <div style='background: #FFF; padding: 10px; border-radius: 8px; margin-bottom: 8px; border-left: 4px solid #2E7D32;'>
                            <b>{item['nome']}</b> (Safra: {item.get('safra', 'N/A')}){dif_texto}<br>
                            Qtd Pedida: <b>{item['quantidade']}</b> | Separada: <b>{item.get('qtd_separada', 0)}</b>
                        </div>
                        """, unsafe_allow_html=True)
                
                st.markdown("---")
                
                todos_conferidos = all(i.get('separado', False) for i in pedido_ativo['itens'])
                todas_divergencias_ok = all(i.get('autorizado_divergencia', False) for i in pedido_ativo['itens'] if i.get('divergencia', 0) != 0)
                
                if todos_conferidos and todas_divergencias_ok:
                    if st.button("🚀 Concluir e Finalizar Expedição deste Mapa", use_container_width=True):
                        pedido_ativo['status'] = "Concluído / Expedido"
                        salvar_pedidos(st.session_state.pedidos)
                        registrar_log(st.session_state.usuario_logado['nome'], "Finalizou Expedição Mapa", pedido_ativo['id'])
                        st.success("🎉 Expedição concluída com sucesso! O painel da matriz foi atualizado.")
                        st.rerun()
                else:
                    st.warning("⚠️ Para concluir a expedição, todos os itens precisam estar conferidos e eventuais divergências autorizadas por senha.")
