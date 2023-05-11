# CLI handbook

The main way to use **resomapper** is through a command-line interface (CLI), which allows users to easily follow the complete image processing pipeline. To use this CLI, after installing the package, simply open a terminal window, enter the `resomapper_cli` command and press {kbd}`Enter`. 

```
> resomapper_cli
```

This will start the processing workflow, and if you need to stop it at any point, just press {kbd}`Ctrl + C`. During this process, the user will be prompted to interact with the program via the terminal (writting a response and pressing {kbd}`Enter`) or pop-up windows (clicking on different options).

The program will follow several steps:

1. {ref}`start_cli`
2. {ref}`convert_studies`
3. {ref}`modal_select`
4. {ref}`mask_creation`
5. {ref}`preprocessing`
6. {ref}`processing`
    * {ref}`T1`
    * {ref}`T2`
    * {ref}`T2E`
    * {ref}`MT`
    * {ref}`DTI`


(start_cli)=
## Choosing a working folder
After displaying a welcome message in the terminal, a pop-up window will appear in which you'll have to choose your working folder and press {kbd}`Select folder`. This directory must contain all the studies we want to process, and it will also hold all the resulting files at the end (see previous section for more details).

```{attention}
Make sure that you have selected the correct working folder.
```

(convert_studies)=
## Converting raw studies to NIfTI
After choosing the working folder the conversion of studies from raw Bruker format to NIfTI will automatically start. In case that the studies have already been converted and stored before on the same folder they will be reused instead of converted again.

During this process the terminal will display some information messages that can be dismissed by the user. When completed, a message will be shown. Also, the folders containing the converted studies will be labeled for an easier identification afterwards. They will be under the working directory, inside a folder named `convertidos`.

(modal_select)=
## Selection of modalities to process
The next step will be to select the modalities we want to process. Currently, in **resomapper**, we have implemented the posibility to generate T1, T2, T2*, MT and DTI parametric maps. A pop-up window will appear showing all these possibilities. We can check all we want and press {kbd}`OK` to start. For each study in the working directory, the selected modalities will be processed in case their adquisitions are present.

When a modality of an study has already been processed and stored before, a message will be displayed in the terminal giving the option to process it again or not. 

```{attention}
Take into account that processing it again means deleting any previous results for that modality (for the correspondig study). For that reason, make sure of copying them to another folder before continuing (you'll recieve a warning message to remind you anyway).
```

(mask_creation)=
## Creating a mask


```{attention}

```

(preprocessing)=
## Preprocessing the images


```{note}

```

(processing)=
## Processing

(T1)=
### T1 map

(T2)=
### T2 map

(T2E)=
### T2* map

(MT)=
### MT - Magnetisation Transfer

(DTI)=
### DTI - Diffusion Tensor Imaging