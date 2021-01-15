import tqdm
import cv2
import sys
import pandas as pd
from itertools import product
from collections import defaultdict
from pathlib import Path

from .utils import create_parser, get_filelist


def get_resolution(path):
    cap = cv2.VideoCapture(str(path))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    return (width, height)


def get_resolution_df(root, speaker, split):
    rows = []
    paths = list(
        get_filelist(
            root,
            speaker,
            split,
            "videos/**/{youtube_id}.mp4",
        )
    )
    for path in paths:
        rows.append(
            {
                "youtube_id": path.stem,
                "resolution": get_resolution(path),
            }
        )
    return pd.DataFrame(rows)


def get_detection_df(root, speaker, split):
    dfs = []
    paths = list(
        get_filelist(
            root,
            speaker,
            split,
            "preprocessed/{youtube_id}/**/*.csv",
        )
    )
    for path in paths:
        try:
            df = pd.read_csv(path)
        except Exception as e:
            continue
        df["youtube_id"] = path.parts[-3]
        df["cut"] = path.parts[-2].replace("cut-", "")
        dfs.append(df)
    if not dfs:
        raise FileNotFoundError(f"No detection is found for {speaker}/{split}.")
    df = pd.concat(dfs).reset_index(drop=True)
    return df


def main():
    parser = create_parser()
    args = parser.parse_args()
    pbar = tqdm.tqdm(list(product(args.speakers, args.splits)))
    for speaker, split in pbar:
        pbar.set_description_str(f"Collecting {speaker}/{split} ...")
        try:
            bdf = get_detection_df(args.root, speaker, split)
        except FileNotFoundError as e:
            print(f"{e} Skipped.")
            continue
        rdf = get_resolution_df(args.root, speaker, split)
        df = pd.merge(bdf, rdf, on="youtube_id")
        path = Path(f"detection/{speaker}-{split}.csv")
        path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(path, index=None)


if __name__ == "__main__":
    main()
