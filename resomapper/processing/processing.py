import os
import json
import resomapper.core.utils as ut
from resomapper.core.misc import NoModalsSelectedError
from resomapper.core.misc import NotStudiesToProcessError
import nibabel as nib
import numpy as np
from dipy.io.gradients import read_bvals_bvecs

from resomapper.core.misc import auto_innited_logger as lggr
import resomapper.model_fitting.Tmapfit as tfit
import resomapper.model_fitting.DTIfit as dtifit
import resomapper.model_fitting.MTRfit as mtrfit

import warnings

warnings.filterwarnings("ignore")

#### COMMON UTILS ####


def get_studies_to_process(path, modals_to_process, auto_mode=False):
    sourcedata_folder = os.path.join(path, "sourcedata")
    derivatives_folder = os.path.join(path, "derivatives")

    studies_to_process = {}

    if len(modals_to_process) == 0:
        raise NoModalsSelectedError

    for study_folder in os.listdir(sourcedata_folder):
        if ut.is_folder_and_not_occult(os.path.join(sourcedata_folder, study_folder)):
            studies_to_process[study_folder] = []
            for study_bids_folder in os.listdir(
                os.path.join(sourcedata_folder, study_folder)
            ):
                if ut.is_folder_and_not_occult(
                    os.path.join(sourcedata_folder, study_folder, study_bids_folder)
                ):
                    for data_file in os.listdir(
                        os.path.join(sourcedata_folder, study_folder, study_bids_folder)
                    ):
                        if ut.is_nii(data_file):
                            modal = ut.get_modality_nii_acq(data_file)
                            if modal in modals_to_process:
                                studies_to_process[study_folder].append(
                                    (modal, data_file)
                                )

    acqs_to_process = {}
    for study in studies_to_process:
        acqs_to_process[study] = [
            (x[0], ut.get_acq(x[1])) for x in studies_to_process[study]
        ]
        acqs_to_process[study] = list(set(acqs_to_process[study]))

    if not any_studies_in_dict(studies_to_process):
        raise NotStudiesToProcessError
    else:
        if not os.path.exists(derivatives_folder):
            # No studies have already been processed
            os.mkdir(derivatives_folder)
            return acqs_to_process
        else:
            # Some studies might have already been processed
            processed_acqs = {}
            for study_folder in os.listdir(derivatives_folder):
                if ut.is_folder_and_not_occult(
                    os.path.join(derivatives_folder, study_folder)
                ):
                    processed_acqs[study_folder] = []
                    for modal_folder in os.listdir(
                        os.path.join(derivatives_folder, study_folder)
                    ):
                        if ut.is_folder_and_not_occult(
                            os.path.join(derivatives_folder, study_folder, modal_folder)
                        ):
                            for data_file in os.listdir(
                                os.path.join(
                                    derivatives_folder, study_folder, modal_folder
                                )
                            ):
                                if ut.is_nii(data_file) and "processedmap" in data_file:
                                    processed_acqs[study_folder].append(
                                        (
                                            ut.get_modality_nii_map(data_file),
                                            ut.get_acq(data_file),
                                        )
                                    )
                            processed_acqs[study_folder] = list(
                                set(processed_acqs[study_folder])
                            )

            coincident_processed_acqs = {}
            for study, acqs in processed_acqs.items():
                if study in acqs_to_process:
                    filtered_list = [
                        acq for acq in acqs if acq in acqs_to_process[study]
                    ]
                    if filtered_list:
                        coincident_processed_acqs[study] = filtered_list
            if any_studies_in_dict(coincident_processed_acqs):

                if auto_mode is False:
                    acqs_to_process = choose_if_reprocess(
                        acqs_to_process, coincident_processed_acqs
                    )

                if not any_studies_in_dict(acqs_to_process):
                    raise NotStudiesToProcessError
            return acqs_to_process


def any_studies_in_dict(studies_dict):
    for array in studies_dict.values():
        if array:
            return True
    return False


def choose_if_reprocess(acqs_to_process, processed_acqs):
    print(
        f"\n{lggr.warn}Some studies have already been processed. Please choose if you want to reprocess them or not."
    )
    print("Already processed studies:")
    i = 0
    index_map = {}
    for study in processed_acqs:
        if processed_acqs[study] != []:
            print(f"\nStudy - {study}:")
            for x in processed_acqs[study]:
                print(f"({i}) - Modality: {x[0]}, Acquisition: {x[1]}")
                index_map[i] = (study, x)
                i += 1
    question = "Select the option you prefer."
    options = {
        "a": "Process again all studies (previous results will be overwritten).",
        # "s": "Select which studies to reprocess.",
        "n": "Do not reprocess any studies already processed.",
    }
    selection = ut.ask_user_options(question, options)

    if selection == "a":
        return acqs_to_process
    elif selection == "n":
        new_acqs_to_process = {}
        for study in acqs_to_process:
            if study in processed_acqs:
                new_acqs_to_process[study] = [
                    x for x in acqs_to_process[study] if x not in processed_acqs[study]
                ]
            else:
                new_acqs_to_process[study] = acqs_to_process[study]
        return new_acqs_to_process
    # TODO: give the option to select some
    # elif selection == "s":
    #     pass


def cli_ask_indexes_to_rm(n_max, map_type, n_basal=None, n_b_val=None):

    if map_type == "T1":
        text_to_remove = "repetition times"
    elif "T2" in map_type:
        text_to_remove = "echo times"
    elif map_type == "DTI":
        text_to_remove = "directions"

    while True:
        try:
            n_dirs_to_rm = int(
                input(
                    f"\n{lggr.ask}How many {text_to_remove} do you want to remove?"
                    f"\n{lggr.pointer}"
                )
            )
            if 0 <= n_dirs_to_rm < n_max:
                # n_dirs = n_max - n_dirs_to_rm
                break
            else:
                print(f"{lggr.error}Please enter a number between 0 and {int(n_max)}.")
        except ValueError:
            print(f"{lggr.error}Please enter only integer numbers.")

    indexes_to_rm = []
    if n_dirs_to_rm != 0:
        print(f"\n{lggr.info}{n_dirs_to_rm} {text_to_remove} will be removed.")
        print(
            f"\n{lggr.ask}Please specify the index of the {text_to_remove} to remove "
            f"(from 1 to {n_max}, one at a time)."
        )
        dirs_to_rm = []
        for i in range(n_dirs_to_rm):
            while True:
                try:
                    temp = int(input(f"({i+1}) {lggr.pointer}"))
                    if (1 <= temp <= n_max) and (temp not in dirs_to_rm):
                        dirs_to_rm.append(temp)
                        break
                    elif temp in dirs_to_rm:
                        print(f"{lggr.error}You have already specified that number.")
                    else:
                        print(
                            f"{lggr.error}You must enter a number between "
                            f"1 and {n_max}."
                        )
                except ValueError:
                    print(f"{lggr.error}Please enter integer numbers.")

        if map_type == "DTI":
            for i_dir in dirs_to_rm:
                # Index of the first bvalue for one direction
                temp = [i_dir + n_basal - 1 + (n_b_val - 1) * (i_dir - 1)]
                # Add the next indexes for the same direction (the rest of bvalues)
                temp.extend(temp[-1] + 1 for _ in range(n_b_val - 1))
                indexes_to_rm += temp
        else:
            indexes_to_rm = [index - 1 for index in dirs_to_rm]

    # Sort to remove up to down
    indexes_to_rm.sort(reverse=True)

    return indexes_to_rm


#### Tmap fitting ####


def process_Tmap(nifti_file_path, mask_nifti_path, T_type, ask_remove_times=False):
    study_nii = nib.load(nifti_file_path)
    nii_data = study_nii.get_fdata()

    json_file_path = nifti_file_path.replace(".nii.gz", ".json")

    with open(json_file_path) as f:
        json_info = json.load(f)

    if T_type == "T1":
        times_array = json_info["RepetitionTime"]
    elif "T2" in T_type:
        times_array = json_info["EchoTime"]

    if np.shape(nii_data)[3] != len(times_array):
        print(
            f"\n{lggr.error}Nifti shape ({np.shape(nii_data)}) does not "
            f"match the length of the times array ({len(times_array)}). "
            "Fitting aborted."
        )
        return
    else:
        if ask_remove_times:
            nifti_file_path, times_array = cli_Tmap_remove_times(
                nifti_file_path, json_file_path, T_type
            )

        output_basename = nifti_file_path.replace(".nii.gz", "")
        tfit.Tmapfit_image(
            nifti_file_path,
            times_array,
            output_basename,
            T_type,
            non_linear_fitting=True,
            ncpu=None,
            mask_nifti=mask_nifti_path,
        )
        return output_basename


def cli_Tmap_remove_times(nifti_file_path, json_file_path, T_type):

    with open(json_file_path) as f:
        json_info = json.load(f)
    if T_type == "T1":
        text_to_rm = "repetition times"
        times_array = json_info["RepetitionTime"]
    elif "T2" in T_type:
        text_to_rm = "echo times"
        times_array = json_info["EchoTime"]

    if ut.ask_user(
        f"Do you want to remove any {text_to_rm} from the original acquisition?"
    ):
        if "_preproc" not in nifti_file_path:
            new_nifti_file_path = nifti_file_path.replace(".nii.gz", "_preproc.nii.gz")
            new_json_file_path = json_file_path.replace(".json", "_preproc.json")
        else:
            new_nifti_file_path = nifti_file_path
            new_json_file_path = json_file_path

        study_nii = nib.load(nifti_file_path)
        nii_data = study_nii.get_fdata()
        indexes_to_rm = cli_ask_indexes_to_rm(len(times_array), T_type)

        nii_data = np.delete(nii_data, indexes_to_rm, axis=3)
        nii_ima = nib.Nifti1Image(
            nii_data.astype(np.float64), study_nii.affine, study_nii.header
        )
        nib.save(nii_ima, new_nifti_file_path)

        times_array = np.delete(times_array, indexes_to_rm)

        if T_type == "T1":
            json_info["RepetitionTime"] = times_array.tolist()
        elif "T2" in T_type:
            json_info["EchoTime"] = times_array.tolist()

        with open(new_json_file_path, "w") as f:
            json.dump(json_info, f, indent=4)

        return new_nifti_file_path, times_array

    else:
        return nifti_file_path, times_array


#### MTRmap fitting ####


def process_MTRmap(mton_nifti_file_path, mtoff_nifti_file_path, mask_nifti_path=None):

    mtr_map_output_path = mton_nifti_file_path.replace(
        ".nii.gz", "_MTR-processedmap.nii.gz"
    )
    mtr_map_output_path = mtr_map_output_path.replace("_MTon", "")
    mton_nii = nib.load(mton_nifti_file_path)
    mton_nii_data = mton_nii.get_fdata()

    mtoff_nii = nib.load(mtoff_nifti_file_path)
    mtoff_nii_data = mtoff_nii.get_fdata()

    mtrfit.check_slices_MT_images()

    if mask_nifti_path is not None:
        mask_nii = nib.load(mask_nifti_path)
        mask_nii_data = mask_nii.get_fdata()
        mton_nii_data = mton_nii_data * mask_nii_data
        mtoff_nii_data = mtoff_nii_data * mask_nii_data

    mtrfit.check_slopes_MT_images()

    mtr_map_data = mtrfit.compute_MTR_map(mton_nii_data, mtoff_nii_data)
    mtr_map_nii = nib.Nifti1Image(
        mtr_map_data.astype(np.float64), mton_nii.affine, mton_nii.header
    )
    nib.save(mtr_map_nii, mtr_map_output_path)


#### DWI-DTI fitting ####


def process_DTI(
    nifti_file_path, mask_nifti_path, ask_user_info=False, ask_remove_dirs=False
):
    study_nii = nib.load(nifti_file_path)
    nii_data = study_nii.get_fdata()

    b_vals_fname = nifti_file_path.replace(".nii.gz", ".bval")

    b_vecs_fname = b_vals_fname.replace(".bval", ".bvec")

    b_vals, b_vecs = read_bvals_bvecs(b_vals_fname, b_vecs_fname)
    n_bval, n_basal, n_dirs = dtifit.count_basal_dirs_bvals(b_vals, b_vecs)

    if np.shape(nii_data)[3] != (n_basal + (n_bval * n_dirs)):
        print(
            f"\n{lggr.error}Nifti shape ({np.shape(nii_data)}) does not "
            f"match with the information of the .bval and .bvec files. "
            "Fitting aborted."
        )
        return

    if ask_user_info:
        dtifit.cli_ask_dti_info(n_bval, n_basal, n_dirs)

    if ask_remove_dirs:
        nifti_file_path, b_vals, b_vecs = cli_DTI_remove_directions(
            nifti_file_path, b_vals, b_vecs, n_bval, n_basal, n_dirs
        )

    print(f"\n{lggr.info}B values and gradient directions info:")
    dtifit.print_bvals_bvecs(b_vals, b_vecs)

    output_basename = nifti_file_path.replace(".nii.gz", "")

    if n_dirs < 6:
        print(
            f"\n{lggr.warn}To accurately fit the DTI model you need an acquisition "
            "of at least 6 gradient directions. Classic monoexponential ADC fitting "
            "will be performed for this study."
        )
        # TODO: ADC fitting
        # return output_basename
    else:
        dtifit.process_dti(
            nifti_file_path, b_vals, b_vecs, output_basename, mask_fname=mask_nifti_path
        )
        return output_basename


def cli_DTI_remove_directions(nifti_file_path, b_vals, b_vecs, n_bval, n_basal, n_dirs):
    if ut.ask_user(
        "Do you want to remove any directions from the original acquisition?"
    ):
        indexes_to_rm = cli_ask_indexes_to_rm(
            n_dirs, "DTI", n_basal=n_basal, n_b_val=n_bval
        )

        if "_preproc" not in nifti_file_path:
            new_nifti_file_path = nifti_file_path.replace(".nii.gz", "_preproc.nii.gz")
        else:
            new_nifti_file_path = nifti_file_path
        bv_output_basename = new_nifti_file_path.replace(".nii.gz", "")

        study_nii = nib.load(nifti_file_path)
        nii_data = study_nii.get_fdata()

        nii_data = np.delete(nii_data, indexes_to_rm, axis=3)
        nii_ima = nib.Nifti1Image(
            nii_data.astype(np.float64), study_nii.affine, study_nii.header
        )
        nib.save(nii_ima, new_nifti_file_path)

        b_vals = np.delete(b_vals, indexes_to_rm)
        b_vecs = np.delete(b_vecs, indexes_to_rm, axis=0)
        dtifit.save_bvals_bvecs(b_vals, b_vecs, bv_output_basename)

        return new_nifti_file_path, b_vals, b_vecs
    else:
        return nifti_file_path, b_vals, b_vecs
