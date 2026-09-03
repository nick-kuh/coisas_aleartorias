#!/usr/bin/env python3
"""
Gera consumer-martech.html — a "B&W Marketing Technology 2026 Agenda" do time de
Consumer BPC — a partir do tracker Excel. Layout de agenda em cards (um card por
frente), paleta lavanda, chips BR/MX/AR coloridos pelo status. Mesmo esquema que
a skill `consumer-martech` descreve para o agente montar a página.

Uso:
    python3 scripts/gerar-consumer-html.py
    python3 scripts/gerar-consumer-html.py caminho/para/outro.xlsx saida.html

Os cards das frentes saem 100% do Excel. A faixa "Marketing Operations" no rodapé
é um elemento fixo do layout (vindo do board de referência), definida em OPS_BAND.
"""
import sys
from pathlib import Path
from datetime import date

import openpyxl

RAIZ = Path(__file__).resolve().parent.parent
XLSX_PADRAO = RAIZ / "data" / "BW_MarTech_2026_Controle_Projetos.xlsx"
SAIDA_PADRAO = RAIZ / "consumer-martech.html"

FRENTES = [
    "Insights",
    "Media & Influencer",
    "dCom and Social Commerce",
    "CoPilot and Agentic",
    "LLM Search / GEO",
    "Beauty Tech",
]

# status PT -> (classe do chip, rótulo EN)
STATUS = {
    "No prazo":     ("good", "On Track"),
    "Atenção":      ("warn", "At Risk"),
    "Crítico":      ("bad",  "Critical"),
    "Não iniciado": ("idle", "Not Started"),
    "N/A":          ("na",   "N/A"),
}
MERCADOS = ["BR", "MX", "AR"]

# Faixa "Marketing Operations" — elemento fixo do board (não vem do Excel).
OPS_BAND = [
    {"tipo": "fases", "titulo": "Social Media Access Mgmt",
     "linhas": [("Deployment", ["Não iniciado", "Não iniciado", "Não iniciado"]),
                ("Adoption",    ["Não iniciado", "Não iniciado", "Não iniciado"])]},
    {"tipo": "contador", "titulo": "Operational Support",  "valores": [0, 0, 0]},
    {"tipo": "contador", "titulo": "Cyber/AI Assessments", "valores": [0, 0, 0]},
    {"tipo": "contador", "titulo": "Automation Requests",  "valores": [0, 0, 0]},
]


def ler_tracker(xlsx):
    wb = openpyxl.load_workbook(xlsx, data_only=True)
    ws = wb["Tracker"]
    linhas = []
    for row in ws.iter_rows(min_row=4, values_only=True):
        frente = (row[0] or "").strip() if row[0] else ""
        if not frente:
            continue
        linhas.append({
            "frente": frente,
            "iniciativa": (row[1] or "").strip() if row[1] else "",
            "item": (row[2] or "").strip() if row[2] else "",
            "fase": (row[3] or "").strip() if row[3] else "",
            "BR": (row[4] or "").strip() if row[4] else "",
            "MX": (row[5] or "").strip() if row[5] else "",
            "AR": (row[6] or "").strip() if row[6] else "",
        })
    return linhas


def esc(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def chip(code, status):
    if not status:
        return f'<span class="chip empty">{code}</span>'
    cls, en = STATUS.get(status, ("idle", status))
    label = "–" if status == "N/A" else code
    return f'<span class="chip {cls}" title="{esc(code)} · {esc(status)} ({esc(en)})">{label}</span>'


def rotulo(l):
    """Rótulo da linha: o item, senão a fase (para Deployment/Adoption)."""
    if l["item"]:
        return l["item"]
    if l["fase"] in ("Deployment", "Adoption"):
        return l["fase"]
    return ""  # Status/Framework soltos: só os chips


def render_card(frente, linhas):
    sub = [l for l in linhas if l["frente"] == frente]
    # agrupa por iniciativa, preservando a ordem do Excel
    grupos = []
    for l in sub:
        if not grupos or grupos[-1][0] != l["iniciativa"]:
            grupos.append((l["iniciativa"], []))
        grupos[-1][1].append(l)

    blocos = []
    for nome, ls in grupos:
        # destaca o bloco quando há risco ativo (Atenção ou Crítico)
        hl = any(l[m] in ("Atenção", "Crítico") for l in ls for m in MERCADOS)
        rows = []
        for l in ls:
            r = rotulo(l)
            rl = f'<span class="rl">{esc(r)}</span>' if r else '<span class="rl"></span>'
            chips = "".join(chip(m, l[m]) for m in MERCADOS)
            rows.append(f'<div class="row">{rl}<span class="chips">{chips}</span></div>')
        blocos.append(
            f'<div class="blk{" hl" if hl else ""}">'
            f'<p class="ini">{esc(nome)}</p>{"".join(rows)}</div>'
        )
    return f'<article class="card"><h3 class="frente">{esc(frente)}</h3>{"".join(blocos)}</article>'


def render_ops():
    cols = []
    for g in OPS_BAND:
        if g["tipo"] == "fases":
            rows = []
            for label, sts in g["linhas"]:
                chips = "".join(chip(m, s) for m, s in zip(MERCADOS, sts))
                rows.append(f'<div class="row"><span class="rl">{esc(label)}</span><span class="chips">{chips}</span></div>')
            cols.append(f'<div class="ops-col"><p class="ops-h">{esc(g["titulo"])}</p>{"".join(rows)}</div>')
        else:
            heads = "".join(f'<span>{m}</span>' for m in MERCADOS)
            vals = "".join(f'<span>{v}</span>' for v in g["valores"])
            cols.append(
                f'<div class="ops-col"><p class="ops-h">{esc(g["titulo"])}</p>'
                f'<div class="cnt-h">{heads}</div><div class="cnt-v">{vals}</div></div>'
            )
    return (
        '<section class="ops">'
        '<div class="ops-title">Marketing<br>Operations</div>'
        f'<div class="ops-grid">{"".join(cols)}</div>'
        '</section>'
    )


CSS = """
  :root{
    --grad1:#F7F1FD; --grad2:#EADFF8; --grad3:#DECFF3;
    --card:#FFFFFF; --card-hl:#EFE8FB;
    --title:#3C1F73; --eyebrow:#7A5AB5; --frente:#22347A;
    --ini:#1E2530; --label:#5B6472; --line:rgba(70,45,110,.12);
    --good:#34B36B; --good-ink:#FFFFFF;
    --warn:#F3C22C; --warn-ink:#5A4600;
    --bad:#E23B3B;  --bad-ink:#FFFFFF;
    --idle:#C4C8D2; --idle-ink:#FFFFFF;
    --na:#E9E6EF;   --na-ink:#B0AAC0;
    --ops:#EFE9FB;  --ops-title:#2B4C9B;
    --serif:"Iowan Old Style",Palatino,"Palatino Linotype",Georgia,serif;
    --body:system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",sans-serif;
  }
  :root[data-theme="dark"], :root.__dk{}
  @media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
    --grad1:#191324; --grad2:#20182F; --grad3:#291E3D;
    --card:#221B2E; --card-hl:#2C2442;
    --title:#CBB6F2; --eyebrow:#A98FDA; --frente:#A6B4E9;
    --ini:#ECE8F3; --label:#A79FB6; --line:rgba(180,160,220,.14);
    --good:#33B06B; --good-ink:#06210F;
    --warn:#E9B838; --warn-ink:#3A2B00;
    --bad:#E4585C;  --bad-ink:#2A0C0D;
    --idle:#4B4660; --idle-ink:#CFC9DC;
    --na:#2F2942;   --na-ink:#7E769A;
    --ops:#2A2340;  --ops-title:#9DB4EE;
  }}
  :root[data-theme="dark"]{
    --grad1:#191324; --grad2:#20182F; --grad3:#291E3D;
    --card:#221B2E; --card-hl:#2C2442;
    --title:#CBB6F2; --eyebrow:#A98FDA; --frente:#A6B4E9;
    --ini:#ECE8F3; --label:#A79FB6; --line:rgba(180,160,220,.14);
    --good:#33B06B; --good-ink:#06210F;
    --warn:#E9B838; --warn-ink:#3A2B00;
    --bad:#E4585C;  --bad-ink:#2A0C0D;
    --idle:#4B4660; --idle-ink:#CFC9DC;
    --na:#2F2942;   --na-ink:#7E769A;
    --ops:#2A2340;  --ops-title:#9DB4EE;
  }
  *{box-sizing:border-box;}
  body{margin:0;color:var(--ini);font-family:var(--body);line-height:1.45;
    background:linear-gradient(135deg,var(--grad1) 0%,var(--grad2) 52%,var(--grad3) 100%);
    background-attachment:fixed;min-height:100vh;-webkit-font-smoothing:antialiased;}
  .wrap{max-width:1480px;margin:0 auto;padding:34px 30px 40px;}

  header.mast{display:flex;align-items:flex-start;justify-content:space-between;
    gap:24px;flex-wrap:wrap;margin-bottom:26px;}
  .eyebrow{font-size:15px;font-weight:600;color:var(--eyebrow);margin:0 0 2px;letter-spacing:.01em;}
  h1{font-family:var(--body);font-weight:800;color:var(--title);margin:0;
    font-size:clamp(28px,3.4vw,46px);line-height:1.04;letter-spacing:-.02em;}
  .brand{display:flex;align-items:center;gap:12px;padding-top:6px;color:var(--title);}
  .brand .uni{display:flex;flex-direction:column;align-items:center;line-height:1;}
  .brand .uni b{font-family:var(--serif);font-size:30px;font-weight:700;letter-spacing:-.02em;}
  .brand .uni small{font-size:9px;letter-spacing:.02em;margin-top:2px;opacity:.8;}
  .brand .rule{width:1.5px;height:44px;background:currentColor;opacity:.5;}
  .brand .bw{font-family:var(--serif);font-size:34px;font-weight:700;letter-spacing:.01em;}

  .grid{display:grid;grid-template-columns:repeat(6,1fr);gap:16px;align-items:start;}
  @media (max-width:1200px){.grid{grid-template-columns:repeat(3,1fr);}}
  @media (max-width:760px){.grid{grid-template-columns:repeat(2,1fr);}}
  @media (max-width:480px){.grid{grid-template-columns:1fr;}}

  .card{background:var(--card);border:1px solid var(--line);border-radius:16px;
    padding:16px 15px 18px;box-shadow:0 8px 22px -12px rgba(60,30,100,.28);}
  .frente{color:var(--frente);text-align:center;font-weight:700;font-size:15.5px;
    line-height:1.15;margin:2px 0 14px;min-height:2.4em;display:flex;
    align-items:center;justify-content:center;}
  .blk{margin-bottom:14px;}
  .blk:last-child{margin-bottom:2px;}
  .blk.hl{background:var(--card-hl);border-radius:11px;padding:8px 9px;
    margin-left:-7px;margin-right:-7px;}
  .ini{font-weight:700;font-size:12.5px;color:var(--ini);margin:0 0 6px;}
  .row{display:flex;align-items:center;justify-content:space-between;gap:8px;
    padding:2.5px 0;font-size:11.5px;color:var(--label);}
  .rl{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
  .chips{display:inline-flex;gap:5px;flex:none;}
  .chip{display:inline-flex;align-items:center;justify-content:center;
    min-width:30px;height:20px;padding:0 5px;border-radius:6px;font-size:10px;
    font-weight:700;letter-spacing:.02em;}
  .chip.good{background:var(--good);color:var(--good-ink);}
  .chip.warn{background:var(--warn);color:var(--warn-ink);}
  .chip.bad{background:var(--bad);color:var(--bad-ink);}
  .chip.idle{background:var(--idle);color:var(--idle-ink);}
  .chip.na{background:var(--na);color:var(--na-ink);}
  .chip.empty{background:transparent;color:transparent;}

  .ops{margin-top:20px;background:var(--ops);border:1px solid var(--line);
    border-radius:16px;padding:18px 22px;display:grid;
    grid-template-columns:170px 1fr;gap:20px;align-items:center;}
  @media (max-width:760px){.ops{grid-template-columns:1fr;}}
  .ops-title{font-family:var(--body);font-weight:800;color:var(--ops-title);
    font-size:23px;line-height:1.05;letter-spacing:-.01em;}
  .ops-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:22px;}
  @media (max-width:900px){.ops-grid{grid-template-columns:repeat(2,1fr);}}
  @media (max-width:480px){.ops-grid{grid-template-columns:1fr;}}
  .ops-h{font-weight:700;font-size:12.5px;color:var(--ini);margin:0 0 8px;}
  .ops-col .row{color:var(--label);}
  .cnt-h,.cnt-v{display:grid;grid-template-columns:repeat(3,1fr);text-align:center;}
  .cnt-h span{font-size:12px;font-weight:700;color:var(--good);}
  .cnt-v span{font-family:var(--serif);font-size:26px;font-weight:700;color:var(--ini);}

  .legend{display:flex;gap:16px;flex-wrap:wrap;align-items:center;
    margin-top:20px;font-size:11.5px;color:var(--label);}
  .legend .chip{min-width:24px;height:17px;margin-right:6px;}
  .stamp{margin-top:14px;font-size:11px;color:var(--label);opacity:.85;}
"""


def build_html(linhas, xlsx_name):
    cards = "".join(render_card(f, linhas) for f in FRENTES if any(l["frente"] == f for l in linhas))
    hoje = date.today().strftime("%d/%m/%Y")
    legenda = (
        '<span><span class="chip good">BR</span>No prazo</span>'
        '<span><span class="chip warn">BR</span>Atenção</span>'
        '<span><span class="chip bad">BR</span>Crítico</span>'
        '<span><span class="chip idle">BR</span>Não iniciado</span>'
        '<span><span class="chip na">–</span>N/A</span>'
    )
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>B&amp;W Marketing Technology 2026 Agenda</title>
<style>{CSS}</style>
</head>
<body>
<div class="wrap">
  <header class="mast">
    <div>
      <p class="eyebrow">Consumer BPC</p>
      <h1>B&amp;W Marketing Technology 2026 Agenda</h1>
    </div>
    <div class="brand" aria-label="Unilever Beauty &amp; Wellbeing">
      <span class="uni"><b>U</b><small>Unilever</small></span>
      <span class="rule"></span>
      <span class="bw">B&amp;W</span>
    </div>
  </header>

  <div class="grid">
    {cards}
  </div>

  {render_ops()}

  <div class="legend">
    {legenda}
  </div>
  <p class="stamp">Consumer BPC · Beauty &amp; Wellbeing + Personal Care · mercados BR · MX · AR · gerado de {esc(xlsx_name)} · {hoje}</p>
</div>
</body>
</html>
"""


def main():
    xlsx = Path(sys.argv[1]) if len(sys.argv) > 1 else XLSX_PADRAO
    saida = Path(sys.argv[2]) if len(sys.argv) > 2 else SAIDA_PADRAO
    linhas = ler_tracker(xlsx)
    saida.write_text(build_html(linhas, xlsx.name), encoding="utf-8")
    print(f"OK: {saida}  ({len(linhas)} linhas, {len(FRENTES)} frentes)")


if __name__ == "__main__":
    main()
