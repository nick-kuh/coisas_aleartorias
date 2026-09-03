#!/usr/bin/env python3
"""
Gera consumer-martech.html a partir do tracker Excel do time de Consumer BPC
(B&W Marketing Technology). É o mesmo esquema que a skill `consumer-martech`
descreve para o agente montar o dashboard — aqui automatizado para o Nick
regerar sempre que o Excel mudar, sem risco de o HTML desalinhar dos dados.

Uso:
    python3 scripts/gerar-consumer-html.py
    python3 scripts/gerar-consumer-html.py caminho/para/outro.xlsx saida.html

O farol por frente segue a MESMA regra do Painel do Excel:
    - qualquer célula Crítico na frente        -> 🔴
    - senão, % No prazo (BR+MX+AR, exclui N/A) >= 50% -> 🟢
    - senão                                    -> 🟡
"""
import sys
from pathlib import Path
from datetime import date

import openpyxl

RAIZ = Path(__file__).resolve().parent.parent
XLSX_PADRAO = RAIZ / "data" / "BW_MarTech_2026_Controle_Projetos.xlsx"
SAIDA_PADRAO = RAIZ / "consumer-martech.html"

# ordem canônica das frentes (pilares da área)
FRENTES = [
    "Insights",
    "Media & Influencer",
    "dCom and Social Commerce",
    "CoPilot and Agentic",
    "LLM Search / GEO",
    "Beauty Tech",
]

# status PT -> (classe CSS, rótulo EN curto)
STATUS = {
    "No prazo":     ("good", "On Track"),
    "Atenção":      ("warn", "At Risk"),
    "Crítico":      ("bad",  "Critical"),
    "Não iniciado": ("idle", "Not Started"),
    "N/A":          ("na",   "N/A"),
}
MERCADOS = ["BR", "MX", "AR"]


def ler_tracker(xlsx):
    wb = openpyxl.load_workbook(xlsx, data_only=True)
    ws = wb["Tracker"]
    linhas = []
    # linha 3 é o cabeçalho: Frente | Iniciativa | Item | Fase | BR | MX | AR | ...
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
    """Conta células de status BR+MX+AR (exclui N/A e vazias)."""
    c = {"No prazo": 0, "Atenção": 0, "Crítico": 0, "Não iniciado": 0}
    for l in linhas:
        if frente and l["frente"] != frente:
            continue
        for m in MERCADOS:
            v = l[m]
            if v in c:
                c[v] += 1
    total = sum(c.values())
    pct = (c["No prazo"] / total) if total else 0.0
    return c, total, pct


def farol(c, pct):
    if c["Crítico"] > 0:
        return "🔴", "bad"
    if pct >= 0.5:
        return "🟢", "good"
    return "🟡", "warn"


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def pill(v):
    if not v:
        return '<td class="mkt"></td>'
    cls, en = STATUS.get(v, ("idle", v))
    return f'<td class="mkt"><span class="pill {cls}" title="{esc(en)}">{esc(v)}</span></td>'


CSS = """
  :root{
    --ground:#EEF0F3; --surface:#FFFFFF; --surface2:#F6F7F9;
    --ink:#191C22; --muted:#5D6371; --faint:#868D9B;
    --line:#D6DAE1; --line-soft:#E5E8ED;
    --accent:#A85B06; --accent-bg:#F7EBD8;
    --good:#0B6E5F; --good-bg:#DDEFEA;
    --warn:#9A6A00; --warn-bg:#FBEFC9;
    --bad:#A82A2F;  --bad-bg:#F8E1E1;
    --idle:#6A7180; --idle-bg:#E7E9ED;
    --na:#9AA0AC;   --na-bg:#F1F2F4;
    --shadow:0 1px 2px rgba(25,28,34,.06),0 8px 24px -12px rgba(25,28,34,.18);
    --display:ui-serif,"Iowan Old Style","Palatino Linotype",Palatino,Georgia,serif;
    --body:system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",sans-serif;
    --data:ui-monospace,"SF Mono","Cascadia Mono",Menlo,Consolas,monospace;
  }
  @media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
    --ground:#121419; --surface:#1A1D24; --surface2:#21252D;
    --ink:#E7EAEF; --muted:#99A0AE; --faint:#6E7684;
    --line:#2E333D; --line-soft:#262B33;
    --accent:#E9A33F; --accent-bg:#3A2C14;
    --good:#46C3A8; --good-bg:#12332E;
    --warn:#E9B84B; --warn-bg:#37300F;
    --bad:#E8737B;  --bad-bg:#38191C;
    --idle:#9AA2B0; --idle-bg:#262A31;
    --na:#767D8B;   --na-bg:#20242B;
    --shadow:0 1px 2px rgba(0,0,0,.4),0 10px 30px -14px rgba(0,0,0,.7);
  }}
  :root[data-theme="dark"]{
    --ground:#121419; --surface:#1A1D24; --surface2:#21252D;
    --ink:#E7EAEF; --muted:#99A0AE; --faint:#6E7684;
    --line:#2E333D; --line-soft:#262B33;
    --accent:#E9A33F; --accent-bg:#3A2C14;
    --good:#46C3A8; --good-bg:#12332E;
    --warn:#E9B84B; --warn-bg:#37300F;
    --bad:#E8737B;  --bad-bg:#38191C;
    --idle:#9AA2B0; --idle-bg:#262A31;
    --na:#767D8B;   --na-bg:#20242B;
    --shadow:0 1px 2px rgba(0,0,0,.4),0 10px 30px -14px rgba(0,0,0,.7);
  }
  *{box-sizing:border-box;}
  body{margin:0;background:var(--ground);color:var(--ink);
    font-family:var(--body);font-size:16px;line-height:1.6;-webkit-font-smoothing:antialiased;}
  .wrap{max-width:1120px;margin:0 auto;padding:0 24px 96px;}
  header.mast{border-bottom:1px solid var(--line);padding:56px 0 0;margin-bottom:36px;}
  .eyebrow{font-family:var(--data);font-size:11px;letter-spacing:.14em;text-transform:uppercase;
    color:var(--accent);margin:0 0 16px;}
  h1{font-family:var(--display);font-weight:600;font-size:clamp(30px,5vw,50px);line-height:1.06;
    letter-spacing:-.018em;text-wrap:balance;margin:0 0 18px;}
  .lede{font-size:17px;color:var(--muted);margin:0 0 28px;max-width:66ch;}
  .lede strong{color:var(--ink);font-weight:600;}
  .board{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:1px;
    background:var(--line);border:1px solid var(--line);border-radius:3px;overflow:hidden;margin-bottom:8px;}
  .board .cell{background:var(--surface);padding:16px 18px 18px;}
  .board .k{font-family:var(--data);font-size:10px;letter-spacing:.1em;text-transform:uppercase;
    color:var(--faint);margin:0 0 9px;}
  .board .v{font-family:var(--data);font-variant-numeric:tabular-nums;font-size:24px;letter-spacing:-.02em;margin:0;}
  .v.bad{color:var(--bad);} .v.warn{color:var(--warn);} .v.good{color:var(--good);} .v.idle{color:var(--idle);}
  .board .note{font-size:12px;color:var(--muted);margin:6px 0 0;line-height:1.4;}
  .stamp{font-family:var(--data);font-size:11.5px;color:var(--faint);margin:0 0 40px;}
  section{padding-top:52px;}
  h2{font-family:var(--display);font-weight:600;font-size:clamp(22px,2.9vw,29px);letter-spacing:-.012em;
    line-height:1.2;margin:0 0 8px;padding-bottom:12px;border-bottom:2px solid var(--ink);display:inline-block;}
  .sec-note{color:var(--muted);font-size:14px;margin:14px 0 22px;max-width:70ch;}
  h3{font-family:var(--display);font-weight:600;font-size:20px;margin:0;letter-spacing:-.01em;}
  .frente-head{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap;margin:40px 0 12px;}
  .frente-head .farol{font-size:17px;}
  .frente-head .meta{font-family:var(--data);font-size:11.5px;color:var(--faint);
    letter-spacing:.04em;margin-left:auto;}
  .scroller{overflow-x:auto;border:1px solid var(--line);border-radius:3px;background:var(--surface);box-shadow:var(--shadow);}
  table{border-collapse:collapse;width:100%;font-size:13.5px;min-width:680px;}
  th,td{text-align:left;padding:10px 14px;border-bottom:1px solid var(--line-soft);vertical-align:middle;}
  thead th{font-family:var(--data);font-size:10px;letter-spacing:.09em;text-transform:uppercase;
    color:var(--faint);font-weight:500;background:var(--surface2);border-bottom:1px solid var(--line);
    position:sticky;top:0;}
  tbody tr:last-child td{border-bottom:none;}
  th.mkt,td.mkt{text-align:center;white-space:nowrap;}
  td.ini{font-weight:600;} td.item{color:var(--muted);}
  td.fase{font-family:var(--data);font-size:11px;letter-spacing:.03em;color:var(--muted);text-transform:uppercase;}
  .pill{font-family:var(--data);font-size:10px;letter-spacing:.04em;text-transform:uppercase;
    padding:3px 8px;border-radius:3px;white-space:nowrap;display:inline-block;font-weight:600;}
  .pill.good{background:var(--good-bg);color:var(--good);}
  .pill.warn{background:var(--warn-bg);color:var(--warn);}
  .pill.bad{background:var(--bad-bg);color:var(--bad);}
  .pill.idle{background:var(--idle-bg);color:var(--idle);}
  .pill.na{background:var(--na-bg);color:var(--na);}
  .health{width:100%;border-collapse:collapse;font-size:14px;}
  .health th,.health td{padding:11px 14px;border-bottom:1px solid var(--line-soft);}
  .health thead th{font-family:var(--data);font-size:10px;letter-spacing:.09em;text-transform:uppercase;
    color:var(--faint);font-weight:500;background:var(--surface2);}
  .health td.num{font-family:var(--data);font-variant-numeric:tabular-nums;text-align:right;white-space:nowrap;}
  .health tr.total td{font-weight:700;border-top:2px solid var(--line);background:var(--surface2);}
  .bar{height:6px;border-radius:3px;background:var(--idle-bg);overflow:hidden;min-width:60px;}
  .bar>span{display:block;height:100%;background:var(--good);}
  .legend{display:flex;gap:18px;flex-wrap:wrap;font-size:13px;color:var(--muted);margin-top:22px;}
  .legend .pill{margin-right:7px;}
  footer{margin-top:64px;padding-top:20px;border-top:1px solid var(--line);
    font-size:12.5px;color:var(--faint);}
"""


def build_html(linhas, xlsx_name):
    tot_c, tot_total, tot_pct = contar(linhas)

    # --- board de KPIs ---
    ativas = len({(l["frente"], l["iniciativa"]) for l in linhas})
    board = f"""
    <div class="board">
      <div class="cell"><p class="k">Iniciativas</p><p class="v">{ativas}</p><p class="note">em {len(FRENTES)} frentes</p></div>
      <div class="cell"><p class="k">Células de status</p><p class="v">{tot_total}</p><p class="note">BR·MX·AR, exclui N/A</p></div>
      <div class="cell"><p class="k">No prazo</p><p class="v good">{tot_c['No prazo']}</p><p class="note">{tot_pct*100:.0f}% do ativo</p></div>
      <div class="cell"><p class="k">Atenção</p><p class="v warn">{tot_c['Atenção']}</p><p class="note">risco moderado</p></div>
      <div class="cell"><p class="k">Crítico</p><p class="v bad">{tot_c['Crítico']}</p><p class="note">requer ação</p></div>
      <div class="cell"><p class="k">Não iniciado</p><p class="v idle">{tot_c['Não iniciado']}</p><p class="note">backlog</p></div>
    </div>"""

    # --- tabela de saúde por frente ---
    health_rows = []
    for f in FRENTES:
        c, total, pct = contar(linhas, f)
        if total == 0:
            continue
        emoji, _ = farol(c, pct)
        health_rows.append(f"""
        <tr>
          <td>{emoji}&nbsp; {esc(f)}</td>
          <td class="num">{c['No prazo']}</td>
          <td class="num">{c['Atenção']}</td>
          <td class="num">{c['Crítico']}</td>
          <td class="num">{c['Não iniciado']}</td>
          <td class="num">{total}</td>
          <td class="num">{pct*100:.0f}%</td>
          <td><div class="bar"><span style="width:{pct*100:.0f}%"></span></div></td>
        </tr>""")
    health_rows.append(f"""
        <tr class="total">
          <td>TOTAL</td>
          <td class="num">{tot_c['No prazo']}</td>
          <td class="num">{tot_c['Atenção']}</td>
          <td class="num">{tot_c['Crítico']}</td>
          <td class="num">{tot_c['Não iniciado']}</td>
          <td class="num">{tot_total}</td>
          <td class="num">{tot_pct*100:.0f}%</td>
          <td></td>
        </tr>""")
    health = f"""
    <div class="scroller">
      <table class="health">
        <thead><tr>
          <th>Frente</th><th class="num">No prazo</th><th class="num">Atenção</th>
          <th class="num">Crítico</th><th class="num">Não iniciado</th>
          <th class="num">Ativo</th><th class="num">% No prazo</th><th>&nbsp;</th>
        </tr></thead>
        <tbody>{''.join(health_rows)}</tbody>
      </table>
    </div>"""

    # --- seções por frente com o tracker ---
    secoes = []
    for f in FRENTES:
        sub = [l for l in linhas if l["frente"] == f]
        if not sub:
            continue
        c, total, pct = contar(linhas, f)
        emoji, _ = farol(c, pct)
        rows = []
        for l in sub:
            rows.append(f"""
          <tr>
            <td class="ini">{esc(l['iniciativa'])}</td>
            <td class="item">{esc(l['item'])}</td>
            <td class="fase">{esc(l['fase'])}</td>
            {pill(l['BR'])}{pill(l['MX'])}{pill(l['AR'])}
          </tr>""")
        secoes.append(f"""
      <div class="frente-head">
        <span class="farol">{emoji}</span>
        <h3>{esc(f)}</h3>
        <span class="meta">{c['No prazo']} no prazo · {c['Atenção']} atenção · {c['Crítico']} crítico · {c['Não iniciado']} não iniciado · {pct*100:.0f}%</span>
      </div>
      <div class="scroller">
        <table>
          <thead><tr>
            <th>Iniciativa</th><th>Item</th><th>Fase</th>
            <th class="mkt">BR</th><th class="mkt">MX</th><th class="mkt">AR</th>
          </tr></thead>
          <tbody>{''.join(rows)}</tbody>
        </table>
      </div>""")

    hoje = date.today().strftime("%d/%m/%Y")
    doc = f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>B&amp;W MarTech 2026 — Controle de Projetos</title>
<style>{CSS}</style>
</head>
<body>
<div class="wrap">
  <header class="mast">
    <p class="eyebrow">Consumer BPC · Farol por mercado</p>
    <h1>B&amp;W Marketing Technology 2026</h1>
    <p class="lede">Controle de projetos do time de <strong>Consumer</strong> — que roda fora do
      DevOps. Cada iniciativa é acompanhada por frente e por fase, com o farol de status de
      <strong>Brasil, México e Argentina</strong> lado a lado. Atualize o status semanalmente.</p>
    {board}
    <p class="stamp">Gerado de {esc(xlsx_name)} · atualizado em {hoje}</p>
  </header>

  <section>
    <h2>Saúde por frente</h2>
    <p class="sec-note">Contagem das células de status BR+MX+AR de cada frente (exclui N/A).
      Farol: <strong>🔴</strong> qualquer crítico · <strong>🟢</strong> ≥ 50% no prazo e sem crítico ·
      <strong>🟡</strong> demais casos.</p>
    {health}
  </section>

  <section>
    <h2>Tracker por frente</h2>
    <p class="sec-note">As iniciativas de cada frente, a fase (Adoption, Deployment, Framework, Status)
      e o farol por mercado.</p>
    {''.join(secoes)}

    <div class="legend">
      <span><span class="pill good">No prazo</span> On Track / dentro do plano</span>
      <span><span class="pill warn">Atenção</span> risco moderado</span>
      <span><span class="pill bad">Crítico</span> atrasado ou bloqueado</span>
      <span><span class="pill idle">Não iniciado</span> ainda não começou</span>
      <span><span class="pill na">N/A</span> não se aplica ao mercado</span>
    </div>
  </section>

  <footer>
    B&amp;W Marketing Technology 2026 · Consumer BPC (Beauty &amp; Wellbeing + Personal Care) ·
    mercados: BR (Brasil), MX (México), AR (Argentina).
  </footer>
</div>
</body>
</html>
"""
    return doc


def main():
    xlsx = Path(sys.argv[1]) if len(sys.argv) > 1 else XLSX_PADRAO
    saida = Path(sys.argv[2]) if len(sys.argv) > 2 else SAIDA_PADRAO
    linhas = ler_tracker(xlsx)
    html = build_html(linhas, xlsx.name)
    saida.write_text(html, encoding="utf-8")
    tot_c, tot_total, tot_pct = contar(linhas)
    print(f"OK: {saida}  ({len(linhas)} linhas, {tot_total} células, {tot_pct*100:.0f}% no prazo)")


if __name__ == "__main__":
    main()
