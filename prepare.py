import tqdm
import cv2
import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import subprocess
from operator import itemgetter
from pathlib import Path
from itertools import product, count

from utils import get_filelist

ffmpeg_version = (
    subprocess.check_output("ffmpeg -version", shell=True)
    .decode("utf8")
    .splitlines()[0]
)

assert (
    "2.8.15" in ffmpeg_version
), "The author sugguests to use ffmpeg==2.8.15, delete this assertion to run on other ffmpeg versions."


def crop(frame, detection):
    w, h = detection["resolution"]
    if frame.shape[:2] != (h, w):
        raise ValueError(f"Expect frame size to be ({h}, {w}), got {frame.shape[:2]}.")
    y1, y2, x1, x2 = itemgetter("y1", "y2", "x1", "x2")(detection)
    y1, y2 = map(lambda y: int(y * h), [y1, y2])
    x1, x2 = map(lambda x: int(x * w), [x1, x2])
    return frame[y1:y2, x1:x2]


def out_dir(mp4, mkdir=False):
    path = Path(str(mp4.with_suffix("")).replace("intervals", "preprocessed"))
    if mkdir:
        path.mkdir(parents=True, exist_ok=True)
    return path


def prepare_video(mp4, detection):
    if out_dir(mp4).exists():
        # skip crop jpgs if this have been done by detect.py
        return
    detection = detection.set_index("frame_id").to_dict("index")
    cap = cv2.VideoCapture(str(mp4))
    for frame_id in count():
        running, frame = cap.read()
        if not running:
            break
        if frame_id in detection:
            face = crop(frame, detection[frame_id])
            cv2.imwrite(str(out_dir(mp4, mkdir=True) / f"{frame_id}.jpg"), face)


def prepare_audio(mp4, sample_rate):
    template = "ffmpeg -loglevel panic -y -i {} -ar {} -f wav {}"
    template2 = "ffmpeg -hide_banner -loglevel panic -threads 1 -y -i {} -async 1 -ac 1 -vn -acodec pcm_s16le -ar 16000 {}"

    wavpath = out_dir(mp4, mkdir=True) / "audio.wav"
    speaker = wavpath.parts[-5]
    if speaker in ["hs", "eh", "dl"]:
        command = template2.format(mp4, wavpath)
    else:
        command = template.format(mp4, sample_rate, wavpath)
    subprocess.call(command, shell=True)


def prepare(detection, args):
    df = pd.read_csv(detection)
    df["resolution"] = df["resolution"].apply(eval)

    mp4s = get_filelist(
        args.root,
        *detection.stem.split("-"),
        "intervals/{youtube_id}/**/*.mp4",
    )
    mp4s = [p for p in mp4s if not (out_dir(p) / "audio.wav").exists()]

    grouped_detection = dict(list(df.groupby(["youtube_id", "cut"])))

    for mp4 in mp4s:
        youtube_id = mp4.parts[-2]
        cut = int(mp4.stem.split("-")[-1])
        index = (youtube_id, cut)
        if index not in grouped_detection:
            print(f"==> INFO: No face detected in {mp4}, skipped.")
            continue
        prepare_video(mp4, grouped_detection[index])
        prepare_audio(mp4, args.sample_rate)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("detections", type=Path, nargs="+")
    parser.add_argument("--root", type=Path, default="Dataset")
    parser.add_argument("--sample-rate", type=int, default=16000)
    args = parser.parse_args()
    for detection in tqdm.tqdm(args.detections):
        prepare(detection, args)


if __name__ == "__main__":
    main()
