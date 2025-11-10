# First steps

This section covers the first steps in order to be able to run Resomapper: the installation and the preparation of the working directory and some considerations about the studies to process.

---

(installation)=
## Installation

Resomapper can be used both in Windows and Unix systems (macOS/Linux). As this software is based on Python, the first step is to install it if you haven’t used before. We recommend Python 3.10 or 3.11, but other versions could work too.

To do so, you can download the desired version installer for your system from [Python's official site](https://www.python.org/downloads/) and follow the installation process. Although optional, it is good practice to use virtual environments to avoid conflicts with other package versions that you have installed for other uses. If you want to know more about this, check out the section {ref}`venv`. If you decide to use conda to manage your virtual environment, you don’t need to install Python from the oficial site, instead you can follow the instructions of said section. 

You can check if both Python and pip are correctly installed by running the following commands from the terminal, that should output the name of the version you have installed:
```
> python --version
```
```
> pip --version
```
Any other packages required by resomapper should be installed automatically when you run the pip installation.

```{warning}
Python versions installed from the Windows store can have some problems with Resommaper. We recommend to install Python from [Python's official site](https://www.python.org/downloads/), or using conda.
```

Once you have Python set up, to install resomapper, you can simply do it via pip. To do so, just open a terminal window (if you are using Windows, you can search for the word “cmd” on the explorer) and run the following command:

```
> pip install resomapper
```

```{note}
Remember to activate your virtual environment before, if you are using one!
```

Then wait for the installation of all the required packages and you will be ready to go! You can check if everything is correct by running the command of the resomapper CLI (see {ref}`cli_run`).

### Updates

To update to a new version of resomapper when available, run the following command:

```
> pip install resomapper --upgrade
```

---

(venv)=
## Using a virtual environment

You can install **resomapper** and all its dependencies directly on your base Python installation. However, it is good practice to use virtual environments to isolate your packages so that they do not conflict with other versions, among other reasons.

In this section two ways of setting up and using a virtual environment are described: Python's `venv` module and through a `conda` installation. 

```{note}
Remember that if you install **resomapper** in a virtual environment, you'll have to activate it before or resomapper will not be available for use.
```

### Using *conda*

Conda is an open source package management system and environment management system, very widely used. To use conda, you will need to install it first. You can use either [miniconda](https://docs.conda.io/en/latest/miniconda.html) or the full [anaconda](https://www.anaconda.com/download/) installer. Miniconda is a lightweight version of conda that has all the features you will need for this use.

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

---

(prepare_studies)=
## Preparing the studies

Once you have resomapper correctly installed, it is time to prepare the working directory and the studies you want to process. 

The working directory is a folder where all the studies you want to process must be stored. This folder can be placed anywhere, but it’s best to avoid long names or deeply nested directory structures.

Currently, Resomapper supports several different input types:
-	Bruker raw Paravision 6.1 format
-	MRSolution scanners data
-	Nifti data (in the structure used by Resomapper)
-	DICOM data (for now, not directly included in the workflow, but via scripts using Resomapper's functions)

Make sure that the studies are stored directly at the working directory, in separate folders. Each study corresponds to a patient (mouse, human...) and contains the folders of the different sequences adquired.

In this same working directory, the output files from Resomapper will be stored. A new folder, called “resomapper_output” will be created containing the results. See the {ref}`output_files` section for more info on this.

```{note}
It is advisable to isolate different batches of processed studies in different working directories. You can later reagrupate all the output files.
```
