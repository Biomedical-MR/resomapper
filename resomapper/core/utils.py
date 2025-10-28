import os
import re
import shutil
import zipfile
import tkinter as tk
from pathlib import Path
from tkinter import filedialog

from resomapper.core.misc import auto_innited_logger as lggr

import warnings

warnings.filterwarnings("ignore")

#### GUI UTILITIES ####


def select_directory():
    """Allows selection of root directory showing a file explorer window.

    Returns:
        Path: full path to the selected directory."""

    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askdirectory()
    root.destroy()
    # root.mainloop()

    return Path(file_path)


def select_file():
    """Allows selection of a file showing a file explorer window.

    Returns:
        Path: full path to the selected file.
    """

    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename()
    root.destroy()
    # root.mainloop()

    return Path(file_path)


def select_modalities_to_process():
    """Select from a checklist those modalities to be processed.

    Returns:
        list: list of str with the selected modalities.
    """

    print(f"\n{lggr.ask}Select the modalities to process in the pop-up window.")

    # init tkinter
    root = tk.Tk()
    root.title("resomapper")

    row = 1
    selected_modals = []
    modalities = ["T1 map", "T2 map", "T2star map", "DTI", "MTR map"]

    # add label
    tk.Label(root, text="Select the modalities to process.").grid(row=0, sticky="w")

    # create checklist
    for modal in modalities:
        var = tk.IntVar()
        selected_modals.append(var)
        tk.Checkbutton(root, text=modal, variable=var).grid(row=row, sticky="w")
        row += 1

    # create button to close the window
    tk.Button(root, text="OK", command=root.destroy).grid(row=6, sticky="w", pady=4)
    root.mainloop()

    return [
        modalities[idx]
        for idx in range(len(modalities))
        if selected_modals[idx].get() == 1
    ]


def close_window(root):
    print("Closing window...")
    root.withdraw()
    root.destroy()
    root.quit()


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
                if value_type is bool:
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

                if value_type is str and not value:
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

    submit_button = tk.Button(root, text="OK", command=submit)
    submit_button.pack(pady=20)

    root.mainloop()
    try:
        return values
    except NameError:
        # TODO: change to raise specific error or check if this is neccesary
        print(
            f"\n\n{lggr.error}You have not selected any parameters. Exiting the program."
        )
        exit()


#### CLI UTILITIES ####


def ask_user(question):
    """Prompts the user with a question and expects a 'y' or 'n' answer.

    Args:
        question (str): The question to be displayed to the user.

    Returns:
        bool: True if the user answers 'y', False if the user answers 'n'.
    """
    while True:
        answer = input("\n" + lggr.ask + question + " [y/n]\n" + lggr.pointer).lower()
        if answer == "y":
            return True
        elif answer == "n":
            return False
        else:
            print(f"\n{lggr.error}Please, select one of the two options. [y/n]\n")


def ask_user_options(question, options):
    """Prompt a question to the user, display options with meanings,
    and return the selected option.

    Args:
        question (str): The question to ask the user.
        options (dict): A dictionary containing the available options as keys and
            their meanings as values.

    Returns:
        str: The selected option.
    """
    while True:
        print("\n" + lggr.ask + question)
        print("Please, select one of the following options:")
        for option, meaning in options.items():
            print(f"- [{option}]: {meaning}")
        user_input = input(lggr.pointer).lower()

        if user_input in options:
            return user_input
        else:
            print(f"\n{lggr.error}Please, select one of the specified otpions.\n")


#### FILE UTILITIES ####


def is_folder_and_not_occult(path):
    return (
        (os.path.isdir(path))
        and not os.path.basename(path).startswith(".")
        and os.path.basename(path) != "resomapper_output"
    )


def is_folder_or_zip_and_not_occult(path):
    return (
        (os.path.isdir(path) or zipfile.is_zipfile(path))
        and not os.path.basename(path).startswith(".")
        and os.path.basename(path) != "resomapper_output"
    )


def is_nii(filename):
    return filename.endswith(".nii") or filename.endswith(".nii.gz")


def get_modality_nii_acq(nii_file):
    if "_T2map_acq" in nii_file:
        return "T2 map"
    elif "_T2starmap_acq" in nii_file:
        return "T2star map"
    elif "_T1map_acq" in nii_file:
        return "T1 map"
    elif "_dwi" in nii_file:
        # TODO: allow choice between DTI or ADC
        return "DTI"
    elif "_MTon" in nii_file:
        return "MTR map"
    else:
        return None


def get_modality_nii_map(nii_file):
    if "_T2map" in nii_file:
        return "T2 map"
    elif "_T2starmap" in nii_file:
        return "T2star map"
    elif "_T1map" in nii_file:
        return "T1 map"
    elif "_DTI" in nii_file:
        return "DTI"
    elif "_MTR" in nii_file:
        return "MTR map"
    else:
        return None


def get_acq(filename):
    pattern = r"acq-[^_]+_"
    result = re.search(pattern, filename)
    return result.group().rstrip("_")


def get_nifti_filenames(sourcedata_dir, study, acq):
    matching_files = []

    regex_pattern = rf"{re.escape(study)}.*{re.escape(acq)}.*\.nii"
    pattern = re.compile(regex_pattern)

    for root, dirs, files in os.walk(sourcedata_dir):
        matching_files.extend(
            os.path.join(root, filename)
            for filename in files
            if pattern.search(filename)
        )
    return matching_files


def rename_associated_files(nifti_filename):
    if "_preproc" in nifti_filename:
        json_file = nifti_filename.replace("_preproc.nii.gz", ".json")
        bval_file = nifti_filename.replace("_preproc.nii.gz", ".bval")
        bvec_file = nifti_filename.replace("_preproc.nii.gz", ".bvec")
        for associated_file in [json_file, bval_file, bvec_file]:
            if os.path.exists(associated_file):
                shutil.copy(
                    associated_file,
                    nifti_filename.replace("nii.gz", associated_file.split(".")[-1]),
                )


def create_readme(output_dir):
    # TODO
    pass
