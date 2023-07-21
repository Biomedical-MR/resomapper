import tkinter as tk
import warnings

import matplotlib
import matplotlib.pyplot as plt
import nibabel as nib
import numpy as np
from dipy.core.gradients import gradient_table
from dipy.denoise.adaptive_soft_matching import adaptive_soft_matching
from dipy.denoise.localpca import localpca, mppca
from dipy.denoise.nlmeans import nlmeans
from dipy.denoise.noise_estimate import estimate_sigma
from dipy.denoise.patch2self import patch2self
from dipy.denoise.pca_noise_estimate import pca_noise_estimate
from skimage.restoration import denoise_nl_means

from resomapper.utils import Headermsg as hmg
from resomapper.utils import ask_user, ask_user_options

warnings.filterwarnings("ignore")
matplotlib.use("TkAgg")


def ask_user_parameters(parameter_dict):
    """Select values for different parameters in an emergent window. If a new value is
    selected it has to be of the same class as the predetermined value.

    Args:
        parameter_dict (dict): Dictionary containing the name of the different
            parameters as keys, along with a list containing the predetermined value for
            each one and a brief description.

    Returns:
        dict: Dictionary containing the selected values for each parameter name.
    """
    root = tk.Tk()
    root.title("resomapper")

    values = {}

    def submit():
        nonlocal values

        for parameter, info in parameter_dict.items():
            value = entry_boxes[parameter].get()
            predetermined_value = info[0]
            value_type = type(predetermined_value)
            try:
                if value_type == bool:
                    # For boolean types, check if the input is 'True' or 'False'
                    value = str(value).lower()
                    if value in ["true", "1"]:
                        value = True
                    elif value in ["false", "0"]:
                        value = False
                    else:
                        raise ValueError
                else:
                    value = value_type(value)

                if value_type == str and not value:
                    raise ValueError
                values[parameter] = value

            except (ValueError, TypeError):
                error_label.config(text=f"Invalid input for {parameter}!")
                return

        root.destroy()
        root.quit()

    entry_boxes = {}
    for parameter, info in parameter_dict.items():
        label_text = f"[{parameter}] {info[1]}"
        label = tk.Label(root, text=label_text)
        label.pack(padx=50, pady=(10, 0))
        entry_box = tk.Entry(root)
        entry_box.insert(0, info[0])  # Set predetermined value as default
        entry_box.pack()
        entry_boxes[parameter] = entry_box

    error_label = tk.Label(root, text="", fg="red")
    error_label.pack()

    submit_button = tk.Button(root, text="Aceptar", command=submit)
    submit_button.pack(pady=20)

    root.mainloop()
    try:
        return values
    except NameError:
        print(
            f"\n\n{hmg.error}No has seleccionado los parámetros de filtrado. "
            "Saliendo del programa."
        )
        exit()


class Denoising:
    def __init__(self, study_path):
        self.study_path = study_path
        self.study_name = study_path.parts[-1]

    def denoise(self):
        selected_filter = self.select_denoising_filter()

        if self.study_name.startswith("MT"):
            n_scans = len(list(self.study_path.glob("*.nii.gz")))
        else:
            n_scans = 1

        process_again = True

        while process_again:
            params = None
            for i in range(n_scans):
                study_nii = self.load_nii(self.study_path, i)
                original_image = study_nii.get_data()

                if selected_filter == "n":
                    denoised_image, params = self.non_local_means_denoising(
                        original_image, params
                    )
                elif selected_filter == "d":
                    denoised_image, params = self.non_local_means_2_denoising(
                        original_image, params
                    )
                elif selected_filter == "a":
                    denoised_image, params = self.ascm_denoising(original_image, params)
                elif selected_filter == "g":
                    pass
                elif selected_filter == "p":
                    bval_fname = list(self.study_path.glob("*DwEffBval.txt"))[0]
                    bvals = np.loadtxt(bval_fname)
                    denoised_image, params = self.patch2self_denoising(
                        original_image, bvals, params
                    )
                elif selected_filter == "l":
                    bval_fname = list(self.study_path.glob("*DwEffBval.txt"))[0]
                    bvec_fname = list(self.study_path.glob("*DwGradVec.txt"))[0]
                    bvals = np.loadtxt(bval_fname)
                    bvecs = np.loadtxt(bvec_fname)
                    gtab = gradient_table(bvals, bvecs)
                    denoised_image, params = self.local_pca_denoising(
                        original_image, gtab, params
                    )
                elif selected_filter == "m":
                    denoised_image, params = self.mp_pca_denoising(
                        original_image, params
                    )

                if i == 0:
                    process_again = self.show_denoised_output(
                        original_image, denoised_image
                    )

                if not process_again:
                    self.save_nii(study_nii, denoised_image)

    def select_denoising_filter(self):
        question = "Elige el filtro que deseas aplicar."
        options = {
            "n": "Non-local means denoising.",
            "d": "Non-local means denoising. (2)",
            "a": "Adaptive Soft Coefficient Matching (ASCM) denoising.",
            # "g": "Gibbs artifacts reduction.",
        }
        if self.study_name.startswith("DT"):
            options["p"] = "Patch2self denoising (for DWI)."
            options["l"] = "Local PCA denoising (for DWI)."
            options["m"] = "Marcenko-Pastur PCA denoising (for DWI)."

        return ask_user_options(question, options)

    def load_nii(self, study_path, scan=0):
        """Load a NIfTI image from the specified study path and return its data.

        This function loads a NIfTI image file located in the given `study_path`.
        If multiple NIfTI files are found  in the directory, the `scan` parameter can be
        used to select a specific file based on its index.

        Args:
            study_path (Path): The path to the directory containing the NIfTI files.
            scan (int, optional): Index of the NIfTI file to be loaded in case multiple
                files are found. Defaults to 0.

        Returns:
            nib.nifti1.Nifti1Image: The loaded NIfTI image object.
        """

        study_full_path = list(study_path.glob("*.nii.gz"))[scan]

        study = nib.load(study_full_path)
        self.study_full_path = study_full_path
        return study

    def save_nii(self, study, array):
        """Save a NIfTI image with the specified data using the study information.

        The NIfTI image is saved in the same path as the loaded study with the same
        filename.

        Args:
            study (nib.nifti1.Nifti1Image): The NIfTI image object from which to extract
                the affine transformation and header information.
            array (numpy.ndarray): The data to be stored in the new NIfTI image.
        """
        nii_ima = nib.Nifti1Image(array, study.affine, study.header)
        nib.save(nii_ima, str(self.study_full_path))

    def info_and_ask_denoising_params(self, filter_name, params):
        """Print a message indicating the selected filter and ask the user to input the
        neccesary parameters.

        Args:
            filter_name (str): Name of the selected filter.
            params (dict): Dictionary containing the parameter names along with a list
                that contains the predetermined value and a brief description

        Returns:
            dict: Dictionary containing the selected values for each parameter name.
        """

        print(f"\n{hmg.info}Has seleccionado el filtro {filter_name} means.\n")
        print(f"{hmg.ask}Selecciona los parámetros en la ventana emergente.")
        return ask_user_parameters(params)

    def show_denoised_output(self, original_image, denoised_image):
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

        ax.flat[0].imshow(orig.T, cmap="gray", interpolation="none")
        ax.flat[0].set_title("Original")
        ax.flat[1].imshow(den.T, cmap="gray", interpolation="none")
        ax.flat[1].set_title("Denoised Output")
        ax.flat[2].imshow(rms_diff.T, cmap="gray", interpolation="none")
        ax.flat[2].set_title("Residuals")
        fig1.show()

        process_again = ask_user("¿Deseas cambiar los parámetros de filtrado?")
        plt.close(fig1)
        return process_again

    ############################### Denoising methods ##################################

    def non_local_means_denoising(self, image, params):
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
        if params is None:
            selection = self.info_and_ask_denoising_params(
                "non-local means", parameters_nlm
            )
        else:
            selection = params

        p_imas = []  # processed images
        p_serie = []

        if len(image.shape) == 4:
            for serie in np.moveaxis(image, -1, 0):
                for ima in np.moveaxis(serie, -1, 0):
                    # denoise using non local means
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
                # denoise using non local means
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

    def non_local_means_2_denoising(self, image, params):
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
        if params is None:
            selection = self.info_and_ask_denoising_params(
                "non-local means (v2)", parameters_nlm_2
            )
        else:
            selection = params

        sigma = estimate_sigma(image, N=selection["N_sigma"])
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

    def ascm_denoising(self, image, params):
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
        if params is None:
            selection = self.info_and_ask_denoising_params("ASCM", parameters_ascm)
        else:
            selection = params

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

    def local_pca_denoising(self, image, gtab, params):
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
        if params is None:
            selection = self.info_and_ask_denoising_params("local PCA", parameters_lpca)
        else:
            selection = params

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

    def mp_pca_denoising(self, image, params):
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
        if params is None:
            selection = self.info_and_ask_denoising_params(
                "Marcenko-Pastur PCA", parameters_mp_pca
            )
        else:
            selection = params

        return mppca(image, patch_radius=selection["patch_radius"]), selection

    def patch2self_denoising(self, image, bvals, params):
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
        if params is None:
            selection = self.info_and_ask_denoising_params("patch2self", parameters_p2s)
        else:
            selection = params

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
