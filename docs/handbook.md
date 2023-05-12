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
    * {ref}`DTI`
    * {ref}`MT`
    * {ref}`Tmaps`


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
Mask pre-visualization window.
```

```{warning}
Make sure to **press {kbd}`enter`** when the mask pre-visualization window is open to continue the process, and not close it with the {kbd}`X` tab. It can be easy to lose these window between other ones we may have opened before.
```

(preprocessing)=
## Preprocessing the images
Before starting the processing, we will have the option to preprocess the images before generating the parametric map. Currently, this preprocessing consist on a noise reduction filtering step (see {ref}`noise-filter` for more details). 

In case you want to perform preprocessing, a pop-up window will be shown asking for the filtering parameters. The first and second ones must be integrers, while the last one can be either an integrer or a decimal number. In the {ref}`noise-filter` you can see what these parameters mean.

```{figure} static/5_preprocessing_params.png
---
width: 250px
name: preprocessing_params
align: center
---
Parameter selection window.
```

Next, a window will appear showing the original image and the preprocessed image, while asking if everything is correct via the terminal. If you are not satisfied with the result, you can repeat the preprocessing as many times as you wish.

```{figure} static/6_filtered_result.png
---
width: 500px
name: filtered_result
align: center
---
Filtered image pre-visualization.
```

```{note}
Take into account that the filtering algorithm currently implemented in resomapper is quite general and might need some parameter tweaking by hand to find a adequate number. We recommend to do only slight filterings. We are currently working on including more advanced denoising filters in resomapper that are better at avoiding loss of visual structures of interest.
```

(processing)=
## Processing
Once the previous steps have been completed, the processing of the corresponding modality will start. The workflow might vary a bit depending on the modality, as described in the following sections.

(DTI)=
### DTI - Diffusion Tensor Imaging
In this case, the user will first be asked for the diffusion weighted images acquisition parameters (number of b values, number of basal images and number of gradient directions). 

This step is taken to help the user keep track of the adquisiton information. The parameter values introduced by the user will be checked with the adquisition method files of the study, and if any of them doesn't match, the user will be warned. In the case of b values and the number of basal images, they will be automatically corrected.

However, in the case of the number of gradient directions, it may be the case that you want to remove some of the directions from the image because they were not acquired correctly. For this reason, if a number smaller than the real was specified, the user will be asked if that's the number of directions desired instead. Anyways, if the correct number was introduced, the user will also be asked if any directions need to be removed, just in case. In both scenarios, after confirming the number of directions to be deleted, the index of those will be asked, as shown below.

```{figure} static/7_DWI_parameters.png
---
width: 500px
name: DWI_parmeters
align: center
---
Diffusion imaging parameter specification.
```

Once we have confirmed all these adquisition parameters, the vector of effective b values and the directions matrix will be shown in the terminal. See the image below to learn how this vector and matrix are structured.

```{figure} static/8_vector_matrix.png
---
width: 500px
name: vector_matrix
align: center
---
B values vector and gradient directions matrix.
```

Finally, the DTI model will be adjusted to the data, the ADC map will be computed and then the tensor will be solved to compute the remaining maps. In total, the maps produced for this modality are:

* **ADC -** Apparent Diffusion Coeficient
* **AD -** Axial Diffusivity
* **RD -** Radial Diffusivity
* **MD -** Mean Diffusivity
* **FA -** Fractional Anisotropy

(MT)=
### MT - Magnetisation Transfer
In the case of MT images, no parameters need to be specified before the processing starts, but there might be several different images in the original study if we have modified the slope.  If so, the program will ask which folder or folders we want to process (normally, folder 1 will be the original adquisition and the following ones will be the images with the modified slope). If there is only one folder, it will be processed directly. The processing of these images is very fast, because it does not require fitting the data to a model.

(Tmaps)=
### T1, T2 and T2* maps
These maps do not require any additional specification before processing begins. Once done, you will be asked if you want to use an {ref}`R2_filter` and the maps can be saved.

(R2_filter)=
#### R{sup}`2` filter
In the modalities that imply fitting the data to a model (DTI and T maps), you will be asked if you want to apply a R{sup}`2` filter. This filter will remove any pixels that have a R{sup}`2` value under a specified threshold, meaning that they adjust worse to the model. This filter is optional and usually is not needed.

## Saving the maps

# Method details

(noise-filter)=
## Noise filtering with non-local menas