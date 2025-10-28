![resomapper](docs/_static/resomapper_logo_color.svg)

[![PyPI version](https://img.shields.io/pypi/v/resomapper?color=blue)](https://pypi.python.org/pypi/resomapper)
[![Documentation Status](https://readthedocs.org/projects/resomapper/badge/?version=latest)](https://resomapper.readthedocs.io/en/latest/?badge=latest)
[![License: MIT](https://img.shields.io/badge/license-MIT-orange)](https://opensource.org/licenses/MIT)

Resomapper is an open-source, cross-platform Python tool designed to simplify quantitative MRI (qMRI) processing. It integrates established processing libraries into a unified and user-friendly workflow, supporting T1, T2, T2*, MTI, and DTI analyses, along with advanced preprocessing steps such as denoising, Gibbs artifact removal, and bias field correction. Users can run analyses interactively through an user-friendly interface, or through automated JSON-based configurations, ensuring compatibility by converting raw MRI data into the standardized NIfTI format within a BIDS-like structure. Resomapper promotes accessibility, reproducibility, and efficient data management in qMRI research and applications.

This software was developed to address the specific needs our lab encountered when processing preclinical MRI data. We hope it will also be valuable to other researchers facing similar challenges by bringing together tools for multiple MRI modalities in a single, user-friendly platform. Designed especially for those without coding experience, Resomapper simplifies advanced qMRI processing through an intuitive workflow.

Please note that Resomapper is an actively developed project, with ongoing improvements and new features being added regularly. It is currently used in-house for preclinical MRI studies—primarily mouse brain imaging—but is adaptable to various types of MRI data. We welcome feedback, suggestions, and contributions from the community to help make it even better.

Here is a brief overview of Resomapper’s installation and usage, though we recommend visiting the [full documentation](https://resomapper.readthedocs.io/en/latest) for detailed instructions and additional information.

## Installation

To install Resomapper, follow these steps:

1. Make sure that you have Python installed on your system. Versions supported are **3.8** and above. 

    * *Optional: create a virtual environment with conda or venv.*

2. Install Resommaper and all its dependencies running the following command from your terminal:

    ```
    pip install resomapper
    ```

3. If you have already been using the software and there is any new version available, you can use the following command to update it:

    ```
    pip install resomapper --upgrade
    ```

## Usage

Then, to start using Resomapper, you'll need to follow these steps:

1. Prepare a working directory (an empty folder located wherever you want) and store inside the studies you want to process.

2. Enter the command shown below to run the program's Command Line Interface. 

    ```
    resomapper_cli
    ```

3. Follow the instructions shown in the terminal.

4. Finally, retrieve all the resulting maps and files obtained after processing from the same working folder you selected at the start of the program.


## Contributing

Interested in contributing? Check out the contributing guidelines. Please note that this project is released with a Code of Conduct. By contributing to this project, you agree to abide by its terms.

## License

Resomapper was created by the *Preclinical neuroImaging Lab* at the *Instituto de Investigaciones Biomédicas Sols-Morreale* (CSIC-UAM), in Madrid. It is licensed under the terms of the MIT license.

