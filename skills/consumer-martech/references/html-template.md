# Template do dashboard HTML — Consumer MarTech (hero roxo + cards)

Esqueleto para o agente montar a **"B&W Marketing Technology 2026 Agenda"** a
partir do `Consumer MarTech Tracker`. Visual "marketing": **hero roxo** no topo
com o logo oficial Unilever · Beauty & Wellbeing (branco), **corpo branco**, um
**card por frente** e os status BR/MX/AR como **chips coloridos**. Entregue **um
arquivo HTML só**, sem CDN, script externo ou fonte remota — tudo inline. Claro e
escuro automáticos.

O exemplo versionado é `consumer-martech.html` (raiz). Fora do Copilot Studio ele
sai pronto com `python3 scripts/gerar-consumer-html.py`.

## O logo (obrigatório, use o real)

O logo é o arquivo **`references/logo-bw.svg`** (mesmo vetor que `assets/logo-bw.svg`
na raiz) — o vetor oficial, com os fills em `currentColor` (por isso fica branco no
hero e roxo em fundo claro). **Inline esse SVG** dentro de `<div class="logo-wrap">`;
nunca redesenhe nem substitua por texto. No hero ele herda `color:#fff`.

## Regras de montagem

1. **Hero (faixa roxa):** eyebrow "CONSUMER BPC" + `<h1>` "B&W Marketing Technology
   2026 Agenda" em branco à esquerda; o **logo** à direita. Abaixo, a régua de
   **stats** (pills translúcidas): nº de iniciativas, nº de frentes, % no prazo,
   em atenção, críticos — números que você contou no Passo 3.
2. **Cabeçalho de seção:** "PORTFÓLIO POR FRENTE" à esquerda + **legenda** dos
   chips à direita.
3. **Grid de 6 cards**, na ordem canônica das frentes. Cada card tem um cabeçalho
   (um **farol dot** + o nome da frente) e o corpo com um **bloco por iniciativa**.
   - Farol dot: `dot bad` se a frente tem crítico · `dot good` se ≥50% no prazo e
     sem crítico · `dot warn` nos demais.
   - Bloco = nome da iniciativa + uma linha por registro. Rótulo da linha = o
     **Item** se houver; senão a **Fase** (Deployment/Adoption). Status/Framework
     soltos ficam só com os chips.
   - **Destaque** (`class="blk hl"`) quando o bloco tem Atenção ou Crítico.
4. **Chips BR/MX/AR** por status:

   | Status | classe | conteúdo |
   |---|---|---|
   | No prazo | `chip good` | BR / MX / AR |
   | Atenção | `chip warn` | BR / MX / AR |
   | Crítico | `chip bad` | BR / MX / AR |
   | Não iniciado | `chip idle` | BR / MX / AR |
   | N/A | `chip na` | `–` |

5. **Faixa "Marketing Operations"** (elemento fixo do board, não vem do Excel):
   Social Media Access Mgmt + três contadores (Operational Support, Cyber/AI
   Assessments, Automation Requests).
6. **Carimbo** de origem/data no rodapé.

> **Não invente dados.** Os cards saem só do `Consumer MarTech Tracker`. A faixa
> Marketing Operations é estrutural (mantém rótulos e zeros do board).

## CSS (colar inteiro)

```css
:root{
  --page1:#FFFFFF; --page2:#F5EFFC;
  --purple:#5B2A9D; --purple-2:#7C3AED; --purple-3:#A855F7; --purple-deep:#3B1470;
  --card:#FFFFFF; --card-hl:#F4EEFC; --card-line:#ECE4F7;
  --ink:#1E1730; --frente:#5B2A9D; --label:#6A6280; --faint:#9A93AC;
  --good:#22B26B; --good-ink:#FFF; --warn:#F4B72E; --warn-ink:#5A4200;
  --bad:#E5484D; --bad-ink:#FFF; --idle:#CBD0DB; --idle-ink:#FFF; --na:#EDE9F4; --na-ink:#B4ADC2;
  --ops:#F4EEFC; --ops-line:#E7DDF6; --shadow:0 12px 34px -18px rgba(70,25,140,.35);
  --body:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --page1:#140E22; --page2:#0E0919; --purple:#7C3AED; --purple-2:#8B44F0; --purple-3:#A855F7; --purple-deep:#241040;
  --card:#1D1630; --card-hl:#271B42; --card-line:#2E2447; --ink:#ECE6F6; --frente:#C6ADF4; --label:#A79FBB; --faint:#7C7594;
  --good:#2FB971; --good-ink:#04210F; --warn:#EBBB40; --warn-ink:#3A2A00; --bad:#EA5A5E; --bad-ink:#280708;
  --idle:#4A4560; --idle-ink:#D3CDE2; --na:#2C2542; --na-ink:#847BA0; --ops:#1B1430; --ops-line:#2C2247; --shadow:0 14px 40px -20px rgba(0,0,0,.7);
}}
:root[data-theme="dark"]{
  --page1:#140E22; --page2:#0E0919; --purple:#7C3AED; --purple-2:#8B44F0; --purple-3:#A855F7; --purple-deep:#241040;
  --card:#1D1630; --card-hl:#271B42; --card-line:#2E2447; --ink:#ECE6F6; --frente:#C6ADF4; --label:#A79FBB; --faint:#7C7594;
  --good:#2FB971; --good-ink:#04210F; --warn:#EBBB40; --warn-ink:#3A2A00; --bad:#EA5A5E; --bad-ink:#280708;
  --idle:#4A4560; --idle-ink:#D3CDE2; --na:#2C2542; --na-ink:#847BA0; --ops:#1B1430; --ops-line:#2C2247; --shadow:0 14px 40px -20px rgba(0,0,0,.7);
}
*{box-sizing:border-box;}
body{margin:0;color:var(--ink);font-family:var(--body);line-height:1.45;min-height:100vh;
  background:linear-gradient(180deg,var(--page1),var(--page2));background-attachment:fixed;}
.wrap{max-width:1500px;margin:0 auto;padding:26px 28px 44px;}
.hero{position:relative;overflow:hidden;border-radius:26px;padding:34px 40px 32px;color:#fff;
  box-shadow:0 20px 50px -24px rgba(70,25,140,.6);
  background:radial-gradient(120% 140% at 88% -30%,rgba(255,255,255,.28),transparent 46%),
    linear-gradient(115deg,var(--purple-deep),var(--purple) 46%,var(--purple-2) 78%,var(--purple-3));}
.hero-top{display:flex;align-items:flex-start;justify-content:space-between;gap:28px;flex-wrap:wrap;}
.eyebrow{font-size:12px;font-weight:700;letter-spacing:.22em;text-transform:uppercase;color:rgba(255,255,255,.82);margin:0 0 10px;}
h1{font-weight:800;margin:0;color:#fff;font-size:clamp(28px,3.5vw,48px);line-height:1.02;letter-spacing:-.022em;}
.logo-wrap{color:#fff;flex:none;} .logo-bw{width:clamp(180px,17vw,236px);height:auto;display:block;}
.stats{display:flex;flex-wrap:wrap;gap:12px;margin-top:24px;}
.stat{display:flex;align-items:baseline;gap:8px;padding:9px 16px;border-radius:999px;background:rgba(255,255,255,.13);border:1px solid rgba(255,255,255,.24);}
.stat b{font-size:19px;font-weight:800;} .stat span{font-size:12px;color:rgba(255,255,255,.82);font-weight:600;}
.sec-head{display:flex;align-items:center;justify-content:space-between;gap:18px;flex-wrap:wrap;margin:30px 2px 16px;}
.sec-head h2{font-size:15px;font-weight:800;color:var(--frente);margin:0;text-transform:uppercase;}
.legend{display:flex;gap:14px;flex-wrap:wrap;align-items:center;font-size:11.5px;color:var(--label);}
.legend .chip{min-width:23px;height:17px;margin-right:6px;}
.grid{display:grid;grid-template-columns:repeat(6,1fr);gap:16px;align-items:start;}
@media (max-width:1200px){.grid{grid-template-columns:repeat(3,1fr);}}
@media (max-width:760px){.grid{grid-template-columns:repeat(2,1fr);}}
@media (max-width:480px){.grid{grid-template-columns:1fr;}}
.card{background:var(--card);border:1px solid var(--card-line);border-radius:18px;box-shadow:var(--shadow);overflow:hidden;}
.card-h{display:flex;align-items:center;justify-content:center;gap:8px;padding:15px 14px 13px;
  border-bottom:1px solid var(--card-line);background:linear-gradient(180deg,rgba(124,58,237,.06),transparent);}
.card-h .dot{width:8px;height:8px;border-radius:50%;flex:none;}
.dot.good{background:var(--good);} .dot.warn{background:var(--warn);} .dot.bad{background:var(--bad);}
.frente{color:var(--frente);text-align:center;font-weight:800;font-size:14.5px;line-height:1.15;margin:0;}
.card-b{padding:15px 15px 17px;}
.blk{margin-bottom:14px;} .blk:last-child{margin-bottom:0;}
.blk.hl{background:var(--card-hl);border:1px solid var(--card-line);border-radius:12px;padding:9px 10px;margin:0 -4px 14px;}
.ini{font-weight:700;font-size:12.5px;color:var(--ink);margin:0 0 7px;}
.row{display:flex;align-items:center;justify-content:space-between;gap:8px;padding:2.5px 0;font-size:11.5px;color:var(--label);}
.rl{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
.chips{display:inline-flex;gap:5px;flex:none;}
.chip{display:inline-flex;align-items:center;justify-content:center;min-width:30px;height:20px;padding:0 5px;border-radius:6px;font-size:10px;font-weight:700;}
.chip.good{background:var(--good);color:var(--good-ink);} .chip.warn{background:var(--warn);color:var(--warn-ink);}
.chip.bad{background:var(--bad);color:var(--bad-ink);} .chip.idle{background:var(--idle);color:var(--idle-ink);} .chip.na{background:var(--na);color:var(--na-ink);}
.ops{margin-top:22px;background:var(--ops);border:1px solid var(--ops-line);border-radius:20px;padding:22px 26px;display:grid;grid-template-columns:180px 1fr;gap:22px;align-items:center;}
@media (max-width:760px){.ops{grid-template-columns:1fr;}}
.ops-title{font-weight:800;color:var(--purple);font-size:23px;line-height:1.05;}
.ops-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:24px;}
@media (max-width:900px){.ops-grid{grid-template-columns:repeat(2,1fr);}}
.ops-h{font-weight:700;font-size:12.5px;color:var(--ink);margin:0 0 8px;}
.cnt-h,.cnt-v{display:grid;grid-template-columns:repeat(3,1fr);text-align:center;}
.cnt-h span{font-size:12px;font-weight:800;color:var(--good);} .cnt-v span{font-size:26px;font-weight:800;color:var(--ink);}
.stamp{margin-top:18px;font-size:11px;color:var(--faint);text-align:center;}
```

## Esqueleto do corpo

```html
<div class="wrap">
  <header class="hero">
    <div class="hero-top">
      <div>
        <p class="eyebrow">Consumer BPC</p>
        <h1>B&amp;W Marketing Technology<br>2026 Agenda</h1>
      </div>
      <div class="logo-wrap"><!-- inline de assets/logo-bw.svg (branco) --></div>
    </div>
    <div class="stats">
      <div class="stat"><b>19</b><span>iniciativas</span></div>
      <div class="stat"><b>6</b><span>frentes</span></div>
      <div class="stat"><b>47%</b><span>no prazo</span></div>
      <div class="stat"><b>12</b><span>em atenção</span></div>
      <div class="stat"><b>2</b><span>críticos</span></div>
    </div>
  </header>

  <div class="sec-head">
    <h2>Portfólio por frente</h2>
    <div class="legend">
      <span><span class="chip good">BR</span>No prazo</span>
      <span><span class="chip warn">BR</span>Atenção</span>
      <span><span class="chip bad">BR</span>Crítico</span>
      <span><span class="chip idle">BR</span>Não iniciado</span>
      <span><span class="chip na">–</span>N/A</span>
    </div>
  </div>

  <div class="grid">
    <article class="card">
      <header class="card-h"><span class="dot bad"></span><h3 class="frente">Insights</h3></header>
      <div class="card-b">
        <div class="blk hl">
          <p class="ini">Winnin</p>
          <div class="row"><span class="rl">Deployment</span><span class="chips">
            <span class="chip good">BR</span><span class="chip good">MX</span><span class="chip good">AR</span></span></div>
          <div class="row"><span class="rl">Adoption</span><span class="chips">
            <span class="chip good">BR</span><span class="chip good">MX</span><span class="chip warn">AR</span></span></div>
        </div>
        <!-- ... demais iniciativas ... -->
      </div>
    </article>
    <!-- ... demais frentes ... -->
  </div>

  <section class="ops">
    <div class="ops-title">Marketing<br>Operations</div>
    <div class="ops-grid">
      <div class="ops-col"><p class="ops-h">Social Media Access Mgmt</p>
        <div class="row"><span class="rl">Deployment</span><span class="chips">
          <span class="chip idle">BR</span><span class="chip idle">MX</span><span class="chip idle">AR</span></span></div>
        <div class="row"><span class="rl">Adoption</span><span class="chips">
          <span class="chip idle">BR</span><span class="chip idle">MX</span><span class="chip idle">AR</span></span></div>
      </div>
      <div class="ops-col"><p class="ops-h">Operational Support</p>
        <div class="cnt-h"><span>BR</span><span>MX</span><span>AR</span></div>
        <div class="cnt-v"><span>0</span><span>0</span><span>0</span></div>
      </div>
      <!-- Cyber/AI Assessments e Automation Requests iguais -->
    </div>
  </section>
</div>
```
