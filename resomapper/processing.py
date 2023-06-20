import glob
import os
import re
import shutil
import tkinter as tk
import warnings
from pathlib import Path

import dipy.reconst.dti as dti
import matplotlib.cm as cm
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from dipy.core.gradients import gradient_table
from dipy.core.sphere import Sphere
from dipy.io.gradients import read_bvals_bvecs
from dipy.io.image import load_nifti, save_nifti
from dipy.reconst.dti import (
    _nlls_err_func,
    apparent_diffusion_coef,
    fractional_anisotropy,
)

import resomapper.dwi.adcm as adcm
from resomapper.myrelax import getT1TR, getT2T2star
from resomapper.utils import Headermsg as hmg
from resomapper.utils import ask_user, ask_user_options, check_shapes

warnings.filterwarnings("ignore")


###############################################################################
# MT PROCESSING
###############################################################################
class MTProcessor:
    def __init__(
        self, mt_study_path: str, mask_path: str, path_mt="", path_m0=""
    ) -> None:
        self.mt_study_path = mt_study_path
        self.mask_path = mask_path
        self.path_mt = path_mt
        self.path_m0 = path_m0

        self.rename_mt_on()
        self.get_associated_mt_off()
        self.select_MT_acq()

    def rename_mt_on(self):
        for f in list(self.mt_study_path.glob("*.nii.gz")):
            new_filename = f.parts[-1].replace("procesado", "procesado_MT")
            shutil.move(os.path.join(f), os.path.join(self.mt_study_path, new_filename))

    def get_associated_mt_off(self):
        """Gets the sutdy path of the MT off .nii file."""

        study_path = Path(
            str(self.mt_study_path)
            .replace("procesados", "convertidos")
            .replace("procesado", "convertido")
            .replace("MT", "M0")
        )
        study_path = Path("/".join(self.mt_study_path.parts[:-1]))
        study_path = Path(
            str(study_path)
            .replace("procesados", "convertidos")
            .replace("procesado", "convertido")
        )
        study_path = list(study_path.glob("M0*"))[0]
        for f in list(study_path.glob("*.nii.gz")):
            new_filename = f.parts[-1].replace("convertido", "procesado_M0")
            shutil.copy(os.path.join(f), os.path.join(self.mt_study_path, new_filename))
        # return study_path

    def select_MT_acq(self):
        # n_mt = int(len(list(self.mt_study_path.glob("*.nii.gz"))) / 2)
        n_mt = len(list(self.mt_study_path.glob("*.nii.gz"))) // 2

        if n_mt == 1:
            mt_folders_list = [1]
        else:
            print(
                f"\n{hmg.warn}Has adquirido imágenes de MT con diferentes slopes para "
                f"este estudio ({n_mt})."
            )

            input_ready = False
            while not input_ready:
                mt_folders_input = input(
                    f"\n{hmg.ask}Indica el número de la carpeta de adquisición que "
                    f"desas procesar (entre 1 y {n_mt}). "
                    "Si deseas procesar más de una carpeta, introduce los diferentes "
                    f'números separados por ",".\n{hmg.pointer}'
                )
                mt_folders_input = mt_folders_input.split(",")
                try:
                    mt_folders_list = [int(x.strip()) for x in mt_folders_input]
                    input_ready = True
                    for number in mt_folders_list:
                        if (number > n_mt) or (number < 1):
                            print(
                                f"\n{hmg.error}Por favor, introduce números entre "
                                f"1 y {n_mt}."
                            )
                            input_ready = False
                            break
                except Exception:
                    print(
                        f"\n{hmg.error}Por favor, introduce sólo números separados por "
                        '"," (si hay más de uno).'
                    )

        self.n_mt_folders = n_mt
        self.selected_mt_folders_list = mt_folders_list

    def check_MT_data(self):
        ok_masks_list = []
        for i in self.selected_mt_folders_list:
            if self.n_mt_folders == 1:
                f_mton_path = list(self.mt_study_path.glob("procesado_MT_*.nii.gz"))[0]
                f_mtoff_path = list(self.mt_study_path.glob("procesado_M0_*.nii.gz"))[0]
                print(f"\n{hmg.info}Comprobando la máscara.")
            else:
                subscan_index = i - 1
                f_mton_path = list(
                    self.mt_study_path.glob(
                        f"procesado_MT_*subscan_{subscan_index}.nii*"
                    )
                )[0]
                f_mtoff_path = list(
                    self.mt_study_path.glob(
                        f"procesado_M0_*subscan_{subscan_index}.nii*"
                    )
                )[0]
                print(f"\n{hmg.info}Comprobando la máscara (carpeta {i}).")

            ok_masks_list.extend(
                (
                    check_shapes(f_mton_path, self.mask_path),
                    check_shapes(f_mtoff_path, self.mask_path),
                )
            )
        return all(ok_masks_list)

    def compute_MT_map(self, mton_image: np.array, mtoff_image: np.array):
        """Computes the formula required to get ratio MT map."""

        mt_map = 100 * (1 - (mton_image / mtoff_image))
        mt_map[mt_map < 0] = 0

        return mt_map

    def process_MT(self):
        """Generates ratio MT maps. Saves map as a nifti file and
        saves heatmaps as .png images."""

        for i in self.selected_mt_folders_list:
            if self.n_mt_folders == 1:
                f_mton_path = list(self.mt_study_path.glob("procesado_MT_*.nii.gz"))[0]
                f_mtoff_path = list(self.mt_study_path.glob("procesado_M0_*.nii.gz"))[0]
            else:
                subscan_index = i - 1
                f_mton_path = list(
                    self.mt_study_path.glob(
                        f"procesado_MT_*subscan_{subscan_index}.nii*"
                    )
                )[0]
                f_mtoff_path = list(
                    self.mt_study_path.glob(
                        f"procesado_M0_*subscan_{subscan_index}.nii*"
                    )
                )[0]

            # from nifti to array
            mt_on, affine1 = load_nifti(f_mton_path)
            mt_off, _ = load_nifti(f_mtoff_path)  # affine matrix is the same
            mask, _ = load_nifti(self.mask_path)

            # apply mask
            mt_on = mt_on * mask
            mt_off = mt_off * mask

            if len(self.selected_mt_folders_list) > 1:
                # get maps
                print(f"\n{hmg.info}Generando mapa de MT (carpeta {i}).")
                mt_map = self.compute_MT_map(mt_on, mt_off)

                os.mkdir(str(self.mt_study_path / str(i)))

                # save as .nii file and save heatmaps
                mt_map_filename = f"MT_map_{str(i)}.nii"
                saving_path = os.path.join(
                    str(self.mt_study_path), str(i), mt_map_filename
                )
                save_nifti(saving_path, mt_map.astype(np.float32), affine1)
                Heatmap().save_heatmap(
                    mt_map,
                    "MT",
                    out_path=os.path.join(str(self.mt_study_path), str(i)),
                )
            else:
                # get maps
                print(f"\n{hmg.info}Generando mapa de MT.")
                mt_map = self.compute_MT_map(mt_on, mt_off)

                # save as .nii file and save heatmaps
                saving_path = str(self.mt_study_path / "MT_map.nii")
                save_nifti(saving_path, mt_map.astype(np.float32), affine1)
                Heatmap().save_heatmap(mt_map, "MT", out_path=str(self.mt_study_path))


###############################################################################
# DTI PROCESSING
###############################################################################
class DTIProcessor:
    def __init__(self, root_path: str, study_path: str) -> None:
        self.root_path = root_path
        self.study_path = study_path

    def ask_dti_info(self):
        """
        Ask the user to enter b values, number of basal images and number of directions.
        """
        while True:
            try:
                n_b_val = int(
                    input(
                        f"\n{hmg.ask}¿Número de b valores para cada dirección?"
                        f"\n{hmg.pointer}"
                    )
                )
                break
            except ValueError:
                print(f"{hmg.error}Debes introducir un número.")
        while True:
            try:
                n_basal = int(
                    input(f"\n{hmg.ask}¿Número de imágenes basales?\n{hmg.pointer}")
                )
                break
            except ValueError:
                print(f"{hmg.error}Debes introducir un número.")
        while True:
            try:
                n_dirs = int(
                    input(f"\n{hmg.ask}¿Número de direcciones?\n{hmg.pointer}")
                )
                break
            except ValueError:
                print(f"{hmg.error}Debes introducir un número.")

        return [n_b_val, n_basal, n_dirs]

    def get_bvals_n_dirs(self, n_b_val, n_basal, n_dirs):
        """Returns b values and direction vectors."""

        src_dirs = list(self.study_path.glob("*_DwGradVec.txt"))[0]
        src_bvals = list(self.study_path.glob("*_DwEffBval.txt"))[0]

        method_path = list(self.study_path.glob("procesado_*_method.txt"))[0]
        with open(method_path, "r") as f:
            lines = f.readlines()
            for line in lines:
                if line.startswith("DwNDiffDir"):
                    n_dirs_real = int(re.search("\d+", line)[0])
                elif line.startswith("DwNDiffExpEach"):
                    n_b_val_real = int(re.search("\d+", line)[0])
                elif line.startswith("DwAoImages"):
                    n_basal_real = int(re.search("\d+", line)[0])

        if n_b_val != n_b_val_real:
            print(
                f"\n{hmg.warn}Has introducido un número de b valores diferente "
                "al adquirido."
            )
            print(
                f"Has especificado {n_b_val}, cuando se adquirieron {n_b_val_real}. "
                "Se va a continuar con el valor real."
            )
            n_b_val = n_b_val_real
        else:
            print(f"\n{hmg.info}Número de b valores correcto.")

        if n_basal != n_basal_real:
            print(
                f"\n{hmg.warn}Has introducido un valor de imágenes basales diferente "
                "al adquirido."
            )
            print(
                f"Has especificado {n_basal}, cuando se adquirieron {n_basal_real}. "
                "Se va a continuar con el valor real."
            )
            n_basal = n_basal_real
        else:
            print(f"\n{hmg.info}Número de imágenes basales correcto.")

        if n_dirs != n_dirs_real:
            print(
                f"\n{hmg.warn}Has introducido un valor de direcciones diferente "
                "al adquirido."
            )
            print(f"Has especificado {n_dirs}, cuando se adquirieron {n_dirs_real}.")
            valid_n_dirs = False
            while not valid_n_dirs:
                if n_dirs > n_dirs_real:
                    while True:
                        try:
                            print(
                                "\nPrueba otra vez. Debes intruducir un valor "
                                f"menor o igual a {n_dirs_real}.\n"
                            )
                            n_dirs = int(
                                input(
                                    f"{hmg.ask}¿Número de direcciones?\n{hmg.pointer}"
                                )
                            )
                            break
                        except ValueError:
                            print(f"{hmg.error}Debes introducir un número.")
                else:
                    valid_n_dirs = True

        if n_dirs == n_dirs_real:
            print(f"\n{hmg.info}Número de direcciones correcto.")
            new_dirs = ask_user(
                "¿Deseas eliminar direcciones antes de continuar? En caso contrario,"
                f" se continuará con el número original ({n_dirs_real})."
            )
            if new_dirs:
                while True:
                    try:
                        n_dirs_to_rm = int(
                            input(
                                f"\n{hmg.ask}¿Cuántas direcciones deseas eliminar?"
                                f"\n{hmg.pointer}"
                            )
                        )
                        if 0 <= n_dirs_to_rm < n_dirs_real:
                            n_dirs = n_dirs_real - n_dirs_to_rm
                            break
                        else:
                            print(
                                f"{hmg.error}Debes introducir un número entre "
                                f"0 y {n_dirs_real}."
                            )
                    except ValueError:
                        print(f"{hmg.error}Debes introducir un número.")
        else:
            new_dirs = True
            n_dirs_to_rm = n_dirs_real - n_dirs
            ok_n_dirs_to_rm = ask_user(f"¿Deseas eliminar {n_dirs_to_rm} direcciones?")
            if not ok_n_dirs_to_rm:
                while True:
                    try:
                        n_dirs_to_rm = int(
                            input(
                                f"\n{hmg.ask}¿Cuántas direcciones deseas eliminar?"
                                f"\n{hmg.pointer}"
                            )
                        )
                        if 0 <= n_dirs_to_rm < n_dirs_real:
                            n_dirs = n_dirs_real - n_dirs_to_rm
                            break
                        else:
                            print(
                                f"{hmg.error}Debes introducir un número entre "
                                f"0 y {n_dirs_real}."
                            )
                    except ValueError:
                        print(f"{hmg.error}Debes introducir un número.")
            else:
                n_dirs = n_dirs_real - n_dirs_to_rm

        indexes_to_rm = []
        if new_dirs and (n_dirs_to_rm != 0):
            print(f"\n{hmg.info}Se van a eliminar {n_dirs_to_rm} direcciones.")
            print(
                f"\n{hmg.ask}Por favor, especifica las direcciones que desees eliminar."
            )
            dirs_to_rm = []
            for i in range(n_dirs_to_rm):
                while True:
                    try:
                        temp = int(input(f"({i+1}) {hmg.pointer}"))
                        if (1 <= temp <= n_dirs_real) and (temp not in dirs_to_rm):
                            dirs_to_rm.append(temp)
                            break
                        elif temp in dirs_to_rm:
                            print(f"{hmg.error}Esa dirección ya la has especificado.")
                        else:
                            print(
                                f"{hmg.error}Debes introducir un número "
                                f"entre 1 y {n_dirs_real}."
                            )
                    except ValueError:
                        print(f"{hmg.error}Debes introducir un número.")

            # Ir eliminando de abajo hacia arriba
            dirs_to_rm.sort(reverse=True)

            b_vals = np.loadtxt(src_bvals)
            dirs = np.loadtxt(src_dirs)

            for i_dir in dirs_to_rm:
                temp = []
                # Indice de la primera fila para una direccion
                temp.append(i_dir + n_basal_real - 1 + ((n_b_val - 1) * (i_dir - 1)))
                for j_bval in range(n_b_val - 1):
                    # Agregar los siguientes indices de la misma direccion
                    temp.append(temp[-1] + 1)
                # Eliminar las filas correspondientes
                b_vals = np.delete(b_vals, temp)
                dirs = np.delete(dirs, temp, axis=0)
                indexes_to_rm.append(temp)

            print(f"\n{hmg.info}Mostrado lista de valores b modificada.\n")
            print(b_vals, "\n")

            print(f"{hmg.info}Mostrado listado de direcciones modificadas.\n")
            print(dirs, "\n")
        else:
            b_vals = np.loadtxt(src_bvals)
            print(
                f"\n{hmg.info}Mostrado lista de valores b adquirida del archivo "
                "métodos.\n"
            )
            print(b_vals, "\n")

            dirs = np.loadtxt(src_dirs)
            print(f"{hmg.info}Mostrado direcciones del archivo métodos.\n")
            print(dirs, "\n")

        dirs = dirs.T
        return [b_vals, dirs, n_b_val, n_basal, n_dirs, indexes_to_rm]

    def get_residuals(self, design_matrix, data, weighting=None, sigma=None, jac=True):
        """Computes non-liear least squares per each pixel and returns a map
        of residual errors.  It uses ordinary least squares (OLS) as starting
        point for optimization. The residual error is obtained per direction
        and per b value, including basal images (b=0)."""

        # preparing data
        data[data == 0] = 1
        r_data = data.reshape((-1, data.shape[-1]))  # vectorize data

        # OLS parameters are used as the starting point for optimization
        log_s = np.log(r_data)
        inv_design = np.linalg.pinv(design_matrix)
        ols_params = np.dot(inv_design, log_s.T).T

        # iterate over each voxel and compute non linear least squares error function
        residuals = np.empty((r_data.shape[0], data.shape[3]))
        for vox in range(r_data.shape[0]):
            start_params = ols_params[vox]  # 7 params per voxel
            if jac:
                # Error func for the non-linear least-squares fit of the tensor.
                residuals[vox] = _nlls_err_func(
                    start_params, design_matrix, r_data[vox], weighting, sigma
                )
        # reshape to the original shape
        residuals.shape = data.shape[:]

        return residuals

    def compute_map(self, map_type: str):
        unit_change = 1_000_000

        if map_type == "AD":
            pmap = self.tensor.ad * unit_change
            pmap[pmap < 0.00000001] = float("nan")
        elif map_type == "RD":
            pmap = self.tensor.rd * unit_change
            pmap[pmap < 0.00000001] = float("nan")
        elif map_type == "MD":
            pmap = self.tensor.md * unit_change
            pmap[pmap < 0.00000001] = float("nan")
        elif map_type == "FA":
            pmap = fractional_anisotropy(self.tensor.evals)
            pmap[pmap > 0.95] = float("nan")

        if self.f_R2_maps_slc is not None:
            pmap = pmap * self.f_R2_maps_slc

        return pmap

    def check_DTI_data(self):
        """Check the adquisited images for DTI maps match with the specified
        mask by calling the 'check_shapes' function to compare their shapes.

        Returns:
            bool: True if the shapes of the image and mask match, False otherwise.
        """
        # read nii file with diffusion images and nii file with masks/rois
        try:
            nii_fname = (
                self.study_path / f"{self.study_path.parts[-1][3:]}_subscan_0.nii.gz"
            )
            data, affine = load_nifti(nii_fname)
        except FileNotFoundError:
            nii_fname = self.study_path / f"{self.study_path.parts[-1][3:]}.nii.gz"
            data, affine = load_nifti(nii_fname)

        try:
            mask, affine = load_nifti(self.study_path / "mask.nii")
        except FileNotFoundError:
            mask, affine = load_nifti(
                Path("/".join(self.study_path.parts[:-1])) / "mask.nii"
            )

        return check_shapes(data, mask)

    def process_DTI(self):
        """Solves diffusion tensor using Non-Linear Least Squares (NLLS) and
        computes ADC, FA, MD, AD, RD and R^2 maps."""

        n_b_val, n_basal, n_dirs = self.ask_dti_info()

        # create B values and B dirs files
        # f_bvals = self.root_path / "supplfiles" / "Bvalues.bval"
        # f_dirs = self.root_path / "supplfiles" / "Bdirs.bvec"

        f_bvals = self.study_path / "Bvalues.bval"
        f_dirs = self.study_path / "Bdirs.bvec"

        b_vals, dirs, n_b_val, n_basal, n_dirs, indexes_to_rm = self.get_bvals_n_dirs(
            n_b_val, n_basal, n_dirs
        )

        with open(f_bvals, "w") as f:
            for b_val in b_vals:
                content = str(b_val) + " "
                f.write(content)

        list_dirs = np.array(dirs).tolist()
        with open(f_dirs, "w") as f:
            for i in list_dirs:
                content = str(i).replace("[", "").replace("]", "").replace(",", "")
                f.write(content)
                f.write("\n")

        # read nii file with diffusion images and nii file with masks/rois
        try:
            nii_fname = self.study_path / (
                (self.study_path.parts[-1])[3:] + "_subscan_0.nii.gz"
            )
            data, affine = load_nifti(nii_fname)
        except FileNotFoundError:
            nii_fname = self.study_path / ((self.study_path.parts[-1])[3:] + ".nii.gz")
            data, affine = load_nifti(nii_fname)

        if len(indexes_to_rm) > 0:
            data = np.delete(data, indexes_to_rm, axis=3)

        try:
            mask, affine = load_nifti(self.study_path / "mask.nii")
        except FileNotFoundError:
            mask, affine = load_nifti(
                Path("/".join(self.study_path.parts[:-1])) / "mask.nii"
            )

        # apply mask
        for i in range(data.shape[3]):  # para cada imagen de cada slice
            data[:, :, :, i] = data[:, :, :, i] * mask

        # read b values (bvals) and gradient directions (bvecs)
        bval_path = str(self.study_path / "bvalues.bval")
        bvec_path = str(self.study_path / "Bdirs.bvec")
        bvals, bvecs = read_bvals_bvecs(bval_path, bvec_path)

        if n_dirs < 6:
            print(
                f"\n{hmg.warn}Para imágenes de menos de 6 direcciones no se puede "
                "ajustar el modelo de DTI. Se va a realizar el ajuste monoexponencial "
                "de ADC."
            )

            question = "Elige el modelo que deseas ajustar."
            options = {
                "m": "Ajuste monoexponencial.",
                "l": "Ajuste lineal.",
            }
            selected_model = ask_user_options(question, options)

            print(f"\n{hmg.info}Ajustando el modelo... Puede tardar unos segundos.")
            adcm_map, s0_map = adcm.fit_volume(
                bvals, dirs, n_basal, n_b_val, n_dirs, data, selected_model
            )
            save_nifti(
                str(self.study_path / "ADC_map"), adcm_map.astype(np.float32), affine
            )
            save_nifti(
                str(self.study_path / "s0_map"), s0_map.astype(np.float32), affine
            )

            adcm.show_fitting(
                adcm_map, s0_map, data, bvals, selected_model, n_basal, n_b_val
            )

            # predicted_signal = 
            # residuals = data - predicted_signal
        else:
            # create gradient table. You can access gradients with gtab.gradients
            gtab = gradient_table(bvals, bvecs, atol=1e-0)
            # gtab contains bvec and bvals, such as
            # -0.066   0.9937   -0.089   421.46    Gradient direction and b_val_1
            # -0.066   0.9937   -0.089   1827.43   Gradient direction and b_val_2
            #   ...      ...      ...      ...

            print(
                f"\n{hmg.info}Se está resolviendo el tensor. "
                "Puede tardar unos segundos."
            )
            tensor_model = dti.TensorModel(gtab, fit_method="NLLS")

            tensor_fit = tensor_model.fit(data)
            self.tensor = tensor_fit
            # Some documentation of tensor_model and tensor_fit
            # tensor_model.design_matrix:
            #   np.array with shape (n_basals + n_b_val*n_dirs, 6 + 1).
            #   Matrix with bi[gxi^2, gyi^2, gzi^2, 2*gxi*gyi, 2*gxi*gzi, 2*gyi*gzi, -1]
            #   with g values obtained from gtab.bvecs corresponding with gradient
            #   directions and bi are the b values obtained from gtab.bvals
            # tensor_model.gtab
            #   gtab contains bvec and bvals
            # tensor_fit.evals
            #   np.array with shape (x_dim, y_dim, n_slices, 3) offers 3 eigenvalues
            #   per pixel sorted from the biggest to the smallest.
            # tensor_fit.evecs
            #   np.array with shape (x_dim, y_dim, n_slices, 3, 3) offers 3
            #   eigenvectors per pixel. Each eigenvector has x, y, z directions,
            #   so we have a 3-by-3 matrix per pixel. First row corresponds with
            #   the biggest eigenvalue, and so on.
            # tensor_fit.directions
            #   np.array with shape (x_dim, y_dim, n_slices, 1, 3) offers the main
            #   direction of each pixel, according to the biggest eigenvalue
            # tensor_fit.model
            #   access to tensor_model
            # tensor_fit.quadratic_form
            #   returns np.array of shape (x_dim, y_dim, n_slices, 3, 3).
            #   Calculates the 3-by-3 diffusion tensor for each voxel.

            # get ADC maps
            print(f"\n{hmg.info}Se está generando el mapa ADC.")
            my_sphere = Sphere(xyz=gtab.bvecs[~gtab.b0s_mask])
            ADC_maps = apparent_diffusion_coef(tensor_fit.quadratic_form, my_sphere)

            # ADC matrix has an adc value per bval and direction. For example,
            # for 2 bvals and 15 directions ADC matrix will have 2*15 adc values per
            # pixel. Actually, an adc value is the same as the slope of the straight
            # line that adjust to the ln(S/S0) values at different b values. Then,
            # the adc is different per direction, not per b value. Considering an
            # adc value per b value has no sense. Thus, we only need one adc per
            # direction.
            if n_b_val > 1:
                leap = [*range(1, n_dirs * n_b_val, n_b_val)]
                ADC_maps = ADC_maps[:, :, :, leap]

            unit_change = 1_000_000
            ADC_maps = ADC_maps * unit_change
            ADC_maps[ADC_maps < 0.00000001] = float("nan")
            save_nifti(
                str(self.study_path / "ADC_map"), ADC_maps.astype(np.float32), affine
            )

            # compute R^2 error maps
            # design matrix computed as:
            #   bi[gxi^2, gyi^2, gzi^2, 2*gxi*gyi, 2*gxi*gzi, 2*gyi*gzi, -1],
            # and -1 will be multiplied by ln(S0)

            # design_matrix = tensor_model.design_matrix

            # get errors between the real signal and the predicted signal per our model

            # residuals = self.get_residuals(design_matrix, data)

            # get basal information
            # basal_residuals = residuals[:, :, :, 0:n_basal]
            # basal_data = data[:, :, :, 0:n_basal]

            # get the signal predicted by the fitted DTI model
            # the predicted signal is normalized, as it is divided by S0
            predicted_signal = tensor_fit.predict(gtab)

            # s0 is the average of the basal images (no diffusion gradient)
            s0 = np.mean(data[:, :, :, :n_basal], axis=3)

            # normalize our original image dividing by s0
            norm_data = np.zeros(data.shape)
            for i in range(data.shape[2]):
                for j in range(data.shape[3]):
                    norm_data[:, :, i, j] += data[:, :, i, j] / s0[:, :, i]

            # get residuals: difference between real data and predicted data
            residuals = norm_data - predicted_signal

        R2_maps = []
        print(f"\n{hmg.info}Generando mapas de R\u00b2.")

        for d in range(n_dirs):
            # compute R^2 maps
            i_dir = n_basal + d * n_b_val
            R2_map = R2MapGenerator().get_R2_map(
                norm_data[:, :, :, i_dir : i_dir + n_b_val],
                residuals[:, :, :, i_dir : i_dir + n_b_val],
            )
            R2_dir_path = self.study_path / f"Dir_{str(d + 1)}"
            R2_dir_path.mkdir(parents=True)
            save_nifti(R2_dir_path / "R2_map", R2_map.astype(np.float32), affine)
            R2_maps.append(R2_map)

        save_nifti(
            self.study_path / "R2_map", np.moveaxis(np.array(R2_maps), 0, -1), affine
        )

        # ask if filtering is desired
        apply_filter = ask_user("¿Quieres usar el filtro de ajuste?")

        # select threshold and create R^2 maps
        if apply_filter:
            # get R2 maps and apply threshold to them to get the masks/filters
            R2_map_paths = list(self.study_path.glob("Dir_*/*"))
            f_R2_maps = []

            th = R2MapGenerator().select_threshold()
            for R2_map_path in R2_map_paths:
                # f_R2_map shape: (x_dim, y_dim, n_slices)
                f_R2_map = R2MapGenerator().get_filtered_R2(R2_map_path, "DTI", th)
                f_R2_maps.append(
                    f_R2_map
                )  # filtered R2 maps for all gradient directions
        else:
            f_R2_maps = np.ones(np.shape(R2_maps))
            f_R2_maps_slc = None

        # save adc filtered heatmaps
        f_ADC_maps = np.rollaxis(ADC_maps, axis=3) * np.array(f_R2_maps)
        vmin, vmax, cmap = Heatmap().save_ADC_heatmap(f_ADC_maps, self.study_path)

        # Getting a map per slice requires to have one R^2 map per slice
        if apply_filter:
            f_R2_maps_slc = np.multiply.reduce(f_R2_maps, axis=0)

        self.f_R2_maps_slc = f_R2_maps_slc

        if n_dirs <= 6:
            # mean diffusivity
            print(f"\n{hmg.info}Generando mapas de MD.")
            MD_map = self.compute_map("MD")
            md_saving_path = str(self.study_path / "MD")
            os.makedirs(md_saving_path)
            save_nifti(
                os.path.join(md_saving_path, "MD_map"),
                MD_map.astype(np.float32),
                affine,
            )
            Heatmap().save_heatmap(MD_map, "MD", md_saving_path, vmin, vmax, cmap)

            # axial diffusivity
            print(f"\n{hmg.info}Generando mapas de AD.")
            AD_map = self.compute_map("AD")
            AD_saving_path = str(self.study_path / "AD")
            os.makedirs(AD_saving_path)
            save_nifti(
                os.path.join(AD_saving_path, "AD_map"),
                AD_map.astype(np.float32),
                affine,
            )
            Heatmap().save_heatmap(AD_map, "AD", AD_saving_path, vmin, vmax, cmap)

            # radial diffusivity
            print(f"\n{hmg.info}Generando mapas de RD.")
            RD_map = self.compute_map("RD")
            RD_saving_path = str(self.study_path / "RD")
            os.makedirs(RD_saving_path)
            save_nifti(
                os.path.join(RD_saving_path, "RD_map"),
                RD_map.astype(np.float32),
                affine,
            )
            Heatmap().save_heatmap(RD_map, "RD", RD_saving_path, vmin, vmax, cmap)

            # fractional anisotropy
            # formula: https://dipy.org/documentation/1.0.0./examples_built/reconst_dti/
            print(f"\n{hmg.info}Generando mapas de FA.")
            FA_map = self.compute_map("FA")
            FA_saving_path = str(self.study_path / "FA")
            os.makedirs(FA_saving_path)
            save_nifti(
                os.path.join(FA_saving_path, "FA_map"),
                FA_map.astype(np.float32),
                affine,
            )
            Heatmap().save_heatmap(FA_map, "FA", FA_saving_path)


###############################################################################
# T1/T2/T2E PROCESSING
###############################################################################
class TimeCollector:
    def __init__(
        self, root_path: str, studies_to_process: str, modals_to_process: list
    ) -> None:
        self.root_path = root_path
        self.studies_to_process = studies_to_process
        self.modals_to_process = modals_to_process

    # GET TIMES AUTOMATICALLY
    def read_times(self, subfolder, time_line_start: str, n_char_to_remove: int):
        """Gets the keywords that allow to identify the line with the times
        in mehtod.txt file and the number of characters that must be removed
        from the study name, allowing to compose the name of the method.txt
        file correctly."""

        try:
            method_path = subfolder / (
                subfolder.parts[-1][n_char_to_remove:] + "_method.txt"
            )
            with open(method_path, "r") as f:
                lines = f.readlines()

            for idx, line in enumerate(lines):
                times = ""
                if line.startswith(time_line_start):
                    k = 1
                    is_digit = True
                    while is_digit:
                        times += line  # concat new line with previous line
                        line = lines[idx + k]
                        is_digit = line[1].isdigit()
                        k += 1
                    break
            times = times.replace("[", "").replace("]", "").split()[2:]
            times = list(map(lambda x: x.rstrip("."), times))

            return times

        except FileNotFoundError:
            print(f"{hmg.error}El directorio no existe.")

    def write_times(self, times: list, file_name: str, subfolder: str):
        """Write times, overwritting if file alredy exists."""

        file_path = self.root_path / subfolder / file_name
        with open(file_path, "w") as f:
            f.write(" ".join([t for t in times]))

        return file_path

    def get_times_auto(self):
        """Read times (TR, TE, TEs) automatically from method.txt files
        located in T1, T2, T2* subfolders.

        Returns
        -------
        times_paths: list
            Contains TR in position 0, TE in position 1, and TEs in position 2.
            It has to be in this way as other functions expect a varible with
            times in this particular structure."""

        times_paths = {}  # empty dictionary that will store times
        for subfolder in self.studies_to_process:
            study_name = subfolder.parts[-1]
            if (
                study_name.startswith("T1_")
                and "T1" in self.modals_to_process
                # and study_name[:2] in self.modals_to_process
            ):
                TR_times = self.read_times(subfolder, "MultiRepTime", 3)
                TR_times_path = self.write_times(
                    TR_times, "TiemposRepeticion.txt", subfolder
                )
                times_paths[subfolder] = TR_times_path

            elif (
                study_name.startswith("T2_")
                and "T2" in self.modals_to_process
                # and study_name[:2] in self.modals_to_process
            ):
                TE_times = self.read_times(subfolder, "EffectiveTE", 3)
                TE_times_path = self.write_times(TE_times, "TiemposEco.txt", subfolder)
                times_paths[subfolder] = TE_times_path

            elif (
                study_name.startswith("T2E_")
                and "T2E" in self.modals_to_process
                # and study_name[:3] in self.modals_to_process
            ):
                TEs_times = self.read_times(subfolder, "EffectiveTE", 4)
                TEs_times_path = self.write_times(
                    TEs_times, "TiemposEcoStar.txt", subfolder
                )
                times_paths[subfolder] = TEs_times_path

        return times_paths

    # GET TIMES MANUALLY
    # def get_TR(self):
    #     trs = []
    #     while True:
    #         try:
    #             n_tr = int(
    #                 input(
    #                     "¿Cuántos tiempos de repetición se usaron "
    #                     "en la acquisición de T1?\n"
    #                 )
    #             )
    #             break
    #         except ValueError:
    #             print("No has introducido un número correcto.")

    #     print("Deberás introducir los TR de mayor a menor.\n")
    #     for i in range(n_tr):
    #         tr = input(f"Introduce el tiempo de repetición {i+1}.\n")
    #         trs.append(tr)

    #     return trs

    # def get_TE(self):
    #     init_te = int(input("¿Primer tiempo de eco en T2? "))
    #     n_te = int(input("¿Cuántos tiempos de eco hay en T2? "))
    #     interval = int(input("¿Separación entre tiempos de eco? "))

    #     return list(range(init_te, interval * n_te + interval, interval))

    # def get_TE_star(self):
    #     init_te_star = float(input("¿Primer tiempo de eco en T2 estrella? "))
    #     n_te_star = float(input("¿Cuántos tiempos de eco hay en T2 estrella? "))
    #     interval_star = float(input("¿Separación entre tiempos de eco? "))

    #     return list(np.arange(init_te_star, interval_star * n_te_star, interval_star))

    # def get_requested_times(self, modal: str):
    #     if modal == "T1":
    #         return self.get_TR()
    #     elif modal == "T2":
    #         return self.get_TE()
    #     elif modal == "T2E":
    #         return self.get_TE_star()

    # def get_selected_time(self, selected_modal: str):
    #     """If it does not exists, fuction returns a file with sequence
    #     times (TR, TE or TE*). If it alredy exists, returns that file, as
    #     it will have the same times.

    #     Parameters
    #     ----------
    #         selected_modal: str
    #             selected modality to process (T1, T2 or T2*).
    #     Returns
    #     -------
    #         file_path: str
    #             path to the file with the written times.
    #     """
    #     # define modalities names and time files names
    #     modals = ["T1", "T2", "T2E"]
    #     time_file_names = [
    #         "TiemposRepeticion.txt",
    #         "TiemposEco.txt",
    #         "TiemposEcoStar.txt",
    #     ]

    #     modal_idx = modals.index(selected_modal)
    #     file_name = time_file_names[
    #         modal_idx
    #     ]  # get file name (str) associated to modality

    #     file_path = str(self.root_path / "supplfiles" / file_name)
    #     if not os.path.exists(file_path):
    #         times = self.get_requested_times(selected_modal)  # collects times
    #         with open(file_path, "w+") as f:  # creates file
    #             f.write(" ".join([str(t) for t in times]))
    #     else:
    #         print("[INFO]: Usando archivo de sujeto anterior para tiempos de eco T2")

    #     return file_path

    # def get_times_manual(self):
    #     """Manually, you get times associated to T1, T2, T2E modalities i.e.
    #     TR, TE, TE*, respectively. If a modality has not been selected by
    #     the user to be processed returns an empty string."""

    #     times = []
    #     for modal in ["T1", "T2", "T2E"]:  # orden de los tiempos: tr, te, ts
    #         if modal in self.modals_to_process:
    #             time = self.get_selected_time(modal)
    #             times.append(time)
    #         else:
    #             times.append("")

    #     return times

    def get_times(self, how="auto"):
        if how == "auto":
            time_paths = self.get_times_auto()
        # else:
        #     time_paths = self.get_times_manual()

        return time_paths


class TMapProcessor:
    def __init__(
        self, study_path: str, mask_path: str, n_cpu: int, fitting_mode="nonlinear"
    ) -> None:
        self.study_path = study_path
        self.mask_path = mask_path
        self.fitting_mode = fitting_mode
        self.n_cpu = n_cpu

    def check_T_data(self):
        """Check the adquisited images for T1, T2 or T2E maps match with the specified
        mask by calling the 'check_shapes' function to compare their shapes.

        Returns:
            bool: True if the shapes of the image and mask match, False otherwise.
        """
        index = 4 if "T2E_" in str(self.study_path) else 3
        try:
            f_name = f"{self.study_path.parts[-1][index:]}_subscan_0.nii.gz"
            f_path = str(self.study_path / f_name)
            return check_shapes(f_path, self.mask_path)
        except (NameError, FileNotFoundError):
            f_name = f"{self.study_path.parts[-1][index:]}.nii.gz"
            f_path = str(self.study_path / f_name)
            return check_shapes(f_path, self.mask_path)

    def process_T_map(self, time_paths):
        """Processing of T1, T2, T2* maps using functions located in "myrelax".
        R^2 map is also computed. All maps are saved.
        """

        if "T2_" in str(self.study_path):
            method = "T2"
            print(f"\n{hmg.info}Generando mapa de T2.\n")
            try:
                f_name = self.study_path.parts[-1][3:] + "_subscan_0.nii.gz"
                f_path = str(self.study_path / f_name)
                out_path = f_path[:-7]  # remove .nii

                getT2T2star.TxyFitME(
                    f_path,
                    time_paths[self.study_path],
                    out_path,
                    self.fitting_mode,
                    self.n_cpu,
                    self.mask_path,
                )

            except (NameError, FileNotFoundError):
                f_name = self.study_path.parts[-1][3:] + ".nii.gz"
                f_path = str(self.study_path / f_name)
                out_path = f_path[:-7]  # remove .nii

                getT2T2star.TxyFitME(
                    f_path,
                    time_paths[self.study_path],
                    out_path,
                    self.fitting_mode,
                    self.n_cpu,
                    self.mask_path,
                )

        elif "T2E" in str(self.study_path):
            method = "T2E"
            print(f"\n{hmg.info}Generando mapa de T2E.\n")
            try:
                f_name = self.study_path.parts[-1][4:] + "_subscan_0.nii.gz"
                f_path = str(self.study_path / f_name)
                out_path = f_path[:-7]  # remove .nii

                getT2T2star.TxyFitME(
                    f_path,
                    time_paths[self.study_path],
                    out_path,
                    self.fitting_mode,
                    self.n_cpu,
                    self.mask_path,
                )
            except (NameError, FileNotFoundError):
                f_name = self.study_path.parts[-1][4:] + ".nii.gz"
                f_path = str(self.study_path / f_name)
                out_path = f_path[:-7]  # remove .nii

                getT2T2star.TxyFitME(
                    f_path,
                    time_paths[self.study_path],
                    out_path,
                    self.fitting_mode,
                    self.n_cpu,
                    self.mask_path,
                )

        elif "T1" in str(self.study_path):
            method = "T1"
            print(f"\n{hmg.info}Generando mapa de T1.\n")
            try:
                f_name = self.study_path.parts[-1][3:] + "_subscan_0.nii.gz"
                f_path = str(self.study_path / f_name)
                out_path = f_path[:-7]  # remove .nii.gz

                getT1TR.TxyFitME(
                    f_path,
                    time_paths[self.study_path],
                    out_path,
                    self.fitting_mode,
                    self.n_cpu,
                    self.mask_path,
                )
            except (NameError, FileNotFoundError):
                f_name = self.study_path.parts[-1][3:] + ".nii.gz"
                f_path = str(self.study_path / f_name)
                out_path = f_path[:-7]  # remove .nii

                getT1TR.TxyFitME(
                    f_path,
                    time_paths[self.study_path],
                    out_path,
                    self.fitting_mode,
                    self.n_cpu,
                    self.mask_path,
                )

        # create a folder to store useful files
        if not (self.study_path / "mapas").exists():
            (self.study_path / "mapas").mkdir(parents=True)

        # get those paths related to T1 map
        T_paths = sorted(glob.glob(str(self.study_path / "*ME.nii")))
        T_paths[0], T_paths[2] = T_paths[2], T_paths[0]  # puts *SSEME.nii file first

        for T_path in T_paths:
            T_maps_folder = str(self.study_path / "mapas")
            shutil.move(T_path, T_maps_folder)
            T_path = Path(T_path)
            T_path = str((self.study_path / "mapas") / T_path.parts[-1])

            # compute T^2 map and save it
            if T_path.endswith("SSEME.nii"):
                sse, affine = load_nifti(T_path)
                data, affine = load_nifti(f_path)
                R2_map = R2MapGenerator().get_R2_map(data=data, sse=sse)
                R2_map_path = T_maps_folder + "/" + "R2_map.nii"
                save_nifti(R2_map_path, R2_map.astype(np.float32), affine)

            # save T1/T2/T2E heatmap and filter by R^2 if required
            elif T_path.endswith("TxyME.nii"):
                T_map, affine = load_nifti(T_path)
                saving_path = T_maps_folder + "/" + f"{method}_map"
                apply_filter = ask_user("¿Quieres usar el filtro de ajuste?")
                if apply_filter:
                    th = R2MapGenerator().select_threshold()
                    f_R2_map = R2MapGenerator().get_filtered_R2(
                        R2_map_path, f"{method}_map", th
                    )
                    T_map = T_map * f_R2_map
                    save_nifti(saving_path, T_map.astype(np.float32), affine)
                Heatmap().save_heatmap(T_map, method, T_maps_folder)


###############################################################################
# R^2 map
###############################################################################
class R2MapGenerator:
    def get_sse(self, x):
        return np.sum(x**2, axis=3)

    def get_sst(self, x):
        avg = sum(x) / len(x)
        return sum((np.array(x) - avg) ** 2)

    def get_R2_map(self, data, residuals=None, sse=None):
        """Compute R^2 map.
            R^2 = 1 - sse/sst , with sse = SUM_i((y_real_i - y_pred_i)^2)
                                     sst = SUM_i((y_real_i - avg)^2)
        Parameters
        ----------
            data : np.array
                original data with shape=(x_dim, y_dim, n_slices, n_basales + n_b_vals).
            residuals : np.array
                Contains differences between predicted signal by our model and
                the real data (y_real_i - y_pred_i).
                residuals.shape=(x_dim, y_dim, n_slices, n_basales + n_b_vals)
        Returns
        -------
            R2_map : np.array
        """

        if sse is None:  # if sse not provided
            sse = self.get_sse(residuals)  # sum of squared errors
        sst = np.apply_along_axis(self.get_sst, 3, data)  # total sum of squares
        R2_map = 1 - sse / sst

        return R2_map

    def select_threshold(self):
        while True:
            try:
                th = input(
                    f"\n{hmg.ask}Introduce el valor que quieres usar como tolerancia "
                    f"(R\u00b2). Ha de ser un valor entre 0 y 1.\n{hmg.pointer}"
                )
                th = float(th)
                if th > 0.99:
                    raise ValueError
                return th
            except ValueError:
                print(
                    f'El umbral debe ser un número entre 0 y 1. Has introducido "{th}".'
                )

    def get_filtered_R2(self, R2_map_path, method, th):
        """Apply threshold to R^2 map."""
        if "T" in method:
            (R2_map, affine) = load_nifti(R2_map_path)
            R2_map[R2_map < th] = float("nan")
            R2_map[R2_map >= th] = 1

        elif "DTI" in method:
            R2_map, _ = load_nifti(R2_map_path)  # R2 map for a direction
            R2_map[R2_map < th] = float("nan")  # if does not reach th set to nan
            R2_map[R2_map >= th] = 1  # else set to 1

        return R2_map


##############################################################################
# HEATMAPS
##############################################################################
class Heatmap:
    def rotate(self, array_2d):
        list_of_tuples = zip(*array_2d[::-1])
        return [list(elem) for elem in list_of_tuples]

    def change_colormap(self):
        while True:
            cmap_name = input("Introduce el nombre del mapa de colores.\n")
            try:
                return cm.get_cmap(cmap_name)
            except ValueError:
                print(
                    f'Has introducido "{cmap_name}" y ese nombre no corresponde '
                    "con ningún mapa. Vuelve a intentarlo.\n"
                )

    def change_vmin_vmax(self):
        while True:
            try:
                vmin = float(input("Introduce el valor mínimo.\n"))
                break
            except Exception:
                print("No has introducido un número.")

        while True:
            try:
                vmax = float(input("Introduce el valor máximo.\n"))
                break
            except Exception:
                print("No has introducido un número.")

        return vmin, vmax

    def compute_heatmaps(
        self,
        maps: np.array,
        map_type: str,
        cmap,
        vmin: int,
        vmax: int,
        out_path="",
        ind=False,
        save=False,
    ):
        n_slices = np.shape(maps)[0]
        if n_slices % 2 == 0:
            cols = int(np.divide(n_slices, 2))
        else:
            cols = int(np.divide(n_slices, 2) + 0.5)
        fig, ax = plt.subplots(2, cols, figsize=(10, 7))
        ax = ax.flatten()
        plt.axis("off")
        cbar_ax = fig.add_axes([0.91, 0.3, 0.03, 0.4])

        for slc_idx, new_map in enumerate(maps):
            r_map = self.rotate(new_map)
            sns.heatmap(
                r_map,
                cmap=cmap,
                xticklabels=False,
                yticklabels=False,
                vmin=vmin,
                vmax=vmax,
                cbar_ax=cbar_ax,
                ax=ax[slc_idx],
            ).invert_xaxis()
            ax[slc_idx].set_title(f"{map_type} slice {str(slc_idx + 1)}")

            if ind is True:
                ind_fig = plt.figure(frameon=False, num=slc_idx + fig.number + 1)
                sns.heatmap(
                    r_map,
                    cmap=cmap,
                    xticklabels=False,
                    yticklabels=False,
                    vmin=vmin,
                    vmax=vmax,
                ).invert_xaxis()
                if save == save:
                    ind_fig.savefig(
                        os.path.join(
                            out_path, f"{map_type}_slice_{str(slc_idx + 1)}.png"
                        )
                    )
                    plt.close(ind_fig)

        plt.suptitle(f"{map_type} slices")
        fig.tight_layout(rect=[0, 0, 0.9, 1])

        if save is True:
            fig.savefig(os.path.join(out_path, f"{map_type}_all_slices.png"))
            plt.close()
        else:
            fig.show()

    def save_ADC_heatmap(self, f_ADC_maps: np.array, study_path: str):
        """Save ADC heatmap. Opens a window to show the heatmaps per slice
        and allows to change color range and color map.
        Parameters
        ----------
        f_ADC_maps : np.array
            Includes filtered ADC directions.
        study_path : Path
            Path to study folder.
        """
        f_ADC_maps[f_ADC_maps == 0.0] = np.nan

        cmap = plt.cm.turbo  # select default cmap
        # cmap.set_bad("black", 1)  # paints NaN values in black
        vmin = 0.1 * np.nanmax(f_ADC_maps) + np.nanmin(f_ADC_maps)
        vmax = 0.9 * np.nanmax(f_ADC_maps)

        self.chosen_cmap = cmap
        self.chosen_vmin = vmin
        self.chosen_vmax = vmax

        for num_dir, ADC_map_dir in enumerate(f_ADC_maps):
            ADC_map_dir = np.rollaxis(ADC_map_dir, axis=2)
            # offer the possibility to change vmin, vmax and cmap in the adc map
            # of the first direction
            if num_dir == 0:
                out_path = os.path.join(study_path, f"Dir_{str(num_dir + 1)}")

                self.compute_heatmaps(
                    ADC_map_dir,
                    "ADC",
                    cmap,
                    vmin,
                    vmax,
                    out_path,
                    ind=False,
                    save=False,
                )

                print(
                    f"\n{hmg.ask}Indica cómo quieres guardar los mapas en la "
                    "ventana emergente."
                )

                # create a frame
                root = tk.Tk()
                root.title("MyX")

                # declaring string variable for storing values
                color_min = tk.IntVar()
                color_max = tk.IntVar()
                colormap = tk.StringVar()

                tk.Label(root, text="Mínimo", font=("calibre", 10, "bold")).grid(
                    row=0, column=0
                )
                tk.Label(root, text="Máximo", font=("calibre", 10, "bold")).grid(
                    row=2, column=0
                )
                tk.Label(root, text="Color", font=("calibre", 10, "bold")).grid(
                    row=4, column=0
                )

                # creating entries for inputs
                color_min_entry = tk.Entry(
                    root, textvariable=color_min, font=("calibre", 10, "normal")
                )
                color_max_entry = tk.Entry(
                    root, textvariable=color_max, font=("calibre", 10, "normal")
                )
                colormap_entry = tk.Entry(
                    root, textvariable=colormap, font=("calibre", 10, "normal")
                )

                color_min_entry.grid(row=1, column=1)
                color_max_entry.grid(row=3, column=1)
                colormap_entry.grid(row=5, column=1)

                # setting default values
                color_min_entry.insert(0, vmin)
                color_max_entry.insert(0, vmax)
                colormap_entry.insert(0, "turbo")

                def get_selection():
                    color_min_val = color_min_entry.get()
                    color_max_val = color_max_entry.get()
                    colormap_val = colormap_entry.get()

                    plt.close("all")
                    plt.clf()

                    self.compute_heatmaps(
                        ADC_map_dir,
                        "ADC",
                        colormap_val,
                        color_min_val,
                        color_max_val,
                        ind=False,
                        save=False,
                    )

                def close():
                    color_min_val = color_min_entry.get()
                    color_max_val = color_max_entry.get()
                    colormap_val = colormap_entry.get()

                    plt.close("all")
                    plt.clf()
                    self.compute_heatmaps(
                        ADC_map_dir,
                        "ADC",
                        colormap_val,
                        color_min_val,
                        color_max_val,
                        out_path,
                        ind=True,
                        save=True,
                    )

                    self.chosen_cmap = colormap_val
                    self.chosen_vmin = color_min_val
                    self.chosen_vmax = color_max_val

                    print(
                        f"\n{hmg.info}Guardadas las direcciones: {num_dir+1} ",
                        end="",
                        flush=True,
                    )

                    root.destroy()
                    root.quit()

                tk.Button(root, text="Actualizar", command=get_selection).grid(
                    row=6, column=0
                )
                tk.Button(root, text="Aceptar", command=close).grid(row=6, column=1)

                root.mainloop()

            else:
                out_path = study_path / f"Dir_{str(num_dir + 1)}"

                self.compute_heatmaps(
                    ADC_map_dir,
                    "ADC",
                    self.chosen_cmap,
                    self.chosen_vmin,
                    self.chosen_vmax,
                    out_path,
                    ind=True,
                    save=True,
                )

                print(num_dir + 1, end=" ", flush=True)
        print()
        return vmin, vmax, cmap

    def save_heatmap(
        self,
        maps: np.array,
        map_type: str,
        out_path: str,
        vmin=None,
        vmax=None,
        cmap=None,
    ):
        """Opens a window to show the heatmaps per slice and allows to
        change color range and color map. Do not use for ADC maps, use
        save_ADC_heatmap function instead.

        Args:
            maps (numpy.array): stack of maps (one map per slice)
            map_type (str): name of the map
            out_path (str): string path to save output maps
        """
        cmap = plt.cm.turbo  # select default cmap
        # cmap.set_bad('black', 1)  # paints NaN values in black

        if map_type == "FA":
            vmin = 0.05  # min possible value of FA
            vmax = 0.95  # max possible value of FA

        if map_type in ["T1", "T2", "T2E", "MT"]:
            vmin = 0.1 * np.nanmax(maps) + np.nanmin(maps)
            vmax = 0.9 * np.nanmax(maps)

        maps[maps == 0.0] = np.nan
        maps = np.rollaxis(maps, 2)

        # show a subplot as a preview, without saving it or showing
        # individual heatmaps
        self.compute_heatmaps(
            maps, map_type, cmap, vmin, vmax, out_path, ind=False, save=False
        )

        print(
            f"\n{hmg.ask}Indica cómo quieres guardar los mapas en la ventana emergente."
        )

        # create a frame
        root = tk.Tk()
        root.title("MyX")

        # declaring string variable for storing values
        color_min = tk.IntVar()
        color_max = tk.IntVar()
        colormap = tk.StringVar()

        tk.Label(root, text="Mínimo", font=("calibre", 10, "bold")).grid(
            row=0, column=0
        )
        tk.Label(root, text="Máximo", font=("calibre", 10, "bold")).grid(
            row=2, column=0
        )
        tk.Label(root, text="Color", font=("calibre", 10, "bold")).grid(row=4, column=0)

        # creating entries for inputs
        color_min_entry = tk.Entry(
            root, textvariable=color_min, font=("calibre", 10, "normal")
        )
        color_max_entry = tk.Entry(
            root, textvariable=color_max, font=("calibre", 10, "normal")
        )
        colormap_entry = tk.Entry(
            root, textvariable=colormap, font=("calibre", 10, "normal")
        )

        color_min_entry.grid(row=1, column=1)
        color_max_entry.grid(row=3, column=1)
        colormap_entry.grid(row=5, column=1)

        # setting default values
        color_min_entry.insert(0, vmin)
        color_max_entry.insert(0, vmax)
        colormap_entry.insert(0, "turbo")

        def get_selection():
            color_min_val = color_min_entry.get()
            color_max_val = color_max_entry.get()
            colormap_val = colormap_entry.get()

            plt.close("all")
            plt.clf()

            self.compute_heatmaps(
                maps,
                map_type,
                colormap_val,
                color_min_val,
                color_max_val,
                ind=False,
                save=False,
            )

        def close():
            color_min_val = color_min_entry.get()
            color_max_val = color_max_entry.get()
            colormap_val = colormap_entry.get()
            plt.close("all")
            plt.clf()
            self.compute_heatmaps(
                maps,
                map_type,
                colormap_val,
                color_min_val,
                color_max_val,
                out_path,
                ind=True,
                save=True,
            )

            root.destroy()
            root.quit()

        tk.Button(root, text="Actualizar", command=get_selection).grid(row=6, column=0)
        tk.Button(root, text="Aceptar", command=close).grid(row=6, column=1)

        root.mainloop()
