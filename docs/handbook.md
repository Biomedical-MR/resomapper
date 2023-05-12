(cli_run)=
# Running the CLI

The main way to use **resomapper** is through a command-line interface (CLI), which allows users to easily follow the complete image processing pipeline. To use this CLI, after installing the package, simply open a terminal window, enter the `resomapper_cli` command. 

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
After displaying a welcome message in the terminal, a pop-up window will appear in which you'll have to choose your working folder and press {kbd}`Select folder`. This directory must contain all the studies we want to process, and it will also hold all the resulting files at the end (see {ref}`prepare_studies` for more details).

```{attention}
Make sure that you have selected the correct working folder.
```

(convert_studies)=
## Converting raw studies to NIfTI
After choosing the working folder the conversion of studies from raw Bruker format to NIfTI will automatically start. In case that the studies have already been converted and stored before on the same folder the user will be asked if they can be reused or they need to be converted again.

During this process the terminal will display some information prompts that can be ignored, and when completed, a message will be shown. Also, the folders containing the converted studies will be labeled with the modal they contain for an easier identification afterwards. They will be stored under the working directory, inside a folder named `convertidos` (see {ref}`converted_studies`).

(modal_select)=
## Selection of modalities to process
The next step will be to select the modalities we want to process. Currently, in **resomapper**, we have implemented the posibility to generate T1, T2, T2*, MT and DTI parametric maps. A pop-up window will appear showing all these possibilities. We can check all we want and press {kbd}`OK` to start. For each study in the working directory, the selected modalities will be processed in case their adquisitions are present.

```{figure} static/2_select_modal.png
---
width: 250px
name: select_modal
align: center
---
Modality selection window.
```

When a modality of an study has already been processed and stored before, a message will be displayed in the terminal giving the option to process it again or not. 

```{attention}
Take into account that processing it again means deleting any previous results for that modality (for the correspondig study). For that reason, make sure of copying them to another folder before continuing (you'll recieve a warning message to remind you anyway).
```

At this point, the processing of the several studies will start. A message will be shown in the terminal at the start of each study and for each modality inside of it.

(mask_creation)=
## Creating a mask
The first step for each instance will be to create the masks or ROIs (Region Of Interest) where we want the processing to take place (in the case of neuroimaging, we need to extract the brain). Pop-up windows will be shown for each slice where the mask can be manually created following the steps shown in the terminal (left-clicking to create lines and right-clicking to close the outline). 

If the study has already been processed and stored in the working directory so there is an available previous mask, you will be asked if you want to reuse it, so that you do not have to create it again.

```{figure} static/3_mask_creation.png
---
width: 500px
name: mask_creation
align: center
---
Manual mask creation.
```

After creating the masks for all slices, a pop-up window will appear with a preview of all of them. Once viewed, press {kbd}`enter` (do it while the window is on focus, you can click on it first to make sure), and the terminal will ask if it is correct. If you are not satisfied with the masks created, you can repeat the process as many times as necessary.

```{figure} static/4_mask_visualization.png
---
width: 500px
name: mask_visualization
align: center
---
Mask pre-visualization.
```

```{warning}
Make sure to **press {kbd}`enter`** when the mask pre-visualization window is open to continue the process, and not close it on the {kbd}`X` tab. It can be easy to lose it between other windows we may have opened too.
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