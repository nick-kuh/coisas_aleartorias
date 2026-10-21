#!/usr/bin/env python3
"""Put the Race to 2030 video inside the CDIO LATAM strategy page, as its opening screen.

The page (v14) already has an intro screen that pointed at the video on SharePoint/Stream,
which needs a Microsoft login, is blocked when the file is opened locally and never says
when the video ends. This swaps that iframe for a native <video> whose MP4 travels inside
the HTML (base64), so the page works offline, from any folder, with no login:

  - plays as soon as the page opens; when the browser does not allow sound to start on its
    own, a Play button shows over a cover frame (one click and it plays with sound)
  - the progress bar follows the real video, and the strategy appears when it ends
  - "Go to 2027 Strategy" / Esc / Enter skip it; Space pauses; "Watch intro" replays it

    python3 embed_intro.py PAGE.html [--video out/race-to-2030-hook.mp4] [--out out/PAGE_v15.html]
"""
import argparse
import base64
import pathlib
import re
import subprocess
import tempfile

HERE = pathlib.Path(__file__).resolve().parent

CSS = """
/* ===== INTRO VIDEO (v15) · native player, the MP4 is embedded in this file ===== */
.intro{--vw:max(320px,min(90vw,calc((100vh - 150px)*16/9),1600px))}  /* until fit() runs, or if scripts are blocked */
.intro-frame video{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;background:#000;cursor:pointer}
.intro-play{position:absolute;inset:0;z-index:3;display:grid;place-items:center;text-align:left;background:radial-gradient(60% 60% at 50% 50%,rgba(12,17,30,.1),rgba(12,17,30,.55));transition:opacity .35s var(--ease)}
.intro-play.hide{opacity:0;pointer-events:none}
.intro-play>span{display:inline-flex;align-items:center;gap:16px;padding:12px 28px 12px 12px;border-radius:999px;background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.28);backdrop-filter:blur(8px);color:#fff;font-size:18px;font-weight:600;letter-spacing:-.01em;transition:transform .3s var(--ease),background .25s}
.intro-play:hover>span,.intro-play:focus-visible>span{background:rgba(255,255,255,.18);transform:scale(1.04)}
.intro-play i{width:56px;height:56px;flex:none;border-radius:50%;display:grid;place-items:center;background:conic-gradient(from 210deg,var(--c1),var(--c3),var(--c5),var(--c1));box-shadow:0 10px 30px -10px var(--c3)}
.intro-play svg{width:20px;height:20px;fill:#fff;margin-left:3px}
.intro-play em{display:block;font-style:normal}
.intro-play small{display:block;margin-top:4px;font-size:10.5px;font-weight:700;letter-spacing:.18em;text-transform:uppercase;color:rgba(255,255,255,.6)}
.intro-replay{position:fixed;right:22px;bottom:22px;z-index:30;display:none;align-items:center;gap:10px;padding:8px 16px 8px 8px;border-radius:999px;font-size:12.5px;font-weight:600;color:var(--ink);background:#fff;border:1px solid var(--line);box-shadow:0 14px 30px -20px rgba(18,26,46,.55);transition:transform .3s var(--ease),box-shadow .3s}
.intro-replay.on{display:inline-flex;animation:rv .6s var(--ease) both}
.intro-replay:hover,.intro-replay:focus-visible{transform:translateY(-2px);box-shadow:0 18px 34px -18px rgba(18,26,46,.6)}
.intro-replay i{width:28px;height:28px;border-radius:50%;display:grid;place-items:center;background:conic-gradient(from 210deg,var(--c1),var(--c3),var(--c5),var(--c1))}
.intro-replay svg{width:11px;height:11px;fill:#fff;margin-left:2px}
@media print{.intro-replay{display:none!important}}
/* shown when the page is opened somewhere that cannot run it (Teams / SharePoint preview, blocked player) */
.intro-help{position:absolute;inset:0;z-index:4;display:none;flex-direction:column;align-items:center;justify-content:center;gap:14px;padding:40px;text-align:center;color:#fff;background:rgba(12,17,30,.8);backdrop-filter:blur(4px)}
.intro-help.on{display:flex}
.intro-help b{font-size:24px;font-weight:600;letter-spacing:-.02em}
.intro-help span{max-width:620px;font-size:15px;line-height:1.55;color:rgba(255,255,255,.78)}
.intro-help ol{display:flex;gap:10px;margin:6px 0 0;padding:0;list-style:none;counter-reset:s}
.intro-help li{counter-increment:s;display:flex;align-items:center;gap:10px;padding:9px 16px 9px 9px;border-radius:999px;font-size:13.5px;font-weight:600;background:rgba(255,255,255,.08);border:1px solid rgba(255,255,255,.18)}
.intro-help li::before{content:counter(s);width:24px;height:24px;border-radius:50%;display:grid;place-items:center;font-size:12px;background:conic-gradient(from 210deg,var(--c1),var(--c3),var(--c5),var(--c1))}
"""

PLAYER = """<video id="intro-video" playsinline preload="auto" poster="data:image/jpeg;base64,{poster}" aria-label="Race to 2030 · opening video"></video>
    <button type="button" class="intro-play hide" id="intro-play" aria-label="Play the opening video with sound"><span><i><svg viewBox="0 0 24 24"><path d="M7 4.5v15l13-7.5z"/></svg></i><em>Play intro<small>Race to 2030 · {length} · sound on</small></em></span></button>
    <div class="intro-help" id="intro-help" role="alert"><b>The video can't play here</b><span>This viewer is blocking the player. Download the file and open it in Edge or Chrome, or go straight to the 2027 Strategy.</span><ol><li>Download the file</li><li>Open it in Edge or Chrome</li></ol></div>
    <noscript><div class="intro-help on"><b>Open this page in your browser</b><span>Previews like Teams and SharePoint don't run the video or the interactive strategy. Download the file and open it in Edge or Chrome.</span><ol><li>Download the file</li><li>Open it in Edge or Chrome</li></ol></div></noscript>"""

REPLAY = """<button type="button" class="intro-replay" id="intro-replay" aria-label="Watch the opening video again"><i><svg viewBox="0 0 24 24"><path d="M7 4.5v15l13-7.5z"/></svg></i>Watch intro</button>"""

SCRIPT = """<script type="application/octet-stream" id="intro-mp4">__VIDEO__</script>
<script>
/* ===== INTRO VIDEO (v15) · plays first, then reveals the strategy ===== */
(function(){
  const intro=document.getElementById("intro"),vid=document.getElementById("intro-video"),bar=document.getElementById("intro-bar");
  const playBtn=document.getElementById("intro-play"),skip=document.getElementById("intro-skip"),replay=document.getElementById("intro-replay");
  const root=document.documentElement;root.classList.add("intro-on");
  let done=false,raf=null;
  const help=document.getElementById("intro-help");
  /* when this viewer cannot play the video: say how to open it, keep "Go to 2027 Strategy" working */
  function fail(){if(done)return;playBtn.classList.add("hide");help.classList.add("on");skip.focus({preventScroll:true});}
  /* the MP4 travels inside this file: decode it once into a blob URL (offline, any folder, no login) */
  try{
    const bin=atob(document.getElementById("intro-mp4").textContent.replace(/\\s+/g,"")),buf=new Uint8Array(bin.length);
    for(let i=0;i<bin.length;i++)buf[i]=bin.charCodeAt(i);
    vid.src=URL.createObjectURL(new Blob([buf],{type:"video/mp4"}));
  }catch(e){fail();}
  function size(){const w=Math.min(innerWidth*.9,(innerHeight-150)*16/9,1600);intro.style.setProperty("--vw",Math.max(320,w)+"px");}
  function tick(){bar.style.transform=`scaleX(${vid.duration?vid.currentTime/vid.duration:0})`;if(!done)raf=requestAnimationFrame(tick);}
  /* starts with sound when the browser allows it; otherwise the Play button stays up */
  function play(){
    if(help.classList.contains("on"))return;
    const t=vid.currentTime;   /* asked to play but the clock never moves (spinner, frozen first frame) */
    setTimeout(()=>{if(!done&&!vid.paused&&vid.currentTime<=t+0.05)fail();},8000);
    vid.play().then(()=>playBtn.classList.add("hide")).catch(e=>{if(e&&e.name==="NotSupportedError")fail();else{playBtn.classList.remove("hide");playBtn.focus({preventScroll:true});}});
  }
  function finish(){
    if(done)return;done=true;cancelAnimationFrame(raf);vid.pause();bar.style.transform="scaleX(1)";
    intro.classList.add("out");root.classList.remove("intro-on");replay.classList.add("on");
    setTimeout(()=>{if(typeof fit==="function")fit();},950);
  }
  function reopen(){
    done=false;if(vid.readyState)vid.currentTime=0;root.classList.add("intro-on");intro.classList.remove("out");replay.classList.remove("on");
    size();tick();play();skip.focus({preventScroll:true});
  }
  vid.addEventListener("ended",finish);
  vid.addEventListener("error",fail);
  vid.addEventListener("play",()=>playBtn.classList.add("hide"));
  vid.addEventListener("pause",()=>{if(!done&&!vid.ended&&!help.classList.contains("on"))playBtn.classList.remove("hide");});
  vid.addEventListener("click",()=>vid.paused?play():vid.pause());
  playBtn.addEventListener("click",play);
  skip.addEventListener("click",finish);
  replay.addEventListener("click",reopen);
  document.addEventListener("keydown",e=>{
    if(done)return;
    if(e.key===" "){e.preventDefault();e.stopImmediatePropagation();vid.paused?play():vid.pause();}
    else if(["Enter","ArrowRight","Escape"].includes(e.key)&&document.activeElement!==playBtn){e.preventDefault();e.stopImmediatePropagation();finish();}
  },true);
  addEventListener("resize",size);size();tick();
  skip.focus({preventScroll:true});
  play();
})();
</script>"""


def run(*cmd):
    return subprocess.run(cmd, check=True, capture_output=True).stdout


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('html', help='strategy page with the v12 intro screen (e.g. CDIO_LATAM_2027_Strategy_E3_v14.html)')
    ap.add_argument('--video', default=str(HERE / 'out' / 'race-to-2030-hook.mp4'))
    ap.add_argument('--poster-at', type=float, default=4.6, help='second of the video used as cover frame')
    ap.add_argument('--out', default=str(HERE / 'out' / 'CDIO_LATAM_2027_Strategy_E3_v15.html'))
    a = ap.parse_args()

    page = pathlib.Path(a.html).read_text(encoding='utf-8')
    with tempfile.TemporaryDirectory() as tmp:
        web, poster = pathlib.Path(tmp, 'web.mp4'), pathlib.Path(tmp, 'poster.jpg')
        # lighter encode for the page: same look (SSIM ~0.998), ~1/3 of the size
        run('ffmpeg', '-v', 'error', '-y', '-i', a.video, '-c:v', 'libx264', '-preset', 'slow', '-crf', '25',
            '-tune', 'animation', '-profile:v', 'high', '-level', '4.1', '-pix_fmt', 'yuv420p',
            '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart', str(web))
        run('ffmpeg', '-v', 'error', '-y', '-ss', str(a.poster_at), '-i', a.video, '-frames:v', '1',
            '-vf', 'scale=1280:-2', '-q:v', '4', str(poster))
        secs = float(run('ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(web)))
        video_b64 = base64.b64encode(web.read_bytes()).decode()
        poster_b64 = base64.b64encode(poster.read_bytes()).decode()
    length = f'{int(secs // 60)}:{int(round(secs % 60)):02d}'

    iframe = re.compile(r'<iframe id="intro-video"[^>]*></iframe>')
    old_js = re.compile(r'<script>\s*/\* ===== INTRO VIDEO \(v12\).*?</script>', re.S)
    print_rule = '@media print{.intro{display:none!important}}'
    section_end = re.compile(r'(<section class="intro" id="intro".*?</section>)', re.S)
    for what, ok in [('intro iframe', iframe.search(page)), ('v12 intro script', old_js.search(page)),
                     ('intro print rule', print_rule in page), ('intro section', section_end.search(page))]:
        if not ok:
            raise SystemExit(f'could not find the {what} in {a.html}: is this the v14 page with the intro screen?')

    page = page.replace('</head>', '<noscript><style>.intro-skip,.intro-prog,.intro-play{display:none!important}</style></noscript>\n</head>', 1)
    page = iframe.sub(lambda m: PLAYER.format(poster=poster_b64, length=length), page, count=1)
    page = page.replace(print_rule, print_rule + CSS, 1)
    page = section_end.sub(lambda m: m.group(1) + '\n' + REPLAY, page, count=1)
    page = old_js.sub(lambda m: SCRIPT.replace('__VIDEO__', video_b64), page, count=1)
    pathlib.Path(a.out).write_text(page, encoding='utf-8')
    print(a.out, f'{len(page.encode()) / 1e6:.1f} MB (video {length})')


if __name__ == '__main__':
    main()
