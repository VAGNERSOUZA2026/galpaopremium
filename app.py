elif st.session_state.menu_atual == "PedidosMatriz":
    st.subheader("📦 Separação no Corredor por Leitor de Código de Barras")
    st.markdown("Caminhe pelo galpão escaneando os códigos de barras dos produtos para identificá-los instantaneamente no pedido ativo.")

    if not st.session_state.pedidos:
        st.info("Nenhum pedido ativo no sistema.")
    else:
        ids_ativos = [p['id'] for p in st.session_state.pedidos if p.get('status') != "Concluído / Expedido"]
        
        if not ids_ativos:
            st.success("Todos os pedidos já foram concluídos!")
        else:
            # Seleção do pedido que está sendo separado no momento
            pedido_sep_id = st.selectbox("Selecione o Pedido em Separação:", ids_ativos, key="select_sep_corredor")
            pedido_obj = next((p for p in st.session_state.pedidos if p['id'] == pedido_sep_id), None)

            if pedido_obj:
                st.markdown("---")
                st.markdown("#### 📷 Aponte a câmera para o Código de Barras da Garrafa / Caixa")
                
                # Componente de leitura contínua
                componente_leitor_barcode("leitor_corredor")

                # Captura o código bipado pela URL/Query Params que o componente injeta
                codigo_bipado = st.session_state.get("codigo_bipado_corredor", "")
                
                # Verificamos também se veio via parâmetro de query do Streamlit recarregado
                if "scanned_leitor_corredor" in st.query_params:
                    codigo_bipado = st.query_params["scanned_leitor_corredor"]
                    del st.query_params["scanned_leitor_corredor"]

                if codigo_bipado:
                    codigo_limpo = str(codigo_bipado).strip()
                    st.success(f"🔍 Código escaneado: **{codigo_limpo}**")

                    # 1. Buscar no Estoque qual vinho tem esse código de barras
                    vinho_encontrado = next((v for v in st.session_state.estoque if str(v.get('codigo_barras', '')).strip() == codigo_limpo), None)

                    if vinho_encontrado:
                        nome_vinho_estoque = vinho_encontrado['nome'].lower()
                        st.info(f"📍 Localização no Galpão: **{vinho_encontrado.get('localizacao')}** (Lado: {vinho_encontrado.get('lado')})")
                        
                        # 2. Procurar se esse vinho está no pedido ativo
                        encontrado_no_pedido = False
                        for item in pedido_obj['itens']:
                            if item['nome'].lower() in nome_vinho_estoque or nome_vinho_estoque in item['nome'].lower():
                                encontrado_no_pedido = True
                                item['qtd_separada'] = item.get('qtd_separada', 0) + 1
                                item['divergencia'] = item['qtd_separada'] - item['quantidade']
                                salvar_pedidos(st.session_state.pedidos)
                                st.toast(f"✅ Item atualizado no pedido: {item['nome']} (Sep.: {item['qtd_separada']}/{item['quantidade']})", icon="🍷")
                                break
                        
                        if not encontrado_no_pedido:
                            st.warning(f"⚠️ O vinho '{vinho_encontrado['nome']}' foi encontrado no estoque ({vinho_encontrado.get('localizacao')}), mas ele **não consta** neste pedido!")
                    else:
                        st.error(f"❌ Nenhum vinho cadastrado no estoque com o código de barras: {codigo_limpo}")

                st.markdown("---")
                st.markdown("#### 📋 Acompanhamento da Separação deste Pedido:")
                
                for idx, item in enumerate(pedido_obj['itens']):
                    cor_status = "#2E7D32" if item.get('qtd_separada', 0) >= item['quantidade'] else "#C62828"
                    st.markdown(f"""
                    <div style='background: #FFF; padding: 10px; border-radius: 8px; border: 1px solid #E9ECEF; margin-bottom: 8px;'>
                        <b>{item['nome']}</b> (Safra: {item.get('safra', 'N/A')})<br>
                        Pedido: <b>{item['quantidade']}</b> | Separado: <b style='color: {cor_status};'>{item.get('qtd_separada', 0)}</b>
                    </div>
                    """, unsafe_allow_html=True)

                if st.button("🚀 Finalizar Separação e Enviar para Expedição", use_container_width=True):
                    pedido_obj['status'] = "Concluído / Expedido"
                    salvar_pedidos(st.session_state.pedidos)
                    registrar_log(st.session_state.usuario_logado['nome'], "Separação Concluída via Leitor", str(pedido_sep_id))
                    st.success("Pedido finalizado com sucesso!")
                    st.rerun()
