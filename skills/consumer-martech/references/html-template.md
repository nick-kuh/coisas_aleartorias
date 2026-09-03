# Template do dashboard HTML — Consumer MarTech

Esqueleto para o agente montar a página "B&W MarTech 2026" a partir do
`Consumer MarTech Tracker`. Entregue **um arquivo HTML só**, sem CDN, script
externo ou fonte remota — tudo inline. Claro e escuro automáticos.

O exemplo versionado no repo é `consumer-martech.html` (na raiz). Fora do
Copilot Studio ele sai pronto com `python3 scripts/gerar-consumer-html.py`.

## Como preencher

1. **Conte os status** por frente e no total (BR+MX+AR, excluindo N/A), como no
   Passo 3 da skill.
2. **Board de KPIs** (topo): Iniciativas · Células de status · No prazo (+%) ·
   Atenção · Crítico · Não iniciado. Classes de cor: `good` / `warn` / `bad` /
   `idle`.
3. **Tabela "Saúde por frente"**: uma linha por frente + total, com o emoji de
   farol pela regra (🔴 qualquer crítico · 🟢 sem crítico e ≥50% · 🟡 resto).
4. **Uma tabela por frente** (na ordem canônica) com colunas
   `Iniciativa · Item · Fase · BR · MX · AR`. Cada célula de mercado é uma pill.
5. **Legenda** ao final.

### status → classe da pill

| Status | classe |
|---|---|
| No prazo | `pill good` |
| Atenção | `pill warn` |
| Crítico | `pill bad` |
| Não iniciado | `pill idle` |
| N/A | `pill na` |

Célula vazia → `<td class="mkt"></td>` (sem pill).

## Esqueleto

```html
<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>B&amp;W MarTech 2026 — Controle de Projetos</title>
<style>
  :root{
    --ground:#EEF0F3; --surface:#FFFFFF; --surface2:#F6F7F9;
    --ink:#191C22; --muted:#5D6371; --faint:#868D9B;
    --line:#D6DAE1; --line-soft:#E5E8ED; --accent:#A85B06;
    --good:#0B6E5F; --good-bg:#DDEFEA; --warn:#9A6A00; --warn-bg:#FBEFC9;
    --bad:#A82A2F; --bad-bg:#F8E1E1; --idle:#6A7180; --idle-bg:#E7E9ED;
    --na:#9AA0AC; --na-bg:#F1F2F4;
    --display:ui-serif,Georgia,serif;
    --body:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
    --data:ui-monospace,Menlo,Consolas,monospace;
  }
  :root[data-theme="dark"], html:not([data-theme="light"]) :root{}
  @media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
    --ground:#121419; --surface:#1A1D24; --surface2:#21252D;
    --ink:#E7EAEF; --muted:#99A0AE; --faint:#6E7684; --line:#2E333D; --line-soft:#262B33;
    --accent:#E9A33F; --good:#46C3A8; --good-bg:#12332E; --warn:#E9B84B; --warn-bg:#37300F;
    --bad:#E8737B; --bad-bg:#38191C; --idle:#9AA2B0; --idle-bg:#262A31; --na:#767D8B; --na-bg:#20242B;
  }}
  :root[data-theme="dark"]{
    --ground:#121419; --surface:#1A1D24; --surface2:#21252D;
    --ink:#E7EAEF; --muted:#99A0AE; --faint:#6E7684; --line:#2E333D; --line-soft:#262B33;
    --accent:#E9A33F; --good:#46C3A8; --good-bg:#12332E; --warn:#E9B84B; --warn-bg:#37300F;
    --bad:#E8737B; --bad-bg:#38191C; --idle:#9AA2B0; --idle-bg:#262A31; --na:#767D8B; --na-bg:#20242B;
  }
  *{box-sizing:border-box;}
  body{margin:0;background:var(--ground);color:var(--ink);font-family:var(--body);line-height:1.6;}
  .wrap{max-width:1120px;margin:0 auto;padding:0 24px 96px;}
  header.mast{border-bottom:1px solid var(--line);padding:56px 0 0;margin-bottom:36px;}
  .eyebrow{font-family:var(--data);font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--accent);margin:0 0 16px;}
  h1{font-family:var(--display);font-weight:600;font-size:clamp(30px,5vw,50px);line-height:1.06;margin:0 0 18px;}
  .lede{font-size:17px;color:var(--muted);max-width:66ch;margin:0 0 28px;}
  .board{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:1px;background:var(--line);border:1px solid var(--line);border-radius:3px;overflow:hidden;}
  .board .cell{background:var(--surface);padding:16px 18px 18px;}
  .board .k{font-family:var(--data);font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:var(--faint);margin:0 0 9px;}
  .board .v{font-family:var(--data);font-variant-numeric:tabular-nums;font-size:24px;margin:0;}
  .v.bad{color:var(--bad);} .v.warn{color:var(--warn);} .v.good{color:var(--good);} .v.idle{color:var(--idle);}
  .board .note{font-size:12px;color:var(--muted);margin:6px 0 0;}
  section{padding-top:52px;}
  h2{font-family:var(--display);font-weight:600;font-size:clamp(22px,2.9vw,29px);margin:0 0 8px;padding-bottom:12px;border-bottom:2px solid var(--ink);display:inline-block;}
  .sec-note{color:var(--muted);font-size:14px;margin:14px 0 22px;max-width:70ch;}
  .frente-head{display:flex;align-items:baseline;gap:12px;flex-wrap:wrap;margin:40px 0 12px;}
  h3{font-family:var(--display);font-weight:600;font-size:20px;margin:0;}
  .frente-head .meta{font-family:var(--data);font-size:11.5px;color:var(--faint);margin-left:auto;}
  .scroller{overflow-x:auto;border:1px solid var(--line);border-radius:3px;background:var(--surface);}
  table{border-collapse:collapse;width:100%;font-size:13.5px;min-width:680px;}
  th,td{text-align:left;padding:10px 14px;border-bottom:1px solid var(--line-soft);}
  thead th{font-family:var(--data);font-size:10px;letter-spacing:.09em;text-transform:uppercase;color:var(--faint);font-weight:500;background:var(--surface2);position:sticky;top:0;}
  th.mkt,td.mkt{text-align:center;white-space:nowrap;}
  td.ini{font-weight:600;} td.item{color:var(--muted);}
  td.fase{font-family:var(--data);font-size:11px;text-transform:uppercase;color:var(--muted);}
  .health td.num,.health th.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap;}
  .health tr.total td{font-weight:700;border-top:2px solid var(--line);background:var(--surface2);}
  .pill{font-family:var(--data);font-size:10px;letter-spacing:.04em;text-transform:uppercase;padding:3px 8px;border-radius:3px;display:inline-block;font-weight:600;}
  .pill.good{background:var(--good-bg);color:var(--good);}
  .pill.warn{background:var(--warn-bg);color:var(--warn);}
  .pill.bad{background:var(--bad-bg);color:var(--bad);}
  .pill.idle{background:var(--idle-bg);color:var(--idle);}
  .pill.na{background:var(--na-bg);color:var(--na);}
  .legend{display:flex;gap:18px;flex-wrap:wrap;font-size:13px;color:var(--muted);margin-top:22px;}
</style>
</head>
<body>
<div class="wrap">
  <header class="mast">
    <p class="eyebrow">Consumer BPC · Farol por mercado</p>
    <h1>B&amp;W Marketing Technology 2026</h1>
    <p class="lede">Controle de projetos do time de Consumer, que roda fora do DevOps.
      Cada iniciativa por frente e fase, com o farol de BR, MX e AR lado a lado.</p>
    <!-- BOARD: um .cell por KPI (Iniciativas, Células, No prazo good, Atenção warn, Crítico bad, Não iniciado idle) -->
    <div class="board"> ... </div>
  </header>

  <section>
    <h2>Saúde por frente</h2>
    <div class="scroller"><table class="health">
      <thead><tr><th>Frente</th><th class="num">No prazo</th><th class="num">Atenção</th><th class="num">Crítico</th><th class="num">Não iniciado</th><th class="num">Ativo</th><th class="num">% No prazo</th></tr></thead>
      <tbody>
        <!-- uma <tr> por frente: <td>🟢 Nome</td> + números; última <tr class="total"> -->
      </tbody>
    </table></div>
  </section>

  <section>
    <h2>Tracker por frente</h2>
    <!-- Para cada frente, na ordem canônica: -->
    <div class="frente-head"><span>🟢</span><h3>Nome da frente</h3><span class="meta">resumo</span></div>
    <div class="scroller"><table>
      <thead><tr><th>Iniciativa</th><th>Item</th><th>Fase</th><th class="mkt">BR</th><th class="mkt">MX</th><th class="mkt">AR</th></tr></thead>
      <tbody>
        <!-- uma <tr> por linha do tracker; célula de mercado = <td class="mkt"><span class="pill good">No prazo</span></td> -->
      </tbody>
    </table></div>

    <div class="legend">
      <span><span class="pill good">No prazo</span> On Track</span>
      <span><span class="pill warn">Atenção</span> risco moderado</span>
      <span><span class="pill bad">Crítico</span> ação</span>
      <span><span class="pill idle">Não iniciado</span> backlog</span>
      <span><span class="pill na">N/A</span> não se aplica</span>
    </div>
  </section>
</div>
</body>
</html>
```
