import os
import shutil
import traceback
import argparse
import json
from pathlib import Path
from datetime import datetime

from resomapper.core.misc import auto_innited_logger as lggr
from resomapper.core.misc import NotStudiesToConvertError
from resomapper.core.misc import NotStudiesToProcessError
from resomapper.core.misc import NoModalsSelectedError
import resomapper.core.utils as ut
import resomapper.format_conversion.bruker_conversion as conv_brk
import resomapper.format_conversion.MRS_conversion as conv_mrs
import resomapper.processing.processing as prc
import resomapper.processing.preprocessing as preprc
import resomapper.processing.masking as msk
import resomapper.processing.heatmap as hmp
import resomapper.core.misc as msc

import warnings

warnings.filterwarnings("ignore")


def auto_prepare():
    parser = argparse.ArgumentParser(
        description='CLI tool to run resomapper in batch mode.')
    
    parser.add_argument('-d', '--directory', type=validate_directory, required=True, help='Path to root directory containing the studies')
    parser.add_argument('-j', '--json', type=validate_json, required=True, help='Path to JSON file with processing options')

    args = parser.parse_args()

    print(lggr.welcome)

    formatted_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{lggr.info}Time: {formatted_time}")

    print(f"\n{lggr.info}Input options:")
    root_path = args.directory
    options_json = args.json
    print(f"Provided root path: {root_path}")
    print(f"Provided JSON file: {options_json}")
    os.chdir(root_path)

    with open(options_json, 'r') as file:
        options = json.load(file)

    if options["input_format"] != "c":
        output_path = os.path.join(root_path, "resomapper_output")
        ut.create_readme(output_path)
        if options["input_format"] == "b":
            conv_brk.convert_studies_from_bruker(
                root_path, output_path, return_list=False
            )
        elif options["input_format"] == "m":
            conv_mrs.convert_studies_from_MRS(root_path, output_path, return_list=False)
        # elif options["input_format"] == "d":
        #     pass
        print(
            f"\n{lggr.info}Studies have been converted and stored in the resomapper_output folder, "
            "under the sourcedata folder."
        )
    else:
        output_path = root_path
        if "sourcedata" not in os.listdir(output_path):
            raise NotStudiesToProcessError
        
    modals_to_process = options["modals_to_process"]
    acqs_to_process = prc.get_studies_to_process(output_path, modals_to_process, auto_mode=True)

    auto_process(acqs_to_process, output_path, options)

def auto_process(acqs_to_process, output_path, options):
    
    sourcedata_dir = os.path.join(output_path, "sourcedata")
    derivatives_dir = os.path.join(output_path, "derivatives")
    for study in acqs_to_process:
        if len(acqs_to_process[study]) != 0:
            print(f"\n\n\n\n{lggr.new_patient1}{study} {lggr.new_patient2}")

            study_derivatives_dir = os.path.join(derivatives_dir, study)
            if not os.path.exists(study_derivatives_dir):
                os.mkdir(study_derivatives_dir)

            for modal in acqs_to_process[study]:
                print(f"\n\n{lggr.new_modal}{modal[0]} ({modal[1]})")
                formatted_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                print(f"\n{lggr.info}Time: {formatted_time}")

                acq_folder_name = f"{modal[0]}_{modal[1]}_{study}"
                study_acq_derivatives_dir = os.path.join(
                    study_derivatives_dir, acq_folder_name
                )
                if os.path.exists(study_acq_derivatives_dir):
                    shutil.rmtree(study_acq_derivatives_dir)
                os.mkdir(study_acq_derivatives_dir)

                nifti_filename_list = ut.get_nifti_filenames(
                    sourcedata_dir, study, modal[1]
                )

                if modal[0] == "MTR map":
                    print(f"\n{lggr.info}{len(nifti_filename_list)} runs of MT images will be processed.")
                    mtoff_nifti_filename_list = ut.get_nifti_filenames(
                        sourcedata_dir, study, "_MToff"
                    )
                    mton_nifti_filename_list = nifti_filename_list
                    nifti_filename_list = [
                        elem
                        for pair in zip(
                            mton_nifti_filename_list, mtoff_nifti_filename_list
                        )
                        for elem in pair
                    ]
                else:
                    nifti_filename_list = [nifti_filename_list[0]]

                #### COPY ORIGINAL FILES TO DERIVATIVES FOLDER ####

                processing_filenames_list = []
                for original_filename_path in nifti_filename_list:
                    new_derivatives_filename = os.path.join(
                        study_acq_derivatives_dir,
                        os.path.basename(original_filename_path),
                    )
                    shutil.copy(original_filename_path, new_derivatives_filename)
                    processing_filenames_list.append(new_derivatives_filename)

                    shutil.copy(
                        original_filename_path.replace(".nii.gz", ".json"),
                        new_derivatives_filename.replace(".nii.gz", ".json"),
                    )
                    if modal[0] == "DTI":
                        shutil.copy(
                            original_filename_path.replace(".nii.gz", ".bval"),
                            new_derivatives_filename.replace(".nii.gz", ".bval"),
                        )
                        shutil.copy(
                            original_filename_path.replace(".nii.gz", ".bvec"),
                            new_derivatives_filename.replace(".nii.gz", ".bvec"),
                        )

                #### APPLY DENOISING FILTER ####

                if options[modal[0]]["denoising"]:
                    selected_filter = options[modal[0]]["denoising_filter"]
                    params = options[modal[0]]["denoising_params"]

                    for i, nifti_filename in enumerate(
                            nifti_filename_list, start=0
                        ):
                            params, denoised_nii_output_path, selected_filter = (
                                preprc.denoise(
                                    nifti_filename,
                                    modal[0],
                                    study_acq_derivatives_dir,
                                    params=params,
                                    selected_filter=selected_filter,
                                )
                            )
                            processing_filenames_list[i] = denoised_nii_output_path

                #### CREATE MASK ####

                mask_nii_filename = os.path.basename(
                    processing_filenames_list[0]
                ).replace(".nii.gz", "_mask.nii.gz")
                mask_nii_output_path = os.path.join(
                    study_acq_derivatives_dir, mask_nii_filename
                )
                msk.no_mask(processing_filenames_list[0], mask_nii_output_path)
                
                #### PROCESS STUDY ####
                if modal[0] == "MTR map":
                    for i in range(0, len(processing_filenames_list), 2):
                        # MTon = i, MToff = i+1
                        prc.process_MTRmap(
                            processing_filenames_list[i],
                            processing_filenames_list[i + 1],
                            mask_nii_output_path,
                        )
                        hmp.auto_save_heatmap(
                            processing_filenames_list[i].replace(".nii.gz","_MTR-processedmap.nii.gz").replace("_MTon",""), "MTRmap"
                        )
                elif modal[0] == "T1 map":
                    prc.process_Tmap(
                        processing_filenames_list[0],
                        mask_nii_output_path,
                        "T1",
                        ask_remove_times=False,
                    )
                    hmp.auto_save_heatmap(
                        processing_filenames_list[0].replace(".nii.gz","_T1-processedmap.nii.gz"), "T1map"
                    )
                elif modal[0] == "T2 map":
                    prc.process_Tmap(
                        processing_filenames_list[0],
                        mask_nii_output_path,
                        "T2",
                        ask_remove_times=False,
                    )
                    hmp.auto_save_heatmap(
                        processing_filenames_list[0].replace(".nii.gz","_T2-processedmap.nii.gz"), "T2map"
                    )
                elif modal[0] == "T2star map":
                    prc.process_Tmap(
                        processing_filenames_list[0],
                        mask_nii_output_path,
                        "T2star",
                        ask_remove_times=False,
                    )
                    hmp.auto_save_heatmap(
                        processing_filenames_list[0].replace(".nii.gz","_T2star-processedmap.nii.gz"), "T2starmap"
                    )
                elif modal[0] == "DTI":
                    prc.process_DTI(
                        processing_filenames_list[0],
                        mask_nii_output_path,
                        ask_user_info=False,
                        ask_remove_dirs=False,
                    )
                    hmp.auto_save_heatmap(
                        processing_filenames_list[0].replace(".nii.gz","_DTI-MD-processedmap.nii.gz"), "MDmap"
                    )
                    hmp.auto_save_heatmap(
                        processing_filenames_list[0].replace(".nii.gz","_DTI-AD-processedmap.nii.gz"), "ADmap"
                    )
                    hmp.auto_save_heatmap(
                        processing_filenames_list[0].replace(".nii.gz","_DTI-RD-processedmap.nii.gz"), "RDmap"
                    )
                    hmp.auto_save_heatmap(
                        processing_filenames_list[0].replace(".nii.gz","_DTI-FA-processedmap.nii.gz"), "FAmap"
                    )
                    # hmp.auto_save_heatmap(
                    #     processing_filenames_list[0].replace(".nii.gz","_DTI-ADC-processedmap.nii.gz"), "ADCmap"
                    # )

    formatted_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n\n{lggr.info}Time: {formatted_time}")
    print(f"\n{lggr.success}Processing completed!")

                

def validate_directory(path):
    """Validates that the path is an existing directory."""
    if not os.path.isdir(path):
        raise argparse.ArgumentTypeError(f"The path {path} is not a valid directory.")
    return path

def validate_json(path):
    """Validates that the file is a valid JSON file."""
    path = Path(path)
    if not path.is_file():
        raise argparse.ArgumentTypeError(f"The file {path} is not a valid file.")
    
    # Attempt to load the JSON file to check its validity
    try:
        with open(path, 'r') as file:
            json.load(file)
    except json.JSONDecodeError:
        raise argparse.ArgumentTypeError(f"The file {path} is not a valid JSON file.")
    
    return path

def create_options_template_auto(output_path, ref_dict=msc.auto_processing_options):
    with open(output_path, 'w') as json_file:
        json.dump(ref_dict, json_file, indent=4)

#### MAIN ####

def run_auto():
    try:
        auto_prepare()
    except KeyboardInterrupt:
        print(f"\n\n{lggr.error}You have exited from resomapper.")
    except NotStudiesToConvertError:
        print(f"\n\n{lggr.error}There are no studies to convert in the selected folder.")
    except NotStudiesToProcessError:
        print(f"\n\n{lggr.error}There are no studies to process in the selected folder.")
    except NoModalsSelectedError:
        print(f"\n\n{lggr.error}You haven't selected any modalities to process.")
    except Exception as err:
        print(f"\n\n{lggr.error}The following error has ocurred: {err}\n")
        print("More information:\n")
        traceback.print_exc()

if __name__ == "__main__":
    run_auto()