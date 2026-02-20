import argparse

from retention_shorts import ShortsGenerator


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create short videos from a YouTube URL using retention-like scoring."
    )
    parser.add_argument("url", help="YouTube URL of the long-form video")
    parser.add_argument(
        "--output-dir",
        default="output",
        help="Directory where downloaded video and generated shorts are stored",
    )
    parser.add_argument(
        "--segment-length",
        default=45,
        type=int,
        help="Length of each short segment in seconds",
    )
    parser.add_argument(
        "--overlap",
        default=15,
        type=int,
        help="Overlap between analyzed segments in seconds",
    )
    parser.add_argument(
        "--min-shorts",
        default=10,
        type=int,
        help="Minimum number of shorts to generate (minimum enforced: 10)",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    generator = ShortsGenerator(
        output_dir=args.output_dir,
        segment_length=args.segment_length,
        overlap=args.overlap,
        min_shorts=args.min_shorts,
    )

    shorts = generator.run(args.url)

    print(f"Generated {len(shorts)} shorts:")
    for short in shorts:
        print(f"- {short}")


if __name__ == "__main__":
    main()
