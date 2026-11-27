"""Extracao segura de anexos compactados."""

from pathlib import Path
import shutil
from zipfile import ZipFile


def extrair_e_remover_zip(caminho_zip: Path) -> list[Path]:
	"""Extrai o ZIP na pasta atual, remove o ZIP apos sucesso e retorna os arquivos extraidos."""
	pasta_original = caminho_zip.parent
	pasta_destino = pasta_original.resolve()
	arquivos_extraidos: list[Path] = []
	with ZipFile(caminho_zip) as arquivo_zip:
		membros = arquivo_zip.infolist()
		caminhos = []
		for membro in membros:
			caminho = (pasta_destino / membro.filename).resolve()
			if caminho != pasta_destino and pasta_destino not in caminho.parents:
				raise ValueError(f"Caminho invalido dentro do ZIP: {membro.filename}")
			if caminho == pasta_destino and not membro.is_dir():
				raise ValueError(f"Nome de arquivo invalido dentro do ZIP: {membro.filename}")
			caminhos.append(caminho)

		for membro, caminho in zip(membros, caminhos):
			if membro.is_dir():
				caminho.mkdir(parents=True, exist_ok=True)
				continue
			if caminho.exists():
				continue
			caminho.parent.mkdir(parents=True, exist_ok=True)
			with arquivo_zip.open(membro) as origem, caminho.open("wb") as destino:
				shutil.copyfileobj(origem, destino)
			arquivos_extraidos.append(pasta_original / caminho.relative_to(pasta_destino))

	caminho_zip.unlink()
	return arquivos_extraidos
