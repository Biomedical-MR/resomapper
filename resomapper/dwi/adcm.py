import numpy as np

from scipy.optimize import curve_fit


class ADCmProcessor:
    """Mono exponential ADC fitting."""

    def __init__(self, root_path: str, study_path: str) -> None:
        self.root_path = root_path
        self.study_path = study_path

    def adcm(self, b, ADCm, C=1):
        """ADC mono: single exponential decay.

        C * exp(-b * ADCm)
        """
        return C * np.exp(-b * ADCm)

    def fit_voxel(self, x, y):
        popt, pcov = curve_fit(lambda b, ADCm: np.exp(-b * ADCm), x, y)


Models.append(
    Model(
        "Mono",
        "ADC monoexponential",
        lambda p, x: adcm(x, *p),
        [Parameter("ADCm", (0.0001, 0.003, 0.00001), (0, 1)), ParamC],
    )
)

# 1. Mono-exponential model:
#    ADCm from 0.1 um2/ms to 3.0 um2/ms with step size of 0.01 um2/ms.

# ADCm    0.0001 mm2/ms to 0.003 mm2/ms with step size of 0.00001 mm2/ms.
from leastsqbound import leastsqbound


def fit_curves_mi(f, xdata, ydatas, guesses, bounds, out_pmap):
    """Fit curves to data with multiple initializations.

    Parameters
    ----------
    f : callable
        Cost function used for fitting in form of f(parameters, x).
    xdata : ndarray, shape = [n_bvalues]
        X data points, i.e. b-values
    ydatas : ndarray, shape = [n_curves, n_bvalues]
        Y data points, i.e. signal intensity curves
    guesses : callable
        A callable that returns an iterable of all combinations of parameter
        initializations, i.e. starting guesses, as tuples
    bounds : sequence of tuples
        Constraints for parameters, i.e. minimum and maximum values
    out_pmap : ndarray, shape = [n_curves, n_parameters+1]
        Output array

    For each signal intensity curve, the resulting parameters with best fit
    will be placed in the output array, along with an RMSE value (root mean
    square error). In case of error, curve parameters will be set to NaN and
    RMSE to infinite.

    See files fit.py and models.py for more information on usage.
    """
    for i, ydata in enumerate(ydatas):
        params, err = fit_curve_mi(f, xdata, ydata, guesses(ydata[0]), bounds)
        out_pmap[i, -1] = err
        if np.isfinite(err):
            out_pmap[i, :-1] = params
        else:
            out_pmap[i, :-1].fill(np.nan)


def fit_curve_mi(f, xdata, ydata, guesses, bounds):
    """Fit a curve to data with multiple initializations.

    Try all given combinations of parameter initializations, and return the
    parameters and RMSE of best fit.
    """
    if np.any(np.isnan(ydata)):
        return None, np.nan
    best_params = []
    best_err = np.inf
    for guess in guesses:
        params, err = fit_curve(f, xdata, ydata, guess, bounds)
        if err < best_err:
            best_params = params
            best_err = err
    return best_params, best_err


def fit_curve(f, xdata, ydata, guess, bounds):
    """Fit a curve to data."""

    def residual(p, x, y):
        return f(p, x) - y

    params, ier = leastsqbound(residual, guess, args=(xdata, ydata), bounds=bounds)
    if 0 < ier < 5:
        err = rmse(f, params, xdata, ydata)
    else:
        err = np.inf
    return params, err


def rmse(f, p, xdata, ydata):
    """Root-mean-square error."""
    sqerr = (f(p, xdata) - ydata) ** 2
    return np.sqrt(sqerr.mean())


class Parameter(object):
    """Parameter used in model definitions."""

    def __init__(self, name, steps, bounds, use_stepsize=True, relative=False):
        """Create a new model parameter.

        Parameters
        ----------
        name : string
            Parameter name.
        steps : tuple
            Steps as (start, stop, size/number).
        bounds : tuple
            Constraints as (start, end).
        use_stepsize : bool, optional, default True
            Use step size instead of number.
        relative : bool, optional, default False
            Values are relative to a constant given upon request.
        """
        self.name = name
        self.steps = steps
        self.bounds = bounds
        self.use_stepsize = use_stepsize
        self.relative = relative

    def __repr__(self):
        return "%s=%s" % (self.name, self.steps)

    def __str__(self):
        return self.name

    def guesses(self, c):
        """Return initial guesses."""
        if self.use_stepsize:
            g = np.arange(*self.steps)
        else:
            g = np.linspace(*self.steps)
        if self.relative:
            g *= c
        return g


fit_curves_mi = dwi.fit_one_by_one.fit_curves_mi


class Model(object):
    def __init__(self, name, desc, func, params, preproc=None, postproc=None):
        """Create a new model definition.

        Parameters
        ----------
        name : string
            Model name.
        desc : string
            Model description.
        func : callable
            Fitted function.
        params : Parameter
            Parameter definitions.
        preproc : callable, optional
            Preprocessing function for data.
        postproc : callable, optional
            Postprocessing function for fitted parameters.
        """
        self.name = name
        self.desc = desc
        self.func = func
        self.params = params
        self.preproc = preproc
        self.postproc = postproc

    def __repr__(self):
        return "%s %s" % (self.name, " ".join(repr(x) for x in self.params))

    def __str__(self):
        return self.name

    def bounds(self):
        """Return bounds of all parameters."""
        return [x.bounds for x in self.params]

    def guesses(self, c):
        """Return all combinations of initial guesses."""
        return product(*[x.guesses(c) for x in self.params])

    def fit(self, xdata, ydatas):
        """Fit model to multiple voxels."""
        xdata = np.asanyarray(xdata)
        ydatas = np.asanyarray(ydatas)
        ydatas = prepare_for_fitting(ydatas)
        if self.preproc:
            for ydata in ydatas:
                self.preproc(ydata)
        shape = (len(ydatas), len(self.params) + 1)
        pmap = np.zeros(shape)
        if self.func:
            fit_curves_mi(self.func, xdata, ydatas, self.guesses, self.bounds(), pmap)
        else:
            pmap[:, :-1] = ydatas  # Fill with original data.
        if self.postproc:
            for params in pmap:
                self.postproc(params[:-1])
        return pmap


def prepare_for_fitting(voxels):
    """Return a copy of voxels, prepared for fitting."""
    voxels = voxels.copy()
    for v in voxels:
        if v[0] == 0:
            # S(0) is not expected to be 0, set whole curve to 1 (ADC 0).
            v[:] = 1
    return voxels
