import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from zipfile import ZipFile

PROJETO_DIR = Path(__file__).resolve().parents[1]
if str(PROJETO_DIR) not in sys.path:
	sys.path.insert(0, str(PROJETO_DIR))

ARQUIVO_MODULO = PROJETO_DIR / "acessar-validator.py"
ESPECIFICACAO = importlib.util.spec_from_file_location("acessar_validator", ARQUIVO_MODULO)
NAVIGATOR = importlib.util.module_from_spec(ESPECIFICACAO)
ESPECIFICACAO.loader.exec_module(NAVIGATOR)


class NavigatorTests(unittest.TestCase):
	def setUp(self):
		self.pasta_origem_original = NAVIGATOR.PASTA_ORIGEM
		self.pasta_destino_original = NAVIGATOR.PASTA_DESTINO

	def tearDown(self):
		NAVIGATOR.PASTA_ORIGEM = self.pasta_origem_original
		NAVIGATOR.PASTA_DESTINO = self.pasta_destino_original

	def test_pasta_destino_e_extensoes_padrao(self):
		self.assertEqual(
			NAVIGATOR.PASTA_DESTINO,
			Path(r"\\brtssisp003\bbb0133$\2 - Intercompany"),
		)
		self.assertEqual(
			NAVIGATOR.EXTENSOES_PERMITIDAS,
			{".xls", ".xlsx", ".csv", ".xlsm", ".zip"},
		)

	def test_analisar_nomes_reais_do_navigator(self):
		casos = [
			(
				"ANS SF - 005_Composições finais de saldos patrimoniais e resultado intercompany_07_2026.xlsx",
				{"mes": "07", "ano": "2026"},
			),
			(
				"ANS SF - 006_Conciliações entre os saldos contábeis (a pagar e a receber) das empresas intercompanies_06_2026.xlsx",
				{"mes": "06", "ano": "2026"},
			),
			(
				"ANS SF - 006_Conciliações entre os saldos contábeis (a pagar e a receber) das empresas intercompanies_06_2026_v1.xlsx",
				{"mes": "06", "ano": "2026"},
			),
			(
				"ans sf - 006_conciliações entre os saldos contábeis (a pagar e a receber) das empresas intercompanies_06_2026_20260821_092214.xlsx",
				{"mes": "06", "ano": "2026"},
			),
			(
				"ANS SF - 007_QRs com os saldos das empresas intercompanies Telefônica_07_2026.xlsx",
				{"mes": "07", "ano": "2026"},
			),
			(
				"Volume SF - 007 Quantidade de partidas classificadas e conciliadas (Conciliacao Intercompany) - 07_2026.xlsm",
				{"mes": "07", "ano": "2026"},
			),
			(
				"Volume SF_014 Quantidade de partidas Identificadas, conferidas e analisadas_07_2026.xlsx",
				{"mes": "07", "ano": "2026"},
			),
			(
				"Volume SF_014 Quantidade de partidas Identificadas, conferidas e analisadas_07_2026_Resumo.csv",
				{"mes": "07", "ano": "2026"},
			),
			(
				"VOLUME SF_014 RESUMO_8_2026.xls",
				{"mes": "08", "ano": "2026"},
			),
		]
		for nome, esperado in casos:
			with self.subTest(nome=nome):
				self.assertEqual(NAVIGATOR.analisar_nome_arquivo(nome), esperado)

	def test_rejeita_arquivos_fora_do_padrao_e_extensoes_invalidas(self):
		invalidos = [
			"ANS SF - 005_07_2026.pdf",
			"ANS SF - 005_07_2026.xlsx.crdownload",
			"~$ANS SF - 005_07_2026.xlsx",
			"ANS SF - 005.xlsx",
			"0185_x_0024_TBRA_x_TID_10_2026.xlsm",
			"relatorio_qualquer_07_2026.xlsx",
		]
		for nome in invalidos:
			with self.subTest(nome=nome):
				self.assertIsNone(NAVIGATOR.analisar_nome_arquivo(nome))

	def test_move_arquivos_e_organiza_versoes_anteriores(self):
		with tempfile.TemporaryDirectory() as diretorio:
			origem = Path(diretorio) / "downloads"
			destino = Path(diretorio) / "rede"
			origem.mkdir()
			destino.mkdir()

			base_006 = "ANS SF - 006_Conciliações_06_2026.xlsx"
			v1_006 = "ANS SF - 006_Conciliações_06_2026_v1.xlsx"
			ans_005 = "ANS SF - 005_Composições_07_2026.xlsx"
			ignorado = "0185_x_0024_TBRA_x_TID_10_2026.xlsm"

			(origem / base_006).write_bytes(b"v0")
			(origem / v1_006).write_bytes(b"v1")
			(origem / ans_005).write_bytes(b"005")
			(origem / ignorado).write_bytes(b"conciliacao")

			NAVIGATOR.PASTA_ORIGEM = origem
			NAVIGATOR.PASTA_DESTINO = destino

			salvos = NAVIGATOR.mover_arquivos_navigator()

			self.assertEqual(len(salvos), 3)
			pasta_06 = destino / "ACCENTURE_NAVIGATOR" / "2026" / "06_2026"
			pasta_07 = destino / "ACCENTURE_NAVIGATOR" / "2026" / "07_2026"

			self.assertTrue((pasta_06 / v1_006).is_file())
			self.assertFalse((pasta_06 / base_006).exists())
			self.assertTrue((pasta_06 / "Versões Anteriores" / base_006).is_file())
			self.assertTrue((pasta_07 / ans_005).is_file())
			self.assertTrue((pasta_07 / "Versões Anteriores").is_dir())

			self.assertFalse((origem / base_006).exists())
			self.assertFalse((origem / v1_006).exists())
			self.assertFalse((origem / ans_005).exists())
			self.assertTrue((origem / ignorado).is_file())

	def test_arquivo_com_mesmo_nome_arquiva_anterior_em_versoes_anteriores(self):
		with tempfile.TemporaryDirectory() as diretorio:
			origem = Path(diretorio) / "downloads"
			destino = Path(diretorio) / "rede"
			origem.mkdir()
			pasta_07 = destino / "ACCENTURE_NAVIGATOR" / "2026" / "07_2026"
			pasta_07.mkdir(parents=True)

			nome = "ANS SF - 005_Composições_07_2026.xlsx"
			(pasta_07 / nome).write_bytes(b"antigo")
			(origem / nome).write_bytes(b"novo")

			salvos = NAVIGATOR.mover_arquivos_navigator(origem, destino)

			self.assertEqual(
				[item.replace("\\", "/") for item in salvos],
				[f"ACCENTURE_NAVIGATOR/2026/07_2026/{nome}"],
			)
			self.assertEqual((pasta_07 / nome).read_bytes(), b"novo")
			self.assertEqual(
				(pasta_07 / "Versões Anteriores" / nome).read_bytes(),
				b"antigo",
			)

	def test_descompacta_zip_antes_de_mover_e_remove_zip_processado(self):
		with tempfile.TemporaryDirectory() as diretorio:
			origem = Path(diretorio) / "downloads"
			destino = Path(diretorio) / "rede"
			origem.mkdir()
			destino.mkdir()

			zip_sharepoint = origem / "OneDrive_1_25-11-2026.zip"
			with ZipFile(zip_sharepoint, "w") as zf:
				zf.writestr("07/ANS SF - 007_QRs_07_2026.xlsx", b"qrs")
				zf.writestr(
					"07/Volume SF_014 Quantidade de partidas_07_2026.xlsx",
					b"vol014",
				)

			zip_unrelated = origem / "outro_arquivo.zip"
			with ZipFile(zip_unrelated, "w") as zf:
				zf.writestr("manual.pdf", b"pdf")

			salvos = NAVIGATOR.mover_arquivos_navigator(origem, destino)

			self.assertEqual(
				[item.replace("\\", "/") for item in salvos],
				[
					"ACCENTURE_NAVIGATOR/2026/07_2026/ANS SF - 007_QRs_07_2026.xlsx",
					"ACCENTURE_NAVIGATOR/2026/07_2026/Volume SF_014 Quantidade de partidas_07_2026.xlsx",
				],
			)
			pasta_07 = destino / "ACCENTURE_NAVIGATOR" / "2026" / "07_2026"
			self.assertEqual((pasta_07 / "ANS SF - 007_QRs_07_2026.xlsx").read_bytes(), b"qrs")
			self.assertEqual(
				(pasta_07 / "Volume SF_014 Quantidade de partidas_07_2026.xlsx").read_bytes(),
				b"vol014",
			)
			self.assertFalse(zip_sharepoint.exists())
			self.assertTrue(zip_unrelated.is_file())

	def test_zip_misto_move_apenas_arquivos_do_navigator_e_preserva_zip(self):
		with tempfile.TemporaryDirectory() as diretorio:
			origem = Path(diretorio) / "downloads"
			destino = Path(diretorio) / "rede"
			origem.mkdir()
			destino.mkdir()

			zip_misto = origem / "pacote_misto.zip"
			with ZipFile(zip_misto, "w") as zf:
				zf.writestr("ANS SF - 005_07_2026.xlsx", b"ans005")
				zf.writestr("nao_mover.pdf", b"pdf")

			salvos = NAVIGATOR.mover_arquivos_navigator(origem, destino)

			self.assertEqual(len(salvos), 1)
			self.assertTrue(
				(destino / "ACCENTURE_NAVIGATOR" / "2026" / "07_2026" / "ANS SF - 005_07_2026.xlsx").is_file()
			)
			self.assertTrue(zip_misto.is_file())

	def test_erro_quando_pasta_origem_nao_existe(self):
		with tempfile.TemporaryDirectory() as diretorio:
			origem_inexistente = Path(diretorio) / "nao_existe"
			destino = Path(diretorio) / "rede"
			with self.assertRaises(FileNotFoundError):
				NAVIGATOR.mover_arquivos_navigator(origem_inexistente, destino)


if __name__ == "__main__":
	unittest.main()

