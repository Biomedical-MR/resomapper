# Files generated after processing

In this section we provide an overview of the different files generated after running the **resomapper CLI**, for easier identification and retrieval of information. All the resulting files can be found in the working directory selected initially, next to the original studies folders.

## Converted studies

```
└── work_folder
    │
    ...
    │
    └── convertidos
        └── convertido_(name of the study)
            └── convertido_(name of the study)_(adquisition number)
                │
                ...
                │
                ├── convertido_(name of the study)_(adquisition number)_(subscan).nii.gz 
                ├── convertido_estudio_method.txt
                └── acquisition_method.txt
```

```{note}
This files will also be copied to the processed studies folder. However, in the case of the image files, if we chose to preprocess them with a filter, the file stored in the processed studies folder will be preprocessed, and the one in the converted studies folders will be the original.
```

## Processed studies

```
└── work_folder 
    │
    ...
    │
    └── procesados
        └── procesado_(name of the study)
            ├── (T1/T2/T2E)_procesado_(name of the study)_(adquisition number) 
            │   │
            │   ...
            │   └── mapas
            │       ├── png images of (T1/T2/T2E) map
            │       ├── R2_map.nii
            │       ├── (...)_TxyME.nii 
            │       ├── (...)_SSEME.nii 
            │       ├── (...)_S0ME.nii
            │       └── (...)_ExitME.nii
            │
            ├── (MT)_procesado_(name of the study)_(adquisition number)
            │   │
            │   ... 
            │   │
            │   ├── png images of MT map
            │   └── MT_map.nii
            │
            └── (DTI)_procesado_(name of the study)_(adquisition number)
                │
                ...
                │
                ├── procesado_estudio_subcarpeta_DwEffBval.txt
                ├── procesado_estudio_subcarpeta_DwGradVec.txt
                ├── ADC_map.nii
                ├── Dir_(x)
                │   ├── png images of ADC map for direction x
                │   └── R2_map.nii
                │
                └── (AD/RD/MD/FA)
                    ├── png images for (AD/RD/MD/FA)
                    └── (AD/RD/MD/FA)_map.nii
```
```{note}
When more than one slope is processed for the MT modality, the files showed in the previous outline will be under different subfolders (under _(MT)\_procesado\_(name of the study)\_(adquisition number)_), each one with the number of the original adquisition order.
```

In general, most modalities contain at least these two files:

* **(*modal*)_map.nii -** NIfTI file containing the corresponding **parametric map**. Contains all the slices (and directions in the case of ADC). In the case of T maps, the name will be different, as described below.
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

These files will be under the modality folder where they where originally created -- _(modal)\_procesado\_(name of the study)\_(adquisition number)_ --, as well as in the general folder of the processed study for studies where we reuse the mask in different modalities -- _procesado\_(name of the study)_.