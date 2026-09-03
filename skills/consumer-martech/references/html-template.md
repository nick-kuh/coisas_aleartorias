# Template do dashboard HTML — Consumer (versão LEVE, para o agente)

Duas verdades importantes:

1. **O board oficial (logo real Unilever·B&W + fonte Poppins embutida) NÃO sai por
   aqui.** Ele exige embutir ~48 KB de logo e ~43 KB de fonte em base64, byte a byte
   — um modelo de linguagem não reproduz isso. Esse board sai do **gerador
   determinístico** (`scripts/gerar-consumer-html.py`) ou de um **Office Script +
   Power Automate**. É esse que o Nick aprovou.
2. **O que VOCÊ (agente) gera na conversa é a versão leve abaixo** — mesma família
   visual (hero roxo, cards brancos, chips, tom claro, fonte Poppins via link), mas
   **sem** o logo real embutido. Serve para um preview rápido. Se pedirem "o board
   oficial/bonito", diga que ele é gerado pelo script/Power Automate e ofereça a
   análise + este preview.

**Regra:** entregue **um HTML só**. Reproduza este esqueleto fielmente — hero roxo,
régua de stats, um card por frente, chips BR/MX/AR. **Não** faça tabela genérica.
**Não** invente dados: só o que veio do Consumer MarTech Tracker.

## Como preencher

- **Stats** (na faixa roxa): nº de iniciativas, nº de frentes, % no prazo, em
  atenção, críticos — contados do tracker.
- **Card por frente** na ordem: Insights · Media & Influencer · dCom and Social
  Commerce · CoPilot and Agentic · LLM Search / GEO · Beauty Tech. Cada card: um
  **farol dot** (🔴 se tem crítico · 🟢 se ≥50% no prazo e sem crítico · 🟡 senão) +
  o nome, e um **bloco por iniciativa** (nome + uma linha por registro).
- **Rótulo da linha** = o Item se houver (Dove, CMI…), senão a Fase
  (Deployment/Adoption). Bloco com Atenção/Crítico ganha classe `blk hl`.
- **Chips:** No prazo→`good` · Atenção→`warn` · Crítico→`bad` · Não iniciado→`idle`
  · N/A→`na` (conteúdo "–").

## Esqueleto completo (colar e preencher)

```html
<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light">
<title>B&amp;W Marketing Technology 2026 Agenda</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@500;600;700;800&display=swap" rel="stylesheet">
<style>
  :root{
    --page1:#FFFFFF; --page2:#F3ECFC; --purple:#6D28D9; --purple-2:#8B5CF6;
    --purple-3:#A78BFA; --purple-deep:#5B21B6; --card:#FFFFFF; --card-hl:#F5EFFD;
    --card-line:#EDE4F9; --ink:#241C36; --frente:#6D28D9; --label:#6B6480; --faint:#9E97B0;
    --good:#22B26B; --warn:#F4B72E; --warn-ink:#5A4200; --bad:#E5484D;
    --idle:#CBD0DB; --na:#EFEAF7; --na-ink:#B4ADC2; --ops:#F4EDFD; --ops-line:#E8DCF8;
    --body:'Poppins',system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
  }
  *{box-sizing:border-box;}
  body{margin:0;color:var(--ink);font-family:var(--body);line-height:1.45;min-height:100vh;
    background:linear-gradient(180deg,var(--page1),var(--page2));}
  .wrap{max-width:1500px;margin:0 auto;padding:26px 28px 44px;}
  .hero{position:relative;overflow:hidden;border-radius:28px;padding:36px 44px 34px;color:#fff;
    box-shadow:0 22px 54px -26px rgba(109,40,217,.55);
    background:radial-gradient(130% 150% at 90% -35%,rgba(255,255,255,.4),transparent 48%),
      linear-gradient(115deg,var(--purple-deep),var(--purple) 40%,var(--purple-2) 74%,var(--purple-3));}
  .hero-top{display:flex;align-items:center;justify-content:space-between;gap:32px;flex-wrap:wrap;}
  .eyebrow{font-size:12px;font-weight:600;letter-spacing:.24em;text-transform:uppercase;color:rgba(255,255,255,.85);margin:0 0 10px;}
  h1{font-weight:800;margin:0;color:#fff;font-size:clamp(30px,3.6vw,50px);line-height:1;letter-spacing:-.03em;}
  .brand{display:flex;align-items:center;gap:14px;color:#fff;}
  .brand .u{font-family:Georgia,serif;font-weight:700;font-size:44px;line-height:1;}
  .brand .rule{width:2px;height:46px;background:rgba(255,255,255,.6);}
  .brand .bw{font-family:Georgia,serif;font-weight:700;font-size:40px;letter-spacing:.01em;}
  .stats{display:flex;flex-wrap:wrap;gap:12px;margin-top:26px;}
  .stat{display:flex;align-items:baseline;gap:8px;padding:10px 18px;border-radius:999px;background:rgba(255,255,255,.16);border:1px solid rgba(255,255,255,.3);}
  .stat b{font-size:20px;font-weight:700;} .stat span{font-size:12px;color:rgba(255,255,255,.86);font-weight:500;}
  .sec-head{display:flex;align-items:center;justify-content:space-between;gap:18px;flex-wrap:wrap;margin:30px 2px 16px;}
  .sec-head h2{font-size:15px;font-weight:800;color:var(--frente);margin:0;text-transform:uppercase;}
  .legend{display:flex;gap:14px;flex-wrap:wrap;align-items:center;font-size:11.5px;color:var(--label);}
  .legend .chip{min-width:23px;height:17px;margin-right:6px;}
  .grid{display:grid;grid-template-columns:repeat(6,1fr);gap:16px;align-items:start;}
  @media (max-width:1200px){.grid{grid-template-columns:repeat(3,1fr);}}
  @media (max-width:760px){.grid{grid-template-columns:repeat(2,1fr);}}
  @media (max-width:480px){.grid{grid-template-columns:1fr;}}
  .card{background:var(--card);border:1px solid var(--card-line);border-radius:18px;box-shadow:0 12px 34px -18px rgba(70,25,140,.35);overflow:hidden;}
  .card-h{display:flex;align-items:center;justify-content:center;gap:8px;padding:15px 14px 13px;border-bottom:1px solid var(--card-line);background:linear-gradient(180deg,rgba(124,58,237,.06),transparent);}
  .dot{width:8px;height:8px;border-radius:50%;}
  .dot.good{background:var(--good);} .dot.warn{background:var(--warn);} .dot.bad{background:var(--bad);}
  .frente{color:var(--frente);text-align:center;font-weight:800;font-size:14.5px;margin:0;}
  .card-b{padding:15px 15px 17px;}
  .blk{margin-bottom:14px;} .blk:last-child{margin-bottom:0;}
  .blk.hl{background:var(--card-hl);border:1px solid var(--card-line);border-radius:12px;padding:9px 10px;margin:0 -4px 14px;}
  .ini{font-weight:700;font-size:12.5px;color:var(--ink);margin:0 0 7px;}
  .row{display:flex;align-items:center;justify-content:space-between;gap:8px;padding:2.5px 0;font-size:11.5px;color:var(--label);}
  .rl{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
  .chips{display:inline-flex;gap:5px;flex:none;}
  .chip{display:inline-flex;align-items:center;justify-content:center;min-width:30px;height:20px;padding:0 5px;border-radius:6px;font-size:10px;font-weight:700;color:#fff;}
  .chip.good{background:var(--good);} .chip.warn{background:var(--warn);color:var(--warn-ink);}
  .chip.bad{background:var(--bad);} .chip.idle{background:var(--idle);} .chip.na{background:var(--na);color:var(--na-ink);}
  .stamp{margin-top:18px;font-size:11px;color:var(--faint);text-align:center;}
</style>
</head>
<body>
<div class="wrap">
  <header class="hero">
    <div class="hero-top">
      <div>
        <p class="eyebrow">Consumer BPC</p>
        <h1>B&amp;W Marketing Technology<br>2026 Agenda</h1>
      </div>
      <!-- Logo: versão leve = lockup tipográfico. Se houver o logo hospedado,
           troque por <img src="URL_DO_LOGO" alt="Unilever Beauty & Wellbeing" style="height:70px"> -->
      <div class="brand"><span class="u">U</span><span class="rule"></span><span class="bw">B&amp;W</span></div>
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
</div>
</body>
</html>
```
