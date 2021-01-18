# Unofficial Lip2Wav Dataset Preprocessing Scripts

[Lip2Wav](https://github.com/Rudrabha/Lip2Wav/) dataset is a large scale lip-to-speech synthesis dataset. This script allows to download and preprocess parts of the dataset, and runs faster. For example, to run only test for dl, you may simply specify `--splits test --speakers dl` for all the following steps.

## Requirements

This script requires `ffmpeg` and has been tested on Ubuntu 20.04.1 LTS.

## Installation

```
pip install git+https://github.com/enhuiz/lip2wav-dataset.git
```

## Steps

### 1. Download raw videos from YouTube

Under an empty folder, run the following command:

```
lip2wav-dataset download --splits test --speakers dl
```

This step automatically download the specified speaker and split (i.e. train/val/test). If not specified, all speakers/splits will be downloaded.

### 2. Cut raw videos into intervals

```
lip2wav-dataset cut ./Dataset
```

This cuts the all existing videos into intervals, no need to specify speakers and splits.

### 3. Detect faces (optional)

Note that if you have downloaded the detection files, this step can be skipped.

```
lip2wav-dataset detect --splits test --speakers dl
```

Detect faces from the intervals, generate the cropped frames to the folder under `Dataset/preprocessed` and also a `detection.csv` in the same folder.

```
lip2wav-dataset collect --splits test --speakers dl
```

The collection command merges all the `detection.csv` for each speaker/split to `detection/{speaker}-{split}.csv`, which you can share with other people.

### 4. Prepare the rest

```
lip2wav-dataset prepare detection/dl-test.csv
```

This command generates frames (if step 3 is skipped), audios and spectrograms. Testing does not requires spectrograms, specify the `--no-spec` flag to skip spectrogram for faster preparation:

```
lip2wav-dataset prepare detection/dl-test.csv --no-spec
```

## Detections

The results of detection for the test sets can be downloaded [here](https://github.com/Rudrabha/Lip2Wav/files/5815157/detection.zip).

## Credits

- The original repo of [Lip2Wav](https://github.com/Rudrabha/Lip2Wav/).
