import argparse
import contextlib
import os
import threading
from queue import Queue
from pathlib import Path


@contextlib.contextmanager
def working_directory(new, mkdir=False):
    old = os.getcwd()
    try:
        if not new.exists() and mkdir:
            Path(new).mkdir(parents=True, exist_ok=True)
        os.chdir(new)
        yield
    finally:
        os.chdir(old)


def create_parser(speaker=True, split=True):
    speakers = ["chem", "chess", "dl", "eh", "hs"]
    splits = ["train", "val", "test"]
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default="Dataset")
    if speaker:
        parser.add_argument("--speakers", choices=speakers, nargs="+", default=speakers)
    if split:
        parser.add_argument("--splits", choices=splits, nargs="+", default=splits)
    return parser


def get_filelist(root, speaker, split, pattern):
    path = (root / speaker / split).with_suffix(".txt")
    with open(path, "r") as f:
        youtube_ids = f.read().splitlines()
    dirpath = root / speaker
    for youtube_id in youtube_ids:
        yield from dirpath.glob(pattern.format(youtube_id=youtube_id))
