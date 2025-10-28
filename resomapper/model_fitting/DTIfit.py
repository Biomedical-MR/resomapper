from resomapper.core.misc import auto_innited_logger as lggr
import numpy as np
from dipy.reconst.dti import (
    apparent_diffusion_coef,
    fractional_anisotropy,
)
import nibabel as nib
from dipy.core.gradients import gradient_table
from dipy.core.sphere import Sphere
from dipy.io.gradients import read_bvals_bvecs
import dipy.reconst.dti as dti


def cli_ask_dti_info(n_bval_real, n_basal_real, n_dirs_real):
    """
    Ask the user to enter b values, number of basal images and number of directions.
    """
    print(
        f"\n{lggr.ask}Please enter some information about this DWI acquisition for a previous check."
    )
    while True:
        try:
            n_bval = int(
                input(
                    f"\n{lggr.ask}How may b values for each direction has this study (= number of shells)?"
                    f"\n{lggr.pointer}"
                )
            )
            if n_bval == n_bval_real:
                print(f"\n{lggr.info}Correct!")
            else:
                print(
                    f"\n{lggr.warn}Incorrect. This DWI study has {n_bval_real} b values per direction."
                )
            break
        except ValueError:
            print(f"\n{lggr.error}Please enter a number.")
    while True:
        try:
            n_basal = int(
                input(
                    f"\n{lggr.ask}How many basal images has this study?\n{lggr.pointer}"
                )
            )
            if n_basal == n_basal_real:
                print(f"\n{lggr.info}Correct!")
            else:
                print(
                    f"\n{lggr.warn}Incorrect. This DWI study has {n_basal_real} basal images."
                )
            break
        except ValueError:
            print(f"\n{lggr.error}Please enter a number.")
    while True:
        try:
            n_dirs = int(
                input(f"\n{lggr.ask}How many directions has this study?\n{lggr.pointer}")
            )
            if n_dirs == n_dirs_real:
                print(f"\n{lggr.info}Correct!")
            elif n_dirs > n_dirs_real:
                print(
                    f"\n{lggr.warn}Incorrect. This DWI study has {n_dirs_real} directions."
                )
            else:
                print(
                    f"\n{lggr.warn}Incorrect. This DWI study has {n_dirs_real} directions. "
                    "You will be able to remove some in the next step, if you want to."
                )
            break
        except ValueError:
            print(f"\n{lggr.error}Please enter a number.")


def count_basal_dirs_bvals(b_vals, b_vecs):
    n_basal = np.sum(np.all(b_vecs == [0, 0, 0], axis=1))
    rounded_b_vals = [round(b_val, -2) for b_val in b_vals]
    # rounded_b_vals = [((b_val // 100) * 100) for b_val in b_vals]
    n_bval = len(set(rounded_b_vals)) - 1
    n_dirs = (len(rounded_b_vals) - n_basal) / n_bval
    return n_bval, n_basal, n_dirs


def save_bvals_bvecs(bvals, bvecs, output_basename):
    np.savetxt(f"{output_basename}.bval", bvals, fmt="%g", newline=" ")
    np.savetxt(f"{output_basename}.bvec", bvecs.T, fmt="%g")


def compute_dti_map(tensor, map_type: str, gtab=None):
    unit_change = 1_000_000

    if map_type == "AD":
        pmap = tensor.ad * unit_change
        pmap[pmap < 0.00000001] = float("nan")
    elif map_type == "RD":
        pmap = tensor.rd * unit_change
        pmap[pmap < 0.00000001] = float("nan")
    elif map_type == "MD":
        pmap = tensor.md * unit_change
        pmap[pmap < 0.00000001] = float("nan")
    elif map_type == "FA":
        pmap = fractional_anisotropy(tensor.evals)
        pmap[pmap > 0.95] = float("nan")
    elif map_type == "ADC":
        my_sphere = Sphere(xyz=gtab.bvecs[~gtab.b0s_mask])
        pmap = apparent_diffusion_coef(tensor.quadratic_form, my_sphere)
        unit_change = 1_000_000
        pmap = pmap * unit_change
        pmap[pmap < 0.00000001] = float("nan")

    return pmap


def print_bvals_bvecs(bvals, bvecs):
    print(f"\n{'bval':<15} {'bvec_x':<15} {'bvec_y':<15} {'bvec_z':<15}")

    for bval, bvec in zip(bvals, bvecs):
        print(f"{bval:<15.3f} {bvec[0]:<15.6f} {bvec[1]:<15.6f} {bvec[2]:<15.6f}")


def process_dti(nii_fname, bval_path, bvec_path, output_basename, mask_fname=None):

    print("\n    ... loading input data")
    study_nii = nib.load(nii_fname)
    study_data = study_nii.get_fdata()

    if mask_fname is not None:
        mask_nii = nib.load(mask_fname)
        mask_data = mask_nii.get_fdata()
        for i in range(np.shape(study_data)[3]):  # For each image of each slice
            study_data[:, :, :, i] = study_data[:, :, :, i] * mask_data

    # Can be a text file or a np.array
    try:
        bvals, bvecs = read_bvals_bvecs(bval_path, bvec_path)
    except ValueError:
        bvals = np.array(bval_path, "float64")
        bvecs = np.array(bvec_path, "float64")

    gtab = gradient_table(bvals, bvecs, atol=1e-0)
    tensor_model = dti.TensorModel(gtab, fit_method="NLLS", return_S0_hat=True)
    print("\n    ... fitting tensor model")
    tensor_fit = tensor_model.fit(study_data)

    predicted_signal = tensor_fit.predict(gtab)
    r2_map = compute_R2(study_data, predicted_signal)
    nii_ima = nib.Nifti1Image(
        r2_map.astype(np.float32), study_nii.affine  # , study_nii.header
    )
    nib.save(nii_ima, output_basename + "_R2map.nii.gz")

    # Process maps
    MD_map = compute_dti_map(tensor_fit, "MD")
    AD_map = compute_dti_map(tensor_fit, "AD")
    RD_map = compute_dti_map(tensor_fit, "RD")
    FA_map = compute_dti_map(tensor_fit, "FA")
    ADC_map = compute_dti_map(tensor_fit, "ADC", gtab)

    print("\n    ... saving output files")

    nii_ima = nib.Nifti1Image(
        MD_map.astype(np.float32), study_nii.affine  # , study_nii.header
    )
    nib.save(nii_ima, output_basename + "_DTI-MD-processedmap.nii.gz")

    nii_ima = nib.Nifti1Image(
        AD_map.astype(np.float32), study_nii.affine  # , study_nii.header
    )
    nib.save(nii_ima, output_basename + "_DTI-AD-processedmap.nii.gz")

    nii_ima = nib.Nifti1Image(
        RD_map.astype(np.float32), study_nii.affine  # , study_nii.header
    )
    nib.save(nii_ima, output_basename + "_DTI-RD-processedmap.nii.gz")

    nii_ima = nib.Nifti1Image(
        FA_map.astype(np.float32), study_nii.affine  # , study_nii.header
    )
    nib.save(nii_ima, output_basename + "_DTI-FA-processedmap.nii.gz")

    nii_ima = nib.Nifti1Image(
        ADC_map.astype(np.float32), study_nii.affine  # , study_nii.header
    )
    nib.save(nii_ima, output_basename + "_DTI-ADC-processedmap.nii.gz")


def compute_R2(signal_data, signal_data_predicted):

    x_dim, y_dim, z_dim, n_dirs = signal_data.shape
    r2_map = np.zeros((x_dim, y_dim, z_dim))

    for x in range(x_dim):
        for y in range(y_dim):
            for z in range(z_dim):
                y_true = signal_data[x, y, z, :]
                y_pred = signal_data_predicted[x, y, z, :]

                y_mean = np.mean(y_true)

                ss_total = np.sum((y_true - y_mean) ** 2)
                ss_residual = np.sum((y_true - y_pred) ** 2)

                # Avoid division by zero in voxels with no signal
                if ss_total == 0:
                    # If there's no variability, R^2 is 1 if predictions are perfect, otherwise 0
                    r2 = 1 if np.allclose(y_true, y_pred) else 0
                else:
                    r2 = 1 - (ss_residual / ss_total)

                r2_map[x, y, z] = r2

    return r2_map
