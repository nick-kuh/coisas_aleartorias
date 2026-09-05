# 11 — Backup e restauração do AURA (modo standard)

Guia para **guardar** e **restaurar** o projeto inteiro do agente AURA + os fluxos
de relatório. Um backup completo tem **4 partes** — as duas soluções não bastam
sozinhas.

---

## O que compõe o projeto (e onde cada coisa mora)

| # | Componente | Onde vive | Vai na solução? |
|---|---|---|---|
| 1 | **Agente AURA** (instruções, tópicos, ligação com tools, *referências* de conhecimento) | Copilot Studio / Dataverse | ✅ (export de solução com o Chatbot) |
| 2 | **Fluxos** (Consumer Report, Publish Area Report, Portfolio Data by Area) + connection references | Power Automate / Dataverse | ✅ (solução `CDIORelatorioArea`) |
| 3 | **Office Script** que gera o HTML do board | Excel Online / OneDrive | ❌ — exportar à parte (`.osts`) |
| 4 | **Arquivos de conhecimento** (Consumer MarTech Tracker `.xlsx`, AURA Playbook `.docx`, transcrições, wiki) | SharePoint / OneDrive | ❌ — só *ponteiros* vão no agente |

> **Conexões não são exportadas** (Excel, SharePoint, DevOps, Power BI, Teams).
> Isso é normal — você as **religa** no momento do import.

---

## Fazer o backup (4 passos)

### 1. Agente
1. **make.powerapps.com → Solutions → + New solution** (ex.: `AURA Backup`, publisher `UnileverCoPilotStudioPOC`).
2. **+ Add existing → Chatbot** (pode aparecer como *Agent*/*Copilot*) → selecione **AURA** → inclua dependências se perguntar.
3. **Solutions → marque a solução → Export solution → Unmanaged → Export.**
   - O zip contém `botContent.yml` (o agente inteiro: instruções, tópicos, tools, referências).

### 2. Fluxos
- **Solutions → CDIO - Relatorio por IT Area → Export → Unmanaged.**
- Guarde a versão **atual** (ex.: `CDIORelatorioArea_1_4_1_8.zip`), não uma antiga.

### 3. Office Script
- Abra o **Consumer MarTech Tracker** no Excel Online → aba **Automate** → o script do board → **⋮ → Save a copy** (ou copie o código `.ts`).
- Sem ele, o board para de ser gerado — o fluxo só o chama por ID.

### 4. Conhecimento
- Copie o **Tracker `.xlsx`** e o **AURA Playbook `.docx`** para a pasta de backup.

> **Dica:** junte tudo numa pasta `AURA_Backup_AAAA-MM-DD` no SharePoint.

---

## Restaurar

1. **Importar a solução dos fluxos** (`CDIORelatorioArea_*.zip`):
   Solutions → Import solution → aponte as conexões (Excel, SharePoint, DevOps) → Import.
   - "0 updates needed" é o esperado quando as conexões já existem.
   - Após importar, **confira que os 3 Cloud Flows estão `On`** (o import pode
     deixá-los `Off`; as *connection references* aparecem `Off` — isso é normal).
2. **Importar a solução do agente** → religar conexões.
3. **Recolocar o Office Script** no Excel e conferir que o fluxo aponta pro ID certo.
4. **Publicar** o agente no Copilot Studio.
5. Testar: pedir o board (sem pedir permissão, cai em `Agent Report/Consumer`) e um
   relatório DevOps (cai na subpasta da área).

---

## Fatos do estado atual (fixados aqui para não se perder)

- **Fluxos rodam `embedded`** (não `invoker`) → **não pedem permissão** de Excel/SharePoint.
  A diferença fica no campo `runtimeSource` de cada conexão, no `.json` do fluxo.
- **Relatórios organizados em subpastas** dentro de `…/CDIO LATAM/Agent Report`:
  `CD` · `Focus Mkt` · `Make` · `Consumer` · `Todo o portfolio` · `Outros`.
  - **Consumer flow** → pasta fixa `/Agent Report/Consumer`.
  - **Publish flow** → o bloco `CONFIG_Folder` monta a subpasta a partir do
    `scope_label` (`Init_Scope`); quem não casa com nenhuma área cai em `Outros`.
- **Site/base:** `https://unilever.sharepoint.com/sites/ITBWLatam`,
  pasta `/Shared Documents/CDIO LATAM/Agent Report`.
- **Instruções do agente:** limite ~8000 caracteres (conta espaços e acentos).
  A **§1 deve conter `Always answer in Brazilian Portuguese.`** — sem isso, como o
  prompt é todo em inglês, o agente tende a responder em inglês.
- Como os fluxos rodam **como o dono (Nicolas)**, ele precisa de acesso ao Tracker
  (OneDrive) e à pasta SharePoint — senão o board dá **"acesso negado"** em vez de
  pedir permissão.

---

## Checklist rápido

- [ ] Solução do **agente** exportada (unmanaged), já com `Always answer in Brazilian Portuguese.` e publicado
- [ ] Solução dos **fluxos** exportada (versão atual, embedded + subpastas)
- [ ] **Office Script** salvo à parte
- [ ] **Tracker** + **Playbook** copiados
- [ ] Tudo numa pasta `AURA_Backup_AAAA-MM-DD`
