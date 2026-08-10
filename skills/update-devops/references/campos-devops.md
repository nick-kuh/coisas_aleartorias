# Campos do Azure DevOps — work item `IT Project`

Extraído do `dynamicInputSchema` da ação `UpdateWorkItem` do agente clássico (`botContent.yml`, L720–L1290). **Todos os reference names abaixo são reais.**

Chave do `userEnteredFields` = o **reference name completo** (`Custom.Note`), nunca o nome amigável (`Note`).

---

## ⛔ NUNCA envie (read-only)

Enviar qualquer um destes faz o PATCH falhar:

```
System.CreatedBy                        System.CreatedDate
System.ChangedBy                        System.ChangedDate
System.TeamProject                      System.WorkItemType
Microsoft.VSTS.Common.StateChangeDate   Microsoft.VSTS.Common.ActivatedBy
Microsoft.VSTS.Common.ActivatedDate     Microsoft.VSTS.Common.ClosedBy
Microsoft.VSTS.Common.ClosedDate        Microsoft.VSTS.Common.ResolvedBy
Microsoft.VSTS.Common.ResolvedDate
```

---

## Campos de sistema editáveis

| Reference name | Nome amigável | Observação |
|---|---|---|
| `System.State` | State | ⚠️ Valida contra as 13 fases oficiais |
| `System.AssignedTo` | Assigned To | E-mail ou nome do responsável |
| `System.History` | History | Adiciona comentário ao histórico |
| `System.Reason` | Reason | Motivo da mudança de estado |
| `System.Tags` | Tags | **Opcional** — nunca sinalize como faltante |
| `System.AreaLevel1` … `System.AreaLevel7` | Area Level 1–7 | Hierarquia de área |
| `System.IterationLevel1` … `System.IterationLevel7` | Iteration Level 1–7 | Hierarquia de iteração |
| `Microsoft.VSTS.Common.StackRank` | Stack Rank | Ordenação |
| `Vsts.TagsAction` | Tags action | Como aplicar as tags |

Campos diretos da operação (fora do `userEnteredFields`): `title`, `description`, `area` (Area Path), `iterationPath`, `priority`, `linkUrl`, `linkType`, `linkComment`.

---

## Campos customizados do CDIO (`Custom.*`)

### 🔴 Governança — obrigatórios

| Reference name | Nome amigável |
|---|---|
| `Custom.BGorBUEngagement` | BG or BU Engagement |
| `Custom.BusinessBenefit` | Business Benefit |
| `Custom.BusinessProductsDomain` | Business Products Domain |
| `Custom.ITArea` | IT Area |
| `Custom.ProjectITManager` | Project IT Manager |
| `Custom.ProjectType` | Project Type |
| `Custom.CountryDeployed` | Country Deployed |
| `Custom.PortfolioYear` | Portfolio Year |
| `Custom.ImplementionTimeinMonths` | Implemention Time in Months |

### 🟡 Condicionais

| Reference name | Nome amigável | Obrigatório quando |
|---|---|---|
| `Custom.SpecifyCross` | Specify Cross | `BG or BU Engagement` = `Cross` |
| `Custom.ProjectTotalBudget` | Project Total Budget | a partir de `06 Plan Analyze` |
| `Custom.ProjectITBudget` | Project IT Budget | idem |
| `Custom.ProjectBenefitValue` | Project Benefit Value | a partir de `05 Cost Approv`; opcional se `Business Benefit` ≠ `Value Added` |
| `Custom.PaybackinMonths` | Payback in Months | a partir de `06 Plan Analyze` |
| `Custom.GoLiveDate` | GoLive Date | a partir de `06 Plan Analyze` |
| `Custom.PGLSEndDate` | PGLS End Date | a partir de `06 Plan Analyze` |

### ⚪ 100% opcionais — **nunca sinalize como faltantes**

`Custom.SecurityAssessmentStatus` (Security Assessment Status) · `Custom.AssentmentSecurityNumber` · `Custom.ClarityID` (Clarity ID) · `Custom.Note` (Note) · `System.Tags`

### Demais campos customizados

| Reference name | Nome amigável |
|---|---|
| `Custom.ArchitetureApprover` | Architeture Approver |
| `Custom.CampaignCost` | Campaign Cost |
| `Custom.Category` | Category |
| `Custom.DefineYourParticipation` | Define Your Participation |
| `Custom.DiscussionTimeline` | Discussion Timeline |
| `Custom.ERPImpact` | ERP Impact |
| `Custom.FundingSource` | Funding Source |
| `Custom.GAPAction` | GAP Action |
| `Custom.GlobalorLocal` | Global or Local |
| `Custom.IncrementalRunningCost` | Incremental Running Cost |
| `Custom.InnovationCategory` | Innovation Category |
| `Custom.MakePillar` | Make Pillar |
| `Custom.Pillar` | Pillar |
| `Custom.ProcessAfected` | Process Afected |
| `Custom.ProductName` | Product Name |
| `Custom.RiskDescription` | Risk Description |
| `Custom.SaaSDelivered` | SaaS Delivered |
| `Custom.SpecifyTypeofBenefit` | Specify Type of Benefit |
| `Custom.Stages` | Stages |
| `Custom.SubAreaSite` | SubArea Site |
| `Custom.SubProductDomain` | Sub Product Domain |
| `Custom.TechImpactonCampaign` | Tech Impact on Campaign |
| `Custom.TechnologyDelivered` | Technology Delivered |
| `Custom.TechParticipation` | Tech Participation |
| `Custom.ToolsorApps` | Tools or Apps |
| `Custom.TypeofBenefit` | Type of Benefit |
| `Custom.VendorSupport` | Vendor Support |
| `Custom.Workstream` | Workstream |

> Também existem no schema, com underscore no nome amigável: `Business_Owner`, `Product_Owner`, `Product_Status`, `Sub_Product Domain`. Confirme o reference name exato no DevOps antes de gravar nestes.

---

## Domínios fechados

| Campo | Valores permitidos |
|---|---|
| `System.State` | `00 Cancelled`, `01 Idea`, `02 Scoping`, `03 Scope Approv`, `04 Costing`, `05 Cost Approv`, `06 Plan Analyze`, `07 Design Build`, `08 UAT`, `09 PGLS`, `10 Deployed`, `11 Closed`, `12 On Holding` |
| `Custom.BusinessBenefit` | `Compliance`, `Value Added` |
| `Custom.ProjectType` | `Big Rock` (padrão) e demais tipos do processo |
| `Custom.BGorBUEngagement` | `BW`, `PC`, `HC`, `Foods`, `Nutrition`, `Ice Cream`, `1 UL`, `Cross` |

Ao gravar `Cross` em `Custom.BGorBUEngagement`, `Custom.SpecifyCross` passa a ser obrigatório.

---

## Exemplos de `userEnteredFields`

Mudar só o estado:
```json
{ "System.State": "07 Design Build" }
```

Preencher os financeiros:
```json
{
  "Custom.ProjectTotalBudget": "250000",
  "Custom.ProjectBenefitValue": "480000",
  "Custom.PaybackinMonths": "14"
}
```

Registrar uma observação:
```json
{ "Custom.Note": "Rebaseline aprovado na LT de 12/08/2026. Novo Go-Live: 30/11/2026." }
```

Colocar em espera:
```json
{
  "System.State": "12 On Holding",
  "Custom.RiskDescription": "Aguardando aprovação de budget do BG."
}
```
