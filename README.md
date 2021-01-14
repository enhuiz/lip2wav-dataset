# Unofficial Lip2Wav Dataset Preprocessing Scripts

These scripts allow to only download and preprocess parts of the dataset, and runs faster.

For example, run only test for dl, you may simply specify `--splits test --speakers dl` for all the following steps.

## Steps

### 1. Download

```
python download.py --splits <splits> --speakers <speakers>
```

The download script will automatically download the given speaker and split (i.e. train/val/test), if not specified, all speakers/splits will be downloaded. This script support automatically downloading by default.

### 2. Split

```
./cut.sh Dataset
```

This cuts the videos into intervals.

### 3. Detect and Collect (Optional)

Note that if you have downloaded the detection files, this step is optional.

```
python3 detect.py --splits <splits> --speakers <speakers>
```

Detect faces from the intervals, generate the cropped frames to the folder under `Dataset/preprocessed` and also generate a `detection.csv` in the same folder.

```
python3 collect.py --splits <splits> --speakers <speakers>
```

This collect the detections for each speaker/split and generate the detection files.

### 4. Prepare

```
python prepare.py detection/chem-test.csv
```

This generate frames (if step 3 is skipped) and audios.
