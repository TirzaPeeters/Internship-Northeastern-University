from abaqus import *
from abaqusConstants import *
from odbAccess import openOdb
import numpy as np
import os
import math
import csv
from collections import defaultdict
import time

# Define function to find nodes on planar surface (kept from your original code)
def select_nodes_at_target_coordinates(instance, P, er):

    """
    Select all nodes within a small box around the target node coordinates.

    Parameters:
    instance = Abaqus instance containing the nodes
    P = coordinates of target node (x1, y1, z1)  
    er = margin taken for selecting nodes around planar surface

    Returns:
    selected_nodes = list of nodes within the selection box
    P = coordinates of target node (x1, y1, z1) 

    """
    # Convert coordinates to arrays
    P_target = np.array(P, dtype=float)

    selected_nodes = []                                 # create empty list to store selected nodes

    for node in instance.nodes:
        # Loop over all nodes for the instance
        p = np.array(node.coordinates, dtype=float)     # convert coordinates to array
        rel = p - P_target                              # calculate the relative vector between the node and the target node

        # Split components of the relative vector
        dx = rel[0]
        dy = rel[1]
        dz = rel[2]

        # Select nodes if they are inside the box with margin er around the target node coordinates
        if (abs(dx) <= er and
            abs(dy) <= er and
            abs(dz) <= er):
            selected_nodes.append(node.label)

    return sorted(selected_nodes), P

# Define function to find connected elements for each node
def get_connected_elements(instance):

    """
    Build a lookup variable to find elements connected to a node.

    Parameters:
    Instance = Abaqus instance containing the nodes

    Returns:
    node_to_elements = lists for each node with the connected elements

    """

    # Create empty lists
    node_to_elements = defaultdict(list)

    # Loop over all elements and store to which nodes it is connected
    for el in instance.elements:
        for n in el.connectivity:
            node_to_elements[n].append(el.label)

    return node_to_elements

# ---------------- USER SETTINGS ----------------
odb_filepath_heat = r"C:\Users\Tirza\Documents\Abaq_finalcleanXS\heat_transfer.odb"
odb_filepath_stress = r"C:\Users\Tirza\Documents\Abaq_finalcleanXS\Stress.odb"

instance_name = 'SUBWITHDEP-1'

for point in range(3):

    start_time = time.time()

    if point == 0:
        # Define target node coordinates
        P = (-15.0, 8.0, 132.0)
        er = 1e-3                                               # margin for node selection around target node coordinates
        point_name = 'XS_P_-15_8_132'							    # define your point name, which is used for the output file name

    elif point == 1:
        # Define target node coordinates
        P = (0.0, 8.0, 152.0)
        er = 1e-3                                               # margin for node selection around target node coordinates
        point_name = 'XS_P_0_8_152'							    # define your point name, which is used for the output file name

    elif point == 2:
        # Define target node coordinates
        P = (-14.0, 8.0, 133.0)
        er = 1e-3                                               # margin for node selection around target node coordinates
        point_name = 'XS_P_-14_8_133'							    # define your point name, which is used for the output file name

    # ------------------ PROCESS HEAT ODB (NT11) ------------------
    odb_heat = openOdb(path=odb_filepath_heat, readOnly=True)           # open the heat_transfer odb file
    instance_heat = odb_heat.rootAssembly.instances[instance_name]

    # Store coordinates and labels of selected nodes
    selected_nodes, P = select_nodes_at_target_coordinates(instance_heat, P, er)
    node_coordinates = {nlabel: instance_heat.getNodeFromLabel(nlabel).coordinates for nlabel in selected_nodes}

    # Store all frames and their times for the heat_transfer odb file (different for stress odb file)
    all_frames = []
    times = ["time (s)", "", "", ""]
    for step in odb_heat.steps.values():
        for frame in step.frames:
            all_frames.append(frame)
            times.append(frame.frameValue)

    # Preload temperature field 'NT11' for each frame into a dict with the nodeLabels and their temperatures
    NT11_frames_dict = []  

    for frame in all_frames:
        try:
            fo = frame.fieldOutputs['NT11']
            subset = fo.getSubset(region=instance_heat)  
            frame_dict = {val.nodeLabel: val.data for val in subset.values}
        except Exception:
            frame_dict = {}

        NT11_frames_dict.append(frame_dict)

    # Write NT11 csv file
    NT11_filename = 'NT11_over_time_' + point_name + '.csv'

    with open(NT11_filename, 'wb') as f:  
        w = csv.writer(f)

        # Write metadata row containing frames per step
        w.writerow(["frames_per_step"]+[len(s.frames) for s in odb_heat.steps.values()])

        # Write metadata row containing target node coordinates
        w.writerow(["P="]+[P])

        # Write metadata row with times
        w.writerow(times)

        # Write empty separator row
        w.writerow([])

        # Write data header
        header = ["Node","xp","yp", "zp"] + ["T{}".format(i) for i in range(len(all_frames))]
        w.writerow(header)

        # Write one row per node
        for node in selected_nodes:
            # Loop over selected nodes and store coordinates
            xp,yp,zp = node_coordinates[node]
            row = [node, xp, yp, zp]

            # Calculate temperature at each node for each frame
            for frame in NT11_frames_dict:
                value = frame.get(node, None)
                row.append("" if value is None else "{:.6f}".format(value))

            w.writerow(row)

    odb_heat.close()
    print("CSV saved as:", NT11_filename)

    # ------------------ PROCESS STRESS ODB (S11, S22, S33, S12, S13, S23, Smises) ------------------
    odb_stress = openOdb(path=odb_filepath_stress, readOnly=True)               # Open stress odb file
    instance_stress = odb_stress.rootAssembly.instances[instance_name]

    # Store coordinates and labels of selected nodes 
    selected_nodes_stress, P = select_nodes_at_target_coordinates(instance_stress, P, er)
    node_coordinates_stress = {nlabel: instance_stress.getNodeFromLabel(nlabel).coordinates for nlabel in selected_nodes_stress}
    node_to_elements = get_connected_elements(instance_stress)

    # Store all frames and their times for the stress odb file (different for heat_transfer odb file)
    all_frames_stress = []
    times_stress = ["time (s)", "", "", ""]
    for step in odb_stress.steps.values():
        for frame in step.frames:
            all_frames_stress.append(frame)
            times_stress.append(frame.frameValue)

    # stress_outputs = ['S11', 'S22', 'S33', 'S12', 'S13', 'S23', 'Smises']
    stress_outputs = ['S11', 'Smises']

    # Preload stress field 'S' for each frame into a dict with the nodeLabels and a list with their stresses
    stress_frames_element_dict = [] 

    for frame in all_frames_stress:
        element_map = defaultdict(list)
        try:
            fo = frame.fieldOutputs['S']
            subset = fo.getSubset(region=instance_stress)  
            for val in subset.values:
                elabel = val.elementLabel
                data_tuple = val.data 
                mises_val = val.mises
                element_map[elabel].append((data_tuple, mises_val))
        except Exception:
            element_map = defaultdict(list)

        stress_frames_element_dict.append(element_map)

    # Now write a CSV per stress component, reusing the cached element IP data
    for field_output_index, field_name in enumerate(stress_outputs):
        stress_filename = field_name + '_over_time_' + point_name + '.csv'

        with open(stress_filename, 'wb') as f:  
            w = csv.writer(f)

            # Write metadata row containing frames per step
            w.writerow(["frames_per_step"]+[len(s.frames) for s in odb_stress.steps.values()])

            # Write metadata row containing target node coordinates
            w.writerow(["P="]+[P])

            # Write metadata row with times
            w.writerow(times_stress)

            # Write empty separator row
            w.writerow([])

            # Write data header
            header = ["Node","xp","yp","zp"] + ["S{}".format(i) for i in range(len(all_frames_stress))]
            w.writerow(header)

            # Write one row per node
            for node in selected_nodes_stress:
                # Loop over selected nodes and store coordinates
                xp,yp,zp = node_coordinates_stress[node]
                row = [node, xp, yp, zp]

                connected_elements = node_to_elements.get(node, [])

                # Calculate stress at each node for each frame
                for frame in stress_frames_element_dict:
                    values = []
                    for elabel in connected_elements:
                        ip_list = frame.get(elabel, [])
                        for (data_tuple, mises_val) in ip_list:
                            if field_name == 'Smises':
                                values.append(mises_val)
                            elif field_name == 'S11':
                                values.append(data_tuple[0])
                            elif field_name == 'S22':
                                values.append(data_tuple[1])
                            elif field_name == 'S33':
                                values.append(data_tuple[2])
                            elif field_name == 'S12':
                                values.append(data_tuple[3])
                            elif field_name == 'S13':
                                values.append(data_tuple[4])
                            elif field_name == 'S23':
                                values.append(data_tuple[5])

                    value = sum(values)/len(values) if values else None
                    row.append("" if value is None else "{:.6f}".format(value))

                w.writerow(row)

        print("CSV saved as:", stress_filename)

    odb_stress.close()

    end_time = time.time()
    elapsed_time = end_time - start_time
    print("Script execution time: ", elapsed_time)

