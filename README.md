# YouTube Long Video to Shorts Generator

This application converts a long-form YouTube video into short-form clips by using a retention-style scoring heuristic.

## How it works

1. Downloads a YouTube video URL.
2. Splits the video into overlapping candidate segments.
3. Scores each segment using:
   - visual activity (frame-to-frame changes), and
   - audio intensity.
4. Selects top segments with diversity constraints.
5. Exports at least **10 shorts** for every input video.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Usage

```bash
python shorts_app.py "https://www.youtube.com/watch?v=<VIDEO_ID>" --min-shorts 10
```

Optional arguments:

- `--output-dir`: Output folder (default: `output`)
- `--segment-length`: Duration of each short in seconds (default: `45`)
- `--overlap`: Overlap between analysis windows in seconds (default: `15`)
- `--min-shorts`: Minimum number of generated shorts (minimum enforced to `10`)

Generated clips are written to:

- `output/source/` (downloaded source video)
- `output/shorts/` (short-form clips)

## Notes

- The app uses a retention proxy heuristic, not native YouTube Analytics retention data.
- Ensure `ffmpeg` is installed on your machine for video export.
