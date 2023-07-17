import tkinter as tk
import warnings
from math import trunc

import matplotlib.pyplot as plt
import nibabel as nib
import numpy as np

# from scipy.ndimage import rotate
from dipy.core.gradients import gradient_table
from dipy.denoise.adaptive_soft_matching import adaptive_soft_matching
from dipy.denoise.localpca import localpca, mppca
from dipy.denoise.nlmeans import nlmeans
from dipy.denoise.noise_estimate import estimate_sigma

# from dipy.denoise.non_local_means import non_local_means
from dipy.denoise.patch2self import patch2self
from dipy.denoise.pca_noise_estimate import pca_noise_estimate
from skimage.restoration import denoise_nl_means
from skimage.transform import rotate

from resomapper.utils import Headermsg as hmg
from resomapper.utils import ask_user, ask_user_options

warnings.filterwarnings("ignore")


######################################### OLD ##########################################
def get_preprocessing_params():
    """Show a window to select the parameters to perform non local means denoising.

    Returns:
        list: Filtering parameters list [search distance, window size, h value]
    """
    print(f"\n{hmg.ask}Indica los parámetros de preprocesado en la ventana emergente.")

    root = tk.Tk()
    root.title("resomapper")

    # declaring string variable for storing values
    patch_s = tk.StringVar()
    patch_d = tk.StringVar()
    h = tk.StringVar()

    # defining a function that will get the entries
    def get_input():
        global entries
        try:
            entry_a = int(patch_d_entry.get())
            entry_b = int(patch_s_entry.get())
            entry_c = float(h_entry.get())
            entries = [entry_a, entry_b, entry_c]
            root.destroy()
            root.quit()
        except ValueError:
            print(
                f"\n{hmg.error}Has introducido un valor no válido. Inténtalo de nuevo."
            )

    # creating a labels
    patch_s_label = tk.Label(
        root, text="Tamaño de la región: ", font=("calibre", 10, "bold")
    )
    patch_d_label = tk.Label(
        root, text="Distancia de búsqueda: ", font=("calibre", 10, "bold")
    )
    h_label = tk.Label(root, text="Valor de H: ", font=("calibre", 10, "bold"))

    # creating entries for inputs
    patch_s_entry = tk.Entry(root, textvariable=patch_s, font=("calibre", 10, "normal"))
    patch_d_entry = tk.Entry(root, textvariable=patch_d, font=("calibre", 10, "normal"))
    h_entry = tk.Entry(root, textvariable=h, font=("calibre", 10, "normal"))

    # setting default values
    patch_s_entry.insert(0, "3")
    patch_d_entry.insert(0, "7")
    h_entry.insert(0, "4.5")

    # creating a button
    sub_btn = tk.Button(root, text="Aceptar", command=get_input)

    # placing the label and entry in the required position using grid
    patch_s_label.grid(row=0, column=0)
    patch_s_entry.grid(row=0, column=1)
    patch_d_label.grid(row=1, column=0)
    patch_d_entry.grid(row=1, column=1)
    h_label.grid(row=2, column=0)
    h_entry.grid(row=2, column=1)
    sub_btn.grid(row=3, column=0)

    root.mainloop()
    try:
        return entries
    except NameError:
        return ""


################################### ^^ OLD ^^ ##########################################


def ask_user_parameters(parameter_dict):
    root = tk.Tk()
    root.title("resomapper")

    def submit():
        global values
        values = {}
        for parameter, info in parameter_dict.items():
            value = entry_boxes[parameter].get()
            predetermined_value = info[0]
            value_type = type(predetermined_value)
            try:
                value = value_type(value)
                if value_type == str and not value:
                    raise ValueError
                values[parameter] = value
            except (ValueError, TypeError):
                error_label.config(text=f"Invalid input for {parameter}!")
                return
        root.destroy()

        # return values  # Return parameter selection

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
                    self.show_denoised_output(original_image, denoised_image)
                    process_again = ask_user(
                        "¿Deseas cambiar los parámetros de filtrado?"
                    )
                    plt.close()

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
        """Returns data in size x_dim x y_dim x num slices x rep times"""

        study_full_path = list(study_path.glob("*.nii.gz"))[scan]

        study = nib.load(study_full_path)
        self.study_full_path = study_full_path
        return study

    def save_nii(self, study, array):
        nii_ima = nib.Nifti1Image(array, study.affine, study.header)
        nib.save(nii_ima, str(self.study_full_path))

    def select_denoising_parameters(self):
        pass

    def show_denoised_output(self, original_image, denoised_image):
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

    ############################### Denoising methods ##################################

    def non_local_means_denoising(self, image, params):
        print(f"\n{hmg.info}Has seleccionado el filtro non-local means.\n")
        print(f"{hmg.ask}Selecciona los parámetros en la ventana emergente.")

        parameters_nlm = {
            "patch_size": [3, "Size of patches used for denoising."],
            "patch_distance": [7, "Maximal search distance (pixels)."],
            "h": [4.5, "Cut-off distance (in gray levels)."],
        }

        selection = ask_user_parameters(parameters_nlm) if params is None else params

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
        print(f"\n{hmg.info}Has seleccionado el filtro non-local means (version 2).\n")
        print(f"{hmg.ask}Selecciona los parámetros en la ventana emergente.")

        parameters_nlm_2 = {
            "N_sigma": [0, ""],
            "patch_radius": [1, ""],
            "block_radius": [2, ""],
            "rician": [True, ""],
        }
        selection = ask_user_parameters(parameters_nlm_2) if params is None else params

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
            params,
        )

    def ascm_denoising(self, image, params):
        print(f"\n{hmg.info}Has seleccionado el filtro ASCM.\n")
        print(f"{hmg.ask}Selecciona los parámetros en la ventana emergente.")

        parameters_ascm = {
            "N_sigma": [0, ""],
            "patch_radius_small": [1, ""],
            "patch_radius_large": [2, ""],
            "block_radius": [2, ""],
            "rician": [True, ""],
        }
        selection = ask_user_parameters(parameters_ascm) if params is None else params

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
            return adaptive_soft_matching(image, den_small, den_large, sigma), params

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
        return denoised_image, params

    def local_pca_denoising(self, image, gtab, params):
        print(f"\n{hmg.info}Has seleccionado el filtro local PCA.\n")
        print(f"{hmg.ask}Selecciona los parámetros en la ventana emergente.")

        parameters_lpca = {
            "correct_bias": [True, ""],
            "smooth": [3, ""],
            "tau_factor": [2.3, ""],
            "patch_radius": [2, ""],
        }
        selection = ask_user_parameters(parameters_lpca) if params is None else params

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
            params,
        )

    def mp_pca_denoising(self, image, params):
        print(f"\n{hmg.info}Has seleccionado el filtro Marcenko-Pasteur PCA.\n")
        print(f"{hmg.ask}Selecciona los parámetros en la ventana emergente.")

        parameters_mp_pca = {
            "patch_radius": [2, ""],
        }
        selection = ask_user_parameters(parameters_mp_pca) if params is None else params
        return mppca(image, patch_radius=selection["patch_radius"]), params

    def patch2self_denoising(self, image, bvals, params):
        print(f"\n{hmg.info}Has seleccionado el filtro patch2self.\n")
        print(f"{hmg.ask}Selecciona los parámetros en la ventana emergente.")

        parameters_p2s = {
            "model": ["ols", ""],
            "shift_intensity": [True, ""],
            "clip_negative_vals": [False, ""],
            "b0_threshold": [50, ""],
        }
        selection = ask_user_parameters(parameters_p2s) if params is None else params

        return (
            patch2self(
                image,
                bvals,
                model=selection["model"],
                shift_intensity=selection["shift_intensity"],
                clip_negative_vals=selection["clip_negative_vals"],
                b0_threshold=selection["b0_threshold"],
            ),
            params,
        )


######################################### OLD ##########################################
class Preprocessing:
    def __init__(self, studies_paths):
        self.studies_paths = studies_paths

    def load_nii(self, study_path, is_mt_study=False, scan=0):
        """Returns data in size x_dim x y_dim x num slices x rep times"""

        study_full_path = list(study_path.glob("*.nii.gz"))[scan]

        study = nib.load(study_full_path)
        self.study_full_path = study_full_path
        return study

    def denoise(self, image, patch_size=3, patch_distance=7, h=4.5):
        return denoise_nl_means(
            image, patch_size=patch_size, patch_distance=patch_distance, h=h
        )

    def save_nii(self, study, array):
        nii_ima = nib.Nifti1Image(array, study.affine, study.header)
        nib.save(nii_ima, str(self.study_full_path))

    def preprocess(self):
        preprocess_again = True

        while preprocess_again:
            denoise_params = get_preprocessing_params()
            if denoise_params == "":
                print(f"\n{hmg.error}No has seleccionado ningún parámetro.")
                exit()

            for study in self.studies_paths:
                if study.parts[-1].split("_")[0] == "MT":
                    n_scans = len(list(study.glob("*.nii.gz")))
                    is_mt_study = True
                else:
                    n_scans = 1
                    is_mt_study = False

                for i in range(n_scans):
                    p_imas = []  # processed images
                    p_serie = []

                    study_nii = self.load_nii(study, is_mt_study, i)
                    study_data = study_nii.get_data()
                    if len(study_data.shape) == 4:
                        for serie in np.moveaxis(study_data, -1, 0):
                            for ima in np.moveaxis(serie, -1, 0):
                                # denoise using non local means
                                d_ima = self.denoise(
                                    ima,
                                    denoise_params[0],
                                    denoise_params[1],
                                    denoise_params[2],
                                )
                                p_serie.append(d_ima)
                            p_imas.append(p_serie)
                            p_serie = []
                        r_imas = np.moveaxis(np.array(p_imas), [0, 1], [-1, -2])
                    elif len(study_data.shape) == 3:  # Caso de la MT - added by Raquel
                        for ima in np.moveaxis(study_data, -1, 0):
                            # denoise using non local means
                            d_ima = self.denoise(
                                ima,
                                denoise_params[0],
                                denoise_params[1],
                                denoise_params[2],
                            )
                            p_imas.append(d_ima)
                        r_imas = np.moveaxis(np.array(p_imas), 0, -1)
                    else:
                        print(
                            f"{hmg.error}Dimensiones de archivo de imagen no esperadas."
                        )
                        exit()

                    if (is_mt_study and (i == 0)) or not is_mt_study:
                        fig, ax = plt.subplots(1, 2)
                        n_slc = np.shape(study_data)[2]
                        if len(study_data.shape) == 4:
                            ax[0].imshow(
                                rotate(study_data[:, :, trunc(n_slc / 2), 0], 270),
                                cmap="gray",
                            )
                            ax[1].imshow(
                                rotate(r_imas[:, :, trunc(n_slc / 2), 0], 270),
                                cmap="gray",
                            )
                        else:
                            ax[0].imshow(
                                rotate(study_data[:, :, trunc(n_slc / 2)], 270),
                                cmap="gray",
                            )
                            ax[1].imshow(
                                rotate(r_imas[:, :, trunc(n_slc / 2)], 270), cmap="gray"
                            )

                        ax[0].set_title("Original")
                        ax[1].set_title("Preprocesada")
                        ax[0].axis("off")
                        ax[1].axis("off")

                        fig.show()

                        preprocess_again = ask_user("¿Desea repetir el preprocesado?")

                    if not preprocess_again:
                        self.save_nii(study_nii, r_imas)

        print(f"\n{hmg.info}Preprocesado completado. Va a comenzar el procesamiento.")


################################### ^^ OLD ^^ ##########################################
