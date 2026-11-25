import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

PROJETO_DIR = Path(__file__).resolve().parents[1]
if str(PROJETO_DIR) not in sys.path:
	sys.path.insert(0, str(PROJETO_DIR))

ARQUIVO_MODULO = PROJETO_DIR / "conciliacao-intercompany.py"
ESPECIFICACAO = importlib.util.spec_from_file_location("conciliacao_intercompany", ARQUIVO_MODULO)
CONCILIACAO = importlib.util.module_from_spec(ESPECIFICACAO)
ESPECIFICACAO.loader.exec_module(CONCILIACAO)


class ConciliacaoIntercompanyTests(unittest.TestCase):
	def setUp(self):
		self.pasta_origem_original = CONCILIACAO.PASTA_ORIGEM
		self.pasta_destino_original = CONCILIACAO.PASTA_DESTINO

	def tearDown(self):
		CONCILIACAO.PASTA_ORIGEM = self.pasta_origem_original
		CONCILIACAO.PASTA_DESTINO = self.pasta_destino_original

	def test_pasta_destino_padrao_rede(self):
		self.assertEqual(
			CONCILIACAO.PASTA_DESTINO,
			Path(r"\\brtssisp003\bbb0133$\2 - Intercompany"),
		)

	def test_extensoes_permitidas(self):
		self.assertEqual(
			CONCILIACAO.EXTENSOES_PERMITIDAS,
			{".xls", ".xlsx", ".csv", ".xlsm", ".zip"},
		)

	def test_analisar_nome_arquivo_exemplo_padrao(self):
		dados = CONCILIACAO.analisar_nome_arquivo("0185_x_0024_TBRA_x_TID_10_2026.xlsm")
		self.assertEqual(
			dados,
			{
				"codigo1": "0185",
				"codigo2": "0024",
				"empresa1": "TBRA",
				"empresa2": "TID",
				"mes": "10",
				"ano": "2026",
				"versao": None,
			},
		)

	def test_analisar_nome_arquivo_normaliza_mes_e_caixa(self):
		dados = CONCILIACAO.analisar_nome_arquivo("0306_X_0185_tis_X_tbra_8_2026_V2.XLSX")
		self.assertEqual(
			dados,
			{
				"codigo1": "0306",
				"codigo2": "0185",
				"empresa1": "TIS",
				"empresa2": "TBRA",
				"mes": "08",
				"ano": "2026",
				"versao": "2",
			},
		)

	def test_rejeita_extensoes_nao_permitidas_e_nomes_invalidos(self):
		invalidos = [
			"0185_x_0024_TBRA_x_TID_10_2026.pdf",
			"0185_x_0024_TBRA_x_TID_10_2026.txt",
			"0185_x_0024_TBRA_x_TID_10_2026.xlsm.crdownload",
			"~$0185_x_0024_TBRA_x_TID_10_2026.xlsm",
			"0185_x_0024_TBRA_x_TID_13_2026.xlsm",
			"0185_x_0024_TBRA_x_TID_00_2026.xlsm",
			"arquivo_aleatorio.xlsx",
		]
		for nome in invalidos:
			with self.subTest(nome=nome):
				self.assertIsNone(CONCILIACAO.analisar_nome_arquivo(nome))

	def test_mover_arquivos_conciliacao_para_destinos_corretos(self):
		with tempfile.TemporaryDirectory() as diretorio:
			origem = Path(diretorio) / "downloads"
			destino = Path(diretorio) / "rede"
			origem.mkdir()
			destino.mkdir()

			arquivos_validos = [
				"0185_x_0024_TBRA_x_TID_10_2026.xlsm",
				"0306_x_0185_TIS_x_TBRA_09_2026.xlsx",
				"1872_x_0185_RECICLA V_x_TBRA_10_2026.xls",
				"2207_x_0185_VSS_x_TBRA_10_2026.csv",
				"0999_x_0185_TGLOG_x_TBRA_10_2026.zip",
			]
			arquivos_ignorados = [
				"0185_x_0024_TBRA_x_TID_10_2026.pdf",
				"nota_pessoal.xlsx",
			]

			for nome in arquivos_validos + arquivos_ignorados:
				(origem / nome).write_bytes(nome.encode("utf-8"))

			CONCILIACAO.PASTA_ORIGEM = origem
			CONCILIACAO.PASTA_DESTINO = destino

			salvos = CONCILIACAO.mover_arquivos_conciliacao()

			esperados = [
				"ANO_2026/10_2026/CONCILIAÇÕES INTERCOMPANY/0185-TBRA/0185_x_0024_TBRA_x_TID_10_2026.xlsm",
				"ANO_2026/09_2026/CONCILIAÇÕES INTERCOMPANY/0306-TIS/0306_x_0185_TIS_x_TBRA_09_2026.xlsx",
				"ANO_2026/10_2026/CONCILIAÇÕES INTERCOMPANY/0999-TGLOG/0999_x_0185_TGLOG_x_TBRA_10_2026.zip",
				"ANO_2026/10_2026/CONCILIAÇÕES INTERCOMPANY/1872-RECICLA V/1872_x_0185_RECICLA V_x_TBRA_10_2026.xls",
				"ANO_2026/10_2026/CONCILIAÇÕES INTERCOMPANY/2207-VSS/2207_x_0185_VSS_x_TBRA_10_2026.csv",
			]
			self.assertEqual([item.replace("\\", "/") for item in salvos], esperados)
			self.assertEqual(len(salvos), 5)

			for nome in arquivos_validos:
				self.assertFalse((origem / nome).exists())
			for nome in arquivos_ignorados:
				self.assertTrue((origem / nome).is_file())

			arquivo_exemplo = (
				destino
				/ "ANO_2026"
				/ "10_2026"
				/ "CONCILIAÇÕES INTERCOMPANY"
				/ "0185-TBRA"
				/ "0185_x_0024_TBRA_x_TID_10_2026.xlsm"
			)
			self.assertTrue(arquivo_exemplo.is_file())
			self.assertEqual(
				arquivo_exemplo.read_bytes(),
				b"0185_x_0024_TBRA_x_TID_10_2026.xlsm",
			)

	def test_sobrescreve_arquivo_existente_no_destino(self):
		with tempfile.TemporaryDirectory() as diretorio:
			origem = Path(diretorio) / "downloads"
			destino = Path(diretorio) / "rede"
			origem.mkdir()
			pasta_existente = (
				destino / "ANO_2026" / "10_2026" / "CONCILIAÇÕES INTERCOMPANY" / "0185-TBRA"
			)
			pasta_existente.mkdir(parents=True)
			nome = "0185_x_0024_TBRA_x_TID_10_2026.xlsm"
			(pasta_existente / nome).write_bytes(b"versao antiga")
			(origem / nome).write_bytes(b"versao nova")

			salvos = CONCILIACAO.mover_arquivos_conciliacao(origem, destino)

			self.assertEqual(len(salvos), 1)
			self.assertFalse((origem / nome).exists())
			self.assertEqual((pasta_existente / nome).read_bytes(), b"versao nova")

	def test_retorna_lista_vazia_quando_nao_ha_arquivos_validos(self):
		with tempfile.TemporaryDirectory() as diretorio:
			origem = Path(diretorio) / "downloads"
			destino = Path(diretorio) / "rede"
			origem.mkdir()
			destino.mkdir()
			(origem / "outro.pdf").write_bytes(b"pdf")

			salvos = CONCILIACAO.mover_arquivos_conciliacao(origem, destino)

			self.assertEqual(salvos, [])
			self.assertIn("Nenhum arquivo novo foi salvo.", str(salvos))

	def test_erro_quando_pasta_origem_nao_existe(self):
		with tempfile.TemporaryDirectory() as diretorio:
			origem_inexistente = Path(diretorio) / "nao_existe"
			destino = Path(diretorio) / "rede"
			with self.assertRaises(FileNotFoundError):
				CONCILIACAO.mover_arquivos_conciliacao(origem_inexistente, destino)


if __name__ == "__main__":
	unittest.main()

