from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

import numpy as np
from moviepy.editor import VideoFileClip
import yt_dlp


@dataclass
class SegmentScore:
    start: float
    end: float
    score: float


class ShortsGenerator:
    """Create short-form clips from a long-form YouTube video using retention-like scoring."""

    def __init__(
        self,
        output_dir: str = "output",
        segment_length: int = 45,
        overlap: int = 15,
        min_shorts: int = 10,
        sample_fps: int = 2,
    ) -> None:
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.segment_length = segment_length
        self.overlap = overlap
        self.min_shorts = max(min_shorts, 10)
        self.sample_fps = sample_fps

    def download_video(self, youtube_url: str) -> Path:
        target = self.output_dir / "source"
        target.mkdir(parents=True, exist_ok=True)

        ydl_opts = {
            "format": "bestvideo+bestaudio/best",
            "outtmpl": str(target / "%(title)s.%(ext)s"),
            "merge_output_format": "mp4",
            "quiet": True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(youtube_url, download=True)
            video_path = Path(ydl.prepare_filename(info))

        if video_path.suffix != ".mp4":
            maybe_mp4 = video_path.with_suffix(".mp4")
            if maybe_mp4.exists():
                return maybe_mp4

        return video_path

    def score_segments(self, clip: VideoFileClip) -> List[SegmentScore]:
        duration = int(clip.duration)
        step = max(5, self.segment_length - self.overlap)

        segments: List[SegmentScore] = []
        for start in range(0, max(1, duration - self.segment_length + 1), step):
            end = min(duration, start + self.segment_length)
            score = self._retention_proxy_score(clip, start, end)
            segments.append(SegmentScore(float(start), float(end), float(score)))

        if not segments:
            segments.append(
                SegmentScore(0.0, min(float(duration), float(self.segment_length)), 0.0)
            )

        segments.sort(key=lambda s: s.score, reverse=True)
        return segments

    def _retention_proxy_score(self, clip: VideoFileClip, start: int, end: int) -> float:
        sample_times = np.arange(start, end, 1 / self.sample_fps)
        visual_change = []

        previous_frame = None
        for t in sample_times:
            frame = clip.get_frame(float(t))
            gray = np.mean(frame, axis=2)
            if previous_frame is not None:
                visual_change.append(np.mean(np.abs(gray - previous_frame)))
            previous_frame = gray

        visual_score = float(np.mean(visual_change)) if visual_change else 0.0

        audio_score = 0.0
        if clip.audio is not None:
            audio = clip.audio.subclip(start, end).to_soundarray(fps=22050)
            if audio.size > 0:
                audio_score = float(np.mean(np.abs(audio))) * 255

        return 0.7 * visual_score + 0.3 * audio_score

    def export_top_shorts(self, clip: VideoFileClip, segments: List[SegmentScore]) -> List[Path]:
        shorts_dir = self.output_dir / "shorts"
        shorts_dir.mkdir(parents=True, exist_ok=True)

        selected = self._select_diverse_segments(segments, target_count=self.min_shorts)
        outputs: List[Path] = []

        for idx, seg in enumerate(selected, start=1):
            short_path = shorts_dir / f"short_{idx:02d}_{int(seg.start)}-{int(seg.end)}.mp4"
            sub = clip.subclip(seg.start, seg.end)
            sub.write_videofile(
                str(short_path),
                codec="libx264",
                audio_codec="aac",
                fps=max(24, int(clip.fps or 24)),
                verbose=False,
                logger=None,
            )
            outputs.append(short_path)

        return outputs

    def _select_diverse_segments(
        self,
        ranked: List[SegmentScore],
        target_count: int,
        min_gap: int = 10,
    ) -> List[SegmentScore]:
        chosen: List[SegmentScore] = []

        for seg in ranked:
            if all(abs(seg.start - c.start) >= min_gap for c in chosen):
                chosen.append(seg)
            if len(chosen) >= target_count:
                break

        idx = 0
        while len(chosen) < target_count and ranked:
            chosen.append(ranked[idx % len(ranked)])
            idx += 1

        return chosen

    def run(self, youtube_url: str) -> List[Path]:
        source = self.download_video(youtube_url)
        with VideoFileClip(str(source)) as clip:
            segments = self.score_segments(clip)
            shorts = self.export_top_shorts(clip, segments)
        return shorts
