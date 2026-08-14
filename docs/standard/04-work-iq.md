# 4. Work IQ — o que é, o que custa, e o que ele resolve no seu caso

Você perguntou sobre o Work IQ, *"que é poder pegar a base de dados do usuário"*. A leitura está certa — e é justamente por isso que ele tem duas pegadinhas que decidem a questão.

---

## 4.1 O que é

Work IQ é a camada de inteligência que aterra o Microsoft 365 Copilot e os agentes no contexto da organização: e-mails, reuniões, chats, arquivos e sinais de atividade do Microsoft 365.

Não é uma fonte de conhecimento que você aponta para um documento. É **acesso dinâmico** aos dados de trabalho, seguindo o contexto e as permissões de quem está usando o agente.

---

## 4.2 Como se adiciona no standard

Ele **existe** na experiência standard — mas não entra em Conhecimento. Entra como **ferramenta MCP**:

> **Ferramentas → Adicionar ferramenta → Model Context Protocol → Work IQ (preview)** → abra o dropdown de conexão → **Criar**

Servidores disponíveis:

| Servidor | O que dá | Serve para você? |
|---|---|---|
| **Work IQ Mail** | Ler e resumir threads de e-mail | Talvez — ver §4.4 |
| **Work IQ Calendar** | Criar, listar, atualizar e excluir eventos; aceitar/recusar; resolver conflitos | Marcar a reunião de rebaseline |
| **Work IQ Teams** | Ler conversas do Teams | Talvez — ver §4.4 |
| **Work IQ Copilot** | Busca semântica em todo o M365 | Cobre parte do que o SharePoint já faz |

Também há endpoints para Copilot Chat, Word, Outlook Mail/Calendar, perfil do usuário M365, SharePoint e OneDrive.

---

## 4.3 🔴 Pegadinha 1 — o custo

**Para agentes customizados, Work IQ é cobrado por consumo em Copilot Credits, e não está incluído na licença do Microsoft 365 Copilot.**

Isso importa muito no seu caso específico: você trocou o motor do GitHub Copilot pelo standard exatamente porque *"o de github copilot tem custo até para testar"*. Ligar Work IQ **reintroduz cobrança por consumo pela porta dos fundos** — dessa vez em Copilot Credits, cobrando por chamada, inclusive nos testes.

Se for avaliar, avalie com número: quantas chamadas por conversa, quantas conversas por dia, e qual o preço do crédito no contrato da Unilever. Não dá para estimar isso daqui.

---

## 4.4 🔴 Pegadinha 2 — de quem é o dado

**Work IQ opera no contexto e nas permissões do usuário logado.**

Ou seja: ele lê a caixa de entrada, a agenda e as conversas **de quem está falando com o agente naquele momento** — não do gestor que você quer cobrar.

Aplicando ao seu cenário:

| Você imagina | O que Work IQ realmente faz |
|---|---|
| "O agente lê a resposta do gestor no e-mail dele" | ❌ Não. Não tem acesso à caixa do gestor |
| "O agente descobre a agenda do gestor" | ❌ Não. Só a sua |
| "O agente lê o que **eu** conversei com o gestor" | ✅ Sim — se a conversa está no *seu* Teams ou no *seu* e-mail |
| "O agente marca uma reunião **na minha** agenda com o gestor" | ✅ Sim, via Work IQ Calendar |

**Conclusão: Work IQ não substitui a mensagem proativa do Teams.** Para o ciclo de cobrança (ir até o gestor, pedir a data nova, gravar no DevOps), o caminho continua sendo o do [`03-teams-conversa-com-gestor.md`](03-teams-conversa-com-gestor.md), que não custa crédito e funciona no contexto certo.

---

## 4.5 Onde ele valeria a pena depois

Quando o agente estiver estável e o custo estiver aprovado, os usos que fazem sentido:

1. **Work IQ Calendar — agendar o rebaseline.** Depois que o gestor confirma a nova data, o agente marca a reunião de rebaseline na sua agenda com os envolvidos. Fecha o ciclo de governança.
2. **Work IQ Mail — recuperar o que ficou combinado por e-mail.** Hoje o contexto humano vem só das Transcrições no SharePoint. Muita decisão de portfólio mora em thread de e-mail que nunca virou ata.
3. **Work IQ Copilot — busca ampla.** Antes de declarar "projeto sem registro" no fallback do Deep Dive, procurar em todo o M365, não só nas duas pastas do SharePoint.

Nos três casos é **enriquecimento do seu contexto**, não acesso ao dado de terceiros. Essa é a fronteira.

---

## 4.6 Recomendação

**Não ligue agora.** Nesta ordem:

1. Corrija as 5 tools ([`02-correcao-das-tools.md`](02-correcao-das-tools.md)) — é o que destrava o agente de verdade e custa zero.
2. Publique no Teams e faça o ciclo de cobrança funcionar ([`03`](03-teams-conversa-com-gestor.md) + [`topics/cobranca-gestor.yaml`](../../topics/cobranca-gestor.yaml)) — também zero de custo adicional.
3. Só então, com o agente rodando e o volume de uso conhecido, leve o número de Copilot Credits para aprovação e avalie o Work IQ Calendar como primeiro passo.

Ligar Work IQ antes de o básico funcionar é pagar por consumo para depurar problema de configuração de tool.

---

## Fontes

- [Work IQ in Microsoft Copilot Studio (preview) — Microsoft Learn](https://learn.microsoft.com/en-us/microsoft-copilot-studio/add-work-iq)
- [Work IQ overview — Microsoft Learn](https://learn.microsoft.com/en-us/microsoft-365/copilot/extensibility/work-iq/)
- [Work IQ General Availability — Microsoft Licensing](https://www.microsoft.com/en-us/licensing/news/work-iq-general-availability)
- [Announcing the new Work IQ APIs — Microsoft 365 Blog](https://www.microsoft.com/en-us/microsoft-365/blog/2026/06/02/announcing-the-new-work-iq-apis/)
- [Microsoft IQ overview for agents (nova experiência)](https://learn.microsoft.com/en-us/microsoft-copilot-studio/agents-experience/use-microsoft-iq)
