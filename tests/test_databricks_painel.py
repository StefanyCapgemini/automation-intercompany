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
)
from pipeline_silver_gold import (
    calcular_metricas_patrimonial,
    calcular_metricas_resultado,
    classificar_item9_eliminacao_x_compfinal,
    classificar_item9_expurgadas_compfinal,
    classificar_item9_somente_compfinal,
    classificar_item9_somente_eliminacao,
    gerar_quadro_sintetico_item9,
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

    def test_metricas_resultado_coluna_ar_e_as(self):
        calc_pos = calcular_metricas_resultado(1508218.85, 81784.08, dif_acumulada_mes_anterior=574350.87)
        self.assertAlmostEqual(calc_pos["inef_liquida"], 1590002.93, places=2)
        self.assertAlmostEqual(calc_pos["dif_real_acumulada_ar"], 656134.95, places=2)
        self.assertEqual(calc_pos["sugestao_diferenca_as"], "Receita Bruta maior que Despesa")

        calc_neg = calcular_metricas_resultado(-58620.06, 3578.98, dif_acumulada_mes_anterior=-860859.01)
        self.assertAlmostEqual(calc_neg["dif_real_acumulada_ar"], -857280.03, places=2)
        self.assertEqual(calc_neg["sugestao_diferenca_as"], "Despesa maior que Receita Bruta")

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

