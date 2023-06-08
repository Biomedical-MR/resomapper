import numpy as np
import matplotlib.pyplot as plt

from scipy.optimize import curve_fit, least_squares
from skimage.transform import rotate


# class ADCmProcessor:
#     """Mono exponential ADC fitting."""

#     def __init__(self, root_path: str, study_path: str) -> None:
#         self.root_path = root_path
#         self.study_path = study_path


def fit_voxel_test(x, y):
    popt, pcov = curve_fit(lambda b, ADCm: np.exp(-b * ADCm), x, y)
    return popt, pcov


def adcm_model(adcm, s0, b):
    """ADC mono: single exponential decay.

    C * exp(-b * ADCm)
    """
    return s0 * np.exp(-b * adcm)


# def residual(param, x, y):
#     adcm = param[0]
#     return y - adcm_model(adcm, x)


def residual(param, x, y):
    adcm = param[0]
    s0 = param[1]
    return y - adcm_model(adcm, s0, x)


def fit_voxel(x, y):
    # bounds = ([0.0001, 0], [0.003, np.inf])
    # bounds = [0.0001, 0.003]
    bounds = ([0, 0], [np.inf, np.inf])
    # diff_step = 0.00001
    # x0 = [0.0005]
    x0 = [0.0005, 1000]
    results = least_squares(
        residual,
        x0,
        args=(x, y),
        bounds=bounds,
        # diff_step=diff_step,
        # loss="soft_l1",
    )
    return results.x


# img[x,y,slice,dirs+bvals]


def fit_volume(bvals, dirs, n_basal, n_bval, n_dirs, img):
    adcm_map = np.zeros(list(img.shape[:3]) + [n_dirs])
    s0_map = np.zeros(list(img.shape[:3]) + [n_dirs])
    n_slices = img.shape[2]
    # s0 = np.mean(img[:, :, :, :n_basal], axis=3)
    for i in range(n_dirs):
        i_dir = i + n_basal + ((n_bval - 1) * (i - 1))
        # xdata = bvals[i_dir : i_dir + n_bval]
        xdata = np.append(bvals[:n_basal], bvals[i_dir : i_dir + n_bval])
        for j in range(n_slices):
            for x in range(img.shape[0]):
                for y in range(img.shape[1]):
                    # ydata = img[x, y, j, i_dir : i_dir + n_bval] / s0[x, y, j]
                    if all(img[x, y, j, :n_basal]):
                        ydata = np.append(
                            img[x, y, j, :n_basal], img[x, y, j, i_dir : i_dir + n_bval]
                        )

                        adcm, s0 = fit_voxel(xdata, ydata)
                        adcm_map[x, y, j, i] = adcm
                        s0_map[x, y, j, i] = s0
                    else:
                        adcm_map[x, y, j, i] = np.nan

                    # if not all(ydata):
                    #     print(ydata)
                    #     adcm_map[x, y, j, i] = np.nan
                    # else:
                    #     # adcm = fit_voxel(xdata, ydata)
                    #     adcm, s0 = fit_voxel(xdata, ydata)
                    #     adcm_map[x, y, j, i] = adcm
    return adcm_map, s0_map


# class ShowFitADC:
#     def __init__(self, adc_map, data, bval):
#         self.adc_map = adc_map
#         self.data = data
#         self.bval = bval


# def show_fitting(self):
def show_fitting(adc_map, s0_map, data, bval):
    img = adc_map[:, :, 0, 0]
    s0 = s0_map[:, :, 0, 0]
    original_data = data
    bvalues = bval
    # s0 = np.mean(original_data[:, :, :, :3], axis=3)

    fig, ax = plt.subplots(1, 2, figsize=(15, 6))

    ax[0].imshow(np.fliplr(rotate(img, 270)), extent=(0, 128, 128, 0))
    ax[1].text(
        0.5,
        0.5,
        "Click on a pixel to show the curve fit.",
        size=15,
        ha="center",
    )

    # Define a function to be called when a pixel is clicked
    def onclick(event):
        # Get the pixel coordinates
        x, y = int(event.xdata), int(event.ydata)

        try:
            # Get the pixel value
            adc_value = img[x, y]

            s0_value = s0[x, y]
            y_data = np.append(original_data[x, y, 0, :3], original_data[x, y, 0, 3:5])
            # y_data = original_data[x, y, 0, 2:4] / s0[x, y, 0]

            # y_data = original_data[x, y, 0, 2:4] / s0[x, y, 0]

            # y_data = [i / j for i, j in zip(original_data[x, y, 0, 2:4], s0[x, y, 2:4])]

            x_data = np.append(bvalues[:3], bvalues[3:5])

            # x_data = bvalues[2:4]
            # y_fitted = [adcm_model(adc_value, b) * s0[x, y, 0] for b in x_data]
            # y_fitted = [adcm_model(adc_value, b) for b in x_data]
            y_fitted = [
                adcm_model(adc_value, s0_value, b)
                for b in range(int(x_data[0]), int(x_data[-1]))
            ]
            x_fitted = list(range(int(x_data[0]), int(x_data[-1])))

            # Generate some sample data for the plot
            # data = np.random.normal(loc=pixel_value, scale=0.1, size=100)
            # data = [1, 2, 3, 4, 5, 6, 7, 7, 8]

            # Create a new figure and plot the data
            # fig2, ax2 = plt.subplots()
            ax[1].clear()
            ax[1].scatter(x_data, y_data, label="Raw data")
            # ax2.plot(x_data, y_fitted, "k", label="Fitted curve")
            ax[1].plot(x_fitted, y_fitted, "k", label="Fitted curve")
            ax[1].set_ylabel("S")
            ax[1].set_xlabel("b value")
            ax[1].legend()

            # ax2.hist(data, bins=20)
            ax[1].set_title(f"ADC value: {adc_value:.6f}. Pixel: {x},{y}.")

            plt.show()

        except IndexError:
            pass

    # Connect the onclick function to the figure
    cid = fig.canvas.mpl_connect("button_press_event", onclick)

    # Show the plot
    plt.show()

    # ax2.scatter(x, y, label="Raw data")
    # ax.plot(x_fitted, y_fitted, "k", label="Fitted curve")
    # ax.set_title("Using polyfit() to fit an exponential function")
    # ax.set_ylabel("y-Values")
    # ax.set_ylim(0, 500)
    # ax.set_xlabel("x-Values")
    # ax.legend()

    # normalize our original image dividing by s0
    # norm_data = np.zeros(data.shape)
    # for i in range(data.shape[2]):
    #     for j in range(data.shape[3]):
    #         norm_data[:, :, i, j] += data[:, :, i, j] / s0[:, :, i]

    # # get residuals: difference between real data and predicted data
    # residuals = norm_data - predicted_signal


# Models.append(
#     Model(
#         "Mono",
#         "ADC monoexponential",
#         lambda p, x: adcm(x, *p),
#         [Parameter("ADCm", (0.0001, 0.003, 0.00001), (0, 1)), ParamC],
#     )
# )

# 1. Mono-exponential model:
#    ADCm from 0.1 um2/ms to 3.0 um2/ms with step size of 0.01 um2/ms.

# ADCm    0.0001 mm2/ms to 0.003 mm2/ms with step size of 0.00001 mm2/ms.


# from leastsqbound import leastsqbound


# def fit_curves_mi(f, xdata, ydatas, guesses, bounds, out_pmap):
#     """Fit curves to data with multiple initializations.

#     Parameters
#     ----------
#     f : callable
#         Cost function used for fitting in form of f(parameters, x).
#     xdata : ndarray, shape = [n_bvalues]
#         X data points, i.e. b-values
#     ydatas : ndarray, shape = [n_curves, n_bvalues]
#         Y data points, i.e. signal intensity curves
#     guesses : callable
#         A callable that returns an iterable of all combinations of parameter
#         initializations, i.e. starting guesses, as tuples
#     bounds : sequence of tuples
#         Constraints for parameters, i.e. minimum and maximum values
#     out_pmap : ndarray, shape = [n_curves, n_parameters+1]
#         Output array

#     For each signal intensity curve, the resulting parameters with best fit
#     will be placed in the output array, along with an RMSE value (root mean
#     square error). In case of error, curve parameters will be set to NaN and
#     RMSE to infinite.

#     See files fit.py and models.py for more information on usage.
#     """
#     for i, ydata in enumerate(ydatas):
#         params, err = fit_curve_mi(f, xdata, ydata, guesses(ydata[0]), bounds)
#         out_pmap[i, -1] = err
#         if np.isfinite(err):
#             out_pmap[i, :-1] = params
#         else:
#             out_pmap[i, :-1].fill(np.nan)


# def fit_curve_mi(f, xdata, ydata, guesses, bounds):
#     """Fit a curve to data with multiple initializations.

#     Try all given combinations of parameter initializations, and return the
#     parameters and RMSE of best fit.
#     """
#     if np.any(np.isnan(ydata)):
#         return None, np.nan
#     best_params = []
#     best_err = np.inf
#     for guess in guesses:
#         params, err = fit_curve(f, xdata, ydata, guess, bounds)
#         if err < best_err:
#             best_params = params
#             best_err = err
#     return best_params, best_err


# def fit_curve(f, xdata, ydata, guess, bounds):
#     """Fit a curve to data."""

#     def residual(p, x, y):
#         return f(p, x) - y

#     params, ier = leastsqbound(residual, guess, args=(xdata, ydata), bounds=bounds)
#     if 0 < ier < 5:
#         err = rmse(f, params, xdata, ydata)
#     else:
#         err = np.inf
#     return params, err


# def rmse(f, p, xdata, ydata):
#     """Root-mean-square error."""
#     sqerr = (f(p, xdata) - ydata) ** 2
#     return np.sqrt(sqerr.mean())


# class Parameter(object):
#     """Parameter used in model definitions."""

#     def __init__(self, name, steps, bounds, use_stepsize=True, relative=False):
#         """Create a new model parameter.

#         Parameters
#         ----------
#         name : string
#             Parameter name.
#         steps : tuple
#             Steps as (start, stop, size/number).
#         bounds : tuple
#             Constraints as (start, end).
#         use_stepsize : bool, optional, default True
#             Use step size instead of number.
#         relative : bool, optional, default False
#             Values are relative to a constant given upon request.
#         """
#         self.name = name
#         self.steps = steps
#         self.bounds = bounds
#         self.use_stepsize = use_stepsize
#         self.relative = relative

#     def __repr__(self):
#         return "%s=%s" % (self.name, self.steps)

#     def __str__(self):
#         return self.name

#     def guesses(self, c):
#         """Return initial guesses."""
#         if self.use_stepsize:
#             g = np.arange(*self.steps)
#         else:
#             g = np.linspace(*self.steps)
#         if self.relative:
#             g *= c
#         return g


# # fit_curves_mi = dwi.fit_one_by_one.fit_curves_mi


# class Model(object):
#     def __init__(self, name, desc, func, params, preproc=None, postproc=None):
#         """Create a new model definition.

#         Parameters
#         ----------
#         name : string
#             Model name.
#         desc : string
#             Model description.
#         func : callable
#             Fitted function.
#         params : Parameter
#             Parameter definitions.
#         preproc : callable, optional
#             Preprocessing function for data.
#         postproc : callable, optional
#             Postprocessing function for fitted parameters.
#         """
#         self.name = name
#         self.desc = desc
#         self.func = func
#         self.params = params
#         self.preproc = preproc
#         self.postproc = postproc

#     def __repr__(self):
#         return "%s %s" % (self.name, " ".join(repr(x) for x in self.params))

#     def __str__(self):
#         return self.name

#     def bounds(self):
#         """Return bounds of all parameters."""
#         return [x.bounds for x in self.params]

#     # def guesses(self, c):
#     #     """Return all combinations of initial guesses."""
#     #     return product(*[x.guesses(c) for x in self.params])

#     def fit(self, xdata, ydatas):
#         """Fit model to multiple voxels."""
#         xdata = np.asanyarray(xdata)
#         ydatas = np.asanyarray(ydatas)
#         ydatas = prepare_for_fitting(ydatas)
#         if self.preproc:
#             for ydata in ydatas:
#                 self.preproc(ydata)
#         shape = (len(ydatas), len(self.params) + 1)
#         pmap = np.zeros(shape)
#         if self.func:
#             fit_curves_mi(self.func, xdata, ydatas, self.guesses, self.bounds(), pmap)
#         else:
#             pmap[:, :-1] = ydatas  # Fill with original data.
#         if self.postproc:
#             for params in pmap:
#                 self.postproc(params[:-1])
#         return pmap


# def prepare_for_fitting(voxels):
#     """Return a copy of voxels, prepared for fitting."""
#     voxels = voxels.copy()
#     for v in voxels:
#         if v[0] == 0:
#             # S(0) is not expected to be 0, set whole curve to 1 (ADC 0).
#             v[:] = 1
#     return voxels
