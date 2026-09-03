/**
 * Office Script — "Consumer Board Builder"
 * Lê a aba Tracker do BW_MarTech_2026_Controle_Projetos.xlsx e devolve o HTML do
 * board de Consumer (mesmo modelo aprovado: hero roxo, logo real, Poppins, cards,
 * chips BR/MX/AR, tom claro). Determinístico — é o que garante o board EXATO que
 * um modelo de linguagem não consegue reproduzir.
 *
 * Como usar: Excel Online → Automatizar → Novo Script → cole isto → Salvar.
 * O Power Automate chama este script (ação "Executar script") e salva/retorna o HTML.
 *
 * Ajuste LOGO_URL para a URL do logo BRANCO (assets/logo-bw-white.svg) hospedado no
 * seu SharePoint. O texto do logo cai para um lockup se a URL ficar vazia.
 */

const LOGO_URL = ""; // ex.: "https://unilever.sharepoint.com/.../logo-bw-white.svg"

const FRENTES = [
  "Insights",
  "Media & Influencer",
  "dCom and Social Commerce",
  "CoPilot and Agentic",
  "LLM Search / GEO",
  "Beauty Tech",
];

// status -> classe do chip
const STATUS: { [k: string]: string } = {
  "No prazo": "good",
  "Atenção": "warn",
  "Crítico": "bad",
  "Não iniciado": "idle",
  "N/A": "na",
};
const MERCADOS = ["BR", "MX", "AR"];

interface Linha {
  frente: string; iniciativa: string; item: string; fase: string;
  BR: string; MX: string; AR: string;
}

function main(workbook: ExcelScript.Workbook): string {
  const ws = workbook.getWorksheet("Tracker");
  const values = ws.getUsedRange().getValues();
  const linhas: Linha[] = [];
  // cabeçalho na linha 3 (índice 2); dados a partir do índice 3
  for (let i = 3; i < values.length; i++) {
    const r = values[i];
    const frente = String(r[0] ?? "").trim();
    if (!frente) continue;
    linhas.push({
      frente,
      iniciativa: String(r[1] ?? "").trim(),
      item: String(r[2] ?? "").trim(),
      fase: String(r[3] ?? "").trim(),
      BR: String(r[4] ?? "").trim(),
      MX: String(r[5] ?? "").trim(),
      AR: String(r[6] ?? "").trim(),
    });
  }
  return buildHtml(linhas);
}

function esc(s: string): string {
  return (s || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function conta(linhas: Linha[], frente?: string) {
  const c: { [k: string]: number } = { "No prazo": 0, "Atenção": 0, "Crítico": 0, "Não iniciado": 0 };
  for (const l of linhas) {
    if (frente && l.frente !== frente) continue;
    for (const m of MERCADOS) {
      const v = (l as unknown as { [k: string]: string })[m];
      if (v in c) c[v]++;
    }
  }
  const total = c["No prazo"] + c["Atenção"] + c["Crítico"] + c["Não iniciado"];
  const pct = total ? c["No prazo"] / total : 0;
  return { c, total, pct };
}

function farolDot(c: { [k: string]: number }, pct: number): string {
  if (c["Crítico"] > 0) return "bad";
  return pct >= 0.5 ? "good" : "warn";
}

function chip(code: string, status: string): string {
  if (!status) return `<span class="chip idle" style="opacity:0">${code}</span>`;
  const cls = STATUS[status] || "idle";
  const label = status === "N/A" ? "–" : code;
  return `<span class="chip ${cls}" title="${esc(code)} · ${esc(status)}">${label}</span>`;
}

function rotulo(l: Linha): string {
  if (l.item) return l.item;
  if (l.fase === "Deployment" || l.fase === "Adoption") return l.fase;
  return "";
}

function renderCard(frente: string, linhas: Linha[]): string {
  const sub = linhas.filter(l => l.frente === frente);
  if (sub.length === 0) return "";
  // agrupa por iniciativa, na ordem
  const grupos: { nome: string; ls: Linha[] }[] = [];
  for (const l of sub) {
    if (grupos.length === 0 || grupos[grupos.length - 1].nome !== l.iniciativa) {
      grupos.push({ nome: l.iniciativa, ls: [] });
    }
    grupos[grupos.length - 1].ls.push(l);
  }
  let blocos = "";
  for (const g of grupos) {
    const hl = g.ls.some(l => MERCADOS.some(m => {
      const v = (l as unknown as { [k: string]: string })[m];
      return v === "Atenção" || v === "Crítico";
    }));
    let rows = "";
    for (const l of g.ls) {
      const r = rotulo(l);
      const chips = MERCADOS.map(m => chip(m, (l as unknown as { [k: string]: string })[m])).join("");
      rows += `<div class="row"><span class="rl">${esc(r)}</span><span class="chips">${chips}</span></div>`;
    }
    blocos += `<div class="blk${hl ? " hl" : ""}"><p class="ini">${esc(g.nome)}</p>${rows}</div>`;
  }
  const { c, pct } = conta(linhas, frente);
  const dot = farolDot(c, pct);
  return `<article class="card"><header class="card-h"><span class="dot ${dot}"></span>` +
    `<h3 class="frente">${esc(frente)}</h3></header><div class="card-b">${blocos}</div></article>`;
}

function buildHtml(linhas: Linha[]): string {
  const cards = FRENTES.map(f => renderCard(f, linhas)).join("");
  const { c, pct } = conta(linhas);
  const nIni = new Set(linhas.map(l => l.frente + "|" + l.iniciativa)).size;
  const logo = LOGO_URL
    ? `<img class="logo-bw" src="${LOGO_URL}" alt="Unilever Beauty & Wellbeing">`
    : `<div class="brand"><span class="u">U</span><span class="rule"></span><span class="bw">B&amp;W</span></div>`;

  const css = `
:root{--page1:#FFFFFF;--page2:#F3ECFC;--purple:#6D28D9;--purple-2:#8B5CF6;--purple-3:#A78BFA;--purple-deep:#5B21B6;
--card:#FFFFFF;--card-hl:#F5EFFD;--card-line:#EDE4F9;--ink:#241C36;--frente:#6D28D9;--label:#6B6480;--faint:#9E97B0;
--good:#22B26B;--warn:#F4B72E;--warn-ink:#5A4200;--bad:#E5484D;--idle:#CBD0DB;--na:#EFEAF7;--na-ink:#B4ADC2;
--body:'Poppins',system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;}
*{box-sizing:border-box;}body{margin:0;color:var(--ink);font-family:var(--body);line-height:1.45;min-height:100vh;
background:linear-gradient(180deg,var(--page1),var(--page2));}
.wrap{max-width:1500px;margin:0 auto;padding:26px 28px 44px;}
.hero{position:relative;overflow:hidden;border-radius:28px;padding:36px 44px 34px;color:#fff;
box-shadow:0 22px 54px -26px rgba(109,40,217,.55);
background:radial-gradient(130% 150% at 90% -35%,rgba(255,255,255,.4),transparent 48%),
linear-gradient(115deg,var(--purple-deep),var(--purple) 40%,var(--purple-2) 74%,var(--purple-3));}
.hero-top{display:flex;align-items:center;justify-content:space-between;gap:32px;flex-wrap:wrap;}
.eyebrow{font-size:12px;font-weight:600;letter-spacing:.24em;text-transform:uppercase;color:rgba(255,255,255,.85);margin:0 0 10px;}
h1{font-weight:800;margin:0;color:#fff;font-size:clamp(30px,3.6vw,50px);line-height:1;letter-spacing:-.03em;}
.logo-bw{width:clamp(250px,26vw,360px);height:auto;display:block;filter:drop-shadow(0 4px 14px rgba(0,0,0,.18));}
.brand{display:flex;align-items:center;gap:14px;color:#fff;}
.brand .u{font-family:Georgia,serif;font-weight:700;font-size:44px;}
.brand .rule{width:2px;height:46px;background:rgba(255,255,255,.6);}
.brand .bw{font-family:Georgia,serif;font-weight:700;font-size:40px;}
.stats{display:flex;flex-wrap:wrap;gap:12px;margin-top:26px;}
.stat{display:flex;align-items:baseline;gap:8px;padding:10px 18px;border-radius:999px;background:rgba(255,255,255,.16);border:1px solid rgba(255,255,255,.3);}
.stat b{font-size:20px;font-weight:700;}.stat span{font-size:12px;color:rgba(255,255,255,.86);font-weight:500;}
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
.dot{width:8px;height:8px;border-radius:50%;}.dot.good{background:var(--good);}.dot.warn{background:var(--warn);}.dot.bad{background:var(--bad);}
.frente{color:var(--frente);text-align:center;font-weight:800;font-size:14.5px;margin:0;}
.card-b{padding:15px 15px 17px;}
.blk{margin-bottom:14px;}.blk:last-child{margin-bottom:0;}
.blk.hl{background:var(--card-hl);border:1px solid var(--card-line);border-radius:12px;padding:9px 10px;margin:0 -4px 14px;}
.ini{font-weight:700;font-size:12.5px;color:var(--ink);margin:0 0 7px;}
.row{display:flex;align-items:center;justify-content:space-between;gap:8px;padding:2.5px 0;font-size:11.5px;color:var(--label);}
.rl{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
.chips{display:inline-flex;gap:5px;flex:none;}
.chip{display:inline-flex;align-items:center;justify-content:center;min-width:30px;height:20px;padding:0 5px;border-radius:6px;font-size:10px;font-weight:700;color:#fff;}
.chip.good{background:var(--good);}.chip.warn{background:var(--warn);color:var(--warn-ink);}
.chip.bad{background:var(--bad);}.chip.idle{background:var(--idle);}.chip.na{background:var(--na);color:var(--na-ink);}
.stamp{margin-top:18px;font-size:11px;color:var(--faint);text-align:center;}`;

  const legenda =
    `<span><span class="chip good">BR</span>No prazo</span>` +
    `<span><span class="chip warn">BR</span>Atenção</span>` +
    `<span><span class="chip bad">BR</span>Crítico</span>` +
    `<span><span class="chip idle">BR</span>Não iniciado</span>` +
    `<span><span class="chip na">–</span>N/A</span>`;

  return `<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light">
<title>B&amp;W Marketing Technology 2026 Agenda</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Poppins:wght@500;600;700;800&display=swap" rel="stylesheet">
<style>${css}</style></head><body>
<div class="wrap">
  <header class="hero"><div class="hero-top">
    <div><p class="eyebrow">Consumer BPC</p><h1>B&amp;W Marketing Technology<br>2026 Agenda</h1></div>
    <div class="logo-wrap">${logo}</div>
  </div>
  <div class="stats">
    <div class="stat"><b>${nIni}</b><span>iniciativas</span></div>
    <div class="stat"><b>${FRENTES.length}</b><span>frentes</span></div>
    <div class="stat"><b>${Math.round(pct * 100)}%</b><span>no prazo</span></div>
    <div class="stat"><b>${c["Atenção"]}</b><span>em atenção</span></div>
    <div class="stat"><b>${c["Crítico"]}</b><span>críticos</span></div>
  </div></header>
  <div class="sec-head"><h2>Portfólio por frente</h2><div class="legend">${legenda}</div></div>
  <div class="grid">${cards}</div>
</div></body></html>`;
}
