# First steps

This section covers the first steps in order to be able to run **resomapper**: the installation and the preparation of the working directory and some considerations about the studies to process.

## Installation

First of all, please make sure to have **Python 3.8 or higher** installed as well as pip.  Check out the section {ref}`requirements` if you need more information on this matter. 

Although optional, it is good practice to use virtual environments to avoid conflicts with other package versions that you have installed for other uses. If you want to know more about this, check out the section {ref}`venv`.

```{warning}
We are still under construction and this is not an stable release. Please wait for the next release, coming soon! Resomapper is still not available for install on PyPi
```

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

(requirements)=
### System requirements

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

(venv)=
### Using a virtual environment

...

(prepare_studies)=
## Preparing the studies

Once you have resomapper correctly installed, it is time to prepare the working directory and the studies you want to process.