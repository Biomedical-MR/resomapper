import itertools
import numpy as np
import matplotlib.pyplot as plt

from scipy.optimize import least_squares
from skimage.transform import rotate
from matplotlib.widgets import Slider

###############################################################################
# Model definition
###############################################################################


def adcm_model(adcm, s0, b):
    """ADC mono-exponential decay model.

    s0 * exp(-b * ADCm)

    Args:
        adcm (float): ADC value.
        s0 (float): S0 value.
        b (float): B value.

    Returns:
        float: Calculated signal value.
    """
    return s0 * np.exp(-b * adcm)


def residual_monoexp(param, x, y):
    """Calculates the residual of the ADC mono-exponential decay model.

    Args:
        param (list): List of the model's parameters [adc, s0].
        x (float): Independent variable value (B value).
        y (float): Observed signal value.

    Returns:
        float: Residual value.
    """
    adcm = param[0]
    s0 = param[1]
    return y - adcm_model(adcm, s0, x)


def adcl_model(adcl, s0, b):
    """ADC linear model.

    ln(S) = ln(S0) - b * ADCl

    Args:
        adcl (float): ADC value.
        s0 (float): S0 value.
        b (float): B value.

    Returns:
        float: Calculated logarithm of signal value.
    """
    return np.log(s0) - (b * adcl)


def residual_linear(param, x, y):
    """Calculates the residual of the ADC linear model.

    Args:
        param (list): List of the model's parameters [adc, s0].
        x (float): Independent variable value (B value).
        y (float): Observed signal value.

    Returns:
        float: Residual value.
    """
    adcl = param[0]
    s0 = param[1]
    return np.log(y) - adcl_model(adcl, s0, x)


###############################################################################
# Fitting functions
###############################################################################

# img[pixel_x, pixel_y, slice, dirs+bvals]
# ADCm    0.0001 mm2/ms to 0.003 mm2/ms with step size of 0.00001 mm2/ms.
# bval    s/mm2


def fit_voxel(x, y, residual):
    """Fitting of an adc model curve for a single pixel, using non linear least squares.

    Args:
        x (list): Independent variable (B values).
        y (list): Observed signal values.
        residual (function): Function to calculate residual (residual_monoexponenital
            or residual_linear)

    Returns:
        list: Result of optimizing the model parameters [adc value, s0 value]
    """
    bounds = ([0, 0], [np.inf, np.inf])  # Lower and upper bounds for each parameter
    # diff_step = 0.00001
    x0 = [0.0005, 1000]  # Starting point for adc and s0
    # Note: starting points could be estimated differently for a more accurate start
    results = least_squares(
        residual,
        x0,
        args=(x, y),
        bounds=bounds,
        # diff_step=diff_step,
        # loss="soft_l1",
    )
    return results.x


def fit_volume(bvals, n_basal, n_bval, n_dirs, img, selected_model):
    """Fitting of an adc model curve for a whole image, using non linear least squares.

    Args:
        bvals (numpy.array): List of effective b values.
        n_basal (int): Number of basal images adquired.
        n_bval (int): Number of b values for each direction adquired.
        n_dirs (int): Number of directions adquired.
        img (numpy.array): Original image.
        selected_model (str): "m" if you want to fit the monoexponential decay model,
            "l" if you want to fit the linearized model.

    Returns:
        numpy.array: adc_map, map of calculated adc values.
        numpy.array: s0_map, map of calculated s0 values.
        numpy.array: residual_map, map of residual errors.
        numpy.array: predicted_data, map of predicted signal using the fitted model.
    """
    adc_map = np.zeros(list(img.shape[:3]) + [n_dirs])
    s0_map = np.zeros(list(img.shape[:3]) + [n_dirs])
    n_slices = img.shape[2]

    residual = residual_monoexp if selected_model == "m" else residual_linear

    # When more than 1 basal image, they are averaged and used as 1. Could be changed to
    # use all of them.
    for i in range(n_dirs):
        i_dir = n_basal + (n_bval * i)

        if n_basal > 1:
            xdata = np.append(np.mean(bvals[:n_basal]), bvals[i_dir : i_dir + n_bval])
        else:
            xdata = np.append(bvals[:n_basal], bvals[i_dir : i_dir + n_bval])

        for j in range(n_slices):
            for x in range(img.shape[0]):
                for y in range(img.shape[1]):
                    if all(img[x, y, j, :n_basal]):
                        if n_basal > 1:
                            ydata = np.append(
                                np.mean(img[x, y, j, :n_basal]),
                                img[x, y, j, i_dir : i_dir + n_bval],
                            )
                        else:
                            ydata = np.append(
                                img[x, y, j, :n_basal],
                                img[x, y, j, i_dir : i_dir + n_bval],
                            )

                        adc, s0 = fit_voxel(xdata, ydata, residual)
                        adc_map[x, y, j, i] = adc
                        s0_map[x, y, j, i] = s0

                    else:
                        adc_map[x, y, j, i] = np.nan

    predicted_data = np.zeros(list(img.shape[:3]) + [n_dirs * n_bval])
    residual_map = np.zeros(list(img.shape[:3]) + [n_dirs * n_bval])

    for x, y, j, i in itertools.product(
        range(img.shape[0]),
        range(img.shape[1]),
        range(n_slices),
        range(n_basal, img.shape[3]),
    ):
        i_dir = round((i - n_basal) / n_bval)
        if selected_model == "m":
            predicted_data[x, y, j, i - n_basal] = adcm_model(
                adc_map[x, y, j, i_dir], s0_map[x, y, j, i_dir], bvals[i]
            )
        else:
            predicted_data[x, y, j, i - n_basal] = np.exp(
                adcl_model(adc_map[x, y, j, i_dir], s0_map[x, y, j, i_dir], bvals[i])
            )
        residual_map[x, y, j, i - n_basal] = (
            img[x, y, j, i] - predicted_data[x, y, j, i - n_basal]
        )

    return adc_map, s0_map, residual_map, predicted_data


###############################################################################
# Show fitted curves
###############################################################################


def show_fitting_adc(adc_map, s0_map, data, bval, selected_model, n_basal, n_b_val):
    """Shows the resulting ADC map and the fitted curves for each pixel.

    To see the curves, click on a pixel and a graph will appear showing dots for the
    original data and a line showing the fitted curve. Use the sliders to browse between
    slices and directions.

    Args:
        adc_map (numpy.array): Calculated ADC values map.
        s0_map (numpy.array): Calculated S0 values map.
        data (numpy.array): Original image.
        bval (numpy.array): List of effective b values.
        selected_model (str): "m" if the monoexponential model was used for fitting,
            "l" if the linearized model was used.
        n_basal (int): Number of basal images adquired.
        n_b_val (int): Number of b values per direction.
    """
    initial_slice = 0
    initial_dir = 0
    current_slice = adc_map[:, :, initial_slice, initial_dir]
    s0 = s0_map[:, :, initial_slice, initial_dir]
    original_data = data
    bvalues = bval

    fig, ax = plt.subplots(1, 2, figsize=(15, 6))

    ax[0].imshow(
        np.fliplr(rotate(current_slice, 270)),
        extent=(0, 128, 128, 0),
        # cmap="turbo",
        # vmin=0.0001,
        # vmax=0.001,
    )
    ax[1].text(
        0.5,
        0.5,
        "Click on a pixel to show the curve fit.",
        size=15,
        ha="center",
    )

    # [left, bottom, width, height]
    slice_slider_ax = fig.add_axes([0.15, 0.03, 0.3, 0.03])
    slice_slider = Slider(
        slice_slider_ax,
        "Slice",
        0,
        adc_map.shape[2] - 1,
        valinit=initial_slice,
        valstep=1,
    )
    dir_slider_ax = fig.add_axes([0.15, 0, 0.3, 0.03])
    dir_slider = Slider(
        dir_slider_ax,
        "Direction",
        0,
        adc_map.shape[3] - 1,
        valinit=initial_dir,
        valstep=1,
    )

    def update_slice(val):
        """Update the image when the slider value changes."""
        nonlocal current_slice
        nonlocal s0

        current_slice = adc_map[:, :, int(slice_slider.val), int(dir_slider.val)]
        s0 = s0_map[:, :, int(slice_slider.val), int(dir_slider.val)]

        ax[0].clear()
        ax[0].imshow(
            np.fliplr(rotate(current_slice, 270)),
            extent=(0, 128, 128, 0),
            # cmap="turbo",
            # vmin=0.0001,
            # vmax=0.001,
        )
        ax[1].clear()
        ax[1].text(
            0.5,
            0.5,
            "Click on a pixel to show the curve fit.",
            size=15,
            ha="center",
        )
        plt.show()

    slice_slider.on_changed(update_slice)
    dir_slider.on_changed(update_slice)

    def onclick(event):
        """Event handler to show the corresponding graph when a pixel is clicked."""
        # Get the pixel coordinates
        try:
            x, y = int(event.xdata), int(event.ydata)

            i_dir = int(dir_slider.val)
            i_slice = int(slice_slider.val)

            # Get the pixel value
            adc_value = current_slice[x, y]

            if np.isnan(adc_value):
                ax[1].clear()
                ax[1].text(
                    0.5,
                    0.5,
                    "Click on a pixel to show the curve fit.",
                    size=15,
                    ha="center",
                )
                plt.show()
                return

            s0_value = s0[x, y]

            x_data = np.append(
                bvalues[:n_basal],
                bvalues[
                    n_basal + (i_dir * n_b_val) : n_basal + (i_dir * n_b_val) + n_b_val
                ],
            )

            y_data = np.append(
                original_data[x, y, i_slice, :n_basal],
                original_data[
                    x,
                    y,
                    i_slice,
                    n_basal + (i_dir * n_b_val) : n_basal + (i_dir * n_b_val) + n_b_val,
                ],
            )

            if selected_model == "l":
                y_data = np.array([np.log(y) for y in y_data])
                y_fitted = [
                    adcl_model(adc_value, s0_value, b)
                    for b in range(int(x_data[0]), int(x_data[-1]))
                ]
                x_fitted = list(range(int(x_data[0]), int(x_data[-1])))

            else:
                y_fitted = [
                    adcm_model(adc_value, s0_value, b)
                    for b in range(int(x_data[0]), int(x_data[-1]))
                ]
                x_fitted = list(range(int(x_data[0]), int(x_data[-1])))

            ax[1].clear()

            ax[1].scatter(x_data, y_data, label="Raw data")
            ax[1].scatter(
                np.mean(x_data[:n_basal]), np.mean(y_data[:n_basal]), label="Basal mean"
            )
            ax[1].plot(x_fitted, y_fitted, "k", label="Fitted curve")
            if selected_model == "m":
                ax[1].set_ylabel("S")
            else:
                ax[1].set_ylabel("ln(S)")
            ax[1].set_xlabel("b value")
            ax[1].legend()
            ax[1].set_title(
                f"ADC value: {adc_value:.6f}. Pixel: {x},{y}. S0 value: {s0_value:.2f}."
            )

            plt.show()

        except (IndexError, TypeError):
            pass

    # Connect the onclick function to the figure
    cid = fig.canvas.mpl_connect("button_press_event", onclick)

    plt.show()
