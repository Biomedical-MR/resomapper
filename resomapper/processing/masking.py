import cv2

# import re
import numpy as np
import nibabel as nib
import matplotlib.pyplot as plt
from scipy.ndimage import rotate

from resomapper.core.misc import auto_innited_logger as lggr
import resomapper.core.utils as ut


import warnings

warnings.filterwarnings("ignore")


def no_mask(nifti_file_path, mask_nii_output_path):
    """
    Create a binary mask from a NIfTI file and save it to a specified output path.

    This function loads a NIfTI file, processes its data to create a mask of ones, 
    and saves the resulting mask as a new NIfTI file. If the input data is 4D, 
    only the first volume is used for the mask.

    Args:
        nifti_file_path (str): The file path to the input NIfTI file.
        mask_nii_output_path (str): The file path where the output mask NIfTI file will be saved.

    Returns:
        None

    Raises:
        FileNotFoundError: If the input NIfTI file does not exist.
        nib.filebasedimages.ImageFileError: If the input file is not a valid NIfTI file.
    """

    study_nii = nib.load(nifti_file_path)
    nii_data = study_nii.get_fdata()
    if len(np.shape(nii_data)) == 4:
        nii_data = nii_data[:, :, :, 0]

    ones_mask = np.ones_like(nii_data)

    nii_ima = nib.Nifti1Image(
            # TODO: CHECK WHICH TYPE IS BETTER
            # ones_mask, study_nii.affine, study_nii.header
            ones_mask.astype(np.float32), study_nii.affine, study_nii.header
        )
    nib.save(nii_ima, mask_nii_output_path)


def hist_strip_mask():
    # TODO
    pass


def manual_mask(nifti_file_path, mask_nii_output_path, ask_if_repeat=False):
    """
    Create a manual mask for a NIfTI file and save it to a specified output path.

    This function allows the user to interactively create a mask for each slice of a 3D or 4D NIfTI image. 
    The user can draw the mask outline using mouse clicks, and the function will save the resulting mask as a new NIfTI file.

    Args:
        nifti_file_path (str): The file path to the input NIfTI file.
        mask_nii_output_path (str): The file path where the output mask NIfTI file will be saved.
        ask_if_repeat (bool): If True, prompts the user to confirm the mask before saving. Defaults to False.

    Returns:
        None

    Raises:
        FileNotFoundError: If the input NIfTI file does not exist.
        nib.filebasedimages.ImageFileError: If the input file is not a valid NIfTI file.
    """

    print(
        f"\n{lggr.ask}Please create the mask for this study in the pop-up window\n"
        "- Left click: create lines between clicks to draw the mask outline\n"
        "- Rigth click: close the outline joining the first and last points and skip to next slice\n"
    )

    study_nii = nib.load(nifti_file_path)
    nii_data = study_nii.get_fdata()
    if len(np.shape(nii_data)) == 4:
        nii_data = nii_data[:, :, :, 0]
    # TODO: what happens with 1-slice images

    # TODO: check if this needs to be done always or only in DTI
    nii_data = min_max_normalization(nii_data) * 255

    x_dim, y_dim = np.shape(nii_data)[:2]  # get real dims
    images = prepare_vol(nii_data)

    # list of lists (one list per slice) for storing masks vertexes
    refPT = [[] for _ in range(len(images))]
    global counter
    counter = 0
    for ima in images:
        refPT = itera(ima, refPT)

    # TODO: extract to separate function
    # shows user their selection ans ask if it is ok
    if ask_if_repeat:
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

            ax[i].imshow(img_poly, cmap="gray")
            ax[i].set_title(f"Slice {i+1}")

        plt.tight_layout()
        for i in range(len(ax)):
            ax[i].axis("off")

        plt.show(block=False)
        correct_selection = ut.ask_user(
            "Is the created mask ok? If not, you can repeat it."
        )
        plt.close()
    else:
        correct_selection = True

    if correct_selection:
        # creates niimask file
        n_slc = np.shape(images)[0]
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

        nii_ima = nib.Nifti1Image(
            masks.astype(np.float32), study_nii.affine, study_nii.header
        )
        nib.save(nii_ima, mask_nii_output_path)
        # TODO???
        # return mask_nii_output_path
    else:
        manual_mask(nifti_file_path, mask_nii_output_path, ask_if_repeat=ask_if_repeat)


def check_mask_shape(img, mask):
    """
    Verify that the shape of the mask matches the shape of the image.
    
    This function checks if the dimensions of the provided mask are compatible with the dimensions of the input image. 
    It raises an error if the shapes do not match, ensuring that the mask can be correctly applied to the image.
    If the input arguments are file paths, the 'load_nifti' function is used to load the respective NIfTI files. 

    Args:
        img (numpy.ndarray or str): Input image array or path to the image file.
        mask (numpy.ndarray or str): The mask array or path  to be checked against the image.

    Returns:
        bool: True if mask and image match dimensions, False if not.
    """

    try:
        if not isinstance(img, np.ndarray):
            img_data = nib.load(img)
            img = img_data.get_fdata()
        if not isinstance(mask, np.ndarray):
            mask_data = nib.load(mask)
            mask = mask_data.get_fdata()
    except nib.filebasedimages.ImageFileError:
        print(f"\n{lggr.error}The file you have provided is not a NiFTI image.")
        return False

    if img.shape[:3] != mask.shape[:3]:
        print(
            f"\n{lggr.error}Mask and image have different shapes. "
            "Please check that you have selected a suitable mask for this study.\n\n"
            "More info:\n"
            f"- Image: size {img.shape[0]}x{img.shape[1]}, "
            f"{img.shape[2]} slices.\n"
            f"- Mask: size {mask.shape[0]}x{mask.shape[1]}, "
            f"{mask.shape[2]} slices."
        )
        return False
    else:
        return True
        

#### Functions for manual masking mode ####


def prepare_vol(vol_3d):
    """Some modifications on the volume: 270 degrees rotation and image flip.

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


def min_max_normalization(img):
    """Apply min-max normalization to the input image. Creates a copy of the input
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
    new_img = (np.asarray(new_img).astype(np.float32) - min_val) / (max_val - min_val)
    return new_img


def click(event, x, y, flags, param):
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


def itera(ima, refPT):
    """Iteratively display slices for masking. Left click adds a line and right
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

    cv2.namedWindow("Mask_drawing")  # creates a new window
    cv2.setMouseCallback("Mask_drawing", click, refPT)

    while True:
        if refPT[counter] == []:
            # shows umodified image first while your vertice list is empty
            cv2.imshow("Mask_drawing", ima)
            # cv2.waitKey(1)
        key = cv2.waitKey(1) & 0xFF
        try:
            if len(refPT[counter]) > 1:  # after two clicks
                ver = len(refPT[counter])  # saves a point
                line = refPT[counter][ver - 2 : ver]  # creates a line
                ima = cv2.line(
                    ima, line[0][0], line[1][0], (255, 255, 255), thickness=2
                )
                cv2.imshow("Mask_drawing", ima)
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
