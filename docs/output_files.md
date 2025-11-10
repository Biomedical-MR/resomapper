(output_files)=
# Output files

In this section we provide an overview of the different files generated after running Resomapper, for easier identification. All the resulting files can be found in the working directory selected initially, under the folder `resomapper_output` and `procesados`, next to the original studies folders. 

<!-- See the section {ref}`file_overview` for an schematic representation of file locations. -->

The most important files are the map files stored in the processed studies folder, however, here we describe some more that can be useful for further analyisis.

---

(converted_studies)=
## SOURCEDATA: Converted studies

The first step of the program is to convert the original studies to NIfTI and JSON files for easier interpretation and handling. The results are stored in the `sourcedata` folder, however, they also are copied to the processed studies folder. 

NIfTI files (.nii.gz extension) contain the images, and JSON files (.json extension) contain acquisition metadata associated to those images.

In addition, for diffusion imaging adquisitions, you can also find two additional files of interest: .bval and .bvec files, containing respectively the B values vector and the matrix representing the diffusion gradient directions employed.

---

## DERIVATIVES: Processed studies

In the `derivatives` folder, you will find the files obtained after processing the images with resomapper. Parametric maps are stored both in NIfTI for quantification (.nii.gz extension), as well as in PNG in the colored version for visualization. The maps can be identified by their suffix, containing the word "processedmap". You will also find the R{sup}`2` score of the model fitting, stored pixelwise in a NIfTI image, except for the case of MTI, as computing this map does not imply the fitting of a model to the data. The mask files will also be stored as binary NIfTI files.

The original acquisitions will be copied into this folder also for reference, and if any preprocessing steps were applied, another image with the label "preproc" will be stored.


<!-- ### Mask files

Also in the processed studies folder, we can find the masks created to select the ROIs, both in NIfTI format (containing all the slices) and as png images, named:

* **mask.nii**
* **shape_slice_(_x_).png**

These files will be under the modality folder where they where originally created (**_modal_\_procesado\__name of the study\_adquisition number_**), and also a copy of the last mask created during the processing of the study will be stored in the general folder of the processed study for studies (**procesado\__name of the study_**). -->

<!-- ---

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
``` -->