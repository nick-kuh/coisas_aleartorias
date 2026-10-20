#!/usr/bin/env python3
"""Lay the soundtrack (and, if given, a narration track) onto the rendered video.

    python3 audio/mux.py                                  -> out/race-to-2030-hook.mp4 (music only)
    python3 audio/mux.py --voice out/narration.wav        -> music ducked under the voice

Loudness is normalised to -16 LUFS / -1.5 dBTP (two-pass loudnorm).
"""
import argparse
import json
import pathlib
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / 'out'

ap = argparse.ArgumentParser()
ap.add_argument('--video', default=str(OUT / 'video.mp4'), help='silent render from render.mjs')
ap.add_argument('--music', default=str(OUT / 'soundtrack.wav'))
ap.add_argument('--voice', help='narration WAV, same timeline as the video')
ap.add_argument('--out', default=str(OUT / 'race-to-2030-hook.mp4'))
args = ap.parse_args()


def graph(music, voice=None):
    """Audio graph ending in [pre]; the music is ducked whenever the voice speaks."""
    if not voice:
        return f'{music}anull[pre]'
    return (f'{voice}aformat=channel_layouts=stereo,asplit=2[v][sc];'
            f'{music}[sc]sidechaincompress=threshold=0.05:ratio=4:attack=20:release=350[duck];'
            '[duck]volume=0.55[m];[m][v]amix=inputs=2:weights=1 1.6:normalize=0[pre]')


audio_in = ['-i', args.music] + (['-i', args.voice] if args.voice else [])

# pass 1: measure loudness of the final mix
g = graph('[0:a]', '[1:a]' if args.voice else None)
err = subprocess.run(['ffmpeg', '-hide_banner', *audio_in, '-filter_complex',
                      g + ';[pre]loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json[o]',
                      '-map', '[o]', '-f', 'null', '-'], capture_output=True, text=True, check=True).stderr
m = json.loads(err[err.rindex('{'): err.rindex('}') + 1])
norm = (f"loudnorm=I=-16:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
        f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")

# pass 2: normalise and mux with the untouched video stream (input 0 is the video here)
g = graph('[1:a]', '[2:a]' if args.voice else None)
subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', args.video, *audio_in,
                '-filter_complex', g + f';[pre]{norm},aresample=48000[a]',
                '-map', '0:v', '-map', '[a]', '-c:v', 'copy', '-c:a', 'aac', '-b:a', '256k',
                '-shortest', '-movflags', '+faststart', args.out], check=True)
print(args.out, f"(mix measured {m['input_i']} LUFS, normalised to -16 LUFS)")
