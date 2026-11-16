"""
Pipeline PySpark & Delta Lake (Camadas Bronze, Silver e Gold) para o Databricks
Processos:
  - Item 7: Fase 2 — Painel de Controle de Eliminação Patrimonial
  - Item 8: Fase 2 — Painel de Controle de Eliminação de Resultado & Validador Silver
"""

from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any

# ==============================================================================
# 1. CONSTANTES DE DOMÍNIO E REGRAS DE NEGÓCIO (ITENS 7 E 8)
# ==============================================================================

STATUS_ANALISTA_OPCOES = [
    "Sem movimento",
    "Recebido da ACT",
    "Em análise",
    "Devolvida para ACT",
    "Ok para revisão",
    "Enviado para reporting",
    "Incorporada",
]

STATUS_REVISOR_OPCOES = [
    "Sem movimento",
    "Aguardando retorno dos pontos",
    "Ok para envio",
    "Incorporada",
]


@dataclass
class ResumoPatrimonialExtraido:
    cruzamento: str
    competencia: str
    ativo_origem: float
    passivo_origem: float
    ativo_contraparte: float
    passivo_contraparte: float
    arquivo_origem: str


@dataclass
class ResumoResultadoExtraido:
    cruzamento: str
    competencia: str
    ineficiencia_tributaria: float
    divergencia: float
    arquivo_origem: str


# ==============================================================================
# 2. FUNÇÕES DE CÁLCULO E REGRAS DA CAMADA SILVER (PATRIMONIAL — ITEM 7)
# ==============================================================================

def calcular_metricas_patrimonial(
    ativo_1: float,
    passivo_2: float,
    ativo_3: float,
    passivo_4: float,
    dif_liquida_mes_anterior: float = 0.0,
) -> dict[str, float | None]:
    """
    Aplica as fórmulas oficiais do Painel de Eliminação Patrimonial (Seção 3 e 4):
      - Coluna H ((1) - (4)): Ativo Origem (1) + Passivo Contraparte (4) [fórmula Excel: =D+G]
      - Coluna I ((2) - (3)): Passivo Origem (2) + Ativo Contraparte (3) [fórmula Excel: =E+F]
      - Coluna J (Diferença Líquida Mês Atual): = SUM(H:I)
      - Coluna K (Diferença Líquida Mês Anterior): montante histórico do mês anterior
      - Coluna L (Var. Horiz. %): ((Coluna J / Coluna K) - 1)
    """
    dif_bruta_1_4 = round((ativo_1 or 0.0) + (passivo_4 or 0.0), 2)
    dif_bruta_2_3 = round((passivo_2 or 0.0) + (ativo_3 or 0.0), 2)
    dif_liquida_atual = round(dif_bruta_1_4 + dif_bruta_2_3, 2)
    anterior = round(dif_liquida_mes_anterior or 0.0, 2)

    if anterior == 0.0:
        var_horiz_pct = None
    else:
        var_horiz_pct = round(((dif_liquida_atual / anterior) - 1.0), 6)

    return {
        "dif_bruta_1_4": dif_bruta_1_4,
        "dif_bruta_2_3": dif_bruta_2_3,
        "dif_liquida_atual": dif_liquida_atual,
        "dif_liquida_anterior": anterior,
        "var_horiz_pct": var_horiz_pct,
    }


# ==============================================================================
# 3. FUNÇÕES DE CÁLCULO E REGRAS DA CAMADA SILVER (RESULTADO — ITEM 8)
# ==============================================================================

def calcular_metricas_resultado(
    inef_trib_atual: float,
    diferenca_atual: float,
    diferencas_historico_mensal: list[float] | None = None,
    dif_acumulada_mes_anterior: float = 0.0,
) -> dict[str, Any]:
    """
    Aplica as fórmulas oficiais do Painel de Eliminação de Resultado (Seção 3 e 4):
      - Ineficiência Líquida = Inef. Trib + Diferença (Divergência)
      - Coluna AR ('Diferença Real Acumulada'): soma acumulada das diferenças de todos os meses
      - Coluna AS ('Sugestão de Diferença'): sugere 1 entre 3 status possíveis com base
        na comparação da Diferença Real Acumulada (Coluna AR).
    """
    inef_trib = round(inef_trib_atual or 0.0, 2)
    diferenca = round(diferenca_atual or 0.0, 2)
    inef_liquida = round(inef_trib + diferenca, 2)

    if diferencas_historico_mensal is not None:
        dif_real_acumulada = round(sum(diferencas_historico_mensal) + diferenca, 2)
    else:
        dif_real_acumulada = round((dif_acumulada_mes_anterior or 0.0) + diferenca, 2)

    if dif_real_acumulada > 0:
        sugestao_diferenca = "Receita Bruta maior que Despesa"
    elif dif_real_acumulada < 0:
        sugestao_diferenca = "Despesa maior que Receita Bruta"
    else:
        sugestao_diferenca = "Sem diferença"

    return {
        "inef_trib": inef_trib,
        "diferenca": diferenca,
        "inef_liquida": inef_liquida,
        "dif_real_acumulada_ar": dif_real_acumulada,
        "sugestao_diferenca_as": sugestao_diferenca,
    }


def validar_totais_resultado_silver(
    rec_liq_anterior: float,
    inef_trib_anterior: float,
    desp_anterior: float,
    rec_liq_atual: float,
    inef_trib_atual: float,
    desp_atual: float,
    tolerancia: float = 0.01,
) -> dict[str, str]:
    """
    Reproduz na Camada Silver do Databricks a lógica da planilha Validadora Manual
    de Resultado (Subscrever Totais: Mês Anterior vs Mês Atual).
    """
    ok_rec = abs((rec_liq_atual or 0.0) - (rec_liq_anterior or 0.0)) <= tolerancia
    ok_inef = abs((inef_trib_atual or 0.0) - (inef_trib_anterior or 0.0)) <= tolerancia
    ok_desp = abs((desp_atual or 0.0) - (desp_anterior or 0.0)) <= tolerancia

    return {
        "check_rec_liq": "OK Rec Liq" if ok_rec else "Divergente Rec Liq",
        "check_inef_tribut": "OK Inef Tribut" if ok_inef else "Divergente Inef Tribut",
        "check_despesa": "OK Despesa" if ok_desp else "Divergente Despesa",
        "status_validador": "Validado" if (ok_rec and ok_inef and ok_desp) else "Requer Análise",
    }


# ==============================================================================
# 4. SQL DDL & MERGE SCRIPTS PARA UNITY CATALOG / DATABRICKS
# ==============================================================================

DDL_DATABRICKS_SQL = """
-- Criação do Schema Intercompany no Unity Catalog (Databricks)
CREATE SCHEMA IF NOT EXISTS intercompany.silver;
CREATE SCHEMA IF NOT EXISTS intercompany.gold;

-- 1. Tabela Silver: Painel de Controle — Eliminação Patrimonial (Item 7)
CREATE TABLE IF NOT EXISTS intercompany.silver.painel_eliminacao_patrimonial (
    competencia STRING NOT NULL COMMENT 'Mês/Ano de fechamento (ex: 08/2026)',
    responsavel STRING COMMENT 'Analista responsável pelo crossing',
    cruzamento STRING NOT NULL COMMENT 'Identificador do crossing (ex: TBRA x ITIS)',
    ativo_origem DOUBLE COMMENT 'Empresa Origem - Ativo (1)',
    passivo_origem DOUBLE COMMENT 'Empresa Origem - Passivo (2)',
    ativo_contraparte DOUBLE COMMENT 'Empresa Contraparte - Ativo (3)',
    passivo_contraparte DOUBLE COMMENT 'Empresa Contraparte - Passivo (4)',
    dif_bruta_1_4 DOUBLE COMMENT 'Coluna H: (1) - (4)',
    dif_bruta_2_3 DOUBLE COMMENT 'Coluna I: (2) - (3)',
    dif_liquida_atual DOUBLE COMMENT 'Coluna J: Diferença Líquida do mês atual',
    dif_liquida_anterior DOUBLE COMMENT 'Coluna K: Diferença Líquida do mês anterior',
    var_horiz_pct DOUBLE COMMENT 'Coluna L: Variação Horizontal (%)',
    composicao_final_rede STRING COMMENT 'Coluna M: Composição Final salva na rede?',
    versao_resultado STRING COMMENT 'Coluna N: Versão Resultado',
    versao_patrimonio STRING COMMENT 'Coluna O: Versão Patrimônio',
    status_analista STRING COMMENT 'Coluna P: Status (Analista)',
    status_revisor STRING COMMENT 'Coluna Q: Status (Revisor)',
    comentarios_revisor STRING COMMENT 'Coluna R: Comentários (Revisor)',
    comentarios_analista STRING COMMENT 'Coluna S: Comentários (Analista)',
    atualizado_em TIMESTAMP COMMENT 'Timestamp da última atualização'
)
USING DELTA
PARTITIONED BY (competencia);

-- 2. View Gold: Aba Sum (Resumo Consolidado por Analista — Eliminação Patrimonial)
CREATE OR REPLACE VIEW intercompany.gold.vw_sum_eliminacao_patrimonial AS
SELECT
    competencia,
    CASE
        WHEN responsavel = 'Z_Sem Movimento' THEN 'Sem Movimento'
        ELSE responsavel
    END AS rotulo_linha,
    COUNT(cruzamento) AS contagem_cruzamento,
    SUM(COALESCE(dif_liquida_atual, 0)) AS soma_mes_atual,
    SUM(COALESCE(dif_liquida_anterior, 0)) AS soma_mes_anterior
FROM intercompany.silver.painel_eliminacao_patrimonial
WHERE responsavel != 'Incorporada'
GROUP BY
    competencia,
    CASE
        WHEN responsavel = 'Z_Sem Movimento' THEN 'Sem Movimento'
        ELSE responsavel
    END;

-- 3. Tabela Silver: Painel de Controle — Eliminação de Resultado (Item 8)
CREATE TABLE IF NOT EXISTS intercompany.silver.painel_eliminacao_resultado (
    competencia STRING NOT NULL COMMENT 'Mês/Ano de fechamento (ex: 08/2026)',
    responsavel STRING COMMENT 'Analista responsável pelo crossing',
    cruzamento STRING NOT NULL COMMENT 'Identificador do crossing (ex: TBRA x ITIS)',
    inef_trib_anterior DOUBLE COMMENT 'Ineficiência Tributária do mês anterior',
    diferenca_anterior DOUBLE COMMENT 'Diferença / Divergência do mês anterior',
    inef_liq_anterior DOUBLE COMMENT 'Ineficiência Líquida do mês anterior',
    inef_trib_atual DOUBLE COMMENT 'Ineficiência Tributária do mês de fechamento (Quadro Receita)',
    diferenca_atual DOUBLE COMMENT 'Divergência do mês de fechamento (Quadro Receita)',
    inef_liq_atual DOUBLE COMMENT 'Ineficiência Líquida calculada automaticamente',
    dif_real_acumulada_ar DOUBLE COMMENT 'Coluna AR: Diferença Real Acumulada de todos os meses',
    sugestao_diferenca_as STRING COMMENT 'Coluna AS: Sugestão automática de diferença',
    status_analista STRING COMMENT 'Status (Analista)',
    status_revisor STRING COMMENT 'Status (Revisor)',
    comentarios_analista STRING COMMENT 'Comentários (Analista)',
    comentarios_revisor STRING COMMENT 'Comentários (Revisor)',
    status_validador_silver STRING COMMENT 'Status do Validador Automático na Camada Silver',
    atualizado_em TIMESTAMP COMMENT 'Timestamp da última atualização'
)
USING DELTA
PARTITIONED BY (competencia);
"""


def gerar_query_merge_patrimonial() -> str:
    """Retorna a instrução MERGE INTO para atualização transacional no Delta Lake."""
    return """
    MERGE INTO intercompany.silver.painel_eliminacao_patrimonial AS target
    USING updates_patrimonial AS source
    ON target.competencia = source.competencia
       AND target.cruzamento = source.cruzamento
    WHEN MATCHED THEN UPDATE SET
        target.ativo_origem = source.ativo_origem,
        target.passivo_origem = source.passivo_origem,
        target.ativo_contraparte = source.ativo_contraparte,
        target.passivo_contraparte = source.passivo_contraparte,
        target.dif_bruta_1_4 = source.dif_bruta_1_4,
        target.dif_bruta_2_3 = source.dif_bruta_2_3,
        target.dif_liquida_atual = source.dif_liquida_atual,
        target.dif_liquida_anterior = source.dif_liquida_anterior,
        target.var_horiz_pct = source.var_horiz_pct,
        target.status_analista = COALESCE(source.status_analista, 'Recebido da ACT'),
        target.status_revisor = COALESCE(source.status_revisor, target.status_revisor),
        target.comentarios_analista = COALESCE(source.comentarios_analista, target.comentarios_analista),
        target.comentarios_revisor = COALESCE(source.comentarios_revisor, target.comentarios_revisor),
        target.atualizado_em = current_timestamp()
    WHEN NOT MATCHED THEN INSERT *;
    """

