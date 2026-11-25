# Guia do Usuário — Primeiros Passos (Automação Intercompany)

Bem-vindo(a) ao aplicativo **Automação Intercompany**. Este guia explica como abrir o programa, entender a tela principal e executar cada rotina no dia a dia, mesmo que seja o seu primeiro acesso.

---

## 1. O que o aplicativo faz

O aplicativo reúne em uma única interface desktop todas as rotinas de captura, organização e salvamento de arquivos do processo de **Intercompany**:

- **Rotinas via Outlook:** sincronizam sua Caixa de Entrada, identificam e-mails padronizados e salvam os anexos automaticamente nas pastas da rede.
- **Rotinas via Downloads (SharePoint / Teams / Portal):** leem os arquivos que você baixou na pasta `Downloads` do seu computador, validam nome e extensão e movem tudo para a pasta correta na rede.

---

## 2. Antes de começar (Pré-requisitos)

Verifique se o seu ambiente atende aos pontos abaixo antes da primeira execução:

1. **Sistema operacional:** Windows 10 ou 11 (64 bits).
2. **Acesso à rede corporativa / VPN:** acesso liberado ao diretório `\\brtssisp003\bbb0133$\2 - Intercompany`.
3. **Microsoft Outlook clássico (desktop):** instalado e configurado com sua conta corporativa (necessário para as rotinas que leem e-mails).
   > **Atenção:** o *Novo Outlook* do Windows não suporta integração COM; utilize a versão clássica do Outlook desktop.
4. **Pasta `Downloads` padrão:** para **Conciliações** e **Navigator**, salve os arquivos baixados na pasta padrão `C:\Users\<seu-usuario>\Downloads`.

---

## 3. Como abrir o aplicativo

### Opção A — Executável pronto (recomendado)
1. Copie e descompacte `automacao_intercompany.zip` (da pasta `dist-homologacao`) em uma pasta do seu computador.
2. Dê um duplo clique em **`automacao_intercompany.exe`**.
3. Aguarde alguns segundos na primeira abertura até a janela **Intercompany** aparecer.

> Se o Windows exibir um aviso de proteção (*SmartScreen*), clique em **Mais informações** → **Executar assim mesmo**.

### Opção B — Pelo código-fonte (ambiente com Python)
- Dê um duplo clique em **`Abrir-Automacao.bat`** na pasta do projeto (requer `.venv` criado e dependências de `requirements-app.txt` instaladas).

---

## 4. Conhecendo a tela principal

A janela **Automação Intercompany** é dividida em três áreas:

1. **Indicador de status (canto superior direito):**
   - **Pronto para iniciar / Concluído** (verde): o aplicativo está livre para uma nova ação.
   - **Executando: `<rotina>`** (amarelo, com círculo girando): há uma rotina em andamento. Durante esse período, todos os botões ficam desabilitados automaticamente para evitar conflitos.
   - **A operação encontrou um erro** (vermelho): ocorreu uma falha; consulte os detalhes no log abaixo.
2. **Barra de Ações (7 botões):**
   - **Botões roxos (rotinas de relatórios do Outlook):** `Eliminação Patrimonial`, `Eliminação Resultado`, `Composição Geral` e `Quadro Resumo`.
   - **Botões brancos (rotinas operacionais e utilitário):** `Navigator`, `Conciliações` e `Atualizar caixa`.
3. **Log da execução (parte inferior):**
   - Mostra o horário (`HH:MM:SS`), o andamento de cada ação, o total de arquivos salvos, a relação dos arquivos processados (quando aplicável) e mensagens de erro.
   - Mantém até **300 linhas** na sessão atual (o log não é gravado em arquivo).
   - Para limpar a tela de log, clique no ícone de **lixeira** no canto superior direito do quadro de log.

---

## 5. Como usar cada botão

### Resumo rápido

| Botão | Origem | Extensões aceitas | Destino principal |
| :--- | :--- | :--- | :--- |
| **Eliminação Patrimonial** | Outlook (Caixa de Entrada) | `.xls`, `.xlsx`, `.csv`, `.xlsm`, `.zip` | `...\ANO_<yyyy>\<mm>_<yyyy>\APLICATIVO ELIMINAÇÃO\Eliminação Patrimonial\<empresa>` |
| **Eliminação Resultado** | Outlook (Caixa de Entrada) | `.xls`, `.xlsx`, `.csv`, `.xlsm`, `.zip` | `...\ANO_<yyyy>\<mm>_<yyyy>\APLICATIVO ELIMINAÇÃO\Eliminação Resultado\<empresa>` |
| **Composição Geral** | Outlook (Caixa de Entrada) | `.xls`, `.xlsx`, `.csv`, `.xlsm`, `.zip` | `...\ANO_<yyyy>\<mm>_<yyyy>\COMPOSIÇÃO DE SALDOS\<codigo>-<empresa>` |
| **Quadro Resumo** | Outlook (Caixa de Entrada) | `.xlsx`, `.zip` (contendo `.xlsx`) | `<destino>\ANO_<yyyy>\<mm>_<yyyy>\QUADRO RESUMO\<codigo>-<empresa>` |
| **Navigator** | Pasta local `Downloads` | `.xls`, `.xlsx`, `.csv`, `.xlsm`, `.zip` | `...\ACCENTURE_NAVIGATOR\<yyyy>\<mm>_<yyyy>` |
| **Conciliações** | Pasta local `Downloads` | `.xls`, `.xlsx`, `.csv`, `.xlsm`, `.zip` | `...\ANO_<yyyy>\<mm>_<yyyy>\CONCILIAÇÕES INTERCOMPANY\<codigo1>-<empresa1>` |
| **Atualizar caixa** | Outlook | — | Apenas sincroniza (Enviar/Receber) a Caixa de Entrada |

> Base da rede: `\\brtssisp003\bbb0133$\2 - Intercompany`

---

### Detalhes de cada rotina

#### 1. Eliminação Patrimonial
- **O que faz:** sincroniza o Outlook, organiza pastas já existentes e salva anexos de e-mails cujo assunto siga o padrão:
  `RELATÓRIO DE ELIMINAÇÃO PATRIMONIAL - <Empresa1> (<Cod1>) x (<Cod2>) <Empresa2> - mm/yyyy`
- **Organização:** cria as subpastas `Checklist` e `Versões Anteriores`, extrai arquivos `.zip` automaticamente e mantém sempre a versão mais recente (`_V<n>`) na raiz da empresa. Anexos já processados não são duplicados.

#### 2. Eliminação Resultado
- **O que faz:** segue a mesma regra da Eliminação Patrimonial, buscando e-mails com assunto:
  `RELATÓRIO DE ELIMINAÇÃO RESULTADO - <Empresa1> (<Cod1>) x (<Cod2>) <Empresa2> - mm/yyyy`
- **Organização:** salva em `...\APLICATIVO ELIMINAÇÃO\Eliminação Resultado\<cod1> x <cod2> - <empresa1> x <empresa2>`, também com `Checklist`, `Versões Anteriores` e extração automática de `.zip`.

#### 3. Composição Geral
- **O que faz:** sincroniza o Outlook e captura anexos de e-mails com assunto:
  `COMPOSIÇÃO DE SALDO PATRIMONIAL - <Empresa> (<Codigo>) - mm/yyyy` ou `COMPOSIÇÃO DE SALDO RESULTADO - <Empresa> (<Codigo>) - mm/yyyy`
- **Organização:** salva em `...\COMPOSIÇÃO DE SALDOS\<codigo>-<empresa>`, extraindo `.zip` e gerenciando `Checklist` e `Versões Anteriores`.

#### 4. Quadro Resumo
- **O que faz:** sincroniza o Outlook e processa e-mails com assunto `QUADRO RESUMO - mm/yyyy` (com ou sem `_V<n>`), aceitando anexos `.xlsx` diretos ou dentro de `.zip` no padrão `Quadro Resumo - <Empresa> - mm_yyyy.xlsx`.
- **Empresas mapeadas:** `0185-TBRA`, `0306-TIS`, `0367-TERRA`, `0999-TGLOG`, `1871-POP`, `1872-RECICLA V`, `2008-CLOUD`, `2011-FIBRASIL`, `2207-VSS` e `2234-VSCD`.
- **Resultado no log:** exibe a quantidade total e a lista de todos os arquivos salvos.
- **Observação:** na versão atual de homologação, esta rotina salva na pasta configurada em `quadro-resumo-patrimonial.py` (sem criar subpastas de versões).

#### 5. Navigator
- **Como executar:**
  1. Baixe os arquivos do Navigator / SharePoint para a sua pasta **`Downloads`**.
  2. Clique no botão **`Navigator`** no aplicativo.
- **Arquivos reconhecidos:** planilhas com prefixo `ANS SF - 005`, `ANS SF - 006`, `ANS SF - 007`, `Volume SF - 007`, `Volume SF_014` e `Volume SF_014 ... Resumo`, contendo a competência (`mm_yyyy`) no nome.
- **Arquivos `.zip`:** quando você baixa vários arquivos juntos em `.zip`, o aplicativo descompacta primeiro em pasta temporária, move somente os arquivos válidos do Navigator para a rede e remove o `.zip` de `Downloads` caso ele contenha apenas arquivos do Navigator.
- **Destino e versionamento:** move para `\\brtssisp003\bbb0133$\2 - Intercompany\ACCENTURE_NAVIGATOR\<yyyy>\<mm>_<yyyy>` e mantém a subpasta **`Versões Anteriores`** (arquivando versões menores ou substituições com o mesmo nome).
- **Resultado no log:** exibe o total de arquivos salvos e o caminho de cada um.

#### 6. Conciliações
- **Como executar:**
  1. Ao receber a notificação no **Teams**, acesse o **SharePoint** e baixe o arquivo de conciliação para a sua pasta **`Downloads`**.
  2. Clique no botão **`Conciliações`** no aplicativo.
- **Padrão de nome aceito:** `codigo1_x_codigo2_empresa1_x_empresa2_mm_yyyy.<ext>`
  - **Exemplo:** `0185_x_0024_TBRA_x_TID_10_2026.xlsm`
  - **Destino gerado:** `\\brtssisp003\bbb0133$\2 - Intercompany\ANO_2026\10_2026\CONCILIAÇÕES INTERCOMPANY\0185-TBRA\`
- **Extensões permitidas:** somente `.xls`, `.xlsx`, `.csv`, `.xlsm` e `.zip`. Arquivos com outras extensões ou nomes fora do padrão permanecem intactos em `Downloads`.
- **Resultado no log:** exibe o total de arquivos salvos e a lista completa dos arquivos movidos.

#### 7. Atualizar caixa
- Executa apenas a sincronização de todas as pastas do Outlook (Enviar/Receber), aguardando até o limite de 5 minutos.
- É opcional, pois as rotinas de Outlook já sincronizam automaticamente antes de buscar e-mails — mas ajuda quando você quer apenas confirmar o recebimento de novos e-mails.

---

## 6. Roteiro rápido para o primeiro uso

1. Conecte-se à **VPN / rede corporativa** e confirme que consegue abrir `\\brtssisp003\bbb0133$\2 - Intercompany` no Explorador de Arquivos.
2. Abra o **Outlook clássico** (se for usar rotinas de e-mail) ou baixe os arquivos do SharePoint para **`Downloads`** (se for usar **Conciliações** ou **Navigator**).
3. Execute **`automacao_intercompany.exe`**.
4. Clique na rotina desejada e aguarde o status voltar para **Concluído** (verde).
5. Confira no quadro **Log da execução** o total e a lista de arquivos salvos.

---

## 7. Solução de problemas comuns

| Situação | Causa provável | O que fazer |
| :--- | :--- | :--- |
| **"Nenhum arquivo novo foi salvo."** | Os arquivos já foram processados antes, ou ainda não estão em `Downloads` / Caixa de Entrada, ou o nome/extensão está fora do padrão. | Confira se o download terminou (sem extensão `.crdownload`), se a extensão está entre `.xls`, `.xlsx`, `.csv`, `.xlsm`, `.zip` e se o nome segue o padrão esperado. |
| **Erro ao acessar a pasta de rede** | Sem conexão VPN ou sem permissão no compartilhamento `\\brtssisp003\bbb0133$`. | Conecte a VPN e teste abrir `\\brtssisp003\bbb0133$\2 - Intercompany` pelo Windows Explorer antes de tentar novamente. |
| **Erro de Outlook / COM** | Outlook fechado, travado ou usando o *Novo Outlook*. | Abra o **Outlook clássico**, confirme que sua caixa carrega normalmente e rode novamente. |
| **Erro de permissão ao mover arquivo** | O arquivo está aberto no Excel (ou bloqueado por outro programa). | Feche a planilha no Excel e clique no botão novamente. |
| **Timeout na sincronização do Outlook** | Sincronização demorou mais de 5 minutos (rede lenta ou muitos e-mails). | Aguarde o Outlook terminar de sincronizar manualmente e execute a rotina novamente. |

