import sys
import numpy as np
sys.path.append(r'../python_imaging')
from pyMCDS_ECM import *

# Script REQUIRES ffmpeg to make movei!!!!!!!

######## If using on remote system, uncomment this line below to load correct matplotlib backend ################
# matplotlib.use('Agg')

import matplotlib.pyplot as plt
from matplotlib.patches import Circle
import math, os, sys, re
import scipy
import distutils.util


def print_stats(arr):
    """
    Produces relevant statistical output to screen given an array of any dimension. It flattens the in row-major style,
    the default np.flatten behavior.

    :param arr: any dimensional array, but it probably makes the most sense to be a 2-d array
    :return: Prints to termminal the array mean, quartiles, min, and max.
    """

    print("Mean: ", np.mean(arr.flatten()))
    print("Q2 quantile of arr : ", np.quantile(arr, .50))
    print("Q1 quantile of arr : ", np.quantile(arr, .25))
    print("Q3 quantile of arr : ", np.quantile(arr, .75))
    print("Min : ", arr.min())
    print("Max : ", arr.max())


def create_plot(snapshot, folder, output_folder='.', output_plot=True, show_plot=False):
    """
    Creates a plot as per instructions inside the function. 
    A base layer of a contour plot of either the anisotropy or the oxygen, the cells in the smulation as a scatter plot,
    and finally the ECM orientation overlaid with a quiver plot.

    Parameters
    ----------
    snapshot :
        Base name of PhysiCell output files - eg 'output00000275' --> 'output' + '%08d'
    folder : str
        Path to input data
    output_folder : str
        Path for image output
    output_plot : bool
        True = image file will be made. Image output is required for movie production.
    show_plot : bool
        True = plot is displayed. Expected to be false for large batches.
    Returns
    -------
    Nothing :
        Produces a png image from the input PhysiCell data.
    """
    
    ###### Flags ######

    produce_for_panel = True
    
    ####################################################################################################################
    ####################################            Load data                                   ########################
    ####################################################################################################################
    # load cell and microenvironment data
    mcds = pyMCDS(snapshot + '.xml', folder)

    # loads and reads ECM data
    mcds.load_ecm(snapshot + '_ECM.mat', folder)

    # Get cell positions and attributes, microenvironment, and ECM data for plotting.

    # Cells
    cell_df = mcds.get_cell_df()

    #### Diffusion microenvironment
    xx, yy = mcds.get_2D_mesh()  # Mesh
    plane_oxy = mcds.get_concentrations('oxygen', 0.0)  # Oxyen (used for contour plot)

    #### ECM microenvironment
    xx_ecm, yy_ecm = mcds.get_2D_ECM_mesh()  # Mesh
    plane_anisotropy = mcds.get_ECM_field('anisotropy', 0.0)  # Anistropy (used for scaling and contour plot)
    # plane_anisotropy = micro # Used for contour plot

    ####################################################################################################################
    ####################################            Preprocessing                               ########################
    ####################################################################################################################

    #### Helper varialbes and functions ######

    # Number of contours (could include as a parameter)
    num_levels = 10  # 25 works well for ECM, 38 works well for oxygen

    # Make levels for contours
    levels_o2 = np.linspace(1e-14, 38, num_levels)
    # levels_ecm = np.linspace(1e-14, 1.0, num_levels)
    levels_ecm = np.linspace(0.90, 0.93, num_levels) # for the march environment - need to especially highlight small changes in anistoropy. 

    ##### Process data for plotting - weight fibers by anisotropy, mask out 0 anisotropy ECM units, get cell radii and types

    # Anisotropy strictly runs between 0 and 1. Element by element mulitplication produces weighted lengths between 0 - 1
    # for vizualization

    scaled_ECM_x = np.multiply(mcds.data['ecm']['ECM_fields']['x_fiber_orientation'][:, :, 0], plane_anisotropy)
    scaled_ECM_y = np.multiply(mcds.data['ecm']['ECM_fields']['y_fiber_orientation'][:, :, 0], plane_anisotropy)

    # if we want the arrows the same length instead
    ECM_x = mcds.data['ecm']['ECM_fields']['x_fiber_orientation'][:, :, 0]
    ECM_y = mcds.data['ecm']['ECM_fields']['y_fiber_orientation'][:, :, 0]

    # mask out zero vectors
    mask = plane_anisotropy > 0.0001

    # get unique cell types and radii
    cell_df['radius'] = (cell_df['total_volume'].values * 3 / (4 * np.pi)) ** (1 / 3)
    types = cell_df['cell_type'].unique()
    colors = ['yellow', 'blue']

    ####################################################################################################################
    ####################################            Plotting                                    ########################
    ####################################################################################################################

    # start plot and make correct size
    fig = plt.figure(figsize=(8, 8))
    ax = fig.gca()
    ax.set_aspect("equal")
    plt.ylim(-500, 500)
    plt.xlim(-500, 500)

    # add contour layer
    # cs = plt.contourf(xx, yy, plane_oxy, cmap="Greens_r", levels=levels_o2)
    cs = plt.contourf(xx_ecm, yy_ecm, plane_anisotropy, cmap="YlGnBu", levels=levels_ecm)

    # Add cells layer
    for i, ct in enumerate(types):
        plot_df = cell_df[cell_df['cell_type'] == ct]
        for j in plot_df.index:
            circ = Circle((plot_df.loc[j, 'position_x'], plot_df.loc[j, 'position_y']),
                           radius=plot_df.loc[j, 'radius'], color='blue', alpha=0.7, edgecolor='black')
            # for a blue circle with a black edge
            # circ = Circle((plot_df.loc[j, 'position_x'], plot_df.loc[j, 'position_y']),
            #                radius=plot_df.loc[j, 'radius'], alpha=0.7, edgecolor='black')
            ax.add_artist(circ)

    # add ECM orientation vectors unscaled by anistorpy ###
    plt.quiver(xx, yy, ECM_x, ECM_y,
    pivot='middle', angles='xy', scale_units='inches', scale=4.75, headwidth=0,headlength=0, headaxislength=0, alpha = 0.3)  ### was at 3.0 before changing the mat size from 12 to 8 to match my otherr images AND get the font for the ticks large

    # Labels and title (will need removed for journal - they will be added manually)
    
    plt.ylim(-500, 500)
    plt.xlim(-500, 500)
    # ax.axis('scaled')

    if produce_for_panel == False:

        ax.set_xlabel('microns')
        ax.set_ylabel('microns')
        fig.colorbar(cs, ax=ax)
        plt.title(snapshot)
        # Carefully place the command to make the plot square AFTER the color bar has been added.
        ax.axis('scaled')
    else:
        
        plt.xticks(fontsize=20)
        plt.yticks(fontsize=20)
        ax.set_xlabel('microns', fontsize=20)
        ax.set_ylabel('microns', fontsize=20)
        fig.tight_layout()

    # Plot output
    if output_plot is True:
        plt.savefig(output_folder + snapshot + '.png', dpi=256)
    if show_plot is True:
        plt.show()
    # plt.close()

if __name__ == '__main__':
    # def create_plot(snapshot, folder, output_folder='.', output_plot=True, show_plot=False)
    snapshot = sys.argv[1]
    output_plot = bool(distutils.util.strtobool(sys.argv[2]))
    show_plot = bool(distutils.util.strtobool(sys.argv[3]))
    create_plot(snapshot, '.', '', output_plot=True, show_plot=False)