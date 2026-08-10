# Checklist de Settings

Diferenças entre o agente clássico (`botContent.yml`, L1–L30) e o novo (`Aura_Agent.yaml`, `entity.configuration`), com o que ajustar.

---

## 🔴 Ajustar

| Config | Clássico | Novo (hoje) | Ajustar para | Por quê |
|---|---|---|---|---|
| **Idioma** | `1046` (pt-BR) + suportados `1033`, `1034`, `21514` | `1033` (en-US) | **Português (Brasil)** | Suas instruções mandam responder em pt-BR mas a config diz en-US. Uma briga que você perde de vez em quando |
| **Moderação de conteúdo** | `High` | `Maximum` | **Alta** | O agente faz cobrança dura ("Gestor Ofensor", "A Pergunta de €1 Milhão"). Moderação máxima corta esse tipo de saída |

---

## ✅ Manter como está

| Config | Valor | Comentário |
|---|---|---|
| **Memory** | `enableMemory: true` | Capacidade nova, boa. Mas **não** é substituta da `Global.tabela_pbi` — ver `docs/03`, seção 3.6 |
| **Busca na web** | `enableWebSearch: false` | Correto para dado corporativo |
| **Modelo** | `Opus48` | Idêntico ao clássico |
| **Controle de acesso** | `accessControlPolicy: GroupMembership` | Idêntico. É a sua alavanca real de restrição — ver `docs/03`, seção 3.8 |
| **Autenticação** | `authenticationMode: Integrated` | Idêntico |

---

## ⚠️ Sem equivalente direto na nova experiência

Estas configs existiam no clássico e não aparecem no YAML novo. Procure na UI; se não existirem, aplique a mitigação.

| Config clássica | Valor | Mitigação se não houver equivalente |
|---|---|---|
| `useModelKnowledge: true` | conhecimento geral do modelo | Se houver toggle equivalente, ligue |
| `isFileAnalysisEnabled: true` | análise de arquivo anexado | Se sumiu, o usuário não anexa planilha para o agente ler |
| `isSemanticSearchEnabled: true` | busca semântica no SharePoint | Confira a qualidade da busca na Wiki no teste da Etapa 4 |
| `optInUseLatestModels: true` | adotar modelo novo automaticamente | Se houver, ligue |
| `gptCapabilities.codeInterpreter: true` | **cálculo determinístico** | ⚠️ O mais sério. Sem ele o `FinalScore` de 4 pilares com pesos vira conta de cabeça do modelo. **Mitigação já embutida nas instruções e nas skills: sempre LER a coluna `[FinalScore]` do dataset, nunca recalcular.** Se precisar de conta nova, calcule no Power BI |

---

## Como verificar depois de aplicar

| Teste | Esperado |
|---|---|
| Digite `olá` | Resposta em português |
| Peça uma análise crítica de governança de uma área | Ele nomeia responsáveis e cobra, sem amenizar |
| Pergunte o FinalScore de um projeto | Ele **lê** o valor do dataset e explica os 4 pilares — não apresenta uma conta própria |
| Encerre e reabra a conversa | Memory: ele lembra de preferência declarada antes |
