# Unofficial Lip2Wav Dataset Preprocessing Scripts

[Lip2Wav](https://github.com/Rudrabha/Lip2Wav/) dataset is a large scale dataset for lip-to-speech synthesis.

These scripts allow to only download and preprocess parts of the dataset, and runs faster. For example, to run only test for dl, you may simply specify `--splits test --speakers dl` for all the following steps.

## Installation

```
pip install git+https://github.com/enhuiz/lip2wav-dataset.git
```

## Steps

### 1. Download raw videos from YouTube

Under any empty folder, run the following command:

```
lip2wav-dataset download --splits test --speakers dl
```

This step automatically download the given speaker and split (i.e. train/val/test). If not specified, all speakers/splits will be downloaded. This script support automatically downloading by default.

### 2. Split raw videos into intervals

```
lip2wav-dataset cut
```

This will the videos into intervals.

### 3. Detect faces (optional)

Note that if you have downloaded the detection files, this step can be skipped.

```
lip2wav-datsaet detect --splits test --speakers dl
```

Detect faces from the intervals, generate the cropped frames to the folder under `Dataset/preprocessed` and also a `detection.csv` in the same folder.

```
lip2wav-dataset collect --splits test --speakers dl
```

This will merge all the `detection.csv` for each speaker/split to `detection/speaker-split.csv`.

### 4. Prepare

```
lip2wav-dataset prepare detection/dl-test.csv
```

This generate frames (if step 3 is skipped), audios and spectrograms.

## Detections

The detection results for test set can be downloaded [here](https://github.com/Rudrabha/Lip2Wav/files/5815157/detection.zip).

## Credits

- The original project of [Lip2Wav](https://github.com/Rudrabha/Lip2Wav/)
