import os
import nibabel as nib
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import tkinter as tk
from resomapper.core.misc import auto_innited_logger as lggr

import warnings

warnings.filterwarnings("ignore")

default_map_scales = {
    "T1map": [2000, 6000],
    "T2map": [0, 200],
    "T2starmap": [0, 80],
    "MTRmap": [0, 55],
    "MDmap": [0, 2500],
    "ADmap": [0, 3000],
    "RDmap": [0, 2500],
    "FAmap": [0, 1],
    "ADCmap": [0, 2500],
}

defaulr_map_units = {
    "T1map": "T\u2081 (ms)",
    "T2map": "T\u2082 (ms)",
    "T2starmap": "T\u2082* (ms)",
    "MTRmap": "MT ratio (%)",
    "MDmap": "MD (\u03bcm\u00b2/s)",
    "ADmap": "AD (\u03bcm\u00b2/s)",
    "RDmap": "RD (\u03bcm\u00b2/s)",
    "FAmap": "FA",
    "ADCmap": "ADC (\u03bcm\u00b2/s)"
}


def rotate(array_2d):
    list_of_tuples = zip(*array_2d[::-1])
    return [list(elem) for elem in list_of_tuples]


def heatmap_printer(
    map_path,
    map_type,
    vmin,
    vmax,
    selected_slice=None,
    selected_dir=None,
    cmap=plt.cm.magma,
    save=False,
    print_filename=True,
    units_text=""
):
    img = nib.load(map_path)
    maps = np.array(img.dataobj)
    maps[maps == 0.0] = np.nan

    if selected_dir is not None:
        dir_idx = selected_dir
        maps = maps[..., dir_idx]

    maps = np.rollaxis(maps, 2)

    if selected_slice is None:
        n_slices = np.shape(maps)[0]
        if n_slices % 2 == 0:
            cols = int(np.divide(n_slices, 2))
        else:
            cols = int(np.divide(n_slices, 2) + 0.5)
        fig, ax = plt.subplots(2, cols, figsize=(12, 8))
        ax = ax.flatten()
        plt.axis("off")
        cbar_ax = fig.add_axes([0.91, 0.3, 0.03, 0.4])

        for slc_idx, new_map in enumerate(maps):
            r_map = rotate(new_map)
            sns.heatmap(
                r_map,
                cmap=cmap,
                cbar_kws={'label': units_text, 'shrink': 0.8},
                xticklabels=False,
                yticklabels=False,
                vmin=vmin,
                vmax=vmax,
                cbar_ax=cbar_ax,
                ax=ax[slc_idx],
            ).invert_xaxis()
            ax[slc_idx].set_title(f"{map_type} slice {str(slc_idx)}")
        if selected_dir is None:
            if print_filename:
                plt.suptitle(f"{map_type} slices\n{os.path.basename(map_path)}")
            else:
                plt.suptitle(f"{map_type} slices")
            slicetext = "allslices"
        else:
            if print_filename:
                plt.suptitle(f"{map_type} slices (dir {dir_idx})\n{os.path.basename(map_path)}")
            else:
                plt.suptitle(f"{map_type} slices (dir {dir_idx})")
            slicetext = f"allslicesdir{dir_idx}"
        fig.tight_layout(rect=[0, 0, 0.9, 1])

    else:
        slc_idx = selected_slice
        new_map = maps[slc_idx]
        r_map = rotate(new_map)
        sns.heatmap(
            r_map, cmap=cmap, cbar_kws={'label': units_text, 'shrink': 0.8}, xticklabels=False, yticklabels=False, vmin=vmin, vmax=vmax
        ).invert_xaxis()
        if selected_dir is None:
            if print_filename:
                plt.title(f"{map_type} slice {str(slc_idx)}\n{os.path.basename(map_path)}")
            else:
                plt.title(f"{map_type} slice {str(slc_idx)}")
            slicetext = f"slice{str(slc_idx)}"
        else:
            if print_filename:
                plt.title(f"{map_type} slice {str(slc_idx)} (dir {dir_idx})\n{os.path.basename(map_path)}")
            else:
                plt.title(f"{map_type} slice {str(slc_idx)} (dir {dir_idx})")
            slicetext = f"slice{str(slc_idx)}dir{dir_idx}"

    if save is True:
        fig.savefig(map_path.replace(".nii.gz", f"_{slicetext}-colormap.png"))
        plt.close()
    else:
        fig.show()

def auto_save_heatmap(
    map_path, map_type, cmap=plt.cm.magma, default_scales=default_map_scales, default_cbarlabels=defaulr_map_units
):
    vmin, vmax = default_scales[map_type]
    units_text = default_cbarlabels[map_type]

    if map_type != "ADCmap":
        heatmap_printer(
            map_path,
            map_type,
            vmin,
            vmax,
            selected_slice=None,
            selected_dir=None,
            cmap=cmap,
            save=True,
            units_text=units_text
        )
    else:
        adc_nii = nib.load(map_path)
        adc_nii_data = np.array(adc_nii.dataobj)
        for dir_idx in range(np.shape(adc_nii_data)[3]):
            heatmap_printer(
                map_path,
                map_type,
                vmin,
                vmax,
                selected_slice=None,
                selected_dir=dir_idx,
                cmap=cmap,
                save=True,
                units_text=units_text
            )



def cli_show_and_save_heatmap(
    map_path, map_type, cmap=plt.cm.magma, default_scales=default_map_scales, default_cbarlabels=defaulr_map_units
):
    vmin, vmax = default_scales[map_type]
    units_text = default_cbarlabels[map_type]

    selected_dir = 0 if map_type == "ADCmap" else None

    heatmap_printer(
        map_path,
        map_type,
        vmin,
        vmax,
        selected_slice=None,
        selected_dir=selected_dir,
        cmap=plt.cm.magma,
        save=False,
        units_text=units_text
    )

    print(
        f"\n{lggr.ask}Please specify how do you want to save the color heatmap in the pop-up window."
    )

    # create a frame
    root = tk.Tk()
    root.title("resomapper")

    # declaring string variable for storing values
    color_min = tk.IntVar()
    color_max = tk.IntVar()
    colormap = tk.StringVar()

    tk.Label(root, text="Minimum", font=("calibre", 10, "bold")).grid(row=0, column=0)
    tk.Label(root, text="Maximum", font=("calibre", 10, "bold")).grid(row=2, column=0)
    tk.Label(root, text="Color scale", font=("calibre", 10, "bold")).grid(
        row=4, column=0
    )

    # creating entries for inputs
    color_min_entry = tk.Entry(
        root, textvariable=color_min, font=("calibre", 10, "normal")
    )
    color_max_entry = tk.Entry(
        root, textvariable=color_max, font=("calibre", 10, "normal")
    )
    colormap_entry = tk.Entry(
        root, textvariable=colormap, font=("calibre", 10, "normal")
    )

    color_min_entry.grid(row=1, column=1)
    color_max_entry.grid(row=3, column=1)
    colormap_entry.grid(row=5, column=1)

    # setting default values
    color_min_entry.insert(0, vmin)
    color_max_entry.insert(0, vmax)
    colormap_entry.insert(0, "magma")

    def get_selection():
        color_min_val = color_min_entry.get()
        color_max_val = color_max_entry.get()
        colormap_val = colormap_entry.get()

        plt.close("all")
        plt.clf()

        heatmap_printer(
            map_path,
            map_type,
            color_min_val,
            color_max_val,
            selected_slice=None,
            selected_dir=selected_dir,
            cmap=colormap_val,
            save=False,
            units_text=units_text
        )

    def close():
        color_min_val = color_min_entry.get()
        color_max_val = color_max_entry.get()
        colormap_val = colormap_entry.get()
        plt.close("all")
        plt.clf()

        heatmap_printer(
            map_path,
            map_type,
            color_min_val,
            color_max_val,
            selected_slice=None,
            selected_dir=selected_dir,
            cmap=colormap_val,
            save=True,
            units_text=units_text
        )

        if map_type == "ADCmap":
            adc_nii = nib.load(map_path)
            adc_nii_data = np.array(adc_nii.dataobj)
            for dir_idx in range(np.shape(adc_nii_data)[3]):
                heatmap_printer(
                    map_path,
                    map_type,
                    color_min_val,
                    color_max_val,
                    selected_slice=None,
                    selected_dir=dir_idx,
                    cmap=colormap_val,
                    save=True,
                    units_text=units_text
                )

        root.destroy()
        root.quit()

    tk.Button(root, text="Update", command=get_selection).grid(row=6, column=0)
    tk.Button(root, text="Save", command=close).grid(row=6, column=1)

    root.mainloop()
