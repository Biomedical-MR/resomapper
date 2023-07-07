# Changelog

## v0.3.0 (07/07/2023)

### Features

- Added ADC model fitting for less than 6 grandient directions (monoexponential decay).

### Fix

- Fixed dependency requirements: Numpy version should be < 1.25.0 to avoid problems with Dipy 1.5.0.

## v0.2.1 (02/06/2023)

### Fix

- Removed the need of having a supplfiles folder
- Fixed T map processing - previously, when different studies where present, repetition/echo times were not being used correctly.
- Fixed the reusing of mask - previously, when selecting other files, they couldn't be reused.

## v0.2.0 (29/05/2023)

### Features

- Added the possibility to choose a mask file.
- Added checking of mask and image dimensions, asking for a new mask if they don't match.

## v0.1.1 (16/05/2023)

### Fix

- Required Dipy version changed to = 1.5.0 because of error in tensor.fit()

## v0.1.0 (05/05/2023)

- First release of `resomapper`!