#!/usr/bin/env python3
"""Gera o pacote de importação do Power Automate para o fluxo "Consumer Board Builder".

Segue a MESMA estrutura de pacote do gerador validado em campo
(scripts/gerar-fluxo.py) — inclusive o manifesto interno
Microsoft.Flow/flows/manifest.json + connectionsMap.json + apisMap.json, que é o
que o importador legado exige (sem eles: erro MissingPackageManifest).

Fluxo: gatilho do Copilot → Executar Office Script (gera o board) →
Criar consumer-martech.html no SharePoint → Responder ao agente com o link.

Uso:  python3 automation/gerar-consumer-flow.py <saida.zip>

Os apontamentos do tenant (workbook, script, site, pasta) entram como PLACEHOLDER
e são repostos no designer depois de importar.
"""
import json, sys, uuid, zipfile, datetime

NOME_FLUXO = "Consumer Board Builder"
DESCRICAO = ("Gera o board oficial de Consumer (B&W MarTech 2026 Agenda) rodando o "
             "Office Script no tracker e salvando o HTML no SharePoint. Chamado pelo agente.")


def excel_action(run_after):
    return {
        "runAfter": run_after, "type": "OpenApiConnection",
        "inputs": {
            "host": {"apiId": "/providers/Microsoft.PowerApps/apis/shared_excelonlinebusiness",
                     "connectionName": "shared_excelonlinebusiness",
                     "operationId": "RunScriptProV2"},
            "parameters": {
                "source": "me",
                "drive": "PLACEHOLDER_DRIVE_ID",
                "file": "PLACEHOLDER_WORKBOOK_ID",
                "scriptId": "PLACEHOLDER_SCRIPT_ID",
                "ScriptParameters": {},
            },
            "authentication": "@parameters('$authentication')",
        },
    }


def sp_create(run_after):
    return {
        "runAfter": run_after, "type": "OpenApiConnection",
        "inputs": {
            "host": {"apiId": "/providers/Microsoft.PowerApps/apis/shared_sharepointonline",
                     "connectionName": "shared_sharepointonline",
                     "operationId": "CreateFile"},
            "parameters": {
                "dataset": "https://PLACEHOLDER_TENANT.sharepoint.com/sites/PLACEHOLDER_SITE",
                "folderPath": "/Shared Documents/Consumer",
                "name": "consumer-martech.html",
                "body": "@body('Run_Office_Script')?['result']",
            },
            "authentication": "@parameters('$authentication')",
        },
        "runtimeConfiguration": {"contentTransfer": {"transferMode": "Chunked"}},
    }


def definicao():
    return {
        "$schema": ("https://schema.management.azure.com/providers/Microsoft.Logic"
                    "/schemas/2016-06-01/workflowdefinition.json#"),
        "contentVersion": "1.0.0.0",
        "parameters": {"$connections": {"defaultValue": {}, "type": "Object"},
                       "$authentication": {"defaultValue": {}, "type": "SecureObject"}},
        "triggers": {
            # Gatilho de BOTÃO ("Executar") — desserializa no importador legado.
            # O gatilho do Copilot (PowerVirtualAgents) NÃO importa por pacote; ele é
            # adicionado depois pelo Copilot Studio (Caminho A do README).
            "manually_triggered": {
                "type": "Request", "kind": "Button",
                "inputs": {"schema": {"type": "object", "properties": {}, "required": []}},
            }
        },
        "actions": {
            "Run_Office_Script": excel_action({}),
            "Create_board_html": sp_create({"Run_Office_Script": ["Succeeded"]}),
        },
        "outputs": {},
    }


def pacote(destino):
    fid, wid = str(uuid.uuid4()), str(uuid.uuid4())
    xl_api, xl_con = str(uuid.uuid4()), str(uuid.uuid4())
    sp_api, sp_con = str(uuid.uuid4()), str(uuid.uuid4())
    agora = datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.0000000Z")

    definition_json = {
        "name": wid, "id": f"/providers/Microsoft.Flow/flows/{wid}",
        "type": "Microsoft.Flow/flows",
        "properties": {
            "apiId": "/providers/Microsoft.PowerApps/apis/shared_logicflows",
            "displayName": NOME_FLUXO,
            "definition": definicao(),
            "connectionReferences": {
                "shared_excelonlinebusiness": {
                    "connectionName": f"shared-excelonlinebus-{xl_con}", "source": "Embedded",
                    "id": "/providers/Microsoft.PowerApps/apis/shared_excelonlinebusiness",
                    "tier": "NotSpecified", "apiName": "excelonlinebusiness"},
                "shared_sharepointonline": {
                    "connectionName": f"shared-sharepointonl-{sp_con}", "source": "Embedded",
                    "id": "/providers/Microsoft.PowerApps/apis/shared_sharepointonline",
                    "tier": "NotSpecified", "apiName": "sharepointonline"},
            },
            "flowFailureAlertSubscribed": False, "isManaged": False,
        },
    }

    ico_xl = ("https://static.powerapps.com/resource/ppcr/releases/v1.0.1813/"
              "1.0.1813.4769/excelonlinebusiness/icon.png")
    ico_sp = ("https://static.powerapps.com/resource/ppcr/releases/v1.0.1813/"
              "1.0.1813.4769/sharepointonline/icon.png")

    def api(nome, disp, icone):
        return {"id": f"/providers/Microsoft.PowerApps/apis/{nome}", "name": nome,
                "type": "Microsoft.PowerApps/apis", "suggestedCreationType": "Existing",
                "details": {"displayName": disp, "iconUri": icone},
                "configurableBy": "System", "hierarchy": "Child", "dependsOn": []}

    def conexao(icone, api_id):
        return {"type": "Microsoft.PowerApps/apis/connections",
                "suggestedCreationType": "Existing", "creationType": "Existing",
                "details": {"displayName": "Consumer Board Builder", "iconUri": icone},
                "configurableBy": "User", "hierarchy": "Child", "dependsOn": [api_id]}

    manifest = {
        "schema": "1.0",
        "details": {"displayName": NOME_FLUXO, "description": DESCRICAO,
                    "createdTime": agora, "packageTelemetryId": str(uuid.uuid4()),
                    "creator": "AURA", "sourceEnvironment": ""},
        "resources": {
            fid: {"type": "Microsoft.Flow/flows", "suggestedCreationType": "New",
                  "creationType": "New", "details": {"displayName": NOME_FLUXO},
                  "configurableBy": "User", "hierarchy": "Root",
                  "dependsOn": [xl_api, xl_con, sp_api, sp_con]},
            xl_api: api("shared_excelonlinebusiness", "Excel Online (Business)", ico_xl),
            xl_con: conexao(ico_xl, xl_api),
            sp_api: api("shared_sharepointonline", "SharePoint", ico_sp),
            sp_con: conexao(ico_sp, sp_api),
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
            {"shared_excelonlinebusiness": xl_con, "shared_sharepointonline": sp_con}))
        z.writestr(f"{base}/apisMap.json", json.dumps(
            {"shared_excelonlinebusiness": xl_api, "shared_sharepointonline": sp_api}))
    return destino


if __name__ == "__main__":
    destino = sys.argv[1] if len(sys.argv) > 1 else "automation/power-automate/ConsumerBoardBuilder_package.zip"
    print("gerado:", pacote(destino))
