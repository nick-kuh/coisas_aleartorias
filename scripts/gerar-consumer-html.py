#!/usr/bin/env python3
"""
Gera consumer-martech.html — a "B&W Marketing Technology 2026 Agenda" do time de
Consumer BPC — a partir do tracker Excel. Hero roxo com o logo oficial Unilever ·
Beauty & Wellbeing (assets/logo-bw.svg), corpo branco, um card por frente e os
status BR/MX/AR como chips coloridos. Mesmo esquema da skill `consumer-martech`.

Uso:
    python3 scripts/gerar-consumer-html.py
    python3 scripts/gerar-consumer-html.py caminho/para/outro.xlsx saida.html

Os cards das frentes saem 100% do Excel. A faixa "Marketing Operations" no rodapé
é um elemento fixo do layout (OPS_BAND). O logo é o arquivo real em assets/.
"""
import sys
from pathlib import Path
from datetime import date

import openpyxl

RAIZ = Path(__file__).resolve().parent.parent
XLSX_PADRAO = RAIZ / "data" / "BW_MarTech_2026_Controle_Projetos.xlsx"
SAIDA_PADRAO = RAIZ / "consumer-martech.html"
LOGO_SVG = RAIZ / "assets" / "logo-bw.svg"
FONT_CSS = RAIZ / "assets" / "poppins-inline.css"

FRENTES = [
    "Insights",
    "Media & Influencer",
    "dCom and Social Commerce",
    "CoPilot and Agentic",
    "LLM Search / GEO",
    "Beauty Tech",
]

STATUS = {
    "No prazo":     ("good", "On Track"),
    "Atenção":      ("warn", "At Risk"),
    "Crítico":      ("bad",  "Critical"),
    "Não iniciado": ("idle", "Not Started"),
    "N/A":          ("na",   "N/A"),
}
MERCADOS = ["BR", "MX", "AR"]

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


def contar(linhas, frente=None):
    c = {"No prazo": 0, "Atenção": 0, "Crítico": 0, "Não iniciado": 0}
    for l in linhas:
        if frente and l["frente"] != frente:
            continue
        for m in MERCADOS:
            if l[m] in c:
                c[l[m]] += 1
    total = sum(c.values())
    return c, total, (c["No prazo"] / total if total else 0.0)


def esc(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def chip(code, status):
    if not status:
        return f'<span class="chip empty">{code}</span>'
    cls, en = STATUS.get(status, ("idle", status))
    label = "–" if status == "N/A" else code
    return f'<span class="chip {cls}" title="{esc(code)} · {esc(status)} ({esc(en)})">{label}</span>'


def rotulo(l):
    if l["item"]:
        return l["item"]
    if l["fase"] in ("Deployment", "Adoption"):
        return l["fase"]
    return ""


def render_card(frente, linhas):
    sub = [l for l in linhas if l["frente"] == frente]
    grupos = []
    for l in sub:
        if not grupos or grupos[-1][0] != l["iniciativa"]:
            grupos.append((l["iniciativa"], []))
        grupos[-1][1].append(l)

    blocos = []
    for nome, ls in grupos:
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

    c, total, pct = contar(linhas, frente)
    emoji = "bad" if c["Crítico"] else ("good" if pct >= 0.5 else "warn")
    return (
        '<article class="card">'
        f'<header class="card-h"><span class="dot {emoji}"></span>'
        f'<h3 class="frente">{esc(frente)}</h3></header>'
        f'<div class="card-b">{"".join(blocos)}</div></article>'
    )


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
  /* tom claro fixo — roxo + branco (sem dark mode, a pedido) */
  :root{
    color-scheme:light;
    --page1:#FFFFFF; --page2:#F3ECFC;
    --purple:#6D28D9; --purple-2:#8B5CF6; --purple-3:#A78BFA; --purple-deep:#5B21B6;
    --card:#FFFFFF; --card-hl:#F5EFFD; --card-line:#EDE4F9;
    --ink:#241C36; --frente:#6D28D9; --label:#6B6480; --faint:#9E97B0;
    --good:#22B26B; --good-ink:#FFFFFF; --warn:#F4B72E; --warn-ink:#5A4200;
    --bad:#E5484D; --bad-ink:#FFFFFF; --idle:#CBD0DB; --idle-ink:#FFFFFF;
    --na:#EFEAF7; --na-ink:#B4ADC2; --ops:#F4EDFD; --ops-line:#E8DCF8;
    --shadow:0 14px 36px -20px rgba(90,40,160,.30);
    --body:'Poppins',system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",sans-serif;
  }
  *{box-sizing:border-box;}
  body{margin:0;color:var(--ink);font-family:var(--body);line-height:1.45;min-height:100vh;
    background:linear-gradient(180deg,var(--page1) 0%,var(--page2) 100%);background-attachment:fixed;
    -webkit-font-smoothing:antialiased;}
  .wrap{max-width:1500px;margin:0 auto;padding:26px 28px 44px;}

  /* ---------- hero ---------- */
  .hero{position:relative;overflow:hidden;border-radius:28px;padding:36px 44px 34px;
    color:#fff;box-shadow:0 22px 54px -26px rgba(109,40,217,.55);
    background:
      radial-gradient(130% 150% at 90% -35%, rgba(255,255,255,.40), transparent 48%),
      radial-gradient(90% 120% at 6% 130%, rgba(255,255,255,.16), transparent 52%),
      linear-gradient(115deg, var(--purple-deep) 0%, var(--purple) 40%, var(--purple-2) 74%, var(--purple-3) 100%);}
  .hero-top{display:flex;align-items:center;justify-content:space-between;gap:32px;flex-wrap:wrap;}
  .eyebrow{font-size:12px;font-weight:600;letter-spacing:.24em;text-transform:uppercase;
    color:rgba(255,255,255,.85);margin:0 0 10px;}
  h1{font-weight:800;margin:0;color:#fff;
    font-size:clamp(30px,3.6vw,50px);line-height:1.0;letter-spacing:-.03em;}
  .logo-wrap{color:#fff;flex:none;}
  .logo-bw{width:clamp(250px,26vw,360px);height:auto;display:block;
    filter:drop-shadow(0 4px 14px rgba(0,0,0,.18));}
  .stats{display:flex;flex-wrap:wrap;gap:12px;margin-top:26px;}
  .stat{display:flex;align-items:baseline;gap:8px;padding:10px 18px;border-radius:999px;
    background:rgba(255,255,255,.16);border:1px solid rgba(255,255,255,.30);backdrop-filter:blur(3px);}
  .stat b{font-size:20px;font-weight:700;letter-spacing:-.02em;}
  .stat span{font-size:12px;color:rgba(255,255,255,.86);font-weight:500;}

  /* ---------- section head ---------- */
  .sec-head{display:flex;align-items:center;justify-content:space-between;gap:18px;
    flex-wrap:wrap;margin:30px 2px 16px;}
  .sec-head h2{font-size:15px;font-weight:800;color:var(--frente);margin:0;letter-spacing:.01em;
    text-transform:uppercase;}
  .legend{display:flex;gap:14px;flex-wrap:wrap;align-items:center;font-size:11.5px;color:var(--label);}
  .legend .chip{min-width:23px;height:17px;margin-right:6px;}

  /* ---------- grid & cards ---------- */
  .grid{display:grid;grid-template-columns:repeat(6,1fr);gap:16px;align-items:start;}
  @media (max-width:1200px){.grid{grid-template-columns:repeat(3,1fr);}}
  @media (max-width:760px){.grid{grid-template-columns:repeat(2,1fr);}}
  @media (max-width:480px){.grid{grid-template-columns:1fr;}}
  .card{background:var(--card);border:1px solid var(--card-line);border-radius:18px;
    box-shadow:var(--shadow);overflow:hidden;}
  .card-h{position:relative;display:flex;align-items:center;justify-content:center;gap:8px;
    padding:15px 14px 13px;border-bottom:1px solid var(--card-line);
    background:linear-gradient(180deg, rgba(124,58,237,.06), transparent);}
  .card-h .dot{width:8px;height:8px;border-radius:50%;flex:none;}
  .dot.good{background:var(--good);} .dot.warn{background:var(--warn);} .dot.bad{background:var(--bad);}
  .frente{color:var(--frente);text-align:center;font-weight:800;font-size:14.5px;line-height:1.15;margin:0;
    letter-spacing:-.01em;}
  .card-b{padding:15px 15px 17px;}
  .blk{margin-bottom:14px;} .blk:last-child{margin-bottom:0;}
  .blk.hl{background:var(--card-hl);border:1px solid var(--card-line);border-radius:12px;
    padding:9px 10px;margin:0 -4px 14px;}
  .ini{font-weight:700;font-size:12.5px;color:var(--ink);margin:0 0 7px;}
  .row{display:flex;align-items:center;justify-content:space-between;gap:8px;padding:2.5px 0;
    font-size:11.5px;color:var(--label);}
  .rl{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
  .chips{display:inline-flex;gap:5px;flex:none;}
  .chip{display:inline-flex;align-items:center;justify-content:center;min-width:30px;height:20px;
    padding:0 5px;border-radius:6px;font-size:10px;font-weight:700;letter-spacing:.02em;}
  .chip.good{background:var(--good);color:var(--good-ink);}
  .chip.warn{background:var(--warn);color:var(--warn-ink);}
  .chip.bad{background:var(--bad);color:var(--bad-ink);}
  .chip.idle{background:var(--idle);color:var(--idle-ink);}
  .chip.na{background:var(--na);color:var(--na-ink);}
  .chip.empty{background:transparent;color:transparent;}

  /* ---------- ops band ---------- */
  .ops{margin-top:22px;background:var(--ops);border:1px solid var(--ops-line);border-radius:20px;
    padding:22px 26px;display:grid;grid-template-columns:180px 1fr;gap:22px;align-items:center;}
  @media (max-width:760px){.ops{grid-template-columns:1fr;}}
  .ops-title{font-family:var(--body);font-weight:800;color:var(--purple);font-size:23px;
    line-height:1.05;letter-spacing:-.01em;}
  .ops-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:24px;}
  @media (max-width:900px){.ops-grid{grid-template-columns:repeat(2,1fr);}}
  @media (max-width:480px){.ops-grid{grid-template-columns:1fr;}}
  .ops-h{font-weight:700;font-size:12.5px;color:var(--ink);margin:0 0 8px;}
  .ops-col .row{color:var(--label);}
  .cnt-h,.cnt-v{display:grid;grid-template-columns:repeat(3,1fr);text-align:center;}
  .cnt-h span{font-size:12px;font-weight:800;color:var(--good);letter-spacing:.02em;}
  .cnt-v span{font-family:var(--body);font-size:26px;font-weight:800;color:var(--ink);}

  .stamp{margin-top:18px;font-size:11px;color:var(--faint);text-align:center;}
"""


def build_html(linhas, xlsx_name):
    logo = LOGO_SVG.read_text(encoding="utf-8") if LOGO_SVG.exists() else ""
    font_css = FONT_CSS.read_text(encoding="utf-8") if FONT_CSS.exists() else ""
    cards = "".join(render_card(f, linhas) for f in FRENTES if any(l["frente"] == f for l in linhas))
    c, total, pct = contar(linhas)
    n_ini = len({(l["frente"], l["iniciativa"]) for l in linhas})
    stats = (
        f'<div class="stat"><b>{n_ini}</b><span>iniciativas</span></div>'
        f'<div class="stat"><b>{len(FRENTES)}</b><span>frentes</span></div>'
        f'<div class="stat"><b>{pct*100:.0f}%</b><span>no prazo</span></div>'
        f'<div class="stat"><b>{c["Atenção"]}</b><span>em atenção</span></div>'
        f'<div class="stat"><b>{c["Crítico"]}</b><span>críticos</span></div>'
    )
    legenda = (
        '<span><span class="chip good">BR</span>No prazo</span>'
        '<span><span class="chip warn">BR</span>Atenção</span>'
        '<span><span class="chip bad">BR</span>Crítico</span>'
        '<span><span class="chip idle">BR</span>Não iniciado</span>'
        '<span><span class="chip na">–</span>N/A</span>'
    )
    hoje = date.today().strftime("%d/%m/%Y")
    return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light">
<title>B&amp;W Marketing Technology 2026 Agenda</title>
<style>{font_css}
{CSS}</style>
</head>
<body>
<div class="wrap">
  <header class="hero">
    <div class="hero-top">
      <div>
        <p class="eyebrow">Consumer BPC</p>
        <h1>B&amp;W Marketing Technology<br>2026 Agenda</h1>
      </div>
      <div class="logo-wrap">{logo}</div>
    </div>
    <div class="stats">{stats}</div>
  </header>

  <div class="sec-head">
    <h2>Portfólio por frente</h2>
    <div class="legend">{legenda}</div>
  </div>

  <div class="grid">
    {cards}
  </div>

  {render_ops()}

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
