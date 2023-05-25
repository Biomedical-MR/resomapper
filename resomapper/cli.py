# import click
import multiprocessing
import os
import traceback
import warnings

from colorama import just_fix_windows_console

import resomapper.file_system_functions as fs
from resomapper.preprocessing import Preprocessing
from resomapper.processing import (
    DTIProcessor,
    MTProcessor,
    TimeCollector,
    TMapProcessor,
)
from resomapper.utils import Headermsg as hmg
from resomapper.utils import Mask, ask_user

warnings.filterwarnings("ignore")


def cli():
    """Comand Line Interface of resomapper:

    1. Select root directory where studies are stored.
    2. Convert Bruker studies to nifti.
    3. Select of modalities to be processed.
    4. Process selected studies and save results.
    """
    # Ensure color text shows
    just_fix_windows_console()

    # Set root directory
    print(hmg.welcome)
    print(f"\n{hmg.ask}Selecciona la carpeta de trabajo en la ventana emergente.")
    root_path = fs.select_directory()
    os.chdir(root_path)

    # create the file system builder object
    fs_builder = fs.FileSystemBuilder(root_path)

    # create the folder system
    fs_builder.create_dir()

    # get studies and convert them from bruker to niftii
    fs_builder.convert_bru_to_nii()

    # rename some study subfolders adding the acq method (T2,T2*,T1,D,MT,M0)
    fs_builder.rename_sutudies()
    print(
        f"\n{hmg.info}Se han etiquetado las carpetas de interés "
        "según su modalidad (T1, T2, T2star, MT, M0, D)."
    )

    # ask user for which modalities he wants to process and
    # replicate those studies in 'procesados'.
    fs_builder.transfer_files()
    print(
        f'\n{hmg.info}Se ha creado la carpeta "procesados" y se han '
        "trasferido los archivos."
    )

    # select those studies to be processed
    studies_to_process, modals_to_process = fs_builder.get_selected_studies()

    if not studies_to_process:
        print(f"\n{hmg.error}No hay estudios que procesar.")
        exit()

    # get times (TR, TE and/or TE*)
    if (
        ("T1" in modals_to_process)
        or ("T2" in modals_to_process)
        or ("T2E" in modals_to_process)
    ):
        time_collector = TimeCollector(root_path, studies_to_process, modals_to_process)
        f_time_paths = time_collector.get_times(how="auto")

    # generate parametric maps
    prev_patient_name = ""
    for study in studies_to_process:
        study_name = study.parts[-1]
        patient_name = study.parts[-2].split("_")[1:]
        if patient_name != prev_patient_name:
            print(
                f'\n\n\n\n{hmg.new_patient1}{"_".join(patient_name)} {hmg.new_patient2}'
            )
        prev_patient_name = patient_name[:]
        current_modal = study_name.split("_")[0]
        print(f"\n\n{hmg.new_modal}Procesamiento del mapa de {current_modal}")

        # Mask specification and creation
        mask = Mask(study)
        mode = mask.select_mask_mode()
        mask_path = mask.create_mask(mode)

        want_preprocess = ask_user("¿Deseas realizar un preprocesado de este estudio?")

        if study_name.startswith("DT"):
            dti_map_pro = DTIProcessor(root_path, study)
            if want_preprocess:
                Preprocessing([study]).preprocess()
            dti_map_pro.process_DTI()

        elif study_name.startswith("MT"):
            mt_map_pro = MTProcessor(study, mask_path)
            if want_preprocess:
                Preprocessing([study]).preprocess()
            mt_map_pro.process_MT()

        else:
            n_cpu = multiprocessing.cpu_count() - 1
            t_map_pro = TMapProcessor(
                study, mask_path, n_cpu=n_cpu, fitting_mode="nonlinear"
            )
            if want_preprocess:
                Preprocessing([study]).preprocess()
            t_map_pro.process_T_map(f_time_paths)

    fs_builder.empty_supplfiles()
    print(f"\n{hmg.success}Procesamiento terminado.")


def run_cli():
    """Runs the CLI of resomapper, catching keyboard interruption to exit the program
    or any other errors during execution.
    """
    try:
        cli()
    except KeyboardInterrupt:
        print(f"\n\n{hmg.error}Has salido del programa.")
    except Exception as err:
        print(f"\n\n{hmg.error}Se ha producido el siguiente error: {err}\n")
        # In case we did not select a correct root folder, the error message will be:
        # "No scans found, are you sure the input folder contains a Bruker study?"
        # In other cases, print more info on the error
        if "Bruker" not in str(err):
            print("Más información:\n")
            traceback.print_exc()


if __name__ == "__main__":
    run_cli()
