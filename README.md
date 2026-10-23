# MARBLE SURVIVAL

Free, reproducible 3D short-video series renderer. Episode 001 is 60 seconds,
1080×1920, 30 fps, H.264 MP4 with original synthesized stereo AAC sound effects.
No narration, captions, text overlays, music, paid services, or external assets.

## Run

Requires Python 3.10+, FFmpeg (with libx264), OpenGL 3.3/EGL (Mesa llvmpipe works).

```sh
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python render.py --seconds 5 --output output/marble_survival_001_preview.mp4
ffprobe output/marble_survival_001_preview.mp4
python render.py --output output/marble_survival_001.mp4
```

Set `MESA_SHADER_CACHE_DIR` to a writable directory if necessary. On a headless
Linux machine Mesa EGL and its software OpenGL driver must be installed.
The renderer uses ModernGL with depth-tested perspective geometry, instanced
meshes, procedural glossy glass-like shading, Fresnel edges, colored interiors,
and camera tracking. No Blender installation is required. Glass appearance is
an artistic shader approximation, rather than physically traced refraction.

## Episode 001

| Seconds | Scene |
| --- | --- |
| 0–3 | 100 marbles start together |
| 3–15 | Rotating sweep hammers and openings |
| 15–30 | Two-turn elevated spiral |
| 30–45 | Narrow bridge, moving sweepers, eliminations |
| 45–57 | Three finalists, two late eliminations |
| 57–60 | Winner on podium, colored confetti and chime |

Motion uses deterministic 120 Hz lateral contact impulses, restitution at course
boundaries, damped steering, and gravity during falls. Forward progress and
elimination timing are choreographed to fit the exact editorial durations.
This is a hybrid simulation/animation, not a general rigid-body solver; rotating
obstacles are animated and do not dynamically solve contacts with the marbles.
Scene transitions are editorial cuts and remaining identities/colors persist.

## Series settings

Copy `config/episode_001.json` to a new episode config and change `episode`,
`seed`, widths, lengths, spiral radius/turns, hammer locations, and pit locations.
Then pass `--config config/episode_002.json --output output/marble_survival_002.mp4`.
Keep five stages and the timeline structure for this renderer. The initial marble count and each stage’s `survivors` value are configurable.
Use decreasing counts, with three entering the final and one entering the
celebration. Episode 001 uses 100 → 55 → 24 → 3 → 1.

## Verification

`verify.py` checks codec, duration, dimensions, frame rate, audio presence, frame
count, and fully decodes the finished file. A contact sheet provides visual QA.

```sh
python verify.py output/marble_survival_001.mp4
```

## GitHub distribution

`publish.sh` reuses an existing `marble-survival` repository, or creates a public
one if absent. It pushes source and documentation and attaches the full video
to a GitHub Release. It does not use Git LFS or commit large generated media.
It requires a working `gh` login with repository creation/push/release permission.
The script never enables Actions, paid services, or other billable resources.

```sh
./publish.sh output/marble_survival_001.mp4
```

For the initial execution environment, the GitHub connector could read account
repositories but exposed no repository-creation action; CLI calls to `api.github.com` were blocked by the environment HTTP proxy
(`CONNECT tunnel failed, response 403`). Authentication readiness could not be
verified through that blocked path. Thus remote creation, push and
release publication could not be completed there. Local Git history is included.
