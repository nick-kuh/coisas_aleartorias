# Template do dashboard HTML — Consumer MarTech (agenda em cards)

Esqueleto para o agente montar a página **"B&W Marketing Technology 2026 Agenda"**
a partir do `Consumer MarTech Tracker`. É um board estilo agenda: um **card por
frente**, fundo lavanda, e os status BR/MX/AR viram **chips coloridos**. Entregue
**um arquivo HTML só**, sem CDN, script externo ou fonte remota — tudo inline.
Claro e escuro automáticos.

O exemplo versionado é `consumer-martech.html` (raiz). Fora do Copilot Studio ele
sai pronto com `python3 scripts/gerar-consumer-html.py`.

## Regras de montagem

1. **Header:** eyebrow "Consumer BPC" + `<h1>` "B&W Marketing Technology 2026
   Agenda" à esquerda; lockup **Unilever · B&W** à direita.
2. **Grid de 6 cards**, na ordem canônica das frentes (Insights · Media &
   Influencer · dCom and Social Commerce · CoPilot and Agentic · LLM Search / GEO
   · Beauty Tech). Cada card = título da frente centralizado + blocos de iniciativa.
3. **Bloco de iniciativa:** nome em negrito + uma linha por registro do tracker.
   - Rótulo da linha = o **Item** se houver (Dove, Clear, CMI…); senão a **Fase**
     (Deployment / Adoption). Linhas Status/Framework soltas ficam só com os chips.
   - **Destaque lavanda** (`class="blk hl"`) no bloco quando qualquer célula dele
     for **Atenção** ou **Crítico**.
4. **Chips BR/MX/AR** (um por mercado), cor pelo status:

   | Status | classe | conteúdo do chip |
   |---|---|---|
   | No prazo | `chip good` | BR / MX / AR |
   | Atenção | `chip warn` | BR / MX / AR |
   | Crítico | `chip bad` | BR / MX / AR |
   | Não iniciado | `chip idle` | BR / MX / AR |
   | N/A | `chip na` | `–` |

5. **Faixa "Marketing Operations"** no rodapé (elemento fixo do board, não vem do
   Excel): Social Media Access Mgmt (linhas Deployment/Adoption) + três contadores
   (Operational Support, Cyber/AI Assessments, Automation Requests) com BR/MX/AR.
6. **Legenda** curta + carimbo de origem/data no fim.

> **Não invente dados.** Os cards saem só do `Consumer MarTech Tracker`. A faixa
> Marketing Operations é estrutural (mantém os rótulos e zeros do board) — se o
> tracker não trouxer esses números, deixe-a como está.

## CSS (colar inteiro)

```css
:root{
  --grad1:#F7F1FD; --grad2:#EADFF8; --grad3:#DECFF3;
  --card:#FFFFFF; --card-hl:#EFE8FB;
  --title:#3C1F73; --eyebrow:#7A5AB5; --frente:#22347A;
  --ini:#1E2530; --label:#5B6472; --line:rgba(70,45,110,.12);
  --good:#34B36B; --good-ink:#FFFFFF; --warn:#F3C22C; --warn-ink:#5A4600;
  --bad:#E23B3B; --bad-ink:#FFFFFF; --idle:#C4C8D2; --idle-ink:#FFFFFF;
  --na:#E9E6EF; --na-ink:#B0AAC0; --ops:#EFE9FB; --ops-title:#2B4C9B;
  --serif:"Iowan Old Style",Palatino,Georgia,serif;
  --body:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){
  --grad1:#191324; --grad2:#20182F; --grad3:#291E3D; --card:#221B2E; --card-hl:#2C2442;
  --title:#CBB6F2; --eyebrow:#A98FDA; --frente:#A6B4E9; --ini:#ECE8F3; --label:#A79FB6;
  --line:rgba(180,160,220,.14); --good:#33B06B; --good-ink:#06210F; --warn:#E9B838; --warn-ink:#3A2B00;
  --bad:#E4585C; --bad-ink:#2A0C0D; --idle:#4B4660; --idle-ink:#CFC9DC; --na:#2F2942; --na-ink:#7E769A;
  --ops:#2A2340; --ops-title:#9DB4EE;
}}
:root[data-theme="dark"]{
  --grad1:#191324; --grad2:#20182F; --grad3:#291E3D; --card:#221B2E; --card-hl:#2C2442;
  --title:#CBB6F2; --eyebrow:#A98FDA; --frente:#A6B4E9; --ini:#ECE8F3; --label:#A79FB6;
  --line:rgba(180,160,220,.14); --good:#33B06B; --good-ink:#06210F; --warn:#E9B838; --warn-ink:#3A2B00;
  --bad:#E4585C; --bad-ink:#2A0C0D; --idle:#4B4660; --idle-ink:#CFC9DC; --na:#2F2942; --na-ink:#7E769A;
  --ops:#2A2340; --ops-title:#9DB4EE;
}
*{box-sizing:border-box;}
body{margin:0;color:var(--ini);font-family:var(--body);line-height:1.45;min-height:100vh;
  background:linear-gradient(135deg,var(--grad1) 0%,var(--grad2) 52%,var(--grad3) 100%);background-attachment:fixed;}
.wrap{max-width:1480px;margin:0 auto;padding:34px 30px 40px;}
header.mast{display:flex;align-items:flex-start;justify-content:space-between;gap:24px;flex-wrap:wrap;margin-bottom:26px;}
.eyebrow{font-size:15px;font-weight:600;color:var(--eyebrow);margin:0 0 2px;}
h1{font-family:var(--body);font-weight:800;color:var(--title);margin:0;font-size:clamp(28px,3.4vw,46px);line-height:1.04;letter-spacing:-.02em;}
.brand{display:flex;align-items:center;gap:12px;padding-top:6px;color:var(--title);}
.brand .uni{display:flex;flex-direction:column;align-items:center;line-height:1;}
.brand .uni b{font-family:var(--serif);font-size:30px;font-weight:700;}
.brand .uni small{font-size:9px;margin-top:2px;opacity:.8;}
.brand .rule{width:1.5px;height:44px;background:currentColor;opacity:.5;}
.brand .bw{font-family:var(--serif);font-size:34px;font-weight:700;}
.grid{display:grid;grid-template-columns:repeat(6,1fr);gap:16px;align-items:start;}
@media (max-width:1200px){.grid{grid-template-columns:repeat(3,1fr);}}
@media (max-width:760px){.grid{grid-template-columns:repeat(2,1fr);}}
@media (max-width:480px){.grid{grid-template-columns:1fr;}}
.card{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:16px 15px 18px;box-shadow:0 8px 22px -12px rgba(60,30,100,.28);}
.frente{color:var(--frente);text-align:center;font-weight:700;font-size:15.5px;line-height:1.15;margin:2px 0 14px;min-height:2.4em;display:flex;align-items:center;justify-content:center;}
.blk{margin-bottom:14px;} .blk:last-child{margin-bottom:2px;}
.blk.hl{background:var(--card-hl);border-radius:11px;padding:8px 9px;margin-left:-7px;margin-right:-7px;}
.ini{font-weight:700;font-size:12.5px;color:var(--ini);margin:0 0 6px;}
.row{display:flex;align-items:center;justify-content:space-between;gap:8px;padding:2.5px 0;font-size:11.5px;color:var(--label);}
.rl{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
.chips{display:inline-flex;gap:5px;flex:none;}
.chip{display:inline-flex;align-items:center;justify-content:center;min-width:30px;height:20px;padding:0 5px;border-radius:6px;font-size:10px;font-weight:700;}
.chip.good{background:var(--good);color:var(--good-ink);}
.chip.warn{background:var(--warn);color:var(--warn-ink);}
.chip.bad{background:var(--bad);color:var(--bad-ink);}
.chip.idle{background:var(--idle);color:var(--idle-ink);}
.chip.na{background:var(--na);color:var(--na-ink);}
.ops{margin-top:20px;background:var(--ops);border:1px solid var(--line);border-radius:16px;padding:18px 22px;display:grid;grid-template-columns:170px 1fr;gap:20px;align-items:center;}
@media (max-width:760px){.ops{grid-template-columns:1fr;}}
.ops-title{font-family:var(--body);font-weight:800;color:var(--ops-title);font-size:23px;line-height:1.05;}
.ops-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:22px;}
@media (max-width:900px){.ops-grid{grid-template-columns:repeat(2,1fr);}}
.ops-h{font-weight:700;font-size:12.5px;color:var(--ini);margin:0 0 8px;}
.cnt-h,.cnt-v{display:grid;grid-template-columns:repeat(3,1fr);text-align:center;}
.cnt-h span{font-size:12px;font-weight:700;color:var(--good);}
.cnt-v span{font-family:var(--serif);font-size:26px;font-weight:700;color:var(--ini);}
.legend{display:flex;gap:16px;flex-wrap:wrap;align-items:center;margin-top:20px;font-size:11.5px;color:var(--label);}
.legend .chip{min-width:24px;height:17px;margin-right:6px;}
.stamp{margin-top:14px;font-size:11px;color:var(--label);opacity:.85;}
```

## Esqueleto do corpo

```html
<div class="wrap">
  <header class="mast">
    <div>
      <p class="eyebrow">Consumer BPC</p>
      <h1>B&amp;W Marketing Technology 2026 Agenda</h1>
    </div>
    <div class="brand">
      <span class="uni"><b>U</b><small>Unilever</small></span>
      <span class="rule"></span><span class="bw">B&amp;W</span>
    </div>
  </header>

  <div class="grid">
    <!-- um card por frente: -->
    <article class="card">
      <h3 class="frente">Insights</h3>
      <!-- um bloco por iniciativa; class="blk hl" se tiver Atenção/Crítico -->
      <div class="blk hl">
        <p class="ini">Winnin</p>
        <div class="row"><span class="rl">Deployment</span><span class="chips">
          <span class="chip good">BR</span><span class="chip good">MX</span><span class="chip good">AR</span></span></div>
        <div class="row"><span class="rl">Adoption</span><span class="chips">
          <span class="chip good">BR</span><span class="chip good">MX</span><span class="chip warn">AR</span></span></div>
      </div>
      <!-- ... demais iniciativas ... -->
    </article>
    <!-- ... demais frentes ... -->
  </div>

  <section class="ops">
    <div class="ops-title">Marketing<br>Operations</div>
    <div class="ops-grid">
      <div class="ops-col">
        <p class="ops-h">Social Media Access Mgmt</p>
        <div class="row"><span class="rl">Deployment</span><span class="chips">
          <span class="chip idle">BR</span><span class="chip idle">MX</span><span class="chip idle">AR</span></span></div>
        <div class="row"><span class="rl">Adoption</span><span class="chips">
          <span class="chip idle">BR</span><span class="chip idle">MX</span><span class="chip idle">AR</span></span></div>
      </div>
      <div class="ops-col">
        <p class="ops-h">Operational Support</p>
        <div class="cnt-h"><span>BR</span><span>MX</span><span>AR</span></div>
        <div class="cnt-v"><span>0</span><span>0</span><span>0</span></div>
      </div>
      <!-- Cyber/AI Assessments e Automation Requests iguais -->
    </div>
  </section>

  <div class="legend">
    <span><span class="chip good">BR</span>No prazo</span>
    <span><span class="chip warn">BR</span>Atenção</span>
    <span><span class="chip bad">BR</span>Crítico</span>
    <span><span class="chip idle">BR</span>Não iniciado</span>
    <span><span class="chip na">–</span>N/A</span>
  </div>
</div>
```
