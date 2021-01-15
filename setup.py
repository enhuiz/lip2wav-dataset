from setuptools import setup

with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name="lip2wav_dataset",
    python_requires=">=3.6.0",
    version="0.0.1.dev0",
    author="enhuiz",
    author_email="niuzhe.nz@outlook.com",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=["lip2wav_dataset"],
    scripts=["lip2wav-dataset"],
    install_requires=[
        "efd @ git+https://github.com/enhuiz/efd",
        "tqdm",
        "pandas",
        "numpy",
    ],
    url="https://github.com/enhuiz/lip2wav_dataset",
    package_data={"lip2wav_dataset": ["data/**/*.txt"]},
)
