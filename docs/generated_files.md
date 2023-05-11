# Files generated after processing

In this section we provide an overview of the different files generated after running the **resomapper CLI**, for easier identification and retrieval of information. All the resulting files can be found in the working directory selected initially, under the folders `convertidos` and `procesados`, next to the original studies folders. See the section {ref}`file_overview` for an schematic representation of file locations.

The most important files are the map files stored in the processed studies folder, however, here we describe some more that can be useful for further analyisis.

## Converted studies

The first step of the program is to convert the raw Bruker files to NIfTI and text files for easier interpretation and handling. The results are stored in the converted studies folder, however, they also are copied to the processed studies folder. 

The most relevant files in the converted studies folder are the following:

* **convertido_(name of the study)\_(adquisition number)\_(subscan).nii.gz -** Original adquired images. If there is more than one, they will have the *subscan* suffix, and the one we will be interested on is **subscan_0**, with the exception of MT, where each one will correspond to the images for the different slopes specified during adquisition (in order).
* **convertido_(name of the study)_(adquisition number)_method.txt -** Adquisition parameters.
* **acquisition_method.txt -** Name of the MR sequence used for adquisition.

In addition, for diffusion imaging adquisitions, we can also find these two files of interest:

* **convertido_(name of the study)_(adquisition number)_DwEffBval.txt -** Effective B values vector.
* **convertido_(name of the study)_(adquisition number)_DwGradVec.txt -** Matrix of gradient directions.

```{note}
This files will also be copied to the processed studies folder, with the same name as before, but changing **"convertido"** for **"procesado"** in the file name. However, in the case of the NIfTI image files, if we chose to preprocess them with a filter, the file stored in the processed studies folder will be preprocessed, and the one in the converted studies folders will be the original.
```

## Processed studies

In general, most processed modalities contain these two files:

* **(modal)_map.nii -** NIfTI file containing the corresponding **parametric map**. Contains all the slices (and directions in the case of ADC). In the case of T maps, the name will be different, as described below.
* **R2_map.nii -** NIfTI file containing a map of the **R{sup}`2` score of the model fitting** for each pixel of our images (contains all slices). It is not present in the case of MT, as computing this map does not imply the fitting of a model to the data.


In the case of T1, T2 or T2* image processing, there are some files that are named a bit different or that are not present in the other modalities:

* **(...)_TxyME.nii -** NIfTI file containing the **T1, T2 or T2* parametric map**.
* **(...)_SSEME.nii -** Fitting sum of squared errors.
* **(...)_S0ME.nii -** T1w proton density, with receiver coil field bias.
* **(...)_ExitME.nii -** Exit code (1 = successful fitting, 0 = background, -1 = 
unsuccessful fitting)


### Mask files

Also in the processed studies folder, we can find the masks created to select the ROIs, both in NIfTI format (containing all the slices) and as png images, named:

* **mask.nii**
* **shape_slice_(_x_).png**

These files will be under the modality folder where they where originally created (**_modal_\_procesado\__name of the study\_adquisition number_**), as well as in the general folder of the processed study for studies where we reuse the mask in different modalities (**procesado\__name of the study_**).

(file_overview)=
## File system overview

```
└── work_folder 
    │
    ...
    │
    ├── convertidos
    │   └── convertido_(name of the study)
    │       └── (modal)_convertido_(name of the study)_(adquisition number)
    │           │
    │           ...
    │           │
    │           ├── convertido_(name of the study)_(adquisition number)_(subscan).nii.gz 
    │           ├── convertido_(name of the study)_(adquisition number)_method.txt
    │           ├── acquisition_method.txt
    │           │
    │           │   ** Just for DWI adquisitions **
    │           ├── convertido_(name of the study)_(adquisition number)_DwEffBval.txt
    │           └── convertido_(name of the study)_(adquisition number)_DwGradVec.txt
    │            
    └── procesados
        └── procesado_(name of the study)
            ├── (T1/T2/T2E)_procesado_(name of the study)_(adquisition number) 
            │   │
            │   ├── method, scan images and mask files
            │   │
            │   └── mapas
            │       │
            │       ├── png images of (T1/T2/T2E) map
            │       ├── R2_map.nii
            │       ├── (...)_TxyME.nii 
            │       ├── (...)_SSEME.nii 
            │       ├── (...)_S0ME.nii
            │       └── (...)_ExitME.nii
            │
            ├── (MT)_procesado_(name of the study)_(adquisition number)
            │   │
            │   ├── method, scan images and mask files
            │   ├── png images of MT map
            │   └── MT_map.nii
            │
            └── (DTI)_procesado_(name of the study)_(adquisition number)
                │
                ├── method, scan images and mask files
                ├── DwEffBval and DwGradVec files
                ├── ADC_map.nii
                │   
                ├── Dir_(x)
                │   │
                │   ├── png images of ADC map for direction x
                │   └── R2_map.nii
                │   
                └── (AD/RD/MD/FA)
                    │
                    ├── png images for (AD/RD/MD/FA)
                    └── (AD/RD/MD/FA)_map.nii
```
```{note}
When more than one slope is processed for the MT modality, the files showed in the previous outline will be under different subfolders (under **MT\_procesado\__name of the study\_adquisition number_**), each one with the number of the original adquisition order.
```