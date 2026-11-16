from pathlib import Path
import sys
import unittest

PROJETO_DIR = Path(__file__).resolve().parents[1]
PAINEL_DIR = PROJETO_DIR / "databricks_painel"
if str(PAINEL_DIR) not in sys.path:
    sys.path.insert(0, str(PAINEL_DIR))

from excel_loader import (
    carregar_dados_iniciais_resultado,
    carregar_painel_patrimonial_xlsx,
)
from pipeline_silver_gold import (
    calcular_metricas_patrimonial,
    calcular_metricas_resultado,
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


if __name__ == "__main__":
    unittest.main()

