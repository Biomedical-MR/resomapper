import os
import re
import json
import pydicom
from tqdm import tqdm
from pydicom import dcmread
from resomapper.core.misc import NotStudiesToConvertError
from resomapper.core.misc import auto_innited_logger as lggr
import resomapper.core.utils as ut
import resomapper.core.misc as msc
import resomapper.format_conversion.DICOM_conversion as dcmconv

import warnings

warnings.filterwarnings("ignore")


def get_modality_MRS(params, conditions_dict=msc.conditions_dict_MRS):
    for modality in conditions_dict:
        if is_modality_MRS(modality, params, conditions_dict):
            return modality
    return "etc"


def is_modality_MRS(modality, params, conditions_dict=msc.conditions_dict_MRS):
    return all(cond(params) for cond in conditions_dict[modality])


def convert_single_study_MRS(path, output_dir, acq_categories=msc.acq_categories_BIDS):
    # brk_dir_info = check_valid_dir_MRS(path)
    # if brk_dir_info is None:
    #     return None
    # else:

    if not os.path.exists(output_dir):
        os.mkdir(output_dir)
    output_dir = os.path.join(output_dir, "sourcedata")
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)

    
    # output_subject_dir = os.path.join(output_dir, subj_sess_name)
    # if not os.path.exists(output_subject_dir):
    #     os.mkdir(output_subject_dir)

    dicom_dir = os.path.join(path, "DICOM")
    sur_dir = os.path.join(path, "Image")
    # nifti_dir = os.path.join(path, "Nifti")

    first_acq = True
    for acq_id in os.listdir(dicom_dir):
        acq_folder_path = os.path.join(dicom_dir, acq_id)
        if ut.is_folder_and_not_occult(acq_folder_path):
            for reco_id in os.listdir(acq_folder_path):
                reco_folder_path = os.path.join(acq_folder_path, reco_id)
                if ut.is_folder_and_not_occult(reco_folder_path):

                    
                    # Check type of sequence
                    first_file = os.listdir(reco_folder_path)[0]
                    ds_first = dcmread(os.path.join(reco_folder_path, first_file))

                    params = {"seq_name": ds_first[0x0018, 0x0024].value,
                              "patient_name": ds_first[0x0010, 0x0010].value,
                              "patient_ID": ds_first[0x0010, 0x0020].value,
                              "accs_num": ds_first[0x0008, 0x0050].value,
                              "modality": ds_first[0x0008, 0x0060].value, # either MR or PET
                              "image_type": ds_first[0x0008, 0x0008].value, # ORIGINAL or DERIVED
                              } 
                    # TODO: delete recoID =1 if every derived image is marked as so
                    if "DERIVED" not in params["image_type"] and reco_id == "1":
                        acq_modality = get_modality_MRS(params)

                        if first_acq:
                            sub_name = "_".join(map(str, [params["patient_ID"], params["accs_num"],  params["patient_name"]]))
                            first_acq = False
                        acq_filename = (
                            f"sub-{sub_name}_acq-{acq_id}_run-{reco_id}_{acq_modality}"
                        )
                        output_subject_dir = os.path.join(output_dir, sub_name)
                        if not os.path.exists(output_subject_dir):
                            os.mkdir(output_subject_dir)

                        acq_category = acq_categories[acq_modality]
                        acq_output_dir = os.path.join(output_subject_dir, acq_category)

                        if not os.path.exists(acq_output_dir):
                            os.mkdir(acq_output_dir)

                        nii_output_path = os.path.join(acq_output_dir, acq_filename+".nii.gz")
                        json_output_path = os.path.join(acq_output_dir, acq_filename+".json")

                        if acq_modality == "localizer":
                            dcmconv.convert_dicom_localizer(reco_folder_path, nii_output_path)
                        else:
                            dcmconv.convert_dicom_series(reco_folder_path, nii_output_path)

                        create_metadata_json_MRS(reco_folder_path,json_output_path,acq_modality,metadata_ref_dict=msc.metadata_ref_DICOM_MRS)

                        if acq_modality == "dwi":
                            btable_path = os.path.join(sur_dir, acq_id, reco_id, "btable.txt")
                            btable_to_bval_bvlec(btable_path, acq_filename, acq_output_dir)

    return sub_name


def convert_studies_from_MRS(root_path, output_dir, return_list=False):
    converted_studies = []
    studies_to_convert, present_studies = get_studies_to_convert_MRS(
        root_path, output_dir
    )

    if len(studies_to_convert) != 0:
        progress_message = (
            f"{lggr.info}Converting studies from MRSolutions DICOM and SUR data"
        )
        print()
        for folder in tqdm(studies_to_convert, desc=progress_message):
            folder_path = os.path.join(root_path, folder)
            if ut.is_folder_and_not_occult(folder_path):
                study_folder_name = convert_single_study_MRS(
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


def get_studies_to_convert_MRS(root_path, output_dir):
    root_path_content = os.listdir(root_path)

    try:
        output_dir_content = os.listdir(os.path.join(output_dir, "sourcedata"))
    except FileNotFoundError:
        output_dir_content = []

    root_path_content = [
        x
        for x in root_path_content
        if (
            ut.is_folder_and_not_occult(os.path.join(root_path, x))
            and study_files_present_MRS(os.path.join(root_path, x))
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
        if not any(x in item for item in output_dir_content)
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

def btable_to_bval_bvlec(btable_path, output_filename, output_path):
    with open(btable_path, 'r') as f:
        lines = f.readlines()

    # Initialize empty lists for bvals and bvecs
    bvals = []
    bvec_x = []
    bvec_y = []
    bvec_z = []

    # Process each line of the btable.txt file
    for line in lines:
        # Split the line into individual values (tab-separated)
        values = line.strip().split('\t')
        
        # The first value is the b-value
        bvals.append(values[0])
        
        # The second, third, and fourth values are the x, y, z components of the b-vector
        bvec_x.append(values[1])
        bvec_y.append(values[2])
        bvec_z.append(values[3])

    bval_output_path = os.path.join(output_path,output_filename+".bval")
    # Write the bvals to a .bval file (space-separated on one line)
    with open(bval_output_path, 'w') as f:
        f.write(' '.join(bvals) + '\n')

    bvec_output_path = os.path.join(output_path,output_filename+".bvec")
    # Write the bvecs to a .bvec file (each component on a separate line)
    with open(bvec_output_path, 'w') as f:
        f.write(' '.join(bvec_x) + '\n')
        f.write(' '.join(bvec_y) + '\n')
        f.write(' '.join(bvec_z) + '\n')

def create_metadata_json_MRS(dicom_path, json_output_path, seq_type, metadata_ref_dict=msc.metadata_ref_DICOM_MRS):
    # TODO
    # json_output_path = os.path.join(output_path, output_filename+".json")
    info_json = {}


    first_file = os.listdir(dicom_path)[0]
    dicom_data = dcmread(os.path.join(dicom_path,first_file))
    
    for bids_key, dicom_field in metadata_ref_dict.items():
        try:
            value = getattr(dicom_data, dicom_field, None)
            info_json[bids_key] = dicom_to_json_serializable(value) if value is not None else None
        except AttributeError:
            info_json[bids_key] = None

    if "T1" in seq_type:
        rep_times = dcmconv.get_rep_times_from_dicom(dicom_path)
        info_json["RepetitionTime"] = dicom_to_json_serializable(rep_times)
    if "T2" in seq_type:
        echo_times = dcmconv.get_echo_times_from_dicom(dicom_path)
        info_json["EchoTime"] = dicom_to_json_serializable(echo_times)

    with open(json_output_path, "w") as f:
        json.dump(info_json, f, indent=4)

def dicom_to_json_serializable(value):
    if isinstance(value, pydicom.valuerep.PersonName) or isinstance(value, pydicom.valuerep.DSfloat) or isinstance(value, pydicom.valuerep.IS):
        return str(value)
    elif isinstance(value, pydicom.uid.UID):
        return str(value)
    elif isinstance(value, list): 
        return [dicom_to_json_serializable(v) for v in value]
    return value

def study_files_present_MRS(path):
    # TODO: is a valid directory??
    return True

MRsolutionsKeys = ['mtc_on']

def parse_PPR_keywords(file_path, keys_list=MRsolutionsKeys):
    with open(file_path, 'rb') as f:
        ppr_text = f.read()
    ppr_text = ppr_text.decode('ascii', errors='ignore').replace('\r\n', '')
    
    par = {}
    if len(ppr_text) > 0:

        for i in keys_list:
            exp = ''.join(["(", i, ")[^_](.*?)(:)"])
            match = re.findall(exp, ppr_text, flags=re.S)
            if match:
                matches = re.findall(exp, ppr_text, flags=re.S)[0]
                tmp = dict(zip(matches[::2], matches[1::2]))
                par.update(tmp)
    else:
        par = {}
    
    return par

def add_SUR_info_to_json():
    pass
