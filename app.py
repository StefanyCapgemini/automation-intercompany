import asyncio
from datetime import datetime
import importlib.util
from pathlib import Path
import sys
import flet as ft
import pythoncom
import win32com.client
from outlook_sync import sincronizar_todas_as_pastas

PROJECT_DIR = Path(__file__).resolve().parent
if str(PROJECT_DIR) not in sys.path:
	sys.path.insert(0, str(PROJECT_DIR))

PRIMARY = "#5A189A"
PRIMARY_DARK = "#2B0A4E"
SURFACE = "#F7F7FA"
BORDER = "#E4E4EC"


def carregar_script(nome_modulo: str, nome_arquivo: str):
	caminho = PROJECT_DIR / nome_arquivo
	especificacao = importlib.util.spec_from_file_location(nome_modulo, caminho)
	if especificacao is None or especificacao.loader is None:
		raise ImportError(f"Nao foi possivel carregar {nome_arquivo}.")

	modulo = importlib.util.module_from_spec(especificacao)
	especificacao.loader.exec_module(modulo)
	return modulo


modulo_patrimonial = carregar_script("eliminacao_patrimonial", "eliminacao-patrimonial.py")
modulo_resultado = carregar_script("eliminacao_resultado", "eliminacao-resultado.py")
modulo_composicao = carregar_script("composicao_geral", "composicao-geral.py")
modulo_quadro_resumo = carregar_script(
	"quadro_resumo_patrimonial", "quadro-resumo-patrimonial.py"
)
modulo_conciliacao = carregar_script(
	"conciliacao_intercompany", "conciliacao-intercompany.py"
)
modulo_navigator = carregar_script(
	"acessar_validator", "acessar-validator.py"
)


def executar_com_com(funcao):
	pythoncom.CoInitialize()
	try:
		return funcao()
	finally:
		pythoncom.CoUninitialize()


def atualizar_caixa_de_entrada() -> None:
	namespace = win32com.client.Dispatch("Outlook.Application").GetNamespace("MAPI")
	sincronizar_todas_as_pastas(namespace)


def executar_navigator() -> list[str]:
	return modulo_navigator.mover_arquivos_navigator()


def executar_conciliacoes() -> list[str]:
	return modulo_conciliacao.mover_arquivos_conciliacao()


def criar_botao_acao(texto: str, icone, on_click=None, primary: bool = True) -> ft.Button:
	estilo = ft.ButtonStyle(
		shape=ft.RoundedRectangleBorder(radius=8),
		padding=ft.Padding.symmetric(horizontal=16, vertical=0),
		elevation=0,
		bgcolor=PRIMARY if primary else ft.Colors.WHITE,
		color=ft.Colors.WHITE if primary else PRIMARY,
		side=None if primary else ft.BorderSide(1, PRIMARY),
	)
	return ft.Button(
		content=ft.Row(
			[
				ft.Icon(icone, size=18),
				ft.Text(texto, size=13, weight=ft.FontWeight.W_500),
			],
			spacing=8,
			tight=True,
		),
		height=40,
		style=estilo,
		on_click=on_click,
	)


def main(page: ft.Page) -> None:
	page.title = "Automação Intercompany"
	page.theme_mode = ft.ThemeMode.LIGHT
	page.bgcolor = ft.Colors.WHITE
	page.padding = 32
	page.scroll = ft.ScrollMode.AUTO
	page.window.width = 960
	page.window.height = 720
	page.window.min_width = 760
	page.window.min_height = 580

	registros: list[str] = []
	botoes: list[ft.Button] = []
	ocupado = False

	texto_status = ft.Text("Pronto para iniciar", size=12, color="#285D4D", weight=ft.FontWeight.W_500)
	icone_status = ft.Icon(ft.Icons.CHECK_CIRCLE, size=16, color="#287A58")
	indicador_status = ft.Container(
		content=ft.Row([icone_status, texto_status], spacing=6, tight=True),
		bgcolor="#E5F2E9",
		border_radius=20,
		padding=ft.Padding.symmetric(horizontal=12, vertical=6),
	)
	progresso = ft.ProgressRing(visible=False, width=18, height=18, stroke_width=2, color=PRIMARY)

	caixa_log = ft.TextField(
		value="Aguardando a primeira ação.",
		multiline=True,
		read_only=True,
		min_lines=14,
		max_lines=18,
		text_style=ft.TextStyle(font_family="Cascadia Code", size=12, color="#2B0A4E"),
		border=ft.InputBorder.NONE,
		bgcolor=ft.Colors.TRANSPARENT,
		expand=True,
	)
	botao_limpar = ft.IconButton(
		icon=ft.Icons.DELETE_OUTLINE,
		icon_size=20,
		tooltip="Limpar log",
		icon_color=ft.Colors.GREY_600,
	)

	def atualizar_log(mensagem: str) -> None:
		horario = datetime.now().strftime("%H:%M:%S")
		registros.append(f"{horario}  {mensagem}")
		caixa_log.value = "\n".join(registros[-300:])

	def definir_status(mensagem: str, cor: str, fundo: str, icone) -> None:
		texto_status.value = mensagem
		texto_status.color = cor
		icone_status.icon = icone
		icone_status.color = cor
		indicador_status.bgcolor = fundo

	async def executar_acao(nome: str, funcao, usar_com: bool = True) -> None:
		nonlocal ocupado
		if ocupado:
			return

		ocupado = True
		for botao in botoes:
			botao.disabled = True
		botao_limpar.disabled = True
		progresso.visible = True
		definir_status(f"Executando: {nome}", "#8A5A12", "#FBF0DA", ft.Icons.SYNC)
		atualizar_log(f"Iniciando {nome.lower()}...")
		page.update()

		try:
			if usar_com:
				resultado = await asyncio.to_thread(executar_com_com, funcao)
			else:
				resultado = await asyncio.to_thread(funcao)

			if resultado is None:
				atualizar_log("Caixa de entrada atualizada.")
			elif isinstance(resultado, list):
				atualizar_log(f"Processamento concluido. Arquivos salvos: {len(resultado)}")
				if resultado:
					for arquivo in resultado:
						atualizar_log(f"- {arquivo}")
				else:
					atualizar_log("Nenhum arquivo novo foi salvo.")
			elif isinstance(resultado, str):
				atualizar_log(resultado)
			else:
				atualizar_log(f"Processamento concluido. Anexos salvos: {resultado}")
			definir_status("Concluído", "#285D4D", "#E5F2E9", ft.Icons.CHECK_CIRCLE)
		except Exception as erro:
			atualizar_log(f"Falha na operacao: {erro}")
			definir_status("A operação encontrou um erro", "#D32F2F", "#FFEBEE", ft.Icons.ERROR_OUTLINE)
		finally:
			ocupado = False
			for botao in botoes:
				botao.disabled = False
			botao_limpar.disabled = False
			progresso.visible = False
			page.update()

	async def clicar_patrimonial(_evento) -> None:
		await executar_acao(
			"Eliminação Patrimonial",
			modulo_patrimonial.salvar_anexos_dos_relatorios,
		)

	async def clicar_resultado(_evento) -> None:
		await executar_acao(
			"Eliminação Resultado",
			modulo_resultado.salvar_anexos_dos_relatorios,
		)

	async def clicar_composicao(_evento) -> None:
		await executar_acao(
			"Composição Geral",
			modulo_composicao.salvar_anexos_dos_relatorios,
		)

	async def clicar_quadro_resumo(_evento) -> None:
		await executar_acao(
			"Quadro Resumo Patrimonial Consolidado",
			modulo_quadro_resumo.salvar_anexos_quadro_resumo,
		)

	async def clicar_navigator(_evento) -> None:
		await executar_acao(
			"Navigator",
			executar_navigator,
			usar_com=False,
		)

	async def clicar_conciliacoes(_evento) -> None:
		await executar_acao(
			"Conciliações",
			executar_conciliacoes,
			usar_com=False,
		)

	async def clicar_atualizar(_evento) -> None:
		await executar_acao("atualização da caixa de entrada", atualizar_caixa_de_entrada)

	def limpar_log(_evento) -> None:
		registros.clear()
		caixa_log.value = ""
		page.update()

	botao_limpar.on_click = limpar_log

	botao_patrimonial = criar_botao_acao("Eliminação Patrimonial", ft.Icons.BALANCE, clicar_patrimonial, primary=True)
	botao_resultado = criar_botao_acao("Eliminação Resultado", ft.Icons.BAR_CHART, clicar_resultado, primary=True)
	botao_composicao = criar_botao_acao("Composição Geral", ft.Icons.ACCOUNT_BALANCE, clicar_composicao, primary=True)
	botao_quadro_resumo = criar_botao_acao("Quadro Resumo", ft.Icons.TABLE_CHART_OUTLINED, clicar_quadro_resumo, primary=True)
	botao_navigator = criar_botao_acao("Navigator", ft.Icons.TRAVEL_EXPLORE, clicar_navigator, primary=False)
	botao_conciliacoes = criar_botao_acao("Conciliações", ft.Icons.COMPARE_ARROWS, clicar_conciliacoes, primary=False)
	botao_atualizar = criar_botao_acao("Atualizar caixa", ft.Icons.SYNC, clicar_atualizar, primary=False)

	botoes.extend(
		[
			botao_patrimonial,
			botao_resultado,
			botao_composicao,
			botao_quadro_resumo,
			botao_navigator,
			botao_conciliacoes,
			botao_atualizar,
		]
	)

	header = ft.Row(
		[
			ft.Column(
				[
					ft.Text(
						"AUTOMAÇÃO DE PROCESSOS",
						size=11,
						color=ft.Colors.GREY_600,
						weight=ft.FontWeight.W_600,
					),
					ft.Text(
						"Intercompany",
						size=26,
						weight=ft.FontWeight.BOLD,
						color=PRIMARY_DARK,
					),
				],
				spacing=2,
			),
			ft.Row([progresso, indicador_status], spacing=10, tight=True),
		],
		alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
		vertical_alignment=ft.CrossAxisAlignment.CENTER,
	)

	acoes = ft.Row(
		[
			botao_patrimonial,
			botao_resultado,
			botao_composicao,
			botao_quadro_resumo,
			ft.VerticalDivider(width=16, color=BORDER),
			botao_navigator,
			botao_conciliacoes,
			botao_atualizar,
		],
		wrap=True,
		spacing=10,
		run_spacing=10,
	)

	log_card = ft.Container(
		content=ft.Column(
			[
				ft.Row(
					[
						ft.Column(
							[
								ft.Text("Log da execução", size=15, weight=ft.FontWeight.W_600, color=PRIMARY_DARK),
								ft.Text(
									"Resultados e mensagens das rotinas",
									size=12,
									color=ft.Colors.GREY_600,
								),
							],
							spacing=2,
						),
						botao_limpar,
					],
					alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
					vertical_alignment=ft.CrossAxisAlignment.CENTER,
				),
				ft.Container(
					content=caixa_log,
					expand=True,
					bgcolor=SURFACE,
					border_radius=8,
					padding=12,
				),
			],
			spacing=10,
			expand=True,
		),
		expand=True,
		border=ft.Border.all(1, BORDER),
		border_radius=12,
		padding=16,
	)

	page.add(
		ft.Column(
			[
				header,
				ft.Text("Ações", size=13, weight=ft.FontWeight.W_600, color=PRIMARY_DARK),
				acoes,
				log_card,
			],
			spacing=20,
			expand=True,
		)
	)


if __name__ in ("__main__", "eliminacao_patrimonial"):
	ft.run(main)
	if __name__ == "eliminacao_patrimonial":
		sys.exit(0)
