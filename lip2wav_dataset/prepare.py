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

from .utils import get_filelist


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


def prepare_audio(mp4, args):
    template = "ffmpeg -loglevel panic -y -i {} -ar {} -f wav {}"
    template2 = "ffmpeg -hide_banner -loglevel panic -threads 1 -y -i {} -async 1 -ac 1 -vn -acodec pcm_s16le -ar 16000 {}"

    wavpath = out_dir(mp4, mkdir=True) / "audio.wav"
    speaker = wavpath.parts[-5]
    if speaker in ["hs", "eh", "dl"]:
        command = template2.format(mp4, wavpath)
    else:
        command = template.format(mp4, args.sample_rate, wavpath)
    subprocess.call(command, shell=True)

    if not args.no_spec:
        try:
            load_wav
        except:
            from .audio import load_wav, melspectrogram, linearspectrogram

        wav = load_wav(wavpath, args.sample_rate)
        spec = melspectrogram(wav, args)
        lspec = linearspectrogram(wav, args)
        np.savez_compressed(wavpath.with_name("mels.npz"), spec=spec, lspec=lspec)


def prepare(detection, args):
    try:
        df = pd.read_csv(detection)
    except Exception as e:
        print(str(e) + " Skipped.")
        return
    df["resolution"] = df["resolution"].apply(eval)

    mp4s = get_filelist(
        args.root,
        *detection.stem.split("-"),
        "intervals/{youtube_id}/**/*.mp4",
    )

    youtube_ids = set(df["youtube_id"])

    mp4s = list(
        filter(
            lambda p: not (out_dir(p) / "audio.wav").exists()
            and p.parent.name in youtube_ids,
            mp4s,
        )
    )

    grouped = dict(list(df.groupby(["youtube_id", "cut"])))

    for mp4 in mp4s:
        youtube_id = mp4.parts[-2]
        cut = int(mp4.stem.split("-")[-1])
        index = (youtube_id, cut)
        if index not in grouped:
            print(f"==> INFO: No face detected in {mp4}, skipped.")
            continue
        prepare_video(mp4, grouped[index])
        prepare_audio(mp4, args)


def str2bool(s):
    s = str(s).lower()
    assert s in ["true", "false"]
    return s == "true"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("detections", type=Path, nargs="+")
    parser.add_argument("--root", type=Path, default="Dataset")
    parser.add_argument("--sample_rate", type=int, default=16000)
    # spec
    parser.add_argument("--no-spec", action="store_true")
    parser.add_argument("--preemphasize", type=str2bool, default=True)
    parser.add_argument("--preemphasis", type=float, default=0.97)
    parser.add_argument("--hop_size", type=float, default=200)
    parser.add_argument("--win_size", type=float, default=800)
    parser.add_argument("--n_fft", type=float, default=800)
    parser.add_argument("--fmax", type=int, default=7600)
    parser.add_argument("--fmin", type=int, default=55)
    parser.add_argument("--num_mels", type=int, default=80)
    parser.add_argument("--signal_normalization", type=str2bool, default=True)
    parser.add_argument("--min_level_db", type=int, default=-100)
    parser.add_argument("--ref_level_db", type=int, default=20)
    parser.add_argument("--max_abs_value", type=float, default=4.0)
    parser.add_argument("--use_lws", type=str2bool, default=False)
    parser.add_argument("--symmetric_mels", type=str2bool, default=True)
    parser.add_argument(
        "--allow_clipping_in_normalization",
        type=str2bool,
        default=True,
    )
    args = parser.parse_args()

    print(args)

    ffmpeg_version = (
        subprocess.check_output("ffmpeg -version", shell=True)
        .decode("utf8")
        .splitlines()[0]
    )

    if "2.8.15" not in ffmpeg_version:
        msg = f"The author sugguests to use ffmpeg==2.8.15, but got: \n{ffmpeg_version}.\nDo you want to continue? (y/n) "
        if input(msg).lower() != "y":
            print("Quiting ...")
            exit()

    for detection in tqdm.tqdm(args.detections):
        prepare(detection, args)


if __name__ == "__main__":
    main()
