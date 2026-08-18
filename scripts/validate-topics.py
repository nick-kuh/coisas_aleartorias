#!/usr/bin/env python3
"""Valida os tópicos de topics/*.yaml contra o dialeto YAML do Copilot Studio.

O Copilot Studio NÃO implementa a especificação YAML completa — implementa um
subconjunto restrito. Validar só com PyYAML dá falsa confiança: um arquivo pode
ser YAML perfeitamente válido e mesmo assim o editor de código recusar com

    Error reading YAML content near line N position M: UnexpectedToken,
    expected: UnquotedValue or QuotedStringValue or MultilineStringValue

Por isso este script roda uma checagem de DIALETO antes do parse, além das
checagens estruturais.

Checagens:
  1. dialeto  — folded scalars (`>` / `>-`), âncoras, aliases, tags, multi-doc
  2. sintaxe  — YAML parseável, root `kind: AdaptiveDialog`, gatilho conhecido
  3. estrutura— ids de nó únicos
  4. vocabulário — `kind:` de nó e entidades conferidos contra um export real
  5. referências — toda tool citada em `dialog:` existe no agente exportado
  6. limites  — descrição de entrada <= 1024 chars, instruções <= 8000 chars

O produto trunca silenciosamente o que passa do limite, e o corte come o FIM
do texto — justamente onde costumam ficar as regras mais restritivas. Por isso
a checagem 6 mede em vez de confiar na memória.

Uso:
    python3 scripts/validate-topics.py [--referencia caminho/para/botContent.yml]

Sem --referencia, procura o export nos caminhos conhecidos. Não achando, as
checagens 4 e 5 são puladas com aviso.
"""
import argparse
import pathlib
import re
import sys

try:
    import yaml
except ImportError:
    sys.exit("PyYAML necessário: pip install pyyaml")

RAIZ = pathlib.Path(__file__).resolve().parent.parent

GATILHOS = {
    "OnRecognizedIntent", "OnConversationStart", "OnUnknownIntent",
    "OnError", "OnEscalate", "OnSelectIntent", "OnRedirect",
}

CAMINHOS_EXPORT = [
    "/tmp/claude-0/-home-user-coisas-aleartorias/"
    "6ba1a081-012a-5b4c-8514-2fdd5144fd8d/scratchpad/zip69/botContent.yml",
    "/tmp/claude-0/-home-user-coisas-aleartorias/"
    "6ba1a081-012a-5b4c-8514-2fdd5144fd8d/scratchpad/zipx/botContent.yml",
    RAIZ / "botContent.yml",
]

# Construções YAML válidas na spec, mas ausentes de todo export do Copilot
# Studio — e que o parser do produto recusa.
PROIBIDO = [
    (
        re.compile(r":\s*>-?\s*$"),
        "folded block scalar (`>` / `>-`)",
        "use `|-` — o parser do Copilot Studio não reconhece `>`, "
        "e reporta o erro só no fim do arquivo",
    ),
    (
        re.compile(r":\s*&\w"),
        "âncora YAML (`&nome`)",
        "escreva o valor por extenso; âncoras não aparecem em nenhum export",
    ),
    (
        re.compile(r":\s*\*\w"),
        "alias YAML (`*nome`)",
        "escreva o valor por extenso",
    ),
    (
        re.compile(r":\s*!!"),
        "tag YAML (`!!tipo`)",
        "remova a tag; o tipo é inferido",
    ),
    (
        re.compile(r"^---\s*$"),
        "separador de documento (`---`)",
        "um arquivo = um documento; remova o separador",
    ),
]


def checar_dialeto(texto):
    """Erros que o PyYAML aceita mas o Copilot Studio recusa."""
    problemas = []
    for n, linha in enumerate(texto.splitlines(), 1):
        if linha.lstrip().startswith("#"):
            continue
        for padrao, o_que, saida in PROIBIDO:
            if padrao.search(linha):
                problemas.append((n, o_que, saida, linha.strip()))
    return problemas


# entity → tipo inferido pelo type checker do Copilot Studio.
TIPOS_DE_ENTITY = {
    "StringPrebuiltEntity":   "String",
    "NumberPrebuiltEntity":   "Number",
    "BooleanPrebuiltEntity":  "Boolean",
    "DateTimePrebuiltEntity": "DateTime",
}


def _tipo_da_entity(ent):
    """Reduz a entity de uma Question ao tipo que o type checker infere.
    Retorna None quando a entity não é reconhecida (não geramos alarme falso)."""
    if isinstance(ent, str):
        return TIPOS_DE_ENTITY.get(ent)
    if isinstance(ent, dict):
        if ent.get("kind") == "EmbeddedEntity":
            defn = ent.get("definition") or {}
            if defn.get("kind") in ("ClosedListEntity", "DynamicClosedListEntity"):
                return "EmbeddedOptionSet"
        return TIPOS_DE_ENTITY.get(ent.get("kind"))
    return None


def tipos_por_variavel(doc):
    """Mapa `Topic.X` → lista de tipos inferidos, um por Question que a define.

    Se aparecerem tipos diferentes para a mesma variável, o type checker do
    Copilot Studio reprova com "A variável está sendo definida com um tipo
    incorreto". Este mapa alimenta duas checagens: colisão de tipos e a regra
    específica de `EmbeddedOptionSet` precisar de `Text()` na comparação."""
    tipos = {}

    def anda(no):
        if isinstance(no, dict):
            if no.get("kind") == "Question" and isinstance(no.get("variable"), str):
                t = _tipo_da_entity(no.get("entity"))
                if t is not None:
                    tipos.setdefault(no["variable"], []).append(t)
            for v in no.values():
                anda(v)
        elif isinstance(no, list):
            for item in no:
                anda(item)

    anda(doc)
    return tipos


def variaveis_de_closed_list(doc):
    """Variáveis que o produto tipa como `EmbeddedOptionSet` — reusa
    `tipos_por_variavel`. Comparar com string literal exige `Text()`."""
    return {var for var, ts in tipos_por_variavel(doc).items() if "EmbeddedOptionSet" in ts}


# Combinações válidas do conector Microsoft Teams "Post message in a chat or
# channel". O próprio schema da action documenta a regra:
#   "Use 'Chat with Flow bot' only when poster is 'Flow bot' or 'Power Virtual Agents'."
# poster: User = signed-in user
# poster: Flow bot = Power Automate bot
# poster: Power Virtual Agents = Microsoft Copilot Studio agent publicado no Teams
# location: Group chat / Channel / Chat with Flow bot ("powerva" no YAML)
POSTER_LOCATION_VALIDO = {
    "User":                 {"Group chat", "Channel"},
    "Flow bot":             {"Group chat", "Channel", "Chat with Flow bot", "powerva"},
    "Power Virtual Agents": {"Chat with Flow bot", "powerva"},
}


def teams_poster_location_coerente(doc):
    """Encontra BeginDialog para a tool do Teams com par poster/location inválido."""
    problemas = []

    def anda(no):
        if isinstance(no, dict):
            if (no.get("kind") == "BeginDialog"
                    and isinstance(no.get("dialog"), str)
                    and "MicrosoftTeams-Postarmensagem" in no["dialog"]):
                inp = no.get("input") or {}
                poster = inp.get("poster")
                location = inp.get("location")
                if isinstance(poster, str) and isinstance(location, str):
                    validos = POSTER_LOCATION_VALIDO.get(poster)
                    if validos and location not in validos:
                        problemas.append((poster, location, sorted(validos)))
            for v in no.values():
                anda(v)
        elif isinstance(no, list):
            for item in no:
                anda(item)

    anda(doc)
    return problemas


def comparacoes_sem_text(texto, variaveis_option_set):
    """Encontra `condition: =<Var> = "literal"` sem `Text()` envolvendo a variável."""
    problemas = []
    for n, linha in enumerate(texto.splitlines(), 1):
        # só condições que atribuem valor Power Fx
        m = re.match(r"^\s*condition:\s*=(.+)$", linha)
        if not m:
            continue
        expr = m.group(1)
        for var in variaveis_option_set:
            # Var = "..."  ou "..." = Var, mas SEM Text(...) envolvendo
            var_esc = re.escape(var)
            # ocorrência crua da variável comparada com string
            padrao_cru = re.compile(
                rf"(?<!Text\(){var_esc}\s*=\s*\"|\"\s*=\s*{var_esc}(?!\))"
            )
            if padrao_cru.search(expr):
                problemas.append((n, var, linha.strip()))
                break
    return problemas


def ids_de_no(doc):
    """Os `id:` que identificam nó, ignorando os `id:` dentro de `input:`
    (ali é nome de parâmetro da tool, não identificador de nó)."""
    achados = []

    def anda(no, dentro_de_input=False):
        if isinstance(no, dict):
            if not dentro_de_input and isinstance(no.get("id"), str):
                achados.append(no["id"])
            for chave, valor in no.items():
                anda(valor, dentro_de_input or chave == "input")
        elif isinstance(no, list):
            for item in no:
                anda(item, dentro_de_input)

    anda(doc)
    return achados


def tools_do_agente(conteudo):
    """Componentes do agente ALVO — as tools que os tópicos podem referenciar."""
    return set(re.findall(r"schemaName: (\S+\.(?:action|topic)\.\S+)", conteudo))


def vocabulario(conteudos):
    """Vocabulário aceito pelo dialeto, somando TODOS os exports disponíveis.

    Kinds e entidades são propriedade da linguagem, não do agente: se aparecem
    em qualquer export real do Copilot Studio, o produto os aceita. Por isso a
    união — usar só o export do agente atual gera aviso falso para construções
    que ele simplesmente ainda não usa.
    """
    kinds, entidades = set(), set()
    for c in conteudos:
        kinds |= set(re.findall(r"^\s*-? ?kind: (\w+)$", c, re.M))
        entidades |= set(re.findall(r"entity: (\w+PrebuiltEntity)", c))
    return {"kinds": kinds, "entidades": entidades}


# ---------------------------------------------------------------- limites
# Tetos do produto, confirmados contra o export do agente ao vivo
# (botContent_75: descrição do `query` com 940 chars, `userEnteredFields` 570).
LIMITE_DESCRICAO = 1024
LIMITE_INSTRUCOES = 8000

# O Copilot Studio NÃO guarda as instruções como você cola. Toda menção a uma
# tool vira uma referência {System.Bot.Components.Actions.'…'.DisplayName}.
# Medido no botContent_76: 8 menções inflaram o texto em +736 caracteres
# (6.657 no arquivo -> 7.393 no agente). Ou seja, ~92 por menção.
# Medir só o arquivo dá falsa folga — por isso a estimativa abaixo.
#
# A estimativa é deliberadamente CONSERVADORA: conta toda ocorrência do nome,
# enquanto o produto converteu 8 de 11 no export real. Erra para o lado de
# avisar cedo, que é o lado certo quando o custo do erro é texto truncado.
INFLACAO_POR_MENCAO = 92
TOOLS_DO_AGENTE = (
    "Power BI Portfolio Database", "Power BI Master DB Search",
    "DevOps Work Item Details", "Devops Query (Knowledge)",
    "Query Devops IT Area", "Query Devops BU", "Update Project",
    "Postar mensagem em um chat ou canal",
)
MARGEM_APERTADA = 74          # avisa quando sobra menos que isto

DOC_TOOLS = "docs/standard/02-correcao-das-tools.md"
DOC_INSTRUCOES = "agent/instructions-standard.md"

# Blocos coláveis: um marcador em negrito seguido de uma cerca ```
MARCADOR = re.compile(
    r"\*\*Descrição d[ao] (?:entrada|tool)[^*]*\*\*[^\n]*\n+```\n(.*?)\n```",
    re.S,
)


def checar_limites(raiz):
    """Mede os textos que o usuário cola no Copilot Studio."""
    erros = avisos = 0

    doc = raiz / DOC_TOOLS
    if doc.exists():
        texto = doc.read_text(encoding="utf-8")
        blocos = MARCADOR.findall(texto)
        print(f"\n=== limites de descrição ({len(blocos)} bloco(s) colável(is)) ===")
        for bloco in blocos:
            corpo = bloco.strip()
            n = len(corpo)
            rotulo = corpo.split("\n")[0][:44].rstrip() + "…"
            if n > LIMITE_DESCRICAO:
                print(f"  ERRO: {n}/{LIMITE_DESCRICAO} — estoura {n - LIMITE_DESCRICAO} | {rotulo}")
                erros += 1
            elif LIMITE_DESCRICAO - n < MARGEM_APERTADA:
                print(f"  aviso: {n}/{LIMITE_DESCRICAO} — só {LIMITE_DESCRICAO - n} de folga | {rotulo}")
                avisos += 1
            else:
                print(f"  OK {n}/{LIMITE_DESCRICAO} (folga {LIMITE_DESCRICAO - n}) | {rotulo}")
    else:
        print(f"\n  aviso: {DOC_TOOLS} não encontrado — limites de descrição não medidos")
        avisos += 1

    instr = raiz / DOC_INSTRUCOES
    if instr.exists():
        texto = instr.read_text(encoding="utf-8")
        bruto = len(texto)
        mencoes = sum(texto.count(t) for t in TOOLS_DO_AGENTE)
        estimado = bruto + mencoes * INFLACAO_POR_MENCAO
        print(f"\n=== instruções ===")
        print(f"  arquivo: {bruto} chars · {mencoes} menção(ões) de tool "
              f"(+{mencoes * INFLACAO_POR_MENCAO} ao colar, estimativa conservadora)")
        if estimado > LIMITE_INSTRUCOES:
            print(f"  ERRO: ~{estimado}/{LIMITE_INSTRUCOES} no agente — estoura {estimado - LIMITE_INSTRUCOES}")
            erros += 1
        else:
            print(f"  OK ~{estimado}/{LIMITE_INSTRUCOES} no agente (folga {LIMITE_INSTRUCOES - estimado})")
    else:
        print(f"\n  aviso: {DOC_INSTRUCOES} não encontrado — instruções não medidas")
        avisos += 1

    return erros, avisos


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--referencia", type=pathlib.Path,
                    help="botContent.yml do agente, para conferir vocabulário e tools")
    args = ap.parse_args()

    disponiveis = [p for p in map(pathlib.Path, CAMINHOS_EXPORT) if p.exists()]
    alvo = args.referencia if args.referencia else (disponiveis[0] if disponiveis else None)

    if alvo and alvo.exists():
        if alvo not in disponiveis:
            disponiveis.insert(0, alvo)
        tools = tools_do_agente(alvo.read_text(encoding="utf-8"))
        vocab = vocabulario([p.read_text(encoding="utf-8") for p in disponiveis])
        vocab["tools"] = tools
        print(f"Agente alvo: {alvo.name} ({len(tools)} componentes)")
        print(f"Vocabulário de {len(disponiveis)} export(s): "
              f"{len(vocab['kinds'])} kinds · {len(vocab['entidades'])} entidades prebuilt")
    else:
        vocab = None
        print("Export de referência não encontrado — vocabulário e tools NÃO conferidos.")

    erros = avisos = 0
    for caminho in sorted((RAIZ / "topics").glob("*.yaml")):
        texto = caminho.read_text(encoding="utf-8")
        print(f"\n=== {caminho.name} ===")

        # 1. dialeto — antes do parse, porque é o que o PyYAML deixa passar
        problemas = checar_dialeto(texto)
        for n, o_que, saida, linha in problemas:
            print(f"  ERRO dialeto (linha {n}): {o_que}")
            print(f"       {linha[:70]}")
            print(f"       -> {saida}")
            erros += 1
        if not problemas:
            print("  dialeto: OK")

        # 2. sintaxe
        try:
            doc = yaml.safe_load(texto)
        except yaml.YAMLError as e:
            print(f"  ERRO: YAML inválido — {e}")
            erros += 1
            continue

        if doc.get("kind") != "AdaptiveDialog":
            print(f"  ERRO: root kind é {doc.get('kind')!r}, esperado 'AdaptiveDialog'")
            erros += 1

        gatilho = doc.get("beginDialog", {}).get("kind")
        if gatilho not in GATILHOS:
            print(f"  ERRO: gatilho {gatilho!r} desconhecido")
            erros += 1
        else:
            queries = doc["beginDialog"].get("intent", {}).get("triggerQueries", [])
            print(f"  gatilho: {gatilho}" + (f" ({len(queries)} frases)" if queries else ""))

        # 3. estrutura
        ids = ids_de_no(doc)
        duplicados = sorted({i for i in ids if ids.count(i) > 1})
        if duplicados:
            print(f"  ERRO: ids de nó duplicados: {', '.join(duplicados)}")
            erros += 1
        else:
            print(f"  ids de nó: {len(ids)}, todos únicos")

        # 3b. type check — o Copilot Studio faz isto no publish
        tipos = tipos_por_variavel(doc)

        # 3b.i colisão: mesma variável recebe tipos diferentes de Questions
        colisoes = {var: sorted(set(ts)) for var, ts in tipos.items() if len(set(ts)) > 1}
        for var, ts in colisoes.items():
            print(f"  ERRO tipo: {var} recebe tipos diferentes ({', '.join(ts)})")
            print(f"       -> cada variável tem UM tipo, fixado na primeira Question.")
            print(f"       -> use variáveis separadas por branch (ex.: Topic.NovaData, Topic.NovoNumero)")
            erros += 1

        # 3b.ii EmbeddedOptionSet precisa de Text() na comparação
        vars_choice = {var for var, ts in tipos.items() if "EmbeddedOptionSet" in ts}
        faltando = comparacoes_sem_text(texto, vars_choice) if vars_choice else []
        for n, var, linha in faltando:
            print(f"  ERRO tipo (linha {n}): {var} vem de ClosedListEntity")
            print(f"       {linha[:70]}")
            print(f"       -> envolva em Text(): condition: =Text({var}) = \"...\"")
            print(f"       (padrão do export antigo: Text(Topic.MeetingArea))")
            erros += 1

        # 3b.iii Teams: poster e location precisam ser coerentes
        teams_ruins = teams_poster_location_coerente(doc)
        for poster, location, validos in teams_ruins:
            print(f"  ERRO Teams: poster '{poster}' + location '{location}' inválido")
            print(f"       -> com poster='{poster}', location precisa ser um de: {', '.join(validos)}")
            print(f"       (schema: \"Chat with Flow bot\" só vale com Flow bot ou Copilot Studio agent)")
            erros += 1

        if not colisoes and not faltando and not teams_ruins:
            n_choice = len(vars_choice)
            print(f"  type check: OK ({len(tipos)} var(s) tipadas" +
                  (f", {n_choice} choice com Text())" if n_choice else ")"))

        if vocab is None:
            continue

        # 4. vocabulário — aviso, não erro: o export cobre só o que o agente usa
        for kind in sorted(set(re.findall(r"^\s*-? ?kind: (\w+)$", texto, re.M))):
            if kind not in vocab["kinds"] and kind != "AdaptiveDialog":
                print(f"  aviso: kind '{kind}' não aparece no export de referência")
                avisos += 1
        for ent in sorted(set(re.findall(r"entity: (\w+PrebuiltEntity)", texto))):
            if ent not in vocab["entidades"]:
                print(f"  aviso: entidade '{ent}' não aparece no export "
                      f"(comprovadas: {', '.join(sorted(vocab['entidades'])) or 'nenhuma'})")
                avisos += 1

        # 5. referências
        for ref in sorted(set(re.findall(r"dialog: (\S+\.action\.\S+)", texto))):
            if ref in vocab["tools"]:
                print(f"  OK {ref}")
            else:
                print(f"  ERRO: tool inexistente no agente — {ref}")
                erros += 1

    e_lim, a_lim = checar_limites(pathlib.Path(__file__).resolve().parent.parent)
    erros += e_lim
    avisos += a_lim

    print("\n" + "-" * 58)
    if erros:
        print(f"FALHOU: {erros} erro(s)" + (f", {avisos} aviso(s)." if avisos else "."))
        return 1
    print(f"OK: todos os tópicos válidos" + (f" ({avisos} aviso(s) a conferir na UI)." if avisos else "."))
    return 0


if __name__ == "__main__":
    sys.exit(main())
