# Unofficial Lip2Wav Dataset Preprocessing Scripts

These scripts allow to only download and preprocess parts of the dataset, and runs faster. For example, to run only test for dl, you may simply specify `--splits test --speakers dl` for all the following steps.

## Steps

### 1. Download raw videos from YouTube

This step automatically download the given speaker and split (i.e. train/val/test). If not specified, all speakers/splits will be downloaded. This script support automatically downloading by default.

```
python download.py --splits <splits> --speakers <speakers>
```

### 2. Split raw videos into intervals

```
./cut.sh Dataset
```

This will the videos into intervals.

### 3. Detect faces (optional)

Note that if you have downloaded the detection files, this step can be skipped.

```
python3 detect.py --splits <splits> --speakers <speakers>
```

Detect faces from the intervals, generate the cropped frames to the folder under `Dataset/preprocessed` and also a `detection.csv` in the same folder.

```
python3 collect.py --splits <splits> --speakers <speakers>
```

This will merge all the `detection.csv` for each speaker/split to `detection/speaker-split.csv`.

### 4. Prepare

```
python prepare.py detection/chem-test.csv
```

This generate frames (if step 3 is skipped) and audios.

## TODOs

- [ ] generate spectrograms for training.
