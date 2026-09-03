#!/usr/bin/env bash
# Valida cada skills/<nome>/SKILL.md contra as regras do Copilot Studio:
#   - frontmatter YAML delimitado por ---
#   - name em kebab-case, <= 64 chars, sem hifen no inicio/fim
#   - name igual ao nome da pasta
#   - description presente e <= 1024 chars
#   - SKILL.md <= 500 linhas (recomendacao)
#   - toda tool citada em **`...`** existe na lista oficial
set -uo pipefail
cd "$(dirname "$0")/.."

TOOLS_OFICIAIS=(
  "Power BI Portfolio Database"
  "Power BI Master DB Search"
  "Power BI KPI Agente"
  "DevOps Portfolio Master Query"
  "DevOps Query by Area or BU"
  "DevOps Work Item Details"
  "DevOps Update Work Item"
  "Teams — Postar mensagem"
)

# Fontes de conhecimento: citadas com a mesma notacao das tools nas skills,
# mas nao sao tools. Nomes conforme os KnowledgeSourceComponent do agente.
KNOWLEDGE_OFICIAL=(
  "CDIO_LATAM_Governance_Wiki"
  "Transcription LT Meetings"
  "Consumer MarTech Tracker"
)

erros=0
avisos=0

for dir in skills/*/; do
  nome_pasta="$(basename "$dir")"
  arquivo="${dir}SKILL.md"
  printf '\n=== %s ===\n' "$nome_pasta"

  if [[ ! -f "$arquivo" ]]; then
    echo "  ERRO: SKILL.md nao encontrado"; erros=$((erros+1)); continue
  fi

  python3 - "$arquivo" "$nome_pasta" "$(printf '%s\n' "${TOOLS_OFICIAIS[@]}")" "$(printf '%s\n' "${KNOWLEDGE_OFICIAL[@]}")" <<'PY'
import re, sys

caminho, pasta, tools_raw, know_raw = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
tools = [t for t in tools_raw.split("\n") if t]
knowledge = [k for k in know_raw.split("\n") if k]
texto = open(caminho, encoding="utf-8").read()
erros, avisos = [], []

m = re.match(r"^---\n(.*?)\n---\n", texto, re.S)
if not m:
    erros.append("frontmatter YAML ausente ou malformado (precisa comecar com --- na linha 1)")
else:
    fm = m.group(1)

    mn = re.search(r"^name:\s*(.+)$", fm, re.M)
    if not mn:
        erros.append("campo 'name' ausente no frontmatter")
    else:
        name = mn.group(1).strip()
        if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name):
            erros.append(f"name '{name}' nao esta em kebab-case (so minusculas, numeros e hifen, sem hifen nas pontas)")
        if len(name) > 64:
            erros.append(f"name tem {len(name)} chars (limite 64)")
        if name != pasta:
            erros.append(f"name '{name}' difere do nome da pasta '{pasta}'")

    md = re.search(r"^description:\s*(>|\|)?\s*\n((?:[ \t]+.*\n?)+)|^description:\s*(.+)$", fm, re.M)
    if not md:
        erros.append("campo 'description' ausente no frontmatter")
    else:
        desc = (md.group(2) or md.group(3) or "").strip()
        desc = " ".join(l.strip() for l in desc.splitlines())
        if len(desc) > 1024:
            erros.append(f"description tem {len(desc)} chars (limite 1024)")
        elif len(desc) < 80:
            avisos.append(f"description tem so {len(desc)} chars - curta demais para o orquestrador rotear bem")
        else:
            print(f"  description: {len(desc)}/1024 chars")
        if "NÃO use" not in desc and "NAO use" not in desc:
            avisos.append("description nao diz QUANDO NAO USAR - risco de duas skills brigarem")

n_linhas = texto.count("\n") + 1
print(f"  tamanho: {n_linhas} linhas")
if n_linhas > 500:
    avisos.append(f"SKILL.md tem {n_linhas} linhas (recomendado <= 500; mova detalhe para references/)")

citadas = set(re.findall(r"\*\*`([^`]+)`\*\*", texto))
refs_tool = sorted(c for c in citadas if c in tools)
refs_know = sorted(c for c in citadas if c in knowledge)
for c in sorted(citadas):
    if c not in tools and c not in knowledge:
        erros.append(f"componente citado '{c}' nao existe: nao esta nas 8 tools nem nas 2 fontes de conhecimento")
if refs_tool:
    print(f"  tools: {', '.join(refs_tool)}")
if refs_know:
    print(f"  knowledge: {', '.join(refs_know)}")

for e in erros:
    print(f"  ERRO: {e}")
for a in avisos:
    print(f"  aviso: {a}")

sys.exit(1 if erros else 0)
PY
  [[ $? -ne 0 ]] && erros=$((erros+1))
done

printf '\n---------------------------------\n'
if [[ $erros -eq 0 ]]; then
  echo "OK: todas as skills passaram na validacao."
else
  echo "FALHOU: $erros skill(s) com erro."
  exit 1
fi
