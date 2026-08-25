#!/usr/bin/env python3
"""Valida os JSON de fluxo de flows/*/Workflows/ antes da importação.

O Power Automate só recusa um fluxo inválido na hora de **ativar**, e a
mensagem não diz onde. Esta checagem roda em segundos e pega a classe de erro
que já custou uma rodada de importação aqui:

    Flow save failed with code 'InvalidVariableInitialization' and message
    'The variable action 'Var_BU_Rows' of type 'InitializeVariable' cannot be
    nested in an action of type 'Scope_Main'.'

Checagens:
  1. InitializeVariable só na raiz — nunca dentro de Scope, If ou Foreach
  2. Response nunca dentro de Foreach/Until
  3. variables() só referencia variável declarada
  4. expressões com parênteses e aspas balanceados
  5. body()/outputs() só apontam para ação que existe
  6. placeholder {{X}} do Template com um replace correspondente
  7. descrição de entrada do gatilho <= 1024 chars
  8. gatilho `Skills` com `$connections` e `$authentication` declarados

Uso:  python3 scripts/validate-flows.py
"""
import glob
import io
import json
import pathlib
import re
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
LIMITE_DESCRICAO = 1024


def achatar(acoes, profundidade=0, caminho=""):
    """Todas as ações, com a profundidade de aninhamento de cada uma."""
    saida = {}
    for nome, acao in acoes.items():
        if not isinstance(acao, dict):
            continue
        saida[nome] = (acao, profundidade, caminho or "(raiz)")
        if "actions" in acao:
            saida.update(achatar(acao["actions"], profundidade + 1, caminho + "/" + nome))
        senao = acao.get("else")
        if isinstance(senao, dict):
            saida.update(achatar(senao.get("actions", {}), profundidade + 1,
                                 caminho + "/" + nome + "/else"))
    return saida


def desbalanceada(expr):
    """Parênteses/aspas de uma expressão do Logic Apps. '' é aspa escapada."""
    nivel, dentro, i = 0, False, 0
    while i < len(expr):
        c = expr[i]
        if c == "'":
            if dentro and i + 1 < len(expr) and expr[i + 1] == "'":
                i += 2
                continue
            dentro = not dentro
        elif not dentro:
            if c == "(":
                nivel += 1
            elif c == ")":
                nivel -= 1
                if nivel < 0:
                    return "fecha parêntese a mais"
        i += 1
    if nivel:
        return "faltam %d parêntese(s)" % nivel
    if dentro:
        return "aspa simples não fechada"
    return None


def expressoes(obj, caminho=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            for x in expressoes(v, caminho + "/" + str(k)):
                yield x
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            for x in expressoes(v, caminho + "/%d" % i):
                yield x
    elif isinstance(obj, str) and "@" in obj and "(" in obj:
        yield caminho, obj


def checar(caminho):
    erros, avisos = [], []
    doc = json.load(io.open(caminho, encoding="utf-8"))
    defi = doc["properties"]["definition"]
    acoes = achatar(defi["actions"])
    bruto = json.dumps(defi, ensure_ascii=False)

    # 1. InitializeVariable só na raiz
    declaradas = set()
    for nome, (acao, profundidade, pai) in acoes.items():
        if acao.get("type") != "InitializeVariable":
            continue
        for var in acao["inputs"]["variables"]:
            declaradas.add(var["name"])
        if profundidade:
            erros.append("`%s` é InitializeVariable dentro de %s — só pode na raiz do fluxo"
                         % (nome, pai))

    # 2. Response dentro de laço
    lacos = [n for n, (a, _, _) in acoes.items() if a.get("type") in ("Foreach", "Until")]
    for nome, (acao, _, pai) in acoes.items():
        if acao.get("type") == "Response" and any(("/" + l) in pai for l in lacos):
            erros.append("`%s` é um Response dentro de %s — laço não pode responder" % (nome, pai))

    # 3. variables() declarada
    for var in sorted(set(re.findall(r"variables\('([^']+)'\)", bruto))):
        if var not in declaradas:
            erros.append("variables('%s') sem InitializeVariable" % var)

    # 4. expressões balanceadas
    for onde, expr in expressoes(defi):
        problema = desbalanceada(expr)
        if problema:
            erros.append("expressão em %s: %s" % (onde, problema))

    # 5. referências entre ações
    for ref in sorted(set(re.findall(r"(?:body|outputs)\('([^']+)'\)", bruto))):
        if ref not in acoes:
            erros.append("body/outputs('%s') não existe no fluxo" % ref)

    # 6. placeholders do template
    template = defi["actions"].get("Template", {}).get("inputs")
    if isinstance(template, str):
        for ph in sorted(set(re.findall(r"\{\{[A-Z_0-9]+\}\}", template))):
            if bruto.count("'" + ph + "'") == 0:
                erros.append("placeholder %s no Template sem replace()" % ph)

    # 7. descrições do gatilho
    props = (defi.get("triggers", {}).get("manual", {}).get("inputs", {})
             .get("schema", {}).get("properties", {}))
    for nome, prop in props.items():
        n = len(prop.get("description", ""))
        if n > LIMITE_DESCRICAO:
            erros.append("descrição da entrada `%s`: %d/%d" % (nome, n, LIMITE_DESCRICAO))
        elif LIMITE_DESCRICAO - n < 74:
            avisos.append("descrição da entrada `%s`: %d/%d, só %d de folga"
                          % (nome, n, LIMITE_DESCRICAO, LIMITE_DESCRICAO - n))

    # 8. parâmetros que o runtime injeta e a definição precisa declarar
    gatilho = defi.get("triggers", {}).get("manual", {})
    declarados = set((defi.get("parameters") or {}).keys())
    if gatilho.get("kind") == "Skills":
        for exigido in ("$connections", "$authentication"):
            if exigido not in declarados:
                erros.append("gatilho Skills sem `%s` em definition.parameters — o runtime injeta "
                             "esse parâmetro e a ativação falha com InvalidTemplate" % exigido)

    for marcador in ("SEU_TENANT", "SEU_SITE", "SUBSTITUA"):
        if marcador in bruto:
            avisos.append("placeholder `%s` ainda no JSON — troque depois de importar" % marcador)

    return erros, avisos


def main():
    arquivos = sorted(glob.glob(str(RAIZ / "flows" / "*" / "Workflows" / "*.json")))
    if not arquivos:
        sys.exit("nenhum fluxo em flows/*/Workflows/")
    total_erros = total_avisos = 0
    for caminho in arquivos:
        erros, avisos = checar(caminho)
        print("\n=== %s ===" % pathlib.Path(caminho).name)
        for e in erros:
            print("  ERRO: %s" % e)
        for a in avisos:
            print("  aviso: %s" % a)
        if not erros and not avisos:
            print("  OK")
        total_erros += len(erros)
        total_avisos += len(avisos)
    print("\n" + "-" * 58)
    if total_erros:
        print("FALHOU: %d erro(s), %d aviso(s)." % (total_erros, total_avisos))
        sys.exit(1)
    print("OK: %d fluxo(s) válido(s), %d aviso(s)." % (len(arquivos), total_avisos))


if __name__ == "__main__":
    main()
