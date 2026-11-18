"""
Databricks App Autocontido (Arquivo Único: app.py)
Painel de Controle Intercompany — Fase 2:
  - Item 7: Eliminação Patrimonial (Abas Elimináveis, Sum e Temas Principais)
  - Item 8: Eliminação de Resultado & Validador Silver
  - Item 9: Composições Gerais e Elimináveis — Patrimonial (Quadro Sintético e 4 Abas Silver)
Paleta oficial extraída do Documento Funcional (#5A189A, #2B0A4E, #C7A6E8, #6E6E6E, #FFFFFF).
"""

from __future__ import annotations
import json
import streamlit as st

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

DADOS_INICIAIS_PATRIMONIAL = {'eliminaveis': [{'linha': 5,
                  'competencia': '08/2026',
                  'responsavel': 'Beatriz',
                  'cruzamento': 'ITIS x TGLOG',
                  'ativo_1': 0.0,
                  'passivo_2': -17261.71,
                  'ativo_3': 207.44,
                  'passivo_4': 0.0,
                  'dif_bruta_1_4': 0.0,
                  'dif_bruta_2_3': -17054.27,
                  'dif_liquida_atual': -17054.27,
                  'dif_liquida_anterior': -38.51,
                  'var_horiz_pct': 441.853025,
                  'comp_final_rede': '',
                  'versao_resultado': '',
                  'versao_patrimonio': '',
                  'status_analista': 'Enviado para reporting',
                  'status_revisor': 'Ok para envio',
                  'comentarios_revisor': '',
                  'comentarios_analista': 'Entrou um valor de 17K de despesas operacionais na '
                                          'ITIS, que não foi registrado na TGLOG, será tratado no '
                                          'decorrer do mês.'},
                 {'linha': 6,
                  'competencia': '08/2026',
                  'responsavel': 'Beatriz',
                  'cruzamento': 'TBRA x POP',
                  'ativo_1': 358617.87,
                  'passivo_2': -490491.70999999996,
                  'ativo_3': 461386.94999999995,
                  'passivo_4': -335505.62,
                  'dif_bruta_1_4': 23112.25,
                  'dif_bruta_2_3': -29104.76,
                  'dif_liquida_atual': -5992.51,
                  'dif_liquida_anterior': -18359.96,
                  'var_horiz_pct': -0.67361,
                  'comp_final_rede': 'Sim',
                  'versao_resultado': 'V0',
                  'versao_patrimonio': 'V0',
                  'status_analista': 'Enviado para reporting',
                  'status_revisor': 'Ok para envio',
                  'comentarios_revisor': 'Bia analisar a conciliação no detalhe durante o mês para '
                                         'regularizar essa diferença.',
                  'comentarios_analista': ''},
                 {'linha': 7,
                  'competencia': '08/2026',
                  'responsavel': 'Beatriz',
                  'cruzamento': 'TBRA x RECICLA V',
                  'ativo_1': 875314.2599999999,
                  'passivo_2': 0.0,
                  'ativo_3': 0.0,
                  'passivo_4': -1232711.86,
                  'dif_bruta_1_4': -357397.6,
                  'dif_bruta_2_3': 0.0,
                  'dif_liquida_atual': -357397.6,
                  'dif_liquida_anterior': -283586.84,
                  'var_horiz_pct': 0.260276,
                  'comp_final_rede': '',
                  'versao_resultado': '',
                  'versao_patrimonio': '',
                  'status_analista': 'Enviado para reporting',
                  'status_revisor': 'Ok para envio',
                  'comentarios_revisor': 'Bia analisar a conciliação no detalhe durante o mês para '
                                         'regularizar essa diferença.',
                  'comentarios_analista': ''},
                 {'linha': 8,
                  'competencia': '08/2026',
                  'responsavel': 'Beatriz',
                  'cruzamento': 'TGLOG x CLOUD',
                  'ativo_1': 0.0,
                  'passivo_2': 0.0,
                  'ativo_3': 0.0,
                  'passivo_4': 0.0,
                  'dif_bruta_1_4': 0.0,
                  'dif_bruta_2_3': 0.0,
                  'dif_liquida_atual': 0.0,
                  'dif_liquida_anterior': 0.0,
                  'var_horiz_pct': None,
                  'comp_final_rede': '',
                  'versao_resultado': '',
                  'versao_patrimonio': '',
                  'status_analista': 'Sem movimento',
                  'status_revisor': 'Sem movimento',
                  'comentarios_revisor': '',
                  'comentarios_analista': ''},
                 {'linha': 9,
                  'competencia': '08/2026',
                  'responsavel': 'Incorporada',
                  'cruzamento': 'TGLOG x FIBR',
                  'ativo_1': 0.0,
                  'passivo_2': 0.0,
                  'ativo_3': 0.0,
                  'passivo_4': 0.0,
                  'dif_bruta_1_4': 0.0,
                  'dif_bruta_2_3': 0.0,
                  'dif_liquida_atual': 0.0,
                  'dif_liquida_anterior': 0.0,
                  'var_horiz_pct': None,
                  'comp_final_rede': '',
                  'versao_resultado': '',
                  'versao_patrimonio': '',
                  'status_analista': 'Incorporada',
                  'status_revisor': 'Incorporada',
                  'comentarios_revisor': '',
                  'comentarios_analista': ''},
                 {'linha': 10,
                  'competencia': '08/2026',
                  'responsavel': 'Thais',
                  'cruzamento': 'ITIS x CLOUD',
                  'ativo_1': -3792912.41,
                  'passivo_2': 9607611.46,
                  'ativo_3': -5435502.290000001,
                  'passivo_4': -701523.55,
                  'dif_bruta_1_4': -4494435.96,
                  'dif_bruta_2_3': 4172109.17,
                  'dif_liquida_atual': -322326.79,
                  'dif_liquida_anterior': 25325.61,
                  'var_horiz_pct': -13.727306,
                  'comp_final_rede': '',
                  'versao_resultado': '',
                  'versao_patrimonio': '',
                  'status_analista': 'Enviado para reporting',
                  'status_revisor': 'Ok para envio',
                  'comentarios_revisor': '',
                  'comentarios_analista': 'A diferença refere-se provisão 1MM + 990K de '
                                          'diferimento, compensado pelo  lucro na venda de '
                                          'mercadoria 1.7MM'},
                 {'linha': 11,
                  'competencia': '08/2026',
                  'responsavel': 'Mayara',
                  'cruzamento': 'ITIS x TERRA',
                  'ativo_1': 159501.27000000002,
                  'passivo_2': 0.0,
                  'ativo_3': 0.0,
                  'passivo_4': -166442.56,
                  'dif_bruta_1_4': -6941.29,
                  'dif_bruta_2_3': 0.0,
                  'dif_liquida_atual': -6941.29,
                  'dif_liquida_anterior': -4758.36,
                  'var_horiz_pct': 0.458757,
                  'comp_final_rede': '',
                  'versao_resultado': '',
                  'versao_patrimonio': '',
                  'status_analista': 'Enviado para reporting',
                  'status_revisor': 'Ok para envio',
                  'comentarios_revisor': '',
                  'comentarios_analista': ''},
                 {'linha': 12,
                  'competencia': '08/2026',
                  'responsavel': 'Mayara',
                  'cruzamento': 'TBRA x ITIS',
                  'ativo_1': 99731615.14000002,
                  'passivo_2': -119690699.07000001,
                  'ativo_3': 85712089.69000001,
                  'passivo_4': -51617218.32,
                  'dif_bruta_1_4': 48114396.82,
                  'dif_bruta_2_3': -33978609.38,
                  'dif_liquida_atual': 14135787.44,
                  'dif_liquida_anterior': 5897146.92,
                  'var_horiz_pct': 1.397055,
                  'comp_final_rede': 'Sim',
                  'versao_resultado': 'V0',
                  'versao_patrimonio': 'V0',
                  'status_analista': 'Enviado para reporting',
                  'status_revisor': 'Ok para envio',
                  'comentarios_revisor': '',
                  'comentarios_analista': 'A principal diferença refere-se 16,1MM de lucro não '
                                          'realizado, compensado pelo valor de 3MM de diferenças '
                                          'entre as provisoes e entradas de notas fiscais que '
                                          'serao conciliados durante o mês para regularização das '
                                          'diferenças, entre outros temas.'},
                 {'linha': 13,
                  'competencia': '08/2026',
                  'responsavel': 'Cibele',
                  'cruzamento': 'TBRA x TERRA',
                  'ativo_1': 5326521.699999999,
                  'passivo_2': -2210242.86,
                  'ativo_3': 3479078.2899999996,
                  'passivo_4': -7030899.65,
                  'dif_bruta_1_4': -1704377.95,
                  'dif_bruta_2_3': 1268835.43,
                  'dif_liquida_atual': -435542.52,
                  'dif_liquida_anterior': -463818.72,
                  'var_horiz_pct': -0.060964,
                  'comp_final_rede': '',
                  'versao_resultado': '',
                  'versao_patrimonio': '',
                  'status_analista': 'Enviado para reporting',
                  'status_revisor': 'Ok para envio',
                  'comentarios_revisor': '',
                  'comentarios_analista': 'Referente a provisão de rateio de despesa tributária '
                                          'onde o valor da contra parte está a maior'},
                 {'linha': 14,
                  'competencia': '08/2026',
                  'responsavel': 'Cibele',
                  'cruzamento': 'CLOUD x VSCD',
                  'ativo_1': 1590002.93,
                  'passivo_2': 0.0,
                  'ativo_3': 0.0,
                  'passivo_4': -1770640.36,
                  'dif_bruta_1_4': -180637.43,
                  'dif_bruta_2_3': 0.0,
                  'dif_liquida_atual': -180637.43,
                  'dif_liquida_anterior': -1618549.78,
                  'var_horiz_pct': -0.888396,
                  'comp_final_rede': '',
                  'versao_resultado': '',
                  'versao_patrimonio': '',
                  'status_analista': 'Enviado para reporting',
                  'status_revisor': 'Ok para envio',
                  'comentarios_revisor': '',
                  'comentarios_analista': 'Refere-se a regularização do A Faturar da Azure na '
                                          'Cloud'},
                 {'linha': 15,
                  'competencia': '08/2026',
                  'responsavel': 'Incorporada',
                  'cruzamento': 'CLOUD x CYBR',
                  'ativo_1': 0.0,
                  'passivo_2': 0.0,
                  'ativo_3': 0.0,
                  'passivo_4': 0.0,
                  'dif_bruta_1_4': 0.0,
                  'dif_bruta_2_3': 0.0,
                  'dif_liquida_atual': 0.0,
                  'dif_liquida_anterior': 0.0,
                  'var_horiz_pct': None,
                  'comp_final_rede': '',
                  'versao_resultado': '',
                  'versao_patrimonio': '',
                  'status_analista': 'Incorporada',
                  'status_revisor': 'Incorporada',
                  'comentarios_revisor': '',
                  'comentarios_analista': ''},
                 {'linha': 16,
                  'competencia': '08/2026',
                  'responsavel': 'Incorporada',
                  'cruzamento': 'ITIS X CYBR',
                  'ativo_1': 0.0,
                  'passivo_2': 0.0,
                  'ativo_3': 0.0,
                  'passivo_4': 0.0,
                  'dif_bruta_1_4': 0.0,
                  'dif_bruta_2_3': 0.0,
                  'dif_liquida_atual': 0.0,
                  'dif_liquida_anterior': 0.0,
                  'var_horiz_pct': None,
                  'comp_final_rede': '',
                  'versao_resultado': '',
                  'versao_patrimonio': '',
                  'status_analista': 'Incorporada',
                  'status_revisor': 'Incorporada',
                  'comentarios_revisor': '',
                  'comentarios_analista': ''},
                 {'linha': 17,
                  'competencia': '08/2026',
                  'responsavel': 'Thais',
                  'cruzamento': 'TBRA x CLOUD',
                  'ativo_1': 88179837.49999999,
                  'passivo_2': -90640811.25999999,
                  'ativo_3': 92401182.18999998,
                  'passivo_4': -89869363.24,
                  'dif_bruta_1_4': -1689525.74,
                  'dif_bruta_2_3': 1760370.93,
                  'dif_liquida_atual': 70845.19,
                  'dif_liquida_anterior': 447708.75,
                  'var_horiz_pct': -0.841761,
                  'comp_final_rede': '',
                  'versao_resultado': '',
                  'versao_patrimonio': '',
                  'status_analista': 'Enviado para reporting',
                  'status_revisor': 'Ok para envio',
                  'comentarios_revisor': '',
                  'comentarios_analista': ''},
                 {'linha': 18,
                  'competencia': '08/2026',
                  'responsavel': 'Cibele',
                  'cruzamento': 'TBRA x VALE (VSS)',
                  'ativo_1': 436832.62,
                  'passivo_2': -6095807.05,
                  'ativo_3': 6095807.05,
                  'passivo_4': -287182.82,
                  'dif_bruta_1_4': 149649.8,
                  'dif_bruta_2_3': 0.0,
                  'dif_liquida_atual': 149649.8,
                  'dif_liquida_anterior': 281164.13,
                  'var_horiz_pct': -0.467749,
                  'comp_final_rede': '',
                  'versao_resultado': '',
                  'versao_patrimonio': '',
                  'status_analista': 'Enviado para reporting',
                  'status_revisor': 'Ok para envio',
                  'comentarios_revisor': '',
                  'comentarios_analista': 'Refere-se a provisão de Reembolso de Licen. Microsoft '
                                          'que não foi considerado pela contraparte'},
                 {'linha': 19,
                  'competencia': '08/2026',
                  'responsavel': 'Cibele',
                  'cruzamento': 'TBRA x VSCD (VPAY SCD)',
                  'ativo_1': 1769150.69,
                  'passivo_2': -729238.63,
                  'ativo_3': 0.0,
                  'passivo_4': -1692567.8499999999,
                  'dif_bruta_1_4': 76582.84,
                  'dif_bruta_2_3': -729238.63,
                  'dif_liquida_atual': -652655.79,
                  'dif_liquida_anterior': -1785213.89,
                  'var_horiz_pct': -0.63441,
                  'comp_final_rede': '',
                  'versao_resultado': '',
                  'versao_patrimonio': '',
                  'status_analista': 'Enviado para reporting',
                  'status_revisor': 'Ok para envio',
                  'comentarios_revisor': '',
                  'comentarios_analista': 'Refere-se a regularização do A Faturar da Azure na '
                                          'contraparte'},
                 {'linha': 20,
                  'competencia': '08/2026',
                  'responsavel': 'Thais',
                  'cruzamento': 'TERRA x CLOUD',
                  'ativo_1': 0.0,
                  'passivo_2': -907303.49,
                  'ativo_3': 947469.8,
                  'passivo_4': 0.0,
                  'dif_bruta_1_4': 0.0,
                  'dif_bruta_2_3': 40166.31,
                  'dif_liquida_atual': 40166.31,
                  'dif_liquida_anterior': 236739.48,
                  'var_horiz_pct': -0.830335,
                  'comp_final_rede': '',
                  'versao_resultado': '',
                  'versao_patrimonio': '',
                  'status_analista': 'Enviado para reporting',
                  'status_revisor': 'Ok para envio',
                  'comentarios_revisor': '',
                  'comentarios_analista': ''},
                 {'linha': 21,
                  'competencia': '08/2026',
                  'responsavel': 'Beatriz',
                  'cruzamento': 'TERRA x VALE (VSS)',
                  'ativo_1': 0.0,
                  'passivo_2': -7.58,
                  'ativo_3': 0.0,
                  'passivo_4': 0.0,
                  'dif_bruta_1_4': 0.0,
                  'dif_bruta_2_3': -7.58,
                  'dif_liquida_atual': -7.58,
                  'dif_liquida_anterior': -15.16,
                  'var_horiz_pct': -0.5,
                  'comp_final_rede': '',
                  'versao_resultado': '',
                  'versao_patrimonio': '',
                  'status_analista': 'Enviado para reporting',
                  'status_revisor': 'Ok para envio',
                  'comentarios_revisor': '',
                  'comentarios_analista': ''},
                 {'linha': 22,
                  'competencia': '08/2026',
                  'responsavel': 'Beatriz',
                  'cruzamento': 'VIMO (VPAY FUNDO) x VSCD',
                  'ativo_1': 0.0,
                  'passivo_2': -420910.25,
                  'ativo_3': 420910.25,
                  'passivo_4': 0.0,
                  'dif_bruta_1_4': 0.0,
                  'dif_bruta_2_3': 0.0,
                  'dif_liquida_atual': 0.0,
                  'dif_liquida_anterior': 0.0,
                  'var_horiz_pct': None,
                  'comp_final_rede': '',
                  'versao_resultado': '',
                  'versao_patrimonio': '',
                  'status_analista': 'Enviado para reporting',
                  'status_revisor': 'Ok para envio',
                  'comentarios_revisor': '',
                  'comentarios_analista': ''},
                 {'linha': 23,
                  'competencia': '08/2026',
                  'responsavel': 'Beatriz',
                  'cruzamento': 'VSCD x VPY3',
                  'ativo_1': 10962.92,
                  'passivo_2': 0.0,
                  'ativo_3': 0.0,
                  'passivo_4': -10962.92,
                  'dif_bruta_1_4': 0.0,
                  'dif_bruta_2_3': 0.0,
                  'dif_liquida_atual': 0.0,
                  'dif_liquida_anterior': 0.0,
                  'var_horiz_pct': None,
                  'comp_final_rede': '',
                  'versao_resultado': '',
                  'versao_patrimonio': '',
                  'status_analista': 'Enviado para reporting',
                  'status_revisor': 'Ok para envio',
                  'comentarios_revisor': '',
                  'comentarios_analista': ''},
                 {'linha': 24,
                  'competencia': '08/2026',
                  'responsavel': 'Incorporada',
                  'cruzamento': 'CLOUD x FIBR',
                  'ativo_1': 0.0,
                  'passivo_2': 0.0,
                  'ativo_3': 0.0,
                  'passivo_4': 0.0,
                  'dif_bruta_1_4': 0.0,
                  'dif_bruta_2_3': 0.0,
                  'dif_liquida_atual': 0.0,
                  'dif_liquida_anterior': -507374.44,
                  'var_horiz_pct': -1.0,
                  'comp_final_rede': '',
                  'versao_resultado': '',
                  'versao_patrimonio': '',
                  'status_analista': 'Incorporada',
                  'status_revisor': 'Incorporada',
                  'comentarios_revisor': '',
                  'comentarios_analista': ''},
                 {'linha': 25,
                  'competencia': '08/2026',
                  'responsavel': 'Incorporada',
                  'cruzamento': 'TBRA X CYBR',
                  'ativo_1': 0.0,
                  'passivo_2': 0.0,
                  'ativo_3': 0.0,
                  'passivo_4': 0.0,
                  'dif_bruta_1_4': 0.0,
                  'dif_bruta_2_3': 0.0,
                  'dif_liquida_atual': 0.0,
                  'dif_liquida_anterior': 0.0,
                  'var_horiz_pct': None,
                  'comp_final_rede': '',
                  'versao_resultado': '',
                  'versao_patrimonio': '',
                  'status_analista': 'Incorporada',
                  'status_revisor': 'Incorporada',
                  'comentarios_revisor': '',
                  'comentarios_analista': ''},
                 {'linha': 26,
                  'competencia': '08/2026',
                  'responsavel': 'Incorporada',
                  'cruzamento': 'TBRA x FIBR',
                  'ativo_1': 0.0,
                  'passivo_2': 0.0,
                  'ativo_3': 0.0,
                  'passivo_4': 0.0,
                  'dif_bruta_1_4': 0.0,
                  'dif_bruta_2_3': 0.0,
                  'dif_liquida_atual': 0.0,
                  'dif_liquida_anterior': -2935327.32,
                  'var_horiz_pct': -1.0,
                  'comp_final_rede': '',
                  'versao_resultado': '',
                  'versao_patrimonio': '',
                  'status_analista': 'Incorporada',
                  'status_revisor': 'Incorporada',
                  'comentarios_revisor': '',
                  'comentarios_analista': ''},
                 {'linha': 27,
                  'competencia': '08/2026',
                  'responsavel': 'Thais',
                  'cruzamento': 'TBRA X I2GO',
                  'ativo_1': 19180461.7,
                  'passivo_2': -4319830.91,
                  'ativo_3': 1165497.36,
                  'passivo_4': -15228234.24,
                  'dif_bruta_1_4': 3952227.46,
                  'dif_bruta_2_3': -3154333.55,
                  'dif_liquida_atual': 797893.91,
                  'dif_liquida_anterior': 1056334.18,
                  'var_horiz_pct': -0.244658,
                  'comp_final_rede': '',
                  'versao_resultado': '',
                  'versao_patrimonio': '',
                  'status_analista': 'Enviado para reporting',
                  'status_revisor': 'Ok para envio',
                  'comentarios_revisor': '',
                  'comentarios_analista': 'Temos registrado em ambos os lados 15MM de '
                                          'adiantamento'},
                 {'linha': 28,
                  'competencia': '08/2026',
                  'responsavel': 'Cibele',
                  'cruzamento': 'TBRA x TGLOG',
                  'ativo_1': 4964126.2700000005,
                  'passivo_2': -25961222.889999997,
                  'ativo_3': 26062166.310000002,
                  'passivo_4': -4851073.12,
                  'dif_bruta_1_4': 113053.15,
                  'dif_bruta_2_3': 100943.42,
                  'dif_liquida_atual': 213996.57,
                  'dif_liquida_anterior': 130893.77,
                  'var_horiz_pct': 0.634887,
                  'comp_final_rede': '',
                  'versao_resultado': '',
                  'versao_patrimonio': '',
                  'status_analista': 'Enviado para reporting',
                  'status_revisor': 'Ok para envio',
                  'comentarios_revisor': '',
                  'comentarios_analista': 'A diferença refere-se a provisão trabalhista '
                                          'considerada a menor na contraparte'},
                 {'linha': 29,
                  'competencia': '08/2026',
                  'responsavel': 'Incorporada',
                  'cruzamento': 'TGLOG  X CYBR',
                  'ativo_1': 0.0,
                  'passivo_2': 0.0,
                  'ativo_3': 0.0,
                  'passivo_4': 0.0,
                  'dif_bruta_1_4': 0.0,
                  'dif_bruta_2_3': 0.0,
                  'dif_liquida_atual': 0.0,
                  'dif_liquida_anterior': 0.0,
                  'var_horiz_pct': None,
                  'comp_final_rede': '',
                  'versao_resultado': '',
                  'versao_patrimonio': '',
                  'status_analista': 'Incorporada',
                  'status_revisor': 'Incorporada',
                  'comentarios_revisor': '',
                  'comentarios_analista': ''},
                 {'linha': 30,
                  'competencia': '08/2026',
                  'responsavel': 'Thais',
                  'cruzamento': 'VSS X I2GO',
                  'ativo_1': 0.0,
                  'passivo_2': 0.0,
                  'ativo_3': 0.0,
                  'passivo_4': 0.0,
                  'dif_bruta_1_4': 0.0,
                  'dif_bruta_2_3': 0.0,
                  'dif_liquida_atual': 0.0,
                  'dif_liquida_anterior': 0.0,
                  'var_horiz_pct': None,
                  'comp_final_rede': '',
                  'versao_resultado': '',
                  'versao_patrimonio': '',
                  'status_analista': 'Sem movimento',
                  'status_revisor': 'Sem movimento',
                  'comentarios_revisor': '',
                  'comentarios_analista': ''},
                 {'linha': 31,
                  'competencia': '08/2026',
                  'responsavel': 'Z_Sem Movimento',
                  'cruzamento': 'TBRA x VIMO (VPAY FUNDO)',
                  'ativo_1': 0.0,
                  'passivo_2': 0.0,
                  'ativo_3': 0.0,
                  'passivo_4': 0.0,
                  'dif_bruta_1_4': 0.0,
                  'dif_bruta_2_3': 0.0,
                  'dif_liquida_atual': 0.0,
                  'dif_liquida_anterior': 0.0,
                  'var_horiz_pct': None,
                  'comp_final_rede': '',
                  'versao_resultado': '',
                  'versao_patrimonio': '',
                  'status_analista': 'Sem movimento',
                  'status_revisor': 'Sem movimento',
                  'comentarios_revisor': '',
                  'comentarios_analista': ''},
                 {'linha': 32,
                  'competencia': '08/2026',
                  'responsavel': 'Z_Sem Movimento',
                  'cruzamento': 'TBRA x VPAY (VPAY HOLDING)',
                  'ativo_1': 0.0,
                  'passivo_2': 0.0,
                  'ativo_3': 0.0,
                  'passivo_4': 0.0,
                  'dif_bruta_1_4': 0.0,
                  'dif_bruta_2_3': 0.0,
                  'dif_liquida_atual': 0.0,
                  'dif_liquida_anterior': 0.0,
                  'var_horiz_pct': None,
                  'comp_final_rede': '',
                  'versao_resultado': '',
                  'versao_patrimonio': '',
                  'status_analista': 'Sem movimento',
                  'status_revisor': 'Sem movimento',
                  'comentarios_revisor': '',
                  'comentarios_analista': ''},
                 {'linha': 33,
                  'competencia': '08/2026',
                  'responsavel': 'Z_Sem Movimento',
                  'cruzamento': 'TBRA x VVENTURES',
                  'ativo_1': 0.0,
                  'passivo_2': 0.0,
                  'ativo_3': 0.0,
                  'passivo_4': 0.0,
                  'dif_bruta_1_4': 0.0,
                  'dif_bruta_2_3': 0.0,
                  'dif_liquida_atual': 0.0,
                  'dif_liquida_anterior': 0.0,
                  'var_horiz_pct': None,
                  'comp_final_rede': '',
                  'versao_resultado': '',
                  'versao_patrimonio': '',
                  'status_analista': 'Sem movimento',
                  'status_revisor': 'Sem movimento',
                  'comentarios_revisor': '',
                  'comentarios_analista': ''}],
 'sum': [{'rotulo_linha': 'Beatriz',
          'contagem_cruzamento': 6,
          'soma_mes_atual': 84925.44,
          'soma_mes_anterior': 373469.73},
         {'rotulo_linha': 'Mayara',
          'contagem_cruzamento': 3,
          'soma_mes_atual': 12152341.54,
          'soma_mes_anterior': 15649399.27},
         {'rotulo_linha': 'Sem Movimento',
          'contagem_cruzamento': 3,
          'soma_mes_atual': 0.0,
          'soma_mes_anterior': 0.0},
         {'rotulo_linha': 'Thais',
          'contagem_cruzamento': 6,
          'soma_mes_atual': 856671.47,
          'soma_mes_anterior': -2564477.85},
         {'rotulo_linha': 'Rebecca',
          'contagem_cruzamento': 9,
          'soma_mes_atual': -2233126.98,
          'soma_mes_anterior': 1192549.75},
         {'rotulo_linha': 'Total Geral',
          'contagem_cruzamento': 27,
          'soma_mes_atual': 10860811.47,
          'soma_mes_anterior': 14650940.9}],
 'temas_principais': [{'cruzamento': 'CLOUD x FIBR',
                       'temas_entre_empresas': '',
                       'ativo_passivo_origem': '',
                       'ativo_passivo_contraparte': ''},
                      {'cruzamento': 'CLOUD x VSCD',
                       'temas_entre_empresas': '',
                       'ativo_passivo_origem': '',
                       'ativo_passivo_contraparte': ''},
                      {'cruzamento': 'CYBR x CLOUD',
                       'temas_entre_empresas': '',
                       'ativo_passivo_origem': '',
                       'ativo_passivo_contraparte': ''},
                      {'cruzamento': 'ITIS x CLOUD',
                       'temas_entre_empresas': '',
                       'ativo_passivo_origem': '',
                       'ativo_passivo_contraparte': ''},
                      {'cruzamento': 'ITIS X CYBR',
                       'temas_entre_empresas': '',
                       'ativo_passivo_origem': '',
                       'ativo_passivo_contraparte': ''},
                      {'cruzamento': 'ITIS x TGLOG',
                       'temas_entre_empresas': '',
                       'ativo_passivo_origem': '',
                       'ativo_passivo_contraparte': ''},
                      {'cruzamento': 'TBRA x CLOUD',
                       'temas_entre_empresas': '',
                       'ativo_passivo_origem': '',
                       'ativo_passivo_contraparte': ''},
                      {'cruzamento': 'TBRA X CYBR',
                       'temas_entre_empresas': '',
                       'ativo_passivo_origem': '',
                       'ativo_passivo_contraparte': ''},
                      {'cruzamento': 'TBRA x FIBR',
                       'temas_entre_empresas': '',
                       'ativo_passivo_origem': '',
                       'ativo_passivo_contraparte': ''},
                      {'cruzamento': 'TBRA X I2GO',
                       'temas_entre_empresas': '',
                       'ativo_passivo_origem': '',
                       'ativo_passivo_contraparte': ''},
                      {'cruzamento': 'TBRA x ITIS',
                       'temas_entre_empresas': '',
                       'ativo_passivo_origem': '',
                       'ativo_passivo_contraparte': ''},
                      {'cruzamento': 'TBRA x POP',
                       'temas_entre_empresas': '',
                       'ativo_passivo_origem': '',
                       'ativo_passivo_contraparte': ''},
                      {'cruzamento': 'TBRA x RECICLA V',
                       'temas_entre_empresas': '',
                       'ativo_passivo_origem': '',
                       'ativo_passivo_contraparte': ''},
                      {'cruzamento': 'TBRA x TERRA',
                       'temas_entre_empresas': '',
                       'ativo_passivo_origem': '',
                       'ativo_passivo_contraparte': ''},
                      {'cruzamento': 'TBRA x TGLOG',
                       'temas_entre_empresas': '',
                       'ativo_passivo_origem': '',
                       'ativo_passivo_contraparte': ''},
                      {'cruzamento': 'TBRA x VALE (VSS)',
                       'temas_entre_empresas': 'Comissão sobre venda de assinaturas de saúde, '
                                               'faturado pela VSS. Aluguel de imóvel, faturado '
                                               'pela TBRA. Rateio de salários, faturado pela TBRA.',
                       'ativo_passivo_origem': '',
                       'ativo_passivo_contraparte': ''},
                      {'cruzamento': 'TBRA x VIMO (VPAY FUNDO)',
                       'temas_entre_empresas': 'Sem movimento',
                       'ativo_passivo_origem': '',
                       'ativo_passivo_contraparte': ''},
                      {'cruzamento': 'TBRA x VPAY (VPAY HOLDING)',
                       'temas_entre_empresas': 'Sem movimento',
                       'ativo_passivo_origem': '',
                       'ativo_passivo_contraparte': ''},
                      {'cruzamento': 'TBRA x VSCD (VPAY SCD)',
                       'temas_entre_empresas': 'Rateio de Salários, prestados pela TBRA.',
                       'ativo_passivo_origem': '',
                       'ativo_passivo_contraparte': ''},
                      {'cruzamento': 'TBRA x VVENTURES',
                       'temas_entre_empresas': 'Sem movimento',
                       'ativo_passivo_origem': '',
                       'ativo_passivo_contraparte': ''},
                      {'cruzamento': 'TERRA x CLOUD',
                       'temas_entre_empresas': '',
                       'ativo_passivo_origem': '',
                       'ativo_passivo_contraparte': ''},
                      {'cruzamento': 'TERRA X ITIS',
                       'temas_entre_empresas': '',
                       'ativo_passivo_origem': '',
                       'ativo_passivo_contraparte': ''},
                      {'cruzamento': 'TERRA x VALE SAÚDE',
                       'temas_entre_empresas': 'Comissão sobre venda de assinaturas de saúde, '
                                               'faturado pela VSS.',
                       'ativo_passivo_origem': '',
                       'ativo_passivo_contraparte': ''},
                      {'cruzamento': 'TGLOG  X CYBR',
                       'temas_entre_empresas': '',
                       'ativo_passivo_origem': '',
                       'ativo_passivo_contraparte': ''},
                      {'cruzamento': 'TGLOG x CLOUD',
                       'temas_entre_empresas': '',
                       'ativo_passivo_origem': '',
                       'ativo_passivo_contraparte': ''},
                      {'cruzamento': 'TGLOG x FIBR',
                       'temas_entre_empresas': '',
                       'ativo_passivo_origem': '',
                       'ativo_passivo_contraparte': ''},
                      {'cruzamento': 'VIMO x VSCD',
                       'temas_entre_empresas': 'Prest. Serviços de Cobranças faturado pela VSCD.',
                       'ativo_passivo_origem': '',
                       'ativo_passivo_contraparte': ''}]}

DADOS_INICIAIS_RESULTADO = [{'linha': 1,
  'competencia': '08/2026',
  'responsavel': 'Incorporada',
  'cruzamento': 'CLOUD x FIBR',
  'jul_inef_trib': 0.0,
  'jul_diferenca': -95435.53,
  'jul_inef_liq': -95435.53,
  'ago_inef_trib': 0.0,
  'ago_diferenca': 0.0,
  'ago_inef_liq': 0.0,
  'dif_real_acumulada_ar': -95435.53,
  'sugestao_diferenca_as': 'Despesa maior que Receita Bruta',
  'status_analista': 'Incorporada',
  'status_revisor': 'Incorporada',
  'comentarios_analista': '',
  'comentarios_revisor': '',
  'validador_silver': 'Validado (OK Rec Liq | OK Inef Tribut | OK Despesa)'},
 {'linha': 2,
  'competencia': '08/2026',
  'responsavel': 'Cibele',
  'cruzamento': 'CLOUD x VSCD',
  'jul_inef_trib': 0.0,
  'jul_diferenca': -459196.37,
  'jul_inef_liq': -459196.37,
  'ago_inef_trib': 1508218.85,
  'ago_diferenca': 81784.08,
  'ago_inef_liq': 1590002.93,
  'dif_real_acumulada_ar': 656134.95,
  'sugestao_diferenca_as': 'Receita Bruta maior que Despesa',
  'status_analista': 'Enviado para reporting',
  'status_revisor': 'Ok para envio',
  'comentarios_analista': 'Tratativa dada a Azure',
  'comentarios_revisor': '',
  'validador_silver': 'Validado (OK Rec Liq | OK Inef Tribut | OK Despesa)'},
 {'linha': 3,
  'competencia': '08/2026',
  'responsavel': 'Incorporada',
  'cruzamento': 'CYBR x CLOUD',
  'jul_inef_trib': 0.0,
  'jul_diferenca': 0.0,
  'jul_inef_liq': 0.0,
  'ago_inef_trib': 0.0,
  'ago_diferenca': 0.0,
  'ago_inef_liq': 0.0,
  'dif_real_acumulada_ar': 0.0,
  'sugestao_diferenca_as': 'Sem diferença',
  'status_analista': 'Incorporada',
  'status_revisor': 'Incorporada',
  'comentarios_analista': '',
  'comentarios_revisor': '',
  'validador_silver': 'Validado (OK Rec Liq | OK Inef Tribut | OK Despesa)'},
 {'linha': 4,
  'competencia': '08/2026',
  'responsavel': 'Thais',
  'cruzamento': 'ITIS x CLOUD',
  'jul_inef_trib': -66323.37,
  'jul_diferenca': -26899.27,
  'jul_inef_liq': -93222.64,
  'ago_inef_trib': -58620.06,
  'ago_diferenca': 3578.98,
  'ago_inef_liq': -55041.08,
  'dif_real_acumulada_ar': -857280.03,
  'sugestao_diferenca_as': 'Despesa maior que Receita Bruta',
  'status_analista': 'Enviado para reporting',
  'status_revisor': 'Ok para envio',
  'comentarios_analista': '',
  'comentarios_revisor': '',
  'validador_silver': 'Validado (OK Rec Liq | OK Inef Tribut | OK Despesa)'},
 {'linha': 5,
  'competencia': '08/2026',
  'responsavel': 'Incorporada',
  'cruzamento': 'ITIS X CYBR',
  'jul_inef_trib': 0.0,
  'jul_diferenca': 0.0,
  'jul_inef_liq': 0.0,
  'ago_inef_trib': 0.0,
  'ago_diferenca': 0.0,
  'ago_inef_liq': 0.0,
  'dif_real_acumulada_ar': 0.0,
  'sugestao_diferenca_as': 'Sem diferença',
  'status_analista': 'Incorporada',
  'status_revisor': 'Incorporada',
  'comentarios_analista': '',
  'comentarios_revisor': '',
  'validador_silver': 'Validado (OK Rec Liq | OK Inef Tribut | OK Despesa)'},
 {'linha': 6,
  'competencia': '08/2026',
  'responsavel': 'Mayara',
  'cruzamento': 'ITIS x TERRA',
  'jul_inef_trib': -10857.1,
  'jul_diferenca': 32890.22,
  'jul_inef_liq': 22033.12,
  'ago_inef_trib': -2525.77,
  'ago_diferenca': -2182.92,
  'ago_inef_liq': -4708.69,
  'dif_real_acumulada_ar': 62424.56,
  'sugestao_diferenca_as': 'Receita Bruta maior que Despesa',
  'status_analista': 'Enviado para reporting',
  'status_revisor': 'Ok para envio',
  'comentarios_analista': '',
  'comentarios_revisor': '',
  'validador_silver': 'Validado (OK Rec Liq | OK Inef Tribut | OK Despesa)'},
 {'linha': 7,
  'competencia': '08/2026',
  'responsavel': 'Beatriz',
  'cruzamento': 'ITIS x TGLOG',
  'jul_inef_trib': 0.0,
  'jul_diferenca': -123.58,
  'jul_inef_liq': -123.58,
  'ago_inef_trib': 0.0,
  'ago_diferenca': -123.58,
  'ago_inef_liq': -123.58,
  'dif_real_acumulada_ar': 74510.72,
  'sugestao_diferenca_as': 'Receita Bruta maior que Despesa',
  'status_analista': 'Enviado para reporting',
  'status_revisor': 'Ok para envio',
  'comentarios_analista': '',
  'comentarios_revisor': 'Avaliar do que se trata esse valor tão pequeno para que ele seja '
                         'conciliado ou até mesmo cancelado.',
  'validador_silver': 'Validado (OK Rec Liq | OK Inef Tribut | OK Despesa)'},
 {'linha': 8,
  'competencia': '08/2026',
  'responsavel': 'Thais',
  'cruzamento': 'TBRA x CLOUD',
  'jul_inef_trib': -2467838.26,
  'jul_diferenca': 284225.83,
  'jul_inef_liq': -2183612.43,
  'ago_inef_trib': -2226172.98,
  'ago_diferenca': 828825.93,
  'ago_inef_liq': -1397347.05,
  'dif_real_acumulada_ar': 1113051.76,
  'sugestao_diferenca_as': 'Receita Bruta maior que Despesa',
  'status_analista': 'Enviado para reporting',
  'status_revisor': 'Ok para envio',
  'comentarios_analista': 'A dif refere principalmente a 800k de diferimento',
  'comentarios_revisor': '',
  'validador_silver': 'Validado (OK Rec Liq | OK Inef Tribut | OK Despesa)'},
 {'linha': 9,
  'competencia': '08/2026',
  'responsavel': 'Incorporada',
  'cruzamento': 'TBRA X CYBR',
  'jul_inef_trib': 0.0,
  'jul_diferenca': 0.0,
  'jul_inef_liq': 0.0,
  'ago_inef_trib': 0.0,
  'ago_diferenca': 0.0,
  'ago_inef_liq': 0.0,
  'dif_real_acumulada_ar': 0.0,
  'sugestao_diferenca_as': 'Sem diferença',
  'status_analista': 'Incorporada',
  'status_revisor': 'Incorporada',
  'comentarios_analista': '',
  'comentarios_revisor': '',
  'validador_silver': 'Validado (OK Rec Liq | OK Inef Tribut | OK Despesa)'},
 {'linha': 10,
  'competencia': '08/2026',
  'responsavel': 'Incorporada',
  'cruzamento': 'TBRA x FIBR',
  'jul_inef_trib': -9636061.57,
  'jul_diferenca': 6763484.66,
  'jul_inef_liq': -2872576.91,
  'ago_inef_trib': 0.0,
  'ago_diferenca': 0.0,
  'ago_inef_liq': 0.0,
  'dif_real_acumulada_ar': 0.0,
  'sugestao_diferenca_as': 'Sem diferença',
  'status_analista': 'Incorporada',
  'status_revisor': 'Incorporada',
  'comentarios_analista': '',
  'comentarios_revisor': '',
  'validador_silver': 'Validado (OK Rec Liq | OK Inef Tribut | OK Despesa)'},
 {'linha': 11,
  'competencia': '08/2026',
  'responsavel': 'Thais',
  'cruzamento': 'TBRA x I2GO',
  'jul_inef_trib': -182120.07,
  'jul_diferenca': 568874.43,
  'jul_inef_liq': 386754.36,
  'ago_inef_trib': -276513.02,
  'ago_diferenca': -522605.87,
  'ago_inef_liq': -799118.89,
  'dif_real_acumulada_ar': 46268.56,
  'sugestao_diferenca_as': 'Receita Bruta maior que Despesa',
  'status_analista': 'Enviado para reporting',
  'status_revisor': 'Ok para envio',
  'comentarios_analista': '',
  'comentarios_revisor': '',
  'validador_silver': 'Validado (OK Rec Liq | OK Inef Tribut | OK Despesa)'},
 {'linha': 12,
  'competencia': '08/2026',
  'responsavel': 'Thais',
  'cruzamento': 'VSS x I2GO',
  'jul_inef_trib': 0.0,
  'jul_diferenca': 0.0,
  'jul_inef_liq': 0.0,
  'ago_inef_trib': 0.0,
  'ago_diferenca': 0.0,
  'ago_inef_liq': 0.0,
  'dif_real_acumulada_ar': 0.0,
  'sugestao_diferenca_as': 'Sem diferença',
  'status_analista': 'Enviado para reporting',
  'status_revisor': 'Ok para envio',
  'comentarios_analista': '',
  'comentarios_revisor': '',
  'validador_silver': 'Validado (OK Rec Liq | OK Inef Tribut | OK Despesa)'},
 {'linha': 13,
  'competencia': '08/2026',
  'responsavel': 'Mayara',
  'cruzamento': 'TBRA x ITIS',
  'jul_inef_trib': -2066610.79,
  'jul_diferenca': -2329361.23,
  'jul_inef_liq': -4395972.02,
  'ago_inef_trib': -3006095.79,
  'ago_diferenca': 9570296.94,
  'ago_inef_liq': 6564201.15,
  'dif_real_acumulada_ar': 7240935.71,
  'sugestao_diferenca_as': 'Receita Bruta maior que Despesa',
  'status_analista': 'Enviado para reporting',
  'status_revisor': 'Ok para envio',
  'comentarios_analista': 'A diferença de R$ 9,5MM refere-se principalmente pelo valor do lucro '
                          'não realizado de R$ 8,3MM, que até o mês anterior estava mascarado por '
                          'ajustes de provisões e diferimentos',
  'comentarios_revisor': 'Deixar no radar os ajustes que foram feitos pelas áreas de negócios caso '
                         'tenha algum impacto',
  'validador_silver': 'Validado (OK Rec Liq | OK Inef Tribut | OK Despesa)'}]

DADOS_INICIAIS_ITEM9 = {'eliminacao_x_compfinal': [{'linha': 1,
                             'cruzamento': 'I2GO x TBRA',
                             'empresa_origem': 'I2GO',
                             'empresa_conc': 'TBRA',
                             'conta': '11218928',
                             'valor_comp_elim': 1165497.36,
                             'valor_comp_final': 1165497.36,
                             'diferenca': 0.0,
                             'resultado_analise': 'Sucesso',
                             'comentarios_analista': 'Partida conciliada sem diferença'},
                            {'linha': 2,
                             'cruzamento': 'I2GO x TBRA',
                             'empresa_origem': 'I2GO',
                             'empresa_conc': 'TBRA',
                             'conta': '21191932',
                             'valor_comp_elim': -15228234.24,
                             'valor_comp_final': -15228234.24,
                             'diferenca': 0.0,
                             'resultado_analise': 'Sucesso',
                             'comentarios_analista': 'Adiantamento 15MM conciliado em ambos os '
                                                     'lados'},
                            {'linha': 3,
                             'cruzamento': 'INN1 x TBRA',
                             'empresa_origem': 'INN1',
                             'empresa_conc': 'TBRA',
                             'conta': '21121111',
                             'valor_comp_elim': -7966.83,
                             'valor_comp_final': -7966.83,
                             'diferenca': 0.0,
                             'resultado_analise': 'Sucesso',
                             'comentarios_analista': ''},
                            {'linha': 4,
                             'cruzamento': 'INN1 x TBRA',
                             'empresa_origem': 'INN1',
                             'empresa_conc': 'TBRA',
                             'conta': '21121112',
                             'valor_comp_elim': -1007634.92,
                             'valor_comp_final': -1007634.92,
                             'diferenca': 0.0,
                             'resultado_analise': 'Sucesso',
                             'comentarios_analista': ''},
                            {'linha': 5,
                             'cruzamento': 'INN1 x TBRA',
                             'empresa_origem': 'INN1',
                             'empresa_conc': 'TBRA',
                             'conta': '21121193',
                             'valor_comp_elim': -112023.92,
                             'valor_comp_final': -112023.92,
                             'diferenca': 0.0,
                             'resultado_analise': 'Sucesso',
                             'comentarios_analista': ''},
                            {'linha': 6,
                             'cruzamento': 'INN1 x TBRA',
                             'empresa_origem': 'INN1',
                             'empresa_conc': 'TBRA',
                             'conta': '21191915',
                             'valor_comp_elim': -105086.19,
                             'valor_comp_final': -105086.19,
                             'diferenca': 0.0,
                             'resultado_analise': 'Sucesso',
                             'comentarios_analista': ''},
                            {'linha': 7,
                             'cruzamento': 'INN1 x TBRA',
                             'empresa_origem': 'INN1',
                             'empresa_conc': 'TBRA',
                             'conta': '21192001',
                             'valor_comp_elim': 0.0,
                             'valor_comp_final': 0.0,
                             'diferenca': 0.0,
                             'resultado_analise': 'Sucesso',
                             'comentarios_analista': ''},
                            {'linha': 8,
                             'cruzamento': 'ITIS x TBRA',
                             'empresa_origem': 'ITIS',
                             'empresa_conc': 'TBRA',
                             'conta': '11211115',
                             'valor_comp_elim': 10865902.81,
                             'valor_comp_final': 10865902.81,
                             'diferenca': 0.0,
                             'resultado_analise': 'Sucesso',
                             'comentarios_analista': ''},
                            {'linha': 9,
                             'cruzamento': 'ITIS x TBRA',
                             'empresa_origem': 'ITIS',
                             'empresa_conc': 'TBRA',
                             'conta': '11211121',
                             'valor_comp_elim': 3528817.67,
                             'valor_comp_final': 3528817.67,
                             'diferenca': 0.0,
                             'resultado_analise': 'Sucesso',
                             'comentarios_analista': ''},
                            {'linha': 10,
                             'cruzamento': 'ITIS x TBRA',
                             'empresa_origem': 'ITIS',
                             'empresa_conc': 'TBRA',
                             'conta': '11211127',
                             'valor_comp_elim': 67084907.48,
                             'valor_comp_final': 67084907.48,
                             'diferenca': 0.0,
                             'resultado_analise': 'Sucesso',
                             'comentarios_analista': ''},
                            {'linha': 11,
                             'cruzamento': 'ITIS x TBRA',
                             'empresa_origem': 'ITIS',
                             'empresa_conc': 'TBRA',
                             'conta': '11211141',
                             'valor_comp_elim': 35444207.57,
                             'valor_comp_final': 35444207.57,
                             'diferenca': 0.0,
                             'resultado_analise': 'Sucesso',
                             'comentarios_analista': ''},
                            {'linha': 12,
                             'cruzamento': 'ITIS x TBRA',
                             'empresa_origem': 'ITIS',
                             'empresa_conc': 'TBRA',
                             'conta': '11211142',
                             'valor_comp_elim': -0.03,
                             'valor_comp_final': -0.03,
                             'diferenca': 0.0,
                             'resultado_analise': 'Sucesso',
                             'comentarios_analista': ''},
                            {'linha': 13,
                             'cruzamento': 'ITIS x TBRA',
                             'empresa_origem': 'ITIS',
                             'empresa_conc': 'TBRA',
                             'conta': '11211922',
                             'valor_comp_elim': 80718.54,
                             'valor_comp_final': 80718.54,
                             'diferenca': 0.0,
                             'resultado_analise': 'Sucesso',
                             'comentarios_analista': ''},
                            {'linha': 14,
                             'cruzamento': 'ITIS x TBRA',
                             'empresa_origem': 'ITIS',
                             'empresa_conc': 'TBRA',
                             'conta': '11251111',
                             'valor_comp_elim': -32112.67,
                             'valor_comp_final': -32112.67,
                             'diferenca': 0.0,
                             'resultado_analise': 'Sucesso',
                             'comentarios_analista': ''},
                            {'linha': 15,
                             'cruzamento': 'ITIS x TBRA',
                             'empresa_origem': 'ITIS',
                             'empresa_conc': 'TBRA',
                             'conta': '11252311',
                             'valor_comp_elim': -30517854.06,
                             'valor_comp_final': -30517854.06,
                             'diferenca': 0.0,
                             'resultado_analise': 'Sucesso',
                             'comentarios_analista': ''},
                            {'linha': 16,
                             'cruzamento': 'ITIS x TBRA',
                             'empresa_origem': 'ITIS',
                             'empresa_conc': 'TBRA',
                             'conta': '11252511',
                             'valor_comp_elim': 30146.61,
                             'valor_comp_final': 30146.61,
                             'diferenca': 0.0,
                             'resultado_analise': 'Sucesso',
                             'comentarios_analista': ''},
                            {'linha': 17,
                             'cruzamento': 'ITIS x TBRA',
                             'empresa_origem': 'ITIS',
                             'empresa_conc': 'TBRA',
                             'conta': '11291114',
                             'valor_comp_elim': -1631755.78,
                             'valor_comp_final': -1631755.78,
                             'diferenca': 0.0,
                             'resultado_analise': 'Sucesso',
                             'comentarios_analista': ''},
                            {'linha': 18,
                             'cruzamento': 'TBRA x TERRA',
                             'empresa_origem': 'TBRA',
                             'empresa_conc': 'TERRA',
                             'conta': '11211115',
                             'valor_comp_elim': 5326521.7,
                             'valor_comp_final': 5333462.99,
                             'diferenca': -6941.29,
                             'resultado_analise': 'Requer Análise',
                             'comentarios_analista': 'Divergência de rateio tributário em análise '
                                                     'com a contraparte'}],
 'expurgadas_compfinal': [{'linha': 1,
                           'cruzamento': '0942 x TBRA',
                           'empresa_origem': '0942 - Fundação Telefônica',
                           'classificacao_base_mestre': 'Não Eliminável',
                           'conta': '11211115',
                           'valor_comp_final': 145230.1,
                           'resultado_analise': 'Sucesso',
                           'comentarios_analista': 'Empresa Não Eliminável parametrizada na Base '
                                                   'Mestre'},
                          {'linha': 2,
                           'cruzamento': '1969 x TBRA',
                           'empresa_origem': '1969 - Visão Prev',
                           'classificacao_base_mestre': 'Não Eliminável',
                           'conta': '21121112',
                           'valor_comp_final': -89410.55,
                           'resultado_analise': 'Sucesso',
                           'comentarios_analista': 'Empresa Não Eliminável parametrizada na Base '
                                                   'Mestre'},
                          {'linha': 3,
                           'cruzamento': '2193 x TBRA',
                           'empresa_origem': '2193 - Vivo Ventures',
                           'classificacao_base_mestre': 'Não Eliminável',
                           'conta': '11211922',
                           'valor_comp_final': 0.0,
                           'resultado_analise': 'Sucesso',
                           'comentarios_analista': 'Sem movimentação no período'},
                          {'linha': 4,
                           'cruzamento': '0306 x TBRA',
                           'empresa_origem': '0306 - ITIS',
                           'classificacao_base_mestre': 'Eliminável',
                           'conta': '11251119',
                           'valor_comp_final': 17261.71,
                           'resultado_analise': 'Requer Análise',
                           'comentarios_analista': 'Verificar partida expurgada de empresa '
                                                   'Eliminável'}],
 'somente_compfinal': [{'linha': 1,
                        'cruzamento': 'TBRA x POP',
                        'empresa_origem': 'TBRA',
                        'empresa_conc': 'POP',
                        'conta': '11211115',
                        'valor_comp_final': 0.0,
                        'resultado_analise': 'Sucesso',
                        'comentarios_analista': 'Saldo zerado na composição final'},
                       {'linha': 2,
                        'cruzamento': 'TBRA x CLOUD',
                        'empresa_origem': 'TBRA',
                        'empresa_conc': 'CLOUD',
                        'conta': '11211127',
                        'valor_comp_final': 0.0,
                        'resultado_analise': 'Sucesso',
                        'comentarios_analista': 'Saldo zerado na composição final'},
                       {'linha': 3,
                        'cruzamento': 'CLOUD x VSCD',
                        'empresa_origem': 'CLOUD',
                        'empresa_conc': 'VSCD',
                        'conta': '11211922',
                        'valor_comp_final': 180637.43,
                        'resultado_analise': 'Requer Análise',
                        'comentarios_analista': 'Regularização A Faturar Azure pendente na '
                                                'Eliminação'}],
 'somente_eliminacao': [{'linha': 1,
                         'cruzamento': 'TBRA x VSS',
                         'empresa_origem': 'TBRA',
                         'valor_comp_elim': 0.0,
                         'conta': '21121111',
                         'resultado_analise': 'Sucesso',
                         'comentarios_analista': 'Sem resíduo exclusivo na eliminação'},
                        {'linha': 2,
                         'cruzamento': 'TBRA x TGLOG',
                         'empresa_origem': 'TBRA',
                         'valor_comp_elim': 0.0,
                         'conta': '21121112',
                         'resultado_analise': 'Sucesso',
                         'comentarios_analista': 'Sem resíduo exclusivo na eliminação'},
                        {'linha': 3,
                         'cruzamento': 'ITIS x TGLOG',
                         'empresa_origem': 'ITIS',
                         'valor_comp_elim': -17261.71,
                         'conta': '21121193',
                         'resultado_analise': 'Requer Análise',
                         'comentarios_analista': 'Despesa operacional registrada na ITIS e não na '
                                                 'TGLOG'}]}


def calcular_metricas_patrimonial(ativo_1, passivo_2, ativo_3, passivo_4, dif_ant=0.0):
    dif_1_4 = round((ativo_1 or 0.0) + (passivo_4 or 0.0), 2)
    dif_2_3 = round((passivo_2 or 0.0) + (ativo_3 or 0.0), 2)
    dif_atual = round(dif_1_4 + dif_2_3, 2)
    ant = round(dif_ant or 0.0, 2)
    var_pct = None if ant == 0.0 else round(((dif_atual / ant) - 1.0), 6)
    return {
        "dif_bruta_1_4": dif_1_4,
        "dif_bruta_2_3": dif_2_3,
        "dif_liquida_atual": dif_atual,
        "dif_liquida_anterior": ant,
        "var_horiz_pct": var_pct,
    }


def calcular_metricas_resultado(inef_trib, diferenca, dif_acum_ant=0.0):
    it = round(inef_trib or 0.0, 2)
    df = round(diferenca or 0.0, 2)
    liq = round(it + df, 2)
    acum = round((dif_acum_ant or 0.0) + df, 2)
    if acum > 0:
        sug = "Receita Bruta maior que Despesa"
    elif acum < 0:
        sug = "Despesa maior que Receita Bruta"
    else:
        sug = "Sem diferença"
    return {
        "inef_trib": it,
        "diferenca": df,
        "inef_liquida": liq,
        "dif_real_acumulada_ar": acum,
        "sugestao_diferenca_as": sug,
    }


def classificar_item9_eliminacao_x_compfinal(valor_comp_elim, valor_comp_final, tolerancia=0.005):
    elim = round(float(valor_comp_elim or 0.0), 2)
    comp = round(float(valor_comp_final or 0.0), 2)
    diferenca = round(elim - comp, 2)
    status = "Sucesso" if abs(diferenca) <= tolerancia else "Requer Análise"
    return {
        "valor_comp_elim": elim,
        "valor_comp_final": comp,
        "diferenca": diferenca,
        "resultado_analise": status,
    }


def classificar_item9_expurgadas_compfinal(tipo_empresa_base_mestre):
    tipo = str(tipo_empresa_base_mestre or "").strip().casefold()
    if "não eliminável" in tipo or "nao eliminavel" in tipo:
        return "Sucesso"
    return "Requer Análise"


def classificar_item9_somente_compfinal(valor_comp_final, tolerancia=0.005):
    val = round(float(valor_comp_final or 0.0), 2)
    return "Sucesso" if abs(val) <= tolerancia else "Requer Análise"


def classificar_item9_somente_eliminacao(valor_comp_elim, tolerancia=0.005):
    val = round(float(valor_comp_elim or 0.0), 2)
    return "Sucesso" if abs(val) <= tolerancia else "Requer Análise"


def gerar_quadro_sintetico_item9(dados_item9):
    config_abas = [
        ("Eliminação x CompFinal", "eliminacao_x_compfinal", "diferenca", "Diferença (Col G) = 0"),
        ("Expurgadas_CompFinal", "expurgadas_compfinal", "valor_comp_final", "Empresa Origem = Não Eliminável"),
        ("Somente_CompFinal", "somente_compfinal", "valor_comp_final", "Valor_CompFinal (Col E) = 0"),
        ("Somente_Eliminacao", "somente_eliminacao", "valor_comp_elim", "Valor_CompElim (Col C) = 0"),
    ]
    resumo = []
    for nome_aba, chave, col_valor, regra_desc in config_abas:
        registros = dados_item9.get(chave, [])
        total = len(registros)
        sucesso = sum(1 for r in registros if r.get("resultado_analise") == "Sucesso")
        requer_analise = sum(1 for r in registros if r.get("resultado_analise") == "Requer Análise")
        atencao = total - sucesso - requer_analise
        impacto_rs = round(
            sum(abs(float(r.get(col_valor) or 0.0)) for r in registros if r.get("resultado_analise") != "Sucesso"),
            2,
        )
        if requer_analise > 0:
            status_geral = "Requer Análise"
        elif atencao > 0:
            status_geral = "Atenção"
        else:
            status_geral = "Sucesso"
        resumo.append({
            "aba_relatorio": nome_aba,
            "regra_aplicada": regra_desc,
            "total_registros": total,
            "qtd_sucesso": sucesso,
            "qtd_atencao": atencao,
            "qtd_requer_analise": requer_analise,
            "impacto_divergencia_rs": impacto_rs,
            "classificacao_sintetica": status_geral,
        })
    return resumo


def formatar_brl(valor):
    if valor is None:
        return "R$ 0,00"
    neg = valor < 0
    s = f"{abs(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"-R$ {s}" if neg else f"R$ {s}"


def renderizar_kpi_cards(cards: list[tuple[str, str]]) -> None:
    colunas = st.columns(len(cards))
    for col, (rotulo, valor) in zip(colunas, cards):
        with col:
            st.markdown(
                f'<div class="kpi-card"><div class="kpi-label">{rotulo}</div><div class="kpi-value">{valor}</div></div>',
                unsafe_allow_html=True,
            )


def recalcular_aba_sum(registros):
    agrupado = {}
    for r in registros:
        resp = r.get("responsavel", "")
        if resp == "Incorporada":
            continue
        rotulo = "Sem Movimento" if resp == "Z_Sem Movimento" else resp
        item = agrupado.setdefault(
            rotulo,
            {"rotulo_linha": rotulo, "contagem_cruzamento": 0, "soma_mes_atual": 0.0, "soma_mes_anterior": 0.0},
        )
        item["contagem_cruzamento"] += 1
        item["soma_mes_atual"] = round(item["soma_mes_atual"] + float(r.get("dif_liquida_atual") or 0.0), 2)
        item["soma_mes_anterior"] = round(item["soma_mes_anterior"] + float(r.get("dif_liquida_anterior") or 0.0), 2)
    linhas = list(agrupado.values())
    linhas.append({
        "rotulo_linha": "Total Geral",
        "contagem_cruzamento": sum(i["contagem_cruzamento"] for i in linhas),
        "soma_mes_atual": round(sum(i["soma_mes_atual"] for i in linhas), 2),
        "soma_mes_anterior": round(sum(i["soma_mes_anterior"] for i in linhas), 2),
    })
    return linhas


def main():
    st.set_page_config(
        page_title="Painel Intercompany — Fechamento Contábil",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    if "dados_pat" not in st.session_state:
        st.session_state.dados_pat = json.loads(json.dumps(DADOS_INICIAIS_PATRIMONIAL))
    if "dados_res" not in st.session_state:
        st.session_state.dados_res = json.loads(json.dumps(DADOS_INICIAIS_RESULTADO))
    if "dados_item9" not in st.session_state:
        st.session_state.dados_item9 = json.loads(json.dumps(DADOS_INICIAIS_ITEM9))

    st.markdown(
        """
        <style>
        .doc-header {
            background-color: #5A189A;
            border-bottom: 4px solid #2B0A4E;
            padding: 18px 24px;
            border-radius: 6px;
            color: #FFFFFF;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 16px;
        }
        .doc-header-icon {
            background-color: #2B0A4E;
            border: 1px solid #C7A6E8;
            width: 44px;
            height: 44px;
            border-radius: 6px;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        }
        .doc-header h1 {
            color: #FFFFFF !important;
            font-size: 1.45rem !important;
            font-weight: 700 !important;
            margin: 0 !important;
            padding: 0 !important;
        }
        .doc-header p {
            color: #C7A6E8 !important;
            font-size: 0.9rem !important;
            margin: 4px 0 0 0 !important;
        }
        .kpi-card {
            background-color: #FFFFFF;
            border: 1px solid #C7A6E8;
            border-left: 5px solid #5A189A;
            padding: 12px 14px;
            border-radius: 4px;
            margin-bottom: 14px;
            min-height: 74px;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }
        .kpi-label {
            color: #6E6E6E;
            font-size: 0.80rem;
            font-weight: 600;
            margin-bottom: 6px;
            white-space: nowrap;
        }
        .kpi-value {
            color: #2B0A4E;
            font-size: clamp(0.95rem, 1.1vw, 1.12rem);
            font-weight: 700;
            line-height: 1.25;
            white-space: nowrap;
        }
        button[kind="primary"] {
            background-color: #5A189A !important;
            border-color: #2B0A4E !important;
            color: #FFFFFF !important;
        }
        button[kind="primary"]:hover {
            background-color: #2B0A4E !important;
            border-color: #2B0A4E !important;
        }
        </style>
        <div class="doc-header">
            <div class="doc-header-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                    <line x1="3" y1="9" x2="21" y2="9"></line>
                    <line x1="9" y1="21" x2="9" y2="9"></line>
                </svg>
            </div>
            <div>
                <h1>Painel de Controle Intercompany — Fechamento Contábil</h1>
                <p>Visão On-line Única | Camada Silver & Gold (workspace.silver / workspace.gold) | Eliminação Patrimonial, Eliminação de Resultado e Composições Gerais e Elimináveis</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    aba_pat, aba_res, aba_item9 = st.tabs([
        ":material/account_balance: Eliminação Patrimonial",
        ":material/analytics: Eliminação de Resultado",
        ":material/fact_check: Composições Gerais e Elimináveis",
    ])

    # ==========================================================================
    # ABA 1: ITEM 7 — ELIMINAÇÃO PATRIMONIAL
    # ==========================================================================
    with aba_pat:
        registros_pat = st.session_state.dados_pat["eliminaveis"]
        c1, c2, c3, c4, c5 = st.columns(5)
        resps = sorted({r["responsavel"] for r in registros_pat if r["responsavel"]})
        with c1:
            f_resp = st.multiselect("Responsável", resps)
        with c2:
            f_st_ana = st.multiselect("Status (Analista)", STATUS_ANALISTA_OPCOES)
        with c3:
            f_st_rev = st.multiselect("Status (Revisor)", STATUS_REVISOR_OPCOES)
        with c4:
            f_mov = st.selectbox("Movimentação", ["Todos", "Com movimentação (!= 0)", "Sem movimentação (= 0)", "Ocultar Incorporadas"])
        with c5:
            ord_por = st.selectbox("Ordenar por", ["Ordem Padrão", "Empresa (A-Z)", "Maior Dif. Líquida", "Menor Dif. Líquida", "Responsável"])

        busca = st.text_input(
            "Buscar por Empresa/Cruzamento ou Comentários (Analista / Revisor)",
            placeholder="Ex.: TBRA x ITIS, Azure, provisão...",
        )

        filtrados = []
        for r in registros_pat:
            if f_resp and r["responsavel"] not in f_resp:
                continue
            if f_st_ana and r["status_analista"] not in f_st_ana:
                continue
            if f_st_rev and r["status_revisor"] not in f_st_rev:
                continue
            mov = abs(r["ativo_1"]) + abs(r["passivo_2"]) + abs(r["ativo_3"]) + abs(r["passivo_4"])
            if f_mov == "Com movimentação (!= 0)" and mov == 0:
                continue
            if f_mov == "Sem movimentação (= 0)" and mov != 0:
                continue
            if f_mov == "Ocultar Incorporadas" and r["responsavel"] == "Incorporada":
                continue
            if busca and busca.casefold() not in " ".join([r["cruzamento"], r["responsavel"], r["comentarios_analista"], r["comentarios_revisor"]]).casefold():
                continue
            filtrados.append(r)

        if ord_por == "Empresa (A-Z)":
            filtrados.sort(key=lambda x: x["cruzamento"])
        elif ord_por == "Maior Dif. Líquida":
            filtrados.sort(key=lambda x: abs(x["dif_liquida_atual"] or 0.0), reverse=True)
        elif ord_por == "Menor Dif. Líquida":
            filtrados.sort(key=lambda x: abs(x["dif_liquida_atual"] or 0.0))
        elif ord_por == "Responsável":
            filtrados.sort(key=lambda x: (x["responsavel"], x["cruzamento"]))

        renderizar_kpi_cards([
            ("Cruzamentos Ativos", f"{len(filtrados)} / {len(registros_pat)}"),
            ("Ativo (1) Origem", formatar_brl(sum(r["ativo_1"] for r in filtrados))),
            ("Passivo (2) Origem", formatar_brl(sum(r["passivo_2"] for r in filtrados))),
            ("Dif. Líquida Ago/26 (J)", formatar_brl(sum(r["dif_liquida_atual"] for r in filtrados))),
            ("Dif. Líquida Jul/26 (K)", formatar_brl(sum(r["dif_liquida_anterior"] for r in filtrados))),
        ])

        t_elim, t_sum, t_temas = st.tabs([
            ":material/table_chart: Elimináveis",
            ":material/summarize: Sum (Por Analista)",
            ":material/bookmark_manager: Temas Principais",
        ])
        with t_elim:
            editados = st.data_editor(
                filtrados,
                use_container_width=True,
                height=520,
                num_rows="dynamic",
                column_config={
                    "linha": None,
                    "competencia": st.column_config.TextColumn("Período", width="small"),
                    "responsavel": st.column_config.TextColumn("Responsável", width="small"),
                    "cruzamento": st.column_config.TextColumn("Cruzamento", width="medium"),
                    "ativo_1": st.column_config.NumberColumn("Ativo (1)", format="R$ %.2f"),
                    "passivo_2": st.column_config.NumberColumn("Passivo (2)", format="R$ %.2f"),
                    "ativo_3": st.column_config.NumberColumn("Ativo (3)", format="R$ %.2f"),
                    "passivo_4": st.column_config.NumberColumn("Passivo (4)", format="R$ %.2f"),
                    "dif_bruta_1_4": st.column_config.NumberColumn("(1)-(4) [H]", format="R$ %.2f", disabled=True),
                    "dif_bruta_2_3": st.column_config.NumberColumn("(2)-(3) [I]", format="R$ %.2f", disabled=True),
                    "dif_liquida_atual": st.column_config.NumberColumn("Ago-26 [J]", format="R$ %.2f", disabled=True),
                    "dif_liquida_anterior": st.column_config.NumberColumn("Jul-26 [K]", format="R$ %.2f"),
                    "var_horiz_pct": st.column_config.NumberColumn("Var. Horiz.", format="%.2f", disabled=True),
                    "status_analista": st.column_config.SelectboxColumn("Status (Analista)", options=STATUS_ANALISTA_OPCOES),
                    "status_revisor": st.column_config.SelectboxColumn("Status (Revisor)", options=STATUS_REVISOR_OPCOES),
                    "comentarios_revisor": st.column_config.TextColumn("Comentários (Revisor)", width="large"),
                    "comentarios_analista": st.column_config.TextColumn("Comentários (Analista)", width="large"),
                },
                key="ed_pat",
            )
            if st.button(":material/save: Recalcular Fórmulas e Atualizar Painel Patrimonial", type="primary", key="btn_save_pat"):
                mapa = {r["cruzamento"]: r for r in editados if r.get("cruzamento")}
                for r in registros_pat:
                    if r["cruzamento"] in mapa:
                        r.update(mapa[r["cruzamento"]])
                        r.update(calcular_metricas_patrimonial(r["ativo_1"], r["passivo_2"], r["ativo_3"], r["passivo_4"], r["dif_liquida_anterior"]))
                st.success("Fórmulas e status atualizados com sucesso.")

        with t_sum:
            st.dataframe(recalcular_aba_sum(registros_pat), use_container_width=True)
        with t_temas:
            st.dataframe(st.session_state.dados_pat["temas_principais"], use_container_width=True)

    # ==========================================================================
    # ABA 2: ITEM 8 — ELIMINAÇÃO RESULTADO
    # ==========================================================================
    with aba_res:
        registros_res = st.session_state.dados_res
        renderizar_kpi_cards([
            ("Cruzamentos Resultado", f"{len(registros_res)}"),
            ("Soma Inef. Líq. Julho", formatar_brl(sum(r["jul_inef_liq"] for r in registros_res))),
            ("Soma Inef. Líq. Agosto", formatar_brl(sum(r["ago_inef_liq"] for r in registros_res))),
            ("Soma Dif. Real Acum. (Col AR)", formatar_brl(sum(r["dif_real_acumulada_ar"] for r in registros_res))),
        ])

        ed_res = st.data_editor(
            registros_res,
            use_container_width=True,
            height=480,
            num_rows="dynamic",
            column_config={
                "linha": None,
                "competencia": st.column_config.TextColumn("Período", width="small"),
                "responsavel": st.column_config.TextColumn("Responsável", width="small"),
                "cruzamento": st.column_config.TextColumn("Cruzamento", width="medium"),
                "jul_inef_trib": st.column_config.NumberColumn("Jul: Inef. Trib", format="R$ %.2f"),
                "jul_diferenca": st.column_config.NumberColumn("Jul: Diferença", format="R$ %.2f"),
                "jul_inef_liq": st.column_config.NumberColumn("Jul: Inef. Líq.", format="R$ %.2f", disabled=True),
                "ago_inef_trib": st.column_config.NumberColumn("Ago: Inef. Trib", format="R$ %.2f"),
                "ago_diferenca": st.column_config.NumberColumn("Ago: Diferença", format="R$ %.2f"),
                "ago_inef_liq": st.column_config.NumberColumn("Ago: Inef. Líq.", format="R$ %.2f", disabled=True),
                "dif_real_acumulada_ar": st.column_config.NumberColumn("Dif. Acum. [Col AR]", format="R$ %.2f", disabled=True),
                "sugestao_diferenca_as": st.column_config.TextColumn("Sugestão [Col AS]", width="medium", disabled=True),
                "status_analista": st.column_config.SelectboxColumn("Status (Analista)", options=STATUS_ANALISTA_OPCOES),
                "status_revisor": st.column_config.SelectboxColumn("Status (Revisor)", options=STATUS_REVISOR_OPCOES),
                "comentarios_analista": st.column_config.TextColumn("Comentários Analista", width="large"),
                "comentarios_revisor": st.column_config.TextColumn("Comentários Revisor", width="large"),
            },
            key="ed_res",
        )
        if st.button(":material/save: Recalcular Ineficiência Líquida e Colunas AR/AS", type="primary", key="btn_save_res"):
            for r in ed_res:
                r["jul_inef_liq"] = round(float(r.get("jul_inef_trib") or 0.0) + float(r.get("jul_diferenca") or 0.0), 2)
                c = calcular_metricas_resultado(r.get("ago_inef_trib"), r.get("ago_diferenca"), r.get("jul_diferenca"))
                r["ago_inef_liq"] = c["inef_liquida"]
                r["dif_real_acumulada_ar"] = c["dif_real_acumulada_ar"]
                r["sugestao_diferenca_as"] = c["sugestao_diferenca_as"]
            st.session_state.dados_res = ed_res
            st.success("Painel de Resultado recalculado com sucesso.")

    # ==========================================================================
    # ABA 3: ITEM 9 — COMPOSIÇÕES GERAIS E ELIMINÁVEIS — PATRIMONIAL
    # ==========================================================================
    with aba_item9:
        dados_i9 = st.session_state.dados_item9
        quadro_sintetico = gerar_quadro_sintetico_item9(dados_i9)

        tot_partidas = sum(q["total_registros"] for q in quadro_sintetico)
        tot_sucesso = sum(q["qtd_sucesso"] for q in quadro_sintetico)
        tot_analise = sum(q["qtd_requer_analise"] for q in quadro_sintetico)
        tot_impacto = sum(q["impacto_divergencia_rs"] for q in quadro_sintetico)
        status_liberacao = "Liberado" if tot_analise == 0 else f"Bloqueado ({tot_analise})"

        renderizar_kpi_cards([
            ("Total Partidas Analisadas", f"{tot_partidas}"),
            ("Classificadas: Sucesso", f"{tot_sucesso}"),
            ("Classificadas: Requer Análise", f"{tot_analise}"),
            ("Impacto Divergências (R$)", formatar_brl(tot_impacto)),
            ("Status de Liberação", status_liberacao),
        ])

        st.subheader("Quadro Sintético — Indicadores de Processamento")
        st.caption(
            "Relatório: **Ago-26_13_1_Validacao_Eliminacoes x CompFinais_Patrimonial.xlsx** | "
            "Arquivo mestre obrigatório em 2_Comp_Finais: **1-Composicao De Saldo_Patrimonial_2026_BASE Nova**"
        )
        st.dataframe(
            quadro_sintetico,
            use_container_width=True,
            column_config={
                "aba_relatorio": st.column_config.TextColumn("Aba do Relatório", width="medium"),
                "regra_aplicada": st.column_config.TextColumn("Regra de Validação", width="medium"),
                "total_registros": st.column_config.NumberColumn("Total Partidas"),
                "qtd_sucesso": st.column_config.NumberColumn("Sucesso"),
                "qtd_atencao": st.column_config.NumberColumn("Atenção"),
                "qtd_requer_analise": st.column_config.NumberColumn("Requer Análise"),
                "impacto_divergencia_rs": st.column_config.NumberColumn("Impacto Divergência (R$)", format="R$ %.2f"),
                "classificacao_sintetica": st.column_config.TextColumn("Status da Aba", width="small"),
            },
        )

        st.divider()
        t_aba1, t_aba2, t_aba3, t_aba4 = st.tabs([
            ":material/compare_arrows: Eliminação x CompFinal",
            ":material/filter_alt_off: Expurgadas_CompFinal",
            ":material/assignment_late: Somente_CompFinal",
            ":material/rule: Somente_Eliminacao",
        ])

        with t_aba1:
            st.caption("Regra Silver: **Diferença (Coluna G) = 0 → Sucesso** | **Diferença != 0 → Requer Análise**")
            ed_a1 = st.data_editor(
                dados_i9["eliminacao_x_compfinal"],
                use_container_width=True,
                height=420,
                num_rows="dynamic",
                column_config={
                    "linha": None,
                    "cruzamento": st.column_config.TextColumn("Cruzamento (Col A)"),
                    "empresa_origem": st.column_config.TextColumn("Empresa Origem (Col B)"),
                    "empresa_conc": st.column_config.TextColumn("Empresa Conc (Col C)"),
                    "conta": st.column_config.TextColumn("Conta (Col D)"),
                    "valor_comp_elim": st.column_config.NumberColumn("Valor_CompElim (Col E)", format="R$ %.2f"),
                    "valor_comp_final": st.column_config.NumberColumn("Valor_CompFinal (Col F)", format="R$ %.2f"),
                    "diferenca": st.column_config.NumberColumn("Diferença (Col G)", format="R$ %.2f", disabled=True),
                    "resultado_analise": st.column_config.TextColumn("Classificação Silver", disabled=True),
                    "comentarios_analista": st.column_config.TextColumn("Comentários Analista", width="large"),
                },
                key="ed_i9_a1",
            )

        with t_aba2:
            st.caption("Regra Silver: **Empresa Origem (Coluna B) = Não Eliminável → Sucesso** | **Eliminável → Requer Análise**")
            ed_a2 = st.data_editor(
                dados_i9["expurgadas_compfinal"],
                use_container_width=True,
                height=320,
                num_rows="dynamic",
                column_config={
                    "linha": None,
                    "cruzamento": st.column_config.TextColumn("Cruzamento (Col A)"),
                    "empresa_origem": st.column_config.TextColumn("Empresa Origem (Col B)"),
                    "classificacao_base_mestre": st.column_config.SelectboxColumn(
                        "Classificação Base Mestre", options=["Não Eliminável", "Eliminável"]
                    ),
                    "conta": st.column_config.TextColumn("Conta"),
                    "valor_comp_final": st.column_config.NumberColumn("Valor_CompFinal", format="R$ %.2f"),
                    "resultado_analise": st.column_config.TextColumn("Classificação Silver", disabled=True),
                    "comentarios_analista": st.column_config.TextColumn("Comentários Analista", width="large"),
                },
                key="ed_i9_a2",
            )

        with t_aba3:
            st.caption("Regra Silver: **Conta (Col D) e Valor_CompFinal (Col E) = 0 → Sucesso** | **!= 0 → Requer Análise**")
            ed_a3 = st.data_editor(
                dados_i9["somente_compfinal"],
                use_container_width=True,
                height=320,
                num_rows="dynamic",
                column_config={
                    "linha": None,
                    "cruzamento": st.column_config.TextColumn("Cruzamento (Col A)"),
                    "empresa_origem": st.column_config.TextColumn("Empresa Origem (Col B)"),
                    "empresa_conc": st.column_config.TextColumn("Empresa Conc (Col C)"),
                    "conta": st.column_config.TextColumn("Conta (Col D)"),
                    "valor_comp_final": st.column_config.NumberColumn("Valor_CompFinal (Col E)", format="R$ %.2f"),
                    "resultado_analise": st.column_config.TextColumn("Classificação Silver", disabled=True),
                    "comentarios_analista": st.column_config.TextColumn("Comentários Analista", width="large"),
                },
                key="ed_i9_a3",
            )

        with t_aba4:
            st.caption("Regra Silver: **Valor_CompElim (Col C) = 0 → Sucesso** | **!= 0 → Requer Análise**")
            ed_a4 = st.data_editor(
                dados_i9["somente_eliminacao"],
                use_container_width=True,
                height=320,
                num_rows="dynamic",
                column_config={
                    "linha": None,
                    "cruzamento": st.column_config.TextColumn("Cruzamento (Col A)"),
                    "empresa_origem": st.column_config.TextColumn("Empresa Origem (Col B)"),
                    "valor_comp_elim": st.column_config.NumberColumn("Valor_CompElim (Col C)", format="R$ %.2f"),
                    "conta": st.column_config.TextColumn("Conta (Col D)"),
                    "resultado_analise": st.column_config.TextColumn("Classificação Silver", disabled=True),
                    "comentarios_analista": st.column_config.TextColumn("Comentários Analista", width="large"),
                },
                key="ed_i9_a4",
            )

        if st.button(":material/save: Recalcular Validações e Atualizar Quadro Sintético", type="primary", key="btn_save_i9"):
            for r in ed_a1:
                r.update(classificar_item9_eliminacao_x_compfinal(r.get("valor_comp_elim"), r.get("valor_comp_final")))
            for r in ed_a2:
                r["resultado_analise"] = classificar_item9_expurgadas_compfinal(r.get("classificacao_base_mestre"))
            for r in ed_a3:
                r["resultado_analise"] = classificar_item9_somente_compfinal(r.get("valor_comp_final"))
            for r in ed_a4:
                r["resultado_analise"] = classificar_item9_somente_eliminacao(r.get("valor_comp_elim"))

            st.session_state.dados_item9 = {
                "eliminacao_x_compfinal": ed_a1,
                "expurgadas_compfinal": ed_a2,
                "somente_compfinal": ed_a3,
                "somente_eliminacao": ed_a4,
            }
            st.success("Validações da Camada Silver e Quadro Sintético atualizados com sucesso.")


if __name__ == "__main__":
    main()
