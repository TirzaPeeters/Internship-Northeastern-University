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
def select_nodes_on_planarsurface(instance, P1, P2, P3, er):

    """
    Select all nodes within a small box around a rectangular planar surface
    defined by three corner points (P1, P2, P3), where P1 and P3 are opposite corners
    and P2 is adjacent to P1.

    Parameters:
    instance = Abaqus instance containing the nodes
    P1 = coordinates of corner 1 (x1, y1, z1)   (opposite corner to P3)
    P2 = coordinates of corner 2 (x2, y2, z2)   (adjacent to P1)
    P3 = coordinates of corner 3 (x3, y3, z3)   (opposite corner to P1)
    er = margin taken for selecting nodes around planar surface

    Returns:
    selected_nodes = list of nodes within the selection box
    e1 = normalized in-plane direction 1
    e2 = normalized in-plane direction 2
    n = normalized out of plane direction
    P1 = coordinates of corner 1 (x1, y1, z1)   (opposite corner to P3)
    P2 = coordinates of corner 2 (x2, y2, z2)   (adjacent to P1)
    P3 = coordinates of corner 3 (x3, y3, z3)   (opposite corner to P1)
    P4 = coordinates of corner 4 (x4, y4, z4)   (adjacent to P1)

    """
    # Convert coordinates to arrays
    P1 = np.array(P1, dtype=float)
    P2 = np.array(P2, dtype=float)
    P3 = np.array(P3, dtype=float)

    # Compute the fourth corner
    P4 = P1 + (P3 - P2)

    # Compute in-plane edge vectors from P1
    v1 = P2 - P1
    v2 = P4 - P1

    # Compute normal vector
    n = np.cross(v1, v2)                                # compute normal vector on planar surface
    n = n / np.linalg.norm(n)                           # normalize the normal vector

    # Compute plane center
    center = (P1 + P3) / 2.0

    # Half-lengths
    half_l1 = np.linalg.norm(v1) / 2.0                  # half the length of edge 1 of the planar surface
    half_l2 = np.linalg.norm(v2) / 2.0                  # half the length of edge 2 of the planar surface

    # Normalize in-plane directions
    e1 = v1 / np.linalg.norm(v1)
    e2 = v2 / np.linalg.norm(v2)

    selected_nodes = []                                 # create empty list to store selected nodes

    for node in instance.nodes:
        # Loop over all nodes for the instance
        p = np.array(node.coordinates, dtype=float)     # convert coordinates to array
        rel = p - center                                # calculate the relative vector between the center and the node

        # Calculate local coordinates (x',y',z') in local plane system (e1,e2,n)
        xp = np.dot(rel, e1)
        yp = np.dot(rel, e2)
        zp = np.dot(rel, n)

        # Select nodes if they are inside the box with margin er around the planar surface
        if (abs(xp) <= half_l1 + er and
            abs(yp) <= half_l2 + er and
            abs(zp) <= er):
            selected_nodes.append(node.label)

    return sorted(selected_nodes), e1, e2, n, P1, P2, P3, P4

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
odb_filepath_heat = r"C:\Users\Tirza\Documents\Abq_XS1_10trk\heat_transfer.odb"
odb_filepath_stress = r"C:\Users\Tirza\Documents\Abq_XS1_10trk\Stress.odb"

instance_name = 'SUBWITHDEP-1'

# ------------------ PROCESS HEAT ODB (NT11) ------------------
start_time = time.time()

odb_heat = openOdb(path=odb_filepath_heat, readOnly=True)           # open the heat_transfer odb file
instance_heat = odb_heat.rootAssembly.instances[instance_name]

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

for plane in range(4):

    if plane == 0:
        # Define 3 corner points of rectangular planar surface
        # P1 and P3 are opposite; P2 adjacent to P1
        P1 = (-5.0, 8.0, 132.0)
        P2 = (5.0, 8.0, 132.0)                         
        P3 = (5.0, 8.0, 172.0)                        
        er = 1e-3                                     
        surface_name = 'horizontal_y8'	

    elif plane == 1:
        # Define 3 corner points of rectangular planar surface
        # P1 and P3 are opposite; P2 adjacent to P1
        P1 = (-5.0, 8.5, 132.0)
        P2 = (5.0, 8.5, 132.0)                         
        P3 = (5.0, 8.5, 172.0)                        
        er = 1e-3                                     
        surface_name = 'horizontal_y8_5'

    elif plane == 2:
        P1 = (-5.0, 8.0, 172.0)
        P2 = (-5.0, 8.5, 172.0)                         
        P3 = (-5.0, 8.5, 132.0)                        
        er = 1e-3                                     
        surface_name = 'vertical_x-5'

    elif plane == 3:
        P1 = (0.0, 8.0, 172.0)
        P2 = (0.0, 8.5, 172.0)                         
        P3 = (0.0, 8.5, 132.0)                        
        er = 1e-3                                     
        surface_name = 'vertical_x0'

    # Store coordinates and labels of nodes on planar surface
    surface_nodes, e1, e2, n, P1a, P2a, P3a, P4a = select_nodes_on_planarsurface(instance_heat, P1, P2, P3, er)
    node_coordinates = {nlabel: instance_heat.getNodeFromLabel(nlabel).coordinates for nlabel in surface_nodes}

    # Write NT11 csv file
    NT11_filename = 'NT11_over_time_' + surface_name + '_surface.csv'

    with open(NT11_filename, 'wb') as f:  
        w = csv.writer(f)

        # Write metadata row containing frames per step
        w.writerow(["frames_per_step"]+[len(s.frames) for s in odb_heat.steps.values()])

        # Write metadata row containing corner points
        w.writerow(["P1, P2, P3, P4"]+[P1a, P2a, P3a, P4a])

        # Write metadata row with times
        w.writerow(times)

        # Write empty separator row
        w.writerow([])

        # Write data header
        header = ["Node","xp","yp", "zp"] + ["T{}".format(i) for i in range(len(all_frames))]
        w.writerow(header)

        # Write one row per node
        for node in surface_nodes:
            # Loop over nodes on surface and calculate local coordinates
            x,y,z = node_coordinates[node]
            rel = np.array([x,y,z]) - P1a
            xp = np.dot(rel, e1)
            yp = np.dot(rel, e2)
            zp = np.dot(rel, n)
            row = [node, xp, yp, zp]

            # Calculate temperature at each node for each frame
            for frame in NT11_frames_dict:
                value = frame.get(node, None)
                row.append("" if value is None else "{:.6f}".format(value))

            w.writerow(row)

        print("CSV saved as:", NT11_filename)

odb_heat.close()
end_time = time.time()
elapsed_time = end_time - start_time
print("Script execution time NT11: ", elapsed_time)

# ------------------ PROCESS STRESS ODB (S11, S22, S33, Smises) ------------------
start_time = time.time()

odb_stress = openOdb(path=odb_filepath_stress, readOnly=True)               # Open stress odb file
instance_stress = odb_stress.rootAssembly.instances[instance_name]

node_to_elements = get_connected_elements(instance_stress)

# Store all frames and their times for the stress odb file (different for heat_transfer odb file)
all_frames_stress = []
times_stress = ["time (s)", "", "", ""]
for step in odb_stress.steps.values():
    for frame in step.frames:
        all_frames_stress.append(frame)
        times_stress.append(frame.frameValue)

# stress_outputs = ['S11', 'S22', 'S33', 'S12', 'S13', 'S23', 'Smises']
stress_outputs = ['S11', 'S22', 'S33', 'Smises']

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

for plane in range(4):

    start_time = time.time()

    if plane == 0:
        # Define 3 corner points of rectangular planar surface
        # P1 and P3 are opposite; P2 adjacent to P1
        P1 = (-5.0, 8.0, 132.0)
        P2 = (5.0, 8.0, 132.0)                         
        P3 = (5.0, 8.0, 172.0)                        
        er = 1e-3                                     
        surface_name = 'horizontal_y8'	

    elif plane == 1:
        # Define 3 corner points of rectangular planar surface
        # P1 and P3 are opposite; P2 adjacent to P1
        P1 = (-5.0, 8.5, 132.0)
        P2 = (5.0, 8.5, 132.0)                         
        P3 = (5.0, 8.5, 172.0)                        
        er = 1e-3                                     
        surface_name = 'horizontal_y8_5'

    elif plane == 2:
        P1 = (-5.0, 8.0, 172.0)
        P2 = (-5.0, 8.5, 172.0)                         
        P3 = (-5.0, 8.5, 132.0)                        
        er = 1e-3                                     
        surface_name = 'vertical_x-5'

    elif plane == 3:
        P1 = (0.0, 8.0, 172.0)
        P2 = (0.0, 8.5, 172.0)                         
        P3 = (0.0, 8.5, 132.0)                        
        er = 1e-3                                     
        surface_name = 'vertical_x0'

    # Store coordinates and labels of nodes on planar surface
    surface_nodes_stress, e1, e2, n, P1a, P2a, P3a, P4a = select_nodes_on_planarsurface(instance_stress, P1, P2, P3, er)
    node_coordinates_stress = {nlabel: instance_stress.getNodeFromLabel(nlabel).coordinates for nlabel in surface_nodes_stress}

    # Now write a CSV per stress component, reusing the cached element IP data
    for field_output_index, field_name in enumerate(stress_outputs):
        stress_filename = field_name + '_over_time_' + surface_name + '_surface.csv'

        with open(stress_filename, 'wb') as f:  
            w = csv.writer(f)

            # Write metadata row containing frames per step
            w.writerow(["frames_per_step"]+[len(s.frames) for s in odb_stress.steps.values()])

            # Write metadata row containing corner points
            w.writerow(["P1, P2, P3, P4"]+[P1a, P2a, P3a, P4a])

            # Write metadata row with times
            w.writerow(times_stress)

            # Write empty separator row
            w.writerow([])

            # Write data header
            header = ["Node","xp","yp","zp"] + ["S{}".format(i) for i in range(len(all_frames_stress))]
            w.writerow(header)

            # Write one row per node
            for node in surface_nodes_stress:
                # Loop over nodes on surface and calculate local coordinates
                x,y,z = node_coordinates_stress[node]
                rel = np.array([x,y,z]) - P1a
                xp = np.dot(rel, e1)
                yp = np.dot(rel, e2)
                zp = np.dot(rel, n)
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
print("Script execution time all stresses: ", elapsed_time)

