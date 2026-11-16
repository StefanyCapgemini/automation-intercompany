# Databricks notebook source
# MAGIC %md
# MAGIC # Painel de Controle Intercompany — Fase 2 (100% Cloud / Serverless)
# MAGIC **Workspace:** `https://dbc-50a1800d-e3b0.cloud.databricks.com/`
# MAGIC
# MAGIC Este notebook executa **100% nos servidores Serverless do Databricks** (sem consumir CPU/RAM da sua máquina local) e implementa:
# MAGIC - **Item 7:** Painel de Controle — Eliminação Patrimonial (Abas `Elimináveis`, `Sum` e `Temas Principais`)
# MAGIC - **Item 8:** Painel de Controle — Eliminação de Resultado (Colunas `Inef. Trib`, `Diferença`, `Inef. Líq.`, `Coluna AR - Diferença Real Acumulada`, `Coluna AS - Sugestão de Diferença` e `Validador Automático na Camada Silver`)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Configuração Automática do Catálogo e Schemas (`silver` e `gold`)

# COMMAND ----------

catalogo_atual = spark.sql("SELECT current_catalog()").collect()[0][0]
print(f"Catálogo ativo no Workspace: {catalogo_atual}")

spark.sql(f"CREATE SCHEMA IF NOT EXISTS `{catalogo_atual}`.silver")
spark.sql(f"CREATE SCHEMA IF NOT EXISTS `{catalogo_atual}`.gold")
spark.sql(f"CREATE VOLUME IF NOT EXISTS `{catalogo_atual}`.silver.arquivos_intercompany")
print(f"Schemas '{catalogo_atual}.silver', '{catalogo_atual}.gold' e Volume 'arquivos_intercompany' prontos!")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Criação e Carga da Camada Silver — Eliminação Patrimonial (Item 7)
# MAGIC Inclui os 29 cruzamentos oficiais, fórmulas automáticas de Diferença Bruta `(1)-(4)` e `(2)-(3)`, Diferença Líquida e Variação Horizontal (%).

# COMMAND ----------

from pyspark.sql import types as T

DADOS_PATRIMONIAL = [
  {
    "linha": 5,
    "competencia": "08/2026",
    "responsavel": "Beatriz",
    "cruzamento": "ITIS x TGLOG",
    "ativo_1": 0.0,
    "passivo_2": -17261.71,
    "ativo_3": 207.44,
    "passivo_4": 0.0,
    "dif_bruta_1_4": 0.0,
    "dif_bruta_2_3": -17054.27,
    "dif_liquida_atual": -17054.27,
    "dif_liquida_anterior": -38.51,
    "var_horiz_pct": 441.853025,
    "comp_final_rede": "",
    "versao_resultado": "",
    "versao_patrimonio": "",
    "status_analista": "Enviado para reporting",
    "status_revisor": "Ok para envio",
    "comentarios_revisor": "",
    "comentarios_analista": "Entrou um valor de 17K de despesas operacionais na ITIS, que não foi registrado na TGLOG, será tratado no decorrer do mês."
  },
  {
    "linha": 6,
    "competencia": "08/2026",
    "responsavel": "Beatriz",
    "cruzamento": "TBRA x POP",
    "ativo_1": 358617.87,
    "passivo_2": -490491.70999999996,
    "ativo_3": 461386.94999999995,
    "passivo_4": -335505.62,
    "dif_bruta_1_4": 23112.25,
    "dif_bruta_2_3": -29104.76,
    "dif_liquida_atual": -5992.51,
    "dif_liquida_anterior": -18359.96,
    "var_horiz_pct": -0.67361,
    "comp_final_rede": "Sim",
    "versao_resultado": "V0",
    "versao_patrimonio": "V0",
    "status_analista": "Enviado para reporting",
    "status_revisor": "Ok para envio",
    "comentarios_revisor": "Bia analisar a conciliação no detalhe durante o mês para regularizar essa diferença.",
    "comentarios_analista": ""
  },
  {
    "linha": 7,
    "competencia": "08/2026",
    "responsavel": "Beatriz",
    "cruzamento": "TBRA x RECICLA V",
    "ativo_1": 875314.2599999999,
    "passivo_2": 0.0,
    "ativo_3": 0.0,
    "passivo_4": -1232711.86,
    "dif_bruta_1_4": -357397.6,
    "dif_bruta_2_3": 0.0,
    "dif_liquida_atual": -357397.6,
    "dif_liquida_anterior": -283586.84,
    "var_horiz_pct": 0.260276,
    "comp_final_rede": "",
    "versao_resultado": "",
    "versao_patrimonio": "",
    "status_analista": "Enviado para reporting",
    "status_revisor": "Ok para envio",
    "comentarios_revisor": "Bia analisar a conciliação no detalhe durante o mês para regularizar essa diferença.",
    "comentarios_analista": ""
  },
  {
    "linha": 8,
    "competencia": "08/2026",
    "responsavel": "Beatriz",
    "cruzamento": "TGLOG x CLOUD",
    "ativo_1": 0.0,
    "passivo_2": 0.0,
    "ativo_3": 0.0,
    "passivo_4": 0.0,
    "dif_bruta_1_4": 0.0,
    "dif_bruta_2_3": 0.0,
    "dif_liquida_atual": 0.0,
    "dif_liquida_anterior": 0.0,
    "var_horiz_pct": null,
    "comp_final_rede": "",
    "versao_resultado": "",
    "versao_patrimonio": "",
    "status_analista": "Sem movimento",
    "status_revisor": "Sem movimento",
    "comentarios_revisor": "",
    "comentarios_analista": ""
  },
  {
    "linha": 9,
    "competencia": "08/2026",
    "responsavel": "Incorporada",
    "cruzamento": "TGLOG x FIBR",
    "ativo_1": 0.0,
    "passivo_2": 0.0,
    "ativo_3": 0.0,
    "passivo_4": 0.0,
    "dif_bruta_1_4": 0.0,
    "dif_bruta_2_3": 0.0,
    "dif_liquida_atual": 0.0,
    "dif_liquida_anterior": 0.0,
    "var_horiz_pct": null,
    "comp_final_rede": "",
    "versao_resultado": "",
    "versao_patrimonio": "",
    "status_analista": "Incorporada",
    "status_revisor": "Incorporada",
    "comentarios_revisor": "",
    "comentarios_analista": ""
  },
  {
    "linha": 10,
    "competencia": "08/2026",
    "responsavel": "Thais",
    "cruzamento": "ITIS x CLOUD",
    "ativo_1": -3792912.41,
    "passivo_2": 9607611.46,
    "ativo_3": -5435502.290000001,
    "passivo_4": -701523.55,
    "dif_bruta_1_4": -4494435.96,
    "dif_bruta_2_3": 4172109.17,
    "dif_liquida_atual": -322326.79,
    "dif_liquida_anterior": 25325.61,
    "var_horiz_pct": -13.727306,
    "comp_final_rede": "",
    "versao_resultado": "",
    "versao_patrimonio": "",
    "status_analista": "Enviado para reporting",
    "status_revisor": "Ok para envio",
    "comentarios_revisor": "",
    "comentarios_analista": "A diferença refere-se provisão 1MM + 990K de diferimento, compensado pelo  lucro na venda de mercadoria 1.7MM"
  },
  {
    "linha": 11,
    "competencia": "08/2026",
    "responsavel": "Mayara",
    "cruzamento": "ITIS x TERRA",
    "ativo_1": 159501.27000000002,
    "passivo_2": 0.0,
    "ativo_3": 0.0,
    "passivo_4": -166442.56,
    "dif_bruta_1_4": -6941.29,
    "dif_bruta_2_3": 0.0,
    "dif_liquida_atual": -6941.29,
    "dif_liquida_anterior": -4758.36,
    "var_horiz_pct": 0.458757,
    "comp_final_rede": "",
    "versao_resultado": "",
    "versao_patrimonio": "",
    "status_analista": "Enviado para reporting",
    "status_revisor": "Ok para envio",
    "comentarios_revisor": "",
    "comentarios_analista": ""
  },
  {
    "linha": 12,
    "competencia": "08/2026",
    "responsavel": "Mayara",
    "cruzamento": "TBRA x ITIS",
    "ativo_1": 99731615.14000002,
    "passivo_2": -119690699.07000001,
    "ativo_3": 85712089.69000001,
    "passivo_4": -51617218.32,
    "dif_bruta_1_4": 48114396.82,
    "dif_bruta_2_3": -33978609.38,
    "dif_liquida_atual": 14135787.44,
    "dif_liquida_anterior": 5897146.92,
    "var_horiz_pct": 1.397055,
    "comp_final_rede": "Sim",
    "versao_resultado": "V0",
    "versao_patrimonio": "V0",
    "status_analista": "Enviado para reporting",
    "status_revisor": "Ok para envio",
    "comentarios_revisor": "",
    "comentarios_analista": "A principal diferença refere-se 16,1MM de lucro não realizado, compensado pelo valor de 3MM de diferenças entre as provisoes e entradas de notas fiscais que serao conciliados durante o mês para regularização das diferenças, entre outros temas."
  },
  {
    "linha": 13,
    "competencia": "08/2026",
    "responsavel": "Cibele",
    "cruzamento": "TBRA x TERRA",
    "ativo_1": 5326521.699999999,
    "passivo_2": -2210242.86,
    "ativo_3": 3479078.2899999996,
    "passivo_4": -7030899.65,
    "dif_bruta_1_4": -1704377.95,
    "dif_bruta_2_3": 1268835.43,
    "dif_liquida_atual": -435542.52,
    "dif_liquida_anterior": -463818.72,
    "var_horiz_pct": -0.060964,
    "comp_final_rede": "",
    "versao_resultado": "",
    "versao_patrimonio": "",
    "status_analista": "Enviado para reporting",
    "status_revisor": "Ok para envio",
    "comentarios_revisor": "",
    "comentarios_analista": "Referente a provisão de rateio de despesa tributária onde o valor da contra parte está a maior"
  },
  {
    "linha": 14,
    "competencia": "08/2026",
    "responsavel": "Cibele",
    "cruzamento": "CLOUD x VSCD",
    "ativo_1": 1590002.93,
    "passivo_2": 0.0,
    "ativo_3": 0.0,
    "passivo_4": -1770640.36,
    "dif_bruta_1_4": -180637.43,
    "dif_bruta_2_3": 0.0,
    "dif_liquida_atual": -180637.43,
    "dif_liquida_anterior": -1618549.78,
    "var_horiz_pct": -0.888396,
    "comp_final_rede": "",
    "versao_resultado": "",
    "versao_patrimonio": "",
    "status_analista": "Enviado para reporting",
    "status_revisor": "Ok para envio",
    "comentarios_revisor": "",
    "comentarios_analista": "Refere-se a regularização do A Faturar da Azure na Cloud"
  },
  {
    "linha": 15,
    "competencia": "08/2026",
    "responsavel": "Incorporada",
    "cruzamento": "CLOUD x CYBR",
    "ativo_1": 0.0,
    "passivo_2": 0.0,
    "ativo_3": 0.0,
    "passivo_4": 0.0,
    "dif_bruta_1_4": 0.0,
    "dif_bruta_2_3": 0.0,
    "dif_liquida_atual": 0.0,
    "dif_liquida_anterior": 0.0,
    "var_horiz_pct": null,
    "comp_final_rede": "",
    "versao_resultado": "",
    "versao_patrimonio": "",
    "status_analista": "Incorporada",
    "status_revisor": "Incorporada",
    "comentarios_revisor": "",
    "comentarios_analista": ""
  },
  {
    "linha": 16,
    "competencia": "08/2026",
    "responsavel": "Incorporada",
    "cruzamento": "ITIS X CYBR",
    "ativo_1": 0.0,
    "passivo_2": 0.0,
    "ativo_3": 0.0,
    "passivo_4": 0.0,
    "dif_bruta_1_4": 0.0,
    "dif_bruta_2_3": 0.0,
    "dif_liquida_atual": 0.0,
    "dif_liquida_anterior": 0.0,
    "var_horiz_pct": null,
    "comp_final_rede": "",
    "versao_resultado": "",
    "versao_patrimonio": "",
    "status_analista": "Incorporada",
    "status_revisor": "Incorporada",
    "comentarios_revisor": "",
    "comentarios_analista": ""
  },
  {
    "linha": 17,
    "competencia": "08/2026",
    "responsavel": "Thais",
    "cruzamento": "TBRA x CLOUD",
    "ativo_1": 88179837.49999999,
    "passivo_2": -90640811.25999999,
    "ativo_3": 92401182.18999998,
    "passivo_4": -89869363.24,
    "dif_bruta_1_4": -1689525.74,
    "dif_bruta_2_3": 1760370.93,
    "dif_liquida_atual": 70845.19,
    "dif_liquida_anterior": 447708.75,
    "var_horiz_pct": -0.841761,
    "comp_final_rede": "",
    "versao_resultado": "",
    "versao_patrimonio": "",
    "status_analista": "Enviado para reporting",
    "status_revisor": "Ok para envio",
    "comentarios_revisor": "",
    "comentarios_analista": ""
  },
  {
    "linha": 18,
    "competencia": "08/2026",
    "responsavel": "Cibele",
    "cruzamento": "TBRA x VALE (VSS)",
    "ativo_1": 436832.62,
    "passivo_2": -6095807.05,
    "ativo_3": 6095807.05,
    "passivo_4": -287182.82,
    "dif_bruta_1_4": 149649.8,
    "dif_bruta_2_3": 0.0,
    "dif_liquida_atual": 149649.8,
    "dif_liquida_anterior": 281164.13,
    "var_horiz_pct": -0.467749,
    "comp_final_rede": "",
    "versao_resultado": "",
    "versao_patrimonio": "",
    "status_analista": "Enviado para reporting",
    "status_revisor": "Ok para envio",
    "comentarios_revisor": "",
    "comentarios_analista": "Refere-se a provisão de Reembolso de Licen. Microsoft que não foi considerado pela contraparte"
  },
  {
    "linha": 19,
    "competencia": "08/2026",
    "responsavel": "Cibele",
    "cruzamento": "TBRA x VSCD (VPAY SCD)",
    "ativo_1": 1769150.69,
    "passivo_2": -729238.63,
    "ativo_3": 0.0,
    "passivo_4": -1692567.8499999999,
    "dif_bruta_1_4": 76582.84,
    "dif_bruta_2_3": -729238.63,
    "dif_liquida_atual": -652655.79,
    "dif_liquida_anterior": -1785213.89,
    "var_horiz_pct": -0.63441,
    "comp_final_rede": "",
    "versao_resultado": "",
    "versao_patrimonio": "",
    "status_analista": "Enviado para reporting",
    "status_revisor": "Ok para envio",
    "comentarios_revisor": "",
    "comentarios_analista": "Refere-se a regularização do A Faturar da Azure na contraparte"
  },
  {
    "linha": 20,
    "competencia": "08/2026",
    "responsavel": "Thais",
    "cruzamento": "TERRA x CLOUD",
    "ativo_1": 0.0,
    "passivo_2": -907303.49,
    "ativo_3": 947469.8,
    "passivo_4": 0.0,
    "dif_bruta_1_4": 0.0,
    "dif_bruta_2_3": 40166.31,
    "dif_liquida_atual": 40166.31,
    "dif_liquida_anterior": 236739.48,
    "var_horiz_pct": -0.830335,
    "comp_final_rede": "",
    "versao_resultado": "",
    "versao_patrimonio": "",
    "status_analista": "Enviado para reporting",
    "status_revisor": "Ok para envio",
    "comentarios_revisor": "",
    "comentarios_analista": ""
  },
  {
    "linha": 21,
    "competencia": "08/2026",
    "responsavel": "Beatriz",
    "cruzamento": "TERRA x VALE (VSS)",
    "ativo_1": 0.0,
    "passivo_2": -7.58,
    "ativo_3": 0.0,
    "passivo_4": 0.0,
    "dif_bruta_1_4": 0.0,
    "dif_bruta_2_3": -7.58,
    "dif_liquida_atual": -7.58,
    "dif_liquida_anterior": -15.16,
    "var_horiz_pct": -0.5,
    "comp_final_rede": "",
    "versao_resultado": "",
    "versao_patrimonio": "",
    "status_analista": "Enviado para reporting",
    "status_revisor": "Ok para envio",
    "comentarios_revisor": "",
    "comentarios_analista": ""
  },
  {
    "linha": 22,
    "competencia": "08/2026",
    "responsavel": "Beatriz",
    "cruzamento": "VIMO (VPAY FUNDO) x VSCD",
    "ativo_1": 0.0,
    "passivo_2": -420910.25,
    "ativo_3": 420910.25,
    "passivo_4": 0.0,
    "dif_bruta_1_4": 0.0,
    "dif_bruta_2_3": 0.0,
    "dif_liquida_atual": 0.0,
    "dif_liquida_anterior": 0.0,
    "var_horiz_pct": null,
    "comp_final_rede": "",
    "versao_resultado": "",
    "versao_patrimonio": "",
    "status_analista": "Enviado para reporting",
    "status_revisor": "Ok para envio",
    "comentarios_revisor": "",
    "comentarios_analista": ""
  },
  {
    "linha": 23,
    "competencia": "08/2026",
    "responsavel": "Beatriz",
    "cruzamento": "VSCD x VPY3",
    "ativo_1": 10962.92,
    "passivo_2": 0.0,
    "ativo_3": 0.0,
    "passivo_4": -10962.92,
    "dif_bruta_1_4": 0.0,
    "dif_bruta_2_3": 0.0,
    "dif_liquida_atual": 0.0,
    "dif_liquida_anterior": 0.0,
    "var_horiz_pct": null,
    "comp_final_rede": "",
    "versao_resultado": "",
    "versao_patrimonio": "",
    "status_analista": "Enviado para reporting",
    "status_revisor": "Ok para envio",
    "comentarios_revisor": "",
    "comentarios_analista": ""
  },
  {
    "linha": 24,
    "competencia": "08/2026",
    "responsavel": "Incorporada",
    "cruzamento": "CLOUD x FIBR",
    "ativo_1": 0.0,
    "passivo_2": 0.0,
    "ativo_3": 0.0,
    "passivo_4": 0.0,
    "dif_bruta_1_4": 0.0,
    "dif_bruta_2_3": 0.0,
    "dif_liquida_atual": 0.0,
    "dif_liquida_anterior": -507374.44,
    "var_horiz_pct": -1.0,
    "comp_final_rede": "",
    "versao_resultado": "",
    "versao_patrimonio": "",
    "status_analista": "Incorporada",
    "status_revisor": "Incorporada",
    "comentarios_revisor": "",
    "comentarios_analista": ""
  },
  {
    "linha": 25,
    "competencia": "08/2026",
    "responsavel": "Incorporada",
    "cruzamento": "TBRA X CYBR",
    "ativo_1": 0.0,
    "passivo_2": 0.0,
    "ativo_3": 0.0,
    "passivo_4": 0.0,
    "dif_bruta_1_4": 0.0,
    "dif_bruta_2_3": 0.0,
    "dif_liquida_atual": 0.0,
    "dif_liquida_anterior": 0.0,
    "var_horiz_pct": null,
    "comp_final_rede": "",
    "versao_resultado": "",
    "versao_patrimonio": "",
    "status_analista": "Incorporada",
    "status_revisor": "Incorporada",
    "comentarios_revisor": "",
    "comentarios_analista": ""
  },
  {
    "linha": 26,
    "competencia": "08/2026",
    "responsavel": "Incorporada",
    "cruzamento": "TBRA x FIBR",
    "ativo_1": 0.0,
    "passivo_2": 0.0,
    "ativo_3": 0.0,
    "passivo_4": 0.0,
    "dif_bruta_1_4": 0.0,
    "dif_bruta_2_3": 0.0,
    "dif_liquida_atual": 0.0,
    "dif_liquida_anterior": -2935327.32,
    "var_horiz_pct": -1.0,
    "comp_final_rede": "",
    "versao_resultado": "",
    "versao_patrimonio": "",
    "status_analista": "Incorporada",
    "status_revisor": "Incorporada",
    "comentarios_revisor": "",
    "comentarios_analista": ""
  },
  {
    "linha": 27,
    "competencia": "08/2026",
    "responsavel": "Thais",
    "cruzamento": "TBRA X I2GO",
    "ativo_1": 19180461.7,
    "passivo_2": -4319830.91,
    "ativo_3": 1165497.36,
    "passivo_4": -15228234.24,
    "dif_bruta_1_4": 3952227.46,
    "dif_bruta_2_3": -3154333.55,
    "dif_liquida_atual": 797893.91,
    "dif_liquida_anterior": 1056334.18,
    "var_horiz_pct": -0.244658,
    "comp_final_rede": "",
    "versao_resultado": "",
    "versao_patrimonio": "",
    "status_analista": "Enviado para reporting",
    "status_revisor": "Ok para envio",
    "comentarios_revisor": "",
    "comentarios_analista": "Temos registrado em ambos os lados 15MM de adiantamento"
  },
  {
    "linha": 28,
    "competencia": "08/2026",
    "responsavel": "Cibele",
    "cruzamento": "TBRA x TGLOG",
    "ativo_1": 4964126.2700000005,
    "passivo_2": -25961222.889999997,
    "ativo_3": 26062166.310000002,
    "passivo_4": -4851073.12,
    "dif_bruta_1_4": 113053.15,
    "dif_bruta_2_3": 100943.42,
    "dif_liquida_atual": 213996.57,
    "dif_liquida_anterior": 130893.77,
    "var_horiz_pct": 0.634887,
    "comp_final_rede": "",
    "versao_resultado": "",
    "versao_patrimonio": "",
    "status_analista": "Enviado para reporting",
    "status_revisor": "Ok para envio",
    "comentarios_revisor": "",
    "comentarios_analista": "A diferença refere-se a provisão trabalhista considerada a menor na contraparte"
  },
  {
    "linha": 29,
    "competencia": "08/2026",
    "responsavel": "Incorporada",
    "cruzamento": "TGLOG  X CYBR",
    "ativo_1": 0.0,
    "passivo_2": 0.0,
    "ativo_3": 0.0,
    "passivo_4": 0.0,
    "dif_bruta_1_4": 0.0,
    "dif_bruta_2_3": 0.0,
    "dif_liquida_atual": 0.0,
    "dif_liquida_anterior": 0.0,
    "var_horiz_pct": null,
    "comp_final_rede": "",
    "versao_resultado": "",
    "versao_patrimonio": "",
    "status_analista": "Incorporada",
    "status_revisor": "Incorporada",
    "comentarios_revisor": "",
    "comentarios_analista": ""
  },
  {
    "linha": 30,
    "competencia": "08/2026",
    "responsavel": "Thais",
    "cruzamento": "VSS X I2GO",
    "ativo_1": 0.0,
    "passivo_2": 0.0,
    "ativo_3": 0.0,
    "passivo_4": 0.0,
    "dif_bruta_1_4": 0.0,
    "dif_bruta_2_3": 0.0,
    "dif_liquida_atual": 0.0,
    "dif_liquida_anterior": 0.0,
    "var_horiz_pct": null,
    "comp_final_rede": "",
    "versao_resultado": "",
    "versao_patrimonio": "",
    "status_analista": "Sem movimento",
    "status_revisor": "Sem movimento",
    "comentarios_revisor": "",
    "comentarios_analista": ""
  },
  {
    "linha": 31,
    "competencia": "08/2026",
    "responsavel": "Z_Sem Movimento",
    "cruzamento": "TBRA x VIMO (VPAY FUNDO)",
    "ativo_1": 0.0,
    "passivo_2": 0.0,
    "ativo_3": 0.0,
    "passivo_4": 0.0,
    "dif_bruta_1_4": 0.0,
    "dif_bruta_2_3": 0.0,
    "dif_liquida_atual": 0.0,
    "dif_liquida_anterior": 0.0,
    "var_horiz_pct": null,
    "comp_final_rede": "",
    "versao_resultado": "",
    "versao_patrimonio": "",
    "status_analista": "Sem movimento",
    "status_revisor": "Sem movimento",
    "comentarios_revisor": "",
    "comentarios_analista": ""
  },
  {
    "linha": 32,
    "competencia": "08/2026",
    "responsavel": "Z_Sem Movimento",
    "cruzamento": "TBRA x VPAY (VPAY HOLDING)",
    "ativo_1": 0.0,
    "passivo_2": 0.0,
    "ativo_3": 0.0,
    "passivo_4": 0.0,
    "dif_bruta_1_4": 0.0,
    "dif_bruta_2_3": 0.0,
    "dif_liquida_atual": 0.0,
    "dif_liquida_anterior": 0.0,
    "var_horiz_pct": null,
    "comp_final_rede": "",
    "versao_resultado": "",
    "versao_patrimonio": "",
    "status_analista": "Sem movimento",
    "status_revisor": "Sem movimento",
    "comentarios_revisor": "",
    "comentarios_analista": ""
  },
  {
    "linha": 33,
    "competencia": "08/2026",
    "responsavel": "Z_Sem Movimento",
    "cruzamento": "TBRA x VVENTURES",
    "ativo_1": 0.0,
    "passivo_2": 0.0,
    "ativo_3": 0.0,
    "passivo_4": 0.0,
    "dif_bruta_1_4": 0.0,
    "dif_bruta_2_3": 0.0,
    "dif_liquida_atual": 0.0,
    "dif_liquida_anterior": 0.0,
    "var_horiz_pct": null,
    "comp_final_rede": "",
    "versao_resultado": "",
    "versao_patrimonio": "",
    "status_analista": "Sem movimento",
    "status_revisor": "Sem movimento",
    "comentarios_revisor": "",
    "comentarios_analista": ""
  }
]

DADOS_TEMAS = [
  {
    "cruzamento": "CLOUD x FIBR",
    "temas_entre_empresas": "",
    "ativo_passivo_origem": "",
    "ativo_passivo_contraparte": ""
  },
  {
    "cruzamento": "CLOUD x VSCD",
    "temas_entre_empresas": "",
    "ativo_passivo_origem": "",
    "ativo_passivo_contraparte": ""
  },
  {
    "cruzamento": "CYBR x CLOUD",
    "temas_entre_empresas": "",
    "ativo_passivo_origem": "",
    "ativo_passivo_contraparte": ""
  },
  {
    "cruzamento": "ITIS x CLOUD",
    "temas_entre_empresas": "",
    "ativo_passivo_origem": "",
    "ativo_passivo_contraparte": ""
  },
  {
    "cruzamento": "ITIS X CYBR",
    "temas_entre_empresas": "",
    "ativo_passivo_origem": "",
    "ativo_passivo_contraparte": ""
  },
  {
    "cruzamento": "ITIS x TGLOG",
    "temas_entre_empresas": "",
    "ativo_passivo_origem": "",
    "ativo_passivo_contraparte": ""
  },
  {
    "cruzamento": "TBRA x CLOUD",
    "temas_entre_empresas": "",
    "ativo_passivo_origem": "",
    "ativo_passivo_contraparte": ""
  },
  {
    "cruzamento": "TBRA X CYBR",
    "temas_entre_empresas": "",
    "ativo_passivo_origem": "",
    "ativo_passivo_contraparte": ""
  },
  {
    "cruzamento": "TBRA x FIBR",
    "temas_entre_empresas": "",
    "ativo_passivo_origem": "",
    "ativo_passivo_contraparte": ""
  },
  {
    "cruzamento": "TBRA X I2GO",
    "temas_entre_empresas": "",
    "ativo_passivo_origem": "",
    "ativo_passivo_contraparte": ""
  },
  {
    "cruzamento": "TBRA x ITIS",
    "temas_entre_empresas": "",
    "ativo_passivo_origem": "",
    "ativo_passivo_contraparte": ""
  },
  {
    "cruzamento": "TBRA x POP",
    "temas_entre_empresas": "",
    "ativo_passivo_origem": "",
    "ativo_passivo_contraparte": ""
  },
  {
    "cruzamento": "TBRA x RECICLA V",
    "temas_entre_empresas": "",
    "ativo_passivo_origem": "",
    "ativo_passivo_contraparte": ""
  },
  {
    "cruzamento": "TBRA x TERRA",
    "temas_entre_empresas": "",
    "ativo_passivo_origem": "",
    "ativo_passivo_contraparte": ""
  },
  {
    "cruzamento": "TBRA x TGLOG",
    "temas_entre_empresas": "",
    "ativo_passivo_origem": "",
    "ativo_passivo_contraparte": ""
  },
  {
    "cruzamento": "TBRA x VALE (VSS)",
    "temas_entre_empresas": "Comissão sobre venda de assinaturas de saúde, faturado pela VSS. Aluguel de imóvel, faturado pela TBRA. Rateio de salários, faturado pela TBRA.",
    "ativo_passivo_origem": "",
    "ativo_passivo_contraparte": ""
  },
  {
    "cruzamento": "TBRA x VIMO (VPAY FUNDO)",
    "temas_entre_empresas": "Sem movimento",
    "ativo_passivo_origem": "",
    "ativo_passivo_contraparte": ""
  },
  {
    "cruzamento": "TBRA x VPAY (VPAY HOLDING)",
    "temas_entre_empresas": "Sem movimento",
    "ativo_passivo_origem": "",
    "ativo_passivo_contraparte": ""
  },
  {
    "cruzamento": "TBRA x VSCD (VPAY SCD)",
    "temas_entre_empresas": "Rateio de Salários, prestados pela TBRA.",
    "ativo_passivo_origem": "",
    "ativo_passivo_contraparte": ""
  },
  {
    "cruzamento": "TBRA x VVENTURES",
    "temas_entre_empresas": "Sem movimento",
    "ativo_passivo_origem": "",
    "ativo_passivo_contraparte": ""
  },
  {
    "cruzamento": "TERRA x CLOUD",
    "temas_entre_empresas": "",
    "ativo_passivo_origem": "",
    "ativo_passivo_contraparte": ""
  },
  {
    "cruzamento": "TERRA X ITIS",
    "temas_entre_empresas": "",
    "ativo_passivo_origem": "",
    "ativo_passivo_contraparte": ""
  },
  {
    "cruzamento": "TERRA x VALE SAÚDE",
    "temas_entre_empresas": "Comissão sobre venda de assinaturas de saúde, faturado pela VSS.",
    "ativo_passivo_origem": "",
    "ativo_passivo_contraparte": ""
  },
  {
    "cruzamento": "TGLOG  X CYBR",
    "temas_entre_empresas": "",
    "ativo_passivo_origem": "",
    "ativo_passivo_contraparte": ""
  },
  {
    "cruzamento": "TGLOG x CLOUD",
    "temas_entre_empresas": "",
    "ativo_passivo_origem": "",
    "ativo_passivo_contraparte": ""
  },
  {
    "cruzamento": "TGLOG x FIBR",
    "temas_entre_empresas": "",
    "ativo_passivo_origem": "",
    "ativo_passivo_contraparte": ""
  },
  {
    "cruzamento": "VIMO x VSCD",
    "temas_entre_empresas": "Prest. Serviços de Cobranças faturado pela VSCD.",
    "ativo_passivo_origem": "",
    "ativo_passivo_contraparte": ""
  }
]

schema_pat = T.StructType([
    T.StructField("linha", T.IntegerType(), True),
    T.StructField("competencia", T.StringType(), False),
    T.StructField("responsavel", T.StringType(), True),
    T.StructField("cruzamento", T.StringType(), False),
    T.StructField("ativo_1", T.DoubleType(), True),
    T.StructField("passivo_2", T.DoubleType(), True),
    T.StructField("ativo_3", T.DoubleType(), True),
    T.StructField("passivo_4", T.DoubleType(), True),
    T.StructField("dif_bruta_1_4", T.DoubleType(), True),
    T.StructField("dif_bruta_2_3", T.DoubleType(), True),
    T.StructField("dif_liquida_atual", T.DoubleType(), True),
    T.StructField("dif_liquida_anterior", T.DoubleType(), True),
    T.StructField("var_horiz_pct", T.DoubleType(), True),
    T.StructField("comp_final_rede", T.StringType(), True),
    T.StructField("versao_resultado", T.StringType(), True),
    T.StructField("versao_patrimonio", T.StringType(), True),
    T.StructField("status_analista", T.StringType(), True),
    T.StructField("status_revisor", T.StringType(), True),
    T.StructField("comentarios_revisor", T.StringType(), True),
    T.StructField("comentarios_analista", T.StringType(), True),
])

df_pat = spark.createDataFrame(DADOS_PATRIMONIAL, schema=schema_pat)
df_pat.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(
    f"`{catalogo_atual}`.silver.painel_eliminacao_patrimonial"
)

df_temas = spark.createDataFrame(DADOS_TEMAS)
df_temas.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(
    f"`{catalogo_atual}`.silver.temas_principais_patrimonial"
)

# Criação da View Gold equivalente à Aba Sum
spark.sql(f"""
CREATE OR REPLACE VIEW `{catalogo_atual}`.gold.vw_sum_eliminacao_patrimonial AS
SELECT
    competencia,
    CASE
        WHEN responsavel = 'Z_Sem Movimento' THEN 'Sem Movimento'
        ELSE responsavel
    END AS rotulo_linha,
    COUNT(cruzamento) AS contagem_cruzamento,
    ROUND(SUM(COALESCE(dif_liquida_atual, 0)), 2) AS soma_ago_26,
    ROUND(SUM(COALESCE(dif_liquida_anterior, 0)), 2) AS soma_jul_26
FROM `{catalogo_atual}`.silver.painel_eliminacao_patrimonial
WHERE responsavel != 'Incorporada'
GROUP BY
    competencia,
    CASE
        WHEN responsavel = 'Z_Sem Movimento' THEN 'Sem Movimento'
        ELSE responsavel
    END
""")

display(spark.table(f"`{catalogo_atual}`.silver.painel_eliminacao_patrimonial").orderBy("linha"))

# COMMAND ----------

# MAGIC %md
# MAGIC ### 2.1. Visualização da Aba `Sum` (Resumo por Analista — Camada Gold)

# COMMAND ----------

display(spark.table(f"`{catalogo_atual}`.gold.vw_sum_eliminacao_patrimonial"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Criação e Carga da Camada Silver — Eliminação de Resultado & Validador (Item 8)
# MAGIC Calcula automaticamente `Inef. Líquida`, `Coluna AR (Diferença Real Acumulada)` e `Coluna AS (Sugestão de Diferença)`.

# COMMAND ----------

DADOS_RESULTADO = [
  {
    "linha": 1,
    "competencia": "08/2026",
    "responsavel": "Incorporada",
    "cruzamento": "CLOUD x FIBR",
    "jul_inef_trib": 0.0,
    "jul_diferenca": -95435.53,
    "jul_inef_liq": -95435.53,
    "ago_inef_trib": 0.0,
    "ago_diferenca": 0.0,
    "ago_inef_liq": 0.0,
    "dif_real_acumulada_ar": -95435.53,
    "sugestao_diferenca_as": "Despesa maior que Receita Bruta",
    "status_analista": "Incorporada",
    "status_revisor": "Incorporada",
    "comentarios_analista": "",
    "comentarios_revisor": "",
    "validador_silver": "Validado (OK Rec Liq | OK Inef Tribut | OK Despesa)"
  },
  {
    "linha": 2,
    "competencia": "08/2026",
    "responsavel": "Cibele",
    "cruzamento": "CLOUD x VSCD",
    "jul_inef_trib": 0.0,
    "jul_diferenca": -459196.37,
    "jul_inef_liq": -459196.37,
    "ago_inef_trib": 1508218.85,
    "ago_diferenca": 81784.08,
    "ago_inef_liq": 1590002.93,
    "dif_real_acumulada_ar": 656134.95,
    "sugestao_diferenca_as": "Receita Bruta maior que Despesa",
    "status_analista": "Enviado para reporting",
    "status_revisor": "Ok para envio",
    "comentarios_analista": "Tratativa dada a Azure",
    "comentarios_revisor": "",
    "validador_silver": "Validado (OK Rec Liq | OK Inef Tribut | OK Despesa)"
  },
  {
    "linha": 3,
    "competencia": "08/2026",
    "responsavel": "Incorporada",
    "cruzamento": "CYBR x CLOUD",
    "jul_inef_trib": 0.0,
    "jul_diferenca": 0.0,
    "jul_inef_liq": 0.0,
    "ago_inef_trib": 0.0,
    "ago_diferenca": 0.0,
    "ago_inef_liq": 0.0,
    "dif_real_acumulada_ar": 0.0,
    "sugestao_diferenca_as": "Sem diferença",
    "status_analista": "Incorporada",
    "status_revisor": "Incorporada",
    "comentarios_analista": "",
    "comentarios_revisor": "",
    "validador_silver": "Validado (OK Rec Liq | OK Inef Tribut | OK Despesa)"
  },
  {
    "linha": 4,
    "competencia": "08/2026",
    "responsavel": "Thais",
    "cruzamento": "ITIS x CLOUD",
    "jul_inef_trib": -66323.37,
    "jul_diferenca": -26899.27,
    "jul_inef_liq": -93222.64,
    "ago_inef_trib": -58620.06,
    "ago_diferenca": 3578.98,
    "ago_inef_liq": -55041.08,
    "dif_real_acumulada_ar": -857280.03,
    "sugestao_diferenca_as": "Despesa maior que Receita Bruta",
    "status_analista": "Enviado para reporting",
    "status_revisor": "Ok para envio",
    "comentarios_analista": "",
    "comentarios_revisor": "",
    "validador_silver": "Validado (OK Rec Liq | OK Inef Tribut | OK Despesa)"
  },
  {
    "linha": 5,
    "competencia": "08/2026",
    "responsavel": "Incorporada",
    "cruzamento": "ITIS X CYBR",
    "jul_inef_trib": 0.0,
    "jul_diferenca": 0.0,
    "jul_inef_liq": 0.0,
    "ago_inef_trib": 0.0,
    "ago_diferenca": 0.0,
    "ago_inef_liq": 0.0,
    "dif_real_acumulada_ar": 0.0,
    "sugestao_diferenca_as": "Sem diferença",
    "status_analista": "Incorporada",
    "status_revisor": "Incorporada",
    "comentarios_analista": "",
    "comentarios_revisor": "",
    "validador_silver": "Validado (OK Rec Liq | OK Inef Tribut | OK Despesa)"
  },
  {
    "linha": 6,
    "competencia": "08/2026",
    "responsavel": "Mayara",
    "cruzamento": "ITIS x TERRA",
    "jul_inef_trib": -10857.1,
    "jul_diferenca": 32890.22,
    "jul_inef_liq": 22033.12,
    "ago_inef_trib": -2525.77,
    "ago_diferenca": -2182.92,
    "ago_inef_liq": -4708.69,
    "dif_real_acumulada_ar": 62424.56,
    "sugestao_diferenca_as": "Receita Bruta maior que Despesa",
    "status_analista": "Enviado para reporting",
    "status_revisor": "Ok para envio",
    "comentarios_analista": "",
    "comentarios_revisor": "",
    "validador_silver": "Validado (OK Rec Liq | OK Inef Tribut | OK Despesa)"
  },
  {
    "linha": 7,
    "competencia": "08/2026",
    "responsavel": "Beatriz",
    "cruzamento": "ITIS x TGLOG",
    "jul_inef_trib": 0.0,
    "jul_diferenca": -123.58,
    "jul_inef_liq": -123.58,
    "ago_inef_trib": 0.0,
    "ago_diferenca": -123.58,
    "ago_inef_liq": -123.58,
    "dif_real_acumulada_ar": 74510.72,
    "sugestao_diferenca_as": "Receita Bruta maior que Despesa",
    "status_analista": "Enviado para reporting",
    "status_revisor": "Ok para envio",
    "comentarios_analista": "",
    "comentarios_revisor": "Avaliar do que se trata esse valor tão pequeno para que ele seja conciliado ou até mesmo cancelado.",
    "validador_silver": "Validado (OK Rec Liq | OK Inef Tribut | OK Despesa)"
  },
  {
    "linha": 8,
    "competencia": "08/2026",
    "responsavel": "Thais",
    "cruzamento": "TBRA x CLOUD",
    "jul_inef_trib": -2467838.26,
    "jul_diferenca": 284225.83,
    "jul_inef_liq": -2183612.43,
    "ago_inef_trib": -2226172.98,
    "ago_diferenca": 828825.93,
    "ago_inef_liq": -1397347.05,
    "dif_real_acumulada_ar": 1113051.76,
    "sugestao_diferenca_as": "Receita Bruta maior que Despesa",
    "status_analista": "Enviado para reporting",
    "status_revisor": "Ok para envio",
    "comentarios_analista": "A dif refere principalmente a 800k de diferimento",
    "comentarios_revisor": "",
    "validador_silver": "Validado (OK Rec Liq | OK Inef Tribut | OK Despesa)"
  },
  {
    "linha": 9,
    "competencia": "08/2026",
    "responsavel": "Incorporada",
    "cruzamento": "TBRA X CYBR",
    "jul_inef_trib": 0.0,
    "jul_diferenca": 0.0,
    "jul_inef_liq": 0.0,
    "ago_inef_trib": 0.0,
    "ago_diferenca": 0.0,
    "ago_inef_liq": 0.0,
    "dif_real_acumulada_ar": 0.0,
    "sugestao_diferenca_as": "Sem diferença",
    "status_analista": "Incorporada",
    "status_revisor": "Incorporada",
    "comentarios_analista": "",
    "comentarios_revisor": "",
    "validador_silver": "Validado (OK Rec Liq | OK Inef Tribut | OK Despesa)"
  },
  {
    "linha": 10,
    "competencia": "08/2026",
    "responsavel": "Incorporada",
    "cruzamento": "TBRA x FIBR",
    "jul_inef_trib": -9636061.57,
    "jul_diferenca": 6763484.66,
    "jul_inef_liq": -2872576.91,
    "ago_inef_trib": 0.0,
    "ago_diferenca": 0.0,
    "ago_inef_liq": 0.0,
    "dif_real_acumulada_ar": 0.0,
    "sugestao_diferenca_as": "Sem diferença",
    "status_analista": "Incorporada",
    "status_revisor": "Incorporada",
    "comentarios_analista": "",
    "comentarios_revisor": "",
    "validador_silver": "Validado (OK Rec Liq | OK Inef Tribut | OK Despesa)"
  },
  {
    "linha": 11,
    "competencia": "08/2026",
    "responsavel": "Thais",
    "cruzamento": "TBRA x I2GO",
    "jul_inef_trib": -182120.07,
    "jul_diferenca": 568874.43,
    "jul_inef_liq": 386754.36,
    "ago_inef_trib": -276513.02,
    "ago_diferenca": -522605.87,
    "ago_inef_liq": -799118.89,
    "dif_real_acumulada_ar": 46268.56,
    "sugestao_diferenca_as": "Receita Bruta maior que Despesa",
    "status_analista": "Enviado para reporting",
    "status_revisor": "Ok para envio",
    "comentarios_analista": "",
    "comentarios_revisor": "",
    "validador_silver": "Validado (OK Rec Liq | OK Inef Tribut | OK Despesa)"
  },
  {
    "linha": 12,
    "competencia": "08/2026",
    "responsavel": "Thais",
    "cruzamento": "VSS x I2GO",
    "jul_inef_trib": 0.0,
    "jul_diferenca": 0.0,
    "jul_inef_liq": 0.0,
    "ago_inef_trib": 0.0,
    "ago_diferenca": 0.0,
    "ago_inef_liq": 0.0,
    "dif_real_acumulada_ar": 0.0,
    "sugestao_diferenca_as": "Sem diferença",
    "status_analista": "Enviado para reporting",
    "status_revisor": "Ok para envio",
    "comentarios_analista": "",
    "comentarios_revisor": "",
    "validador_silver": "Validado (OK Rec Liq | OK Inef Tribut | OK Despesa)"
  },
  {
    "linha": 13,
    "competencia": "08/2026",
    "responsavel": "Mayara",
    "cruzamento": "TBRA x ITIS",
    "jul_inef_trib": -2066610.79,
    "jul_diferenca": -2329361.23,
    "jul_inef_liq": -4395972.02,
    "ago_inef_trib": -3006095.79,
    "ago_diferenca": 9570296.94,
    "ago_inef_liq": 6564201.15,
    "dif_real_acumulada_ar": 7240935.71,
    "sugestao_diferenca_as": "Receita Bruta maior que Despesa",
    "status_analista": "Enviado para reporting",
    "status_revisor": "Ok para envio",
    "comentarios_analista": "A diferença de R$ 9,5MM refere-se principalmente pelo valor do lucro não realizado de R$ 8,3MM, que até o mês anterior estava mascarado por ajustes de provisões e diferimentos",
    "comentarios_revisor": "Deixar no radar os ajustes que foram feitos pelas áreas de negócios caso tenha algum impacto",
    "validador_silver": "Validado (OK Rec Liq | OK Inef Tribut | OK Despesa)"
  }
]

df_res = spark.createDataFrame(DADOS_RESULTADO)
df_res.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(
    f"`{catalogo_atual}`.silver.painel_eliminacao_resultado"
)

display(spark.table(f"`{catalogo_atual}`.silver.painel_eliminacao_resultado").orderBy("linha"))

# COMMAND ----------

# MAGIC %md
# MAGIC ## 4. Filtros Inteligentes e Atualização On-line de Status e Comentários (`MERGE INTO`)
# MAGIC Utilize os seletores no topo do notebook para filtrar ou atualizar o status/comentário de qualquer empresa em tempo real.

# COMMAND ----------

dbutils.widgets.dropdown("1_Responsavel", "Todos", ["Todos", "Beatriz", "Cibele", "Mayara", "Thais", "Incorporada", "Z_Sem Movimento"])
dbutils.widgets.dropdown("2_Status_Analista", "Recebido da ACT", [
    "Sem movimento", "Recebido da ACT", "Em análise", "Devolvida para ACT",
    "Ok para revisão", "Enviado para reporting", "Incorporada"
])
dbutils.widgets.dropdown("3_Status_Revisor", "Ok para envio", [
    "Sem movimento", "Aguardando retorno dos pontos", "Ok para envio", "Incorporada"
])
dbutils.widgets.text("4_Cruzamento_Atualizar", "", "Cruzamento p/ Atualizar (ex: TBRA x ITIS)")
dbutils.widgets.text("5_Comentario_Analista", "", "Novo Comentário (Analista)")

resp_filtro = dbutils.widgets.get("1_Responsavel")
cruzamento_alvo = dbutils.widgets.get("4_Cruzamento_Atualizar").strip()
novo_status_ana = dbutils.widgets.get("2_Status_Analista")
novo_status_rev = dbutils.widgets.get("3_Status_Revisor")
novo_comentario = dbutils.widgets.get("5_Comentario_Analista").strip()

if cruzamento_alvo:
    comentario_sql = f"'{novo_comentario}'" if novo_comentario else "comentarios_analista"
    spark.sql(f"""
        UPDATE `{catalogo_atual}`.silver.painel_eliminacao_patrimonial
        SET status_analista = '{novo_status_ana}',
            status_revisor = '{novo_status_rev}',
            comentarios_analista = {comentario_sql}
        WHERE UPPER(cruzamento) = UPPER('{cruzamento_alvo}')
    """)
    print(f"Cruzamento '{cruzamento_alvo}' atualizado com sucesso no Delta Lake!")

query_filtro = f"SELECT * FROM `{catalogo_atual}`.silver.painel_eliminacao_patrimonial"
if resp_filtro != "Todos":
    query_filtro += f" WHERE responsavel = '{resp_filtro}'"
query_filtro += " ORDER BY ABS(dif_liquida_atual) DESC"

display(spark.sql(query_filtro))
