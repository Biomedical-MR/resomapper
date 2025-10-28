import numpy as np


def compute_MTR_map(mton_image: np.array, mtoff_image: np.array):
    """Computes the formula required to get MTR map."""

    mtr_map = 100 * (1 - (mton_image / mtoff_image))
    mtr_map[mtr_map < 0] = 0

    return mtr_map

def check_slopes_MT_images():
    pass

def check_slices_MT_images():
    pass