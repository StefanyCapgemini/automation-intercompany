from pathlib import Path
import sys
import unittest

PROJETO_DIR = Path(__file__).resolve().parents[1]
PAINEL_DIR = PROJETO_DIR / "databricks_painel"
if str(PAINEL_DIR) not in sys.path:
    sys.path.insert(0, str(PAINEL_DIR))

from excel_loader import (
    carregar_dados_iniciais_item9_patrimonial,
    carregar_dados_iniciais_resultado,
    carregar_painel_patrimonial_xlsx,
    carregar_painel_resultado_xlsx,
)
from pipeline_silver_gold import (
    calcular_metricas_patrimonial,
    calcular_metricas_resultado,
    classificar_item9_eliminacao_x_compfinal,
    classificar_item9_expurgadas_compfinal,
    classificar_item9_somente_compfinal,
    classificar_item9_somente_eliminacao,
    gerar_quadro_sintetico_item9,
    recalcular_linha_resultado_anual,
    validar_totais_resultado_silver,
)


class DatabricksPainelTests(unittest.TestCase):
    def test_carrega_29_cruzamentos_da_planilha_oficial_patrimonial(self):
        caminho = PROJETO_DIR / "documentacao" / "Painel Eliminação Patrimonial_08-2026.xlsx"
        dados = carregar_painel_patrimonial_xlsx(caminho)
        self.assertEqual(len(dados["eliminaveis"]), 29)
        self.assertEqual(len(dados["sum"]), 6)
        self.assertEqual(len(dados["temas_principais"]), 27)

        # Verifica cálculo exato da linha TBRA x ITIS (linha 12)
        tbra_itis = next(r for r in dados["eliminaveis"] if r["cruzamento"] == "TBRA x ITIS")
        self.assertAlmostEqual(tbra_itis["ativo_1"], 99731615.14, places=2)
        self.assertAlmostEqual(tbra_itis["passivo_2"], -119690699.07, places=2)
        self.assertAlmostEqual(tbra_itis["dif_bruta_1_4"], 48114396.82, places=2)
        self.assertAlmostEqual(tbra_itis["dif_bruta_2_3"], -33978609.38, places=2)
        self.assertAlmostEqual(tbra_itis["dif_liquida_atual"], 14135787.44, places=2)
        self.assertEqual(tbra_itis["status_analista"], "Enviado para reporting")
        self.assertEqual(tbra_itis["status_revisor"], "Ok para envio")

    def test_carrega_29_cruzamentos_da_planilha_oficial_resultado_10_2026(self):
        caminho = PROJETO_DIR / "documentacao" / "Painel Eliminacao_Resultado_10-2026.xlsx"
        dados = carregar_painel_resultado_xlsx(caminho)
        self.assertEqual(len(dados["resumo"]), 29)
        self.assertEqual(len(dados["todos_cruzamentos"]), 66)
        self.assertEqual(len(dados["aliquotas"]), 1014)
        self.assertGreater(len(dados["tabela_aliquotas"]), 8000)

        # Verifica linha TBRA x ITIS (linha 15) — Outubro/2026 e acumulados AR/AS/AT/AU
        tbra_itis = next(r for r in dados["resumo"] if r["cruzamento"] == "TBRA x ITIS")
        self.assertEqual(tbra_itis["competencia"], "10/2026")
        self.assertEqual(tbra_itis["responsavel"], "Mayara")
        self.assertAlmostEqual(tbra_itis["out_inef_trib"], -2888494.16, places=2)
        self.assertAlmostEqual(tbra_itis["out_diferenca"], 2067216.55, places=2)
        self.assertAlmostEqual(tbra_itis["out_inef_liq"], -821277.61, places=2)
        self.assertAlmostEqual(tbra_itis["acum_inef_trib_ar"], -17225271.19, places=2)
        self.assertAlmostEqual(tbra_itis["acum_diferenca_as"], 9962545.51, places=2)
        self.assertAlmostEqual(tbra_itis["acum_inef_liq_at"], -7262725.68, places=2)
        self.assertEqual(tbra_itis["sugestao_diferenca_au"], "Receita Bruta maior que Despesa")

        # Verifica CLOUD x VSCD (linha 4)
        cloud_vscd = next(r for r in dados["resumo"] if r["cruzamento"] == "CLOUD x VSCD")
        self.assertAlmostEqual(cloud_vscd["out_diferenca"], 51442.24, places=2)
        self.assertAlmostEqual(cloud_vscd["acum_diferenca_as"], -186250.44, places=2)
        self.assertEqual(cloud_vscd["sugestao_diferenca_au"], "Despesa maior que Receita Bruta")

        # Verifica parsing contábil brasileiro ' (0,85)' em TERRA x VALE (VSS) (Abril)
        terra_vale = next(r for r in dados["resumo"] if r["cruzamento"] == "TERRA x VALE (VSS)")
        self.assertAlmostEqual(terra_vale["abr_inef_trib"], -0.85, places=2)
        self.assertAlmostEqual(terra_vale["acum_inef_trib_ar"], -19.26, places=2)
        self.assertAlmostEqual(terra_vale["acum_diferenca_as"], 0.01, places=2)
        self.assertEqual(terra_vale["sugestao_diferenca_au"], "Receita Bruta maior que Despesa")

        # Verifica higienização de espaços em TBRA x I2GO e VSCD x VPY3
        tbra_i2go = next(r for r in dados["resumo"] if r["cruzamento"] == "TBRA x I2GO")
        self.assertEqual(tbra_i2go["responsavel"], "Thais")
        vscd_vpy3 = next(r for r in dados["resumo"] if r["cruzamento"] == "VSCD x VPY3")
        self.assertEqual(vscd_vpy3["responsavel"], "Beatriz")
        self.assertAlmostEqual(vscd_vpy3["acum_inef_trib_ar"], -9207.05, places=2)

        # Verifica função de carga padrão
        self.assertEqual(len(carregar_dados_iniciais_resultado()), 29)

    def test_filtro_calendario_patrimonial_restaurado(self):
        import types
        from datetime import date
        sys.modules.setdefault("streamlit", types.ModuleType("streamlit"))
        import app as painel_app

        self.assertTrue(painel_app.registro_dentro_filtro_data("08/2026", (date(2026, 8, 1), date(2026, 8, 31))))
        self.assertTrue(painel_app.registro_dentro_filtro_data("08/2026", (date(2026, 8, 15), date(2026, 9, 10))))
        self.assertFalse(painel_app.registro_dentro_filtro_data("08/2026", (date(2026, 9, 1), date(2026, 9, 30))))
        self.assertTrue(painel_app.registro_dentro_filtro_data("08/2026", ()))

    def test_metricas_resultado_colunas_ar_as_at_au(self):
        calc_pos = calcular_metricas_resultado(
            -2888494.16,
            2067216.55,
            dif_acumulada_mes_anterior=7895328.96,
            inef_trib_acumulada_mes_anterior=-14336777.03,
        )
        self.assertAlmostEqual(calc_pos["inef_liquida"], -821277.61, places=2)
        self.assertAlmostEqual(calc_pos["acum_inef_trib_ar"], -17225271.19, places=2)
        self.assertAlmostEqual(calc_pos["acum_diferenca_as"], 9962545.51, places=2)
        self.assertAlmostEqual(calc_pos["acum_inef_liq_at"], -7262725.68, places=2)
        self.assertEqual(calc_pos["sugestao_diferenca_au"], "Receita Bruta maior que Despesa")

        calc_neg = calcular_metricas_resultado(-58620.06, 3578.98, dif_acumulada_mes_anterior=-860859.01)
        self.assertAlmostEqual(calc_neg["acum_diferenca_as"], -857280.03, places=2)
        self.assertEqual(calc_neg["sugestao_diferenca_au"], "Despesa maior que Receita Bruta")

        calc_zero = calcular_metricas_resultado(0.0, 0.0, dif_acumulada_mes_anterior=0.0)
        self.assertEqual(calc_zero["sugestao_diferenca_au"], "Sem Diferença")

        # Recálculo anual completo
        linha = {
            "set_inef_trib": -100.0,
            "set_diferenca": 40.0,
            "out_inef_trib": -50.0,
            "out_diferenca": -10.0,
        }
        recalcular_linha_resultado_anual(linha)
        self.assertAlmostEqual(linha["set_inef_liq"], -60.0, places=2)
        self.assertAlmostEqual(linha["out_inef_liq"], -60.0, places=2)
        self.assertAlmostEqual(linha["acum_inef_trib_ar"], -150.0, places=2)
        self.assertAlmostEqual(linha["acum_diferenca_as"], 30.0, places=2)
        self.assertAlmostEqual(linha["acum_inef_liq_at"], -120.0, places=2)
        self.assertEqual(linha["sugestao_diferenca_au"], "Receita Bruta maior que Despesa")

    def test_validador_totais_resultado_silver(self):
        res = validar_totais_resultado_silver(
            35901920.79, 4395972.02, 40297892.81,
            35901920.79, 4395972.02, 40297892.81,
        )
        self.assertEqual(res["status_validador"], "Validado")
        self.assertEqual(res["check_rec_liq"], "OK Rec Liq")

    def test_item9_regras_camada_silver_e_quadro_sintetico(self):
        # 1. Aba Eliminação x CompFinal
        ok_res = classificar_item9_eliminacao_x_compfinal(1165497.36, 1165497.36)
        self.assertEqual(ok_res["diferenca"], 0.0)
        self.assertEqual(ok_res["resultado_analise"], "Sucesso")

        div_res = classificar_item9_eliminacao_x_compfinal(5326521.70, 5333462.99)
        self.assertAlmostEqual(div_res["diferenca"], -6941.29, places=2)
        self.assertEqual(div_res["resultado_analise"], "Requer Análise")

        # 2. Aba Expurgadas_CompFinal
        self.assertEqual(classificar_item9_expurgadas_compfinal("Não Eliminável"), "Sucesso")
        self.assertEqual(classificar_item9_expurgadas_compfinal("Eliminável"), "Requer Análise")

        # 3. Aba Somente_CompFinal e Somente_Eliminacao
        self.assertEqual(classificar_item9_somente_compfinal(0.0), "Sucesso")
        self.assertEqual(classificar_item9_somente_compfinal(180637.43), "Requer Análise")
        self.assertEqual(classificar_item9_somente_eliminacao(0.0), "Sucesso")
        self.assertEqual(classificar_item9_somente_eliminacao(-17261.71), "Requer Análise")

        # 4. Quadro Sintético das 4 abas
        dados_i9 = carregar_dados_iniciais_item9_patrimonial()
        quadro = gerar_quadro_sintetico_item9(dados_i9)
        self.assertEqual(len(quadro), 4)
        self.assertEqual(quadro[0]["aba_relatorio"], "Eliminação x CompFinal")
        self.assertEqual(quadro[0]["total_registros"], 18)
        self.assertEqual(quadro[0]["qtd_sucesso"], 17)
        self.assertEqual(quadro[0]["qtd_requer_analise"], 1)


if __name__ == "__main__":
    unittest.main()
