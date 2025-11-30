import subprocess
import os
import argparse
from datetime import datetime
import time


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("url", help="YouTube livestream URL")
    parser.add_argument(
        "-n", "--nth", type=int, default=300, help="Save every n-th frame 300"
    )
    parser.add_argument(
        "-o", "--output", default="frames", help="Folder to save frames"
    )
    parser.add_argument(
        "-d",
        "--duration",
        type=float,
        default=5.0,
        help="Hours of livestream to capture (default: 5.0)",
    )
    parser.add_argument(
        "-t",
        "--timeout",
        type=float,
        default=1800,
        help="Timeout after which the download is stopped",
    )
    args = parser.parse_args()

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = os.path.join(args.output, timestamp)
    os.makedirs(output_dir, exist_ok=True)

    streams_dir = "streams"
    os.makedirs(streams_dir, exist_ok=True)

    output_video = os.path.join(streams_dir, f"stream_capture_{timestamp}.mp4")
    timeout_seconds = args.timeout

    print(f"timeout: {timeout_seconds}s)")

    yt_dlp_cmd = [
        "yt-dlp",
        "--extractor-args",
        "youtube:player_client=default",
        "--live-from-start",
        "--download-sections",
        f"#-{int(args.duration * 3600)}s - 0",
        "--abort-on-error",
        "--fragment-retries",
        "2",
        "--socket-timeout",
        "5",
        "-o",
        output_video,
        args.url,
    ]

    try:
        process = subprocess.Popen(yt_dlp_cmd)
        process.wait(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        print(
            f"\nTimeout reached after {timeout_seconds}s, killing download process..."
        )
        process.kill()
        time.sleep(5)
    except KeyboardInterrupt:
        process.kill()
        time.sleep(5)

    part_files = [
        f
        for f in os.listdir(streams_dir)
        if f.startswith(f"stream_capture_{timestamp}") and f.endswith(".part")
    ]
    if part_files and not os.path.exists(output_video):
        part_file = os.path.join(streams_dir, part_files[0])
        print(f"Using partial download: {part_file}")
        os.rename(part_file, output_video)

    ffmpeg_cmd = [
        "ffmpeg",
        "-i",
        output_video,
        "-vf",
        f"select='not(mod(n\\,{args.nth}))'",
        "-vsync",
        "vfr",
        "-q:v",
        "2",
        f"{output_dir}/frame_%06d.jpg",
    ]

    _ = subprocess.run(ffmpeg_cmd)

    frame_count = len(
        [
            f
            for f in os.listdir(output_dir)
            if f.startswith("frame_") and f.endswith(".jpg")
        ]
    )
    print(f"{frame_count} frames saved")
    print(f"Video file saved as: {output_video}")


if __name__ == "__main__":
    main()
