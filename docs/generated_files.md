# Files generated after processing

In this section we provide an overview of the different files generated after running the **resomapper CLI**, for easier identification and retrieval of information. All the resulting files can be found in the working directory selected initially, next to the original studies folders.

## Converted studies

```{code-block} c++
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

```{code-block} r
└── work_folder 
    │
    ...
    │
    └── procesados
        └── procesado_(name of the study)
            ├── (modal)_procesado_(name of the study)_(adquisition number)
            ├── (T1/T2/T2E)_procesado_(name of the study)_(adquisition number) 
            │   │
            │   ...
            │   │
            │   ├── (T1/T2/T2E) map images.png
            │   ├── R2_map.nii
            │   ├── (...)_TxyME.nii 
            │   ├── (...)_SSEME.nii 
            │   ├── (...)_S0ME.nii
            │   └── (...)_ExitME.nii
            │
            ├── (MT)_procesado_(name of the study)_(adquisition number)
            │   │
            │   ... (when more than one slope is processed, the following files will be under 
            │   ... different folders, with the number of the original adquisition order)
            │   │
            │   ├── MT map images.png
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
                │   ├── ADC map of direction x images.png
                │   └── R2_map.nii
                │
                └── (AD/RD/MD/FA)
                    ├── (AD/RD/MD/FA) map images.png
                    └── (AD/RD/MD/FA)_map.nii
```

### Mask files
