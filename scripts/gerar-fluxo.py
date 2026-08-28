#!/usr/bin/env python3
"""Gera um pacote de importacao do Power Automate para o fluxo de transcricoes.

Parte do fluxo validado em campo e aplica, por conta de origem:
  - dataset e driveId de quem organiza as reunioes
  - o nome real da pasta de gravacoes (varia com o idioma da conta)
  - a classificacao de area pelo nome do arquivo
  - o nome do arquivo de saida com a area e a hora

Uso:  python3 scripts/gerar-fluxo.py <config.json> <saida.zip>

O arquivo de configuracao carrega UPN e driveId reais e NAO deve ser
versionado. Ha um exemplo com marcadores em flows/config-exemplo.json.
"""
import json, sys, uuid, zipfile, datetime

NOME = "triggerOutputs()?['body/Name']"
NOME_LOWER = f"toLower({NOME})"


def expr_area(areas, prefixo=None):
    """Compose Area: o nome da area, ou string vazia se nao reconhecer.

    E a unica fonte da verdade da classificacao — a condicao do fluxo so
    checa se este Compose resolveu. Assim as palavras-chave vivem num lugar so.

    `prefixo` e uma ancora obrigatoria: quando informado, cada area so casa se
    o nome tambem contiver esse texto. Existe porque palavra-chave curta cabe
    dentro de outra palavra — 'cd' cabe em 'cdio', e sem a ancora uma reuniao
    "CDIO Sync" viraria uma transcricao de LT de CD, gravada com cara de certa.
    """
    def nivel(i):
        if i >= len(areas):
            return "''"
        a = areas[i]
        termos = [f"contains({NOME_LOWER}, '{k.lower()}')" for k in a["palavras"]]
        teste = termos[0] if len(termos) == 1 else "or(" + ", ".join(termos) + ")"
        if prefixo:
            teste = f"and(contains({NOME_LOWER}, '{prefixo.lower()}'), {teste})"
        return f"if({teste}, '{a['nome']}', {nivel(i + 1)})"
    return "@" + nivel(0)


def encerrar(codigo, mensagem):
    return {"runAfter": {}, "type": "Terminate",
            "inputs": {"runStatus": "Failed",
                       "runError": {"code": codigo, "message": mensagem}}}


def sp_action(operation, parameters, run_after):
    return {"runAfter": run_after, "type": "OpenApiConnection",
            "inputs": {"host": {"apiId": "/providers/Microsoft.PowerApps/apis/shared_sharepointonline",
                                "connectionName": "shared_sharepointonline",
                                "operationId": operation},
                       "parameters": parameters,
                       "authentication": "@parameters('$authentication')"}}


def definicao(c):
    pasta = c["pastaGravacoes"].strip("/")

    do_until = {
        "runAfter": {"Caminho": ["Succeeded"]},
        "type": "Until",
        "expression": "@greater(length(coalesce(body('Passo_4')?['value'], json('[]'))), 0)",
        "limit": {"count": 60, "timeout": "PT1H"},
        "actions": {
            "Delay": {"runAfter": {}, "type": "Wait",
                      "inputs": {"interval": {"count": 30, "unit": "Second"}}},
            "Passo_4": sp_action("HttpRequest", {
                "dataset": c["datasetOrigem"],
                "parameters/method": "GET",
                "parameters/uri": (f"_api/v2.1/drives/{c['driveId']}"
                                   "/root:@{outputs('Caminho')}:/media/transcripts"),
            }, {"Delay": ["Succeeded"]}),
            # Enquanto a transcricao processa a API responde 404. Sem esta acao,
            # o filho falhado derruba o Do until na primeira volta e o loop nunca espera.
            "Tolera": {
                "runAfter": {"Passo_4": ["Succeeded", "Failed", "TimedOut"]},
                "type": "Compose",
                "inputs": ("@if(equals(length(coalesce(body('Passo_4')?['value'], "
                           "json('[]'))), 0), 'aguardando', 'pronto')"),
            },
        },
    }

    gravar = {
        "TextoLimpo": {"runAfter": {}, "type": "Compose",
                       "inputs": "@join(body('Falas'), decodeUriComponent('%0A'))"},
        "Create_file": {
            **sp_action("CreateFile", {
                "dataset": c["datasetDestino"],
                "folderPath": c["pastaDestino"],
                "name": ("@concat('LT-', outputs('Area'), '-', formatDateTime("
                         "triggerOutputs()?['body/LastModified'], 'yyyy-MM-dd-HHmm'), '.txt')"),
                "body": "@outputs('TextoLimpo')",
            }, {"TextoLimpo": ["Succeeded"]}),
            "runtimeConfiguration": {"contentTransfer": {"transferMode": "Chunked"}},
        },
    }
    if c.get("bibliotecaDestino"):
        gravar["Update_file_properties"] = sp_action("PatchFileItem", {
            "dataset": c["datasetDestino"],
            "table": c["bibliotecaDestino"],
            "id": "@outputs('Create_file')?['body/ItemId']",
            "item/DataReuni_x00e3_o": ("@formatDateTime(triggerOutputs()?"
                                       "['body/LastModified'], 'yyyy-MM-dd')"),
            "item/Origem": "Teams",
        }, {"Create_file": ["Succeeded"]})

    condition_2 = {
        "runAfter": {"Do_until": ["Succeeded"]},
        "type": "If",
        "expression": {"and": [{"greater": [
            "@length(coalesce(body('Passo_4')?['value'], json('[]')))", 0]}]},
        "actions": {
            "Passo_5": {
                "runAfter": {}, "type": "Http",
                "inputs": {"method": "GET",
                           "uri": "@last(body('Passo_4')?['value'])?['temporaryDownloadUrl']"},
                "runtimeConfiguration": {"contentTransfer": {"transferMode": "Chunked"}},
            },
            "Linhas": {"runAfter": {"Passo_5": ["Succeeded"]}, "type": "Compose",
                       "inputs": ("@split(replace(string(body('Passo_5')), "
                                  "decodeUriComponent('%0D'), ''), decodeUriComponent('%0A'))")},
            "Falas": {"runAfter": {"Linhas": ["Succeeded"]}, "type": "Query",
                      "inputs": {"from": "@outputs('Linhas')",
                                 "where": ("@and(not(empty(item())), not(equals(item(), 'WEBVTT')), "
                                           "not(contains(item(), '-->')), or(contains(item(), ' '), "
                                           "not(contains(item(), '/'))))")}},
            "Condition_1": {
                "runAfter": {"Falas": ["Succeeded"]}, "type": "If",
                "expression": {"and": [{"greater": ["@length(body('Falas'))", 0]}]},
                "actions": gravar,
                "else": {"actions": {"TranscricaoVazia": encerrar(
                    "TranscricaoVazia",
                    "O filtro nao achou linhas de fala. Abra a saida do Passo 5.")}},
            },
        },
        "else": {"actions": {"TranscricaoNaoFicouPronta": encerrar(
            "TranscricaoNaoFicouPronta",
            "O Do until esgotou as tentativas e a transcricao nunca ficou pronta.")}},
    }

    return {
        "$schema": ("https://schema.management.azure.com/providers/Microsoft.Logic"
                    "/schemas/2016-06-01/workflowdefinition.json#"),
        "contentVersion": "1.0.0.0",
        "parameters": {"$connections": {"defaultValue": {}, "type": "Object"},
                       "$authentication": {"defaultValue": {}, "type": "SecureObject"}},
        "triggers": {
            "When_a_file_is_created_(properties_only)": {
                "recurrence": {"frequency": "Minute", "interval": 1},
                "splitOn": "@triggerOutputs()?['body']",
                "metadata": {c["folderId"]: "/" + pasta},
                "type": "OpenApiConnection",
                "inputs": {
                    "host": {"apiId": "/providers/Microsoft.PowerApps/apis/shared_onedriveforbusiness",
                             "connectionName": "shared_onedriveforbusiness",
                             "operationId": "OnNewFilesV2"},
                    "parameters": {"folderId": c["folderId"], "includeSubfolders": False,
                                   "maxFileCount": 10},
                    "authentication": "@parameters('$authentication')",
                },
            }
        },
        "actions": {
            "Area": {"runAfter": {}, "type": "Compose",
                     "inputs": expr_area(c["areas"], c.get("prefixoObrigatorio"))},
            "Condition": {
                "runAfter": {"Area": ["Succeeded"]},
                "type": "If",
                # .mp4 E o Area resolveu. Gravacao que nao e de nenhuma das reunioes
                # cai no ramo vazio e o fluxo termina VERDE sem fazer nada — que e o
                # comportamento certo numa pasta pessoal cheia de outras reunioes.
                "expression": {"and": [
                    {"equals": [f"@endsWith({NOME_LOWER}, '.mp4')", True]},
                    {"greater": ["@length(outputs('Area'))", 0]},
                ]},
                "actions": {
                    "Caminho": {"runAfter": {}, "type": "Compose",
                                "inputs": (f"@concat('/{pasta}/', replace({NOME}, ' ', '%20'))")},
                    "Do_until": do_until,
                    "Condition_2": condition_2,
                },
                "else": {"actions": {}},
            },
        },
        "outputs": {},
    }


def pacote(c, destino):
    fid, wid = str(uuid.uuid4()), str(uuid.uuid4())
    sp_api, sp_con = str(uuid.uuid4()), str(uuid.uuid4())
    od_api, od_con = str(uuid.uuid4()), str(uuid.uuid4())
    agora = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.0000000Z")

    definition_json = {
        "name": wid, "id": f"/providers/Microsoft.Flow/flows/{wid}",
        "type": "Microsoft.Flow/flows",
        "properties": {
            "apiId": "/providers/Microsoft.PowerApps/apis/shared_logicflows",
            "displayName": c["nomeDoFluxo"],
            "definition": definicao(c),
            "connectionReferences": {
                "shared_sharepointonline": {
                    "connectionName": f"shared-sharepointonl-{sp_con}", "source": "Embedded",
                    "id": "/providers/Microsoft.PowerApps/apis/shared_sharepointonline",
                    "tier": "NotSpecified", "apiName": "sharepointonline"},
                "shared_onedriveforbusiness": {
                    "connectionName": f"shared-onedriveforbu-{od_con}", "source": "Embedded",
                    "id": "/providers/Microsoft.PowerApps/apis/shared_onedriveforbusiness",
                    "tier": "NotSpecified", "apiName": "onedriveforbusiness"},
            },
            "flowFailureAlertSubscribed": False, "isManaged": False,
        },
    }

    ico_sp = ("https://static.powerapps.com/resource/ppcr/releases/v1.0.1813/"
              "1.0.1813.4769/sharepointonline/icon.png")
    ico_od = ("https://static.powerapps.com/resource/ppcr/releases/v1.0.1825/"
              "1.0.1825.4855/onedriveforbusiness/icon.png")

    def api(nome, disp, icone):
        return {"id": f"/providers/Microsoft.PowerApps/apis/{nome}", "name": nome,
                "type": "Microsoft.PowerApps/apis", "suggestedCreationType": "Existing",
                "details": {"displayName": disp, "iconUri": icone},
                "configurableBy": "System", "hierarchy": "Child", "dependsOn": []}

    def conexao(icone, api_id):
        return {"type": "Microsoft.PowerApps/apis/connections",
                "suggestedCreationType": "Existing", "creationType": "Existing",
                "details": {"displayName": c["donoDaConta"], "iconUri": icone},
                "configurableBy": "User", "hierarchy": "Child", "dependsOn": [api_id]}

    manifest = {
        "schema": "1.0",
        "details": {"displayName": c["nomeDoFluxo"], "description": c.get("descricao", ""),
                    "createdTime": agora, "packageTelemetryId": str(uuid.uuid4()),
                    "creator": "N/A", "sourceEnvironment": ""},
        "resources": {
            fid: {"type": "Microsoft.Flow/flows", "suggestedCreationType": "New",
                  "creationType": "New", "details": {"displayName": c["nomeDoFluxo"]},
                  "configurableBy": "User", "hierarchy": "Root",
                  "dependsOn": [sp_api, sp_con, od_api, od_con]},
            sp_api: api("shared_sharepointonline", "SharePoint", ico_sp),
            sp_con: conexao(ico_sp, sp_api),
            od_api: api("shared_onedriveforbusiness", "OneDrive for Business", ico_od),
            od_con: conexao(ico_od, od_api),
        },
    }

    base = f"Microsoft.Flow/flows/{fid}"
    with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("manifest.json", json.dumps(manifest))
        z.writestr("Microsoft.Flow/flows/manifest.json",
                   json.dumps({"packageSchemaVersion": "1.0",
                               "flowAssets": {"assetPaths": [fid]}}))
        z.writestr(f"{base}/definition.json", json.dumps(definition_json))
        z.writestr(f"{base}/connectionsMap.json", json.dumps(
            {"shared_sharepointonline": sp_con, "shared_onedriveforbusiness": od_con}))
        z.writestr(f"{base}/apisMap.json", json.dumps(
            {"shared_sharepointonline": sp_api, "shared_onedriveforbusiness": od_api}))
    return destino


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    cfg = json.load(open(sys.argv[1], encoding="utf-8"))
    print("gerado:", pacote(cfg, sys.argv[2]))
    print("  Area:", expr_area(cfg["areas"], cfg.get("prefixoObrigatorio")))
