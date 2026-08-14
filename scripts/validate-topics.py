#!/usr/bin/env python3
"""Valida os tópicos de topics/*.yaml contra o export do agente.

Confere:
  - YAML parseável e root `kind: AdaptiveDialog`
  - gatilho presente (OnRecognizedIntent / OnConversationStart / ...)
  - ids de nó únicos dentro do tópico
  - toda tool referenciada em `dialog:` existe de fato no agente exportado

Uso:
    python3 scripts/validate-topics.py [caminho/para/botContent.yml]

Sem argumento, procura o export nos caminhos conhecidos e, se não achar,
valida só a estrutura e avisa que não conferiu as referências.
"""
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


def ids_de_no(doc):
    """Coleta os `id:` que são identificadores de nó, ignorando os `id:`
    que aparecem dentro de blocos `input:` (ali é nome de parâmetro da tool)."""
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


def main():
    if len(sys.argv) > 1:
        export = pathlib.Path(sys.argv[1])
    else:
        export = next(
            (p for p in map(pathlib.Path, [
                "/tmp/claude-0/-home-user-coisas-aleartorias/"
                "6ba1a081-012a-5b4c-8514-2fdd5144fd8d/scratchpad/zip69/botContent.yml",
                RAIZ / "botContent.yml",
            ]) if p.exists()),
            None,
        )

    if export:
        conteudo = export.read_text(encoding="utf-8")
        tools = set(re.findall(r"schemaName: (\S+\.(?:action|topic)\.\S+)", conteudo))
        print(f"Export: {export}  ({len(tools)} componentes)")
    else:
        tools = None
        print("Export não encontrado — referências de tool NÃO serão conferidas.")

    erros = 0
    for caminho in sorted((RAIZ / "topics").glob("*.yaml")):
        texto = caminho.read_text(encoding="utf-8")
        print(f"\n=== {caminho.name} ===")

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

        ids = ids_de_no(doc)
        duplicados = sorted({i for i in ids if ids.count(i) > 1})
        if duplicados:
            print(f"  ERRO: ids de nó duplicados: {', '.join(duplicados)}")
            erros += 1
        else:
            print(f"  ids de nó: {len(ids)}, todos únicos")

        referencias = sorted(set(re.findall(r"dialog: (\S+\.action\.\S+)", texto)))
        for ref in referencias:
            if tools is None:
                print(f"  ?  {ref}")
            elif ref in tools:
                print(f"  OK {ref}")
            else:
                print(f"  ERRO: tool inexistente no agente — {ref}")
                erros += 1

    print("\n" + "-" * 55)
    if erros:
        print(f"FALHOU: {erros} problema(s).")
        return 1
    print("OK: todos os tópicos válidos.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
