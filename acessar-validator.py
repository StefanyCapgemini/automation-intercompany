"""Move planilhas do Navigator baixadas para a pasta de rede."""

from pathlib import Path
import re
import shutil
import tempfile
from zipfile import BadZipFile, ZipFile
from company_folder import PASTA_VERSOES_ANTERIORES, organizar_versoes


PASTA_ORIGEM = Path.home() / "Downloads"
PASTA_DESTINO = Path(r"\\brtssisp003\bbb0133$\2 - Intercompany")
PASTA_NAVIGATOR = "ACCENTURE_NAVIGATOR"
EXTENSOES_PERMITIDAS = {".xls", ".xlsx", ".csv", ".xlsm", ".zip"}
EXTENSOES_ARQUIVOS = EXTENSOES_PERMITIDAS - {".zip"}

PREFIXO_NAVIGATOR = re.compile(
	r"^(?:ANS|VOL(?:UME)?\.?)[\s_]+SF(?:\s*[-–_]\s*|\s+)\d{3}(?!\d)",
	re.IGNORECASE,
)
COMPETENCIA_ARQUIVO = re.compile(
	r"(?<!\d)(?P<mes>0?[1-9]|1[0-2])[_/-](?P<ano>\d{4})(?!\d)"
)
IGNORAR_NO_ZIP = {"thumbs.db", "desktop.ini", ".ds_store"}


class ListaArquivosSalvos(list):
	"""Lista de arquivos salvos com formatação legível para o log."""

	def __str__(self) -> str:
		if not self:
			return "0\nNenhum arquivo novo foi salvo."
		linhas = "\n".join(f"- {arquivo}" for arquivo in self)
		return f"{len(self)}\n{linhas}"


def analisar_nome_arquivo(
	nome: str,
	permitir_zip: bool = False,
) -> dict[str, str] | None:
	"""Valida extensão, prefixo do Navigator e extrai competência (mm/yyyy)."""
	arquivo = Path(nome)
	extensoes = EXTENSOES_PERMITIDAS if permitir_zip else EXTENSOES_ARQUIVOS
	if arquivo.suffix.lower() not in extensoes:
		return None

	stem = arquivo.stem.strip()
	if not PREFIXO_NAVIGATOR.match(stem):
		return None

	correspondencia = COMPETENCIA_ARQUIVO.search(stem)
	if not correspondencia:
		return None

	return {
		"mes": correspondencia.group("mes").zfill(2),
		"ano": correspondencia.group("ano"),
	}


def obter_pasta_destino(
	dados: dict[str, str],
	pasta_destino: Path | None = None,
) -> Path:
	"""Monta a pasta de destino ACCENTURE_NAVIGATOR\\yyyy\\mm_yyyy."""
	destino_base = PASTA_DESTINO if pasta_destino is None else Path(pasta_destino)
	return destino_base / PASTA_NAVIGATOR / dados["ano"] / f"{dados['mes']}_{dados['ano']}"


def _arquivar_em_versoes_anteriores(arquivo: Path, pasta_competencia: Path) -> Path:
	pasta_anteriores = pasta_competencia / PASTA_VERSOES_ANTERIORES
	pasta_anteriores.mkdir(exist_ok=True)
	destino = pasta_anteriores / arquivo.name
	contador = 1
	while destino.exists():
		destino = pasta_anteriores / f"{arquivo.stem}_{contador}{arquivo.suffix}"
		contador += 1
	shutil.move(str(arquivo), str(destino))
	return destino


def _mover_arquivo_para_competencia(
	origem: Path,
	dados: dict[str, str],
	destino_base: Path,
) -> str:
	pasta_competencia = obter_pasta_destino(dados, destino_base)
	pasta_competencia.mkdir(parents=True, exist_ok=True)
	(pasta_competencia / PASTA_VERSOES_ANTERIORES).mkdir(exist_ok=True)

	destino = pasta_competencia / origem.name
	if destino.exists():
		_arquivar_em_versoes_anteriores(destino, pasta_competencia)

	shutil.move(str(origem), str(destino))
	organizar_versoes(pasta_competencia)

	if destino.is_file():
		return str(destino.relative_to(destino_base))
	return str((pasta_competencia / PASTA_VERSOES_ANTERIORES / origem.name).relative_to(destino_base))


def _membro_ignorado(caminho_membro: str) -> bool:
	partes = Path(caminho_membro).parts
	if any(parte == "__MACOSX" for parte in partes):
		return True
	return Path(caminho_membro).name.lower() in IGNORAR_NO_ZIP


def _processar_zip(caminho_zip: Path, destino_base: Path) -> list[str]:
	"""Descompacta arquivos válidos do Navigator antes de movê-los para a rede."""
	try:
		with ZipFile(caminho_zip) as arquivo_zip:
			membros_validos = []
			possui_outros_arquivos = False

			for membro in arquivo_zip.infolist():
				if membro.is_dir() or _membro_ignorado(membro.filename):
					continue
				nome = Path(membro.filename).name
				if not nome or nome in (".", ".."):
					continue

				dados = analisar_nome_arquivo(nome, permitir_zip=False)
				if dados is None:
					possui_outros_arquivos = True
					continue
				membros_validos.append((membro, nome, dados))

			if not membros_validos:
				return []

			arquivos_salvos: list[str] = []
			with tempfile.TemporaryDirectory() as diretorio_temporario:
				pasta_temp = Path(diretorio_temporario)
				for indice, (membro, nome, dados) in enumerate(membros_validos):
					subpasta = pasta_temp / str(indice)
					subpasta.mkdir()
					caminho_extraido = subpasta / nome
					with arquivo_zip.open(membro) as origem, caminho_extraido.open("wb") as destino:
						shutil.copyfileobj(origem, destino)
					arquivos_salvos.append(
						_mover_arquivo_para_competencia(caminho_extraido, dados, destino_base)
					)
	except BadZipFile:
		return []

	if not possui_outros_arquivos:
		caminho_zip.unlink()

	return arquivos_salvos


def mover_arquivos_navigator(
	pasta_origem: Path | None = None,
	pasta_destino: Path | None = None,
) -> ListaArquivosSalvos:
	"""Move arquivos válidos do Navigator da pasta local para a rede."""
	origem_base = PASTA_ORIGEM if pasta_origem is None else Path(pasta_origem)
	destino_base = PASTA_DESTINO if pasta_destino is None else Path(pasta_destino)

	if not origem_base.is_dir():
		raise FileNotFoundError(f"Pasta de origem não encontrada: {origem_base}")

	arquivos_salvos = ListaArquivosSalvos()
	for arquivo in sorted(origem_base.iterdir(), key=lambda item: item.name.casefold()):
		if not arquivo.is_file():
			continue

		extensao = arquivo.suffix.lower()
		if extensao not in EXTENSOES_PERMITIDAS:
			continue

		if extensao == ".zip":
			arquivos_salvos.extend(_processar_zip(arquivo, destino_base))
			continue

		dados = analisar_nome_arquivo(arquivo.name, permitir_zip=False)
		if dados is None:
			continue

		arquivos_salvos.append(
			_mover_arquivo_para_competencia(arquivo, dados, destino_base)
		)

	return arquivos_salvos


acessar_navigator = mover_arquivos_navigator


if __name__ == "__main__":
	arquivos_salvos = mover_arquivos_navigator()
	print(f"Arquivos salvos: {len(arquivos_salvos)}")
	for arquivo in arquivos_salvos:
		print(f"- {arquivo}")
