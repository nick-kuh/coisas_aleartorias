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

    print("\n" + "-" * 58)
    if erros:
        print(f"FALHOU: {erros} erro(s)" + (f", {avisos} aviso(s)." if avisos else "."))
        return 1
    print(f"OK: todos os tópicos válidos" + (f" ({avisos} aviso(s) a conferir na UI)." if avisos else "."))
    return 0


if __name__ == "__main__":
    sys.exit(main())
