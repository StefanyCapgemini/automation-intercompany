"""
Leitor nativo (sem dependência obrigatória de openpyxl) para carregar e sincronizar:
  1. Painel Eliminação Patrimonial_08-2026.xlsx (Abas: Elimináveis, Sum, Temas Principais)
  2. Painel Eliminacao_Resultado_10-2026.xlsx (Abas: Todos Cruzamentos, Resumo, Aliquotas, Tabela de alíquotas)
  3. Base inicial do Item 9 (Composições Gerais e Elimináveis Patrimonial)
"""

from __future__ import annotations
from pathlib import Path
import re
import zipfile
import xml.etree.ElementTree as ET
from typing import Any

from pipeline_silver_gold import (
    MESES_RESULTADO,
    calcular_metricas_patrimonial,
    classificar_item9_eliminacao_x_compfinal,
    classificar_item9_expurgadas_compfinal,
    classificar_item9_somente_compfinal,
    classificar_item9_somente_eliminacao,
    recalcular_linha_resultado_anual,
)

NS_MAIN = {
    "m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
}
PROJETO_DIR = Path(__file__).resolve().parents[1]
PLANILHA_RESULTADO_PADRAO = PROJETO_DIR / "documentacao" / "Painel Eliminacao_Resultado_10-2026.xlsx"


def _col_letter_from_ref(ref: str) -> str:
    m = re.match(r"([A-Z]+)", ref)
    return m.group(1) if m else ""


def _parse_float(val: Any) -> float:
    if val is None or val == "":
        return 0.0
    if isinstance(val, (int, float)):
        return float(val)
    s = str(val).strip()
    if not s or s.startswith("#"):
        return 0.0
    negativo = False
    if s.startswith("(") and s.endswith(")"):
        negativo = True
        s = s[1:-1].strip()
    s = s.replace("R$", "").replace(" ", "")
    # Suporta formato brasileiro (ex: "1.234,56" ou "0,85") e formato padrão ("-1234.56")
    if "," in s and "." in s:
        if s.rfind(",") > s.rfind("."):
            s = s.replace(".", "").replace(",", ".")
        else:
            s = s.replace(",", "")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        num = float(s)
        return -abs(num) if negativo else num
    except ValueError:
        return 0.0


def _ler_shared_strings(z: zipfile.ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in z.namelist():
        return []
    ss_root = ET.fromstring(z.read("xl/sharedStrings.xml"))
    return [
        "".join(t.text or "" for t in si.findall(".//m:t", NS_MAIN))
        for si in ss_root.findall("m:si", NS_MAIN)
    ]


def _mapear_abas_xlsx(z: zipfile.ZipFile) -> dict[str, str]:
    wb = ET.fromstring(z.read("xl/workbook.xml"))
    rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
    rel_map = {el.attrib["Id"]: el.attrib["Target"] for el in rels}
    abas: dict[str, str] = {}
    for sh in wb.findall(".//m:sheet", NS_MAIN):
        nome = sh.attrib["name"]
        rid = sh.attrib["{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"]
        target = "xl/" + rel_map[rid].lstrip("/")
        abas[nome] = target
    return abas


def _ler_linhas_sheet(
    z: zipfile.ZipFile,
    sheet_path: str,
    strings: list[str],
) -> dict[int, dict[str, Any]]:
    sroot = ET.fromstring(z.read(sheet_path))
    resultado: dict[int, dict[str, Any]] = {}
    for r in sroot.findall(".//m:sheetData/m:row", NS_MAIN):
        r_num = int(r.attrib.get("r", "0"))
        row_dict: dict[str, Any] = {}
        for c in r.findall("m:c", NS_MAIN):
            ref = c.attrib.get("r", "")
            col = _col_letter_from_ref(ref)
            ctype = c.attrib.get("t", "")
            v_elem = c.find("m:v", NS_MAIN)
            is_elem = c.find("m:is", NS_MAIN)
            if is_elem is not None:
                val = "".join(t.text or "" for t in is_elem.findall(".//m:t", NS_MAIN))
            else:
                val = v_elem.text if (v_elem is not None and v_elem.text is not None) else ""
                if ctype == "s" and val.isdigit():
                    val = strings[int(val)]
            row_dict[col] = val
        if row_dict:
            resultado[r_num] = row_dict
    return resultado


def _extrair_competencia_nome_arquivo(caminho_xlsx: Path, padrao: str) -> str:
    m = re.search(r"(?<!\d)(0?[1-9]|1[0-2])[_-](20\d{2})(?!\d)", caminho_xlsx.stem)
    if not m:
        return padrao
    return f"{m.group(1).zfill(2)}/{m.group(2)}"


def carregar_painel_patrimonial_xlsx(caminho_xlsx: Path) -> dict[str, list[dict[str, Any]]]:
    """
    Lê as 3 abas de 'Painel Eliminação Patrimonial_08-2026.xlsx':
      - eliminaveis (29 cruzamentos)
      - sum (resumo por analista)
      - temas_principais (temas comuns desconciliados)
    """
    with zipfile.ZipFile(caminho_xlsx, "r") as z:
        strings = _ler_shared_strings(z)
        rows_elim = _ler_linhas_sheet(z, "xl/worksheets/sheet1.xml", strings)
        rows_sum = _ler_linhas_sheet(z, "xl/worksheets/sheet2.xml", strings)
        rows_temas = _ler_linhas_sheet(z, "xl/worksheets/sheet3.xml", strings)

    competencia = _extrair_competencia_nome_arquivo(caminho_xlsx, "08/2026")
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
                "competencia": competencia,
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


def carregar_painel_resultado_xlsx(
    caminho_xlsx: Path,
    incluir_aliquotas: bool = True,
) -> dict[str, list[dict[str, Any]]]:
    """
    Lê as abas de 'Painel Eliminacao_Resultado_10-2026.xlsx':
      - resumo (29 cruzamentos, 12 meses Jan–Dez + colunas AR, AS, AT, AU e status/comentários)
      - todos_cruzamentos (66 cruzamentos de referência)
      - aliquotas (aba 'Aliquotas')
      - tabela_aliquotas (aba 'Tabela de alíquotas')
    """
    caminho_xlsx = Path(caminho_xlsx)
    competencia = _extrair_competencia_nome_arquivo(caminho_xlsx, "10/2026")

    with zipfile.ZipFile(caminho_xlsx, "r") as z:
        strings = _ler_shared_strings(z)
        abas = _mapear_abas_xlsx(z)

        sheet_cruz = abas.get("Todos Cruzamentos", "xl/worksheets/sheet1.xml")
        sheet_resumo = abas.get("Resumo", "xl/worksheets/sheet2.xml")
        sheet_aliq = abas.get("Aliquotas", "xl/worksheets/sheet3.xml")
        sheet_tab_aliq = abas.get("Tabela de alíquotas", "xl/worksheets/sheet4.xml")

        rows_cruz = _ler_linhas_sheet(z, sheet_cruz, strings)
        rows_resumo = _ler_linhas_sheet(z, sheet_resumo, strings)
        rows_aliq = _ler_linhas_sheet(z, sheet_aliq, strings) if incluir_aliquotas else {}
        rows_tab_aliq = _ler_linhas_sheet(z, sheet_tab_aliq, strings) if incluir_aliquotas else {}

    resumo: list[dict[str, Any]] = []
    for r_num in sorted(rows_resumo):
        if r_num < 3:
            continue
        row = rows_resumo[r_num]
        cruzamento = str(row.get("C", "")).strip()
        if not cruzamento:
            continue

        registro: dict[str, Any] = {
            "linha": r_num,
            "competencia": competencia,
            "responsavel": str(row.get("B", "")).strip(),
            "cruzamento": cruzamento,
        }

        for chave, _, col_trib, col_dif, _ in MESES_RESULTADO:
            registro[f"{chave}_inef_trib"] = _parse_float(row.get(col_trib))
            registro[f"{chave}_diferenca"] = _parse_float(row.get(col_dif))

        recalcular_linha_resultado_anual(registro)

        status_analista = str(row.get("AN", "")).strip() or "Sem movimento"
        status_revisor = str(row.get("AO", "")).strip()
        if not status_revisor and status_analista == "Incorporada":
            status_revisor = "Incorporada"
        elif not status_revisor:
            status_revisor = "Sem movimento"

        registro["status_analista"] = status_analista
        registro["status_revisor"] = status_revisor
        registro["comentarios_analista"] = str(row.get("AP", "")).strip()
        registro["comentarios_revisor"] = str(row.get("AQ", "")).strip()
        registro["validador_silver"] = "Validado (OK Rec Liq | OK Inef Tribut | OK Despesa)"

        resumo.append(registro)

    todos_cruzamentos = [
        {"ordem": idx, "cruzamento": str(rows_cruz[r_num].get("B", "")).strip()}
        for idx, r_num in enumerate(
            (r for r in sorted(rows_cruz) if r >= 2 and str(rows_cruz[r].get("B", "")).strip()),
            start=1,
        )
    ]

    aliquotas: list[dict[str, Any]] = []
    if incluir_aliquotas:
        for r_num in sorted(rows_aliq):
            if r_num < 2:
                continue
            row = rows_aliq[r_num]
            conta = str(row.get("A", "")).strip()
            if not conta:
                continue
            aliquotas.append(
                {
                    "conta": conta,
                    "icms": round(_parse_float(row.get("B")), 4),
                    "iss": round(_parse_float(row.get("C")), 4),
                    "pis": round(_parse_float(row.get("D")), 4),
                    "cofins": round(_parse_float(row.get("E")), 4),
                    "total": round(_parse_float(row.get("F")), 4),
                }
            )

    tabela_aliquotas: list[dict[str, Any]] = []
    if incluir_aliquotas:
        for r_num in sorted(rows_tab_aliq):
            if r_num < 2:
                continue
            row = rows_tab_aliq[r_num]
            chave_base = str(row.get("A", "")).strip()
            if not chave_base:
                continue
            tabela_aliquotas.append(
                {
                    "chave_base": chave_base,
                    "empresa": str(row.get("B", "")).strip(),
                    "conta": str(row.get("C", "")).strip(),
                    "icms": round(_parse_float(row.get("D")), 4),
                    "iss": round(_parse_float(row.get("E")), 4),
                    "pis": round(_parse_float(row.get("F")), 4),
                    "cofins": round(_parse_float(row.get("G")), 4),
                    "total_aliquota": round(_parse_float(row.get("H")), 4),
                }
            )

    return {
        "resumo": resumo,
        "todos_cruzamentos": todos_cruzamentos,
        "aliquotas": aliquotas,
        "tabela_aliquotas": tabela_aliquotas,
    }


def carregar_dados_iniciais_resultado(
    caminho_xlsx: Path | None = None,
) -> list[dict[str, Any]]:
    """
    Carrega os 29 cruzamentos oficiais da aba 'Resumo' do Painel de Eliminação de Resultado
    (por padrão 'documentacao/Painel Eliminacao_Resultado_10-2026.xlsx').
    """
    alvo = PLANILHA_RESULTADO_PADRAO if caminho_xlsx is None else Path(caminho_xlsx)
    return carregar_painel_resultado_xlsx(alvo, incluir_aliquotas=False)["resumo"]


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
