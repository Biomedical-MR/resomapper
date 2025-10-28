import os
import glob
import shutil
import traceback
from colorama import just_fix_windows_console

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

import warnings

warnings.filterwarnings("ignore")


def cli_prepare():
    """Comand Line Interface of resomapper.

    1. Select root directory where studies are stored.
    2. Convert studies to nifti and organize them.
    3. Select of modalities to be processed.
    4. Process selected studies and save results.
    """

    # Ensure color text shows
    just_fix_windows_console()

    # Set root directory
    print(lggr.welcome)

    input_format = cli_select_input_format()

    print(f"\n{lggr.ask}Please select the root working directory in the pop-up window.")
    root_path = ut.select_directory()

    os.chdir(root_path)

    if input_format != "c":
        output_path = os.path.join(root_path, "resomapper_output")
        ut.create_readme(output_path)
        if input_format == "b":
            conv_brk.convert_studies_from_bruker(
                root_path, output_path, return_list=False
            )
        elif input_format == "m":
            conv_mrs.convert_studies_from_MRS(root_path, output_path, return_list=False)
        # elif input_format == "d":
        #     pass
        print(
            f"\n{lggr.info}Studies have been converted and stored in the resomapper_output folder, "
            "under the sourcedata folder."
        )
    else:
        output_path = root_path
        if "sourcedata" not in os.listdir(output_path):
            raise NotStudiesToProcessError

    modals_to_process = ut.select_modalities_to_process()
    acqs_to_process = prc.get_studies_to_process(output_path, modals_to_process)

    cli_process(acqs_to_process, output_path)


def cli_process(acqs_to_process, output_path):
    """
    Manage the interactive processing of acquisition data for a study.

    This function facilitates the step-by-step processing of various modalities
    for each study in the provided acquisition list. It handles directory creation,
    file copying, and user interactions for selecting processing options.

    Args:
        acqs_to_process (dict): A dictionary where keys are study identifiers and values are lists of modalities to process.
        output_path (str): The directory path where processed data and derivatives will be saved.
    """

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
                    mtoff_nifti_filename_list = ut.get_nifti_filenames(
                        sourcedata_dir, study, "_MToff"
                    )

                    if len(mtoff_nifti_filename_list) == 0:
                        print(
                            f"\n{lggr.error}There is no MToff in this study to pair with the MTon. Skipping this modal."
                        )
                        continue
                    if len(nifti_filename_list) > 1:
                        print(
                            f"\n{lggr.warn}There are several files (runs) for this acquisition, probably due to reconstructing with different slopes."
                        )
                        mton_nifti_filename_list, mtoff_nifti_filename_list = (
                            cli_select_mt_runs(
                                nifti_filename_list, mtoff_nifti_filename_list
                            )
                        )

                    elif len(nifti_filename_list) == 1:
                        if len(mtoff_nifti_filename_list) > 1:
                            print(
                                f"\n{lggr.warn}There are several files (runs) for the MToff acquisition but only one for the MTon. Only the corresponding run will be processed."
                            )

                        mton_nifti_filename_list = nifti_filename_list
                        mtoff_nifti_filename_list = [mtoff_nifti_filename_list[0]]

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

                if ut.ask_user(
                    "Do you want to pre-process with a noise reduction filter?"
                ):
                    params, denoised_nii_output_path, selected_filter = preprc.denoise(
                        nifti_filename_list[0],
                        modal[0],
                        study_acq_derivatives_dir,
                        params=None,
                        selected_filter=None,
                    )
                    processing_filenames_list[0] = denoised_nii_output_path
                    if (
                        len(nifti_filename_list) > 1
                        and "_preproc" in processing_filenames_list[0]
                    ):
                        for i, nifti_filename in enumerate(
                            nifti_filename_list[1:], start=1
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

                #### APPLY GIBBS ARTIFACT SUPPRESION ####

                if ut.ask_user("Do you want to apply Gibbs artifact suppression?"):
                    gibbs_corrected, corrected_filename = preprc.gibbs_suppress(
                        processing_filenames_list[0]
                    )
                    if gibbs_corrected:
                        if corrected_filename != processing_filenames_list[0]:
                            processing_filenames_list[0] = corrected_filename

                        for i, nifti_filename in enumerate(
                            processing_filenames_list[1:], start=1
                        ):
                            gibbs_corrected, corrected_filename = preprc.gibbs_suppress(
                                nifti_filename, check_params=False
                            )
                            if corrected_filename != nifti_filename:
                                processing_filenames_list[i] = corrected_filename

                #### APPLY BIAS FIELD CORRECTION ####

                if ut.ask_user("Do you want to apply N4 bias field correction?"):
                    n4_corrected, corrected_filename, params = (
                        preprc.n4_bias_field_correct(processing_filenames_list[0])
                    )
                    if n4_corrected:
                        if corrected_filename != processing_filenames_list[0]:
                            processing_filenames_list[0] = corrected_filename

                        for i, nifti_filename in enumerate(
                            processing_filenames_list[1:], start=1
                        ):
                            n4_corrected, corrected_filename, _ = (
                                preprc.n4_bias_field_correct(
                                    nifti_filename, params=params, check_params=False
                                )
                            )
                            if corrected_filename != nifti_filename:
                                processing_filenames_list[i] = corrected_filename

                #### CREATE MASK ####

                mask_nii_filename = os.path.basename(
                    processing_filenames_list[0]
                ).replace(".nii.gz", "_mask.nii.gz")
                # TODO: remove _preproc in mask name if present?
                # mask_nii_filename = re.sub(r'run-\w+_', '', mask_nii_filename)
                # mask_nii_filename = re.sub(r'_preproc', '', mask_nii_filename)
                mask_nii_output_path = os.path.join(
                    study_acq_derivatives_dir, mask_nii_filename
                )
                mask_ok = False
                while not mask_ok:
                    mask_mode, most_recent_mask = cli_select_masking_mode(
                        study_derivatives_dir
                    )

                    if mask_mode == "m":
                        msk.manual_mask(
                            processing_filenames_list[0],
                            mask_nii_output_path,
                            ask_if_repeat=True,
                        )
                        mask_ok = True
                    elif mask_mode == "s":
                        selected_mask_file = ut.select_file()
                        mask_ok = msk.check_mask_shape(
                            processing_filenames_list[0], selected_mask_file
                        )
                        if mask_ok:
                            shutil.copy(selected_mask_file, mask_nii_output_path)
                    elif mask_mode == "n":
                        msk.no_mask(processing_filenames_list[0], mask_nii_output_path)
                        mask_ok = True
                    elif mask_mode == "r":
                        mask_ok = msk.check_mask_shape(
                            processing_filenames_list[0], most_recent_mask
                        )
                        if mask_ok:
                            shutil.copy(most_recent_mask, mask_nii_output_path)

                #### PROCESS STUDY ####
                if modal[0] == "MTR map":
                    for i in range(0, len(processing_filenames_list), 2):
                        # MTon = i, MToff = i+1
                        prc.process_MTRmap(
                            processing_filenames_list[i],
                            processing_filenames_list[i + 1],
                            mask_nii_output_path,
                        )
                        hmp.cli_show_and_save_heatmap(
                            processing_filenames_list[i]
                            .replace(".nii.gz", "_MTR-processedmap.nii.gz")
                            .replace("_MTon", ""),
                            "MTRmap",
                        )
                elif modal[0] == "T1 map":
                    output_basename = prc.process_Tmap(
                        processing_filenames_list[0],
                        mask_nii_output_path,
                        "T1",
                        ask_remove_times=True,
                    )
                    hmp.cli_show_and_save_heatmap(
                        # processing_filenames_list[0].replace(".nii.gz","_T1-processedmap.nii.gz"), "T1map"
                        output_basename + "_T1-processedmap.nii.gz",
                        "T1map",
                    )
                elif modal[0] == "T2 map":
                    output_basename = prc.process_Tmap(
                        processing_filenames_list[0],
                        mask_nii_output_path,
                        "T2",
                        ask_remove_times=True,
                    )
                    hmp.cli_show_and_save_heatmap(
                        # processing_filenames_list[0].replace(".nii.gz","_T2-processedmap.nii.gz"), "T2map"
                        output_basename + "_T2-processedmap.nii.gz",
                        "T2map",
                    )
                elif modal[0] == "T2star map":
                    output_basename = prc.process_Tmap(
                        processing_filenames_list[0],
                        mask_nii_output_path,
                        "T2star",
                        ask_remove_times=True,
                    )
                    hmp.cli_show_and_save_heatmap(
                        # processing_filenames_list[0].replace(".nii.gz","_T2star-processedmap.nii.gz"), "T2starmap"
                        output_basename + "_T2star-processedmap.nii.gz",
                        "T2starmap",
                    )
                elif modal[0] == "DTI":
                    output_basename = prc.process_DTI(
                        processing_filenames_list[0],
                        mask_nii_output_path,
                        ask_user_info=True,
                        ask_remove_dirs=True,
                    )
                    hmp.cli_show_and_save_heatmap(
                        # processing_filenames_list[0].replace(".nii.gz","_DTI-MD-processedmap.nii.gz"), "MDmap"
                        output_basename + "_DTI-MD-processedmap.nii.gz",
                        "MDmap",
                    )
                    hmp.cli_show_and_save_heatmap(
                        # processing_filenames_list[0].replace(".nii.gz","_DTI-AD-processedmap.nii.gz"), "ADmap"
                        output_basename + "_DTI-AD-processedmap.nii.gz",
                        "ADmap",
                    )
                    hmp.cli_show_and_save_heatmap(
                        # processing_filenames_list[0].replace(".nii.gz","_DTI-RD-processedmap.nii.gz"), "RDmap"
                        output_basename + "_DTI-RD-processedmap.nii.gz",
                        "RDmap",
                    )
                    hmp.cli_show_and_save_heatmap(
                        # processing_filenames_list[0].replace(".nii.gz","_DTI-FA-processedmap.nii.gz"), "FAmap"
                        output_basename + "_DTI-FA-processedmap.nii.gz",
                        "FAmap",
                    )
                    # hmp.cli_show_and_save_heatmap(
                    #    # processing_filenames_list[0].replace(".nii.gz","_DTI-ADC-processedmap.nii.gz"), "ADCmap"
                    #     output_basename+"_DTI-ADC-processedmap.nii.gz", "ADCmap"
                    # )

    print(f"\n\n{lggr.success}Processing completed!")


def cli_select_input_format():
    """
    Prompt the user to select the input data format for processing.

    Returns:
        str: The selected input data format as specified by the user.
    """

    question = "Select the input data format."

    options = {
        "b": "From Bruker raw data.",
        "m": "From MRSolutions data.",
        # "d": "From Dicom data.",
        "c": "From Nifti converted by resomapper.",
    }
    # TODO: implement the other two options

    return ut.ask_user_options(question, options)


def cli_select_masking_mode(study_dir):
    """
    Prompt the user to select a masking mode for a study.

    This function presents the user with options for providing a mask, including manual drawing,
    selecting an existing mask, or processing the image without a mask. It also checks for any previously
    created masks in the specified study directory and offers the option to reuse the most recent mask if available.

    Args:
        study_dir (str): The directory containing the study data and potential mask files.

    Returns:
        tuple: A tuple containing the selected masking mode and the path to the most recent mask, if available.
    """

    question = "Select how you want to provide the mask for this study."

    options = {
        "m": "Manual drawing of mask outline.",
        "s": "Selection of existing mask in NiFTI file.",
        "n": "Process whole image without mask.",
    }

    mask_files = glob.glob(os.path.join(study_dir, "*_mask.nii.gz"))
    if mask_files:
        options["r"] = "Reuse last mask created for this study."
        most_recent_mask = max(mask_files, key=os.path.getmtime)
    else:
        most_recent_mask = None

    return ut.ask_user_options(question, options), most_recent_mask


def cli_select_mt_runs(mton_filename_list, mtoff_filename_list):
    if len(mton_filename_list) != len(mtoff_filename_list):
        print(f"\n{lggr.warn}There are different number of MToff and MTon files.")
        n_mt = min(len(mton_filename_list), len(mtoff_filename_list))
    else:
        n_mt = len(mton_filename_list)

    print("\nMTon files:\n")
    for i, mton_filename in enumerate(mton_filename_list, start=1):
        print(f"({i}) {os.path.basename(mton_filename)}")
    print("\nMToff files:\n")
    for i, mtoff_filename in enumerate(mtoff_filename_list, start=1):
        print(f"({i}) {os.path.basename(mtoff_filename)}")

    input_ready = False
    while not input_ready:
        mt_folders_input = input(
            f"\n{lggr.ask}Please indicate the number of the run "
            f"that you want to process (between (1) and ({n_mt}), as shown in the list). "
            "If you want to process multiple runs, enter the different numbers "
            f'separated by ",".\n{lggr.pointer}'
        )
        mt_folders_input = mt_folders_input.split(",")
        try:
            mt_folders_list = [int(x.strip()) for x in mt_folders_input]
            input_ready = True
            for number in mt_folders_list:
                if (number > n_mt) or (number < 1):
                    print(
                        f"\n{lggr.error}Please enter numbers only between "
                        f"1 and {n_mt}."
                    )
                    input_ready = False
                    break
        except Exception:
            print(
                f"\n{lggr.error}Please, enter only numbers separated by "
                '"," (if more than one).'
            )
    selected_mton_filename_list = []
    selected_mtoff_filename_list = []
    for i in mt_folders_list:
        selected_mton_filename_list.append(mton_filename_list[i - 1])
        selected_mtoff_filename_list.append(mtoff_filename_list[i - 1])

    return selected_mton_filename_list, selected_mtoff_filename_list


#### MAIN ####


def run_cli():
    """Runs the CLI of resomapper, catching keyboard interruption to exit the program
    or any other errors during execution.
    """
    try:
        cli_prepare()
    except KeyboardInterrupt:
        print(f"\n\n{lggr.error}You have exited from resomapper.")
    except NotStudiesToConvertError:
        print(
            f"\n\n{lggr.error}There are no studies to convert in the selected folder."
        )
    except NotStudiesToProcessError:
        print(
            f"\n\n{lggr.error}There are no studies to process in the selected folder."
        )
    except NoModalsSelectedError:
        print(f"\n\n{lggr.error}You haven't selected any modalities to process.")
    except Exception as err:
        print(f"\n\n{lggr.error}The following error has ocurred: {err}\n")
        print("More information:\n")
        traceback.print_exc()


if __name__ == "__main__":
    run_cli()
