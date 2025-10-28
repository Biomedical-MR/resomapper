import os
# import nibabel as nib
# import numpy as np
import SimpleITK as sitk
from pydicom import dcmread

import warnings

warnings.filterwarnings("ignore")

#### DICOM CONVERSION FUNCTIONS ####


# def convert_dicom_series(dicom_series_path, output_nifti_path):
#     # Read the DICOM series
#     reader = sitk.ImageSeriesReader()
#     dicom_series = reader.GetGDCMSeriesFileNames(dicom_series_path)
#     reader.SetFileNames(dicom_series)
#     image = reader.Execute()

#     # Convert the image to NIfTI format and save
#     sitk.WriteImage(image, output_nifti_path)


def convert_dicom_series(dicom_series_path, output_nifti_path):
    # Read the series of DICOM files
    reader = sitk.ImageSeriesReader()
    dicom_series = reader.GetGDCMSeriesFileNames(dicom_series_path)
    reader.SetFileNames(dicom_series)
    
    # Read DICOM metadata to identify temporal positions (0020,0105)
    temporal_positions = set()  # Store unique temporal positions
    dicom_files = []
    
    # Extract temporal position for each DICOM file
    for dicom_file in dicom_series:
        ds = dcmread(dicom_file)
        # Get the temporal position from tag (0020,0105), default to 1 if not available
        temporal_position = getattr(ds, 'TemporalPositionIdentifier', 1)
        temporal_positions.add(temporal_position)
        dicom_files.append((temporal_position, dicom_file))
    
    # Sort dicom_files by temporal position
    dicom_files.sort(key=lambda x: x[0])
    
    # Group the files by temporal positions if more than 1 position
    dicom_files_grouped = {}
    for position, dicom_file in dicom_files:
        if position not in dicom_files_grouped:
            dicom_files_grouped[position] = []
        dicom_files_grouped[position].append(dicom_file)
    
    # Process each temporal position group
    images = []
    for position, files in dicom_files_grouped.items():
        # Set filenames for the current temporal position group
        reader.SetFileNames(files)
        # Read image for this temporal position
        image = reader.Execute()
        images.append(image)
    
    # If there are multiple temporal positions, join them into a 4D image
    if len(images) > 1:
        image_4d = sitk.JoinSeries(images)
    else:
        image_4d = images[0]  # Only one position, use the single image (3D)
    
    # Save the image as NIfTI
    sitk.WriteImage(image_4d, output_nifti_path)


def convert_dicom_localizer(dicom_series_path, output_nifti_path):
    dicom_files = [os.path.join(dicom_series_path, f) for f in os.listdir(dicom_series_path)]
    
    # Read DICOM files individually
    images = []
    for dicom_file in dicom_files:

        ds = dcmread(dicom_file)
        pixel_array = ds.pixel_array
        image = sitk.GetImageFromArray(pixel_array)
        
        # Get spacing from DICOM header
        if 'PixelSpacing' in ds:
            spacing_xy = ds.PixelSpacing  # X and Y spacing
        else:
            spacing_xy = [1.0, 1.0]  # Default values

        if 'SliceThickness' in ds:
            spacing_z = ds.SliceThickness  # Z spacing
        else:
            spacing_z = 1.0  # Default value

        # If zspacing is 0, adjust to a small value
        if spacing_z == 0:
            spacing_z = 1.0  # Adjust if neccesary

        new_spacing = [float(spacing_xy[0]), float(spacing_xy[1]), float(spacing_z)]
        image.SetSpacing(new_spacing)
        
        images.append(image)
    
    # Combine images into 3D stack
    combined_image = sitk.JoinSeries(images)

    sitk.WriteImage(combined_image, output_nifti_path)



def get_echo_times_from_dicom(dicom_series_path, output_echo_times_path=None):
    echo_times = []
    for file in os.listdir(dicom_series_path):
        ds = dcmread(os.path.join(dicom_series_path, file))
        echo_times.append(int(ds.EchoTime))  # TODO: or float??
    unique_echos_list = [
        item for index, item in enumerate(echo_times) if item not in echo_times[:index]
    ]
    if output_echo_times_path is not None:
        with open(output_echo_times_path, "w") as f:
            f.write(" ".join(map(str, unique_echos_list)))
    else:
        return unique_echos_list


def get_rep_times_from_dicom(dicom_series_path, output_rep_times_path=None):
    repetition_times = []
    for file in os.listdir(dicom_series_path):
        ds = dcmread(os.path.join(dicom_series_path, file))
        repetition_times.append(int(ds.RepetitionTime))  # TODO: or float??
    unique_reps_list = [
        item
        for index, item in enumerate(repetition_times)
        if item not in repetition_times[:index]
    ]
    if output_rep_times_path is not None:
        with open(output_rep_times_path, "w") as f:
            f.write(" ".join(map(str, unique_reps_list)))
    else:
        return unique_reps_list


# def reshape_nifti_from_times_file(nifti_path, times_files_path, output_path):
#     img = nib.load(nifti_path)
#     data = img.get_fdata()

#     # TODO: use array instead of file
#     with open(os.path.join(times_files_path), "r") as f:
#         times_str = f.read().split()
#         times = [int(time) for time in times_str]

#     num_times = len(times)
#     pixel_res_1 = int(img.shape[0])
#     pixel_res_2 = int(img.shape[1])
#     num_slices = int(img.shape[2] / num_times)

#     desired_shape = (pixel_res_1, pixel_res_2, num_times, num_slices)

#     # Assuming slices are along the first dimension
#     reshaped_data = data.reshape(desired_shape)
#     reshaped_data = np.swapaxes(reshaped_data, 2, 3)

#     # Save the reshaped data as a new NIfTI file
#     reshaped_img = nib.Nifti1Image(reshaped_data, img.affine)
#     nib.save(reshaped_img, output_path)
