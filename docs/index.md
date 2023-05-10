# resomapper

```{warning}
We are still under construction and this is not an stable release. Please wait for the next release, coming soon!
```

Welcome to **resomapper**, a pipeline for processing MR images and generating parametric maps. 

This tool is designed and developed by the *Biomedical Magnetic Resonance Lab* at the *Instituto de Investigaciones Biomédicas "Alberto Sols"* (CSIC-UAM). This project aims to collect a series of MR image processing tools written in Python under a friendly user interface for the lab needs. It is designed to streamline the processing of images, starting from raw adquisition files (we use Bruker study folders) to end up with parametric maps such as T1, T2 or T2* maps, as well as diffusion metric maps derived from DTI analysis.

```{note}
**Resomapper** is a tool under active development, with new features and improvements still on the way. It is used in-house for preclinical MRI data, mainly for mouse brain imaging, but can be used for different types of MRI data. Any suggestions are welcome!
```

% Overview: main page also in toctree
```{toctree}
:maxdepth: 1
:hidden:

self
```

```{toctree}
:maxdepth: 1
:hidden:
:caption: User's guide

first_steps.md
handbook.md
```

```{toctree}
:maxdepth: 1
:hidden:
:caption: More info

autoapi/index
changelog.md
contributing.md
conduct.md
example.ipynb
```