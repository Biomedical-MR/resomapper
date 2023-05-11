# resomapper

Welcome to `resomapper`, a pipeline for processing MR images and generating parametric maps. 

This tool is designed and developed by the *Biomedical Magnetic Resonance Lab* at the *Instituto de Investigaciones Biomédicas "Alberto Sols"* (CSIC-UAM). This project aims to collect a series of MR image processing tools written in Python under a friendly user interface for the lab needs. It is designed to streamline the processing of images, starting from raw adquisition files (we use Bruker study folders) to end up with parametric maps such as T1, T2 or T2* maps, as well as diffusion metric maps derived from DTI analysis.

Note that `resomapper` is a tool under active development, with new features and improvements still on the way. It is used in-house for preclinical MRI data, mainly for mouse brain imaging, but can be used for different types of MRI data. Any suggestions are welcome!

## Installation

Soon, resomapper will be available for installation via pip. Please stay tuned.

```bash
pip install resomapper
```

It is recommended to use this tool from a virtual environment, that can be created with conda or venv.

## Usage

The main feature of `resomapper` is its Command Line Interface, that can be started directly from the terminal with a single command:

```bash
resomapper_cli
```

After running this command, you'll only need to follow the instructions that will be shown in the terminal. Initially, you will need to provide a folder containing the studies to be processed in Bruker format. This is also where the result files will be stored. The structure of this root folder is the following:

```
└── root_folder
    ├── study_folder_1
    │   ├── 1
    │   ├── 2
    │   ...
    │   └── ...
    ├── study_folder_2
    │   ├── 1
    │   ├── 2
    │   ...
    │   └── ...
    ...
    ├── * convertidos 
    ├── * procesados
    └── * supplfiles 

* Automatically created after processing, storing the results. 
```

## Contributing

Interested in contributing? Check out the contributing guidelines. Please note that this project is released with a Code of Conduct. By contributing to this project, you agree to abide by its terms.

## License

`resomapper` was created by Biomedical-MR. It is licensed under the terms of the MIT license.

