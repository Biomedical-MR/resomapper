(cli_run)=
# Running the CLI

The main way to use **resomapper** is through a command-line interface (CLI), which allows users to easily follow the complete image processing pipeline. To use this CLI, after installing the package, simply open a terminal window, enter the `resomapper_cli` command. 

```
> resomapper_cli
```

This will start the processing workflow, and if you need to stop it at any point, just press {kbd}`Ctrl + C`. During this process, the user will be prompted to interact with the program via the terminal (writting a response and pressing {kbd}`Enter`) or pop-up windows (clicking on different options).

The program will follow several steps:

1. [Choosing a working folder](start_cli)
2. [Converting raw studies to NIfTI](convert_studies)
3. [Selection of modalities to process](modal_select)
4. [Creating a mask](mask_creation)
5. [Preprocessing the images](preprocessing)
6. [Processing](processing)
    * {ref}`DTI`
    * {ref}`MT`
    * {ref}`Tmaps`
7. [Saving the maps](save_maps)

(start_cli)=
## 1. Choosing a working folder
After displaying a welcome message in the terminal, a pop-up window will appear in which you'll have to choose your working folder and press {kbd}`Select folder`. This directory must contain all the studies we want to process, and it will also hold all the resulting files at the end (see {ref}`prepare_studies` for more details).

```{attention}
Make sure that you have selected the correct working folder.
```

(convert_studies)=
## 2. Converting raw studies to NIfTI
After choosing the working folder the conversion of studies from raw Bruker format to NIfTI will automatically start. In case that the studies have already been converted and stored before on the same folder the user will be asked if they can be reused or they need to be converted again.

During this process the terminal will display some information prompts that can be ignored, and when completed, a message will be shown. Also, the folders containing the converted studies will be labeled with the modal they contain for an easier identification afterwards. They will be stored under the working directory, inside a folder named `convertidos` (see {ref}`converted_studies`).

(modal_select)=
## 3. Selection of modalities to process
The next step will be to select the modalities we want to process. Currently, in **resomapper**, we have implemented the posibility to generate T1, T2, T2*, MT and DTI parametric maps. A pop-up window will appear showing all these possibilities. We can check all we want and press {kbd}`OK` to start. For each study in the working directory, the selected modalities will be processed in case their adquisitions are present.

```{figure} _static/2_select_modal.png
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
## 4. Creating a mask
The first step for each instance will be to create the masks or ROIs (Region Of Interest) where we want the processing to take place (in the case of neuroimaging, we need to extract the brain). Pop-up windows will be shown for each slice where the mask can be manually created following the steps shown in the terminal (left-clicking to create lines and right-clicking to close the outline). 

If the study has already been processed and stored in the working directory so there is an available previous mask, you will be asked if you want to reuse it, so that you do not have to create it again.

```{figure} _static/3_mask_creation.png
---
width: 500px
name: img_mask_creation
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

(preprocessing)=
## 5. Preprocessing the images
Before starting the processing, we will have the option to preprocess the images before generating the parametric map. Currently, this preprocessing consist on a noise reduction filtering step (see {ref}`noise-filter` for more details). 

In case you want to perform preprocessing, a pop-up window will be shown asking for the filtering parameters. The first and second ones must be integrers, while the last one can be either an integrer or a decimal number. In the {ref}`noise-filter` section you can see what these parameters mean.

```{figure} _static/5_preprocessing_params.png
---
width: 250px
name: preprocessing_params
align: center
---
Parameter selection window.
```

Next, a window will appear showing the original image and the preprocessed image, while asking if everything is correct via the terminal. If you are not satisfied with the result, you can repeat the preprocessing as many times as you wish.

```{figure} _static/6_filtered_result.png
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

(MT)=
### MT - Magnetisation Transfer
In the case of MT images, no parameters need to be specified before the processing starts, but there might be several different images in the original study if we have modified the slope.  If so, the program will ask which folder or folders we want to process (normally, folder 1 will be the original adquisition and the following ones will be the images with the modified slope). If there is only one folder, it will be processed directly. The processing of these images is very fast, because it does not require fitting the data to a model.

(Tmaps)=
### T1, T2 and T2* maps
These maps do not require any additional specification before processing begins. Once done, you will be asked if you want to use an [R{sup}`2` filter](R2_filter) and the maps can be saved.

Processing of T maps is made thanks to the [MyRelax](https://github.com/fragrussu/MyRelax) library.

(R2_filter)=
### R{sup}`2` filter
In the modalities that imply fitting the data to a model (DTI and T maps), you will be asked if you want to apply a R{sup}`2` filter. This filter will remove any pixels that have a R{sup}`2` value under a specified threshold, meaning that they adjust worse to the model. This filter is optional and usually is not needed.

Regardless of your choice, a R{sup}`2` map will be saved for these modalities. This map consist on an image where each pixel value corresponds with the R{sup}`2` for that position. 

(save_maps)=
## 7. Saving the maps
Each time a map or a result is generated, in any of the modalities, a pop-up window will open showing the result. In addition, it will be possible to modify the color scale in which it is displayed, specifying the minimum and maximum value, as well as the name of the color palette.

```{figure} _static/9_map_scale.png
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

---

## Method details

(noise-filter)=
### Noise filtering with non-local means
The preprocessing performed includes only a noise reduction in the image using the non-local means algorithm. This algorithm is based on replacing the intensity value of a pixel with the average value of the intensities of similar pixels. As these similar pixels do not necessarily have to be close to the target pixel, this algorithm searches the whole image (hence it is non-local).

As searching the whole image is computationally expensive, we generally work by neighborhoods of pixels. For each target pixel (pixel whose intensity value is to be replaced) is taken:

* A region size T around the target pixel.
* A search area at a distance D in pixels defining a neighborhood around the target pixel.  In this neighborhood we will search for regions of size T with which to average. 
* An intensity distance H that will allow averaging those pixels that have an intensity value similar to the target pixel. It serves as a tolerance value.

The image below shows, in blue, the neighborhood defined by a distance D; in orange, the target pixel P; and in green, a region with a size T of 3x3 around P. The algorithm places a region of size T around each pixel Q that is within the neighborhood and that is in the range of values allowed by H. In the image, it is observed that Q1 and Q2 will serve to obtain the new value of P, but Q3 will not because it is outside the neighborhood. In the case of Q4, as the intensity values of its region are different from those of P, it will be a region that will also be discarded. To obtain the new value of P, a weighted sum of the average values of the pixels contained in each of the Q regions will be made, where each Q region will have a weight associated with a distance value (color distance, i.e. how similar the gray values are) between itself and the P region.

```{figure} _static/filter_non_local_means.png
---
width: 500px
name: filter_non_local_means
align: center
---
Regions used by the non-local means filtering algorithm.
```

In the program, 3 parameters must be entered:

* Size of the region, which refers to T. It must be an integer, because with this parameter regions of size TxT pixels are formed. For example, 3x3. 
* Search distance, which refers to D. It must be an integer, because with this parameter regions of size DxD pixels are formed. For example, 7x7. 
* Value of H. It can be integer or decimal. The higher it is, the more permissive it is to include regions with different intensities, so the image will be more blurred/blurred.

It is advisable to test at the beginning to see which values are most suitable for each study and even for each modality. For example, if you are working with larger images, it will be convenient to increase the search distance or the region size.

The article describing the method can be found [here](https://www.ipol.im/pub/art/2011/bcm_nlm/article.pdf). The code implementation of this algorithm has been implemented using the SciPy library. For more information see [here](https://scikit-image.org/docs/stable/auto_examples/filters/plot_nonlocal_means.html) and [here](https://scikit-image.org/docs/stable/api/skimage.restoration.html#skimage.restoration.denoise_nl_means).