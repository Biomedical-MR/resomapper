# First steps

This section covers the first steps in order to be able to run **resomapper**: the installation and the preparation of the working directory and some considerations about the studies to process.

---

(installation)=
## Installation

First of all, please make sure to have **Python 3.8 or higher** installed as well as pip.  Check out the section {ref}`requirements` if you need more information on this matter. 

Although optional, it is good practice to use virtual environments to avoid conflicts with other package versions that you have installed for other uses. If you want to know more about this, check out the section {ref}`venv`.

To install resomapper, you can simply install it via `pip`. To do so, just open a terminal window (if you are using Windows, you can search for the word "cmd" on the explorer) and run the following command:

```
> pip install resomapper
```

Then wait for the installation of all the required packages and you will be ready to go! You can check if everything is correct by running the command of the resomapper CLI (see {ref}`cli_run`).

### Updates

To update to a new version of resomapper when available, run the following command:

```
> pip install resomapper --upgrade
```

---

(requirements)=
## System requirements

Resomapper can be used both in Windows and Unix systems (macOS/Linux). Currently the testing of the program in our lab is being done primarily on Windows, however, there should not be major problems on other operating systems as long as they are reasonably up to date.

Resomapper is based on **Python**, so make sure to have it properly installed. To do so, download the desired version installer for your system from [Python's official site](https://www.python.org/downloads/) and follow the installation process.

This program works with versions of Python 3.8 and avobe. Some older versions might work too, however, we recommend to stick to these recommendations as we have not checked for problems on previous version. If you want to be completely sure, we have tested resomapper in Python **3.8.5**, **3.8.16** and **3.10.0** versions.

You will also need **pip** to install this program, but don't worry about this, because it already comes with your Python installation.

You can check if both Python and pip are correctly installed by running the following commands from the terminal, that should output the name of the version you have installed:

```
> python --version
```

```
> pip --version
```

Any other packages required by resomapper should be installed automatically when you run the pip installation. 

```{warning}
Python versions installed from the Windows store can have some problems with resommaper. We recommend to install Python from [Python's official site](https://www.python.org/downloads/).
```

---

(venv)=
## Using a virtual environment

You can install **resomapper** and all its dependencies directly on your base Python installation. However, it is good practice to use virtual environments to isolate your packages so that they do not conflict with other versions, among other reasons.

In this section two ways of setting up and using a virtual environment are described: Python's `venv` module and through a `conda` installation. 

```{note}
Remember that if you install **resomapper** in a virtual environment, you'll have to activate it before or resomapper will not be available for use.
```

### Using *venv*

With your Python installation, by default, you'll have access to the venv module, which supports the creation of lightweight virtual environments. The files of these virtual environments need to be stored in a directory of your choice. The command to create a new virtual environment is the following:

```
> python -m venv /path/to/new/virtual/environment
```

Then, to activate the virtual environment, you'll need to run the following comand from the terminal, being on the directory you created the virtual environment in:

* *Unix/macOS:*
```
> source env/bin/activate
```
* *Windows:*
```
> .\env\Scripts\activate
```

See the [full guide](https://packaging.python.org/en/latest/guides/installing-using-pip-and-virtual-environments/#creating-a-virtual-environment) and [Python's venv docs](https://docs.python.org/3/library/venv.html) for more information.


### Using *conda*

To use conda, you will need to install it first. You can use either [miniconda](https://docs.conda.io/en/latest/miniconda.html) or the full [anaconda](https://www.anaconda.com/download/) installer. Miniconda is a lightweight version of conda that has all the features you will need for this use.

Either way, to create a virtual environment with conda, you'll need to enter the following command in the terminal (resomapper will be the name of the environment we will create, but you can use any other name):

```
> conda create --name resomapper
```

You can also specify the Python version you want to use for the virtual environment (if not specified, as before, it will use the default Python version of your conda installation):

```
> conda create --name resomapper python=3.8
```

In either case, answer yes when conda asks you to proceed. After creating the environment, whenever you want to use it, you will have to enter the comand:

```
> conda activate resomapper
```

And to exit the virtual environment:

```
> conda deactivate
```

Go to the [official conda documentation](https://docs.conda.io/projects/conda/en/stable/user-guide/tasks/manage-environments.html) for the full information.

---

(prepare_studies)=
## Preparing the studies

Once you have resomapper correctly installed, it is time to prepare the working directory and the studies you want to process. 

The working directory is a folder where all the studies you want to process must be stored. This folder can be located anywhere, but it is preferable that it is easily accessible for you. 

The studies must be in **Bruker raw format** (not DICOM or others). This means that they will have a similar structure to the one shown in the figure below.

```{figure} static/bruker_folder.png
---
width: 400px
name: bruker_folder
align: center
---
Example of Bruker study folder.
```

Make sure that the studies are stored directly at the working directory, in separate folders, as shown below. Each study corresponds to a patient (mouse, human...) and contains the folders of the different sequences adquired.

```
└── work_folder 
    │
    ├── study_1
    │   └── Adquisition folders (1, 2, 3, 4...) and other files
    │
    ├── study_2
    │   └── Adquisition folders (1, 2, 3, 4...) and other files
    ...
```

In addition, the following folders will be automatically generated during the CLI program execution (see {ref}`output_files` section for more info on this):

* **"Convertidos" folder:** will contain the original studies converted to NIfTI format. The subfolders of a study with possible interest for processing will have a prefix to better identify them (DT, MT, T1, T2 or T2E).
* **"Procesados" folder:** will contain the results of processing. Within each study there will be a subfolder with the results for each processed modality. What each file consists of in these folders according to the modality will be specified later.
* **"supplfiles" folder:** it is generated to save temporary files during the execution. It is not necessary to do anything with it and can be deleted.

```{note}
It is advisable to empty the working directory and save the files of interest before processing new studies. This will help to avoid confusing files and making mistakes. You can also have several work folders.
```
