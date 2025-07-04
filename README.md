![resomapper](docs/_static/logo_fixed_white.svg)

[![PyPI version](https://img.shields.io/pypi/v/resomapper?color=blue)](https://pypi.python.org/pypi/resomapper)
[![Documentation Status](https://readthedocs.org/projects/resomapper/badge/?version=latest)](https://resomapper.readthedocs.io/en/latest/?badge=latest)
[![License: MIT](https://img.shields.io/badge/license-MIT-orange)](https://opensource.org/licenses/MIT)

Welcome to `resomapper`, a pipeline for processing MR images and generating parametric maps. 

This tool is designed and developed by the *Biomedical Magnetic Resonance Lab* at the *Instituto de Investigaciones Biomédicas "Alberto Sols"* (CSIC-UAM). This project aims to collect a series of MR image processing tools written in Python under a friendly user interface for the lab needs. It is designed to streamline the processing of images, starting from raw adquisition files (we use Bruker study folders) to end up with parametric maps such as T1, T2 or T2* maps, as well as diffusion metric maps derived from DTI analysis.

Note that `resomapper` is a tool under active development, with new features and improvements still on the way. It is used in-house for preclinical MRI data, mainly for mouse brain imaging, but can be used for different types of MRI data. Any suggestions are welcome!

For more info, visit the [whole documentation](https://resomapper.readthedocs.io/en/latest).

### DISCLAIMER: right now, this is a beta version of Resomapper. Soon, on summer 2025, the complete version with more functionalities will be available. Stay tuned!!!

## Installation

To install **resomapper**, follow these steps:

1. Make sure that you have Python installed on your system. Versions supported are **3.8** and above. 

    * *Optional: create a virtual environment with conda or venv.*

2. Install **resommaper** and all its dependencies running the following command from your terminal:

    ```
    pip install resomapper
    ```

3. If you have already been using **resomapper** and there is any new version available, you can use the following command to update it:

    ```
    pip install resomapper --upgrade
    ```

## Usage

Then, to start using **resomapper**, you'll need to follow these steps:

1. Prepare a working directory (an empty folder located wherever you want) and store inside the studies you want to process as folders in *Bruker* raw format.

2. Enter the command shown below to run the program's Command Line Interface. 

    ```
    resomapper_cli
    ```

3. Follow the instructions shown in the terminal.

4. Finally, retrieve all the resulting maps and files obtained after processing from the same working folder you selected at the start of the program.


## Contributing

Interested in contributing? Check out the contributing guidelines. Please note that this project is released with a Code of Conduct. By contributing to this project, you agree to abide by its terms.

## License

`resomapper` was created by Biomedical-MR. It is licensed under the terms of the MIT license.

