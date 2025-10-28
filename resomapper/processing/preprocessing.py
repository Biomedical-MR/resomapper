import os

import matplotlib
import matplotlib.pyplot as plt
import nibabel as nib
import numpy as np
import SimpleITK as sitk

from dipy.core.gradients import gradient_table
from dipy.denoise.adaptive_soft_matching import adaptive_soft_matching
from dipy.denoise.localpca import localpca, mppca
from dipy.denoise.nlmeans import nlmeans
from dipy.denoise.noise_estimate import estimate_sigma
from dipy.denoise.patch2self import patch2self
from dipy.denoise.pca_noise_estimate import pca_noise_estimate
from dipy.denoise.gibbs import gibbs_removal

# TODO: if we remove one of the nlmeans maybe this to remove one dependency
from skimage.restoration import denoise_nl_means


import resomapper.core.utils as ut
from resomapper.core.misc import auto_innited_logger as lggr

import warnings

warnings.filterwarnings("ignore")
matplotlib.use("TkAgg")


#### DENOISING FILTERS ####


def denoise(
    nifti_file_path, modality, output_folder, params=None, selected_filter=None
):

    if selected_filter is None:
        selected_filter = select_denoising_filter(modality)

    if params is None:
        check_params = True
    elif params == "default":
        params = None
        check_params = False
    else:
        check_params = False

    process_again = True

    while process_again:
        study_nii = nib.load(nifti_file_path)
        original_image = study_nii.get_fdata()

        if selected_filter == "n":
            denoised_image, params = non_local_means_denoising(
                original_image, params, check_params=check_params
            )
        elif selected_filter == "d":
            denoised_image, params = non_local_means_2_denoising(
                original_image, params, check_params=check_params
            )
        elif selected_filter == "a":
            denoised_image, params = ascm_denoising(
                original_image, params, check_params=check_params
            )
        elif selected_filter == "p":
            bval_fname = nifti_file_path.replace(".nii.gz", ".bval")
            bvals = np.loadtxt(bval_fname)
            denoised_image, params = patch2self_denoising(
                original_image, bvals, params, check_params=check_params
            )
        elif selected_filter == "l":
            bval_fname = nifti_file_path.replace(".nii.gz", ".bval")
            bvec_fname = nifti_file_path.replace(".nii.gz", ".bvec")
            bvals = np.loadtxt(bval_fname)
            bvecs = np.loadtxt(bvec_fname)
            gtab = gradient_table(bvals, bvecs)
            denoised_image, params = local_pca_denoising(
                original_image, gtab, params, check_params=check_params
            )
        elif selected_filter == "m":
            denoised_image, params = mp_pca_denoising(
                original_image, params, check_params=check_params
            )

        if check_params:
            save, process_again = show_denoised_output(original_image, denoised_image)
        else:
            save = True
            process_again = False

        if not process_again:
            if save:
                nii_ima = nib.Nifti1Image(
                    denoised_image, study_nii.affine, study_nii.header
                )
                denoised_nii_name = os.path.basename(nifti_file_path).replace(
                    ".nii.gz", "_preproc.nii.gz"
                )
                denoised_nii_output_path = os.path.join(
                    output_folder, denoised_nii_name
                )
                nib.save(nii_ima, denoised_nii_output_path)
                ut.rename_associated_files(denoised_nii_output_path)
            else:
                denoised_nii_output_path = nifti_file_path
        else:
            params = None
    return params, denoised_nii_output_path, selected_filter


def select_denoising_filter(modality):
    question = "Choose the denoising filter to apply."
    options = {
        "n": "Non-local means denoising.",
        "d": "Non-local means denoising. (2)",
        "a": "Adaptive Soft Coefficient Matching (ASCM) denoising.",
        # "l": "Local PCA denoising",
        # "m": "Marcenko-Pastur PCA denoising",
    }
    if modality == "DTI":
        options["p"] = "Patch2self denoising (for DWI)."
        options["l"] = "Local PCA denoising (for DWI)."
        options["m"] = "Marcenko-Pastur PCA denoising (for DWI)."

    return ut.ask_user_options(question, options)


def info_and_ask_denoising_params(filter_name, params):
    """Print a message indicating the selected filter and ask the user to input the
    neccesary parameters.

    Args:
        filter_name (str): Name of the selected filter.
        params (dict): Dictionary containing the parameter names along with a list
            that contains the predetermined value and a brief description

    Returns:
        dict: Dictionary containing the selected values for each parameter name.
    """

    print(f"\n{lggr.info}You have selected {filter_name}.\n")
    print(f"{lggr.ask}Please select the filtering parameters in the pop-up window.")
    return ut.ask_user_parameters(params)


def show_denoised_output(original_image, denoised_image, ask_user="Denoising"):
    """Display the denoised output and residuals of the denoising process.

    This method takes the original image and its denoised counterpart and displays
    them side by side along with the residual image obtained by computing
    the element-wise squared difference between the original and denoised images.
    A middle slice is shown.

    Args:
        original_image (numpy.ndarray): The original 3D or 4D image to be denoised.
        denoised_image (numpy.ndarray): The denoised version of the original image.

    Returns:
        bool: A boolean value indicating whether the user wants to change the
            denoising parameters.
    """

    sli = original_image.shape[2] // 2

    if len(original_image.shape) == 3:
        orig = original_image[:, :, sli]
        den = denoised_image[:, :, sli]
        gra = "-"
    else:
        gra = original_image.shape[2] // 2
        orig = original_image[:, :, sli, gra]
        den = denoised_image[:, :, sli, gra]

    # compute the residuals
    rms_diff = np.sqrt((orig - den) ** 2)

    fig1, ax = plt.subplots(
        1, 3, figsize=(12, 6), subplot_kw={"xticks": [], "yticks": []}
    )

    fig1.subplots_adjust(hspace=0.3, wspace=0.05)
    fig1.suptitle(f"Sample of residuals (slice {sli}, subslice {gra})")

    ax.flat[0].imshow(orig.T, cmap="gray", interpolation="none")
    ax.flat[0].set_title("Original")
    ax.flat[1].imshow(den.T, cmap="gray", interpolation="none")
    ax.flat[1].set_title("Denoised Output")
    ax.flat[2].imshow(rms_diff.T, cmap="gray", interpolation="none")
    ax.flat[2].set_title("Residuals")
    fig1.show()

    if ask_user == "Denoising":
        if ut.ask_user("Are you happy with the results?"):
            save = True
            process_again = False
        else:
            save = False
            process_again = ut.ask_user(
                "Do you want to change the parameters? (if not, no filtering will be applied)"
            )

    elif ask_user == "Gibbs":
        save = ut.ask_user("Do you want to keep the unringed image?")
        process_again = False
    else:
        save = True
        process_again = False
    plt.close(fig1)
    return save, process_again


#### DENOISING FILTERS ####

# TODO: check if we need thwo nlm


def non_local_means_denoising(image, params, check_params=True):
    """Apply non local means denoising to an image using specified parameters.
    This version uses the skimage library implementation of this filter.

    Args:
        image (numpy.ndarray): Input 3D/4D image array to be denoised.
        params (dict or None): Dictionary containing the denoising parameters to be
            used. If None, the user will be prompted to select the parameters.

    Returns:
        tuple: A tuple containing the denoised image and the selected denoising
            parameters.
    """

    parameters_nlm = {
        "patch_size": [3, "Size of patches used for denoising."],
        "patch_distance": [7, "Maximal search distance (pixels)."],
        "h": [4.5, "Cut-off distance (in gray levels)."],
    }
    if params is None and check_params:
        selection = info_and_ask_denoising_params(
            "non-local means denoising", parameters_nlm
        )
    elif params is None and not check_params:
        selection = {key: value[0] for key, value in parameters_nlm.items()}
    else:
        selection = params

    p_imas = []  # processed images
    p_serie = []

    print("\n    ... applying nlm1 denoising filter")

    if len(image.shape) == 4:
        for serie in np.moveaxis(image, -1, 0):
            for ima in np.moveaxis(serie, -1, 0):
                # denoise using non local means from skimage.restoration
                d_ima = denoise_nl_means(
                    ima,
                    patch_size=selection["patch_size"],
                    patch_distance=selection["patch_distance"],
                    h=selection["h"],
                    preserve_range=True,
                )
                p_serie.append(d_ima)
            p_imas.append(p_serie)
            p_serie = []
        r_imas = np.moveaxis(np.array(p_imas), [0, 1], [-1, -2])

    elif len(image.shape) == 3:  # Images like MT only have an image per slice
        for ima in np.moveaxis(image, -1, 0):
            # denoise using non local means from skimage.restoration
            d_ima = denoise_nl_means(
                ima,
                patch_size=selection["patch_size"],
                patch_distance=selection["patch_distance"],
                h=selection["h"],
                preserve_range=True,
            )
            p_imas.append(d_ima)
        r_imas = np.moveaxis(np.array(p_imas), 0, -1)

    return r_imas, selection


def non_local_means_2_denoising(image, params, check_params=True):
    """Apply non local means denoising to an image using specified parameters.
    This version uses Dipy's implementation of this filter.

    Args:
        image (numpy.ndarray): Input 3D/4D image array to be denoised.
        params (dict or None): Dictionary containing the denoising parameters to be
            used. If None, the user will be prompted to select the parameters.

    Returns:
        tuple: A tuple containing the denoised image and the selected denoising
            parameters.
    """

    parameters_nlm_2 = {
        "N_sigma": [0, ""],
        "patch_radius": [1, ""],
        "block_radius": [2, ""],
        "rician": [True, ""],
    }

    if params is None and check_params:
        selection = info_and_ask_denoising_params(
            "non-local means (2) denoising", parameters_nlm_2
        )
    elif params is None and not check_params:
        selection = {key: value[0] for key, value in parameters_nlm_2.items()}
    else:
        selection = params

    sigma = estimate_sigma(image, N=selection["N_sigma"])
    # Denoise using dipy's nlmeans filter
    print("\n    ... applying nlm2 denoising filter")
    return (
        nlmeans(
            image,
            sigma=sigma,
            # mask=mask,
            patch_radius=selection["patch_radius"],
            block_radius=selection["block_radius"],
            rician=selection["rician"],
        ),
        selection,
    )


def ascm_denoising(image, params, check_params=True):
    """Apply Adapative Soft Coefficient Matching denoising to an image using
    specified parameters.

    Args:
        image (numpy.ndarray): Input 3D/4D image array to be denoised.
        params (dict or None): Dictionary containing the denoising parameters to be
            used. If None, the user will be prompted to select the parameters.

    Returns:
        tuple: A tuple containing the denoised image and the selected denoising
            parameters.
    """

    parameters_ascm = {
        "N_sigma": [0, ""],
        "patch_radius_small": [1, ""],
        "patch_radius_large": [2, ""],
        "block_radius": [2, ""],
        "rician": [True, ""],
    }

    if params is None and check_params:
        selection = info_and_ask_denoising_params("ASCM denoising", parameters_ascm)
    elif params is None and not check_params:
        selection = {key: value[0] for key, value in parameters_ascm.items()}
    else:
        selection = params

    print("\n    ... applying ascm denoising filter")

    sigma = estimate_sigma(image, N=selection["N_sigma"])

    den_small = nlmeans(
        image,
        sigma=sigma,
        # mask=mask,
        patch_radius=selection["patch_radius_small"],
        block_radius=selection["block_radius"],
        rician=selection["rician"],
    )

    den_large = nlmeans(
        image,
        sigma=sigma,
        # mask=mask,
        patch_radius=selection["patch_radius_large"],
        block_radius=selection["block_radius"],
        rician=selection["rician"],
    )

    if len(image.shape) == 3:
        return adaptive_soft_matching(image, den_small, den_large, sigma), selection

    denoised_image = []
    for i in range(image.shape[-1]):
        denoised_vol = adaptive_soft_matching(
            image[:, :, :, i],
            den_small[:, :, :, i],
            den_large[:, :, :, i],
            sigma[i],
        )
        denoised_image.append(denoised_vol)

    denoised_image = np.moveaxis(np.array(denoised_image), 0, -1)
    return denoised_image, selection


def local_pca_denoising(image, gtab, params, check_params=True):
    """Apply local PCA denoising to the given image using specified parameters.

    Args:
        image (numpy.ndarray): Input 3D/4D image array to be denoised.
        gtab (numpy.ndarray): B-values and gradient directions associated with the
            input image.
        params (dict or None): Dictionary containing the denoising parameters to be
            used. If None, the user will be prompted to select the parameters.

    Returns:
        tuple: A tuple containing the denoised image and the selected denoising
            parameters.
    """

    parameters_lpca = {
        "correct_bias": [True, ""],
        "smooth": [3, ""],
        "tau_factor": [2.3, ""],
        "patch_radius": [2, ""],
    }
    if params is None and check_params:
        selection = info_and_ask_denoising_params(
            "local PCA denoising", parameters_lpca
        )
    elif params is None and not check_params:
        selection = {key: value[0] for key, value in parameters_lpca.items()}
    else:
        selection = params

    print("\n    ... applying lpca denoising filter")

    sigma = pca_noise_estimate(
        image,
        gtab,
        correct_bias=selection["correct_bias"],
        smooth=selection["smooth"],
    )
    return (
        localpca(
            image,
            sigma,
            tau_factor=selection["tau_factor"],
            patch_radius=selection["patch_radius"],
        ),
        selection,
    )


def mp_pca_denoising(image, params, check_params=True):
    """Apply Marcenko-Pastur PCA denoising to an image using specified parameters.

    Args:
        image (numpy.ndarray): Input 3D/4D image array to be denoised.
        params (dict or None): Dictionary containing the denoising parameters to be
            used. If None, the user will be prompted to select the parameters.

    Returns:
        tuple: A tuple containing the denoised image and the selected denoising
            parameters.
    """

    parameters_mp_pca = {
        "patch_radius": [2, ""],
    }
    if params is None and check_params:
        selection = info_and_ask_denoising_params(
            "Marcenko-Pastur PCA denoising", parameters_mp_pca
        )
    elif params is None and not check_params:
        selection = {key: value[0] for key, value in parameters_mp_pca.items()}
    else:
        selection = params

    print("\n    ... applying mppca denoising filter")

    return mppca(image, patch_radius=selection["patch_radius"]), selection


def patch2self_denoising(image, bvals, params, check_params=True):
    """Apply patch2self denoising to the given image using specified parameters.

    Args:
        image (numpy.ndarray): Input 3D/4D image array to be denoised.
        bvals (numpy.ndarray): B-values associated with the input image.
        params (dict or None): Dictionary containing the denoising parameters to be
            used. If None, the user will be prompted to select the parameters.

    Returns:
        tuple: A tuple containing the denoised image and the selected denoising
            parameters.
    """

    parameters_p2s = {
        "model": ["ols", ""],
        "shift_intensity": [True, ""],
        "clip_negative_vals": [False, ""],
        "b0_threshold": [50, ""],
    }
    if params is None and check_params:
        selection = info_and_ask_denoising_params(
            "patch2self denoising", parameters_p2s
        )
    elif params is None and not check_params:
        selection = {key: value[0] for key, value in parameters_p2s.items()}
    else:
        selection = params

    print("\n    ... applying p2s denoising filter")

    return (
        patch2self(
            image,
            bvals,
            model=selection["model"],
            shift_intensity=selection["shift_intensity"],
            clip_negative_vals=selection["clip_negative_vals"],
            b0_threshold=selection["b0_threshold"],
        ),
        selection,
    )


#### GIBBS REMOVAL ####


def gibbs_suppress(nifti_file_path, unringed_nii_output_path=None, check_params=True):
    study_nii = nib.load(nifti_file_path)
    original_img = study_nii.get_fdata()
    unringed_img = gibbs_removal(original_img, inplace=False)
    if check_params:
        keep_unringed, _ = show_denoised_output(
            original_img, unringed_img, ask_user="Gibbs"
        )
    else:
        keep_unringed = True

    if keep_unringed:
        if unringed_nii_output_path is None:
            if "_preproc" not in nifti_file_path:
                unringed_nii_output_path = nifti_file_path.replace(
                    ".nii.gz", "_preproc.nii.gz"
                )
                ut.rename_associated_files(unringed_nii_output_path)
            else:
                unringed_nii_output_path = nifti_file_path

        nii_ima = nib.Nifti1Image(unringed_img, study_nii.affine, study_nii.header)
        nib.save(nii_ima, unringed_nii_output_path)

    else:
        unringed_nii_output_path = nifti_file_path

    return keep_unringed, unringed_nii_output_path


#### BIAS FIELD CORRECTION ####


def show_bias_field_correction_ask(original_image, corrected_image, log_bias_field):

    sli = original_image.shape[2] // 2

    if len(original_image.shape) == 3:
        orig = original_image[:, :, sli]
        den = corrected_image[:, :, sli]
        biasf = log_bias_field[:, :, sli]
        gra = "-"
    else:
        gra = original_image.shape[2] // 2
        orig = original_image[:, :, sli, gra]
        den = corrected_image[:, :, sli, gra]
        if len(log_bias_field.shape) == 3:
            biasf = log_bias_field[:, :, sli]
        else:
            biasf = log_bias_field[:, :, sli, gra]

    fig1, ax = plt.subplots(
        1, 3, figsize=(12, 6), subplot_kw={"xticks": [], "yticks": []}
    )

    fig1.subplots_adjust(hspace=0.3, wspace=0.05)
    fig1.suptitle(f"Sample of bias-field corrected image (slice {sli}, subslice {gra})")

    ax.flat[0].imshow(orig.T, cmap="gray", interpolation="none")
    ax.flat[0].set_title("Original")
    ax.flat[1].imshow(den.T, cmap="gray", interpolation="none")
    ax.flat[1].set_title("Corrected")
    ax.flat[2].imshow(biasf.T, cmap="gray", interpolation="none")
    ax.flat[2].set_title("Bias field")
    fig1.show()

    if ut.ask_user("Are you happy with the results?"):
        save = True
        reprocess = False
    else:
        save = False
        reprocess = ut.ask_user(
            "Do you want to change the parameters? (if not, no filtering will be applied)"
        )

    plt.close(fig1)
    return save, reprocess


def n4_bias_field_correct(
    nifti_file_path, corrected_nii_output_path=None, params=None, check_params=True
):
    parameters_n4bias = {
        "shrink_factor": [1, "(1 for none)"],
        "number_fitting_levels": [4, ""],
        "number_of_iterations": [50, ""],
        "save_bias_field": [False, ""],
        "use_first_field_only_4d": [True, ""],
    }

    result_ok = False

    while not result_ok:

        if params is None and check_params:
            selection = info_and_ask_denoising_params(
                "N4 bias field correction", parameters_n4bias
            )
        elif params is None and not check_params:
            selection = {key: value[0] for key, value in parameters_n4bias.items()}
        else:
            selection = params

        original_img = sitk.ReadImage(nifti_file_path)

        if len(original_img.GetSize()) == 4:
            original_img_4d = original_img
            original_img = original_img[:, :, :, 0]
        else:
            original_img_4d = False

        otsu_mask = sitk.OtsuThreshold(original_img, 0, 1, 200)

        if selection["shrink_factor"] > 1:
            original_img_shrink = sitk.Shrink(
                original_img, [selection["shrink_factor"]] * original_img.GetDimension()
            )
            otsu_mask_shrink = sitk.Shrink(
                otsu_mask, [selection["shrink_factor"]] * original_img.GetDimension()
            )
        else:
            original_img_shrink = original_img
            otsu_mask_shrink = otsu_mask

        corrector = sitk.N4BiasFieldCorrectionImageFilter()
        corrector.SetMaximumNumberOfIterations(
            [int(selection["number_of_iterations"])]
            * selection["number_fitting_levels"]
        )

        _ = corrector.Execute(original_img_shrink, otsu_mask_shrink)
        log_bias_field = corrector.GetLogBiasFieldAsImage(original_img)
        corrected_image_fullres = original_img / sitk.Exp(log_bias_field)

        if original_img_4d is not False:
            corrected_image_list = []
            if selection["use_first_field_only_4d"]:
                for i in range(original_img_4d.GetSize()[-1]):
                    corrected_image_list.append(
                        original_img_4d[:, :, :, i] / sitk.Exp(log_bias_field)
                    )
                corrected_image_fullres = sitk.JoinSeries(corrected_image_list)
            else:
                log_fields_list = []
                for i in range(original_img_4d.GetSize()[-1]):
                    if selection["shrink_factor"] > 1:
                        img_shrink = sitk.Shrink(
                            original_img_4d[:, :, :, i],
                            [selection["shrink_factor"]] * original_img.GetDimension(),
                        )
                    else:
                        img_shrink = original_img_4d[:, :, :, i]
                    _ = corrector.Execute(img_shrink, otsu_mask_shrink)
                    log_bias_field = corrector.GetLogBiasFieldAsImage(original_img)
                    corrected_image_list.append(
                        original_img_4d[:, :, :, i] / sitk.Exp(log_bias_field)
                    )
                    log_fields_list.append(log_bias_field)
                corrected_image_fullres = sitk.JoinSeries(corrected_image_list)
                log_bias_field = sitk.JoinSeries(log_fields_list)

        if check_params:
            if original_img_4d is False or selection["use_first_field_only_4d"]:
                save, reprocess = show_bias_field_correction_ask(
                    np.swapaxes(sitk.GetArrayFromImage(original_img), 0, 2),
                    np.swapaxes(sitk.GetArrayFromImage(corrected_image_fullres), 0, 2),
                    np.swapaxes(sitk.GetArrayFromImage(log_bias_field), 0, 2),
                )
            else:
                save, reprocess = show_bias_field_correction_ask(
                    np.swapaxes(sitk.GetArrayFromImage(original_img), 0, 2),
                    np.swapaxes(sitk.GetArrayFromImage(corrected_image_fullres), 0, 2),
                    np.swapaxes(
                        sitk.GetArrayFromImage(log_bias_field[:, :, :, 0]), 0, 2
                    ),
                )
            if save or not reprocess:
                result_ok = True
        else:
            save = True
            result_ok = True

    if save:
        if corrected_nii_output_path is None:
            if "_preproc" not in nifti_file_path:
                corrected_nii_output_path = nifti_file_path.replace(
                    ".nii.gz", "_preproc.nii.gz"
                )
                ut.rename_associated_files(corrected_nii_output_path)
            else:
                corrected_nii_output_path = nifti_file_path
        sitk.WriteImage(corrected_image_fullres, corrected_nii_output_path)
        if selection["save_bias_field"]:
            bias_field_nii_path = corrected_nii_output_path.replace(
                ".nii.gz", "_biasf.nii.gz"
            )
            sitk.WriteImage(log_bias_field, bias_field_nii_path)
    else:
        corrected_nii_output_path = nifti_file_path

    return save, corrected_nii_output_path, selection
