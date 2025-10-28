# CODE ADAPTED BY BIOMEDICAL-MR LAB 2024 FROM:
#
# Author: Francesco Grussu, University College London
# 		    CDSQuaMRI Project
# 		   <f.grussu@ucl.ac.uk> <francegrussu@gmail.com>
#
# Code released under BSD Two-Clause license
#
# Copyright (c) 2019 University College London.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# The views and conclusions contained in the software and documentation are those
# of the authors and should not be interpreted as representing official policies,
# either expressed or implied, of the FreeBSD Project.

### Load useful modules
import multiprocessing
import numpy as np
from scipy.optimize import minimize
import nibabel as nib
from resomapper.core.misc import auto_innited_logger as lggr


def signal_equation_T1(mri_tr, tissue_par):
    """Generate the signal for a spin echo experiment at variable TR

    PARAMETERS
    - mri_tr: list/array indicating the TRs (repetition times, in ms) used for the experiment (one measurement per TR)
    - tissue_par: list/array of tissue parameters, in the following order:
                  tissue_par[0] = S0 (T1-weighted proton density)
                  tissue_par[1] = T1 (longitudinal relaxation time, in ms)

    RETURNS
    - signal: a numpy array of measurements generated according to a multi-repetition time acquistion,

                signal  =  S0 * 1 - (exp(-TR/T1))

                where TR is the repetition time and where S0 and T1 are the tissue parameters (S0 is the T1-weighted proton
                density, and T1 is the longitudinal relaxation time, i.e. T1).

    References: "Quantitative MRI of the brain", 2nd edition, Tofts, Cercignani and Dowell editors, Taylor and Francis Group

    Author: Francesco Grussu, University College London
            CDSQuaMRI Project
           <f.grussu@ucl.ac.uk> <francegrussu@gmail.com>"""

    ### Handle inputs
    # Make sure TR values are stored as a numpy array
    tr_values = np.array(mri_tr, "float64")  # TR values
    s0_value = tissue_par[0]  # S0
    t1_value = tissue_par[1]  # T1

    ### Calculate signal
    with np.errstate(divide="raise", invalid="raise"):
        try:
            signal = s0_value * (1 - np.exp((-1.0) * tr_values / t1_value))
        except FloatingPointError:
            signal = 0.0 * tr_values  # Just output zeros when t1_value is 0.0

    ### Output signal
    return signal


def signal_equation_T2T2star(mri_te, tissue_par):
    """Generate the signal for a multi-echo experiment at fixed TR

    PARAMETERS
    - mri_te: list/array indicating the TEs (echo times, in ms) used for the experiment (one measurement per TR)
    - tissue_par: list/array of tissue parameters, in the following order:
                  tissue_par[0] = S0 (T1-weighted proton density)
                  tissue_par[1] = T2 or T2star (transvere relaxation time), in ms

    RETURNS
    - signal: a numpy array of measurements generated according to a multi-echo signal model,

                signal  =  S0 * exp(-TE/T2)

                where TE is the echo time and where S0 and T2 are the tissue parameters (S0 is the T1-weighted proton
                density, and T2 is the transverse relaxation time, i.e. T2 or T2*).


    Dependencies (Python packages): numpy

    References: "Quantitative MRI of the brain", 2nd edition, Tofts, Cercignani and Dowell editors, Taylor and Francis Group

    Author: Francesco Grussu, University College London
            CDSQuaMRI Project
           <f.grussu@ucl.ac.uk> <francegrussu@gmail.com>"""

    ### Handle inputs
    # Make sure TR values are stored as a numpy array
    te_values = np.array(mri_te, "float64")  # TR values
    s0_value = tissue_par[0]  # S0
    t2_value = tissue_par[1]  # T1

    ### Calculate signal
    with np.errstate(divide="raise", invalid="raise"):
        try:
            signal = s0_value * np.exp((-1.0) * te_values / t2_value)
        except FloatingPointError:
            signal = 0.0 * te_values  # Just output zeros when t2_value is 0.0

    ### Output signal
    return signal


def Fobj_SSE_Tmaps(tissue_par, mri_times, meas, signal_equation):
    """Fitting objective function for exponential decay signal model

    PARAMETERS
    - tissue_par: list/array of tissue parameters, in the following order:
                  tissue_par[0] = S0 (T1-weighted proton density)
                  tissue_par[1] = either T1 (longitudinal relaxation time), T2 or T2star (transverse relaxation time), in ms
    - mri_times: list/array indicating the TRs (repetition times) or TEs (echo times), in ms used for the experiment (one measurement per TE)
    - meas: list/array of measurements

    RETURNS
    - fobj: objective function measured as sum of squared errors (SSE) between measurements and predictions, i.e.

                         fobj = SUM_OVER_n( (prediction - measurement)^2 )

             Above, the prediction are obtained using the multi-echo signal model implemented by function signal_equation_multiTE().

    References: "Quantitative MRI of the brain", 2nd edition, Tofts, Cercignani and Dowell editors, Taylor and Francis Group

    Author: Francesco Grussu, University College London
            CDSQuaMRI Project
           <f.grussu@ucl.ac.uk> <francegrussu@gmail.com>"""

    ### Predict signals given tissue and sequence parameters
    pred = signal_equation(mri_times, tissue_par)

    ### Calculate objective function and return
    fobj = np.sum((np.array(pred) - np.array(meas)) ** 2)
    return fobj


def Tmapfit_voxel_GridSearch(mri_times, meas, T_type):
    """Grid search for non-linear fitting of exponential decay signal models

    PARAMETERS
    - mri_times: list/array indicating the TEs (echo times, in ms) used for the experiment (one measurement per TE)
    - meas: list/array of measurements

    RETURNS
    - tissue_estimate: estimate of tissue parameters that explain the measurements reasonably well. The parameters are
                       estimated sampling the fitting objective function Fobj_T2fitting_multiTE() over a grid; the output is
                       tissue_estimate[0] = S0 (T1-weighted proton density)
                       tissue_estimate[1] = T2 or T2star (transverse relaxation time, in ms)
    - fobj_grid:       value of the objective function when the tissue parameters equal tissue_estimate

    References: "Quantitative MRI of the brain", 2nd edition, Tofts, Cercignani and Dowell editors, Taylor and Francis Group

    Author: Francesco Grussu, University College London
            CDSQuaMRI Project
           <f.grussu@ucl.ac.uk> <francegrussu@gmail.com>"""

    ### Prepare grid for grid search
    if T_type == "T1":
        signal_equation = signal_equation_T1
        # Grid of T1
        txy_grid = np.array([1000.0, 1600.0, 2200.0, 2800.0, 3400.0, 4000.0])  
        # Grid of S0 values: from 0 up to 10 times the maximum signal taken as input
        s0_grid = np.linspace(0.0,np.max(meas),num=2)

        # txy_grid = np.linspace(100.0,4500.0,num=12)
        # s0_grid = np.linspace(0.0, 10 * np.max(meas), num=12)
    elif T_type in ["T2", "T2star"]:
        signal_equation = signal_equation_T2T2star
        # Grid of T2 or T2star values
        txy_grid = np.array(
            [
                10.0,
                15.0,
                20.0,
                25.0,
                30.0,
                35.0,
                40.0,
                45.0,
                50.0,
                55.0,
                60.0,
                65.0,
                70.0,
                75.0,
                80.0,
                85.0,
                90.0,
                150.0,
                200.0,
                300.0,
                400.0,
                600.0,
                800.0,
                1000.0,
            ]
        )
        # Grid of S0 values: from 0 up to 10 times the maximum signal taken as input
        s0_grid = np.linspace(0.0, 10 * np.max(meas), num=24)

    ### Initialise objective function to infinity and parameters for grid search
    fobj_best = float("inf")
    s0_best = 0.0
    txy_best = 0.0

    ### Run grid search
    for ii in range(0, len(txy_grid)):

        txy_ii = txy_grid[ii]
        for jj in range(0, len(s0_grid)):

            s0_jj = s0_grid[jj]
            params = np.array([s0_jj, txy_ii])

            # Objective function
            fval = Fobj_SSE_Tmaps(params, mri_times, meas, signal_equation)

            # Check if objective function is smaller than previous value
            if fval < fobj_best:
                fobj_best = fval
                s0_best = s0_jj
                txy_best = txy_ii

    ### Return output
    paramsgrid = np.array([s0_best, txy_best])
    fobjgrid = fobj_best
    return paramsgrid, fobjgrid


def Tmapfit_voxel_2timesanalitical(sig_voxel, time_values, T_type):
    sig1 = sig_voxel[0]  # Signal for first TE
    sig2 = sig_voxel[1]  # Signal for second TE
    time1 = time_values[0]  # First TE
    time2 = time_values[1]  # Second TE

    if T_type == "T1":
        txy_max_val = 5000.0  # We fix the maximum possible T1 to 5000
    elif T_type == "T2" or T_type == "T2star":
        txy_max_val = 1200.0  # We fix the maximum possible T2 or T2star to 1200

    # Calculate maps analytically, handling warnings
    with np.errstate(divide="raise", invalid="raise"):
        try:
            txy_voxel = (time2 - time1) / np.log(sig1 / sig2)
            s0_voxel = sig1 / np.exp((-1.0) * time1 / txy_voxel)
            exit_voxel = 1

            # Check whether the solution is plausible
            if txy_voxel < 0:
                s0_voxel = np.mean(sig_voxel)
                txy_voxel = txy_max_val
                exit_voxel = -1
            if s0_voxel < 0:
                s0_voxel = 0.0
                exit_voxel = -1

            sse_voxel = Fobj_SSE_Tmaps([s0_voxel, txy_voxel], time_values, sig_voxel)
            # Error (0 when fitting provides txy > 0 ad s0 > 0 at the first attempt)

        except FloatingPointError:
            s0_voxel = 0.0
            txy_voxel = 0.0
            exit_voxel = -1
            sse_voxel = 0.0

        return s0_voxel, txy_voxel, exit_voxel, sse_voxel


def Tmapfit_voxel_linear(sig_voxel, time_values, T_type):
    if T_type == "T1":
        signal_equation = signal_equation_T1
        txy_max_val = 5000.0  # We fix the maximum possible T1 to 5000
    elif T_type == "T2" or T_type == "T2star":
        signal_equation = signal_equation_T2T2star
        txy_max_val = 1200.0  # We fix the maximum possible T2 or T2star to 1200

    Nmeas = len(time_values)
    times_column = np.reshape(
        time_values, (Nmeas, 1)
    )  # Store TE values as a column array
    # TODO check if this is neccesary???
    # Reshape measurements as column array
    # sig_voxel_column = np.reshape(sig_voxel, (Nmeas, 1))

    # Calculate linear regression coefficients as ( W * Q )^-1 * (W * m), while handling warnings
    with np.errstate(divide="raise", invalid="raise"):
        try:
            # Create matrices and arrays to be combinted via matrix multiplication
            Yvals = np.log(sig_voxel)  # Independent variable of linearised model
            Xvals = (-1.0) * times_column  # Dependent variable of linearised model
            allones = np.ones([Nmeas, 1])  # Column of ones
            Qmat = np.concatenate((allones, Xvals), axis=1)  # Design matrix Q
            Wmat = np.diag(sig_voxel)  # Matrix of weights W

            # Calculate coefficients via matrix multiplication
            coeffs = np.matmul(
                np.linalg.pinv(np.matmul(Wmat, Qmat)),
                np.matmul(Wmat, Yvals),
            )

            # Retrieve signal model parameters from linear regression coefficients
            s0_voxel = np.exp(coeffs[0])
            txy_voxel = 1.0 / coeffs[1]
            exit_voxel = 1

            # Check whether the solution is plausible: if not, declare fitting failed
            if txy_voxel < 0:
                s0_voxel = np.mean(sig_voxel)
                txy_voxel = txy_max_val
                exit_voxel = -1
            if s0_voxel < 0:
                s0_voxel = 0.0
                exit_voxel = -1

            sse_voxel = Fobj_SSE_Tmaps(
                [s0_voxel, txy_voxel], time_values, sig_voxel, signal_equation
            )  # Measure of quality of fit

        except FloatingPointError:
            s0_voxel = 0.0
            txy_voxel = 0.0
            exit_voxel = -1
            sse_voxel = 0.0

        return s0_voxel, txy_voxel, exit_voxel, sse_voxel


def Tmapfit_voxel_nonlinear(sig_voxel, time_values, param_init, fobj_init, T_type):

    # s0_voxel == param_init[0]
    if T_type == "T1":
        signal_equation = signal_equation_T1
        # Range for S0 and T1 limited to be < 5000)
        param_bound = ((0,5*param_init[0]),(0,5000),)  
    elif T_type == "T2" or T_type == "T2star":
        signal_equation = signal_equation_T2T2star
        # Range for S0 and T2 or T2star (T2/T2star limited to be < 1800)	
        param_bound = ((0,2*param_init[0]),(0,1200),) 

    # Minimise the objective function numerically
    
    
    modelfit = minimize(
        Fobj_SSE_Tmaps,
        param_init,
        method="L-BFGS-B",
        args=tuple([time_values, sig_voxel, signal_equation]),
        bounds=param_bound,
    )
    fit_exit_success = modelfit.success
    fobj_fit = modelfit.fun

    # Get fitting output if non-linear optimisation was successful and if succeeded in providing a smaller value of the objective function as compared to the grid search
    if fit_exit_success is True and fobj_fit < fobj_init:
        param_fit = modelfit.x
        s0_voxel = param_fit[0]
        txy_voxel = param_fit[1]
        exit_voxel = 1
        sse_voxel = fobj_fit

    # Otherwise, output the best we could find with linear fitting or, when linear fitting fails, with grid search (note that grid search cannot fail by implementation)
    else:
        s0_voxel = param_init[0]
        txy_voxel = param_init[1]
        exit_voxel = -1
        sse_voxel = fobj_init

    return s0_voxel, txy_voxel, exit_voxel, sse_voxel


# def Tmapfit_slice(
#     signal_slice, time_values, mask_slice, idx_slice, T_type, non_linear_fitting=True
# ):
def Tmapfit_slice(data):
    """Fit T1 for a multi-echo experiment on one MRI slice stored as a 2D numpy array


    INTERFACE
    data_out = Tmapfit_slice(data)

    PARAMETERS
    - data: a list of 7 elements, such that
        signal_slice is a 3D numpy array contaning the data to fit. The first and second dimensions of data[0]
                are the slice first and second dimensions, whereas the third dimension of data[0] stores
                measurements obtained with different flip angles
        time_values is a numpy monodimensional array storing the TR values (ms)
        non_linear_fitting is a boolean describing the fitting algorithm (False if only "linear" or True if "nonlinear")
        mask_slice is a 2D numpy array contaning the fitting mask within the MRI slice (see Tmapfit_image())
        idx_slice is a scalar containing the index of the MRI slice in the 3D volume

    RETURNS
    - data_out: a list of 4 elements, such that
            data_out[0] is the parameter S0 (see Tmapfit_image()) within the MRI slice
            data_out[1] is the parameter T1 (see Tmapfit_image()) within the MRI slice
            data_out[2] is the exit code of the fitting (see Tmapfit_image()) within the MRI slice
            data_out[3] is the fitting sum of squared errors withint the MRI slice
            data_out[4] equals data[4]

            Fitted parameters in data_out will be stored as double-precision floating point (FLOAT64)

    References: "Quantitative MRI of the brain", 2nd edition, Tofts, Cercignani and Dowell editors, Taylor and Francis Group

    Author: Francesco Grussu, University College London
            CDSQuaMRI Project
           <f.grussu@ucl.ac.uk> <francegrussu@gmail.com>"""
    
    signal_slice = data[0]
    time_values = data[1]
    mask_slice = data[2]
    idx_slice = data[3]
    T_type = data[4]
    non_linear_fitting = data[5]

    slicesize = signal_slice.shape  # Get number of voxels of slice along each dimension
    time_values = np.array(time_values)  # Make sure the TR is an array

    ### Allocate output variables
    s0_slice = np.zeros(slicesize[:2], "float64")
    txy_slice = np.zeros(slicesize[:2], "float64")
    exit_slice = np.zeros(slicesize[:2], "float64")
    sse_slice = np.zeros(slicesize[:2], "float64")
    Nmeas = slicesize[2]  # Number of measurements

    ### Fit monoexponential decay model in the voxels within the current slice
    for xx in range(0, slicesize[0]):
        for yy in range(0, slicesize[1]):

            # Get mask for current voxel
            mask_voxel = mask_slice[xx, yy]  # Fitting mask for current voxel

            # The voxel is not background: fit the signal model
            if mask_voxel == 1:

                # Get signal and fitting mask
                sig_voxel = signal_slice[xx, yy, :]  # Extract signals for current voxel
                sig_voxel = np.array(sig_voxel)  # Convert to array

                ## Simplest case: there are only two echo times --> get the solution analytically
                if "T2" in T_type and Nmeas == 2:
                    s0_voxel, txy_voxel, exit_voxel, sse_voxel = (
                        Tmapfit_voxel_2timesanalitical(sig_voxel, time_values, T_type)
                    )

                ## General case: there are more than two echo times --> get the solution minimising an objective function
                else:

                    exit_voxel = 0
                    if "T2" in T_type:
                        # Perform linear fitting as first thing - if non-linear fitting is required, the linear fitting will be used to initialise the non-linear optimisation afterwards
                        s0_voxel, txy_voxel, exit_voxel, sse_voxel = Tmapfit_voxel_linear(
                            sig_voxel, time_values, T_type
                        )
                        param_init = [
                                s0_voxel,
                                txy_voxel,
                            ]  # If linear fitting did not fail: use linear fitting output to initialise non-linear optimisation
                        fobj_init = sse_voxel
                    if "T1" in T_type or exit_voxel == -1:
                        param_init, fobj_init = Tmapfit_voxel_GridSearch(
                                time_values, sig_voxel, T_type
                            )  # Case of T1 map or T2 inear fitting has failed: run a grid search

                    # Refine the results from linear with non-linear optimisation if the selected algorithm is "nonlinear"
                    if "T1" in T_type or non_linear_fitting:
                        s0_voxel, txy_voxel, exit_voxel, sse_voxel = (
                            Tmapfit_voxel_nonlinear(
                                sig_voxel, time_values, param_init, fobj_init, T_type
                            )
                        )

            # The voxel is background
            else:
                s0_voxel = np.nan
                txy_voxel = np.nan
                exit_voxel = np.nan
                sse_voxel = np.nan

            # Store fitting results for current voxel
            s0_slice[xx, yy] = s0_voxel
            txy_slice[xx, yy] = txy_voxel
            exit_slice[xx, yy] = exit_voxel
            sse_slice[xx, yy] = sse_voxel

    ### Create output list storing the fitted parameters and then return
    data_out = [s0_slice, txy_slice, exit_slice, sse_slice, idx_slice]
    return data_out


def Tmapfit_image(
    sig_nifti,
    times_file,
    output_rootname,
    T_type,
    non_linear_fitting=True,
    ncpu=None,
    mask_nifti=None,
):
    """Fit T1 for multi-echo experiment

    PARAMETERS
    - me_nifti: path of a Nifti file storing the multi-echo data as 4D data.
    - te_text: path of a text file storing the echo times (ms) used to acquire the data.
    - output_basename: base name of output files. Output files will end in
                    "_S0ME.nii"   --> T1-weighted proton density, with receiver coil field bias
                    "_T1ME.nii"  --> T1 (ms)
                    "_ExitME.nii" --> exit code (1: successful fitting; 0 background; -1: unsuccessful fitting)
                    "_SSEME.nii"  --> fitting sum of squared errors

                    Note that in the background and where fitting fails, S0, T1 and MSE are set to 0.0
                    Output files will be stored as double-precision floating point (FLOAT64)

    - non_linear_fitting: fitting algorithm ("linear" or "nonlinear")
    - ncpu: number of processors to be used for computation
    - mask_nifti: path of a Nifti file storing a binary mask, where 1 flgas voxels where the
                  signal model needs to be fitted, and 0 otherwise

    References: "Quantitative MRI of the brain", 2nd edition, Tofts, Cercignani and Dowell editors, Taylor and Francis Group

    Dependencies: numpy, nibabel, scipy (other than standard library)

    Author: Francesco Grussu, University College London
            CDSQuaMRI Project
           <f.grussu@ucl.ac.uk> <francegrussu@gmail.com>"""

    ### Get input parametrs
    ncpu_physical = multiprocessing.cpu_count()
    if ncpu is None:
        ncpu = ncpu_physical
    elif ncpu > ncpu_physical:
        print(
            f"\nWARNING: {ncpu} CPUs were requested. Using {ncpu_physical} instead (all available CPUs)...\n"
        )
        # Do not open more workers than the physical number of CPUs
        ncpu = ncpu_physical

    ### Load MRI data
    print("\n    ... loading input data")
    sig_obj = nib.load(sig_nifti)

    # Get image dimensions and convert to float64
    sig_data = sig_obj.get_fdata()
    imgsize = sig_data.shape
    sig_data = np.array(sig_data, "float64")
    imgsize = np.array(imgsize)

    # Make sure that the text file with sequence parameters exists and makes sense
    # Can be a text file or a np.array
    try:
        seqarray = np.loadtxt(times_file)
        seqarray = np.array(seqarray, "float64")
    except Exception:
        seqarray = np.array(times_file, "float64")
    seqarray_size = seqarray.size

    # TODO: CHECK NUMBER OF TRS AND IMAGE

    # Check consistency of sequence parameter file and number of measurements
    if imgsize.size != 4:
        print("")
        print(
            f"\n{lggr.error}The input file {sig_nifti} is not a 4D nifti. Fitting aborted."
        )
        # sys.exit(1)
        return False
    if seqarray_size != imgsize[3]:
        print(
            f"\n{lggr.error}The number of measurements in {sig_nifti} does not match the number of echo times in {times_file}. Fitting aborted."
        )
        # sys.exit(1)
        return False
    seq = seqarray

    ### Deal with optional arguments: mask
    if mask_nifti is not None:
        mask_obj = nib.load(mask_nifti)

        # Make sure that the mask has header information that is consistent with the input data containing the VFA measurements
        sig_header = sig_obj.header
        sig_affine = sig_header.get_best_affine()
        sig_dims = sig_obj.shape
        mask_dims = mask_obj.shape
        mask_header = mask_obj.header
        mask_affine = mask_header.get_best_affine()
        # Make sure the mask is a 3D file
        mask_data = mask_obj.get_fdata()
        masksize = mask_data.shape
        masksize = np.array(masksize)
        if masksize.size != 3:
            print("")
            print(
                "WARNING: the mask file {} is not a 3D Nifti file. Ignoring mask...".format(
                    mask_nifti
                )
            )
            print("")
            mask_data = np.ones(imgsize[0:3], "float64")
        elif (
            (np.sum(sig_affine == mask_affine) != 16)
            or (sig_dims[0] != mask_dims[0])
            or (sig_dims[1] != mask_dims[1])
            or (sig_dims[2] != mask_dims[2])
        ):
            print("")
            print(
                "WARNING: the geometry of the mask file {} does not match that of the input data. Ignoring mask...".format(
                    mask_nifti
                )
            )
            print("")
            mask_data = np.ones(imgsize[0:3], "float64")
        else:
            mask_data = np.array(mask_data, "float64")
            # Make sure mask data is a numpy array
            mask_data[mask_data > 0] = 1
            mask_data[mask_data <= 0] = 0
    else:
        mask_data = np.ones(imgsize[0:3], "float64")

    ### Allocate memory for outputs
    s0_data = np.zeros(
        imgsize[0:3], "float64"
    )  # T1-weighted proton density with receiver field bias (double-precision floating point)
    txy_data = np.zeros(imgsize[0:3], "float64")  # T1 (double-precision floating point)
    exit_data = np.zeros(
        imgsize[0:3], "float64"
    )  # Exit code (double-precision floating point)
    sse_data = np.zeros(
        imgsize[0:3], "float64"
    )  # Fitting sum of squared errors (MSE) (double-precision floating point)

    #### Fitting
    print("    ... longitudinal relaxation time estimation")
    # Create the list of input data
    inputlist = []
    for zz in range(0, imgsize[2]):
        sliceinfo = [
            sig_data[:, :, zz, :],
            seq,
            mask_data[:, :, zz],
            zz,
            T_type,
            non_linear_fitting,
        ]  # List of information relative to the zz-th MRI slice
        inputlist.append(
            sliceinfo
        )  # Append each slice list and create a longer list of MRI slices whose processing will run in parallel

    # Clear some memory
    del sig_data, mask_data

    # Call a pool of workers to run the fitting in parallel if parallel processing is required (and if the the number of slices is > 1)
    if ncpu > 1 and imgsize[2] > 1:

        # Create the parallel pool and give jobs to the workers
        fitpool = multiprocessing.Pool(processes=ncpu)  # Create parallel processes
        fitpool_pids_initial = [
            proc.pid for proc in fitpool._pool
        ]  # Get initial process identifications (PIDs)
        fitresults = fitpool.map_async(
            Tmapfit_slice, inputlist
        )  # Give jobs to the parallel processes

        # Busy-waiting: until work is done, check whether any worker dies (in that case, PIDs would change!)
        while not fitresults.ready():
            fitpool_pids_new = [
                proc.pid for proc in fitpool._pool
            ]  # Get process IDs again
            # Check whether the IDs have changed from the initial values
            if fitpool_pids_new != fitpool_pids_initial:
                # Yes, they changed: at least one worker has died! Exit with error
                print(
                    f"\n{lggr.error}Some processes died during parallel fitting. Fitting aborted."
                )
                # sys.exit(1)
                return False

        # Work done: get results
        fitlist = fitresults.get()

        # Collect fitting output and re-assemble MRI slices
        for kk in range(0, imgsize[2]):
            fitslice = fitlist[
                kk
            ]  # Fitting output relative to kk-th element in the list
            slicepos = fitslice[4]  # Spatial position of kk-th MRI slice
            s0_data[:, :, slicepos] = fitslice[
                0
            ]  # Parameter S0 of mono-exponential decay model
            txy_data[:, :, slicepos] = fitslice[
                1
            ]  # Parameter T1 of mono-exponential decay model
            exit_data[:, :, slicepos] = fitslice[2]  # Exit code
            sse_data[:, :, slicepos] = fitslice[3]  # Sum of Squared Errors

    # Run serial fitting as no parallel processing is required (it can take up to 1 hour per brain)
    else:
        for kk in range(0, imgsize[2]):
            fitslice = Tmapfit_slice(
                inputlist[kk]
            )  # Fitting output relative to kk-th element in the list
            slicepos = fitslice[4]  # Spatial position of kk-th MRI slice
            s0_data[:, :, slicepos] = fitslice[0]  # Parameter S0 of VFA model
            txy_data[:, :, slicepos] = fitslice[
                1
            ]  # Parameter T1 of mono-exponential decay model
            exit_data[:, :, slicepos] = fitslice[2]  # Exit code
            sse_data[:, :, slicepos] = fitslice[3]  # Sum of Squared Errors

    ### Save the output maps
    print("    ... saving output files")
    buffer_string = ""
    seq_string = (output_rootname, f"_{T_type}-processedmap.nii.gz")
    txy_outfile = buffer_string.join(seq_string)
    buffer_string = ""
    seq_string = (output_rootname, "_S0-processedmap.nii.gz")
    s0_outfile = buffer_string.join(seq_string)
    buffer_string = ""
    seq_string = (output_rootname, "_Exit-processedmap.nii.gz")
    exit_outfile = buffer_string.join(seq_string)
    buffer_string = ""
    seq_string = (output_rootname, "_SSE-processedmap.nii.gz")
    mse_outfile = buffer_string.join(seq_string)
    buffer_header = sig_obj.header
    buffer_header.set_data_dtype(
        "float64"
    )  # Make sure we save quantitative maps as float64, even if input header indicates a different data type
    txy_obj = nib.Nifti1Image(txy_data, sig_obj.affine, buffer_header)
    nib.save(txy_obj, txy_outfile)
    s0_obj = nib.Nifti1Image(s0_data, sig_obj.affine, buffer_header)
    nib.save(s0_obj, s0_outfile)
    exit_obj = nib.Nifti1Image(exit_data, sig_obj.affine, buffer_header)
    nib.save(exit_obj, exit_outfile)
    mse_obj = nib.Nifti1Image(sse_data, sig_obj.affine, buffer_header)
    nib.save(mse_obj, mse_outfile)

    return True
