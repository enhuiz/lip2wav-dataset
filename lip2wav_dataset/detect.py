import tqdm
import torch
import numpy as np
import pandas as pd
import argparse, os, cv2, subprocess
import torch.nn.functional as F
import threading
from queue import Queue
from torch.utils.data import Dataset
from pathlib import Path
from functools import partial
from itertools import product
from more_itertools import chunked
from efd import s3fd

from .utils import create_parser, get_filelist


def crop_frames(frames, speaker):
    """
    frames: (b h w c)
    """
    if speaker == "chem" or speaker == "hs":
        return frames
    elif speaker == "chess":
        return frames[:, 270:460, 770:1130]
    elif speaker == "dl" or speaker == "eh":
        return frames[:, int(frames.shape[1] * 3 / 4) :, int(frames.shape[2] * 3 / 4) :]
    else:
        raise ValueError("Unknown speaker!")


def compute_relative_bbox(bbox, size, speaker):
    """Bounding box relative to the full frame size

    x for width and y for height

    (y1, x1)
        *-------
        |      |
        |      |
        -------* (y2, x2)

    """
    if speaker == "chess":
        bbox["y1"] += 270
        bbox["y2"] += 270
        bbox["x1"] += 770
        bbox["x2"] += 770
    elif speaker == "dl" or speaker == "eh":
        bbox["y1"] += int(size[0] * 3 / 4)
        bbox["y2"] += int(size[0] * 3 / 4)
        bbox["x1"] += int(size[1] * 3 / 4)
        bbox["x2"] += int(size[1] * 3 / 4)
    bbox["y1"] /= size[0]
    bbox["y2"] /= size[0]
    bbox["x1"] /= size[1]
    bbox["x2"] /= size[1]
    return bbox


def out_dir(mp4, mkdir=False):
    path = Path(str(mp4.with_suffix("")).replace("intervals", "preprocessed"))
    if mkdir:
        path.mkdir(parents=True, exist_ok=True)
    return path


class VideoFrameLoader(threading.Thread):
    """
    This loader prefetches frames, faster than only calling cap.read() when needed.
    """

    def __init__(self, path, batch_size, prefetch=128):
        super().__init__()
        cap = cv2.VideoCapture(str(path))
        self.height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.cap = cap
        self.batch_size = batch_size
        self.queue = Queue(prefetch)
        self.daemon = True
        self.start()

    @property
    def frame_size(self):
        return (self.height, self.width)

    def run(self):
        while True:
            success, frame = self.cap.read()
            if not success:
                break
            self.queue.put(frame)
        self.queue.put(None)

    def frame_iter(self):
        while True:
            ret = self.queue.get()
            if ret is None:
                break
            yield ret

    def __iter__(self):
        return chunked(self.frame_iter(), self.batch_size)


def detect(model, mp4, args):
    if (out_dir(mp4) / "detection.csv").exists():
        # this video been processed by other running process
        return

    speaker = mp4.relative_to(args.root).parts[0]

    data_loader = VideoFrameLoader(mp4, args.batch_size)

    bboxes = []

    frame_id = -1
    for images in tqdm.tqdm(data_loader, desc=f"Detecting {mp4}"):
        images = torch.from_numpy(np.stack(images)).to(args.device)
        images = crop_frames(images, speaker)  # pre-crop
        images = images[..., [2, 1, 0]]  # bgr to rgb
        images = (images / 255.0).permute(0, 3, 1, 2)  # numpy int8 to tensor float32
        bbox_lists, patch_iters = model.detect(images, args.scale_factor)
        for bbox_list, patch_iter in zip(bbox_lists, patch_iters):
            frame_id += 1
            try:
                face = next(patch_iter)
                bbox = next(bbox_list.iterrows())[1]
                bbox = compute_relative_bbox(bbox, data_loader.frame_size, speaker)
                bbox["frame_id"] = frame_id
                bboxes.append(bbox)
                face = face * 255.0
                face = face.permute(1, 2, 0).cpu().numpy()
                face = face[..., [2, 1, 0]]  # rgb to bgr
                cv2.imwrite(str(out_dir(mp4, True) / f"{frame_id}.jpg"), face)
            except StopIteration:
                pass

    if bboxes:
        df = pd.DataFrame(bboxes)
        df["frame_id"] = df["frame_id"].astype(int)
        del df["score"]
    else:
        # nothing is detected, create an empty csv
        df = pd.DataFrame()

    df.to_csv(
        out_dir(mp4, True) / "detection.csv",
        index=None,
        float_format="%.4f",
    )


def main():
    parser = create_parser()
    parser.add_argument(
        "--batch_size",
        default=16,
        type=int,
    )
    parser.add_argument(
        "--scale_factor",
        help="Resize the frames before face detection",
        default=0.5,
        type=float,
    )
    parser.add_argument(
        "--device",
        default="cuda",
    )

    args = parser.parse_args()
    model = s3fd(pretrained=True).to(args.device)

    filelist = []
    for speaker, split in product(args.speakers, args.splits):
        filelist.extend(
            get_filelist(
                args.root,
                speaker,
                split,
                "intervals/{youtube_id}/**/*.mp4",
            )
        )
    filelist = [p for p in filelist if not (out_dir(p) / "detection.csv").exists()]

    # shuffle the list to allow concurrent processes running in different order
    np.random.shuffle(filelist)

    for mp4 in tqdm.tqdm(filelist):
        detect(model, mp4, args)


if __name__ == "__main__":
    main()
