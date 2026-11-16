"""
Databricks App — Painel de Controle Intercompany (Fase 2)
Itens 7 e 8:
  - Painel de Eliminação Patrimonial (Abas: Elimináveis, Sum, Temas Principais)
  - Painel de Eliminação de Resultado + Validador Automático na Camada Silver
"""

from __future__ import annotations
import json
import os
from pathlib import Path
import streamlit as st

from excel_loader import (
    carregar_dados_iniciais_resultado,
    carregar_painel_patrimonial_xlsx,
)
from pipeline_silver_gold import (
    DDL_DATABRICKS_SQL,
    STATUS_ANALISTA_OPCOES,
    STATUS_REVISOR_OPCOES,
    calcular_metricas_patrimonial,
    calcular_metricas_resultado,
    gerar_query_merge_patrimonial,
    validar_totais_resultado_silver,
)

BASE_DIR = Path(__file__).resolve().parent
PLANILHA_OFICIAL = (
    BASE_DIR.parent / "documentacao" / "Painel Eliminação Patrimonial_08-2026.xlsx"
)
ESTADO_PATRIMONIAL_JSON = BASE_DIR / "state_patrimonial.json"
ESTADO_RESULTADO_JSON = BASE_DIR / "state_resultado.json"
CATALOGO = os.getenv("DATABRICKS_CATALOG", "workspace")


def formatar_brl(valor: float | None) -> str:
    if valor is None:
        return "R$ 0,00"
    negativo = valor < 0
    s = f"{abs(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"-R$ {s}" if negativo else f"R$ {s}"


def obter_estado_patrimonial() -> dict:
    if ESTADO_PATRIMONIAL_JSON.exists():
        return json.loads(ESTADO_PATRIMONIAL_JSON.read_text(encoding="utf-8"))
    if PLANILHA_OFICIAL.exists():
        dados = carregar_painel_patrimonial_xlsx(PLANILHA_OFICIAL)
        ESTADO_PATRIMONIAL_JSON.write_text(
            json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return dados
    return {"eliminaveis": [], "sum": [], "temas_principais": []}


def salvar_estado_patrimonial(dados: dict) -> None:
    ESTADO_PATRIMONIAL_JSON.write_text(
        json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def obter_estado_resultado() -> list[dict]:
    if ESTADO_RESULTADO_JSON.exists():
        return json.loads(ESTADO_RESULTADO_JSON.read_text(encoding="utf-8"))
    dados = carregar_dados_iniciais_resultado()
    ESTADO_RESULTADO_JSON.write_text(
        json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return dados


def salvar_estado_resultado(dados: list[dict]) -> None:
    ESTADO_RESULTADO_JSON.write_text(
        json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def recalcular_aba_sum(registros_eliminaveis: list[dict]) -> list[dict]:
    agrupado: dict[str, dict] = {}
    for r in registros_eliminaveis:
        resp = r.get("responsavel", "")
        if resp == "Incorporada":
            continue
        rotulo = "Sem Movimento" if resp == "Z_Sem Movimento" else resp
        item = agrupado.setdefault(
            rotulo,
            {
                "rotulo_linha": rotulo,
                "contagem_cruzamento": 0,
                "soma_mes_atual": 0.0,
                "soma_mes_anterior": 0.0,
            },
        )
        item["contagem_cruzamento"] += 1
        item["soma_mes_atual"] = round(
            item["soma_mes_atual"] + float(r.get("dif_liquida_atual") or 0.0), 2
        )
        item["soma_mes_anterior"] = round(
            item["soma_mes_anterior"] + float(r.get("dif_liquida_anterior") or 0.0), 2
        )

    linhas = list(agrupado.values())
    linhas.append(
        {
            "rotulo_linha": "Total Geral",
            "contagem_cruzamento": sum(i["contagem_cruzamento"] for i in linhas),
            "soma_mes_atual": round(sum(i["soma_mes_atual"] for i in linhas), 2),
            "soma_mes_anterior": round(sum(i["soma_mes_anterior"] for i in linhas), 2),
        }
    )
    return linhas


def main() -> None:
    st.set_page_config(
        page_title="Painel Intercompany — Vivo / Telefônica",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    st.markdown(
        """
        <style>
        .vivo-header {
            background: linear-gradient(90deg, #380054 0%, #660099 60%, #0B1F4D 100%);
            padding: 18px 26px;
            border-radius: 12px;
            color: white;
            margin-bottom: 18px;
        }
        .vivo-header h1 {
            color: white !important;
            font-size: 1.65rem !important;
            margin: 0 !important;
            padding: 0 !important;
        }
        .vivo-header p {
            color: #E2D4F0 !important;
            font-size: 0.92rem !important;
            margin: 4px 0 0 0 !important;
        }
        div[data-testid="stMetric"] {
            background-color: #F8FAFC;
            border: 1px solid #E2E8F0;
            border-left: 5px solid #660099;
            padding: 12px 16px;
            border-radius: 8px;
        }
        </style>
        <div class="vivo-header">
            <h1>Painel de Controle Intercompany — Fechamento Contábil (Fase 2)</h1>
            <p>Visão On-line Única • Camada Silver & Gold (Catálogo: <b>workspace.silver</b> / <b>workspace.gold</b>) • Eliminação Patrimonial e Resultado</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    aba_patrimonial, aba_resultado, aba_arquitetura = st.tabs(
        [
            "📊 Item 7: Painel Eliminação Patrimonial",
            "📈 Item 8: Painel Eliminação Resultado & Validador Silver",
            "⚙️ Tabelas Unity Catalog (workspace.silver / workspace.gold)",
        ]
    )

    # ==========================================================================
    # ABA 1: PAINEL ELIMINAÇÃO PATRIMONIAL (ITEM 7)
    # ==========================================================================
    with aba_patrimonial:
        dados_pat = obter_estado_patrimonial()
        registros_pat = dados_pat["eliminaveis"]

        col_f1, col_f2, col_f3, col_f4, col_f5 = st.columns(5)
        responsaveis_unicos = sorted({r["responsavel"] for r in registros_pat if r["responsavel"]})
        with col_f1:
            filtro_resp = st.multiselect("Responsável", responsaveis_unicos)
        with col_f2:
            filtro_status_ana = st.multiselect("Status (Analista)", STATUS_ANALISTA_OPCOES)
        with col_f3:
            filtro_status_rev = st.multiselect("Status (Revisor)", STATUS_REVISOR_OPCOES)
        with col_f4:
            filtro_mov = st.selectbox(
                "Filtro de Movimentação",
                ["Todos", "Com movimentação (!= 0)", "Sem movimentação (= 0)", "Ocultar Incorporadas"],
            )
        with col_f5:
            ordenar_por = st.selectbox(
                "Ordenação Inteligente",
                [
                    "Ordem Padrão (Planilha)",
                    "Empresa / Cruzamento (A-Z)",
                    "Maior Diferença Líquida (Absoluta)",
                    "Menor Diferença Líquida",
                    "Responsável",
                    "Status (Analista)",
                ],
            )

        busca_texto = st.text_input(
            "🔍 Buscar por Empresa/Cruzamento ou Comentários (Analista / Revisor)",
            placeholder="Digite p/ filtrar instantaneamente (ex.: TBRA x ITIS, Azure, provisão, Beatriz...)",
        )

        filtrados_pat = []
        for r in registros_pat:
            if filtro_resp and r["responsavel"] not in filtro_resp:
                continue
            if filtro_status_ana and r["status_analista"] not in filtro_status_ana:
                continue
            if filtro_status_rev and r["status_revisor"] not in filtro_status_rev:
                continue
            mov_total = (
                abs(r["ativo_1"])
                + abs(r["passivo_2"])
                + abs(r["ativo_3"])
                + abs(r["passivo_4"])
            )
            if filtro_mov == "Com movimentação (!= 0)" and mov_total == 0:
                continue
            if filtro_mov == "Sem movimentação (= 0)" and mov_total != 0:
                continue
            if filtro_mov == "Ocultar Incorporadas" and r["responsavel"] == "Incorporada":
                continue
            if busca_texto:
                termo = busca_texto.casefold()
                alvo = " ".join(
                    [
                        r["cruzamento"],
                        r["responsavel"],
                        r["comentarios_analista"],
                        r["comentarios_revisor"],
                    ]
                ).casefold()
                if termo not in alvo:
                    continue
            filtrados_pat.append(r)

        if ordenar_por == "Empresa / Cruzamento (A-Z)":
            filtrados_pat.sort(key=lambda x: x["cruzamento"])
        elif ordenar_por == "Maior Diferença Líquida (Absoluta)":
            filtrados_pat.sort(key=lambda x: abs(x["dif_liquida_atual"] or 0.0), reverse=True)
        elif ordenar_por == "Menor Diferença Líquida":
            filtrados_pat.sort(key=lambda x: abs(x["dif_liquida_atual"] or 0.0))
        elif ordenar_por == "Responsável":
            filtrados_pat.sort(key=lambda x: (x["responsavel"], x["cruzamento"]))
        elif ordenar_por == "Status (Analista)":
            filtrados_pat.sort(key=lambda x: (x["status_analista"], x["cruzamento"]))

        soma_d = sum(r["ativo_1"] for r in filtrados_pat)
        soma_e = sum(r["passivo_2"] for r in filtrados_pat)
        soma_j = sum(r["dif_liquida_atual"] for r in filtrados_pat)
        soma_k = sum(r["dif_liquida_anterior"] for r in filtrados_pat)

        k1, k2, k3, k4, k5 = st.columns(5)
        k1.metric("Cruzamentos Ativos", f"{len(filtrados_pat)} de {len(registros_pat)}")
        k2.metric("Empresa Origem — Ativo (1)", formatar_brl(soma_d))
        k3.metric("Empresa Origem — Passivo (2)", formatar_brl(soma_e))
        k4.metric("Dif. Líquida Atual (Ago/26)", formatar_brl(soma_j))
        k5.metric("Dif. Líquida Anterior (Jul/26)", formatar_brl(soma_k))

        sub_elim, sub_sum, sub_temas = st.tabs(
            [
                "Aba Elimináveis (Tabela Principal Editável)",
                "Aba Sum (Resumo Consolidado por Analista)",
                "Aba Temas Principais (Desconciliado)",
            ]
        )

        with sub_elim:
            editados_pat = st.data_editor(
                filtrados_pat,
                use_container_width=True,
                height=560,
                num_rows="dynamic",
                column_config={
                    "linha": None,
                    "competencia": st.column_config.TextColumn("Período", width="small"),
                    "responsavel": st.column_config.TextColumn("Responsável", width="small"),
                    "cruzamento": st.column_config.TextColumn("Cruzamento", width="medium"),
                    "ativo_1": st.column_config.NumberColumn("Ativo (1) Origem", format="R$ %.2f"),
                    "passivo_2": st.column_config.NumberColumn("Passivo (2) Origem", format="R$ %.2f"),
                    "ativo_3": st.column_config.NumberColumn("Ativo (3) Contrap.", format="R$ %.2f"),
                    "passivo_4": st.column_config.NumberColumn("Passivo (4) Contrap.", format="R$ %.2f"),
                    "dif_bruta_1_4": st.column_config.NumberColumn("(1) - (4) [H]", format="R$ %.2f", disabled=True),
                    "dif_bruta_2_3": st.column_config.NumberColumn("(2) - (3) [I]", format="R$ %.2f", disabled=True),
                    "dif_liquida_atual": st.column_config.NumberColumn("Dif. Líq. Ago-26 [J]", format="R$ %.2f", disabled=True),
                    "dif_liquida_anterior": st.column_config.NumberColumn("Dif. Líq. Jul-26 [K]", format="R$ %.2f"),
                    "var_horiz_pct": st.column_config.NumberColumn("Var. Horiz. [L]", format="%.2f", disabled=True),
                    "comp_final_rede": st.column_config.SelectboxColumn("Comp. Rede?", options=["", "Sim", "Não"]),
                    "versao_resultado": st.column_config.TextColumn("Ver. Res."),
                    "versao_patrimonio": st.column_config.TextColumn("Ver. Pat."),
                    "status_analista": st.column_config.SelectboxColumn("Status (Analista)", options=STATUS_ANALISTA_OPCOES),
                    "status_revisor": st.column_config.SelectboxColumn("Status (Revisor)", options=STATUS_REVISOR_OPCOES),
                    "comentarios_revisor": st.column_config.TextColumn("Comentários (Revisor)", width="large"),
                    "comentarios_analista": st.column_config.TextColumn("Comentários (Analista)", width="large"),
                },
                key="editor_patrimonial",
            )

            if st.button("Recalcular Fórmulas e Salvar Alterações (Patrimonial)", type="primary", key="btn_save_pat"):
                mapa_editados = {r["cruzamento"]: r for r in editados_pat if r.get("cruzamento")}
                nova_lista = []
                for orig in registros_pat:
                    item = mapa_editados.get(orig["cruzamento"], orig)
                    calc = calcular_metricas_patrimonial(
                        float(item.get("ativo_1") or 0.0),
                        float(item.get("passivo_2") or 0.0),
                        float(item.get("ativo_3") or 0.0),
                        float(item.get("passivo_4") or 0.0),
                        float(item.get("dif_liquida_anterior") or 0.0),
                    )
                    item.update(calc)
                    nova_lista.append(item)
                atuais_nomes = {r["cruzamento"] for r in nova_lista}
                for c_nome, item in mapa_editados.items():
                    if c_nome not in atuais_nomes:
                        calc = calcular_metricas_patrimonial(
                            float(item.get("ativo_1") or 0.0),
                            float(item.get("passivo_2") or 0.0),
                            float(item.get("ativo_3") or 0.0),
                            float(item.get("passivo_4") or 0.0),
                            float(item.get("dif_liquida_anterior") or 0.0),
                        )
                        item.update(calc)
                        nova_lista.append(item)

                dados_pat["eliminaveis"] = nova_lista
                dados_pat["sum"] = recalcular_aba_sum(nova_lista)
                salvar_estado_patrimonial(dados_pat)
                st.success("Fórmulas recalculadas e painel atualizado com sucesso!")

        with sub_sum:
            st.subheader("Resumo Consolidado por Analista (Aba Sum)")
            st.dataframe(recalcular_aba_sum(registros_pat), use_container_width=True)

        with sub_temas:
            st.subheader("Temas Comuns — Desconciliado (Aba Temas Principais)")
            st.dataframe(dados_pat["temas_principais"], use_container_width=True)

    # ==========================================================================
    # ABA 2: PAINEL ELIMINAÇÃO RESULTADO & VALIDADOR SILVER (ITEM 8)
    # ==========================================================================
    with aba_resultado:
        registros_res = obter_estado_resultado()
        st.subheader("Painel de Controle — Eliminação de Resultado (Camada Silver & Gold)")
        st.caption(
            "Fonte automática: **Interno_Relatório de Eliminação Resultado** (Quadro 'Receita' → "
            "Linhas 'Ineficiência' e 'Divergência') + **Validador Automático na Camada Silver**."
        )

        editados_res = st.data_editor(
            registros_res,
            use_container_width=True,
            height=460,
            num_rows="dynamic",
            column_config={
                "linha": None,
                "competencia": st.column_config.TextColumn("Período", width="small"),
                "responsavel": st.column_config.TextColumn("Responsável", width="small"),
                "cruzamento": st.column_config.TextColumn("Cruzamento", width="medium"),
                "jul_inef_trib": st.column_config.NumberColumn("Julho: Inef. Trib", format="R$ %.2f"),
                "jul_diferenca": st.column_config.NumberColumn("Julho: Diferença", format="R$ %.2f"),
                "jul_inef_liq": st.column_config.NumberColumn("Julho: Inef. Líq.", format="R$ %.2f", disabled=True),
                "ago_inef_trib": st.column_config.NumberColumn("Agosto: Inef. Trib", format="R$ %.2f"),
                "ago_diferenca": st.column_config.NumberColumn("Agosto: Diferença", format="R$ %.2f"),
                "ago_inef_liq": st.column_config.NumberColumn("Agosto: Inef. Líq.", format="R$ %.2f", disabled=True),
                "dif_real_acumulada_ar": st.column_config.NumberColumn("Dif. Real Acum. [Col AR]", format="R$ %.2f", disabled=True),
                "sugestao_diferenca_as": st.column_config.TextColumn("Sugestão Diferença [Col AS]", width="medium", disabled=True),
                "status_analista": st.column_config.SelectboxColumn("Status (Analista)", options=STATUS_ANALISTA_OPCOES),
                "status_revisor": st.column_config.SelectboxColumn("Status (Revisor)", options=STATUS_REVISOR_OPCOES),
                "comentarios_analista": st.column_config.TextColumn("Comentários Analista", width="large"),
                "comentarios_revisor": st.column_config.TextColumn("Comentários Revisor", width="large"),
                "validador_silver": st.column_config.TextColumn("Validador Camada Silver", width="medium", disabled=True),
            },
            key="editor_resultado",
        )

        if st.button("Recalcular Ineficiência Líquida, Coluna AR/AS e Salvar (Resultado)", type="primary", key="btn_save_res"):
            for r in editados_res:
                r["jul_inef_liq"] = round(
                    float(r.get("jul_inef_trib") or 0.0) + float(r.get("jul_diferenca") or 0.0), 2
                )
                calc_r = calcular_metricas_resultado(
                    float(r.get("ago_inef_trib") or 0.0),
                    float(r.get("ago_diferenca") or 0.0),
                    diferencas_historico_mensal=[float(r.get("jul_diferenca") or 0.0)],
                )
                r["ago_inef_liq"] = calc_r["inef_liquida"]
                r["dif_real_acumulada_ar"] = calc_r["dif_real_acumulada_ar"]
                r["sugestao_diferenca_as"] = calc_r["sugestao_diferenca_as"]
            salvar_estado_resultado(editados_res)
            st.success("Painel de Resultado e indicadores AR/AS atualizados!")

        st.divider()
        st.subheader("Validador Automático na Camada Silver (Substitui Planilha Resultado_v10 Manual)")
        c1, c2, c3 = st.columns(3)
        with c1:
            rec_ant = st.number_input("Rec Liq Total (Mês Anterior)", value=35901920.79)
            rec_atu = st.number_input("Rec Liq Total (Mês Atual)", value=35901920.79)
        with c2:
            inef_ant = st.number_input("Inef Trib Total (Mês Anterior)", value=4395972.02)
            inef_atu = st.number_input("Inef Trib Total (Mês Atual)", value=4395972.02)
        with c3:
            desp_ant = st.number_input("Desp Total (Mês Anterior)", value=40297892.81)
            desp_atu = st.number_input("Desp Total (Mês Atual)", value=40297892.81)

        res_val = validar_totais_resultado_silver(rec_ant, inef_ant, desp_ant, rec_atu, inef_atu, desp_atu)
        v1, v2, v3, v4 = st.columns(4)
        v1.metric("Check Receita Líquida", res_val["check_rec_liq"])
        v2.metric("Check Inef. Tributária", res_val["check_inef_tribut"])
        v3.metric("Check Despesa Total", res_val["check_despesa"])
        v4.metric("Status Camada Silver", res_val["status_validador"])

    # ==========================================================================
    # ABA 3: ARQUITETURA PYSPARK / DELTA LAKE (DDL & MERGE)
    # ==========================================================================
    with aba_arquitetura:
        st.subheader(f"Tabelas Ativas no Catálogo `{CATALOGO}`")
        st.markdown(
            f"""
            - `{CATALOGO}.silver.painel_eliminacao_patrimonial`
            - `{CATALOGO}.silver.temas_principais_patrimonial`
            - `{CATALOGO}.silver.painel_eliminacao_resultado`
            - `{CATALOGO}.gold.vw_sum_eliminacao_patrimonial`
            """
        )
        st.code(DDL_DATABRICKS_SQL.replace("intercompany.", f"{CATALOGO}."), language="sql")
        st.subheader("Instrução MERGE INTO Transacional")
        st.code(gerar_query_merge_patrimonial().replace("intercompany.", f"{CATALOGO}."), language="sql")


if __name__ == "__main__":
    main()
