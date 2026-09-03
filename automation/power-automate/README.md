# Power Automate — fluxo "Consumer Board Builder"

`ConsumerBoardBuilder_package.zip` é o fluxo pronto para **importar** no Power
Automate (formato *Importar Pacote / Legado*). Ele faz:

```
Agente (Copilot) chama  →  Executar Office Script (gera o board)  →
    Criar arquivo consumer-martech.html no SharePoint  →  Responder ao agente com o link
```

> **Importante — o que o pacote NÃO consegue trazer pronto:** o workbook/script do
> Excel e o site do SharePoint têm GUIDs do **seu** tenant, e as conexões são
> escolhidas no assistente. Então o fluxo entra como **esqueleto** e você repõe
> 4 apontamentos (abaixo). Pré-requisito: o Office Script **Consumer Board Builder**
> já criado no Excel (ver `docs/standard/10-agente-gera-board.md`, Etapas 1–2).

## Importar (5 min)

1. **flow.microsoft.com** → **Meus fluxos** → **Importar** → **Importar Pacote (Legado)**.
2. Suba `ConsumerBoardBuilder_package.zip`.
3. Em **Recursos relacionados**, clique em cada conexão e selecione (ou crie):
   - **Excel Online (Business)**
   - **SharePoint**
4. **Importar**. Abra o fluxo em **Editar**.

## Repor os 4 apontamentos (5 min)

Na ação **Run Office Script**:
1. **Arquivo (workbook)** → selecione `BW_MarTech_2026_Controle_Projetos.xlsx`
   (isto preenche o Drive e o File; substitui os `PLACEHOLDER_...`).
2. **Script** → escolha **Consumer Board Builder**.

Na ação **Create board html**:
3. **Site Address** → seu site do SharePoint.
4. **Folder Path** → a pasta onde o board mora (deixei `/Shared Documents/Consumer`).

Salve. (O nome do arquivo já é `consumer-martech.html` e o conteúdo já é a saída do
script.)

## Ligar no agente (3 min)

Copilot Studio → **Ferramentas → Adicionar ferramenta → Fluxo** → **Consumer Board
Builder**. Descrição da ferramenta (cole):

> Builds the OFFICIAL Consumer board (B&W Marketing Technology 2026 Agenda: hero,
> real Unilever·B&W logo, cards, BR/MX/AR farol) from the Consumer MarTech Tracker
> Excel and returns its link. Call this whenever the user asks for the Consumer
> board, dashboard, agenda or HTML. Do NOT hand-write the HTML yourself.

## Teste

No agente: **"monta o board de Consumer"** → ele chama o fluxo e responde com o link
do `consumer-martech.html`.

---

### Se o seu tenant bloquear a importação legada

Use `flow-definition.json` (mesma pasta): crie um fluxo em branco com o gatilho
**"Quando um agente chama o fluxo"**, e monte as 3 ações na mão conforme o JSON —
ou siga o passo a passo do `docs/standard/10-agente-gera-board.md` (Etapa 3). O
resultado é idêntico.

### Atualização automática (opcional)

Para o board se regerar sozinho quando o tracker muda, duplique o fluxo trocando o
gatilho por **"Quando um arquivo é modificado (SharePoint)"** apontando para o
`.xlsx`, mantendo as ações Run Script → Create file.
