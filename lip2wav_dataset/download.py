import pkg_resources
import shutil
import numpy as np
import soundfile
import librosa
import os
import tqdm
import subprocess
import sys
from itertools import product
from pathlib import Path

from .utils import working_directory, create_parser


def get_todo_list(split):
    video_dir = Path("videos")
    done = set([path.stem for path in video_dir.glob("*.mp4")])
    with open(f"{split}.txt", "r") as f:
        target = set(f.read().strip().splitlines())
    todo = target - done
    return list(todo)


def download(todo):
    video_dir = Path("videos")
    video_dir.mkdir(exist_ok=True)
    with open("todo.txt", "w") as f:
        f.write("\n".join(sorted(todo)))
    args = ["youtube-dl", "-f", "best", "-a", "todo.txt", "-o", "videos/%(id)s.%(ext)s"]
    try:
        subprocess.check_call(args)
        os.remove("todo.txt")
    except Exception as e:
        print(e)


def create_datalist(root, speaker, split):
    tgt = (root / speaker / split).with_suffix(".txt")
    if not tgt.exists():
        tgt.parent.mkdir(parents=True, exist_ok=True)
        src = pkg_resources.resource_filename(__name__, f"data/{speaker}/{split}.txt")
        shutil.copy(src, tgt)


def main():
    parser = create_parser()
    args = parser.parse_args()

    pairs = sorted(product(args.speakers, args.splits))
    np.random.shuffle(pairs)
    pbar = tqdm.tqdm(pairs)

    for speaker, split in pbar:
        create_datalist(args.root, speaker, split)
        with working_directory(args.root / speaker, mkdir=True):
            todo = get_todo_list(split)
            if todo:
                print(f"==> Downloading {speaker}/{split} ...")
                np.random.shuffle(todo)
                download(todo)
            else:
                print(f"==> {speaker}/{split} is completed.")


if __name__ == "__main__":
    main()
