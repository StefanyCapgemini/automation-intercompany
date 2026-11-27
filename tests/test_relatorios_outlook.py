import importlib.util
from io import BytesIO
from pathlib import Path
import sys
import tempfile
import types
import unittest
from zipfile import ZipFile

if "pythoncom" not in sys.modules:
	sys.modules["pythoncom"] = types.ModuleType("pythoncom")
if "win32com" not in sys.modules:
	win32com_mod = types.ModuleType("win32com")
	win32com_mod.client = types.ModuleType("win32com.client")
	sys.modules["win32com"] = win32com_mod
	sys.modules["win32com.client"] = win32com_mod.client

PROJETO_DIR = Path(__file__).resolve().parents[1]
if str(PROJETO_DIR) not in sys.path:
	sys.path.insert(0, str(PROJETO_DIR))


def _carregar(nome_modulo: str, arquivo: str):
	spec = importlib.util.spec_from_file_location(nome_modulo, PROJETO_DIR / arquivo)
	mod = importlib.util.module_from_spec(spec)
	spec.loader.exec_module(mod)
	return mod


PATRIMONIAL = _carregar("eliminacao_patrimonial", "eliminacao-patrimonial.py")
RESULTADO = _carregar("eliminacao_resultado", "eliminacao-resultado.py")
COMPOSICAO = _carregar("composicao_geral", "composicao-geral.py")


class _FakeAttachment:
	def __init__(self, filename: str, content: bytes):
		self.FileName = filename
		self._content = content

	def SaveAsFile(self, path: str) -> None:
		Path(path).write_bytes(self._content)


class _FakeMail:
	Class = 43

	def __init__(self, subject: str, attachments: list[_FakeAttachment]):
		self.Subject = subject
		self.Attachments = attachments


class _FakeItems(list):
	def Sort(self, *_args, **_kwargs):
		return None


class _FakeFolder:
	def __init__(self, mails: list[_FakeMail]):
		self.Items = _FakeItems(mails)


class _FakeNamespace:
	def __init__(self, mails: list[_FakeMail]):
		self._folder = _FakeFolder(mails)

	def GetDefaultFolder(self, _idx: int):
		return self._folder


class _FakeOutlookApp:
	def __init__(self, mails: list[_FakeMail]):
		self._ns = _FakeNamespace(mails)

	def GetNamespace(self, _name: str):
		return self._ns


def _criar_zip_bytes(arquivos: dict[str, bytes]) -> bytes:
	buf = BytesIO()
	with ZipFile(buf, "w") as zf:
		for nome, conteudo in arquivos.items():
			zf.writestr(nome, conteudo)
	return buf.getvalue()


class RelatoriosOutlookListaSalvosTests(unittest.TestCase):
	def _executar_com_emails(self, modulo, mails: list[_FakeMail], destino: Path):
		dest_orig = modulo.PASTA_DESTINO
		sync_orig = modulo.sincronizar_todas_as_pastas
		dispatch_orig = getattr(modulo.win32com.client, "Dispatch", None)
		try:
			modulo.PASTA_DESTINO = destino
			modulo.sincronizar_todas_as_pastas = lambda _ns: None
			modulo.win32com.client.Dispatch = lambda _prog: _FakeOutlookApp(mails)
			return modulo.salvar_anexos_dos_relatorios()
		finally:
			modulo.PASTA_DESTINO = dest_orig
			modulo.sincronizar_todas_as_pastas = sync_orig
			if dispatch_orig is None:
				delattr(modulo.win32com.client, "Dispatch")
			else:
				modulo.win32com.client.Dispatch = dispatch_orig

	def test_eliminacao_patrimonial_retorna_lista_arquivos_salvos_e_extraidos(self):
		with tempfile.TemporaryDirectory() as diretorio:
			destino = Path(diretorio)
			zip_bytes = _criar_zip_bytes({"Relatorio_Patrimonial_08_2026_V1.xlsx": b"zip-xlsx"})
			mails = [
				_FakeMail(
					"RELATÓRIO DE ELIMINAÇÃO PATRIMONIAL - TBRA (0185) x (0306) ITIS - 08/2026",
					[
						_FakeAttachment("Patrimonial_08_2026.xlsx", b"xlsx"),
						_FakeAttachment("Pacote_08_2026.zip", zip_bytes),
						_FakeAttachment("ignorar.pdf", b"pdf"),
					],
				)
			]

			salvos = self._executar_com_emails(PATRIMONIAL, mails, destino)

			self.assertIsInstance(salvos, list)
			self.assertEqual(
				[p.replace("\\", "/") for p in salvos],
				[
					"ANO_2026/08_2026/APLICATIVO ELIMINAÇÃO/Eliminação Patrimonial/0185 x 0306 - TBRA x ITIS/Patrimonial_08_2026.xlsx",
					"ANO_2026/08_2026/APLICATIVO ELIMINAÇÃO/Eliminação Patrimonial/0185 x 0306 - TBRA x ITIS/Relatorio_Patrimonial_08_2026_V1.xlsx",
				],
			)
			self.assertIn("2\n- ", str(salvos))

	def test_eliminacao_resultado_retorna_lista_arquivos_salvos(self):
		with tempfile.TemporaryDirectory() as diretorio:
			destino = Path(diretorio)
			mails = [
				_FakeMail(
					"RELATÓRIO DE ELIMINAÇÃO RESULTADO - TBRA (0185) x (0306) ITIS - 10/2026",
					[_FakeAttachment("Resultado_10_2026.xlsm", b"xlsm")],
				)
			]

			salvos = self._executar_com_emails(RESULTADO, mails, destino)

			self.assertIsInstance(salvos, list)
			self.assertEqual(
				[p.replace("\\", "/") for p in salvos],
				[
					"ANO_2026/10_2026/APLICATIVO ELIMINAÇÃO/Eliminação Resultado/0185 x 0306 - TBRA x ITIS/Resultado_10_2026.xlsm",
				],
			)
			# Segunda execução não salva novamente
			salvos_2 = self._executar_com_emails(RESULTADO, mails, destino)
			self.assertEqual(salvos_2, [])
			self.assertIn("Nenhum arquivo novo foi salvo.", str(salvos_2))

	def test_composicao_geral_retorna_lista_arquivos_salvos(self):
		with tempfile.TemporaryDirectory() as diretorio:
			destino = Path(diretorio)
			mails = [
				_FakeMail(
					"COMPOSIÇÃO DE SALDO PATRIMONIAL - TBRA (0185) - 10/2026",
					[_FakeAttachment("Composicao_TBRA_10_2026.xlsx", b"comp")],
				)
			]

			salvos = self._executar_com_emails(COMPOSICAO, mails, destino)

			self.assertIsInstance(salvos, list)
			self.assertEqual(
				[p.replace("\\", "/") for p in salvos],
				[
					"ANO_2026/10_2026/COMPOSIÇÃO DE SALDOS/0185-TBRA/Composicao_TBRA_10_2026.xlsx",
				],
			)


if __name__ == "__main__":
	unittest.main()

