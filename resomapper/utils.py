import os
import shutil
from pathlib import Path

import cv2
import matplotlib.pyplot as plt
import numpy as np
from dipy.io.image import load_nifti, save_nifti
from scipy.ndimage import rotate

# from PIL import Image

import resomapper.file_system_functions as fs


class Headermsg:
    """Class containing headers for messages during execution of the CLI."""

    info = "\x1b[0;30;44m [INFO] \x1b[0m "
    warn = "\x1b[0;30;43m [WARNING] \x1b[0m "
    error = "\x1b[0;30;41m [ERROR] \x1b[0m "
    success = "\x1b[0;30;42m [SUCCESS] \x1b[0m "
    pointer = "\x1b[5;36;40m>>>\x1b[0m "
    ask = "\x1b[0;30;46m ? \x1b[0m "
    welcome = (
        "\n\x1b[0;30;46m                              \x1b[0m\n"
        + "\x1b[0;30;46m  \x1b[0m                          \x1b[0;30;46m  \x1b[0m\n"
        + "\x1b[0;30;46m  \x1b[0m  \x1b[0;36;40mWelcome to resomapper!\x1b[0m  "
        + "\x1b[0;30;46m  \x1b[0m\n"
        + "\x1b[0;30;46m  \x1b[0m                          \x1b[0;30;46m  \x1b[0m\n"
        + "\x1b[0;30;46m                              \x1b[0m\n"
    )
    new_patient1 = "\x1b[0;30;47m * STUDY *  "
    new_patient2 = " * STUDY * \x1b[0m "
    new_modal = "\x1b[0;30;47m > MODAL > \x1b[0m "


def ask_user(question):
    """Prompts the user with a question and expects a 'y' or 'n' answer.

    Args:
        question (str): The question to be displayed to the user.

    Returns:
        bool: True if the user answers 'y', False if the user answers 'n'.
    """
    while True:
        answer = input(
            "\n" + Headermsg.ask + question + " [y/n]\n" + Headermsg.pointer
        ).lower()
        if answer == "y":
            return True
        elif answer == "n":
            return False
        else:
            print(
                f"\n{Headermsg.error}Por favor, introduce una de las dos opciones. "
                "[y/n]\n"
            )


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
        print("\n" + Headermsg.ask + question)
        print("Por favor, selecciona una opción entre las siguientes:")
        for option, meaning in options.items():
            print(f"- [{option}]: {meaning}")
        user_input = input(Headermsg.pointer)

        if user_input in options:
            return user_input
        else:
            print(
                f"\n{Headermsg.error}Por favor, introduce una de las opciones "
                "especificadas.\n"
            )


# def check_shapes(img, mask, callback_func=None, study_path=None):
def check_shapes(img, mask):
    """Check if an image and mask have the same shapes (resolution and slices).
    If the input arguments are file paths, the 'load_nifti' function is used to load the
    respective NIfTI files. The program will terminate if the shapes of the image and
    mask do not match.

    Args:
        img (numpy.ndarray or str): Input image array or path to the image file.
        mask (numpy.ndarray or str): Input mask array or path to the image file.

    Returns:
        bool: True if mask and image match dimensions, False if not.
    """
    if not isinstance(img, np.ndarray):
        img, affine = load_nifti(img)
    if not isinstance(mask, np.ndarray):
        mask, affine = load_nifti(mask)

    if img.shape[:3] != mask.shape[:3]:
        print(
            f"\n{Headermsg.error}Mask and image have different shapes. "
            "Please check that you have selected a suitable mask for this study.\n\n"
            "More info:\n"
            f"- Image: resolution {img.shape[0]}x{img.shape[1]}, "
            f"{img.shape[2]} slices.\n"
            f"- Mask: resolution {mask.shape[0]}x{mask.shape[1]}, "
            f"{mask.shape[2]} slices."
        )
        return False
    else:
        return True
        # if (callback_func is not None) and (study_path is not None):
        #     mask = Mask(study_path)
        #     mode = mask.select_mask_mode()
        #     mask.create_mask(mode)
        #     callback_func()
        # else:
        #     exit()
        # exit()


###############################################################################
# Mask creation
###############################################################################
class Mask:
    def __init__(self, study_subfolder: str) -> None:
        """Initialize a new instance of the Mask class.

        Args:
            study_subfolder (str): The path or name of the study subfolder.
        """
        self.study_subfolder = study_subfolder

    def prepare_vol(self, vol_3d):
        """Some modifications are needed on the volume: 270 degrees
        rotation and image flip.

        Args:
            vol_3d (ndarray): Input image.

        Returns:
            list: Transformed image ready for visualization.
        """
        n_slc = vol_3d.shape[2]  # numer of slices
        vol_prepared = []
        rot_degrees = 270
        for j in range(n_slc):
            ima = vol_3d[:, :, j]
            ima = rotate(ima, rot_degrees)
            ima = np.flip(ima, axis=1)
            ima = ima.astype(np.uint8)

            # change only for better visualization purposes
            scale_percent = 440
            width = int(ima.shape[1] * scale_percent / 100)
            height = int(ima.shape[0] * scale_percent / 100)
            dim = (width, height)
            ima = cv2.resize(ima, dim, interpolation=cv2.INTER_AREA)
            vol_prepared.append(ima)

        return vol_prepared

    def min_max_normalization(self, img):
        """Applies min-max normalization to the input image. Creates a copy of the input
        image and computes the minimum and maximum values. The image is normalized using
        the formula (img - min_val) / (max_val - min_val).

        Args:
            img (numpy.ndarray): Input image array.

        Returns:
            numpy.ndarray: Normalized image array.
        """
        new_img = img.copy()
        new_img = new_img.astype(np.float32)

        min_val = np.min(new_img)
        max_val = np.max(new_img)
        new_img = (np.asarray(new_img).astype(np.float32) - min_val) / (
            max_val - min_val
        )
        return new_img

    def click(self, event, x, y, flags, param):
        """Event handler function for mouse clicks.

        Args:
            event: The type of mouse event (left button down, right button down, etc.).
            x: The x-coordinate of the mouse click position.
            y: The y-coordinate of the mouse click position.
            flags: Additional flags associated with the mouse event.
            param: Additional parameters associated with the mouse event.

        The function handles mouse click events and updates the global variables
        'status' and 'counter'. If the event is a left button down click, the function
        appends the coordinates of the click position to the list specified by
        'param[counter]'. If the event is a right button down click, the function
        performs the same action as the left click and also sets the 'status' variable
        to 0, indicating that the click operation is finished.

        Note:
            - The global variables 'status' and 'counter' are used and updated within
              this function.
            - The 'param' argument is expected to be a list or an array-like object.

        Example:
            mouse_params = [[] for _ in range(5)] # Create list to store click positions
            cv2.setMouseCallback("window", click, param=mouse_params)
        """
        global status
        global counter
        if event == cv2.EVENT_LBUTTONDOWN:  # left click
            click_pos = [(x, y)]
            param[counter].append(click_pos)
        elif event == cv2.EVENT_RBUTTONDOWN:  # right click
            click_pos = [(x, y)]
            param[counter].append(click_pos)
            status = 0  # finish

    def itera(self, ima, refPT):
        """Iteratively displays slices for masking.Left click adds a line and right
        click closes the polygon. Next slice will be showed after right click.

        Args:
            ima (numpy.ndarray): Input image array.
            refPT (list): List to store the masked vertices for each slice.

        The 'click' event handler is used to handle mouse events and update the 'refPT'
        list with the coordinates of the drawn lines. The function continues to display
        and process slices until all slices have been processed or until the 'c' key or
        a right-click event is detected. At that point, the function returns the updated
        'refPT' list.

        Note:
            - The global variables 'counter' and 'status' are used and updated within
              this function.
            - The 'click' event handler is set using 'cv2.setMouseCallback' with the
              'refPT' argument.

        Returns:
            list: Updated 'refPT' list with the masked vertices for each slice.

        Example:
            image = np.zeros((256, 256, 3), dtype=np.uint8)  # Create a blank image
            ref_points = [[] for _ in range(10)]  # Create list to store masked vertices
            masker = Mask(study_path)
            masked_vertices = masker.itera(image, ref_points)
        """
        global counter
        global status
        status = 1

        cv2.namedWindow("Imagen")  # creates a new window
        cv2.setMouseCallback("Imagen", self.click, refPT)

        while True:
            if refPT[counter] == []:
                # shows umodified image first while your vertice list is empty
                cv2.imshow("Imagen", ima)
                # cv2.waitKey(1)
            key = cv2.waitKey(1) & 0xFF
            try:
                if len(refPT[counter]) > 1:  # after two clicks
                    ver = len(refPT[counter])  # saves a point
                    line = refPT[counter][ver - 2 : ver]  # creates a line
                    ima = cv2.line(
                        ima, line[0][0], line[1][0], (255, 255, 255), thickness=2
                    )
                    cv2.imshow("Imagen", ima)
                    cv2.waitKey(1)
                    if key == ord("c") or status == 0:  # if 'c' key or right click
                        cv2.destroyAllWindows()
                        status = 1  # restore to 1
                        counter += 1  # pass to the next slice
                        break
            except IndexError:
                cv2.destroyAllWindows()
                break
        return refPT

    def draw_mask(self):
        """Creates a binary mask for the roi where processing will take place and saves
        it as a NIfTI file. The user is prompted to create the mask by selecting
        contours in a pop-up window.

        The function loads the appropriate input image based on the study type, prepares
        the volume and creates a list of lists, 'refPT', to store the vertexes of the
        masks for each slice. The user is then presented with the selected contours
        overlaid on the image slices, and the function saves the image files and waits
        for a keyboard enter from the user to proceed.

        Next, the function creates a binary mask by filling the contours with ones and
        resizing the mask to match the original image dimensions. The resulting masks
        are converted to a NIfTI format by transposing the axes to match the expected
        shape. The mask is saved both in the method subfolder.

        Example:
            masker = Mask(study_path)
            mask.draw_mask()
        """

        study_name = self.study_subfolder.parts[-2]
        print(
            f"\n{Headermsg.ask}Crea la máscara para el estudio {str(study_name)}"
            " en la ventana emergente.\n"
            "- Click izquierdo: unir las líneas del contorno de selección\n"
            "- Click derecho: cierrar el contorno uniendo primer y último punto\n"
        )

        if "T2E" in str(self.study_subfolder):
            try:
                (nii_data, affine) = load_nifti(
                    self.study_subfolder
                    / f"{self.study_subfolder.parts[-1][4:]}_subscan_0.nii.gz"
                )
            except FileNotFoundError:
                (nii_data, affine) = load_nifti(
                    self.study_subfolder
                    / f"{self.study_subfolder.parts[-1][4:]}.nii.gz"
                )
            nii_data = nii_data[:, :, :, 0]
        else:
            try:
                (nii_data, affine) = load_nifti(
                    self.study_subfolder
                    / f"{self.study_subfolder.parts[-1][3:]}_subscan_0.nii.gz"
                )
            except FileNotFoundError:
                (nii_data, affine) = load_nifti(
                    self.study_subfolder
                    / f"{self.study_subfolder.parts[-1][3:]}.nii.gz"
                )

            if len(np.shape(nii_data)) == 4:
                nii_data = nii_data[:, :, :, 0]
            if "DT" in str(self.study_subfolder):
                # normalise values to 0-255 range
                nii_data = self.min_max_normalization(nii_data) * 255

        x_dim, y_dim = np.shape(nii_data)[:2]  # get real dims
        images = self.prepare_vol(nii_data)

        # list of lists (one list per slice) for storing masks vertexes
        refPT = [[] for _ in range(len(images))]
        global counter
        counter = 0
        for ima in images:
            refPT = self.itera(ima, refPT)

        # shows user their selection and saves a .png file
        n_slc = np.shape(images)[0]
        rows = 2
        cols = int(np.ceil(n_slc / rows))

        fig, ax = plt.subplots(rows, cols, figsize=(10, 7))
        ax = ax.flatten()
        for i in range(n_slc):
            poly = np.array((refPT[i]), np.int32)
            img_copy = np.copy(images[i])
            img_poly = cv2.polylines(
                img_copy, [poly], True, (255, 255, 255), thickness=3
            )
            # Removed saving png images - not needed
            # im = Image.fromarray(img_poly)
            # im.save(self.study_subfolder / f"shape_slice_{str(i+1)}.png")

            ax[i].imshow(img_poly, cmap="gray")
            ax[i].set_title(f"Slice {i+1}")
            ax[i].axis("off")

        plt.tight_layout()
        keyboardClick = False
        while not keyboardClick:
            keyboardClick = plt.waitforbuttonpress(0)
        plt.close()

        # creates niimask file
        masks = []
        for i in range(n_slc):
            poly = np.array((refPT[i]), np.int32)
            background = np.zeros(images[i].shape)
            mask = cv2.fillPoly(background, [poly], 1)
            mask = cv2.resize(mask, (x_dim, y_dim), interpolation=cv2.INTER_NEAREST)
            mask = mask.astype(np.int32)
            masks.append(mask)
            # cv2.destroyAllWindows()
        masks = np.asarray(masks)
        masks = masks.transpose(2, 1, 0)

        # saving mask in method subfolder
        save_nifti(self.study_subfolder / "mask", masks.astype(np.float32), affine)

    def create_mask(self, mode="manual"):
        """Create a mask for the study image. Implemented modes:
        - 'manual': manual drawing, allowing several tries if user is not satisfied.
        - 'reuse': reuse last mask used for the current patient.
        - 'file_selection': manually select a mask file already created.

        Args:
            mode (str, optional): The mode indicating the masking behavior.
                Defaults to "manual".

        Returns:
            Path: Study's mask file path.
        """
        study_path = self.study_subfolder
        dst_mask_path = study_path / "mask.nii"
        reusing_mask_path = Path("/".join(study_path.parts[:-1])) / "mask.nii"
        if mode == "manual":
            correct_selection = False
            while not correct_selection:
                self.draw_mask()
                correct_selection = ask_user(
                    "¿Es la previsualización de la selección lo que deseas?"
                )
            print(f"\n{Headermsg.info}Máscara creada correctamente.")
            shutil.copy(dst_mask_path, reusing_mask_path)

        elif mode == "reuse":
            src_path = Path("/".join(study_path.parts[:-1])) / "mask.nii"
            shutil.copy(src_path, dst_mask_path)

        elif mode == "file_selection":
            src_path = fs.select_file()
            ok_file = False
            while not ok_file:
                if src_path in [dst_mask_path, reusing_mask_path]:
                    print(
                        f"\n{Headermsg.error}You selected the same mask as before. "
                        "Try again"
                    )
                    src_path = fs.select_file()
                    ok_file = False
                else:
                    ok_file = True
            ext = os.path.splitext(src_path)[1]
            if src_path is not None and ext in [".nii", ".gz"]:
                shutil.copy(src_path, dst_mask_path)
                shutil.copy(src_path, reusing_mask_path)
            else:
                print(f"\n{Headermsg.error}You didn't select a NiFTI file.")
                exit()

        else:
            print(f"\n{Headermsg.error}Invalid masking mode selected.")
            exit()

        return dst_mask_path

    def select_mask_mode(self, again=False):
        """Prompt the user to select the mode for specifying the mask for the study.
        The function checks if a previous mask file exists in the subject's folder to
        determine if the reuse option is available.

        Args:
            again (bool, optional): whether we are calling this function the first time
                or a second time after an error when checking the mask and image
                resolutions. In that case, the reuse option is not available.

        Returns:
            str: The selected mask mode.

        Possible return values:
            - "reuse": The user selected to reuse the last created mask.
            - "manual": The user selected manual selection mode.
            - "file_selection": The user selected to select another file.
        """
        study_path = self.study_subfolder
        options = {
            "m": "Selección manual de la máscara.",
            "s": "Seleccionar otro archivo (máscara en formato NiFTI).",
        }

        last_mask_path = Path("/".join(study_path.parts[:-1])) / "mask.nii"
        if last_mask_path.exists() and not again:
            options["r"] = "Reutilizar la última máscara creada para este sujeto."

        question = "Selecciona cómo quieres especificar la máscara para este estudio."
        selected_option = ask_user_options(question, options)
        if selected_option == "r":
            return "reuse"
        elif selected_option == "m":
            return "manual"
        elif selected_option == "s":
            return "file_selection"
