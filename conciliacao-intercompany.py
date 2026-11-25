"""Move planilhas de Conciliação Intercompany baixadas para a pasta de rede."""

from pathlib import Path
import re
import shutil


PASTA_ORIGEM = Path.home() / "Downloads"
PASTA_DESTINO = Path(r"\\brtssisp003\bbb0133$\2 - Intercompany")
PASTA_CONCILIACOES = "CONCILIAÇÕES INTERCOMPANY"
EXTENSOES_PERMITIDAS = {".xls", ".xlsx", ".csv", ".xlsm", ".zip"}

ARQUIVO_CONCILIACAO = re.compile(
	r"^(?P<codigo1>\d+)_x_(?P<codigo2>\d+)_"
	r"(?P<empresa1>.+?)_x_(?P<empresa2>.+?)_"
	r"(?P<mes>0?[1-9]|1[0-2])_(?P<ano>\d{4})"
	r"(?:[ _-]+V(?P<versao>\d+))?$",
	re.IGNORECASE,
)


class ListaArquivosSalvos(list):
	"""Lista de arquivos salvos com formatação legível para o log."""

	def __str__(self) -> str:
		if not self:
			return "0\nNenhum arquivo novo foi salvo."
		linhas = "\n".join(f"- {arquivo}" for arquivo in self)
		return f"{len(self)}\n{linhas}"


def _sanitizar_nome_pasta(valor: str) -> str:
	texto = " ".join(valor.split())
	return re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", texto).strip(" .")


def analisar_nome_arquivo(nome: str) -> dict[str, str | None] | None:
	"""Extrai códigos, empresas e competência do nome do arquivo de conciliação."""
	arquivo = Path(nome)
	if arquivo.suffix.lower() not in EXTENSOES_PERMITIDAS:
		return None

	correspondencia = ARQUIVO_CONCILIACAO.fullmatch(arquivo.stem.strip())
	if not correspondencia:
		return None

	dados = correspondencia.groupdict()
	empresa1 = _sanitizar_nome_pasta(dados["empresa1"]).upper()
	empresa2 = _sanitizar_nome_pasta(dados["empresa2"]).upper()
	if not empresa1 or not empresa2:
		return None

	return {
		"codigo1": dados["codigo1"],
		"codigo2": dados["codigo2"],
		"empresa1": empresa1,
		"empresa2": empresa2,
		"mes": dados["mes"].zfill(2),
		"ano": dados["ano"],
		"versao": dados["versao"],
	}


def obter_pasta_destino(
	dados: dict[str, str | None],
	pasta_destino: Path | None = None,
) -> Path:
	"""Monta a pasta de destino com base na competência, codigo1 e empresa1."""
	destino_base = PASTA_DESTINO if pasta_destino is None else Path(pasta_destino)
	return (
		destino_base
		/ f"ANO_{dados['ano']}"
		/ f"{dados['mes']}_{dados['ano']}"
		/ PASTA_CONCILIACOES
		/ f"{dados['codigo1']}-{dados['empresa1']}"
	)


def mover_arquivos_conciliacao(
	pasta_origem: Path | None = None,
	pasta_destino: Path | None = None,
) -> ListaArquivosSalvos:
	"""Move arquivos válidos de conciliação da pasta local para a rede."""
	origem_base = PASTA_ORIGEM if pasta_origem is None else Path(pasta_origem)
	destino_base = PASTA_DESTINO if pasta_destino is None else Path(pasta_destino)

	if not origem_base.is_dir():
		raise FileNotFoundError(f"Pasta de origem não encontrada: {origem_base}")

	arquivos_salvos = ListaArquivosSalvos()
	for arquivo in sorted(origem_base.iterdir(), key=lambda item: item.name.casefold()):
		if not arquivo.is_file():
			continue

		dados = analisar_nome_arquivo(arquivo.name)
		if dados is None:
			continue

		pasta_empresa = obter_pasta_destino(dados, destino_base)
		pasta_empresa.mkdir(parents=True, exist_ok=True)

		destino = pasta_empresa / arquivo.name
		shutil.move(str(arquivo), str(destino))
		arquivos_salvos.append(str(destino.relative_to(destino_base)))

	return arquivos_salvos


if __name__ == "__main__":
	arquivos_salvos = mover_arquivos_conciliacao()
	print(f"Arquivos salvos: {len(arquivos_salvos)}")
	for arquivo in arquivos_salvos:
		print(f"- {arquivo}")
