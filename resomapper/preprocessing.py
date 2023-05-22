import tkinter as tk
import warnings
from math import trunc
from tkinter.messagebox import askyesno

import matplotlib.pyplot as plt
import nibabel as nib
import numpy as np

# from scipy.ndimage import rotate
from skimage.restoration import denoise_nl_means
from skimage.transform import rotate

from resomapper.utils import Headermsg as hmg  # Added by Raquel
from resomapper.utils import ask_user

warnings.filterwarnings("ignore")


def get_preprocessing_params():
    print(f"\n{hmg.ask}Indica los parámetros de preprocesado en la ventana emergente.")

    root = tk.Tk()
    root.title("MyX")

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


def ask_yes_no_preprocessing():
    """Creates a window to ask a question that has a yes/no answer."""

    warnings.filterwarnings("ignore")

    root = tk.Tk()
    root.withdraw()
    answer = askyesno(title="MyX", message="¿Quieres realizar un preprocesado?")
    root.destroy()
    # añadir root.quit para que funcione (creo)

    root.mainloop()

    return answer


def ask_yes_no_mask():
    """Creates a window to ask a question that has a yes/no answer."""
    warnings.filterwarnings("ignore")

    root = tk.Tk()
    root.withdraw()
    msg = "¿Quieres reutilizar la última máscara hecha para este sujeto?"
    answer = askyesno(title="MyX", message=msg)
    root.destroy()

    root.mainloop()

    return answer


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
