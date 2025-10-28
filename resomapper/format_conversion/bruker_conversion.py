import brkraw
import os
import json
import zipfile
import nibabel as nib
import numpy as np
from tqdm import tqdm

import resomapper.core.misc as msc
import resomapper.core.utils as ut
from resomapper.core.misc import auto_innited_logger as lggr

from resomapper.core.misc import NotStudiesToConvertError

import warnings

warnings.filterwarnings("ignore")

#### BRUKER CONVERSION ####


def get_common_info_study_bruker(pvdset, print_info=False):
    study_common_info = {
        # "UserAccount" : pvdset.pvobj.user_account,
        "Date": str(pvdset.get_scan_time()["date"]),
        "SubjectID": pvdset.pvobj.subj_id,
        # "StudyID" : pvdset.pvobj.study_id,
        "SessionID": pvdset.pvobj.session_id,
        "UserName": pvdset.pvobj.user_name,
        "SubjectEntry": pvdset.pvobj.subj_entry,
        "SubjectPos": pvdset.pvobj.subj_pose,
        # "SubjectSex" : pvdset.pvobj.subj_sex,
        "SubjectType": pvdset.pvobj.subj_type,
        # "SubjectWeight" : pvdset.pvobj.subj_weight,
        # "SubjectBirthDate" : pvdset.pvobj.subj_dob,
    }

    if print_info:
        # print('UserAccount:\t{}'.format(study_common_info['UserAccount']))
        print("Date:\t\t{}".format(study_common_info["Date"]))
        print("Researcher:\t{}".format(study_common_info["UserName"]))
        print("Subject ID:\t{}".format(study_common_info["SubjectID"]))
        print("Session ID:\t{}".format(study_common_info["SessionID"]))
        # print('Study ID:\t{}'.format(study_common_info['StudyID']))
        # print('Date of Birth:\t{}'.format(study_common_info['SubjectBirthDate']))
        # print('Sex:\t\t{}'.format(study_common_info['SubjectSex']))
        # print('Weight:\t\t{} kg'.format(study_common_info['SubjectWeight']))
        print("Subject Type:\t{}".format(study_common_info["SubjectType"]))
        print(
            "Position:\t{}\t\tEntry:\t{}".format(
                study_common_info["SubjectPos"], study_common_info["SubjectEntry"]
            )
        )

    return study_common_info


def convert_and_save_nifti_bruker(
    pvdset,
    scan_id,
    reco_id,
    filename,
    dir="./",
    ext="nii.gz",
    crop=None,
    slope=False,
    offset=False,
):
    niiobj = pvdset.get_niftiobj(
        scan_id, reco_id, crop=crop, slope=slope, offset=offset
    )
    output_path = os.path.join(dir, "{}.{}".format(filename, ext))

    if isinstance(niiobj, list):
        original_dtype = niiobj[0].get_data_dtype()
        data_arrays = [nii.get_fdata().astype(original_dtype) for nii in niiobj]
        concatenated_data = np.stack(data_arrays, axis=-1)
        affine = niiobj[0].affine

        # TODO: try ? instead of changing one part of the header, include the header like:
        # new_nifti_series = nib.Nifti1Image(concatenated_data, affine, niiobj[0].header)
        new_nifti_series = nib.Nifti1Image(concatenated_data, affine)
        new_nifti_series.header["xyzt_units"] = niiobj[0].header["xyzt_units"]

        new_nifti_series.to_filename(output_path)

    else:
        niiobj.to_filename(output_path)


def is_modality_bruker(modality, params, conditions_dict=msc.conditions_dict_bruker):
    return all(cond(params) for cond in conditions_dict[modality])


def get_modality_bruker(params, conditions_dict=msc.conditions_dict_bruker):
    for modality in conditions_dict:
        if is_modality_bruker(modality, params, conditions_dict):
            return modality
    return "etc"


def create_metadata_json_bruker(
    pvdset,
    scan_id,
    reco_id,
    filename,
    dir="./",
    subject_info=None,
    extra_info=None,
    metadata_dict=msc.metadata_ref_BIDS_bruker,
):
    results_json = pvdset._parse_json(scan_id, reco_id, metadata=metadata_dict)
    json_output_path = os.path.join(dir, filename + ".json")

    results_json_modified = {
        k: (None if results_json[k] == metadata_dict[k] else results_json[k])
        for k in results_json
    }
    if subject_info is not None:
        results_json_modified = {**subject_info, **results_json_modified}

    if extra_info is not None:
        results_json_modified = {**results_json_modified, **extra_info}

    with open(json_output_path, "w") as f:
        json.dump(results_json_modified, f, indent=4)


def check_valid_dir_bruker(path):
    if "subject" in os.listdir(path):
        pvdset = brkraw.load(path)
        if pvdset.is_pvdataset:
            study_info = get_common_info_study_bruker(pvdset, print_info=False)
            subj_sess_name = (
                "sub-" + study_info["SubjectID"] + "_" + study_info["SessionID"]
            )
            return (pvdset, study_info, subj_sess_name)
        else:
            return None
    else:
        return None


def convert_single_study_bruker(
    path, output_dir, acq_categories=msc.acq_categories_BIDS
):
    brk_dir_info = check_valid_dir_bruker(path)
    if brk_dir_info is None:
        return None
    else:
        pvdset = brk_dir_info[0]
        study_info = brk_dir_info[1]
        subj_sess_name = brk_dir_info[2]

        if not os.path.exists(output_dir):
            os.mkdir(output_dir)

        output_dir = os.path.join(output_dir, "sourcedata")
        if not os.path.exists(output_dir):
            os.mkdir(output_dir)

        output_subject_dir = os.path.join(output_dir, subj_sess_name)

        if not os.path.exists(output_subject_dir):
            os.mkdir(output_subject_dir)

        for i, (scan_id, recos) in enumerate(pvdset._avail.items()):
            method_file = pvdset.get_method(scan_id)
            scan_method = method_file.parameters["Method"]
            try:
                mt_on_off = method_file.parameters["PVM_MagTransOnOff"]
            except KeyError:
                mt_on_off = None

            for reco_id in recos:
                visu_pars = pvdset.get_visu_pars(scan_id, reco_id)
                series_type = visu_pars.parameters["VisuSeriesTypeId"]
                if series_type != "DERIVED_ISA":  # == ACQ_BRUKER_PVM
                    seq_name = visu_pars.parameters["VisuAcquisitionProtocol"]
                    try:
                        echo_time = visu_pars.parameters["VisuAcqEchoTime"]
                    except KeyError:
                        echo_time = None

                    try:
                        acqp = pvdset.get_acqp(scan_id)
                        rg = acqp.parameters["RG"]
                    except Exception:
                        rg = None

                    try:
                        reco = pvdset.pvobj.get_reco(scan_id, reco_id)
                        reco_slope = reco.parameters["RECO_map_slope"]
                    except Exception:
                        reco_slope = None

                    params = {
                        "scan_method": scan_method,
                        "mt_on_off": mt_on_off,
                        "echo_time": echo_time,
                        "seq_name": seq_name,
                    }

                    extra_info = {
                        "RecieverGain": rg,
                        "RecoSlope": reco_slope,
                    }

                    acq_modality = get_modality_bruker(params)
                    acq_filename = (
                        f"{subj_sess_name}_acq-{scan_id}_run-{reco_id}_{acq_modality}"
                    )

                    acq_category = acq_categories[acq_modality]
                    acq_output_dir = os.path.join(output_subject_dir, acq_category)

                    if not os.path.exists(acq_output_dir):
                        os.mkdir(acq_output_dir)

                    convert_and_save_nifti_bruker(
                        pvdset,
                        scan_id,
                        reco_id,
                        acq_filename,
                        dir=acq_output_dir,
                        ext="nii.gz",
                    )
                    create_metadata_json_bruker(
                        pvdset,
                        scan_id,
                        reco_id,
                        acq_filename,
                        dir=acq_output_dir,
                        subject_info=study_info,
                        extra_info=extra_info,
                        metadata_dict=msc.metadata_ref_BIDS_bruker,
                    )

                    if acq_modality == "dwi":
                        pvdset.save_bdata(scan_id, acq_filename, dir=acq_output_dir)

        return subj_sess_name


def convert_studies_from_bruker(root_path, output_dir, return_list=False):
    converted_studies = []

    # if not os.path.exists(root_path):
    #     print(f"\n{lggr.error}Input folder does not exist")
    #     return

    studies_to_convert, present_studies = get_studies_to_convert_bruker(
        root_path, output_dir
    )
    if len(studies_to_convert) != 0:
        progress_message = f"{lggr.info}Converting studies from Bruker raw data"
        print()
        for folder in tqdm(studies_to_convert, desc=progress_message):
            folder_path = os.path.join(root_path, folder)
            if os.path.isdir(folder_path) or zipfile.is_zipfile(folder_path):
                study_folder_name = convert_single_study_bruker(
                    folder_path, output_dir, acq_categories=msc.acq_categories_BIDS
                )
                if (
                    study_folder_name is not None
                    and study_folder_name not in converted_studies
                ):
                    converted_studies.append(study_folder_name)

        if return_list:
            return converted_studies
    elif not present_studies:
        raise NotStudiesToConvertError


def subject_file_present_bruker(path):
    return "subject" in os.listdir(path)


def get_studies_to_convert_bruker(root_path, output_dir):
    root_path_content = os.listdir(root_path)

    try:
        output_dir_content = os.listdir(os.path.join(output_dir, "sourcedata"))
    except FileNotFoundError:
        output_dir_content = []

    root_path_content = [
        x
        for x in root_path_content
        if (
            ut.is_folder_or_zip_and_not_occult(os.path.join(root_path, x))
            and subject_file_present_bruker(os.path.join(root_path, x))
        )
    ]
    if len(root_path_content) != 0:
        present_studies = True
    else:
        present_studies = False

    output_dir_content = [
        x
        for x in output_dir_content
        if ut.is_folder_and_not_occult(os.path.join(output_dir, "sourcedata", x))
    ]
    output_dir_content = [x.replace("sub-", "") for x in output_dir_content]

    studies_already_converted = [
        x for x in output_dir_content if any(x in item for item in root_path_content)
    ]

    studies_not_converted = [
        x
        for x in root_path_content
        if not any(item in x for item in output_dir_content)
    ]

    n_studies_already_converted = len(studies_already_converted)
    if n_studies_already_converted == 0:
        studies_to_convert = root_path_content
    elif len(studies_not_converted) == 0:
        print(
            f"\n{lggr.info}All studies ({n_studies_already_converted}) have already been converted before."
        )
        studies_to_convert = []
    else:
        print(
            f"\n{lggr.info}Some studies ({n_studies_already_converted}) have already been converted before. The rest will be converted now."
        )
        studies_to_convert = studies_not_converted

    return studies_to_convert, present_studies
