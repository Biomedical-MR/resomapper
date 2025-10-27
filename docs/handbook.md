(cli_run)=
# Running the interactive workflow (CLI)

The main way to use Resomapper is through a command-line interface (CLI), which allows users to easily follow the complete image processing pipeline. To use this CLI, after installing the package, simply open a terminal window and enter the `resomapper_cli` command. 

```
> resomapper_cli
```

This will start the processing workflow, and if you need to stop it at any point, just press {kbd}`Ctrl + C`. During this process, the user will be prompted to interact with the program via the terminal (writting a response and pressing {kbd}`Enter`) or pop-up windows (clicking on different options).

The program will follow several steps:

1. [Choosing a working folder](start_cli)
2. [Converting studies to NIfTI](convert_studies)
3. [Selection of modalities to process](modal_select)
4. [Preprocessing the images](preprocessing)
5. [Creating a mask](mask_creation)
6. [Processing](processing)
    * {ref}`DTI`
    * {ref}`MT`
    * {ref}`Tmaps`
7. [Saving the output maps](save_maps)

(start_cli)=
## 1. Choosing a working folder
After displaying a welcome message in the terminal, a pop-up window will appear in which you'll have to choose your working folder and press {kbd}`Select folder`. This directory must contain all the studies we want to process, and it will also hold all the resulting files at the end (see {ref}`prepare_studies` and {ref}`output_files`for more details).

```{attention}
Make sure that you have selected the correct working directory. If you are selecting the folder of only one study, it won't be recognised. You should select the folder that contains that study (or more than one).
```

(convert_studies)=
## 2. Converting studies to NIfTI
If your input data is not already on NIfTI format, the conversion of studies will automatically start after choosing the working directory. In case that the studies have already been converted and stored before on the same folder the user will be asked if they can be reused or they need to be converted again. When completed, a message will be shown. Also, the folders containing the converted studies will be labeled according to the BIDS format with the modal they contain for an easier identification afterwards. They will be stored under the working directory, inside a folder named `resomapper_output` (see {ref}`converted_studies`).

(modal_select)=
## 3. Selection of modalities to process
The next step will be to select the modalities we want to process. Currently, in Resomapper, we have implemented the posibility to generate T1, T2, T2*, MTI and DTI parametric maps. A pop-up window will appear showing all these possibilities. You can check all the ones you want and press {kbd}`OK` to start. For each study in the working directory, the selected modalities will be processed in case their adquisitions are present.

```{figure} _static/fig_select_modal.png
---
width: 250px
name: select_modal
align: center
---
Modality selection window.
```

If any studies have already been processed and stored before, a message will be displayed in the terminal giving the option to process it again or not. 

```{attention}
Take into account that processing it again means deleting any previous results for that modality (for the correspondig study). For that reason, make sure of copying them to another folder before continuing if you need them (you'll recieve a warning message to remind you anyway).
```

At this point, the processing workflow for the several studies will start. A message will be shown in the terminal at the start of each study and for each modality inside of it.

(preprocessing)=
## 4. Preprocessing the images
Before starting the processing, you will have the option to preprocess the images before generating the parametric map. Currently, the available preprocessing options available include several denoising filters, Gibbs artifact suppression and bias field correction.

For each of these, a question will be asked to determine if you want to use any of these, and if so, in the case of the denoising filters and bias field correction, a pop-up window will be shown asking for the filtering parameters. Usually, no changes should be done to these parameters, unless you get unwanted results and need to fine tune them. In that case, here are the references from the original packages where they come from, so you can check exactly what each parameter means:

...

After using any of the preprocessing options, a window will appear showing one of the slices of the original image and the corresponding preprocessed one. Also, in the case of the denoising filters or the Gibbs artifact correction, the residuals between both images (img1-img2)^2 will be shown. Ideally, in the case of denoising, these should be more or less randomly distributed, meaning that no structures of the original image have been over-smoothed. For Gibbs artifacts, you should see the removed rings in the residuals. In the case of the bias field correction, the calculated bias field will be shown. If you are not satisfied with the result, you can repeat the preprocessing as many times as you wish.

```{figure} _static/fig_denoising.png
---
width: 500px
name: denoising
align: center
---
Filtered image pre-visualization.
```

(mask_creation)=
## 5. Creating a mask
The first step for each instance will be to create the masks or ROIs (Region Of Interest) where we want the processing to take place (in the case of neuroimaging, we need to extract the brain). To do so, the user will be asked between the following options:

* **Selecting a file** that contains a binary mask, in NiFTI format.

* **Reusing the last mask** used for the current study. This option will be available only if any of the modals have been processed before and there is a mask file stored in the general study folder.

* **Manually creating a mask** by drawing it. In this case, pop-up windows will be shown for each slice where the mask can be manually created following the steps shown in the terminal (left-clicking to create lines and right-clicking to close the outline). 

```{figure} _static/fig_mask_creation.png
---
width: 500px
name: mask_creation
align: center
---
Manual mask creation.
```

After creating the masks for all slices, a pop-up window will appear with a preview of all of them. Once viewed, press {kbd}`enter` (do it while the window is on focus, you can click on it first to make sure), and the terminal will ask if it is correct. If you are not satisfied with the masks created, you can repeat the process as many times as necessary.

```{figure} _static/4_mask_visualization.png
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

```{note}
After specifying a mask, the program will check if the images to be processed and the seleted mask match. If you have accidentally selected a mask file with more slices or different resolution, you will have the option to select the mask again.
```

(processing)=
## 6. Processing
Once the previous steps have been completed, the processing of the corresponding modality will start. The workflow might vary a bit depending on the modality, as described in the following sections.

(DTI)=
### DTI - Diffusion Tensor Imaging
In this case, the user will first be asked for the diffusion weighted images acquisition parameters (number of b values, number of basal images and number of gradient directions). 

This step is taken to help the user keep track of the adquisiton information. The parameter values introduced by the user will be checked with the adquisition method files of the study, and if any of them doesn't match, the user will be warned. In the case of b values and the number of basal images, they will be automatically corrected.

However, in the case of the number of gradient directions, it may be the case that you want to remove some of the directions from the image because they were not acquired correctly. For this reason, if a number smaller than the real was specified, the user will be asked if that's the number of directions desired instead. Anyways, if the correct number was introduced, the user will also be asked if any directions need to be removed, just in case. In both scenarios, after confirming the number of directions to be deleted, the index of those will be asked, as shown below.

```{figure} _static/7_DWI_parameters.png
---
width: 600px
name: DWI_parmeters
align: center
---
Diffusion imaging parameter specification.
```

Once we have confirmed all these adquisition parameters, the vector of effective b values and the directions matrix will be shown in the terminal. See the image below to learn how this vector and matrix are structured.

```{figure} _static/8_vector_matrix.png
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

Before saving the maps, you will be asked if you want to use an [R{sup}`2` filter](R2_filter) and you will be able to adjust the color scale of each map (see {ref}`save_maps`).

Proccesing of DTI maps is made thanks to the [DIPY](https://dipy.org/) library.

#### ADC for acquisitions of less than 6 directions
For DWI acquisitions with less than 6 directions available, the DTI model can't be calculated. In that case, the program will provide the option to use the monoexponential decay model, that means fitting the signal values for each pixel to the following curve equation: 
$S=S_0 * e^{-b * ADC}$

There is also the option to do a line regression fitting to the linearized equation: 
$ln(S)=ln(S_0) - b*ADC$

The user will be given the option to choose between these two options, and then the model will be fitted. After that, the user will have the opportunity to examine the fitted curves for each pixel in an interactive graphic. Finally, the ADC map will be saved the same way as before.

```{note}
Fitting these models will only give the ADC map and the R{sup}`2` map as outputs. AD, RD and FA maps are exclusive of the DTI model. MD can be estimated as the mean of all the ADC directions.
```

(MT)=
### MTI - Magnetisation Transfer Imaging
In the case of MT images, no parameters need to be specified before the processing starts, but there might be several different images in the original study if we have modified the slope.  If so, the program will ask which folder or folders we want to process (normally, folder 1 will be the original adquisition and the following ones will be the images with the modified slope). If there is only one folder, it will be processed directly. The processing of these images is very fast, because it does not require fitting the data to a model.

(Tmaps)=
### Relaxometry: T1, T2 and T2* maps
These maps do not require any additional specification before processing begins. Once done, you will be asked if you want to use an [R{sup}`2` filter](R2_filter) and the maps can be saved.

Processing of T maps is made thanks to the [MyRelax](https://github.com/fragrussu/MyRelax) library.

(R2_filter)=
### R{sup}`2` filter
In the modalities that imply fitting the data to a model (DTI and T maps), you will be asked if you want to apply a R{sup}`2` filter. This filter will remove any pixels that have a R{sup}`2` value under a specified threshold, meaning that they adjust worse to the model. This filter is optional and usually is not needed.

Regardless of your choice, a R{sup}`2` map will be saved for these modalities. This map consist on an image where each pixel value corresponds with the R{sup}`2` for that position. 

(save_maps)=
## 7. Saving the maps
Each time a map or a result is generated, in any of the modalities, a pop-up window will open showing the result. In addition, it will be possible to modify the color scale in which it is displayed, specifying the minimum and maximum value, as well as the name of the color palette.

```{figure} _static/fig_map_saving.png
---
width: 500px
name: map_scale
align: center
---
Map scaling windows.
```

The different color palettes and their names can be found in the figure below (see ). The recommended ones are "turbo" (selected by default), and "jet". You can try different combinations and visualize them by pressing the {kbd}`Refresh` button. Once you are satisfied, click on {kbd}`Accept` to save the map.

```{figure} _static/colorbars.png
---
width: 500px
name: colorbars
align: center
---
Different color palettes that can be used for map coloring.
```

When all the maps of the selected modalities from all the studies included in the working directory have been processed and, the processing will be complete and the resomapper CLI will stop running.
