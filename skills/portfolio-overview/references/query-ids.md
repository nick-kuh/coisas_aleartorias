# Query IDs do Azure DevOps

Use com a tool **`DevOps Query by Area or BU`** (inputs `account` e `project` já vêm fixos).

**Nunca invente um GUID.** Se o recorte pedido não estiver aqui, use o default e avise o usuário que é a visão geral.

## Por IT Area

| Área (e sinônimos aceitos) | Query ID |
|---|---|
| **Make** · Business Ops · Supply Chain · Supply | `8b53a319-c304-4d55-be7e-0e3b8e2c2d03` |
| **Consumer** · Marketing | `95581604-d21e-4268-a1fa-ca5bd59185f9` |
| **CD** · Customer Development | `10271fab-00ff-44c6-98d7-241877e53ee7` |
| **Focus Market** · Customer Operations · Customer Ops | `236b80a4-395a-40cd-a962-8b3284fce608` |

## Por Business Unit

| BU (e sinônimos) | Query ID |
|---|---|
| **Foods** | `e15d1af6-0238-4e26-93ba-1f456b6258a9` |
| **HC** · Home Care | `61e1da44-eb44-4f0f-8ff7-385d045f397c` |
| **PC** · Personal Care | `bf99b079-207d-4027-97c2-6573129c5400` |
| **BW** · B&W · Beauty · Beauty and Wellbeing | `472b3677-9bd9-4289-8367-c61826219f3d` |

## Especiais

| Escopo | Query ID | Tool |
|---|---|---|
| **Default / Others** (recorte não mapeado) | `590e44b1-fdb4-4e3b-bd2e-32813b771443` | `DevOps Query by Area or BU` |
| **Master** (portfólio inteiro) | `9aecac87-a35a-45be-b1f4-af64000189ca` | `DevOps Portfolio Master Query` (já fixo, não precisa passar) |

## Acrônimos combinados

Não existe Query ID para combinações. Rode uma consulta por BU e junte os resultados:

| Acrônimo | Rodar |
|---|---|
| `BPC` | BW + PC |
| `HPC` | HC + PC |
| `HPF` | HC + PC + Foods |

Alternativa mais econômica: use a `Power BI Portfolio Database` com o filtro de BU do `dax-cookbook.md`, receita 3, que já resolve combinações em uma chamada.
