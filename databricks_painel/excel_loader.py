"""
Leitor nativo (sem dependência obrigatória de openpyxl) para carregar e sincronizar:
  1. Painel Eliminação Patrimonial_08-2026.xlsx (Abas: Elimináveis, Sum, Temas Principais)
  2. Painel Eliminação de Resultado (com Histórico Mensal, Coluna AR, Coluna AS e Validador Silver)
  3. Extração automática dos Relatórios de Eliminação recebidos da Accenture (.xlsx / .xlsm)
"""

from __future__ import annotations
from pathlib import Path
import re
import zipfile
import xml.etree.ElementTree as ET
from typing import Any

from pipeline_silver_gold import (
    calcular_metricas_patrimonial,
    calcular_metricas_resultado,
    classificar_item9_eliminacao_x_compfinal,
    classificar_item9_expurgadas_compfinal,
    classificar_item9_somente_compfinal,
    classificar_item9_somente_eliminacao,
)

NS_MAIN = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def _col_letter_from_ref(ref: str) -> str:
    m = re.match(r"([A-Z]+)", ref)
    return m.group(1) if m else ""


def _parse_float(val: Any) -> float:
    if val is None or val == "":
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip()
    if s.startswith("#"):
        return 0.0
    try:
        return float(s)
    except ValueError:
        return 0.0


def carregar_painel_patrimonial_xlsx(caminho_xlsx: Path) -> dict[str, list[dict[str, Any]]]:
    """
    Lê as 3 abas de 'Painel Eliminação Patrimonial_08-2026.xlsx':
      - eliminaveis (29 cruzamentos)
      - sum (resumo por analista)
      - temas_principais (temas comuns desconciliados)
    """
    with zipfile.ZipFile(caminho_xlsx, "r") as z:
        ss_root = ET.fromstring(z.read("xl/sharedStrings.xml"))
        strings = [
            "".join(t.text or "" for t in si.findall(".//m:t", NS_MAIN))
            for si in ss_root.findall("m:si", NS_MAIN)
        ]

        def ler_linhas(sheet_path: str) -> dict[int, dict[str, Any]]:
            sroot = ET.fromstring(z.read(sheet_path))
            resultado: dict[int, dict[str, Any]] = {}
            for r in sroot.findall(".//m:row", NS_MAIN):
                r_num = int(r.attrib.get("r", "0"))
                row_dict: dict[str, Any] = {}
                for c in r.findall("m:c", NS_MAIN):
                    ref = c.attrib.get("r", "")
                    col = _col_letter_from_ref(ref)
                    ctype = c.attrib.get("t", "")
                    v_elem = c.find("m:v", NS_MAIN)
                    val = v_elem.text if v_elem is not None else ""
                    if ctype == "s" and val.isdigit():
                        val = strings[int(val)]
                    row_dict[col] = val
                if row_dict:
                    resultado[r_num] = row_dict
            return resultado

        rows_elim = ler_linhas("xl/worksheets/sheet1.xml")
        rows_sum = ler_linhas("xl/worksheets/sheet2.xml")
        rows_temas = ler_linhas("xl/worksheets/sheet3.xml")

    eliminaveis = []
    for r_num in range(5, 34):
        row = rows_elim.get(r_num, {})
        if not row.get("C"):
            continue
        ativo_1 = _parse_float(row.get("D"))
        passivo_2 = _parse_float(row.get("E"))
        ativo_3 = _parse_float(row.get("F"))
        passivo_4 = _parse_float(row.get("G"))
        dif_ant = _parse_float(row.get("K"))
        calc = calcular_metricas_patrimonial(ativo_1, passivo_2, ativo_3, passivo_4, dif_ant)

        eliminaveis.append(
            {
                "linha": r_num,
                "competencia": "08/2026",
                "responsavel": str(row.get("B", "")).strip(),
                "cruzamento": str(row.get("C", "")).strip(),
                "ativo_1": ativo_1,
                "passivo_2": passivo_2,
                "ativo_3": ativo_3,
                "passivo_4": passivo_4,
                "dif_bruta_1_4": calc["dif_bruta_1_4"],
                "dif_bruta_2_3": calc["dif_bruta_2_3"],
                "dif_liquida_atual": calc["dif_liquida_atual"],
                "dif_liquida_anterior": calc["dif_liquida_anterior"],
                "var_horiz_pct": calc["var_horiz_pct"],
                "comp_final_rede": str(row.get("M", "")).strip(),
                "versao_resultado": str(row.get("N", "")).strip(),
                "versao_patrimonio": str(row.get("O", "")).strip(),
                "status_analista": str(row.get("P", "Sem movimento")).strip(),
                "status_revisor": str(row.get("Q", "Sem movimento")).strip(),
                "comentarios_revisor": str(row.get("R", "")).strip(),
                "comentarios_analista": str(row.get("S", "")).strip(),
            }
        )

    aba_sum = []
    for r_num in range(3, 9):
        row = rows_sum.get(r_num, {})
        if not row.get("B"):
            continue
        aba_sum.append(
            {
                "rotulo_linha": str(row.get("B", "")).strip(),
                "contagem_cruzamento": int(_parse_float(row.get("C"))),
                "soma_mes_atual": round(_parse_float(row.get("D")), 2),
                "soma_mes_anterior": round(_parse_float(row.get("E")), 2),
            }
        )

    temas = []
    for r_num in range(3, 30):
        row = rows_temas.get(r_num, {})
        if not row.get("B"):
            continue
        temas.append(
            {
                "cruzamento": str(row.get("B", "")).strip(),
                "temas_entre_empresas": str(row.get("C", "")).strip(),
                "ativo_passivo_origem": str(row.get("D", "")).strip(),
                "ativo_passivo_contraparte": str(row.get("E", "")).strip(),
            }
        )

    return {
        "eliminaveis": eliminaveis,
        "sum": aba_sum,
        "temas_principais": temas,
    }


def carregar_dados_iniciais_resultado() -> list[dict[str, Any]]:
    """
    Retorna a base inicial do Painel de Controle de Eliminação de Resultado (Item 8),
    espelhando fielmente os cruzamentos, valores de Julho e Agosto, Coluna AR
    (Diferença Real Acumulada), Coluna AS (Sugestão de Diferença), Status e Comentários
    mapeados no Documento Funcional da Fase 2 — Eliminação Resultado.
    """
    registros_base = [
        {
            "responsavel": "Incorporada",
            "cruzamento": "CLOUD x FIBR",
            "jul_inef_trib": 0.00,
            "jul_diferenca": -95435.53,
            "ago_inef_trib": 0.00,
            "ago_diferenca": 0.00,
            "acumulado_previo": -95435.53,
            "status_analista": "Incorporada",
            "status_revisor": "Incorporada",
            "comentarios_analista": "",
            "comentarios_revisor": "",
        },
        {
            "responsavel": "Cibele",
            "cruzamento": "CLOUD x VSCD",
            "jul_inef_trib": 0.00,
            "jul_diferenca": -459196.37,
            "ago_inef_trib": 1508218.85,
            "ago_diferenca": 81784.08,
            "acumulado_previo": 574350.87,
            "status_analista": "Enviado para reporting",
            "status_revisor": "Ok para envio",
            "comentarios_analista": "Tratativa dada a Azure",
            "comentarios_revisor": "",
        },
        {
            "responsavel": "Incorporada",
            "cruzamento": "CYBR x CLOUD",
            "jul_inef_trib": 0.00,
            "jul_diferenca": 0.00,
            "ago_inef_trib": 0.00,
            "ago_diferenca": 0.00,
            "acumulado_previo": 0.00,
            "status_analista": "Incorporada",
            "status_revisor": "Incorporada",
            "comentarios_analista": "",
            "comentarios_revisor": "",
        },
        {
            "responsavel": "Thais",
            "cruzamento": "ITIS x CLOUD",
            "jul_inef_trib": -66323.37,
            "jul_diferenca": -26899.27,
            "ago_inef_trib": -58620.06,
            "ago_diferenca": 3578.98,
            "acumulado_previo": -860859.01,
            "status_analista": "Enviado para reporting",
            "status_revisor": "Ok para envio",
            "comentarios_analista": "",
            "comentarios_revisor": "",
        },
        {
            "responsavel": "Incorporada",
            "cruzamento": "ITIS X CYBR",
            "jul_inef_trib": 0.00,
            "jul_diferenca": 0.00,
            "ago_inef_trib": 0.00,
            "ago_diferenca": 0.00,
            "acumulado_previo": 0.00,
            "status_analista": "Incorporada",
            "status_revisor": "Incorporada",
            "comentarios_analista": "",
            "comentarios_revisor": "",
        },
        {
            "responsavel": "Mayara",
            "cruzamento": "ITIS x TERRA",
            "jul_inef_trib": -10857.10,
            "jul_diferenca": 32890.22,
            "ago_inef_trib": -2525.77,
            "ago_diferenca": -2182.92,
            "acumulado_previo": 64607.48,
            "status_analista": "Enviado para reporting",
            "status_revisor": "Ok para envio",
            "comentarios_analista": "",
            "comentarios_revisor": "",
        },
        {
            "responsavel": "Beatriz",
            "cruzamento": "ITIS x TGLOG",
            "jul_inef_trib": 0.00,
            "jul_diferenca": -123.58,
            "ago_inef_trib": 0.00,
            "ago_diferenca": -123.58,
            "acumulado_previo": 74634.30,
            "status_analista": "Enviado para reporting",
            "status_revisor": "Ok para envio",
            "comentarios_analista": "",
            "comentarios_revisor": "Avaliar do que se trata esse valor tão pequeno para que ele seja conciliado ou até mesmo cancelado.",
        },
        {
            "responsavel": "Thais",
            "cruzamento": "TBRA x CLOUD",
            "jul_inef_trib": -2467838.26,
            "jul_diferenca": 284225.83,
            "ago_inef_trib": -2226172.98,
            "ago_diferenca": 828825.93,
            "acumulado_previo": 284225.83,
            "status_analista": "Enviado para reporting",
            "status_revisor": "Ok para envio",
            "comentarios_analista": "A dif refere principalmente a 800k de diferimento",
            "comentarios_revisor": "",
        },
        {
            "responsavel": "Incorporada",
            "cruzamento": "TBRA X CYBR",
            "jul_inef_trib": 0.00,
            "jul_diferenca": 0.00,
            "ago_inef_trib": 0.00,
            "ago_diferenca": 0.00,
            "acumulado_previo": 0.00,
            "status_analista": "Incorporada",
            "status_revisor": "Incorporada",
            "comentarios_analista": "",
            "comentarios_revisor": "",
        },
        {
            "responsavel": "Incorporada",
            "cruzamento": "TBRA x FIBR",
            "jul_inef_trib": -9636061.57,
            "jul_diferenca": 6763484.66,
            "ago_inef_trib": 0.00,
            "ago_diferenca": 0.00,
            "acumulado_previo": 0.00,
            "status_analista": "Incorporada",
            "status_revisor": "Incorporada",
            "comentarios_analista": "",
            "comentarios_revisor": "",
        },
        {
            "responsavel": "Thais",
            "cruzamento": "TBRA x I2GO",
            "jul_inef_trib": -182120.07,
            "jul_diferenca": 568874.43,
            "ago_inef_trib": -276513.02,
            "ago_diferenca": -522605.87,
            "acumulado_previo": 568874.43,
            "status_analista": "Enviado para reporting",
            "status_revisor": "Ok para envio",
            "comentarios_analista": "",
            "comentarios_revisor": "",
        },
        {
            "responsavel": "Thais",
            "cruzamento": "VSS x I2GO",
            "jul_inef_trib": 0.00,
            "jul_diferenca": 0.00,
            "ago_inef_trib": 0.00,
            "ago_diferenca": 0.00,
            "acumulado_previo": 0.00,
            "status_analista": "Enviado para reporting",
            "status_revisor": "Ok para envio",
            "comentarios_analista": "",
            "comentarios_revisor": "",
        },
        {
            "responsavel": "Mayara",
            "cruzamento": "TBRA x ITIS",
            "jul_inef_trib": -2066610.79,
            "jul_diferenca": -2329361.23,
            "ago_inef_trib": -3006095.79,
            "ago_diferenca": 9570296.94,
            "acumulado_previo": -2329361.23,
            "status_analista": "Enviado para reporting",
            "status_revisor": "Ok para envio",
            "comentarios_analista": "A diferença de R$ 9,5MM refere-se principalmente pelo valor do lucro não realizado de R$ 8,3MM, que até o mês anterior estava mascarado por ajustes de provisões e diferimentos",
            "comentarios_revisor": "Deixar no radar os ajustes que foram feitos pelas áreas de negócios caso tenha algum impacto",
        },
    ]

    saida = []
    for idx, r in enumerate(registros_base, start=1):
        jul_liq = round(r["jul_inef_trib"] + r["jul_diferenca"], 2)
        calc = calcular_metricas_resultado(
            r["ago_inef_trib"],
            r["ago_diferenca"],
            dif_acumulada_mes_anterior=r["acumulado_previo"],
        )
        saida.append(
            {
                "linha": idx,
                "competencia": "08/2026",
                "responsavel": r["responsavel"],
                "cruzamento": r["cruzamento"],
                "jul_inef_trib": r["jul_inef_trib"],
                "jul_diferenca": r["jul_diferenca"],
                "jul_inef_liq": jul_liq,
                "ago_inef_trib": calc["inef_trib"],
                "ago_diferenca": calc["diferenca"],
                "ago_inef_liq": calc["inef_liquida"],
                "dif_real_acumulada_ar": calc["dif_real_acumulada_ar"],
                "sugestao_diferenca_as": calc["sugestao_diferenca_as"],
                "status_analista": r["status_analista"],
                "status_revisor": r["status_revisor"],
                "comentarios_analista": r["comentarios_analista"],
                "comentarios_revisor": r["comentarios_revisor"],
                "validador_silver": "Validado (OK Rec Liq | OK Inef Tribut | OK Despesa)",
            }
        )
    return saida


def carregar_dados_iniciais_item9_patrimonial() -> dict[str, list[dict[str, Any]]]:
    """
    Retorna a base inicial do Item 9 (Fase 2 — Composições Gerais e Elimináveis Patrimonial)
    espelhando as 4 abas do relatório '13_1_Validacao_Eliminacoes x CompFinais_Patrimonial.xlsx':
      1. eliminacao_x_compfinal (Aba: Eliminação x CompFinal)
      2. expurgadas_compfinal (Aba: Expurgadas_CompFinal)
      3. somente_compfinal (Aba: Somente_CompFinal)
      4. somente_eliminacao (Aba: Somente_Eliminacao)
    """
    raw_elim_x_comp = [
        ("I2GO x TBRA", "I2GO", "TBRA", "11218928", 1165497.36, 1165497.36, "Partida conciliada sem diferença"),
        ("I2GO x TBRA", "I2GO", "TBRA", "21191932", -15228234.24, -15228234.24, "Adiantamento 15MM conciliado em ambos os lados"),
        ("INN1 x TBRA", "INN1", "TBRA", "21121111", -7966.83, -7966.83, ""),
        ("INN1 x TBRA", "INN1", "TBRA", "21121112", -1007634.92, -1007634.92, ""),
        ("INN1 x TBRA", "INN1", "TBRA", "21121193", -112023.92, -112023.92, ""),
        ("INN1 x TBRA", "INN1", "TBRA", "21191915", -105086.19, -105086.19, ""),
        ("INN1 x TBRA", "INN1", "TBRA", "21192001", 0.00, 0.00, ""),
        ("ITIS x TBRA", "ITIS", "TBRA", "11211115", 10865902.81, 10865902.81, ""),
        ("ITIS x TBRA", "ITIS", "TBRA", "11211121", 3528817.67, 3528817.67, ""),
        ("ITIS x TBRA", "ITIS", "TBRA", "11211127", 67084907.48, 67084907.48, ""),
        ("ITIS x TBRA", "ITIS", "TBRA", "11211141", 35444207.57, 35444207.57, ""),
        ("ITIS x TBRA", "ITIS", "TBRA", "11211142", -0.03, -0.03, ""),
        ("ITIS x TBRA", "ITIS", "TBRA", "11211922", 80718.54, 80718.54, ""),
        ("ITIS x TBRA", "ITIS", "TBRA", "11251111", -32112.67, -32112.67, ""),
        ("ITIS x TBRA", "ITIS", "TBRA", "11252311", -30517854.06, -30517854.06, ""),
        ("ITIS x TBRA", "ITIS", "TBRA", "11252511", 30146.61, 30146.61, ""),
        ("ITIS x TBRA", "ITIS", "TBRA", "11291114", -1631755.78, -1631755.78, ""),
        ("TBRA x TERRA", "TBRA", "TERRA", "11211115", 5326521.70, 5333462.99, "Divergência de rateio tributário em análise com a contraparte"),
    ]
    aba1 = []
    for idx, (cruz, emp_o, emp_c, conta, v_elim, v_comp, coment) in enumerate(raw_elim_x_comp, start=1):
        calc = classificar_item9_eliminacao_x_compfinal(v_elim, v_comp)
        aba1.append(
            {
                "linha": idx,
                "cruzamento": cruz,
                "empresa_origem": emp_o,
                "empresa_conc": emp_c,
                "conta": conta,
                "valor_comp_elim": calc["valor_comp_elim"],
                "valor_comp_final": calc["valor_comp_final"],
                "diferenca": calc["diferenca"],
                "resultado_analise": calc["resultado_analise"],
                "comentarios_analista": coment,
            }
        )

    raw_expurgadas = [
        ("0942 x TBRA", "0942 - Fundação Telefônica", "Não Eliminável", "11211115", 145230.10, "Empresa Não Eliminável parametrizada na Base Mestre"),
        ("1969 x TBRA", "1969 - Visão Prev", "Não Eliminável", "21121112", -89410.55, "Empresa Não Eliminável parametrizada na Base Mestre"),
        ("2193 x TBRA", "2193 - Vivo Ventures", "Não Eliminável", "11211922", 0.00, "Sem movimentação no período"),
        ("0306 x TBRA", "0306 - ITIS", "Eliminável", "11251119", 17261.71, "Verificar partida expurgada de empresa Eliminável"),
    ]
    aba2 = []
    for idx, (cruz, emp_o, tipo_bm, conta, v_comp, coment) in enumerate(raw_expurgadas, start=1):
        aba2.append(
            {
                "linha": idx,
                "cruzamento": cruz,
                "empresa_origem": emp_o,
                "classificacao_base_mestre": tipo_bm,
                "conta": conta,
                "valor_comp_final": round(v_comp, 2),
                "resultado_analise": classificar_item9_expurgadas_compfinal(tipo_bm),
                "comentarios_analista": coment,
            }
        )

    raw_somente_comp = [
        ("TBRA x POP", "TBRA", "POP", "11211115", 0.00, "Saldo zerado na composição final"),
        ("TBRA x CLOUD", "TBRA", "CLOUD", "11211127", 0.00, "Saldo zerado na composição final"),
        ("CLOUD x VSCD", "CLOUD", "VSCD", "11211922", 180637.43, "Regularização A Faturar Azure pendente na Eliminação"),
    ]
    aba3 = []
    for idx, (cruz, emp_o, emp_c, conta, v_comp, coment) in enumerate(raw_somente_comp, start=1):
        aba3.append(
            {
                "linha": idx,
                "cruzamento": cruz,
                "empresa_origem": emp_o,
                "empresa_conc": emp_c,
                "conta": conta,
                "valor_comp_final": round(v_comp, 2),
                "resultado_analise": classificar_item9_somente_compfinal(v_comp),
                "comentarios_analista": coment,
            }
        )

    raw_somente_elim = [
        ("TBRA x VSS", "TBRA", 0.00, "21121111", "Sem resíduo exclusivo na eliminação"),
        ("TBRA x TGLOG", "TBRA", 0.00, "21121112", "Sem resíduo exclusivo na eliminação"),
        ("ITIS x TGLOG", "ITIS", -17261.71, "21121193", "Despesa operacional registrada na ITIS e não na TGLOG"),
    ]
    aba4 = []
    for idx, (cruz, emp_o, v_elim, conta, coment) in enumerate(raw_somente_elim, start=1):
        aba4.append(
            {
                "linha": idx,
                "cruzamento": cruz,
                "empresa_origem": emp_o,
                "valor_comp_elim": round(v_elim, 2),
                "conta": conta,
                "resultado_analise": classificar_item9_somente_eliminacao(v_elim),
                "comentarios_analista": coment,
            }
        )

    return {
        "eliminacao_x_compfinal": aba1,
        "expurgadas_compfinal": aba2,
        "somente_compfinal": aba3,
        "somente_eliminacao": aba4,
    }

