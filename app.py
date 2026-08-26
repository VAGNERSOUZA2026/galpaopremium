with aba_ped1:
        st.markdown("Cadastre o mapa de separação enviado pela matriz ou adicione itens escaneando os códigos de barras.")
        proximo_numero = len(st.session_state.pedidos) + 1
        id_sugerido = f"123{proximo_numero:03d}"
        
        # Inicializa a lista de itens temporária do novo pedido na sessão se não existir
        if "itens_novo_pedido_temp" not in st.session_state:
            st.session_state.itens_novo_pedido_temp = []

        id_pedido = st.text_input("Código de Barras do Mapa (Ex: 1234552)", value=id_sugerido)
        
        st.markdown("---")
        st.markdown("#### 📷 Adicionar Vinho via Leitor de Código de Barras")
        componente_leitor_barcode("cadastro_pedido_camera")
        
        # Captura o código lido pela câmera do celular no cadastro
        codigo_lido_cadastro = st.session_state.get("codigo_bipado_cadastro_pedido_camera", "")
        if "scanned_cadastro_pedido_camera" in st.query_params:
            codigo_lido_cadastro = st.query_params["scanned_cadastro_pedido_camera"]
            del st.query_params["scanned_cadastro_pedido_camera"]

        if codigo_lido_cadastro:
            cod_limpo = str(codigo_lido_cadastro).strip()
            # Busca no estoque pelo código de barras
            vinho_cad = next((v for v in st.session_state.estoque if str(v.get('codigo_barras', '')).strip() == cod_limpo), None)
            if vinho_cad:
                # Verifica se já está na lista temporária para somar a quantidade
                encontrado_temp = False
                for it in st.session_state.itens_novo_pedido_temp:
                    if it['nome'].lower() == vinho_cad['nome'].lower():
                        it['quantidade'] += 1
                        encontrado_temp = True
                        break
                if not encontrado_temp:
                    st.session_state.itens_novo_pedido_temp.append({
                        "nome": vinho_cad['nome'],
                        "safra": vinho_cad.get('safra', ''),
                        "quantidade": 1,
                        "separado": False,
                        "qtd_separada": 0,
                        "divergencia": 0,
                        "autorizado_divergencia": False
                    })
                st.success(f"✅ Vinho adicionado à lista: **{vinho_cad['nome']}**")
            else:
                st.error(f"❌ Código de barras '{cod_limpo}' não encontrado no estoque do galpão!")

        st.markdown("---")
        arq_pedido = st.file_uploader("Ou envie Arquivo de Pedido (Excel ou TXT)", type=["xlsx", "xls", "txt"])
        texto_manual_pedido = st.text_area("Ou digite um item por linha (Nome / Safra / Qtd):", value="")

        # Exibe os itens adicionados até o momento via leitor/manual
        if st.session_state.itens_novo_pedido_temp:
            st.markdown("##### 🛒 Itens na Lista do Novo Pedido:")
            for idx_t, it_t in enumerate(st.session_state.itens_novo_pedido_temp):
                st.write(f"- **{it_t['nome']}** (Safra: {it_t.get('safra', 'N/A')}) - Qtd: {it_t['quantidade']}")
            if st.button("🧹 Limpar Lista Temporária"):
                st.session_state.itens_novo_pedido_temp = []
                st.rerun()

        if st.button("💾 Salvar Pedido Completo no Sistema", use_container_width=True):
            itens_finais = list(st.session_state.itens_novo_pedido_temp)
            if arq_pedido is not None:
                itens_finais.extend(extrair_pedidos_de_arquivo(arq_pedido))
            if texto_manual_pedido.strip():
                for linha in texto_manual_pedido.split("\n"):
                    if linha.strip():
                        itens_finais.append(interpretar_linha_pedido(linha))

            if itens_finais:
                novo_registro_pedido = {
                    "id": str(id_pedido).strip(),
                    "data": obter_horario_brasilia().strftime("%d/%m/%Y %H:%M"),
                    "itens": itens_finais,
                    "status": "Pendente"
                }
                st.session_state.pedidos.append(novo_registro_pedido)
                salvar_pedidos(st.session_state.pedidos)
                sincronizar_estoque_com_pedidos(st.session_state.pedidos, st.session_state.estoque)
                registrar_log(st.session_state.usuario_logado['nome'], "Cadastrou Pedido via Leitor/Manual", str(id_pedido))
                st.session_state.itens_novo_pedido_temp = []
                st.success(f"Pedido {id_pedido} salvo com sucesso!")
                st.rerun()
            else:
                st.error("Adicione itens usando o leitor de código de barras, arquivo ou digitação.")
