![resomapper](docs/static/logo.svg)
Welcome to the documentation of **resomapper**, a pipeline for processing MR images and generating parametric maps. 

This tool is designed and developed by the ***Biomedical Magnetic Resonance Lab*** at the *Instituto de Investigaciones Biomédicas "Alberto Sols" (CSIC-UAM)*, and aims to collect a series of MR image processing tools written in Python under a friendly user interface for the lab needs. It is designed to streamline the processing of images, starting from raw adquisition files (we use Bruker study folders) to end up with parametric maps such as T1, T2 or T2* maps, as well as diffusion metric maps derived from DTI analysis.

```{note}
**Resomapper** is a tool under active development, with new features and improvements still on the way. It is used in-house for preclinical MRI data, mainly for mouse brain imaging, but can be used for different types of MRI data. Any suggestions are welcome!
```

(overview_resomapper)=
## Overview: how to install and use **resomapper**

To install **resomapper**, follow these steps:

1. Make sure that you have Python installed on your system. Versions supported are **3.8** and above (more info [here](requirements)). 

* *Optional: create a virtual environment (more info [here](venv)).*

2. Install **resommaper** and all its dependencies running the following command from your terminal:

    ```
    > pip install resomapper
    ```

3. If you have already been using **resomapper** and there is any new version available, you can use the following command to update it:

    ```
    > pip install resomapper --upgrade
    ```

Then, to start using **resomapper**, you'll need to follow these steps:

1. Prepare a working directory (an empty folder located wherever you want) and store inside the studies you want to process as folders in *Bruker* raw format (more info [here](prepare_studies)).

2. Enter the command shown below to run the program. 

    ```
    > resomapper_cli
    ```

3. Follow the instructions shown in the terminal (read the whole manual [here](cli_run) for info on the whole workflow).

4. Finally, retrieve all the resulting maps and files obtained after processing from the same working folder ([here](output_files) you can find more information on what is each file and its location).

% Overview: main page also in toctree
%```{toctree}
%:maxdepth: 1
%:hidden:

%self
%```

```{toctree}
:maxdepth: 1
:hidden:
:caption: User's guide

first_steps.md
handbook.md
output_files.md
```

```{toctree}
:maxdepth: 1
:hidden:
:caption: More info

autoapi/index
changelog.md
contributing.md
conduct.md
credits.md
example.ipynb
```