from abaqus import *
from abaqusConstants import *
import __main__
import section
import regionToolset
import displayGroupMdbToolset as dgm
import part
import material
import assembly
import optimization
import step
import interaction
import load
import mesh
import job
import sketch
import visualization
import xyPlot
import displayGroupOdbToolset as dgo
import connectorBehavior
import os
from caeModules import *
import math
import string
import sys
import os.path
import json
import interaction
from collections import OrderedDict
import csv

from textRepr import prettyPrint as PP

os.chdir(r"C:\Users\Tirza\Documents\Abaqus_step_opt")

# 
#  UNITS:
#  - LENGTH: 	mm
#  - TIME: 		s
#  - MASS: 		kg
#  - TEMP:		K
#  - FORCE:		mN
#  - PRESSURE: 	kPa
#  - ENERGY: 	uJ
#  - POWER: 	uW



session.journalOptions.setValues(replayGeometry=COORDINATE, recoverGeometry=COORDINATE)


def convert_csv_to_json(csv_file_path, json_file_path):
    """
    Convert a CSV file to a JSON file, ignoring any columns beyond the first two.
    #
    :param csv_file_path: Path to the CSV file.
    :param json_file_path: Path to the output JSON file.
    """
    # Initialize an ordered dictionary to maintain the order of data
    data = OrderedDict()
    #
    # Read the CSV file
    with open(csv_file_path, 'r') as csv_file:
        reader = csv.reader(csv_file)
        current_category = None
        for row in reader:
            # Adjusted to handle rows where category names might follow an empty string
            if len(row) >= 1 and row[0] and not row[1]:
                current_category = row[0]
                data[current_category] = OrderedDict()
            # Handle key-value pairs, ignoring any third column or beyond
            elif len(row) >= 2 and current_category is not None:
                key, value = row[:2]  # Only consider the first two columns for key-value pairs
                if value:  # Ensure the value is not empty
                    try:
                        # Attempt to convert numeric values
                        data[current_category][key] = float(value)
                    except ValueError:
                        data[current_category][key] = value
                else:
                    print("Skipping row with empty value:", row)
            else:
                # This can be refined or removed based on actual CSV format
                print("Skipping unrecognized row:", row)
    #
    # Write to the JSON file
    with open(json_file_path, 'w') as json_file:
        json.dump(data, json_file, indent=4)
    #
    return json_file_path



current_directory = os.getcwd()


for finp in os.listdir('.'):
  if finp.endswith(".csv"):
      csv_file_path       = os.path.join(current_directory, finp)
      json_file_path      = os.path.join(current_directory, 'converted_data.json')
      converted_json_path = convert_csv_to_json(csv_file_path, json_file_path)
      print "Conversion successful. JSON file saved at:", converted_json_path


secname='converted_data.json'


with open(secname, 'r') as f:
    data=json.load(f)

#########
# Tirza Peeters change 11-04-2025 added parameter for hotplateSS if-statement
Run_step_1 = 1                      # 1 if hotplateSS step should be included, 0 if not
# Tirza Peeters change 11-04-2025 added parameter for preheating if-statement
Run_step_2 = 0                      # 1 if preheating step should be included, 0 if not

UnitDepLength       = 1
UnitDepLengthBase   = UnitDepLength*5
#
# SM change: Changed the inputs from hardcode to the parameters files
#
HotplateSSTime      = data['Steps']['HotplateSSTime']
HotplateSSTimeInc   = data['Steps']['HotplateSSTimeInc']
HotPlateTemp        = data['HotPlate']['HotPlateTemp'] 
film_ContactCoefHP  = data['HotPlate']['film_ContactCoefHP']
FreeConvectionCf    = data['Others']['FreeConvectionCf']

print("HotPlateTemp       = {} ".format(HotPlateTemp))
print("film_ContactCoefHP = {} ".format(film_ContactCoefHP))
print("FreeConvectionCf   = {} ".format(FreeConvectionCf))
#
# SM change: end of the chaanged area
#
#############
# others
ambientTemp         = data['Others']['ambientTemp']
emissSubsDep        = data['Others']['emissSubsDep']

DepInitialTemp      = 590
SubstrateTemp       = ambientTemp
BaseInitialTemp     = ambientTemp

#Base
baseWidth           = data['Base']['baseWidth']
baseLength          = data['Base']['baseLength']
baseThick           = data['Base']['baseThick']

#Substrate
subsWidth           = data['Substrate']['subsWidth']
subsLength          = data['Substrate']['subsLength']
subsThick           = data['Substrate']['subsThick']

# deposition
#Trk 
depTrkWidth         = data['Deposition']['depTrkWidth']
depTrkThick         = data['Deposition']['depTrkThick']
depTrksPerLyr       = data['Deposition']['depTrksPerLyr']

# Layers
depNoOfLyrs         = data['Layers']['depNoOfLyrs']

depWidth 	        = depTrkWidth * depTrksPerLyr
depLength 	        = subsLength
depThick 	        = depTrkThick * depNoOfLyrs

PartitionThick      = depTrkThick

NumPartition        = depThick/PartitionThick

dep1Width 		= depWidth # needs to be a function of number of pass and thickness of each pass
dep1Length 		= (baseLength-subsLength)/2
dep1Thick 		= depThick  # needs to be a function of number of layers and thickness of each layer

dep2Width 		= depWidth # needs to be a function of number of pass and thickness of each pass
dep2Length 		= subsLength
dep2Thick 		= depThick  # needs to be a function of number of layers and thickness of each layer

dep3Width 		= depWidth # needs to be a function of number of pass and thickness of each pass
dep3Length 		= (baseLength-subsLength)/2
dep3Thick 		= depThick  # needs to be a function of number of layers and thickness of each layer


subsMatl        = 'Al6061'
depMatl         = 'Al6061'
BaseMatl        = 'Al6061'

#Steps
PreHeatingTime      = data['Steps']['PreHeatingTime']
PreHeatingTimeInc   = data['Steps']['PreHeatingTimeInc']
#DepositionTime      = data['Steps']['DepositionTime']
DepositionTimeInc   = data['Steps']['DepositionTimeInc']
CoolingTime1        = data['Steps']['CoolingTime1']
CoolingTimeInc1     = data['Steps']['CoolingTimeInc1']
ReleaseFixturesTime = data['Steps']['ReleaseFixturesTime']
CoolingTime2        = data['Steps']['CoolingTime2']
CoolingTimeInc2     = data['Steps']['CoolingTimeInc2']

# ................
# SM addition-01
#
sprayNzzlVel       = data['Nozzle']['sprayNzzlVel']
sprayNzzlAccel     = data['Nozzle']['sprayNzzlAccel']
depLength          = data['Deposition']['depLength']

sprayTimePerTrk    = sprayNzzlVel/sprayNzzlAccel + depLength/sprayNzzlVel
DepositionTime     = sprayTimePerTrk * depTrksPerLyr * depNoOfLyrs

print("sprayNzzlVel        = {} ".format(sprayNzzlVel))
print("sprayNzzlAccel      = {} ".format(sprayNzzlAccel))
print("dep1Length          = {} ".format(depLength))

print("sprayTimePerTrk = {} ".format(sprayTimePerTrk))
print("depTrksPerLyr   = {} ".format(depTrksPerLyr))
print("depNoOfLyrs     = {} ".format(depNoOfLyrs)) 
print("DepositionTime  = {} ".format(DepositionTime))
#
# ................
# 
# SM addition-02
TimeTotal       = HotplateSSTime + PreHeatingTime + DepositionTime + CoolingTime1 + ReleaseFixturesTime + CoolingTime2

TimeStep01Begin = 0
TimeStep01End   = HotplateSSTime

TimeStep02Begin = HotplateSSTime
TimeStep02End   = HotplateSSTime + PreHeatingTime

TimeStep03Begin = HotplateSSTime + PreHeatingTime
TimeStep03End   = HotplateSSTime + PreHeatingTime + DepositionTime

TimeStep04Begin = HotplateSSTime + PreHeatingTime + DepositionTime
TimeStep04End   = HotplateSSTime + PreHeatingTime + DepositionTime + CoolingTime1

TimeStep05Begin = HotplateSSTime + PreHeatingTime + DepositionTime + CoolingTime1
TimeStep05End   = HotplateSSTime + PreHeatingTime + DepositionTime + CoolingTime1 + ReleaseFixturesTime

TimeStep06Begin = HotplateSSTime + PreHeatingTime + DepositionTime + CoolingTime1 + ReleaseFixturesTime
TimeStep06End   = HotplateSSTime + PreHeatingTime + DepositionTime + CoolingTime1 + ReleaseFixturesTime + CoolingTime2

print("TimeTotal       = {} ".format(TimeTotal))
print("TimeStep01Begin = {} ".format(TimeStep01Begin))
print("TimeStep01End   = {} ".format(TimeStep01End))

print("TimeStep02Begin = {} ".format(TimeStep02Begin))
print("TimeStep02End   = {} ".format(TimeStep02End))

print("TimeStep03Begin = {} ".format(TimeStep03Begin))
print("TimeStep03End   = {} ".format(TimeStep03End))

print("TimeStep04Begin = {} ".format(TimeStep04Begin))
print("TimeStep04End   = {} ".format(TimeStep04End))

print("TimeStep05Begin = {} ".format(TimeStep05Begin))
print("TimeStep05End   = {} ".format(TimeStep05End))

print("TimeStep06Begin = {} ".format(TimeStep06Begin))
print("TimeStep06End   = {} ".format(TimeStep06End))

# End of SM addition
#
# ....................

#BC-clamps
clampWidthXplus     = data['clamps']['clampWidthXplus']
clampWidthXminus    = data['clamps']['clampWidthXminus']

#MeshSeeds

BiasMeshSubDir1Ratio=data['Mesh']['BiasMeshSubDir1Ratio']
BiasMeshSubDir2Ratio=data['Mesh']['BiasMeshSubDir2Ratio']
BiasMeshSubDir3Ratio=data['Mesh']['BiasMeshSubDir3Ratio']

GeneralSize	    = depTrkWidth*10

maxSize1	    = depTrkWidth*BiasMeshSubDir1Ratio # TruWidth
minSize1 	    = depTrkWidth

maxSize2	    = depTrkWidth*BiasMeshSubDir2Ratio

maxSize3 	    = UnitDepLength*BiasMeshSubDir3Ratio

minSize1B	    = minSize1*5
maxSize1B	    = maxSize1*5

# TruThickness

# -------------------------------------------------------
# BaseModel_createPart():
# -------------------------------------------------------

myModel=mdb.Model(name='Model-1')
myModel.setValues(absoluteZero=0, stefanBoltzmann=5.669e-08)

##Base
mySketch=myModel.ConstrainedSketch(
	name      = '__profile__', 
	sheetSize = 200.0)

mySketch.rectangle(
	point1=(-baseWidth/2, 0.0), 
	point2=(baseWidth/2, baseThick))

myModel.Part(
    dimensionality=THREE_D, 
    name='BasePlate', 
    type= DEFORMABLE_BODY)
    
myModel.parts['BasePlate'].BaseSolidExtrude(
    depth=baseLength, 
    sketch=mySketch)
del mySketch

##Substrate
mySketch=myModel.ConstrainedSketch(
    name='__profile__', 
    sheetSize=200.0)
    
mySketch.rectangle(
    point1=(-subsWidth/2, baseThick), 
    point2=(subsWidth/2, subsThick+baseThick))
    
myModel.Part(
    dimensionality=THREE_D, 
    name='Substrate', 
    type=DEFORMABLE_BODY)
    
myModel.parts['Substrate'].BaseSolidExtrude(
    depth=subsLength, 
    sketch=mySketch)
del mySketch

##Deposition-1
mySketch=myModel.ConstrainedSketch(
    name='__profile__', 
    sheetSize=200.0)
    
mySketch.rectangle(
    point1=(-dep1Width/2, baseThick), 
    point2=(dep1Width/2, dep1Thick+baseThick))
    
myModel.Part(
    dimensionality=THREE_D, 
    name='Deposition-1', 
    type=DEFORMABLE_BODY)
    
myModel.parts['Deposition-1'].BaseSolidExtrude(
    depth=dep1Length, 
    sketch=mySketch)
del mySketch

##Deposition-2
mySketch=myModel.ConstrainedSketch(
    name='__profile__', 
    sheetSize=200.0)
    
mySketch.rectangle(
    point1=(-dep2Width/2, baseThick+subsThick), 
    point2=(dep2Width/2, dep2Thick+baseThick+subsThick))
    
myModel.Part(
    dimensionality=THREE_D, 
    name='Deposition-2', 
    type=DEFORMABLE_BODY)
    
myModel.parts['Deposition-2'].BaseSolidExtrude(
    depth=dep2Length, 
    sketch=mySketch)
del mySketch

##Deposition-3
mySketch=myModel.ConstrainedSketch(
    name='__profile__', 
    sheetSize=200.0)
    
mySketch.rectangle(
    point1=(-dep3Width/2, baseThick), 
    point2=(dep3Width/2, dep3Thick+baseThick))
    
myModel.Part(
    dimensionality=THREE_D, 
    name='Deposition-3', 
    type=DEFORMABLE_BODY)

myModel.parts['Deposition-3'].BaseSolidExtrude(
    depth=dep3Length, 
    sketch=mySketch)
del mySketch

##Assembly-1
myAssembly=myModel.rootAssembly
myModel.rootAssembly.DatumCsysByDefault(CARTESIAN)
myModel.rootAssembly.Instance(dependent=ON, name='BasePlate-1',    part=myModel.parts['BasePlate'])
myModel.rootAssembly.Instance(dependent=ON, name='Deposition-1-1', part=myModel.parts['Deposition-1'])
myModel.rootAssembly.Instance(dependent=ON, name='Deposition-3-1', part=myModel.parts['Deposition-3'])
myModel.rootAssembly.translate(instanceList=('Deposition-3-1', ),  vector=(0.0, 0.0, dep1Length+subsLength))

##Assembly -1- Merge
myModel.rootAssembly.InstanceFromBooleanMerge(domain=GEOMETRY, 
    instances=(myModel.rootAssembly.instances['BasePlate-1'],  
    myModel.rootAssembly.instances['Deposition-1-1'],  
    myModel.rootAssembly.instances['Deposition-3-1']), 
    keepIntersections=ON, name='BasewithDep', originalInstances=SUPPRESS)
    
    
##Assembly-2
myAssembly=myModel.rootAssembly
myModel.rootAssembly.DatumCsysByDefault(CARTESIAN)
myModel.rootAssembly.Instance(dependent=ON, name='Deposition-2-1', part=myModel.parts['Deposition-2'])
myModel.rootAssembly.Instance(dependent=ON, name='Substrate-1', part=myModel.parts['Substrate'])
myModel.rootAssembly.translate(instanceList=('Substrate-1', ), vector=(0.0, 0.0, dep1Length))
myModel.rootAssembly.translate(instanceList=('Deposition-2-1', ), vector=(0.0, 0.0, dep1Length))


##Assembly -2- Merge
myModel.rootAssembly.InstanceFromBooleanMerge(domain=GEOMETRY, 
    instances=(myModel.rootAssembly.instances['Substrate-1'],  
    myModel.rootAssembly.instances['Deposition-2-1']), 
    keepIntersections=ON, name='SubwithDep', originalInstances=SUPPRESS) 
    

#Datums
#BasewithDep
myPart=myModel.parts['BasewithDep']
myPart.DatumPlaneByPrincipalPlane(offset= dep2Width/2, principalPlane=YZPLANE)                   #2
myPart.DatumPlaneByPrincipalPlane(offset=-dep2Width/2, principalPlane=YZPLANE)                   #3
myPart.DatumPlaneByPrincipalPlane(offset= dep1Length, principalPlane=XYPLANE)                    #4
myPart.DatumPlaneByPrincipalPlane(offset= dep1Length+subsLength, principalPlane=XYPLANE)         #5


#PlaneforDepositononBasePlate
for i in range(1,int(NumPartition)):
    myPart.DatumPlaneByPrincipalPlane(offset=baseThick+PartitionThick*i, principalPlane=XZPLANE) #
    
#Planeforsubstrate-left-right
myPart.DatumPlaneByPrincipalPlane(offset=subsWidth/2, principalPlane=YZPLANE)                   
myPart.DatumPlaneByPrincipalPlane(offset=-subsWidth/2, principalPlane=YZPLANE)  


#Partitions
#BasewithDep
for i in range(int(NumPartition)-1):
    myPart.PartitionCellByDatumPlane(cells= myPart.cells.findAt(((0, baseThick+0.5*PartitionThick+i*PartitionThick, dep1Length/2), ),
    ((0, baseThick+0.5*PartitionThick+i*PartitionThick, baseLength-dep3Length/2), ), ), datumPlane=myPart.datums[i+6])

if int(NumPartition)==1:
    i=-1
  

myPart.PartitionCellByDatumPlane(cells=myPart.cells.findAt(((-baseWidth/2, baseThick/2, baseLength/2), )), datumPlane=myPart.datums[3])
myPart.PartitionCellByDatumPlane(cells=myPart.cells.findAt(((baseWidth/2, baseThick/2, baseLength/2), )), datumPlane=myPart.datums[2])
myPart.PartitionCellByDatumPlane(cells=myPart.cells.findAt(((baseWidth/3, baseThick/2, baseLength/3), )), datumPlane=myPart.datums[4])
myPart.PartitionCellByDatumPlane(cells=myPart.cells.findAt(((baseWidth/3, baseThick/2, 2*baseLength/3), )), datumPlane=myPart.datums[5])
myPart.PartitionCellByDatumPlane(cells=myPart.cells.findAt(((-baseWidth/3, baseThick/2, baseLength/3), )), datumPlane=myPart.datums[4])
myPart.PartitionCellByDatumPlane(cells=myPart.cells.findAt(((-baseWidth/3, baseThick/2, 2*baseLength/3), )), datumPlane=myPart.datums[5])

myPart.PartitionCellByDatumPlane(cells=myPart.cells.findAt(((0, baseThick/2, baseLength/2), )), datumPlane=myPart.datums[4])
myPart.PartitionCellByDatumPlane(cells=myPart.cells.findAt(((0, baseThick/2, baseLength/2), )), datumPlane=myPart.datums[5])


#Right and  Left of substrate on base plate
myPart.PartitionCellByDatumPlane(cells=
    myPart.cells.findAt(
    ((dep1Width/2+(subsWidth-dep1Width)/4, baseThick/2, dep1Length/2), ),
    ((dep1Width/2+(subsWidth-dep1Width)/4, baseThick/2, dep1Length+dep2Length/2), ), 
    ((dep1Width/2+(subsWidth-dep1Width)/4, baseThick/2, dep1Length+dep2Length+dep3Length/2), ), ), 
    datumPlane= myPart.datums[i+7])

myPart.PartitionCellByDatumPlane(cells=
    myPart.cells.findAt(
    ((-dep1Width/2-(subsWidth-dep1Width)/4, baseThick/2, dep1Length/2), ),
    ((-dep1Width/2-(subsWidth-dep1Width)/4, baseThick/2, dep1Length+dep2Length/2), ), 
    ((-dep1Width/2-(subsWidth-dep1Width)/4, baseThick/2, dep1Length+dep2Length+dep3Length/2), ), ), 
    datumPlane= myPart.datums[i+8])


#Datums
#SubwithDep
myPart=myModel.parts['SubwithDep']
myPart.DatumPlaneByPrincipalPlane(offset=dep2Width/2, principalPlane=YZPLANE)                   
myPart.DatumPlaneByPrincipalPlane(offset=-dep2Width/2, principalPlane=YZPLANE)  


for i in range(1,int(NumPartition)):
    myPart.DatumPlaneByPrincipalPlane(offset=baseThick+subsThick+PartitionThick*i, principalPlane=XZPLANE) #
   
##BC-clamps
#X_plus
myPart.DatumPlaneByPrincipalPlane(offset=subsWidth/2-clampWidthXplus, principalPlane=YZPLANE)
#X_minus
myPart.DatumPlaneByPrincipalPlane(offset=-(subsWidth/2-clampWidthXplus), principalPlane=YZPLANE)


#Partitions
#SubwithDep
myPart.PartitionCellByDatumPlane(cells= myPart.cells.findAt(((0, baseThick+subsThick/2, dep1Length+subsLength/2), )), datumPlane=myPart.datums[2])
myPart.PartitionCellByDatumPlane(cells=myPart.cells.findAt(((0, baseThick+subsThick/2, dep1Length+subsLength/2), )), datumPlane=myPart.datums[3])


for i in range(int(NumPartition)-1):
    myPart.PartitionCellByDatumPlane(cells=myPart.cells.findAt(((0, baseThick+subsThick+0.5*PartitionThick+i*PartitionThick, dep2Length/2+dep1Length), )), 
    datumPlane=myPart.datums[i+4])
   

myPart.PartitionCellByDatumPlane(cells=myPart.cells.findAt(((dep2Width/2+(subsWidth-dep2Width)/4, baseThick+subsThick/2, dep2Length/2+dep1Length), )), 
    datumPlane= myPart.datums[i+5])
    
myPart.PartitionCellByDatumPlane(cells=myPart.cells.findAt(((-(dep2Width/2+(subsWidth-dep2Width)/4), baseThick+subsThick/2, dep2Length/2+dep1Length), )), 
    datumPlane= myPart.datums[i+6])
    
    
## Materials 

# Create materials
myModel.Material(name='Copper', 
    description='UNITS:\n- LENGTH: 	mm\n- TIME: 		s\n- MASS: 		kg\n- TEMP:		K\n- FORCE:		mN\n- PRESSURE: 	kPa\n- ENERGY: 	uJ\n- POWER: 	uW\n\nCOMMENTS FROM *DENSITY\n======================\n\nDamage Initiation, criterion=SHEAR\n3.,  0.,100.\nDamage Evolution, type=ENERGY\n0.,\n\nCOMMENTS FROM *SPECIFIC HEAT\n============================\n\nRate Dependent, type=JOHNSON COOK\n 0.025,1.')
myModel.materials['Copper'].Conductivity(table=((387000.0, ), 
    ))
myModel.materials['Copper'].Density(table=((8.94e-06, ), ))
myModel.materials['Copper'].Elastic(temperatureDependency=ON, 
    table=((128000000.0, 0.347, 284.0), (128000000.0, 0.347, 294.0), (
    127000000.0, 0.347, 304.0), (126000000.0, 0.347, 314.0), (126000000.0, 
    0.348, 324.0), (125000000.0, 0.348, 334.0), (124000000.0, 0.348, 
    344.0), (124000000.0, 0.348, 354.0), (123000000.0, 0.349, 364.0), (
    123000000.0, 0.349, 374.0), (122000000.0, 0.349, 384.0), (121000000.0, 
    0.349, 394.0), (121000000.0, 0.35, 404.0), (120000000.0, 0.35, 414.0), 
    (119000000.0, 0.35, 424.0), (119000000.0, 0.35, 434.0), (118000000.0, 
    0.351, 444.0), (117000000.0, 0.351, 454.0), (117000000.0, 0.351, 
    464.0), (116000000.0, 0.351, 474.0), (115000000.0, 0.351, 484.0), (
    115000000.0, 0.352, 494.0), (114000000.0, 0.352, 504.0), (114000000.0, 
    0.352, 514.0), (113000000.0, 0.352, 524.0), (112000000.0, 0.353, 
    534.0), (112000000.0, 0.353, 544.0), (111000000.0, 0.353, 554.0), (
    110000000.0, 0.353, 564.0), (110000000.0, 0.354, 574.0), (109000000.0, 
    0.354, 584.0), (108000000.0, 0.354, 594.0), (108000000.0, 0.354, 
    604.0), (107000000.0, 0.355, 614.0), (107000000.0, 0.355, 624.0), (
    106000000.0, 0.355, 634.0), (105000000.0, 0.355, 644.0), (105000000.0, 
    0.356, 654.0), (104000000.0, 0.356, 664.0), (103000000.0, 0.356, 
    674.0), (103000000.0, 0.356, 684.0), (102000000.0, 0.357, 694.0), (
    102000000.0, 0.357, 704.0), (101000000.0, 0.357, 714.0), (100000000.0, 
    0.357, 724.0), (99600000.0, 0.358, 734.0), (99000000.0, 0.358, 744.0), 
    (98400000.0, 0.358, 754.0), (97700000.0, 0.358, 764.0), (97100000.0, 
    0.358, 774.0), (96400000.0, 0.359, 784.0), (95800000.0, 0.359, 794.0), 
    (95200000.0, 0.359, 804.0), (94500000.0, 0.359, 814.0), (93900000.0, 
    0.36, 824.0), (93200000.0, 0.36, 834.0), (92600000.0, 0.36, 844.0), (
    91900000.0, 0.36, 854.0), (91300000.0, 0.361, 864.0), (90600000.0, 
    0.361, 874.0), (90000000.0, 0.361, 884.0), (89300000.0, 0.361, 894.0), 
    (88700000.0, 0.362, 904.0), (88000000.0, 0.362, 914.0), (87300000.0, 
    0.362, 924.0), (86700000.0, 0.362, 934.0), (86000000.0, 0.363, 944.0), 
    (85300000.0, 0.363, 954.0), (84600000.0, 0.363, 964.0), (83900000.0, 
    0.363, 974.0), (83300000.0, 0.364, 984.0), (82600000.0, 0.364, 994.0), 
    (81900000.0, 0.364, 1004.0), (81200000.0, 0.364, 1014.0), (80500000.0, 
    0.364, 1024.0), (79800000.0, 0.365, 1034.0), (79100000.0, 0.365, 
    1044.0), (78400000.0, 0.365, 1054.0), (77700000.0, 0.365, 1064.0), (
    76900000.0, 0.366, 1074.0), (76200000.0, 0.366, 1084.0), (75500000.0, 
    0.366, 1094.0), (74800000.0, 0.366, 1104.0), (74100000.0, 0.367, 
    1114.0), (73300000.0, 0.367, 1124.0), (72600000.0, 0.367, 1134.0), (
    71900000.0, 0.367, 1144.0), (71200000.0, 0.368, 1154.0), (70400000.0, 
    0.368, 1164.0), (69700000.0, 0.368, 1174.0), (69000000.0, 0.368, 
    1184.0), (68300000.0, 0.369, 1194.0), (67500000.0, 0.369, 1204.0), (
    66800000.0, 0.369, 1214.0), (66100000.0, 0.369, 1224.0), (65400000.0, 
    0.37, 1234.0), (64700000.0, 0.37, 1244.0), (64000000.0, 0.37, 1254.0), 
    (63300000.0, 0.37, 1264.0), (62600000.0, 0.37, 1274.0), (61900000.0, 
    0.371, 1284.0), (61200000.0, 0.371, 1294.0), (60500000.0, 0.371, 
    1304.0), (59800000.0, 0.371, 1314.0), (59200000.0, 0.372, 1324.0), (
    58800000.0, 0.372, 1330.0)))
myModel.materials['Copper'].Expansion(table=((1.66e-05, 284.0), (
    1.67e-05, 294.0), (1.69e-05, 304.0), (1.7e-05, 314.0), (1.71e-05, 
    324.0), (1.72e-05, 334.0), (1.73e-05, 344.0), (1.74e-05, 354.0), (
    1.75e-05, 364.0), (1.76e-05, 374.0), (1.77e-05, 384.0), (1.78e-05, 
    394.0), (1.79e-05, 404.0), (1.8e-05, 414.0), (1.8e-05, 424.0), (
    1.81e-05, 434.0), (1.82e-05, 444.0), (1.83e-05, 454.0), (1.83e-05, 
    464.0), (1.84e-05, 474.0), (1.85e-05, 484.0), (1.85e-05, 494.0), (
    1.86e-05, 504.0), (1.87e-05, 514.0), (1.87e-05, 524.0), (1.88e-05, 
    534.0), (1.88e-05, 544.0), (1.89e-05, 554.0), (1.89e-05, 564.0), (
    1.9e-05, 574.0), (1.9e-05, 584.0), (1.91e-05, 594.0), (1.91e-05, 
    604.0), (1.92e-05, 614.0), (1.92e-05, 624.0), (1.92e-05, 634.0), (
    1.93e-05, 644.0), (1.93e-05, 654.0), (1.93e-05, 664.0), (1.94e-05, 
    674.0), (1.94e-05, 684.0), (1.94e-05, 694.0), (1.95e-05, 704.0), (
    1.95e-05, 714.0), (1.95e-05, 724.0), (1.96e-05, 734.0), (1.96e-05, 
    744.0), (1.96e-05, 754.0), (1.97e-05, 764.0), (1.97e-05, 774.0), (
    1.97e-05, 784.0), (1.98e-05, 794.0), (1.98e-05, 800.0)), zero=293.0, 
    temperatureDependency=ON)
myModel.materials['Copper'].InelasticHeatFraction()
myModel.materials['Copper'].Plastic(hardening=JOHNSON_COOK, 
    table=((90000.0, 292000.0, 0.31, 1.09, 1356.0, 293.0), ))
myModel.materials['Copper'].SpecificHeat(table=((384000000.0, ), 
    ))
myModel.Material(name='Steel')
myModel.materials['Steel'].Conductivity(temperatureDependency=ON, 
    table=((13100.0, 284.0), (13300.0, 294.0), (13400.0, 304.0), (13600.0, 
    314.0), (13700.0, 324.0), (13900.0, 334.0), (14000.0, 344.0), (14200.0, 
    354.0), (14300.0, 364.0), (14500.0, 374.0), (14600.0, 384.0), (14800.0, 
    394.0), (14900.0, 404.0), (15100.0, 414.0), (15200.0, 424.0), (15400.0, 
    434.0), (15500.0, 444.0), (15700.0, 454.0), (15800.0, 464.0), (16000.0, 
    474.0), (16100.0, 484.0), (16300.0, 494.0), (16400.0, 504.0), (16500.0, 
    514.0), (16700.0, 524.0), (16800.0, 534.0), (17000.0, 544.0), (17100.0, 
    554.0), (17300.0, 564.0), (17400.0, 574.0), (17500.0, 584.0), (17700.0, 
    594.0), (17800.0, 604.0), (17900.0, 614.0), (18100.0, 624.0), (18200.0, 
    634.0), (18400.0, 644.0), (18500.0, 654.0), (18600.0, 664.0), (18800.0, 
    674.0), (18900.0, 684.0), (19000.0, 694.0), (19100.0, 704.0), (19300.0, 
    714.0), (19400.0, 724.0), (19500.0, 734.0), (19700.0, 744.0), (19800.0, 
    754.0), (19900.0, 764.0), (20000.0, 774.0), (20200.0, 784.0), (20300.0, 
    794.0), (20400.0, 804.0), (20500.0, 814.0), (20700.0, 824.0), (20800.0, 
    834.0), (20900.0, 844.0), (21000.0, 854.0), (21200.0, 864.0), (21300.0, 
    874.0), (21400.0, 884.0), (21500.0, 894.0), (21600.0, 904.0), (21800.0, 
    914.0), (21900.0, 924.0), (22000.0, 934.0), (22100.0, 944.0), (22200.0, 
    954.0), (22300.0, 964.0), (22400.0, 974.0), (22600.0, 984.0), (22700.0, 
    994.0), (22800.0, 1004.0), (22900.0, 1014.0), (23000.0, 1024.0), (
    23100.0, 1034.0), (23200.0, 1044.0), (23300.0, 1054.0), (23400.0, 
    1064.0), (23600.0, 1074.0), (23700.0, 1084.0), (23800.0, 1094.0), (
    23900.0, 1104.0), (24000.0, 1114.0), (24100.0, 1124.0), (24200.0, 
    1134.0), (24300.0, 1144.0), (24400.0, 1154.0), (24500.0, 1164.0), (
    24600.0, 1174.0), (24700.0, 1184.0), (24800.0, 1194.0), (24900.0, 
    1204.0), (25000.0, 1214.0), (25100.0, 1220.0)))
myModel.materials['Steel'].Density(table=((8e-06, ), ))
myModel.materials['Steel'].Elastic(temperatureDependency=ON, 
    table=((194000000.0, 0.294, 295.0), (193000000.0, 0.295, 305.0), (
    192000000.0, 0.296, 315.0), (191000000.0, 0.296, 325.0), (190000000.0, 
    0.297, 335.0), (190000000.0, 0.298, 345.0), (189000000.0, 0.299, 
    355.0), (188000000.0, 0.3, 365.0), (187000000.0, 0.301, 375.0), (
    186000000.0, 0.301, 385.0), (185000000.0, 0.302, 395.0), (184000000.0, 
    0.303, 405.0), (184000000.0, 0.304, 415.0), (183000000.0, 0.305, 
    425.0), (182000000.0, 0.305, 435.0), (181000000.0, 0.306, 445.0), (
    180000000.0, 0.307, 455.0), (179000000.0, 0.308, 465.0), (179000000.0, 
    0.309, 475.0), (178000000.0, 0.309, 485.0), (177000000.0, 0.31, 495.0), 
    (176000000.0, 0.311, 505.0), (175000000.0, 0.312, 515.0), (174000000.0, 
    0.313, 525.0), (174000000.0, 0.313, 535.0), (173000000.0, 0.314, 
    545.0), (172000000.0, 0.315, 555.0), (171000000.0, 0.316, 565.0), (
    170000000.0, 0.317, 575.0), (169000000.0, 0.317, 585.0), (169000000.0, 
    0.318, 595.0), (168000000.0, 0.319, 605.0), (167000000.0, 0.32, 615.0), 
    (166000000.0, 0.321, 625.0), (165000000.0, 0.321, 635.0), (164000000.0, 
    0.322, 645.0), (163000000.0, 0.323, 655.0), (163000000.0, 0.324, 
    665.0), (162000000.0, 0.325, 675.0), (161000000.0, 0.325, 685.0), (
    160000000.0, 0.326, 695.0), (159000000.0, 0.327, 705.0), (158000000.0, 
    0.328, 715.0), (158000000.0, 0.329, 725.0), (157000000.0, 0.329, 
    735.0), (156000000.0, 0.33, 745.0), (155000000.0, 0.331, 755.0), (
    154000000.0, 0.332, 765.0), (153000000.0, 0.333, 775.0), (153000000.0, 
    0.334, 785.0), (152000000.0, 0.334, 795.0), (151000000.0, 0.335, 
    805.0), (150000000.0, 0.336, 815.0), (149000000.0, 0.337, 825.0), (
    148000000.0, 0.338, 835.0), (148000000.0, 0.338, 845.0), (147000000.0, 
    0.339, 855.0), (146000000.0, 0.34, 865.0), (145000000.0, 0.341, 875.0), 
    (144000000.0, 0.342, 885.0), (143000000.0, 0.342, 895.0), (143000000.0, 
    0.343, 905.0), (142000000.0, 0.344, 915.0), (141000000.0, 0.345, 
    925.0), (140000000.0, 0.346, 935.0), (139000000.0, 0.346, 945.0), (
    138000000.0, 0.347, 955.0), (137000000.0, 0.348, 965.0), (137000000.0, 
    0.349, 975.0), (136000000.0, 0.35, 985.0), (135000000.0, 0.35, 995.0), 
    (134000000.0, 0.351, 1005.0), (133000000.0, 0.352, 1015.0), (
    132000000.0, 0.353, 1025.0), (132000000.0, 0.354, 1035.0), (
    131000000.0, 0.354, 1045.0), (130000000.0, 0.355, 1055.0), (
    129000000.0, 0.356, 1065.0), (128000000.0, 0.357, 1075.0), (
    127000000.0, 0.358, 1085.0), (127000000.0, 0.358, 1095.0), (
    126000000.0, 0.359, 1105.0), (125000000.0, 0.36, 1115.0), (124000000.0, 
    0.361, 1125.0), (123000000.0, 0.362, 1135.0), (122000000.0, 0.362, 
    1145.0), (122000000.0, 0.363, 1155.0), (121000000.0, 0.364, 1165.0), (
    120000000.0, 0.365, 1173.0)))
myModel.materials['Steel'].Expansion(table=((1.65e-05, ), ))
myModel.materials['Steel'].Plastic(hardening=JOHNSON_COOK, 
    table=((305000.0, 1161000.0, 0.61, 0.517, 1644.0, 293.0), ))
myModel.materials['Steel'].SpecificHeat(temperatureDependency=ON, 
    table=((480000000.0, 284.0), (486000000.0, 294.0), (491000000.0, 
    304.0), (496000000.0, 314.0), (501000000.0, 324.0), (505000000.0, 
    334.0), (510000000.0, 344.0), (514000000.0, 354.0), (518000000.0, 
    364.0), (522000000.0, 374.0), (525000000.0, 384.0), (529000000.0, 
    394.0), (532000000.0, 404.0), (536000000.0, 414.0), (539000000.0, 
    424.0), (542000000.0, 434.0), (545000000.0, 444.0), (548000000.0, 
    454.0), (551000000.0, 464.0), (554000000.0, 474.0), (556000000.0, 
    484.0), (559000000.0, 494.0), (562000000.0, 504.0), (564000000.0, 
    514.0), (566000000.0, 524.0), (569000000.0, 534.0), (571000000.0, 
    544.0), (573000000.0, 554.0), (575000000.0, 564.0), (577000000.0, 
    574.0), (579000000.0, 584.0), (581000000.0, 594.0), (583000000.0, 
    604.0), (585000000.0, 614.0), (587000000.0, 624.0), (589000000.0, 
    634.0), (590000000.0, 644.0), (592000000.0, 654.0), (594000000.0, 
    664.0), (596000000.0, 674.0), (597000000.0, 684.0), (599000000.0, 
    694.0), (601000000.0, 704.0), (602000000.0, 714.0), (604000000.0, 
    724.0), (605000000.0, 734.0), (607000000.0, 744.0), (609000000.0, 
    754.0), (610000000.0, 764.0), (612000000.0, 774.0), (614000000.0, 
    784.0), (615000000.0, 794.0), (617000000.0, 804.0), (618000000.0, 
    814.0), (620000000.0, 824.0), (622000000.0, 834.0), (623000000.0, 
    844.0), (625000000.0, 854.0), (627000000.0, 864.0), (628000000.0, 
    874.0), (630000000.0, 884.0), (632000000.0, 894.0), (633000000.0, 
    904.0), (635000000.0, 914.0), (637000000.0, 924.0), (639000000.0, 
    934.0), (641000000.0, 944.0), (642000000.0, 954.0), (644000000.0, 
    964.0), (646000000.0, 974.0), (648000000.0, 984.0), (650000000.0, 
    994.0), (652000000.0, 1004.0), (654000000.0, 1014.0), (656000000.0, 
    1024.0), (658000000.0, 1034.0), (660000000.0, 1044.0), (662000000.0, 
    1054.0), (664000000.0, 1064.0), (666000000.0, 1074.0), (668000000.0, 
    1084.0), (670000000.0, 1094.0), (672000000.0, 1104.0), (674000000.0, 
    1114.0), (676000000.0, 1124.0), (678000000.0, 1134.0), (680000000.0, 
    1144.0), (682000000.0, 1154.0), (685000000.0, 1164.0), (687000000.0, 
    1174.0), (689000000.0, 1184.0), (691000000.0, 1194.0), (693000000.0, 
    1204.0), (695000000.0, 1214.0), (697000000.0, 1224.0), (700000000.0, 
    1234.0), (702000000.0, 1244.0), (704000000.0, 1254.0), (706000000.0, 
    1264.0), (708000000.0, 1274.0), (710000000.0, 1284.0), (712000000.0, 
    1294.0), (714000000.0, 1304.0), (716000000.0, 1314.0), (718000000.0, 
    1324.0), (720000000.0, 1334.0), (722000000.0, 1344.0), (724000000.0, 
    1354.0), (726000000.0, 1364.0), (728000000.0, 1374.0), (730000000.0, 
    1384.0), (731000000.0, 1394.0), (733000000.0, 1404.0), (735000000.0, 
    1414.0), (736000000.0, 1424.0), (738000000.0, 1434.0), (739000000.0, 
    1444.0), (740000000.0, 1454.0), (742000000.0, 1464.0), (743000000.0, 
    1474.0), (744000000.0, 1484.0), (745000000.0, 1494.0), (746000000.0, 
    1500.0)))
myModel.Material(name='Al6061')
myModel.materials['Al6061'].Conductivity(
    temperatureDependency=ON, table=((5150.0, 4.0), (20200.0, 14.0), (
    33700.0, 24.0), (45700.0, 34.0), (56300.0, 44.0), (65800.0, 54.0), (
    74200.0, 64.0), (81700.0, 74.0), (88400.0, 84.0), (94400.0, 94.0), (
    99900.0, 104.0), (105000.0, 114.0), (110000.0, 124.0), (114000.0, 
    134.0), (118000.0, 144.0), (122000.0, 154.0), (126000.0, 164.0), (
    129000.0, 174.0), (132000.0, 184.0), (135000.0, 194.0), (137000.0, 
    204.0), (140000.0, 214.0), (142000.0, 224.0), (144000.0, 234.0), (
    146000.0, 244.0), (148000.0, 254.0), (150000.0, 264.0), (152000.0, 
    274.0), (153000.0, 284.0), (155000.0, 294.0), (157000.0, 304.0), (
    158000.0, 314.0), (160000.0, 324.0), (161000.0, 334.0), (163000.0, 
    344.0), (164000.0, 354.0), (166000.0, 364.0), (167000.0, 374.0), (
    168000.0, 384.0), (170000.0, 394.0), (171000.0, 404.0), (172000.0, 
    414.0), (173000.0, 424.0), (174000.0, 434.0), (175000.0, 444.0), (
    176000.0, 454.0), (177000.0, 464.0), (178000.0, 474.0), (179000.0, 
    484.0), (179000.0, 494.0), (180000.0, 504.0), (181000.0, 514.0), (
    181000.0, 524.0), (182000.0, 534.0), (182000.0, 544.0), (182000.0, 
    554.0), (183000.0, 564.0), (183000.0, 574.0), (183000.0, 584.0), (
    183000.0, 594.0), (184000.0, 604.0), (184000.0, 614.0), (184000.0, 
    624.0), (184000.0, 634.0), (183000.0, 644.0), (183000.0, 654.0), (
    183000.0, 664.0), (183000.0, 674.0), (183000.0, 684.0), (182000.0, 
    694.0), (182000.0, 704.0), (181000.0, 714.0), (181000.0, 724.0), (
    180000.0, 734.0), (180000.0, 744.0), (179000.0, 754.0), (178000.0, 
    764.0), (177000.0, 774.0), (176000.0, 784.0), (176000.0, 794.0), (
    175000.0, 804.0), (174000.0, 811.0)))
myModel.materials['Al6061'].Density(table=((2.7e-06, ), ))
myModel.materials['Al6061'].Elastic(temperatureDependency=ON, 
    table=((76600000.0, 0.324, 0.0), (76600000.0, 0.324, 10.0), (
    76600000.0, 0.324, 20.0), (76500000.0, 0.324, 30.0), (76400000.0, 
    0.324, 40.0), (76300000.0, 0.325, 50.0), (76100000.0, 0.325, 60.0), (
    76000000.0, 0.325, 70.0), (75800000.0, 0.325, 80.0), (75500000.0, 
    0.326, 90.0), (75300000.0, 0.326, 100.0), (75100000.0, 0.326, 110.0), (
    74800000.0, 0.326, 120.0), (74500000.0, 0.327, 130.0), (74200000.0, 
    0.327, 140.0), (73900000.0, 0.327, 150.0), (73600000.0, 0.328, 160.0), 
    (73300000.0, 0.328, 170.0), (73000000.0, 0.328, 180.0), (72700000.0, 
    0.329, 190.0), (72300000.0, 0.329, 200.0), (72000000.0, 0.329, 210.0), 
    (71700000.0, 0.33, 220.0), (71300000.0, 0.33, 230.0), (71000000.0, 
    0.33, 240.0), (70600000.0, 0.33, 250.0), (70300000.0, 0.331, 260.0), (
    69900000.0, 0.331, 270.0), (69600000.0, 0.331, 280.0), (69200000.0, 
    0.331, 290.0), (68900000.0, 0.331, 300.0), (68600000.0, 0.332, 310.0), 
    (68200000.0, 0.332, 320.0), (67900000.0, 0.332, 330.0), (67500000.0, 
    0.332, 340.0), (67200000.0, 0.332, 350.0), (66800000.0, 0.332, 360.0), 
    (66500000.0, 0.332, 370.0), (66100000.0, 0.333, 380.0), (65800000.0, 
    0.333, 390.0), (65400000.0, 0.333, 400.0), (65100000.0, 0.333, 410.0), 
    (64700000.0, 0.333, 420.0), (64400000.0, 0.333, 430.0), (64000000.0, 
    0.333, 440.0), (63600000.0, 0.334, 450.0), (63200000.0, 0.334, 460.0), 
    (62800000.0, 0.334, 470.0), (62400000.0, 0.335, 480.0), (62000000.0, 
    0.335, 490.0), (61500000.0, 0.335, 500.0), (61100000.0, 0.336, 510.0), 
    (60600000.0, 0.336, 520.0), (60100000.0, 0.337, 530.0), (59600000.0, 
    0.337, 540.0), (59100000.0, 0.338, 550.0), (58500000.0, 0.339, 560.0), 
    (57900000.0, 0.34, 570.0), (57300000.0, 0.341, 580.0), (56600000.0, 
    0.342, 590.0), (55900000.0, 0.343, 600.0), (55200000.0, 0.345, 610.0), 
    (54400000.0, 0.346, 620.0), (53600000.0, 0.348, 630.0), (52800000.0, 
    0.35, 640.0), (51900000.0, 0.352, 650.0), (50900000.0, 0.354, 660.0), (
    49900000.0, 0.356, 670.0), (48800000.0, 0.359, 680.0), (47700000.0, 
    0.361, 690.0), (46500000.0, 0.364, 700.0), (45300000.0, 0.367, 710.0), 
    (43900000.0, 0.371, 720.0), (42500000.0, 0.375, 730.0), (41000000.0, 
    0.379, 740.0), (39500000.0, 0.383, 750.0), (37800000.0, 0.387, 760.0), 
    (36100000.0, 0.392, 770.0), (35600000.0, 0.394, 773.0)))
myModel.materials['Al6061'].Expansion(table=((1.24e-08, 0.0), (
    2.53e-07, 10.0), (5.05e-07, 20.0), (9.48e-07, 30.0), (1.7e-06, 40.0), (
    2.83e-06, 50.0), (4.34e-06, 60.0), (6.17e-06, 70.0), (8.2e-06, 80.0), (
    1.02e-05, 90.0), (1.18e-05, 100.0), (1.32e-05, 110.0), (1.44e-05, 
    120.0), (1.54e-05, 130.0), (1.62e-05, 140.0), (1.69e-05, 150.0), (
    1.75e-05, 160.0), (1.81e-05, 170.0), (1.86e-05, 180.0), (1.9e-05, 
    190.0), (1.94e-05, 200.0), (1.98e-05, 210.0), (2.01e-05, 220.0), (
    2.05e-05, 230.0), (2.08e-05, 240.0), (2.11e-05, 250.0), (2.14e-05, 
    260.0), (2.17e-05, 270.0), (2.2e-05, 280.0), (2.22e-05, 290.0), (
    2.24e-05, 300.0), (2.26e-05, 310.0), (2.28e-05, 320.0), (2.3e-05, 
    330.0), (2.32e-05, 340.0), (2.34e-05, 350.0), (2.36e-05, 360.0), (
    2.38e-05, 370.0), (2.39e-05, 380.0), (2.41e-05, 390.0), (2.43e-05, 
    400.0), (2.45e-05, 410.0), (2.47e-05, 420.0), (2.49e-05, 430.0), (
    2.5e-05, 440.0), (2.52e-05, 450.0), (2.54e-05, 460.0), (2.56e-05, 
    470.0), (2.57e-05, 480.0), (2.59e-05, 490.0), (2.61e-05, 500.0), (
    2.62e-05, 510.0), (2.64e-05, 520.0), (2.66e-05, 530.0), (2.67e-05, 
    540.0), (2.69e-05, 550.0), (2.7e-05, 560.0), (2.72e-05, 570.0), (
    2.73e-05, 575.0)), temperatureDependency=ON)
myModel.materials['Al6061'].InelasticHeatFraction()
myModel.materials['Al6061'].Plastic(hardening=JOHNSON_COOK, 
    table=((270000.0, 154300.0, 0.239, 1.42, 925.0, 293.0), ))
myModel.materials['Al6061'].SpecificHeat(
    temperatureDependency=ON, table=((218000.0, 4.0), (3210000.0, 14.0), (
    16000000.0, 24.0), (50100000.0, 34.0), (107000000.0, 44.0), (
    179000000.0, 54.0), (254000000.0, 64.0), (327000000.0, 74.0), (
    395000000.0, 84.0), (458000000.0, 94.0), (514000000.0, 104.0), (
    565000000.0, 114.0), (612000000.0, 124.0), (654000000.0, 134.0), (
    692000000.0, 144.0), (724000000.0, 154.0), (754000000.0, 164.0), (
    783000000.0, 174.0), (809000000.0, 184.0), (834000000.0, 194.0), (
    858000000.0, 204.0), (880000000.0, 214.0), (901000000.0, 224.0), (
    921000000.0, 234.0), (939000000.0, 244.0), (956000000.0, 254.0), (
    972000000.0, 264.0), (988000000.0, 274.0), (1000000000.0, 284.0), (
    1010000000.0, 294.0), (1030000000.0, 304.0), (1040000000.0, 314.0), (
    1050000000.0, 324.0), (1060000000.0, 334.0), (1070000000.0, 344.0), (
    1080000000.0, 354.0), (1090000000.0, 364.0), (1090000000.0, 374.0), (
    1100000000.0, 384.0), (1110000000.0, 394.0), (1110000000.0, 404.0), (
    1120000000.0, 414.0), (1130000000.0, 424.0), (1130000000.0, 434.0), (
    1140000000.0, 444.0), (1140000000.0, 454.0), (1150000000.0, 464.0), (
    1150000000.0, 474.0), (1160000000.0, 484.0), (1160000000.0, 494.0), (
    1160000000.0, 504.0), (1170000000.0, 514.0), (1170000000.0, 524.0), (
    1180000000.0, 534.0), (1180000000.0, 544.0), (1190000000.0, 554.0), (
    1190000000.0, 564.0), (1190000000.0, 574.0), (1200000000.0, 584.0), (
    1200000000.0, 594.0), (1210000000.0, 604.0), (1210000000.0, 614.0), (
    1220000000.0, 624.0), (1220000000.0, 634.0), (1230000000.0, 644.0), (
    1230000000.0, 654.0), (1230000000.0, 664.0), (1240000000.0, 674.0), (
    1250000000.0, 684.0), (1250000000.0, 694.0), (1260000000.0, 704.0), (
    1260000000.0, 714.0), (1270000000.0, 724.0), (1270000000.0, 734.0), (
    1280000000.0, 744.0), (1280000000.0, 754.0), (1290000000.0, 764.0), (
    1290000000.0, 774.0), (1300000000.0, 784.0), (1300000000.0, 794.0), (
    1310000000.0, 804.0), (1310000000.0, 811.0)))
# Create sections
myModel.HomogeneousSolidSection(name='Deposit', 
    material=depMatl, thickness=None)
myModel.HomogeneousSolidSection(name='Substrate', 
    material=subsMatl, thickness=None)
myModel.HomogeneousSolidSection(name='Base', 
    material=BaseMatl, thickness=None)
  

# Assign Sections
myPart = myModel.parts['BasewithDep']

# Define the bounding box coordinates (xMin, yMin, zMin, xMax, yMax, zMax)
xMin, yMin, zMin = -baseWidth, 0, 0  
xMax, yMax, zMax = baseWidth, baseThick, baseLength    

# Select cells within the bounding box
selected_cells = myPart.cells.getByBoundingBox(xMin, yMin, zMin, xMax, yMax, zMax)

# Create a region from the selected cells directly in the SectionAssignment
myPart.SectionAssignment(region=(selected_cells,), sectionName='Base', 
                         offset=0.0, offsetType=MIDDLE_SURFACE, 
                         offsetField='', thicknessAssignment=FROM_SECTION)

    
    


# Define the bounding box coordinates (xMin, yMin, zMin, xMax, yMax, zMax)
xMin, yMin, zMin = -baseWidth, baseThick, 0  
xMax, yMax, zMax = baseWidth, baseThick+dep2Thick, baseLength    

# Select cells within the bounding box
selected_cells = myPart.cells.getByBoundingBox(xMin, yMin, zMin, xMax, yMax, zMax)

# Create a region from the selected cells directly in the SectionAssignment
myPart.SectionAssignment(region=(selected_cells,), sectionName='Deposit', 
                         offset=0.0, offsetType=MIDDLE_SURFACE, 
                         offsetField='', thicknessAssignment=FROM_SECTION)

# Assign Sections
myPart = myModel.parts['SubwithDep']

# Define the bounding box coordinates (xMin, yMin, zMin, xMax, yMax, zMax)
xMin, yMin, zMin = -baseWidth, baseThick, 0  
xMax, yMax, zMax = baseWidth, baseThick+subsThick, baseLength    

# Select cells within the bounding box
selected_cells = myPart.cells.getByBoundingBox(xMin, yMin, zMin, xMax, yMax, zMax)

# Create a region from the selected cells directly in the SectionAssignment
myPart.SectionAssignment(region=(selected_cells,), sectionName='Substrate', 
                         offset=0.0, offsetType=MIDDLE_SURFACE, 
                         offsetField='', thicknessAssignment=FROM_SECTION)

    
    


# Define the bounding box coordinates (xMin, yMin, zMin, xMax, yMax, zMax)
xMin, yMin, zMin = -baseWidth, baseThick+subsThick, 0  
xMax, yMax, zMax = baseWidth, baseThick+subsThick+dep2Thick, baseLength    

# Select cells within the bounding box
selected_cells = myPart.cells.getByBoundingBox(xMin, yMin, zMin, xMax, yMax, zMax)

# Create a region from the selected cells directly in the SectionAssignment
myPart.SectionAssignment(region=(selected_cells,), sectionName='Deposit', 
                         offset=0.0, offsetType=MIDDLE_SURFACE, 
                         offsetField='', thicknessAssignment=FROM_SECTION)
  
#Mesh Seeding - 
#Horizontal

myPart=myModel.parts['SubwithDep']

#General Seeding
myPart.seedPart(deviationFactor=0.1, minSizeFactor=0.1, size=UnitDepLength)

# Define the coordinates of the bounding box (xMin, yMin, zMin, xMax, yMax, zMax)
xMin, yMin, zMin = -1.01*dep2Width/2, 0.99*(baseThick+subsThick), 0
xMax, yMax, zMax = 1.01*dep2Width/2, 1.01*(baseThick+subsThick+dep2Thick), baseLength

# Select edges within the bounding box
selected_edges = myPart.edges.getByBoundingBox(xMin, yMin, zMin, xMax, yMax, zMax)

# Use the selected edges in the seedEdgeBySize method
myPart.seedEdgeBySize(constraint=FINER, deviationFactor=0.1, edges=selected_edges, size=UnitDepLength)


for i in range(int(NumPartition)+1):
    myPart.seedEdgeBySize(constraint=FINER, deviationFactor=0.1, edges=
        myPart.edges.findAt(
        ((0, baseThick+subsThick+depTrkThick*i, baseLength-(baseLength-subsLength)/2), ), 
        ), minSizeFactor=0.1, size=minSize1)

for i in range(int(NumPartition)+1):
    myPart.seedEdgeBySize(constraint=FINER, deviationFactor=0.1, edges=
        myPart.edges.findAt(
        ((0, baseThick+subsThick+depTrkThick*i, (baseLength-subsLength)/2), ), 
        ), minSizeFactor=0.1, size=minSize1)



myPart.seedEdgeByBias(biasMethod=SINGLE, 
    constraint=FINER, end1Edges=myPart.edges.findAt(((0.5*dep2Width+0.5*(subsWidth-dep2Width)*0.1, baseThick+subsThick, dep1Length+subsLength), )), 
    maxSize=maxSize1, minSize=minSize1)
     
myPart.seedEdgeByBias(biasMethod=SINGLE, 
    constraint=FINER, end2Edges= myPart.edges.findAt(((0.5*dep2Width+0.5*(subsWidth-dep2Width)*0.1, baseThick, dep1Length+subsLength), 
    )), maxSize=maxSize1, minSize=minSize1)
      
myPart.seedEdgeByBias(biasMethod=SINGLE, 
    constraint=FINER, end1Edges=myPart.edges.findAt(((0.5*dep2Width+0.5*(subsWidth-dep2Width)*0.1, baseThick+subsThick, dep1Length), )), 
    maxSize=maxSize1, minSize=minSize1)
    
myPart.seedEdgeByBias(biasMethod=SINGLE, 
    constraint=FINER, end2Edges=myPart.edges.findAt(((0.5*dep2Width+0.5*(subsWidth-dep2Width)*0.1, baseThick, dep1Length), )), 
    maxSize=maxSize1, minSize=minSize1)
    

    
myPart.seedEdgeByBias(biasMethod=SINGLE, 
    constraint=FINER, end2Edges=myPart.edges.findAt(((-(0.5*dep2Width+0.5*(subsWidth-dep2Width)*0.1), baseThick+subsThick, dep1Length+subsLength), )), 
    maxSize=maxSize1, minSize=minSize1)
    
myPart.seedEdgeByBias(biasMethod=SINGLE, 
    constraint=FINER, end1Edges= myPart.edges.findAt(((-(0.5*dep2Width+0.5*(subsWidth-dep2Width)*0.1), baseThick, dep1Length+subsLength), 
    )), maxSize=maxSize1, minSize=minSize1)
    
myPart.seedEdgeByBias(biasMethod=SINGLE, 
    constraint=FINER, end2Edges=myPart.edges.findAt(((-(0.5*dep2Width+0.5*(subsWidth-dep2Width)*0.1), baseThick+subsThick, dep1Length), )), 
    maxSize=maxSize1, minSize=minSize1)
  
myPart.seedEdgeByBias(biasMethod=SINGLE, 
    constraint=FINER, end1Edges= myPart.edges.findAt(((-(0.5*dep2Width+0.5*(subsWidth-dep2Width)*0.1), baseThick, dep1Length), 
    )), maxSize=maxSize1, minSize=minSize1)


#Vertical
myPart.seedEdgeByBias(biasMethod=SINGLE, 
    constraint=FINER, end1Edges=myPart.edges.findAt(((dep2Width/2, baseThick+0.9*subsThick, dep1Length+subsLength), )), 
    maxSize=maxSize2, minSize=minSize1)
    
myPart.seedEdgeByBias(biasMethod=SINGLE, 
    constraint=FINER, end2Edges=myPart.edges.findAt(((dep2Width/2, baseThick+0.9*subsThick, dep1Length), )), 
    maxSize=maxSize2, minSize=minSize1)
    
    
myPart.seedEdgeByBias(biasMethod=SINGLE, 
    constraint=FINER, end1Edges=myPart.edges.findAt(((subsWidth/2, baseThick+0.9*subsThick, dep1Length+subsLength), )), 
    maxSize=maxSize2, minSize=minSize1)
    
myPart.seedEdgeByBias(biasMethod=SINGLE, 
    constraint=FINER, end1Edges=myPart.edges.findAt(((subsWidth/2, baseThick+0.9*subsThick, dep1Length), )), 
    maxSize=maxSize2, minSize=minSize1)
    


myPart.seedEdgeByBias(biasMethod=SINGLE, 
    constraint=FINER, end1Edges=myPart.edges.findAt(((-dep2Width/2, baseThick+0.9*subsThick, dep1Length+subsLength), )), 
    maxSize=maxSize2, minSize=minSize1)
    
myPart.seedEdgeByBias(biasMethod=SINGLE, 
    constraint=FINER, end2Edges=myPart.edges.findAt(((-dep2Width/2, baseThick+0.9*subsThick, dep1Length), )), 
    maxSize=maxSize2, minSize=minSize1)
       
myPart.seedEdgeByBias(biasMethod=SINGLE, 
    constraint=FINER, end2Edges=myPart.edges.findAt(((-subsWidth/2, baseThick+0.9*subsThick, dep1Length+subsLength), )), 
    maxSize=maxSize2, minSize=minSize1)
    
myPart.seedEdgeByBias(biasMethod=SINGLE, 
    constraint=FINER, end2Edges=myPart.edges.findAt(((-subsWidth/2, baseThick+0.9*subsThick, dep1Length), )), 
    maxSize=maxSize2, minSize=minSize1)
    
    
    
myPart.seedEdgeByBias(biasMethod=SINGLE, 
    constraint=FINER, end2Edges=myPart.edges.findAt(((-subsWidth/2+clampWidthXminus, baseThick+0.9*subsThick, dep1Length), )), 
    maxSize=maxSize2, minSize=minSize1)
    
myPart.seedEdgeByBias(biasMethod=SINGLE, 
    constraint=FINER, end1Edges=myPart.edges.findAt(((-subsWidth/2+clampWidthXminus, baseThick+0.9*subsThick, dep1Length+subsLength), )), 
    maxSize=maxSize2, minSize=minSize1)
    
    
myPart.seedEdgeByBias(biasMethod=SINGLE, 
    constraint=FINER, end2Edges=myPart.edges.findAt(((subsWidth/2-clampWidthXplus, baseThick+0.9*subsThick, dep1Length), )), 
    maxSize=maxSize2, minSize=minSize1)
    
myPart.seedEdgeByBias(biasMethod=SINGLE, 
    constraint=FINER, end1Edges=myPart.edges.findAt(((subsWidth/2-clampWidthXplus, baseThick+0.9*subsThick, dep1Length+subsLength), )), 
    maxSize=maxSize2, minSize=minSize1)
    
    
myPart.seedEdgeBySize(constraint=FINER, 
    deviationFactor=0.1, edges=myPart.edges.findAt(
    ((subsWidth/2-clampWidthXplus/2, baseThick+subsThick, dep1Length), ), 
    ((subsWidth/2-clampWidthXplus/2, baseThick, dep1Length), ), 
    ((subsWidth/2-clampWidthXplus/2, baseThick+subsThick, dep1Length+subsLength), ), 
    ((subsWidth/2-clampWidthXplus/2, baseThick, dep1Length+subsLength), ), 
    ), minSizeFactor=0.1, size=maxSize1)   
    
myPart.seedEdgeBySize(constraint=FINER, 
    deviationFactor=0.1, edges=myPart.edges.findAt(
    ((-subsWidth/2+clampWidthXplus/2, baseThick+subsThick, dep1Length), ), 
    ((-subsWidth/2+clampWidthXplus/2, baseThick, dep1Length), ), 
    ((-subsWidth/2+clampWidthXplus/2, baseThick+subsThick, dep1Length+subsLength), ), 
    ((-subsWidth/2+clampWidthXplus/2, baseThick, dep1Length+subsLength), ), 
    ), minSizeFactor=0.1, size=maxSize1)       
    
    #
    
    
    
    
    

    
#Mesh Seeding - 
#BasewithDep
myPart=myModel.parts['BasewithDep']
#General Seeding
myPart.seedPart(deviationFactor=0.1, minSizeFactor=0.1, size=UnitDepLengthBase)
# Define the coordinates of the bounding box (xMin, yMin, zMin, xMax, yMax, zMax)
xMin, yMin, zMin = -dep2Width/2, -baseThick, dep1Length
xMax, yMax, zMax = dep2Width/2, baseThick, dep1Length+subsLength

# Select edges within the bounding box
selected_edges = myPart.edges.getByBoundingBox(xMin, yMin, zMin, xMax, yMax, zMax)

# Use the selected edges in the seedEdgeBySize method
myPart.seedEdgeBySize(constraint=FINER, deviationFactor=0.1, edges=selected_edges, size=UnitDepLengthBase)


# +X Direction
myPart.seedEdgeByBias(biasMethod=SINGLE, 
    constraint=FINER, end1Edges= myPart.edges.findAt(((dep1Width/2+(baseWidth-dep1Width)*0.5*0.1, baseThick, 0.0), )), maxSize=maxSize1, minSize=minSize1)
        
myPart.seedEdgeByBias(biasMethod=SINGLE, 
    constraint=FINER, end2Edges= myPart.edges.findAt(((dep1Width/2+(baseWidth-dep1Width)*0.5*0.1, 0, 0.0), )), maxSize=maxSize1, minSize=minSize1)
    
myPart.seedEdgeByBias(biasMethod=SINGLE, 
    constraint=FINER, end2Edges= myPart.edges.findAt(((dep1Width/2+(baseWidth-dep1Width)*0.5*0.1, baseThick, dep1Length), )), maxSize=maxSize1, minSize=minSize1)
    
myPart.seedEdgeByBias(biasMethod=SINGLE, 
    constraint=FINER, end1Edges= myPart.edges.findAt(((dep1Width/2+(baseWidth-dep1Width)*0.5*0.1, 0, dep1Length), )), maxSize=maxSize1, minSize=minSize1)
    
myPart.seedEdgeByBias(biasMethod=SINGLE, 
    constraint=FINER, end2Edges= myPart.edges.findAt(((dep1Width/2+(baseWidth-dep1Width)*0.5*0.1, baseThick, dep1Length+dep2Length), )), maxSize=maxSize1, minSize=minSize1)
    
myPart.seedEdgeByBias(biasMethod=SINGLE, 
    constraint=FINER, end1Edges= myPart.edges.findAt(((dep1Width/2+(baseWidth-dep1Width)*0.5*0.1, 0, dep1Length+dep2Length), )), maxSize=maxSize1, minSize=minSize1)
    
myPart.seedEdgeByBias(biasMethod=SINGLE, 
    constraint=FINER, end1Edges= myPart.edges.findAt(((dep1Width/2+(baseWidth-dep1Width)*0.5*0.1, baseThick, baseLength), )), maxSize=maxSize1, minSize=minSize1)
    
myPart.seedEdgeByBias(biasMethod=SINGLE, 
    constraint=FINER, end2Edges= myPart.edges.findAt(((dep1Width/2+(baseWidth-dep1Width)*0.5*0.1, 0, baseLength), )), maxSize=maxSize1, minSize=minSize1)
        
        




# -X Direction
myPart.seedEdgeByBias(biasMethod=SINGLE, 
    constraint=FINER, end2Edges= myPart.edges.findAt(((-(dep1Width/2+(baseWidth-dep1Width)*0.5*0.1), baseThick, 0.0), )), maxSize=maxSize1, minSize=minSize1)
    
myPart.seedEdgeByBias(biasMethod=SINGLE, 
    constraint=FINER, end1Edges= myPart.edges.findAt(((-(dep1Width/2+(baseWidth-dep1Width)*0.5*0.1), 0, 0.0), )), maxSize=maxSize1, minSize=minSize1)
    
myPart.seedEdgeByBias(biasMethod=SINGLE, 
    constraint=FINER, end1Edges= myPart.edges.findAt(((-(dep1Width/2+(baseWidth-dep1Width)*0.5*0.1), baseThick, dep1Length), )), maxSize=maxSize1, minSize=minSize1)
    
myPart.seedEdgeByBias(biasMethod=SINGLE, 
    constraint=FINER, end2Edges= myPart.edges.findAt(((-(dep1Width/2+(baseWidth-dep1Width)*0.5*0.1), 0, dep1Length), )), maxSize=maxSize1, minSize=minSize1)
    
myPart.seedEdgeByBias(biasMethod=SINGLE, 
    constraint=FINER, end1Edges= myPart.edges.findAt(((-(dep1Width/2+(baseWidth-dep1Width)*0.5*0.1), baseThick, dep1Length+dep2Length), )), maxSize=maxSize1, minSize=minSize1)
    
myPart.seedEdgeByBias(biasMethod=SINGLE, 
    constraint=FINER, end2Edges= myPart.edges.findAt(((-(dep1Width/2+(baseWidth-dep1Width)*0.5*0.1), 0, dep1Length+dep2Length), )), maxSize=maxSize1, minSize=minSize1)
    
myPart.seedEdgeByBias(biasMethod=SINGLE, 
    constraint=FINER, end2Edges= myPart.edges.findAt(((-(dep1Width/2+(baseWidth-dep1Width)*0.5*0.1), baseThick, baseLength), )), maxSize=maxSize1, minSize=minSize1)
    
myPart.seedEdgeByBias(biasMethod=SINGLE, 
    constraint=FINER, end1Edges= myPart.edges.findAt(((-(dep1Width/2+(baseWidth-dep1Width)*0.5*0.1), 0, baseLength), )), maxSize=maxSize1, minSize=minSize1)
    
    
      







# Reference to the part

myPart=myModel.parts['BasewithDep']
# Function to generate edge selection for a given y value
def find_edge1s_for_layer(y_value):
    coordinates = [(dep2Width/2, y_value, dep1Length/2), (-dep2Width/2, y_value, baseLength-dep3Length/2)]
    edges = myPart.edges.findAt(*[(coord,) for coord in coordinates])
    return edges
      
def find_edge2s_for_layer(y_value):
    coordinates = [(-dep2Width/2, y_value, dep1Length/2), (dep2Width/2, y_value, baseLength-dep3Length/2)]
    edges = myPart.edges.findAt(*[(coord,) for coord in coordinates])
    return edges

# Using loops to generate edge selections for each layer
end1_edges = []
end2_edges = []

for i in range(1, int(NumPartition)):
    Addthickness        = PartitionThick*i
    y_value             = baseThick + Addthickness
    end1_edges.extend(find_edge1s_for_layer(y_value))
    # Assume end2Edges need similar logic or adjust as necessary
    end2_edges.extend(find_edge2s_for_layer(y_value))  # Adjust based on your model
    
    

        
    

# Seed edges by bias - using the dynamically generated edge lists
myPart.seedEdgeByBias(biasMethod=SINGLE, constraint=FINER, end1Edges=end1_edges,
                    end2Edges=end2_edges, maxSize=maxSize3, minSize=depTrkWidth)




for i in range(int(NumPartition)+1):
    myPart.seedEdgeBySize(constraint=FINER, deviationFactor=0.1, edges=
        myPart.edges.findAt(
        ((0, baseThick+depTrkThick*i, baseLength), ), 
        ), minSizeFactor=0.1, size=minSize1)

for i in range(int(NumPartition)+1):
    myPart.seedEdgeBySize(constraint=FINER, deviationFactor=0.1, edges=
        myPart.edges.findAt(
        ((0, baseThick+depTrkThick*i, 0), ), 
        ), minSizeFactor=0.1, size=minSize1)

for i in range(int(NumPartition)+1):
    myPart.seedEdgeBySize(constraint=FINER, deviationFactor=0.1, edges=
        myPart.edges.findAt(
        ((0, baseThick+depTrkThick*i, dep1Length), ), 
        ), minSizeFactor=0.1, size=minSize1)


for i in range(int(NumPartition)+1):
    myPart.seedEdgeBySize(constraint=FINER, deviationFactor=0.1, edges=
        myPart.edges.findAt(
        ((0, baseThick+depTrkThick*i, baseLength-dep1Length), ), 
        ), minSizeFactor=0.1, size=minSize1)




for i in range(1, int(NumPartition)):
    myPart.seedEdgeByBias(biasMethod=SINGLE, 
        constraint=FINER, end2Edges= myPart.edges.findAt(
        ((dep1Width/2, baseThick+depTrkThick*i, baseLength-dep1Length/2), )), 
        maxSize=maxSize3, minSize=UnitDepLength)
    
for i in range(1, int(NumPartition)):
    myPart.seedEdgeByBias(biasMethod=SINGLE, 
        constraint=FINER, end1Edges= myPart.edges.findAt(
        ((-dep1Width/2, baseThick+depTrkThick*i, baseLength-dep1Length/2), )), 
        maxSize=maxSize3, minSize=UnitDepLength)    


for i in range(1, int(NumPartition)):
    myPart.seedEdgeByBias(biasMethod=SINGLE, 
        constraint=FINER, end1Edges= myPart.edges.findAt(
        ((dep1Width/2, baseThick+depTrkThick*i, dep1Length/2), )), 
        maxSize=maxSize3, minSize=UnitDepLength)
    
for i in range(1, int(NumPartition)):
    myPart.seedEdgeByBias(biasMethod=SINGLE, 
        constraint=FINER, end2Edges= myPart.edges.findAt(
        ((-dep1Width/2, baseThick+depTrkThick*i, dep1Length/2), )), 
        maxSize=maxSize3, minSize=UnitDepLength) 


myPart.seedEdgeByBias(biasMethod=SINGLE, 
    constraint=FINER, end1Edges=
    myPart.edges.findAt(
    ((dep2Width/2, baseThick+dep1Thick, baseLength-dep3Length/2), ), 
    ((-dep2Width/2, baseThick+dep1Thick, baseLength-dep3Length/2), ), 
    ((dep2Width/2, 0.0, dep1Length/2), ), 
    ((dep2Width/2, baseThick, baseLength-dep3Length/2), ), 
    ((-dep2Width/2, baseThick, dep1Length/2), ), 
    ((-dep2Width/2, 0.0, dep1Length/2), ), 
    ((- subsWidth/2 , baseThick, baseLength-dep3Length/2), ), 
    (( subsWidth/2 , baseThick, baseLength-dep3Length/2), ), 
    (( subsWidth/2 , 0, dep1Length/2), ), 
    ((- subsWidth/2 , 0, dep1Length/2), ), 
    ((-baseWidth/2, baseThick, baseLength-dep3Length/2), ), 
    ((-baseWidth/2, 0.0, baseLength-dep3Length/2), ), 
    ((baseWidth/2, baseThick, baseLength-dep3Length/2), ), 
    ((baseWidth/2, 0.0, baseLength-dep3Length/2), ), ), 
    end2Edges=myPart.edges.findAt(
    ((dep2Width/2, baseThick+dep1Thick, dep1Length/2), ), 
    ((-dep2Width/2, baseThick+dep1Thick, dep1Length/2), ), 
    ((dep2Width/2, baseThick, dep1Length/2), ), 
    ((dep2Width/2, 0.0, baseLength-dep3Length/2), ), 
    ((-dep2Width/2, baseThick, baseLength-dep3Length/2), ), 
    ((-dep2Width/2, 0.0, baseLength-dep3Length/2), ), 
    ((-baseWidth/2, baseThick, dep1Length/2), ), 
    ((- subsWidth/2 , baseThick, dep1Length/2), ), 
    (( subsWidth/2 , baseThick, dep1Length/2), ), 
    (( subsWidth/2 , 0, baseLength-dep3Length/2), ), 
    ((- subsWidth/2 , 0, baseLength-dep3Length/2), ), 
    ((-baseWidth/2, 0.0, dep1Length/2), ), 
    ((baseWidth/2, baseThick, dep1Length/2), ), 
    ((baseWidth/2, 0.0, dep1Length/2), ), ), 
    maxSize=maxSize3, minSize=UnitDepLength)


myPart.seedEdgeByBias(biasMethod=SINGLE, 
    constraint=FINER, end1Edges=
    myPart.edges.findAt(
    ((-subsWidth/2, baseThick/2,  baseLength), ), 
    ((-dep2Width/2, baseThick/2, baseLength), ), 
    ((subsWidth/2, baseThick/2, baseLength), ), 
    ((baseWidth/2, baseThick/2, baseLength), ), 
    ((dep2Width/2, baseThick/2, baseLength), ), ), 
    end2Edges=
    myPart.edges.findAt(
    ((-baseWidth/2, baseThick/2, baseLength), )), 
    maxSize=2.0, minSize=0.5)
 
myPart.seedEdgeByBias(biasMethod=SINGLE, 
    constraint=FINER, end2Edges=
    myPart.edges.findAt(
    ((-subsWidth/2, baseThick/2,  0), ), 
    ((-dep2Width/2, baseThick/2, 0), ), 
    ((subsWidth/2, baseThick/2, 0), ), 
    ((-baseWidth/2, baseThick/2, 0), ), 
    ((dep2Width/2, baseThick/2, 0), ), ), 
    end1Edges=
    myPart.edges.findAt(
    ((baseWidth/2, baseThick/2, 0), )), 
    maxSize=2.0, minSize=0.5) 
    
myPart.seedEdgeByBias(biasMethod=SINGLE, 
    constraint=FINER, end1Edges=
    myPart.edges.findAt(
    ((-subsWidth/2, baseThick/2,  dep1Length), ), 
    ((subsWidth/2, baseThick/2, dep1Length), ), 
    ((-baseWidth/2, baseThick/2, dep1Length), ), 
    ), end2Edges=
    myPart.edges.findAt(
    ((baseWidth/2, baseThick/2, dep1Length), ),
    ((-dep2Width/2, baseThick/2, dep1Length), ), 
    ((dep2Width/2, baseThick/2, dep1Length), ), 
    ), maxSize=2.0, minSize=0.5)      
    
myPart.seedEdgeByBias(biasMethod=SINGLE, 
    constraint=FINER, end1Edges=
    myPart.edges.findAt(
    ((-subsWidth/2, baseThick/2,  baseLength-dep1Length), ), 
    ((subsWidth/2, baseThick/2, baseLength-dep1Length), ), 
    ((-baseWidth/2, baseThick/2, baseLength-dep1Length), ), 
    ), end2Edges=
    myPart.edges.findAt(
    ((baseWidth/2, baseThick/2, baseLength-dep1Length), ),
    ((-dep2Width/2, baseThick/2, baseLength-dep1Length), ), 
    ((dep2Width/2, baseThick/2, baseLength-dep1Length), ), 
    ), maxSize=2.0, minSize=0.5)  
    
#Element Type Assignment
myPart=myModel.parts['BasewithDep']
# Define the bounding box coordinates (xMin, yMin, zMin, xMax, yMax, zMax)
xMin, yMin, zMin = -baseWidth, 0, 0  # Adjust these values as per your model
xMax, yMax, zMax = baseWidth, baseThick+subsThick+dep2Thick, 2*baseLength     # Adjust these values as per your model

# Select cells within the bounding box
selected_cells = myPart.cells.getByBoundingBox(xMin, yMin, zMin, xMax, yMax, zMax)


# Define a reference region coordinate that is within the part
reference_point = (0, baseThick, baseLength/2)  # Ensure this point is valid within the part

# Find the face at the reference point
reference_face = myPart.faces.findAt(reference_point)


myPart.assignStackDirection(cells=selected_cells, referenceRegion=reference_face)

# Define element types (adjust these as per your requirements)
elemType1 = mesh.ElemType(elemCode=DC3D8, elemLibrary=STANDARD)
elemType2 = mesh.ElemType(elemCode=DC3D6, elemLibrary=STANDARD)
elemType3 = mesh.ElemType(elemCode=DC3D4, elemLibrary=STANDARD)

# Assign element types to the selected cells
myPart.setElementType(regions=(selected_cells,), elemTypes=(elemType1, elemType2, elemType3))



myPart.generateMesh()

#Element Type Assignment
myPart=myModel.parts['SubwithDep']
# Define the bounding box coordinates (xMin, yMin, zMin, xMax, yMax, zMax)
xMin, yMin, zMin = -baseWidth, 0, 0  # Adjust these values as per your model
xMax, yMax, zMax = baseWidth, baseThick+subsThick+dep2Thick, 2*baseLength     # Adjust these values as per your model

# Select cells within the bounding box
selected_cells = myPart.cells.getByBoundingBox(xMin, yMin, zMin, xMax, yMax, zMax)

# Define element types (adjust these as per your requirements)
elemType1 = mesh.ElemType(elemCode=DC3D8, elemLibrary=STANDARD)
elemType2 = mesh.ElemType(elemCode=DC3D6, elemLibrary=STANDARD)
elemType3 = mesh.ElemType(elemCode=DC3D4, elemLibrary=STANDARD)

# Assign element types to the selected cells
myPart.setElementType(regions=(selected_cells,), elemTypes=(elemType1, elemType2, elemType3))                      

myPart.generateMesh()


##Surfaces

#Z-Direction
myAssembly=myModel.rootAssembly

    
myAssembly.Surface(name='SubZplus', side1Faces=myAssembly.instances['SubwithDep-1'].faces.findAt(
    ((0, baseThick+subsThick/2, dep1Length+subsLength), ),  
    ((dep2Width/2+(subsWidth-dep2Width-2*clampWidthXplus)/4, baseThick+subsThick/2, dep1Length+subsLength), ),   
    ((-dep2Width/2-(subsWidth-dep2Width-2*clampWidthXplus)/4, baseThick+subsThick/2, dep1Length+subsLength), ),    
    ((subsWidth/2-clampWidthXplus/2, baseThick+subsThick/2, dep1Length+subsLength), ),    
    ((-subsWidth/2+clampWidthXplus/2, baseThick+subsThick/2, dep1Length+subsLength), ),       
    ))    

   
myAssembly.Surface(name='SubZminus', side1Faces=myAssembly.instances['SubwithDep-1'].faces.findAt((
    (-(dep2Width/2+(subsWidth-dep2Width)/4), baseThick+subsThick/2, dep1Length), ),
    ((dep2Width/2+(subsWidth/2-dep1Width/2-clampWidthXplus/2)/2, baseThick+subsThick/2, dep1Length), ),
    ((-(dep2Width/2+(subsWidth/2-dep1Width/2-clampWidthXplus/2)/2), baseThick+subsThick/2, dep1Length), ),
    (((dep2Width/2+(subsWidth-dep2Width)/4), baseThick+subsThick/2, dep1Length), ), ))
   
myAssembly.Surface(name='SubZminus', side1Faces=myAssembly.instances['SubwithDep-1'].faces.findAt(
    ((0, baseThick+subsThick/2, dep1Length), ),  
    ((dep2Width/2+(subsWidth-dep2Width-2*clampWidthXplus)/4, baseThick+subsThick/2, dep1Length), ),   
    ((-dep2Width/2-(subsWidth-dep2Width-2*clampWidthXplus)/4, baseThick+subsThick/2, dep1Length), ),    
    ((subsWidth/2-clampWidthXplus/2, baseThick+subsThick/2, dep1Length), ),    
    ((-subsWidth/2+clampWidthXplus/2, baseThick+subsThick/2, dep1Length), ),       
    ))      
#X-Direction   
myAssembly.Surface(name='SubXplus', side1Faces=
    myAssembly.instances['SubwithDep-1'].faces.findAt((
    (subsWidth/2, baseThick+subsThick/2, dep1Length+subsLength/2), ), ))
    
myAssembly.Surface(name='SubXminus', side1Faces=
    myAssembly.instances['SubwithDep-1'].faces.findAt((
    (-subsWidth/2, baseThick+subsThick/2, dep1Length+subsLength/2), ), ))




myAssembly.SurfaceByBoolean(name='SubstrateSides', surfaces=(
    myAssembly.surfaces['SubZminus'], 
    myAssembly.surfaces['SubZplus'], 
    myAssembly.surfaces['SubXplus'], 
    myAssembly.surfaces['SubXminus']))



#Y-Direction    

  
myAssembly.Surface(name='SubYplus_woClamp', side1Faces=myAssembly.instances['SubwithDep-1'].faces.findAt(
    ((0, baseThick+subsThick, dep1Length+subsLength/2), ),  
    ((dep2Width/2+(subsWidth-dep2Width-2*clampWidthXplus)/4, baseThick+subsThick, dep1Length+subsLength/2), ),   
    ((-dep2Width/2-(subsWidth-dep2Width-2*clampWidthXplus)/4, baseThick+subsThick, dep1Length+subsLength/2), ),          
    ))

myAssembly.Surface(name='SubYplus_wClamp', side1Faces=myAssembly.instances['SubwithDep-1'].faces.findAt(
    ((0, baseThick+subsThick, dep1Length+subsLength/2), ),  
    ((dep2Width/2+(subsWidth-dep2Width-2*clampWidthXplus)/4, baseThick+subsThick, dep1Length+subsLength/2), ),   
    ((-dep2Width/2-(subsWidth-dep2Width-2*clampWidthXplus)/4, baseThick+subsThick, dep1Length+subsLength/2), ),    
    ((subsWidth/2-clampWidthXplus/2, baseThick+subsThick, dep1Length+subsLength/2), ),    
    ((-subsWidth/2+clampWidthXplus/2, baseThick+subsThick, dep1Length+subsLength/2), ),       
    ))


myAssembly.Surface(name='ClampYplus', side1Faces=myAssembly.instances['SubwithDep-1'].faces.findAt(  
    ((subsWidth/2-clampWidthXplus/2, baseThick+subsThick, dep1Length+subsLength/2), ),    
    ((-subsWidth/2+clampWidthXplus/2, baseThick+subsThick, dep1Length+subsLength/2), ),       
    ))


  

myAssembly.Surface(name='SubYminus', side1Faces=myAssembly.instances['SubwithDep-1'].faces.findAt(
    ((0, baseThick, dep1Length+subsLength/2), ),  
    ((dep2Width/2+(subsWidth-dep2Width-2*clampWidthXplus)/4, baseThick, dep1Length+subsLength/2), ),   
    ((-dep2Width/2-(subsWidth-dep2Width-2*clampWidthXplus)/4, baseThick, dep1Length+subsLength/2), ),    
    ((subsWidth/2-clampWidthXplus/2, baseThick, dep1Length+subsLength/2), ),    
    ((-subsWidth/2+clampWidthXplus/2, baseThick, dep1Length+subsLength/2), ),       
    ))
    
##

#Set_Creation_Deposition1
myPart=myModel.parts['BasewithDep']
# Define the bounding box coordinates (xMin, yMin, zMin, xMax, yMax, zMax)
xMin, yMin, zMin = -dep2Width/2, baseThick, 0  # Adjust these values as per your model
xMax, yMax, zMax = dep2Width/2, baseThick+dep1Thick, dep1Length     # Adjust these values as per your model
# Select cells within the bounding box
selected_cells = myPart.cells.getByBoundingBox(xMin, yMin, zMin, xMax, yMax, zMax)
myPart.Set(cells=selected_cells, name='Deposition1')



#Set_Creation_Deposition2
myPart=myModel.parts['SubwithDep']
# Define the bounding box coordinates (xMin, yMin, zMin, xMax, yMax, zMax)
xMin, yMin, zMin = -dep2Width/2, baseThick+subsThick, dep1Length  # Adjust these values as per your model
xMax, yMax, zMax = dep2Width/2, baseThick+subsThick+dep2Thick, dep1Length+dep2Length     # Adjust these values as per your model
# Select cells within the bounding box
selected_cells = myPart.cells.getByBoundingBox(xMin, yMin, zMin, xMax, yMax, zMax)
myPart.Set(cells=selected_cells, name='Deposition2')


#Set_Creation_Deposition3
myPart=myModel.parts['BasewithDep']
# Define the bounding box coordinates (xMin, yMin, zMin, xMax, yMax, zMax)
xMin, yMin, zMin = -dep2Width/2, baseThick, dep1Length+dep2Length  # Adjust these values as per your model
xMax, yMax, zMax = dep2Width/2, baseThick+dep3Thick, baseLength     # Adjust these values as per your model

# Select cells within the bounding box
selected_cells = myPart.cells.getByBoundingBox(xMin, yMin, zMin, xMax, yMax, zMax)
myPart.Set(cells=selected_cells, name='Deposition3')

#Set_Creation_Base
myPart=myModel.parts['BasewithDep']
# Define the bounding box coordinates (xMin, yMin, zMin, xMax, yMax, zMax)
xMin, yMin, zMin = -baseWidth/2, 0, 0  # Adjust these values as per your model
xMax, yMax, zMax = baseWidth/2, baseThick, baseLength     # Adjust these values as per your model

# Select cells within the bounding box
selected_cells = myPart.cells.getByBoundingBox(xMin, yMin, zMin, xMax, yMax, zMax)
myPart.Set(cells=selected_cells, name='Base')


#Set_Creation_Substrate
myPart=myModel.parts['SubwithDep']
# Define the bounding box coordinates (xMin, yMin, zMin, xMax, yMax, zMax)
xMin, yMin, zMin = -subsWidth/2, baseThick, dep1Length  # Adjust these values as per your model
xMax, yMax, zMax = subsWidth/2, baseThick+subsThick, dep1Length+dep2Length     # Adjust these values as per your model
# Select cells within the bounding box
selected_cells = myPart.cells.getByBoundingBox(xMin, yMin, zMin, xMax, yMax, zMax)
myPart.Set(cells=selected_cells, name='Substrate')




for i in range(int(NumPartition)+1):
    surfName = 'Dep2Layer'+str(i)+'Top'
    myAssembly.Surface(name=surfName, side1Faces=
        myAssembly.instances['SubwithDep-1'].faces.findAt(((0, baseThick+subsThick+PartitionThick*i, dep1Length+dep2Length/2), )))

surfName = 'Dep2Top'
myAssembly.Surface(name=surfName, side1Faces=
    myAssembly.instances['SubwithDep-1'].faces.findAt(((0, baseThick+subsThick+PartitionThick*i, dep1Length+dep2Length/2), )))

for i in range(int(NumPartition)+1):
    surfName = 'Dep1Layer'+str(i)+'Top'
    myAssembly.Surface(name=surfName, side1Faces=
        myAssembly.instances['BasewithDep-1'].faces.findAt(((0, baseThick+PartitionThick*i, dep1Length/2), )))

surfName = 'Dep1Top'
myAssembly.Surface(name=surfName, side1Faces=
    myAssembly.instances['BasewithDep-1'].faces.findAt(((0, baseThick+PartitionThick*i, dep1Length/2), )))  


for i in range(int(NumPartition)+1):
    surfName = 'Dep3Layer'+str(i)+'Top'
    myAssembly.Surface(name=surfName, side1Faces=
        myAssembly.instances['BasewithDep-1'].faces.findAt(((0, baseThick+PartitionThick*i, dep1Length+dep2Length+dep3Length/2), )))

surfName = 'Dep3Top'
myAssembly.Surface(name=surfName, side1Faces=
    myAssembly.instances['BasewithDep-1'].faces.findAt(((0, baseThick+PartitionThick*i, dep1Length+dep2Length+dep3Length/2), )))

##Plate
#Plate_Bottom

myAssembly.Surface(name='PlateBottom', side1Faces=
    myAssembly.instances['BasewithDep-1'].faces.findAt(
    ((0, 0.0, (baseLength-subsLength)/4), ), #1,2
    ((0, 0.0, baseLength/2), ), #2,2
    ((0, 0.0, baseLength-(baseLength-subsLength)/4), ), #3,2
    ((dep1Width/2+(baseWidth-dep1Width-subsWidth)/4, 0.0, (baseLength-subsLength)/4), ), #1,2
    ((dep1Width/2+(baseWidth-dep1Width-subsWidth)/4, 0.0, baseLength/2), ), #2,2
    ((dep1Width/2+(baseWidth-dep1Width-subsWidth)/4, 0.0, baseLength-(baseLength-subsLength)/4), ), #3,2
    ((-dep1Width/2-(baseWidth-dep1Width-subsWidth)/4, 0.0, (baseLength-subsLength)/4), ), #1,2
    ((-dep1Width/2-(baseWidth-dep1Width-subsWidth)/4, 0.0, baseLength/2), ), #2,2
    ((-dep1Width/2-(baseWidth-dep1Width-subsWidth)/4, 0.0, baseLength-(baseLength-subsLength)/4), ), #3,2 
    ((subsWidth/2-clampWidthXplus/2, 0.0, (baseLength-subsLength)/4), ), #1,2
    ((subsWidth/2-clampWidthXplus/2, 0.0, baseLength/2), ), #2,2
    ((subsWidth/2-clampWidthXplus/2, 0.0, baseLength-(baseLength-subsLength)/4), ), #3,2
    ((-subsWidth/2+clampWidthXplus/2, 0.0, (baseLength-subsLength)/4), ), #1,2
    ((-subsWidth/2+clampWidthXplus/2, 0.0, baseLength/2), ), #2,2
    ((-subsWidth/2+clampWidthXplus/2, 0.0, baseLength-(baseLength-subsLength)/4), ), #3,2
    )) #3,3


myAssembly.Surface(name='PlateBot-Zone1', side1Faces=
    myAssembly.instances['BasewithDep-1'].faces.findAt(
    ((0, 0.0, baseLength/2), ), #2,2
    )) #3,3
    
myAssembly.Surface(name='PlateBot-Zone2', side1Faces=
    myAssembly.instances['BasewithDep-1'].faces.findAt(
    ((dep1Width/2+(baseWidth-dep1Width-subsWidth)/4, 0.0, baseLength/2), ), #2,2
    ((-dep1Width/2-(baseWidth-dep1Width-subsWidth)/4, 0.0, baseLength/2), ), #2,2
    )) #3,3
    
    
myAssembly.Surface(name='PlateBot-Zone3', side1Faces=
    myAssembly.instances['BasewithDep-1'].faces.findAt(
    ((baseWidth/2-clampWidthXplus/2, 0.0, baseLength/2), ), #2,2
    ((-baseWidth/2+clampWidthXplus/2, 0.0, baseLength/2), ), #2,2
    )) #3,3    


#Plate_Top
myAssembly.Surface(name='PlateTop', side1Faces=
    myAssembly.instances['BasewithDep-1'].faces.findAt(
    ((0, baseThick, (baseLength-subsLength)/4), ), #1,2
    ((0, baseThick, baseLength/2), ), #2,2
    ((0, baseThick, baseLength-(baseLength-subsLength)/4), ), #3,2
    ((dep1Width/2+(baseWidth-dep1Width-subsWidth)/4, baseThick, (baseLength-subsLength)/4), ), #1,2
    ((dep1Width/2+(baseWidth-dep1Width-subsWidth)/4, baseThick, baseLength/2), ), #2,2
    ((dep1Width/2+(baseWidth-dep1Width-subsWidth)/4, baseThick, baseLength-(baseLength-subsLength)/4), ), #3,2
    ((-dep1Width/2-(baseWidth-dep1Width-subsWidth)/4, baseThick, (baseLength-subsLength)/4), ), #1,2
    ((-dep1Width/2-(baseWidth-dep1Width-subsWidth)/4, baseThick, baseLength/2), ), #2,2
    ((-dep1Width/2-(baseWidth-dep1Width-subsWidth)/4, baseThick, baseLength-(baseLength-subsLength)/4), ), #3,2 
    ((baseWidth/2-clampWidthXplus/2, baseThick, (baseLength-subsLength)/4), ), #1,2
    ((baseWidth/2-clampWidthXplus/2, baseThick, baseLength/2), ), #2,2
    ((baseWidth/2-clampWidthXplus/2, baseThick, baseLength-(baseLength-subsLength)/4), ), #3,2
    ((-baseWidth/2+clampWidthXplus/2, baseThick, (baseLength-subsLength)/4), ), #1,2
    ((-baseWidth/2+clampWidthXplus/2, baseThick, baseLength/2), ), #2,2
    ((-baseWidth/2+clampWidthXplus/2, baseThick, baseLength-(baseLength-subsLength)/4), ), #3,2
    )) #3,3
    
#Plate_Top_Radiation
myAssembly.Surface(name='PlateTop_Exposed', side1Faces=
    myAssembly.instances['BasewithDep-1'].faces.findAt(
    ((0, baseThick, (baseLength-subsLength)/4), ), #1,2
    ((0, baseThick, baseLength-(baseLength-subsLength)/4), ), #3,2
    ((dep1Width/2+(baseWidth-dep1Width-subsWidth)/4, baseThick, (baseLength-subsLength)/4), ), #1,2
    ((dep1Width/2+(baseWidth-dep1Width-subsWidth)/4, baseThick, baseLength-(baseLength-subsLength)/4), ), #3,2
    ((-dep1Width/2-(baseWidth-dep1Width-subsWidth)/4, baseThick, (baseLength-subsLength)/4), ), #1,2
    ((-dep1Width/2-(baseWidth-dep1Width-subsWidth)/4, baseThick, baseLength-(baseLength-subsLength)/4), ), #3,2 
    ((baseWidth/2-clampWidthXplus/2, baseThick, (baseLength-subsLength)/4), ), #1,2
    ((baseWidth/2-clampWidthXplus/2, baseThick, baseLength/2), ), #2,2
    ((baseWidth/2-clampWidthXplus/2, baseThick, baseLength-(baseLength-subsLength)/4), ), #3,2
    ((-baseWidth/2+clampWidthXplus/2, baseThick, (baseLength-subsLength)/4), ), #1,2
    ((-baseWidth/2+clampWidthXplus/2, baseThick, baseLength/2), ), #2,2
    ((-baseWidth/2+clampWidthXplus/2, baseThick, baseLength-(baseLength-subsLength)/4), ), #3,2
    )) #3,3


#Plate_X_plus


    
myAssembly.Surface(name='BaseXplus', side1Faces=myAssembly.instances['BasewithDep-1'].faces.findAt((
    (baseWidth/2, baseThick/2, baseLength/6), ),
    ((baseWidth/2, baseThick/2, baseLength/2), ),
    ((baseWidth/2, baseThick/2, 5*baseLength/6), ), ))
    
myAssembly.Surface(name='BaseXminus', side1Faces=myAssembly.instances['BasewithDep-1'].faces.findAt((
    (-baseWidth/2, baseThick/2, baseLength/6), ),
    ((-baseWidth/2, baseThick/2, baseLength/2), ),
    ((-baseWidth/2, baseThick/2, 5*baseLength/6), ), ))
  
myAssembly.Surface(name='BaseZminus', side1Faces=myAssembly.instances['BasewithDep-1'].faces.findAt(
    ((0, baseThick/2, 0), ),
    ((dep1Width/2+(subsWidth-dep1Width)/4, baseThick/2, 0), ),
    ((-dep1Width/2-(subsWidth-dep1Width)/4, baseThick/2, 0), ),
    ((-5*baseWidth/12, baseThick/2, 0), ),
    ((5*baseWidth/12, baseThick/2, 0), ), ))
      
myAssembly.Surface(name='BaseZplus', side1Faces=myAssembly.instances['BasewithDep-1'].faces.findAt(
    ((0, baseThick/2, baseLength), ),
    ((dep1Width/2+(subsWidth-dep1Width)/4, baseThick/2, baseLength), ),
    ((-dep1Width/2-(subsWidth-dep1Width)/4, baseThick/2, baseLength), ),
    ((-5*baseWidth/12, baseThick/2, baseLength), ),
    ((5*baseWidth/12, baseThick/2, baseLength), ), ))
    
  

myAssembly.SurfaceByBoolean(name='BaseSides', surfaces=(
    myAssembly.surfaces['BaseXminus'], 
    myAssembly.surfaces['BaseXplus'], 
    myAssembly.surfaces['BaseZminus'], 
    myAssembly.surfaces['BaseZplus']))

  
    
# Define the coordinates of the bounding box
xmin, ymin, zmin = -24, 0.0, 103.4  # Lower corner of the box
xmax, ymax, zmax = 24, 0.05, 201.4  # Upper corner of the box

# Get the part and its nodes
part = mdb.models['Model-1'].parts['BasewithDep']
nodes = part.nodes

# Initialize an empty list to hold the node labels
node_labels = []

# Iterate through the nodes and check if they are inside the bounding box
for node in nodes:
    x, y, z = node.coordinates
    if xmin <= x <= xmax and ymin <= y <= ymax and zmin <= z <= zmax:
        node_labels.append(node.label)

# Create the node set with the nodes inside the bounding box
part.Set(name='Zone1', nodes=nodes.sequenceFromLabels(node_labels))






#####

# Define the coordinates of the bounding box
x_min, y_min, z_min = -200, 0.0, -5  # Lower corner of the box
x_max, y_max, z_max = 200, 0.05, 400  # Upper corner of the box


# Get the mesh elements of the part
elements = part.elements

# Initialize a list to store the elements inside the box
elements_inside_box = []

# Iterate over the elements to find those with at least three nodes on the bottom surface
for element in elements:
    nodes = element.getNodes()
    count = 0
    for node in nodes:
        x, y, z = node.coordinates
        if x_min <= x <= x_max and y == 0 and z_min <= z <= z_max:
            count += 1
    if count >= 3:
        elements_inside_box.append(element)

# Create a set for the elements inside the box
element_labels = [element.label for element in elements_inside_box]


instance_name = 'BasewithDep-1'  # 


myAssembly.Surface(face1Elements=myAssembly.instances[instance_name].elements.sequenceFromLabels(element_labels), name='BaseBottomSurface')                                         



#####
'''
# Define the coordinates of the bounding box
x_min, y_min, z_min = -24, 0.0, 103.4  # Lower corner of the box
x_max, y_max, z_max = 24, 0.05, 201.4  # Upper corner of the box


# Get the mesh elements of the part
elements = part.elements

# Initialize a list to store the elements inside the box
elements_inside_box = []

# Iterate over the elements to find those with at least three nodes on the bottom surface
for element in elements:
    nodes = element.getNodes()
    count = 0
    for node in nodes:
        x, y, z = node.coordinates
        if x_min <= x <= x_max and y == 0 and z_min <= z <= z_max:
            count += 1
    if count >= 3:
        elements_inside_box.append(element)

# Create a set for the elements inside the box
element_labels = [element.label for element in elements_inside_box]


instance_name = 'BasewithDep-1'  # 


myAssembly.Surface(face1Elements=myAssembly.instances[instance_name].elements.sequenceFromLabels(element_labels), name='Zone1')

##     ZONE5    ####
# Define the coordinates of the bounding box
x_min, y_min, z_min = -90, 0.0, 62.4  # Lower corner of the box
x_max, y_max, z_max = -65, 0.05, 245  # Upper corner of the box

# Get the mesh elements of the part
elements = part.elements

# Initialize a list to store the elements inside the box
elements_inside_box = []

# Iterate over the elements to find those with at least three nodes on the bottom surface
for element in elements:
    nodes = element.getNodes()
    count = 0
    for node in nodes:
        x, y, z = node.coordinates
        if x_min <= x <= x_max and y == 0 and z_min <= z <= z_max:
            count += 1
    if count >= 3:
        elements_inside_box.append(element)

# Create a set for the elements inside the box
element_labels = [element.label for element in elements_inside_box]

myAssembly.Surface(face1Elements=myAssembly.instances[instance_name].elements.sequenceFromLabels(element_labels), name='BottomSurfaceSet-Zone5-1')


# Define the coordinates of the bounding box
x_min, y_min, z_min = 65, 0.0, 62.4  # Lower corner of the box
x_max, y_max, z_max = 90, 0.05, 245  # Upper corner of the box

# Get the mesh elements of the part
elements = part.elements

# Initialize a list to store the elements inside the box
elements_inside_box = []

# Iterate over the elements to find those with at least three nodes on the bottom surface
for element in elements:
    nodes = element.getNodes()
    count = 0
    for node in nodes:
        x, y, z = node.coordinates
        if x_min <= x <= x_max and y == 0 and z_min <= z <= z_max:
            count += 1
    if count >= 3:
        elements_inside_box.append(element)

# Create a set for the elements inside the box
element_labels = [element.label for element in elements_inside_box]

myAssembly.Surface(face1Elements=myAssembly.instances[instance_name].elements.sequenceFromLabels(element_labels), name='BottomSurfaceSet-Zone5-2')


myAssembly.SurfaceByBoolean(name='Zone5', surfaces=(
    myAssembly.surfaces['BottomSurfaceSet-Zone5-1'], 
    myAssembly.surfaces['BottomSurfaceSet-Zone5-2']))



##     ZONE4    ####
# Define the coordinates of the bounding box
x_min, y_min, z_min = -75, 0.0, 62.4  # Lower corner of the box
x_max, y_max, z_max = -55, 0.05, 245  # Upper corner of the box

# Get the mesh elements of the part
elements = part.elements

# Initialize a list to store the elements inside the box
elements_inside_box = []


# Iterate over the elements to find those with at least three nodes on the bottom surface
for element in elements:
    nodes = element.getNodes()
    count = 0
    for node in nodes:
        x, y, z = node.coordinates
        if x_min <= x <= x_max and y == 0 and z_min <= z <= z_max:
            count += 1
    if count >= 3:
        elements_inside_box.append(element)


# Create a set for the elements inside the box
element_labels = [element.label for element in elements_inside_box]

myAssembly.Surface(face1Elements=myAssembly.instances[instance_name].elements.sequenceFromLabels(element_labels), name='BottomSurfaceSet-Zone4-1')


# Define the coordinates of the bounding box
x_min, y_min, z_min = 55, 0.0, 62.4  # Lower corner of the box
x_max, y_max, z_max = 75, 0.05, 245  # Upper corner of the box


# Get the mesh elements of the part
elements = part.elements

# Initialize a list to store the elements inside the box
elements_inside_box = []


# Iterate over the elements to find those with at least three nodes on the bottom surface
for element in elements:
    nodes = element.getNodes()
    count = 0
    for node in nodes:
        x, y, z = node.coordinates
        if x_min <= x <= x_max and y == 0 and z_min <= z <= z_max:
            count += 1
    if count >= 3:
        elements_inside_box.append(element)


# Create a set for the elements inside the box
element_labels = [element.label for element in elements_inside_box]

myAssembly.Surface(face1Elements=myAssembly.instances[instance_name].elements.sequenceFromLabels(element_labels), name='BottomSurfaceSet-Zone4-2')


myAssembly.SurfaceByBoolean(name='Zone4', surfaces=(
    myAssembly.surfaces['BottomSurfaceSet-Zone4-1'], 
    myAssembly.surfaces['BottomSurfaceSet-Zone4-2']))



##     ZONE3    ####


# Define the coordinates of the bounding box
x_min, y_min, z_min = -60, 0.0, 62.4  # Lower corner of the box
x_max, y_max, z_max = -40, 0.05, 245  # Upper corner of the box

# Get the mesh elements of the part
elements = part.elements

# Initialize a list to store the elements inside the box
elements_inside_box = []


# Iterate over the elements to find those with at least three nodes on the bottom surface
for element in elements:
    nodes = element.getNodes()
    count = 0
    for node in nodes:
        x, y, z = node.coordinates
        if x_min <= x <= x_max and y == 0 and z_min <= z <= z_max:
            count += 1
    if count >= 3:
        elements_inside_box.append(element)


# Create a set for the elements inside the box
element_labels = [element.label for element in elements_inside_box]

myAssembly.Surface(face1Elements=myAssembly.instances[instance_name].elements.sequenceFromLabels(element_labels), name='BottomSurfaceSet-Zone3-1')


# Define the coordinates of the bounding box
x_min, y_min, z_min = 40, 0.0, 62.4  # Lower corner of the box
x_max, y_max, z_max = 60, 0.05, 245  # Upper corner of the box


# Get the mesh elements of the part
elements = part.elements

# Initialize a list to store the elements inside the box
elements_inside_box = []


# Iterate over the elements to find those with at least three nodes on the bottom surface
for element in elements:
    nodes = element.getNodes()
    count = 0
    for node in nodes:
        x, y, z = node.coordinates
        if x_min <= x <= x_max and y == 0 and z_min <= z <= z_max:
            count += 1
    if count >= 3:
        elements_inside_box.append(element)


# Create a set for the elements inside the box
element_labels = [element.label for element in elements_inside_box]

myAssembly.Surface(face1Elements=myAssembly.instances[instance_name].elements.sequenceFromLabels(element_labels), name='BottomSurfaceSet-Zone3-2')



# Define the coordinates of the bounding box
x_min, y_min, z_min = -60, 0.0, 62.4  # Lower corner of the box
x_max, y_max, z_max = 60, 0.05, 86.4  # Upper corner of the box

# Get the mesh elements of the part
elements = part.elements

# Initialize a list to store the elements inside the box
elements_inside_box = []


# Iterate over the elements to find those with at least three nodes on the bottom surface
for element in elements:
    nodes = element.getNodes()
    count = 0
    for node in nodes:
        x, y, z = node.coordinates
        if x_min <= x <= x_max and y == 0 and z_min <= z <= z_max:
            count += 1
    if count >= 3:
        elements_inside_box.append(element)


# Create a set for the elements inside the box
element_labels = [element.label for element in elements_inside_box]

myAssembly.Surface(face1Elements=myAssembly.instances[instance_name].elements.sequenceFromLabels(element_labels), name='BottomSurfaceSet-Zone3-3')


# Define the coordinates of the bounding box
x_min, y_min, z_min = -60, 0.0, 218  # Lower corner of the box
x_max, y_max, z_max = 60, 0.05, 245  # Upper corner of the box


# Get the mesh elements of the part
elements = part.elements

# Initialize a list to store the elements inside the box
elements_inside_box = []


# Iterate over the elements to find those with at least three nodes on the bottom surface
for element in elements:
    nodes = element.getNodes()
    count = 0
    for node in nodes:
        x, y, z = node.coordinates
        if x_min <= x <= x_max and y == 0 and z_min <= z <= z_max:
            count += 1
    if count >= 3:
        elements_inside_box.append(element)


# Create a set for the elements inside the box
element_labels = [element.label for element in elements_inside_box]

myAssembly.Surface(face1Elements=myAssembly.instances[instance_name].elements.sequenceFromLabels(element_labels), name='BottomSurfaceSet-Zone3-4')



myAssembly.SurfaceByBoolean(name='Zone3', surfaces=(
    myAssembly.surfaces['BottomSurfaceSet-Zone3-1'], 
    myAssembly.surfaces['BottomSurfaceSet-Zone3-2'], 
    myAssembly.surfaces['BottomSurfaceSet-Zone3-3'], 
    myAssembly.surfaces['BottomSurfaceSet-Zone3-4']))



##     ZONE2    ####

# Define the coordinates of the bounding box
x_min, y_min, z_min = -42, 0.0, 86.4  # Lower corner of the box
x_max, y_max, z_max = -24, 0.05, 218  # Upper corner of the box

# Get the mesh elements of the part
elements = part.elements

# Initialize a list to store the elements inside the box
elements_inside_box = []


# Iterate over the elements to find those with at least three nodes on the bottom surface
for element in elements:
    nodes = element.getNodes()
    count = 0
    for node in nodes:
        x, y, z = node.coordinates
        if x_min <= x <= x_max and y == 0 and z_min <= z <= z_max:
            count += 1
    if count >= 3:
        elements_inside_box.append(element)


# Create a set for the elements inside the box
element_labels = [element.label for element in elements_inside_box]

myAssembly.Surface(face1Elements=myAssembly.instances[instance_name].elements.sequenceFromLabels(element_labels), name='BottomSurfaceSet-Zone2-1')


# Define the coordinates of the bounding box
x_min, y_min, z_min = 24, 0.0, 86.4  # Lower corner of the box
x_max, y_max, z_max = 42, 0.05, 218  # Upper corner of the box


# Get the mesh elements of the part
elements = part.elements

# Initialize a list to store the elements inside the box
elements_inside_box = []


# Iterate over the elements to find those with at least three nodes on the bottom surface
for element in elements:
    nodes = element.getNodes()
    count = 0
    for node in nodes:
        x, y, z = node.coordinates
        if x_min <= x <= x_max and y == 0 and z_min <= z <= z_max:
            count += 1
    if count >= 3:
        elements_inside_box.append(element)


# Create a set for the elements inside the box
element_labels = [element.label for element in elements_inside_box]

myAssembly.Surface(face1Elements=myAssembly.instances[instance_name].elements.sequenceFromLabels(element_labels), name='BottomSurfaceSet-Zone2-2')


# Define the coordinates of the bounding box
x_min, y_min, z_min = -42, 0.0, 84  # Lower corner of the box
x_max, y_max, z_max = 42, 0.05, 108  # Upper corner of the box

# Get the mesh elements of the part
elements = part.elements

# Initialize a list to store the elements inside the box
elements_inside_box = []


# Iterate over the elements to find those with at least three nodes on the bottom surface
for element in elements:
    nodes = element.getNodes()
    count = 0
    for node in nodes:
        x, y, z = node.coordinates
        if x_min <= x <= x_max and y == 0 and z_min <= z <= z_max:
            count += 1
    if count >= 3:
        elements_inside_box.append(element)


# Create a set for the elements inside the box
element_labels = [element.label for element in elements_inside_box]

myAssembly.Surface(face1Elements=myAssembly.instances[instance_name].elements.sequenceFromLabels(element_labels), name='BottomSurfaceSet-Zone2-3')


# Define the coordinates of the bounding box
x_min, y_min, z_min = -42, 0.0, 196  # Lower corner of the box
x_max, y_max, z_max = 42, 0.05, 220  # Upper corner of the box


# Get the mesh elements of the part
elements = part.elements

# Initialize a list to store the elements inside the box
elements_inside_box = []


# Iterate over the elements to find those with at least three nodes on the bottom surface
for element in elements:
    nodes = element.getNodes()
    count = 0
    for node in nodes:
        x, y, z = node.coordinates
        if x_min <= x <= x_max and y == 0 and z_min <= z <= z_max:
            count += 1
    if count >= 3:
        elements_inside_box.append(element)


# Create a set for the elements inside the box
element_labels = [element.label for element in elements_inside_box]

myAssembly.Surface(face1Elements=myAssembly.instances[instance_name].elements.sequenceFromLabels(element_labels), name='BottomSurfaceSet-Zone2-4')



myAssembly.SurfaceByBoolean(name='Zone2', surfaces=(
    myAssembly.surfaces['BottomSurfaceSet-Zone2-1'], 
    myAssembly.surfaces['BottomSurfaceSet-Zone2-2'], 
    myAssembly.surfaces['BottomSurfaceSet-Zone2-3'], 
    myAssembly.surfaces['BottomSurfaceSet-Zone2-4']))

##

myAssembly.SurfaceByBoolean(name='HotPlate', surfaces=(
    myAssembly.surfaces['Zone1'], 
    myAssembly.surfaces['Zone2'], 
    myAssembly.surfaces['Zone3'], 
    myAssembly.surfaces['Zone4'], 
    myAssembly.surfaces['Zone5']))




myAssembly.SurfaceByBoolean(name='BaseBottomSurface_wo_HotPlate', operation=
    DIFFERENCE, surfaces=(
    myAssembly.surfaces['BaseBottomSurface'], 
    myAssembly.surfaces['HotPlate']))   
    
##






# Define the coordinates of the bounding box
xmin1, ymin1, zmin1 = -90, 0.0, 62.4  # Lower corner of the box
xmax1, ymax1, zmax1 = -75, 0.05, 245  # Upper corner of the box

# Define the coordinates of the bounding box
xmin2, ymin2, zmin2 = 75, 0.0, 62.4  # Lower corner of the box
xmax2, ymax2, zmax2 = 90, 0.05, 245  # Upper corner of the box

# Get the part and its nodes
part = mdb.models['Model-1'].parts['BasewithDep']
nodes = part.nodes

# Initialize an empty list to hold the node labels
node_labels = []

# Iterate through the nodes and check if they are inside the bounding box
for node in nodes:
    x, y, z = node.coordinates
    if xmin1 <= x <= xmax1 and ymin1 <= y <= ymax1 and zmin1 <= z <= zmax1:
        node_labels.append(node.label)
    if xmin2 <= x <= xmax2 and ymin2 <= y <= ymax2 and zmin2 <= z <= zmax2:
        node_labels.append(node.label)    

# Create the node set with the nodes inside the bounding box
part.Set(name='Zone5', nodes=nodes.sequenceFromLabels(node_labels))









#####




# Define the coordinates of the bounding box
xmin1, ymin1, zmin1 = -75, 0.0, 62.4  # Lower corner of the box
xmax1, ymax1, zmax1 = -60, 0.05, 245  # Upper corner of the box

# Define the coordinates of the bounding box
xmin2, ymin2, zmin2 = 60, 0.0, 62.4  # Lower corner of the box
xmax2, ymax2, zmax2 = 75, 0.05, 245  # Upper corner of the box

# Get the part and its nodes
part = mdb.models['Model-1'].parts['BasewithDep']
nodes = part.nodes

# Initialize an empty list to hold the node labels
node_labels = []

# Iterate through the nodes and check if they are inside the bounding box
for node in nodes:
    x, y, z = node.coordinates
    if xmin1 <= x <= xmax1 and ymin1 <= y <= ymax1 and zmin1 <= z <= zmax1:
        node_labels.append(node.label)
    if xmin2 <= x <= xmax2 and ymin2 <= y <= ymax2 and zmin2 <= z <= zmax2:
        node_labels.append(node.label)    

# Create the node set with the nodes inside the bounding box
part.Set(name='Zone4', nodes=nodes.sequenceFromLabels(node_labels))



##


# Define the coordinates of the bounding box
xmin1, ymin1, zmin1 = -60, 0.0, 62.4  # Lower corner of the box
xmax1, ymax1, zmax1 = -45, 0.05, 245  # Upper corner of the box

# Define the coordinates of the bounding box
xmin2, ymin2, zmin2 = 45, 0.0, 62.4  # Lower corner of the box
xmax2, ymax2, zmax2 = 60, 0.05, 245  # Upper corner of the box

# Define the coordinates of the bounding box
xmin3, ymin3, zmin3 = -60, 0.0, 62.4  # Lower corner of the box
xmax3, ymax3, zmax3 = 60, 0.05, 86.4  # Upper corner of the box

# Define the coordinates of the bounding box
xmin4, ymin4, zmin4 = -60, 0.0, 218  # Lower corner of the box
xmax4, ymax4, zmax4 = 60, 0.05, 245  # Upper corner of the box

# Get the part and its nodes
part = mdb.models['Model-1'].parts['BasewithDep']
nodes = part.nodes

# Initialize an empty list to hold the node labels
node_labels = []

# Iterate through the nodes and check if they are inside the bounding box
for node in nodes:
    x, y, z = node.coordinates
    if xmin1 <= x <= xmax1 and ymin1 <= y <= ymax1 and zmin1 <= z <= zmax1:
        node_labels.append(node.label)
    if xmin2 <= x <= xmax2 and ymin2 <= y <= ymax2 and zmin2 <= z <= zmax2:
        node_labels.append(node.label)    
    if xmin3 <= x <= xmax3 and ymin3 <= y <= ymax3 and zmin3 <= z <= zmax3:
        node_labels.append(node.label) 
    if xmin4 <= x <= xmax4 and ymin4 <= y <= ymax4 and zmin4 <= z <= zmax4:
        node_labels.append(node.label)
        
# Create the node set with the nodes inside the bounding box
part.Set(name='Zone3', nodes=nodes.sequenceFromLabels(node_labels))



# Define the coordinates of the bounding box
xmin1, ymin1, zmin1 = -42, 0.0, 86.4  # Lower corner of the box
xmax1, ymax1, zmax1 = -24, 0.05, 218  # Upper corner of the box

# Define the coordinates of the bounding box
xmin2, ymin2, zmin2 = 24, 0.0, 86.4  # Lower corner of the box
xmax2, ymax2, zmax2 = 42, 0.05, 218  # Upper corner of the box

# Define the coordinates of the bounding box
xmin3, ymin3, zmin3 = -42, 0.0, 86.4  # Lower corner of the box
xmax3, ymax3, zmax3 = 42, 0.05, 103.4  # Upper corner of the box

# Define the coordinates of the bounding box
xmin4, ymin4, zmin4 = -42, 0.0, 201.4  # Lower corner of the box
xmax4, ymax4, zmax4 = 42, 0.05, 218  # Upper corner of the box

# Get the part and its nodes
part = mdb.models['Model-1'].parts['BasewithDep']
nodes = part.nodes

# Initialize an empty list to hold the node labels
node_labels = []

# Iterate through the nodes and check if they are inside the bounding box
for node in nodes:
    x, y, z = node.coordinates
    if xmin1 <= x <= xmax1 and ymin1 <= y <= ymax1 and zmin1 <= z <= zmax1:
        node_labels.append(node.label)
    if xmin2 <= x <= xmax2 and ymin2 <= y <= ymax2 and zmin2 <= z <= zmax2:
        node_labels.append(node.label)    
    if xmin3 <= x <= xmax3 and ymin3 <= y <= ymax3 and zmin3 <= z <= zmax3:
        node_labels.append(node.label) 
    if xmin4 <= x <= xmax4 and ymin4 <= y <= ymax4 and zmin4 <= z <= zmax4:
        node_labels.append(node.label)
        
# Create the node set with the nodes inside the bounding box
part.Set(name='Zone2', nodes=nodes.sequenceFromLabels(node_labels))    
    
    
'''


#Loadings
#InitialTemperatures
myModel.Temperature(
    createStepName          ='Initial', 
    crossSectionDistribution=CONSTANT_THROUGH_THICKNESS, 
    distributionType        =UNIFORM, 
    magnitudes              =(DepInitialTemp, ), 
    name                    ='Dep1InitialTemp', 
    region                  =myAssembly.instances['BasewithDep-1'].sets['Deposition1'])   
myModel.Temperature(
    createStepName          ='Initial', 
    crossSectionDistribution=CONSTANT_THROUGH_THICKNESS, 
    distributionType        = UNIFORM, 
    magnitudes              =(DepInitialTemp, ), 
    name                    ='Dep2InitialTemp', 
    region                  =myAssembly.instances['SubwithDep-1'].sets['Deposition2'])      
myModel.Temperature(
    createStepName          ='Initial', 
    crossSectionDistribution=CONSTANT_THROUGH_THICKNESS, 
    distributionType        = UNIFORM, 
    magnitudes              =(DepInitialTemp, ), 
    name                    ='Dep3InitialTemp', 
    region                  =myAssembly.instances['BasewithDep-1'].sets['Deposition3'])    
    
    
myModel.Temperature(
    createStepName          ='Initial', 
    crossSectionDistribution=CONSTANT_THROUGH_THICKNESS, 
    distributionType        =UNIFORM, 
    magnitudes              =(SubstrateTemp, ), 
    name                    ='SubstrateTemp', 
    region                  =myAssembly.instances['SubwithDep-1'].sets['Substrate'])  
myModel.Temperature(
    createStepName          ='Initial', 
    crossSectionDistribution=CONSTANT_THROUGH_THICKNESS, 
    distributionType        =UNIFORM, 
    magnitudes              =(BaseInitialTemp, ), 
    name                    ='BaseInitialTemp', 
    region                  =myAssembly.instances['BasewithDep-1'].sets['Base'])           
    
# Steps

#PreHeating
# Tirza Peeters change 11-04-2025 move hotplateSS to an if-statement
if Run_step_1 == 1:
    myModel.HeatTransferStep(
        name='HotplateSS', 
        previous='Initial', 
        timePeriod=HotplateSSTime, 
        maxNumInc=100000, 
        timeIncrementationMethod=FIXED, 
        initialInc=HotplateSSTimeInc)
    
# Tirza Peeters change 11-04-2025 move preheating and hotplateSS to an if-statement
if Run_step_2 == 1:
    if Run_step_1 == 1:
        myModel.HeatTransferStep(
            name='PreHeating', 
            previous='HotplateSS', 
            timePeriod=PreHeatingTime, 
            maxNumInc=100000, 
            timeIncrementationMethod=FIXED, 
            initialInc=PreHeatingTimeInc)

    elif Run_step_1 == 0:
        myModel.HeatTransferStep(
            name='PreHeating', 
            previous='Initial', 
            timePeriod=PreHeatingTime, 
            maxNumInc=100000, 
            timeIncrementationMethod=FIXED, 
            initialInc=PreHeatingTimeInc)
    
    #Deposition
    myModel.HeatTransferStep(
        name='Deposition', 
        previous='PreHeating', 
        timePeriod=DepositionTime, 
        maxNumInc=1000000, 
        timeIncrementationMethod=FIXED, 
        initialInc=DepositionTimeInc)

elif Run_step_2 == 0:
    if Run_step_1 == 1:
        #Deposition
        myModel.HeatTransferStep(
            name='Deposition', 
            previous='HotplateSS', 
            timePeriod=DepositionTime, 
            maxNumInc=1000000, 
            timeIncrementationMethod=FIXED, 
            initialInc=DepositionTimeInc)

    elif Run_step_1 == 0:
        myModel.HeatTransferStep(
            name='Deposition', 
            previous='Initial', 
            timePeriod=DepositionTime, 
            maxNumInc=1000000, 
            timeIncrementationMethod=FIXED, 
            initialInc=DepositionTimeInc)

    

#Cooling1
myModel.HeatTransferStep(
    name='Cooling1', 
    previous='Deposition', 
    timePeriod=CoolingTime1, 
    maxNumInc=100000, 
    timeIncrementationMethod=FIXED, 
    initialInc=CoolingTimeInc1)
    
#   
# SM change: In the original file this step had timeIncrementationMethod=AUTOMATIC
# I am reverting this back to FIXED (7/30/2025)
# 
#ReleaseFixtures
myModel.HeatTransferStep(
    name      = 'ReleaseFixtures', 
    previous  = 'Cooling1', 
    timePeriod= ReleaseFixturesTime, 
    maxNumInc = 100000, 
    initialInc= ReleaseFixturesTime/10, 
    minInc    = 1.0e-05, 
    maxInc    = ReleaseFixturesTime, 
    deltmx    = 1000.0)
    
#ReleaseFixturesTimeInc = ReleaseFixturesTime/10
    
#myModel.HeatTransferStep(
#    name='ReleaseFixtures', 
#    previous='Cooling1', 
#   timePeriod=ReleaseFixturesTime, 
#    maxNumInc=100000, 
#    timeIncrementationMethod=FIXED, 
#    initialInc=ReleaseFixturesTimeInc)   
#
# end of SM changes   
# 
    
#Cooling2
myModel.HeatTransferStep(
    name='Cooling2', 
    previous='ReleaseFixtures', 
    timePeriod=CoolingTime2, 
    maxNumInc=100000, 
    timeIncrementationMethod=FIXED, 
    initialInc=CoolingTimeInc2)
    
  
#BC-clamps

#Heat Transfer anaysis does not need clamp 

#BCs
#BasePlateBottomTemp


'''
myModel.TemperatureBC(createStepName='PreHeating', distributionType=
    UNIFORM, fieldName='', magnitude=BasePlateBottomTemp, name='BasePlateBottomTemp', region=
    myAssembly.instances['BasewithDep-1'].sets['Base'])
myModel.boundaryConditions['BasePlateBottomTemp'].deactivate('Cooling1')
'''


#Conduction
myModel.ContactProperty('Conduction')
myModel.interactionProperties['Conduction'].ThermalConductance(
    clearanceDepTable=((300000000000.0, 0.0), (0.0, 0.015)), 
    clearanceDependency=ON, 
    definition=TABULAR, 
    dependenciesC=0, 
    massFlowRateDependencyC=OFF, 
    pressureDependency=OFF, 
    temperatureDependencyC=OFF)
    
myModel.SurfaceToSurfaceContactStd(
    adjustMethod=NONE, 
    clearanceRegion=None, 
    createStepName='Initial', 
    datumAxis=None, 
    initialClearance=OMIT, 
    interactionProperty='Conduction', 
    main=myModel.rootAssembly.surfaces['PlateTop'], 
    name='Conduction', 
    secondary=myModel.rootAssembly.surfaces['SubYminus'], 
    sliding=
    FINITE, 
    thickness=ON)


#Heat-Flux-Load
# Tirza Peeters change 11-04-2025 move preheating to an if-statement
if Run_step_2 == 1:

    for i in range(0, int(NumPartition) + 1):
        surfNameDep2 = 'Dep2Layer' + str(i) + 'Top'
        myModel.SurfaceHeatFlux(createStepName  ='PreHeating', 
                                distributionType=USER_DEFINED,
                                magnitude       =1.0, 
                                name            =surfNameDep2, 
                                region          =myAssembly.surfaces[surfNameDep2])                           
        myModel.loads[surfNameDep2].deactivate('Cooling1')
    
        #
        # For Dep1Layer
        surfNameDep1 = 'Dep1Layer' + str(i) + 'Top'
        myModel.SurfaceHeatFlux(createStepName  ='PreHeating', 
                                distributionType=USER_DEFINED,
                                magnitude       =1.0, 
                                name            =surfNameDep1, 
                                region          =myAssembly.surfaces[surfNameDep1])                            
        myModel.loads[surfNameDep1].deactivate('Cooling1')
        #
        # For Dep3Layer
        surfNameDep3 = 'Dep3Layer' + str(i) + 'Top'
        myModel.SurfaceHeatFlux(createStepName  ='PreHeating', 
                                distributionType=USER_DEFINED,
                                magnitude       =1.0, 
                                name            =surfNameDep3, 
                                region          =myAssembly.surfaces[surfNameDep3])                           
        myModel.loads[surfNameDep3].deactivate('Cooling1')


    myModel.SurfaceHeatFlux(
        createStepName  ='PreHeating', 
        distributionType=USER_DEFINED, 
        magnitude       =1.0, 
        name            ='SubUserHeatFlux', 
        region          =myModel.rootAssembly.surfaces['SubYplus_woClamp'])

    myModel.loads['SubUserHeatFlux'].deactivate('Cooling1')
  
    myModel.SurfaceHeatFlux(
        createStepName  ='PreHeating', 
        distributionType=USER_DEFINED, 
        magnitude       =1.0, 
        name            ='BaseUserHeatFlux', 
        region          =myModel.rootAssembly.surfaces['PlateTop_Exposed'])

    myModel.loads['BaseUserHeatFlux'].deactivate('Cooling1')

##Interactions

#########PlateBottom-Sides#########
'''
myModel.RadiationToAmbient(ambientTemperature=ambientTemp, 
    ambientTemperatureAmp='', createStepName='HotplateSS', distributionType=
    UNIFORM, emissivity=emissSubsDep, field='', name='PlateBottom_Radiation', radiationType=AMBIENT
    , surface=myAssembly.surfaces['BaseBottomSurface'])
'''

# Tirza Peeters change 11-04-2025 move hotplateSS to an if-statement
if Run_step_1 == 1:
    myModel.FilmCondition(
        createStepName      ='HotplateSS', 
        definition          =EMBEDDED_COEFF, 
        filmCoeff           =film_ContactCoefHP, 
        filmCoeffAmplitude  ='', 
        name                ='PlateBottom_Hotplate', 
        sinkAmplitude       ='', 
        sinkDistributionType=UNIFORM, 
        sinkFieldName       ='', 
        sinkTemperature     =HotPlateTemp, 
        surface=myAssembly.surfaces['BaseBottomSurface']) 

    myModel.interactions['PlateBottom_Hotplate'].deactivate('Cooling1')


myModel.FilmCondition(
    createStepName='Cooling1', 
    definition          = EMBEDDED_COEFF, 
    filmCoeff           =film_ContactCoefHP, 
    filmCoeffAmplitude  ='', 
    name                ='PlateBottom_Hotplate_cooling', 
    sinkAmplitude       ='', 
    sinkDistributionType=UNIFORM, 
    sinkFieldName       ='', 
    sinkTemperature     =HotPlateTemp/2+ambientTemp/2, 
    surface             =myAssembly.surfaces['BaseBottomSurface']) 

myModel.interactions['PlateBottom_Hotplate_cooling'].deactivate('ReleaseFixtures')


myModel.FilmCondition(
    createStepName      ='ReleaseFixtures', 
    definition          = EMBEDDED_COEFF, 
    filmCoeff           =FreeConvectionCf, 
    filmCoeffAmplitude  ='', 
    name                ='PlateBottom_Table', 
    sinkAmplitude       ='', 
    sinkDistributionType=UNIFORM, 
    sinkFieldName       ='', 
    sinkTemperature     =ambientTemp, 
    surface             =myAssembly.surfaces['BaseBottomSurface']) 

#########Substrate#########
# Tirza Peeters change 11-04-2025 move hotplateSS and preheatig to an if-statement
if Run_step_1 == 1:
    myModel.RadiationToAmbient(
        ambientTemperature   =ambientTemp, 
        ambientTemperatureAmp='', 
        createStepName       ='HotplateSS', 
        distributionType     =UNIFORM, 
        emissivity           =emissSubsDep, 
        field                ='', 
        name                 ='SubstrateSides-Radiation', 
        radiationType        =AMBIENT, 
        surface              =myAssembly.surfaces['SubstrateSides'])


    myModel.FilmCondition(
        createStepName     ='HotplateSS', 
        definition          = EMBEDDED_COEFF, 
        filmCoeff           =FreeConvectionCf, 
        filmCoeffAmplitude  ='', 
        name                ='SubstrateSides_Convection', 
        sinkAmplitude       ='', 
        sinkDistributionType=UNIFORM, 
        sinkFieldName       ='', 
        sinkTemperature     =ambientTemp, 
        surface             =myAssembly.surfaces['SubstrateSides']) 
elif Run_step_2 == 1:
    myModel.RadiationToAmbient(
        ambientTemperature   =ambientTemp, 
        ambientTemperatureAmp='', 
        createStepName       ='PreHeating', 
        distributionType     =UNIFORM, 
        emissivity           =emissSubsDep, 
        field                ='', 
        name                 ='SubstrateSides-Radiation', 
        radiationType        =AMBIENT, 
        surface              =myAssembly.surfaces['SubstrateSides'])


    myModel.FilmCondition(
        createStepName     ='PreHeating', 
        definition          = EMBEDDED_COEFF, 
        filmCoeff           =FreeConvectionCf, 
        filmCoeffAmplitude  ='', 
        name                ='SubstrateSides_Convection', 
        sinkAmplitude       ='', 
        sinkDistributionType=UNIFORM, 
        sinkFieldName       ='', 
        sinkTemperature     =ambientTemp, 
        surface             =myAssembly.surfaces['SubstrateSides']) 
else:
    myModel.RadiationToAmbient(
        ambientTemperature   =ambientTemp, 
        ambientTemperatureAmp='', 
        createStepName       ='Deposition', 
        distributionType     =UNIFORM, 
        emissivity           =emissSubsDep, 
        field                ='', 
        name                 ='SubstrateSides-Radiation', 
        radiationType        =AMBIENT, 
        surface              =myAssembly.surfaces['SubstrateSides'])


    myModel.FilmCondition(
        createStepName     ='Deposition', 
        definition          = EMBEDDED_COEFF, 
        filmCoeff           =FreeConvectionCf, 
        filmCoeffAmplitude  ='', 
        name                ='SubstrateSides_Convection', 
        sinkAmplitude       ='', 
        sinkDistributionType=UNIFORM, 
        sinkFieldName       ='', 
        sinkTemperature     =ambientTemp, 
        surface             =myAssembly.surfaces['SubstrateSides']) 


#########Substrate#########
  
########## 
 
myModel.RadiationToAmbient(
    ambientTemperature   =ambientTemp, 
    ambientTemperatureAmp='', 
    createStepName       ='Cooling1', 
    distributionType     =UNIFORM, 
    emissivity           =emissSubsDep, 
    field                ='', 
    name                 ='SubstrateTop_Radiation', 
    radiationType        =AMBIENT, 
    surface              =myAssembly.surfaces['SubYplus_woClamp']) 
    
  
myModel.FilmCondition(
    createStepName      ='Cooling1', 
    definition          =EMBEDDED_COEFF, 
    filmCoeff           =FreeConvectionCf, 
    filmCoeffAmplitude  ='', 
    name                ='SubstrateTop_Convection', 
    sinkAmplitude       ='', 
    sinkDistributionType=UNIFORM, 
    sinkFieldName       ='', 
    sinkTemperature     =ambientTemp, 
    surface             =myAssembly.surfaces['SubYplus_woClamp'])    

# Tirza Peeters change 11-04-2025 move hotplateSS and preheating to an if-statement
if Run_step_1 == 1:
    myModel.FilmCondition(
        createStepName      ='HotplateSS', 
        definition          =EMBEDDED_COEFF, 
        filmCoeff           =film_ContactCoefHP, 
        filmCoeffAmplitude  ='', 
        name                ='Clamp_Conduction', 
        sinkAmplitude       ='', 
        sinkDistributionType=UNIFORM, 
        sinkFieldName       ='', 
        sinkTemperature     =ambientTemp, 
        surface             =myAssembly.surfaces['ClampYplus']) 

    myModel.interactions['Clamp_Conduction'].deactivate('ReleaseFixtures')

elif Run_step_2 == 1:
    myModel.FilmCondition(
        createStepName      ='PreHeating', 
        definition          =EMBEDDED_COEFF, 
        filmCoeff           =film_ContactCoefHP, 
        filmCoeffAmplitude  ='', 
        name                ='Clamp_Conduction', 
        sinkAmplitude       ='', 
        sinkDistributionType=UNIFORM, 
        sinkFieldName       ='', 
        sinkTemperature     =ambientTemp, 
        surface             =myAssembly.surfaces['ClampYplus']) 

    myModel.interactions['Clamp_Conduction'].deactivate('ReleaseFixtures')

else:
    myModel.FilmCondition(
        createStepName      ='Deposition', 
        definition          =EMBEDDED_COEFF, 
        filmCoeff           =film_ContactCoefHP, 
        filmCoeffAmplitude  ='', 
        name                ='Clamp_Conduction', 
        sinkAmplitude       ='', 
        sinkDistributionType=UNIFORM, 
        sinkFieldName       ='', 
        sinkTemperature     =ambientTemp, 
        surface             =myAssembly.surfaces['ClampYplus']) 

    myModel.interactions['Clamp_Conduction'].deactivate('ReleaseFixtures')


myModel.FilmCondition(
    createStepName='Cooling2', 
    definition          =EMBEDDED_COEFF, 
    filmCoeff           =FreeConvectionCf, 
    filmCoeffAmplitude  ='', 
    name                ='Clamp_Convection', 
    sinkAmplitude       ='', 
    sinkDistributionType=UNIFORM, 
    sinkFieldName       ='', 
    sinkTemperature     =ambientTemp, 
    surface             =myAssembly.surfaces['ClampYplus']) 

#########

#########Base#########

##########
# Tirza Peeters change 11-04-2025 move hotplateSS and preheating to an if-statement
if Run_step_1 == 1:
    myModel.FilmCondition(
        createStepName      ='HotplateSS', 
        definition          =EMBEDDED_COEFF, 
        filmCoeff           =FreeConvectionCf, 
        filmCoeffAmplitude  ='', 
        name                ='PlateTop_Convection', 
        sinkAmplitude       ='', 
        sinkDistributionType=UNIFORM, 
        sinkFieldName       ='', 
        sinkTemperature     =ambientTemp, 
        surface             =myAssembly.surfaces['PlateTop_Exposed']) 

    myModel.RadiationToAmbient(
        ambientTemperature    =ambientTemp, 
        ambientTemperatureAmp ='', 
        createStepName        ='HotplateSS', 
        distributionType      = UNIFORM, 
        emissivity            =emissSubsDep, 
        field                 ='', 
        name                  ='PlateTop_Radiation', 
        radiationType         =AMBIENT, 
        surface               =myAssembly.surfaces['PlateTop_Exposed']) 

elif Run_step_2 == 1:
    myModel.FilmCondition(
        createStepName      ='PreHeating', 
        definition          =EMBEDDED_COEFF, 
        filmCoeff           =FreeConvectionCf, 
        filmCoeffAmplitude  ='', 
        name                ='PlateTop_Convection', 
        sinkAmplitude       ='', 
        sinkDistributionType=UNIFORM, 
        sinkFieldName       ='', 
        sinkTemperature     =ambientTemp, 
        surface             =myAssembly.surfaces['PlateTop_Exposed']) 

    myModel.RadiationToAmbient(
        ambientTemperature    =ambientTemp, 
        ambientTemperatureAmp ='', 
        createStepName        ='PreHeating', 
        distributionType      = UNIFORM, 
        emissivity            =emissSubsDep, 
        field                 ='', 
        name                  ='PlateTop_Radiation', 
        radiationType         =AMBIENT, 
        surface               =myAssembly.surfaces['PlateTop_Exposed']) 

else:
    myModel.FilmCondition(
        createStepName      ='Deposition', 
        definition          =EMBEDDED_COEFF, 
        filmCoeff           =FreeConvectionCf, 
        filmCoeffAmplitude  ='', 
        name                ='PlateTop_Convection', 
        sinkAmplitude       ='', 
        sinkDistributionType=UNIFORM, 
        sinkFieldName       ='', 
        sinkTemperature     =ambientTemp, 
        surface             =myAssembly.surfaces['PlateTop_Exposed']) 

    myModel.RadiationToAmbient(
        ambientTemperature    =ambientTemp, 
        ambientTemperatureAmp ='', 
        createStepName        ='Deposition', 
        distributionType      = UNIFORM, 
        emissivity            =emissSubsDep, 
        field                 ='', 
        name                  ='PlateTop_Radiation', 
        radiationType         =AMBIENT, 
        surface               =myAssembly.surfaces['PlateTop_Exposed']) 
    
##########

###BasePlate###
# Tirza Peeters change 11-04-2025 move hotplateSS and preheating to an if-statement
if Run_step_1 == 1:
    myModel.RadiationToAmbient(
        ambientTemperature    =ambientTemp, 
        ambientTemperatureAmp ='', 
        createStepName        ='HotplateSS', 
        distributionType      = UNIFORM, 
        emissivity            =emissSubsDep, 
        field                 ='', 
        name                  ='BaseSides-Radiation', 
        radiationType         =AMBIENT,
        surface               =myAssembly.surfaces['BaseSides'])
    
    ##
    myModel.FilmCondition(
        createStepName      ='HotplateSS', 
        definition          =EMBEDDED_COEFF, 
        filmCoeff           =FreeConvectionCf, 
        filmCoeffAmplitude  ='', 
        name                ='BaseSides_Convection', 
        sinkAmplitude       ='', 
        sinkDistributionType=UNIFORM, 
        sinkFieldName       ='', 
        sinkTemperature     =ambientTemp, 
        surface             =myAssembly.surfaces['BaseSides'])  

elif Run_step_2 == 1:
    myModel.RadiationToAmbient(
        ambientTemperature    =ambientTemp, 
        ambientTemperatureAmp ='', 
        createStepName        ='PreHeating', 
        distributionType      = UNIFORM, 
        emissivity            =emissSubsDep, 
        field                 ='', 
        name                  ='BaseSides-Radiation', 
        radiationType         =AMBIENT,
        surface               =myAssembly.surfaces['BaseSides'])
    
    ##
    myModel.FilmCondition(
        createStepName      ='PreHeating', 
        definition          =EMBEDDED_COEFF, 
        filmCoeff           =FreeConvectionCf, 
        filmCoeffAmplitude  ='', 
        name                ='BaseSides_Convection', 
        sinkAmplitude       ='', 
        sinkDistributionType=UNIFORM, 
        sinkFieldName       ='', 
        sinkTemperature     =ambientTemp, 
        surface             =myAssembly.surfaces['BaseSides'])

else:
    myModel.RadiationToAmbient(
        ambientTemperature    =ambientTemp, 
        ambientTemperatureAmp ='', 
        createStepName        ='Deposition', 
        distributionType      = UNIFORM, 
        emissivity            =emissSubsDep, 
        field                 ='', 
        name                  ='BaseSides-Radiation', 
        radiationType         =AMBIENT,
        surface               =myAssembly.surfaces['BaseSides'])
    
    ##
    myModel.FilmCondition(
        createStepName      ='Deposition', 
        definition          =EMBEDDED_COEFF, 
        filmCoeff           =FreeConvectionCf, 
        filmCoeffAmplitude  ='', 
        name                ='BaseSides_Convection', 
        sinkAmplitude       ='', 
        sinkDistributionType=UNIFORM, 
        sinkFieldName       ='', 
        sinkTemperature     =ambientTemp, 
        surface             =myAssembly.surfaces['BaseSides'])
    
##Cooling-deposition

myModel.RadiationToAmbient(
    ambientTemperature   =ambientTemp, 
    ambientTemperatureAmp='', 
    createStepName       ='Cooling1', 
    distributionType     =UNIFORM, 
    emissivity           =emissSubsDep, 
    field                ='', 
    name                 ='DepTop1-Radiation', 
    radiationType        =AMBIENT, 
    surface              =myAssembly.surfaces['Dep1Top'])


myModel.RadiationToAmbient(
    ambientTemperature   =ambientTemp, 
    ambientTemperatureAmp='', 
    createStepName       ='Cooling1', 
    distributionType     = UNIFORM, 
    emissivity           =emissSubsDep, 
    field                ='', 
    name                 ='DepTop2-Radiation', 
    radiationType        =AMBIENT, 
    surface              =myAssembly.surfaces['Dep2Top'])

myModel.RadiationToAmbient(
    ambientTemperature   =ambientTemp, 
    ambientTemperatureAmp='', 
    createStepName       ='Cooling1', 
    distributionType     = UNIFORM, 
    emissivity           = emissSubsDep, 
    field                ='', 
    name                 ='DepTop3-Radiation', 
    radiationType        =AMBIENT, 
    surface              = myAssembly.surfaces['Dep3Top'])


##
myModel.FilmCondition(
    createStepName      ='Cooling1', 
    definition          =EMBEDDED_COEFF, 
    filmCoeff           =FreeConvectionCf, 
    filmCoeffAmplitude  ='', 
    name                ='DepTop1_Convection', 
    sinkAmplitude       ='', 
    sinkDistributionType=UNIFORM, 
    sinkFieldName       ='', 
    sinkTemperature     =ambientTemp, 
    surface             =myAssembly.surfaces['Dep1Top']) 


myModel.FilmCondition(
    createStepName      ='Cooling1', 
    definition          =EMBEDDED_COEFF, 
    filmCoeff           =FreeConvectionCf, 
    filmCoeffAmplitude  ='', 
    name                ='DepTop2_Convection', 
    sinkAmplitude       ='', 
    sinkDistributionType=UNIFORM, 
    sinkFieldName       ='', 
    sinkTemperature     =ambientTemp, 
    surface             =myAssembly.surfaces['Dep2Top']) 

myModel.FilmCondition(
    createStepName      ='Cooling1', 
    definition          =EMBEDDED_COEFF, 
    filmCoeff           =FreeConvectionCf, 
    filmCoeffAmplitude  ='', 
    name                ='DepTop3_Convection', 
    sinkAmplitude       ='', 
    sinkDistributionType=UNIFORM, 
    sinkFieldName       ='', 
    sinkTemperature     =ambientTemp, 
    surface             =myAssembly.surfaces['Dep3Top']) 


###BasePlate###


###HotPlate###
# SM Additions: Commented code deleted

# -------------------------------------------------------
# HT_setGeneralSolnCtrls():
# -------------------------------------------------------

# Tirza Peeters change 11-04-2025 move hotplateSS to an if-statement (not sure)
if Run_step_1 == 1:
    myModel.steps['HotplateSS'].control.setValues(
        resetDefaultValues=ON)
    myModel.steps['HotplateSS'].control.setValues(
        allowPropagation=OFF, 
        resetDefaultValues=OFF, 
        timeIncrementation=(8.0, 10.0, 9.0, 16.0, 10.0, 4.0, 12.0, 15.0, 6.0, 3.0, 50.0))
    myModel.steps['HotplateSS'].control.setValues(
        temperatureField=(0.015, 1.0, 0.0, 0.0, 0.02, 1e-05, 0.001, 1e-08, 1.0, 1e-05))


    # Set field & history output requests
    myModel.FieldOutputRequest(
        name='F-Output-1', 
        createStepName='HotplateSS', 
        variables=('TEMP', 'NT', 'EACTIVE', 'HFL', 'HTL', 'RFLE', 'NFLUX' , 'FILMCOEF', 'SINKTEMP'))
    myModel.HistoryOutputRequest(
        name='H-Output-1', 
        createStepName='HotplateSS', 
        variables=PRESELECT)

elif Run_step_2 == 1:
    myModel.steps['PreHeating'].control.setValues(
        resetDefaultValues=ON)
    myModel.steps['PreHeating'].control.setValues(
        allowPropagation=OFF, 
        resetDefaultValues=OFF, 
        timeIncrementation=(8.0, 10.0, 9.0, 16.0, 10.0, 4.0, 12.0, 15.0, 6.0, 3.0, 50.0))
    myModel.steps['PreHeating'].control.setValues(
        temperatureField=(0.015, 1.0, 0.0, 0.0, 0.02, 1e-05, 0.001, 1e-08, 1.0, 1e-05))


    # Set field & history output requests
    myModel.FieldOutputRequest(
        name='F-Output-1', 
        createStepName='PreHeating', 
        variables=('TEMP', 'NT', 'EACTIVE', 'HFL', 'HTL', 'RFLE', 'NFLUX' , 'FILMCOEF', 'SINKTEMP'))
    myModel.HistoryOutputRequest(
        name='H-Output-1', 
        createStepName='PreHeating', 
        variables=PRESELECT)

else:
    myModel.steps['Deposition'].control.setValues(
        resetDefaultValues=ON)
    myModel.steps['Deposition'].control.setValues(
        allowPropagation=OFF, 
        resetDefaultValues=OFF, 
        timeIncrementation=(8.0, 10.0, 9.0, 16.0, 10.0, 4.0, 12.0, 15.0, 6.0, 3.0, 50.0))
    myModel.steps['Deposition'].control.setValues(
        temperatureField=(0.015, 1.0, 0.0, 0.0, 0.02, 1e-05, 0.001, 1e-08, 1.0, 1e-05))


    # Set field & history output requests
    myModel.FieldOutputRequest(
        name='F-Output-1', 
        createStepName='Deposition', 
        variables=('TEMP', 'NT', 'EACTIVE', 'HFL', 'HTL', 'RFLE', 'NFLUX' , 'FILMCOEF', 'SINKTEMP'))
    myModel.HistoryOutputRequest(
        name='H-Output-1', 
        createStepName='Deposition', 
        variables=PRESELECT)


##input file modifications##
def GetBlockPosition(modelName, blockPrefix):                             
    if blockPrefix == '':
        return len(mdb.models[modelName].keywordBlock.sieBlocks)-1
    pos = 0
    for block in mdb.models[modelName].keywordBlock.sieBlocks:
        if block[0:len(blockPrefix)].lower()==blockPrefix.lower():
            return pos
        pos=pos+1
    return -1
   
current_model_name = mdb.models.keys()[-1]
   
myModel.keywordBlock.synchVersions(storeNodesAndElements=False)

##Specifying Elements for Activation
#You must first define the elements that can be used 
#for activation in the model in the same way that you define regular elements.
#Then you must assign the elements to a specific progressive element activation feature.

myModel.keywordBlock.insert(GetBlockPosition(current_model_name, '*End Assembly')-1,
    """*ELEMENT PROGRESSIVE ACTIVATION,NAME=ACTIVE1,ELSET=BasewithDep-1.Deposition1,FOLLOW=YES""")

myModel.keywordBlock.insert(GetBlockPosition(current_model_name, '*End Assembly')-1,
    """*ELEMENT PROGRESSIVE ACTIVATION,NAME=ACTIVE2,ELSET=SubwithDep-1.Deposition2,FOLLOW=YES""")

myModel.keywordBlock.insert(GetBlockPosition(current_model_name, '*End Assembly')-1,
    """*ELEMENT PROGRESSIVE ACTIVATION,NAME=ACTIVE3,ELSET=BasewithDep-1.Deposition3,FOLLOW=YES""")
    
#Switching Off/On Progressive Element Activation in a Step   
#Elements that are assigned to a specific progressive element activation can
#be activated only in steps in which the feature is switched on. 
#Use the following option to switch on progressive element activation
#in a step:
#repeat the option in each step as many times as necessary to turn on multiple activations.

stepName = 'Deposition'
myModel.keywordBlock.insert(
    GetBlockPosition(current_model_name, '*Step, name=' + stepName) + 1,
    """*ACTIVATE ELEMENT,ACTIVATION=ACTIVE3""")
myModel.keywordBlock.insert(
    GetBlockPosition(current_model_name, '*Step, name=' + stepName) + 1,
    """*ACTIVATE ELEMENT,ACTIVATION=ACTIVE2""")
myModel.keywordBlock.insert(
    GetBlockPosition(current_model_name, '*Step, name=' + stepName) + 1,
    """*ACTIVATE ELEMENT,ACTIVATION=ACTIVE1""")
    

##SubroutineGeneration

##Activation

# Extracting 'P' and 'r0' values from the JSON data
P_deposition = data['Laser']['P_deposition']
P_preheat    = data['Laser']['P_preheat']
r0           = data['Laser']['r0']

sprayNzzlVel = data['Nozzle']['sprayNzzlVel']
sprayNzzlAccel = data['Nozzle']['sprayNzzlAccel']

sprayFrmsPerTrk = data['Spray']['sprayFrmsPerTrk']

depLength     = data['Deposition']['depLength']

eig11 = data['Stress']['eig11']
eig22 = data['Stress']['eig22']
eig33 = data['Stress']['eig33']

#print("eig11 = {} ".format(eig11))

PartitionThick = data['Deposition']['depTrkThick']

# Layers
depNoOfLyrs = data['Layers']['depNoOfLyrs']

#
# SM additions:
# Forced heat transfer coefficients
TrA1= data['ForcedConvection']['TrA1']
TrB1= data['ForcedConvection']['TrB1']
TrA2= data['ForcedConvection']['TrA2']
TrB2= data['ForcedConvection']['TrB2']
hrA1= data['ForcedConvection']['hrA1']
hrB1= data['ForcedConvection']['hrB1']
hrA2= data['ForcedConvection']['hrA2']
hrB2= data['ForcedConvection']['hrB2']
#
# SM additions: end of additions
#

# Template for the Fortran subroutine with placeholders for variables
fortran_template = """C
C UEPACTIVATIONVOL Subroutine --------------------------------------
C
C User subroutine to obtain volume fraction increase for element activation
C
      subroutine uepactivationvol(
     * lFlags,
     * epaName,
     * noel,
     * nElemNodes,
     * iElemNodes,
     * mcrd,
     * coordNodes,
     * uNodes,
     * kstep,
     * kinc,
     * time,
     * dtime,
     * temp,
     * npredef,
     * predef,
     * nsvars,
     * svars,
     * sol,
     * solinc,
     * volFract,
     * nVolumeAddEvents,
     * volFractAdded,
     * csiAdded,
     * ori,
     * eigenstrains)     
C
      include 'aba_param.inc'
C
      dimension   
     * lFlags(*),
     * iElemNodes(nElemNodes),
     * coordNodes(mcrd,nElemNodes),
     * uNodes(mcrd,nElemNodes),
     * time(2),
     * svars(nsvars,2),
     * temp(2,nElemNodes),
     * predef(2,npredef,nElemNodes),
     * sol(nElemNodes),
     * solinc(nElemNodes),
     * volFract(*),
     * volFractAdded(*),
     * csiAdded(3,*),
     * ori(3,3),
     * eigenstrains(*)

      character*80 epaName
C
      parameter ( zero = 0.d0, one = 1.d0 )
      
C     -------------------------------------------------------------
      
      PreHeatingTime		= {PreHeatingTime} 
      
      depLength            = {depLength}

      emissSubsDep          = {emissSubsDep}           ! Emissivity of substrate during deposition
      ambientTemp           = {ambientTemp}            ! Ambient temperature
      stefBoltzman          = 5.669d-08                ! Stefan-Boltzmann constant

      pltWidth              = {baseWidth}              ! Width of the base plate
      pltLength             = {baseLength}             ! Length of the base plate
      pltThick              = {baseThick}              ! Thickness of the base plate
      
      pltRear               =  0.0d0                   ! Rear position of the base plate
      pltCent               =  0.0d0                   ! Center position of the base plate
      pltBot                =  0.0d0                   ! Bottom position of the base plate
      
      pltFront              = pltRear + pltLength      ! Front position of the base plate
      pltLeft               = pltCent - pltWidth/2.0d0 ! Left position of the base plate
      pltRight              = pltCent + pltWidth/2.0d0 ! Right position of the base plate
      pltTop                = pltBot + pltThick        ! Top position of the base plate

      subsWidth             = {subsWidth}                  ! Width of the substrate
      subsLength            = {subsLength}                  ! Length of the substrate
      subsThick             = {subsThick}                   ! Thickness of the substrate

      subsRear              = pltRear + (pltLength-subsLength)/2.0d0 ! Rear position of the substrate
      subsCent              = pltCent                  ! Center position of the substrate
      subsBot               = pltTop                   ! Bottom position of the substrate
            
      subsFront             = subsRear + subsLength    ! Front position of the substrate
      subsLeft              = subsCent - subsWidth/2.0d0 ! Left position of the substrate
      subsRight             = subsCent + subsWidth/2.0d0 ! Right position of the substrate
      subsTop               = subsBot + subsThick      ! Top position of the substrate

      depTrkWidth           = {depTrkWidth}                   ! Width of the deposition track
      depTrkThick           = {depTrkThick}                   ! Thickness of the deposition track
      depTrksPerLyr         = {depTrksPerLyr}                       ! Number of tracks per layer in deposition
      depNoOfLyrs           = {depNoOfLyrs}                        ! Number of layers in deposition
      
      depElemHt             = {depTrkThick}                   ! Height of each deposition element
      depElemWid            = {depTrkWidth}                   ! Width of each deposition element
      depElemLen            = {PartitionThick}                   ! Length of each deposition element
      depElemPerLayer       = depTrkThick / depElemHt  ! Number of elements per layer through thickness

      depWidth              = depTrkWidth * depTrksPerLyr ! Total width of deposition
      depThick              = depTrkThick * depNoOfLyrs   ! Total thickness of deposition
      
      depCent               = subsCent                  ! Center of the deposition
      depLeft               = depCent - depWidth/2.0d0 ! Left position of the deposition
      depRight              = depCent + depWidth/2.0d0 ! Right position of the deposition
      
      UndepLengthRear       =  (pltLength-depLength)/2
      UndepLengthFront      =  (pltLength-depLength)/2
      
      depPltRr              = pltRear + UndepLengthRear         ! Rear position of the deposition on the base plate
      depPltFrt             = pltFront - UndepLengthFront        ! Front position of the deposition on the base plate
      
      depSubsRr             = subsRear                 ! Rear position of the deposition on the substrate
      depSubsFrt            = subsFront                ! Front position of the deposition on the substrate
      depSubsBot            = subsTop                  ! Bottom position of the deposition on the substrate
      depSubsTop            = depSubsBot + depThick    ! Top position of the deposition on the substrate
            
      sprayNzzlVel          = {sprayNzzlVel}                   ! Velocity of the nozzle
      sprayNzzlAccel        = {sprayNzzlAccel}                   ! Acceleration of the nozzle
      
      sprayFrmsPerTrk       = {sprayFrmsPerTrk}                       ! Number of frames per track in the spray process
      
     
   
      sprayTimePerTrk       = sprayNzzlVel/sprayNzzlAccel + depLength/sprayNzzlVel          ! Time per track for spraying, calculated based on nozzle velocity, acceleration, and distance
      sprayTimePerFrm       = sprayTimePerTrk / sprayFrmsPerTrk                             ! Time per frame in the spray process, derived from time per track and number of frames per track
      sprayTimePerLyr       = depTrksPerLyr * sprayTimePerTrk                               ! Total time per layer, based on the number of tracks per layer and time per track
      
      sprayX0               = depLeft + depTrkWidth/2.0d0                                   ! Initial X-coordinate for spraying, set to the middle of the deposition width
      sprayZ0               = depPltRr                                                      ! Initial Z-coordinate for spraying, set to the rear position relative to the platform

C SM corrected hard coded eig values (8/25/2025)
      eig11                 =  {eig11}
      eig22                 =  {eig22}
      eig33                 =  {eig33}
      eig12                 =  zero
      eig23                 =  zero
      eig31                 =  zero
C End of SM correction (8/25/2025)
      
      
C     -------------------------------------------------------------
      
      tTol                  = 0.001d0            ! Tolerance for time
      xTol                  = depElemWid/2.0d0   ! Tolerance for x-coordinate (half of element width)
      yTol                  = depElemHt/2.0d0    ! Tolerance for y-coordinate (half of element height)
      zTol                  = depElemLen/2.0d0   ! Tolerance for z-coordinate (half of element length)


      wTrk                  = depTrkWidth         ! Width of the track
      hTrk                  = depTrkThick         ! Thickness of the track
      trksPerLyr            = depTrksPerLyr       ! Number of tracks per layer

      emiss                 = emissSubsDep        ! Emissivity of the substrate deposition
      boltz                 = stefBoltzman        ! Stefan-Boltzmann constant
      Tamb                  = ambientTemp         ! Ambient temperature

      frmsPerTrk            = sprayFrmsPerTrk     ! Number of frames per track in the spray process
      v                     = sprayNzzlVel        ! Velocity of the spray nozzle
      a                     = sprayNzzlAccel      ! Acceleration of the spray nozzle
      L                     = depLength   ! Longitudinal distance of the spray nozzle
      tPerTrk               = sprayTimePerTrk     ! Time per track in the spray process
      tPerFrm               = sprayTimePerFrm     ! Time per frame in the spray process

      x0                    = sprayX0             ! Initial X-coordinate for spraying
      z0                    = sprayZ0             ! Initial Z-coordinate for spraying
     
      t_step                = time(1)*1.d0        ! Frame time (converted to double precision)


      frmTot                = anint(t_step / tPerFrm) ! Total number of frames, rounded to nearest integer
      trkTot                = ceiling(frmTot * 1.d0 / frmsPerTrk) ! Total number of tracks, rounded up
      lyr                   = ceiling(trkTot * 1.d0 / trksPerLyr) ! Number of layers, rounded up
      trkLyr                = trkTot - trksPerLyr * (lyr - 1)      ! Track number within the current layer
      frmTrk                = frmTot - frmsPerTrk * (trkTot - 1)   ! Frame number within the current track
      tTrk                  = frmTrk * tPerFrm                     ! Time associated with the current track

      x0_trk  = x0 + (trkLyr-1) * wTrk             ! X-coordinate for the current track
      z0_trk  = z0 + ((1 + (-1)**trkLyr) / 2.0d0) * L ! Z-coordinate for the current track, alternating pattern
      d_trk   = anint((-1)**(trkLyr-1))            ! Direction indicator, alternating with each layer

      
      xn      = x0_trk
      
C     This part calculates the position of the nozzle along the long-rastering
C     (z) direction, based on the current time.
      
      t0  = 0.0d0 ! ??? what is the purpose here?
      t1  = v/a
      t2  = L/v
      t3  = (v/a + L/v)
    
      if      ((t0 - tTol) .lt. tTrk .and. tTrk .lt. (t1 + tTol)) then
          zn      = z0_trk + d_trk * 0.5d0 * a * (tTrk - t0)**2 ! position calculation during nozzle acceleration
          NozzlaStatus = 1
      else if ((t1 - tTol) .lt. tTrk .and. tTrk .lt. (t2 + tTol)) then
          z1      = z0_trk + d_trk * 0.5d0 * a * (t1 - t0)**2
          zn      = z1 + d_trk * v * (tTrk - t1)
          NozzlaStatus = 0
      else if ((t2 - tTol) .lt. tTrk .and. tTrk .lt. (t3 + tTol)) then
          z1      = z0_trk + d_trk * 0.5d0 * a * (t1 - t0)**2
          z2      = z1 + d_trk * v * (t2 - t1)
          zn      = z2 + d_trk * ( v*(tTrk - t2) - 
     *                0.5d0 * a * (tTrk - t2)**2 )     
          NozzlaStatus = -1     
      end if
      

      trkSubsTop    = subsTop + lyr * hTrk
      trkSubsBot    = subsTop + (lyr - 1) * hTrk
      trkPltTop     = pltTop + lyr * hTrk
      trkPltBot     = pltTop + (lyr - 1) * hTrk 
     
      trkRight      = xn + wTrk / 2.0d0 ! calculates right position of current track
      trkLeft       = xn - wTrk / 2.0d0 ! calculates left position of current track
      

      
      if     (d_trk .GT. zero) then
      
          trkPltNewRr   = depPltRr
          trkPltNewFrt  = zn
          trkPltOldRr   = zn
          trkPltOldFrt  = depPltFrt
          
          trkSubsNewRr  = depSubsRr
          trkSubsNewFrt = zn
          trkSubsOldRr  = zn
          trkSubsOldFrt = depSubsFrt
          
      elseif (d_trk .LT. zero) then
      
          trkPltNewRr   = zn
          trkPltNewFrt  = depPltFrt
          trkPltOldRr   = depPltRr
          trkPltOldFrt  = zn
          
          trkSubsNewRr  = zn
          trkSubsNewFrt = depSubsFrt
          trkSubsOldRr  = depSubsRr
          trkSubsOldFrt = zn
          
      end if

      if     (trkSubsNewFrt .GT. depSubsFrt) then
      
          trkSubsNewFrt   = depSubsFrt
          
      end if  

      if     (trkSubsNewRr .LT. depSubsRr) then
      
          trkSubsNewRr   = depSubsRr
          
      end if        

C     -------------------------------------------------------------
C
      if  ( 
C         This section activates the elements in the section of the track 
C         (new track) that is currently being laid on the base plate.
!
     *    CoordNodes(2,1) .lt. trkPltTop       + yTol .and.
     *    CoordNodes(2,2) .lt. trkPltTop       + yTol .and.
     *    CoordNodes(2,3) .lt. trkPltTop       + yTol .and.
     *    CoordNodes(2,4) .lt. trkPltTop       + yTol .and.
     *    CoordNodes(2,5) .lt. trkPltTop       + yTol .and.
     *    CoordNodes(2,6) .lt. trkPltTop       + yTol .and.
     *    CoordNodes(2,7) .lt. trkPltTop       + yTol .and.
     *    CoordNodes(2,8) .lt. trkPltTop       + yTol .and.
!
     *    CoordNodes(2,1) .gt. trkPltBot       - yTol .and.
     *    CoordNodes(2,2) .gt. trkPltBot       - yTol .and.
     *    CoordNodes(2,3) .gt. trkPltBot       - yTol .and.
     *    CoordNodes(2,4) .gt. trkPltBot       - yTol .and.
     *    CoordNodes(2,5) .gt. trkPltBot       - yTol .and.
     *    CoordNodes(2,6) .gt. trkPltBot       - yTol .and.
     *    CoordNodes(2,7) .gt. trkPltBot       - yTol .and.
     *    CoordNodes(2,8) .gt. trkPltBot       - yTol .and.
!     
     *    CoordNodes(1,1) .lt. trkRight     + xTol .and.
     *    CoordNodes(1,2) .lt. trkRight     + xTol .and.
     *    CoordNodes(1,3) .lt. trkRight     + xTol .and.
     *    CoordNodes(1,4) .lt. trkRight     + xTol .and.
     *    CoordNodes(1,5) .lt. trkRight     + xTol .and.
     *    CoordNodes(1,6) .lt. trkRight     + xTol .and.
     *    CoordNodes(1,7) .lt. trkRight     + xTol .and.
     *    CoordNodes(1,8) .lt. trkRight     + xTol .and.
!     
     *    CoordNodes(1,1) .gt. trkLeft      - xTol .and.
     *    CoordNodes(1,2) .gt. trkLeft      - xTol .and.
     *    CoordNodes(1,3) .gt. trkLeft      - xTol .and.
     *    CoordNodes(1,4) .gt. trkLeft      - xTol .and.
     *    CoordNodes(1,5) .gt. trkLeft      - xTol .and.
     *    CoordNodes(1,6) .gt. trkLeft      - xTol .and.
     *    CoordNodes(1,7) .gt. trkLeft      - xTol .and.
     *    CoordNodes(1,8) .gt. trkLeft      - xTol .and.
!     
     *    CoordNodes(3,1) .lt. trkPltNewFrt    + zTol .and.
     *    CoordNodes(3,2) .lt. trkPltNewFrt    + zTol .and.
     *    CoordNodes(3,3) .lt. trkPltNewFrt    + zTol .and.
     *    CoordNodes(3,4) .lt. trkPltNewFrt    + zTol .and.
     *    CoordNodes(3,5) .lt. trkPltNewFrt    + zTol .and.
     *    CoordNodes(3,6) .lt. trkPltNewFrt    + zTol .and.
     *    CoordNodes(3,7) .lt. trkPltNewFrt    + zTol .and.
     *    CoordNodes(3,8) .lt. trkPltNewFrt    + zTol .and.
!     
     *    CoordNodes(3,1) .gt. trkPltNewRr     - zTol .and.
     *    CoordNodes(3,2) .gt. trkPltNewRr     - zTol .and.
     *    CoordNodes(3,3) .gt. trkPltNewRr     - zTol .and.
     *    CoordNodes(3,4) .gt. trkPltNewRr     - zTol .and.
     *    CoordNodes(3,5) .gt. trkPltNewRr     - zTol .and.
     *    CoordNodes(3,6) .gt. trkPltNewRr     - zTol .and.
     *    CoordNodes(3,7) .gt. trkPltNewRr     - zTol .and.
     *    CoordNodes(3,8) .gt. trkPltNewRr     - zTol
     *    ) then
     
          volFractAdded(1)  = one 
          eigenstrains(1)   = eig11
          eigenstrains(2)   = eig22
          eigenstrains(3)   = eig33
          eigenstrains(4)   = eig12
          eigenstrains(5)   = eig23
          eigenstrains(6)   = eig31
          
          
      elseif
     *    ( 
C         This section activates the elements in the section of the track 
C         (new track) that is currently being laid on the substrate.
     *    CoordNodes(2,1) .lt. trkSubsTop       + yTol .and.
     *    CoordNodes(2,2) .lt. trkSubsTop       + yTol .and.
     *    CoordNodes(2,3) .lt. trkSubsTop       + yTol .and.
     *    CoordNodes(2,4) .lt. trkSubsTop       + yTol .and.
     *    CoordNodes(2,5) .lt. trkSubsTop       + yTol .and.
     *    CoordNodes(2,6) .lt. trkSubsTop       + yTol .and.
     *    CoordNodes(2,7) .lt. trkSubsTop       + yTol .and.
     *    CoordNodes(2,8) .lt. trkSubsTop       + yTol .and.
!     
     *    CoordNodes(2,1) .gt. trkSubsBot       - yTol .and.
     *    CoordNodes(2,2) .gt. trkSubsBot       - yTol .and.
     *    CoordNodes(2,3) .gt. trkSubsBot       - yTol .and.
     *    CoordNodes(2,4) .gt. trkSubsBot       - yTol .and.
     *    CoordNodes(2,5) .gt. trkSubsBot       - yTol .and.
     *    CoordNodes(2,6) .gt. trkSubsBot       - yTol .and.
     *    CoordNodes(2,7) .gt. trkSubsBot       - yTol .and.
     *    CoordNodes(2,8) .gt. trkSubsBot       - yTol .and.
!     
     *    CoordNodes(1,1) .lt. trkRight     + xTol .and.
     *    CoordNodes(1,2) .lt. trkRight     + xTol .and.
     *    CoordNodes(1,3) .lt. trkRight     + xTol .and.
     *    CoordNodes(1,4) .lt. trkRight     + xTol .and.
     *    CoordNodes(1,5) .lt. trkRight     + xTol .and.
     *    CoordNodes(1,6) .lt. trkRight     + xTol .and.
     *    CoordNodes(1,7) .lt. trkRight     + xTol .and.
     *    CoordNodes(1,8) .lt. trkRight     + xTol .and.
!     
     *    CoordNodes(1,1) .gt. trkLeft      - xTol .and.
     *    CoordNodes(1,2) .gt. trkLeft      - xTol .and.
     *    CoordNodes(1,3) .gt. trkLeft      - xTol .and.
     *    CoordNodes(1,4) .gt. trkLeft      - xTol .and.
     *    CoordNodes(1,5) .gt. trkLeft      - xTol .and.
     *    CoordNodes(1,6) .gt. trkLeft      - xTol .and.
     *    CoordNodes(1,7) .gt. trkLeft      - xTol .and.
     *    CoordNodes(1,8) .gt. trkLeft      - xTol .and.
!     
     *    CoordNodes(3,1) .lt. trkSubsNewFrt    + zTol .and.
     *    CoordNodes(3,2) .lt. trkSubsNewFrt    + zTol .and.
     *    CoordNodes(3,3) .lt. trkSubsNewFrt    + zTol .and.
     *    CoordNodes(3,4) .lt. trkSubsNewFrt    + zTol .and.
     *    CoordNodes(3,5) .lt. trkSubsNewFrt    + zTol .and.
     *    CoordNodes(3,6) .lt. trkSubsNewFrt    + zTol .and.
     *    CoordNodes(3,7) .lt. trkSubsNewFrt    + zTol .and.
     *    CoordNodes(3,8) .lt. trkSubsNewFrt    + zTol .and.
!     
     *    CoordNodes(3,1) .gt. trkSubsNewRr     - zTol .and.
     *    CoordNodes(3,2) .gt. trkSubsNewRr     - zTol .and.
     *    CoordNodes(3,3) .gt. trkSubsNewRr     - zTol .and.
     *    CoordNodes(3,4) .gt. trkSubsNewRr     - zTol .and.
     *    CoordNodes(3,5) .gt. trkSubsNewRr     - zTol .and.
     *    CoordNodes(3,6) .gt. trkSubsNewRr     - zTol .and.
     *    CoordNodes(3,7) .gt. trkSubsNewRr     - zTol .and.
     *    CoordNodes(3,8) .gt. trkSubsNewRr     - zTol
     *    ) then
          
          volFractAdded(1)  = one
          eigenstrains(1)   = eig11
          eigenstrains(2)   = eig22
          eigenstrains(3)   = eig33
          eigenstrains(4)   = eig12
          eigenstrains(5)   = eig23
          eigenstrains(6)   = eig31
          
          else
          
C         Any elements outside of the above sections should be left off.
          volFractAdded(1)  = zero
          eigenstrains(1)   = zero
          eigenstrains(2)   = zero
          eigenstrains(3)   = zero
          eigenstrains(4)   = zero
          eigenstrains(5)   = zero
          eigenstrains(6)   = zero
      
      end if 

      !WRITE(6, *) 'trkSubsTop = ', trkSubsTop 
      !WRITE(6, *) 'trkSubsBot = ', trkSubsBot 
      !WRITE(6, *) 'trkRight = ', trkRight   	
      !WRITE(6, *) 'trkLeft = ', trkLeft  
      !WRITE(6, *) 'trkSubsNewFrt = ', trkSubsNewFrt  
      !WRITE(6, *) 'trkSubsNewRr = ', trkSubsNewRr  

      !WRITE(6, *) 'trkPltTop = ', trkPltTop 
      !WRITE(6, *) 'trkPltBot = ', trkPltBot 
      !WRITE(6, *) 'trkRight = ', trkRight   	
      !WRITE(6, *) 'trkLeft = ', trkLeft  
      !WRITE(6, *) 'trkPltNewFrt = ', trkPltNewFrt  
      !WRITE(6, *) 'trkPltNewRr = ', trkPltNewRr  
      
      !WRITE(6, *) 'lyr = ', lyr   	
      !WRITE(6, *) 'trkLyr = ', trkLyr  
      !WRITE(6, *) 'frmTrk = ', frmTrk  
!      WRITE(6, *) 'ACTIVE = ', trkSubsTop, trkSubsBot,  trkRight,  trkLeft, trkSubsNewFrt,
!     * trkSubsNewRr, trkPltTop,  trkPltBot, trkPltNewFrt, trkPltNewRr
!     * t_step, lyr, trkLyr, frmTrk 
!      WRITE(6, *) 'Active = ', t_step, lyr, trkLyr, frmTrk        
      return
      end
      
 
C      
C
C UEPACTIVATIONVOL Subroutine --------------------------------------
C
C User subroutine to obtain volume fraction increase for element activation
C
C DFLUX Subroutine -------------------------------------------------
C
      SUBROUTINE DFLUX(FLUX,SOL,KSTEP,KINC,TIME,NOEL,NPT,COORDS,
     1 JLTYP,TEMP,PRESS,SNAME)
C
      INCLUDE 'ABA_PARAM.INC'

      DIMENSION COORDS(3),FLUX(2),TIME(2)
      CHARACTER*80 SNAME

      parameter ( zero = 0.d0, one = 1.d0 )
      pi 					= 3.14159265358979323846
C     -------------------------------------------------------------
C	#	  # 
C	#  UNITS:
C	#  - LENGTH: 	mm
C	#  - TIME: 		s
C	#  - MASS: 		kg
C	#  - TEMP:		K
C	#  - FORCE:		mN
C	#  - PRESSURE: 	kPa
C	#  - ENERGY: 	uJ
C	#  - POWER: 	uW

C SM Addition: 8/29/2025
      TrA1 = {TrA1}
      TrB1 = {TrB1}
      TrA2 = {TrA2}
      TrB2 = {TrB2}
	  hrA1 = {hrA1}
      hrB1 = {hrB1}
      hrA2 = {hrA2}
      hrB2 = {hrB2}
C End of SM Addition: 8/29/2025

      PreHeatingTime		= {PreHeatingTime}     
      
      P_deposition		    = {P_deposition}
      P_preheat             = {P_preheat}
      r0					= {r0}
      emissSubsDep          = {emissSubsDep}           ! Emissivity of substrate during deposition
      ambientTemp           = {ambientTemp}            ! Ambient temperature
      stefBoltzman          = 5.669d-08  

      subsWidth             = {subsWidth}                  ! Width of the substrate
      subsLength            = {subsLength}                  ! Length of the substrate
      subsThick             = {subsThick}                   ! Thickness of the substrate
      
      pltWidth              = {baseWidth}              ! Width of the base plate
      pltLength             = {baseLength}             ! Length of the base plate
      pltThick              = {baseThick}              ! Thickness of the base plate
      
   
      pltRear               =  0.0d0
      pltCent               =  0.0d0
      pltBot                =  0.0d0
      
      pltFront              = pltRear + pltLength
      pltLeft               = pltCent - pltWidth/2.0d0
      pltRight              = pltLeft + pltWidth
      pltTop                = pltBot + pltThick

      subsWidth             = {subsWidth}                  ! Width of the substrate
      subsLength            = {subsLength}                  ! Length of the substrate
      subsThick             = {subsThick}                   ! Thickness of the substrate

      subsRear              = pltRear + (pltLength-subsLength)/2.0d0 ! Rear position of the substrate
      subsCent              = pltCent
      subsBot			    = pltTop
            
      subsFront			    = subsRear + subsLength
      subsLeft 			    = subsCent - subsWidth/2.0d0
      subsRight 			= subsLeft + subsWidth
      subsTop			    = subsBot + subsThick

      depLength             = {depLength}


      depTrkWidth           = {depTrkWidth}                   ! Width of the deposition track
      depTrkThick           = {depTrkThick}                   ! Thickness of the deposition track
      depTrksPerLyr         = {depTrksPerLyr}                       ! Number of tracks per layer in deposition
      depNoOfLyrs           = {depNoOfLyrs}                        ! Number of layers in deposition
      
      depElemHt             = {depTrkThick}                   ! Height of each deposition element
      depElemWid            = {depTrkWidth}                   ! Width of each deposition element
      depElemLen            = {PartitionThick}                   ! Length of each deposition element
      depElemPerLayer       = depTrkThick / depElemHt  ! Number of elements per layer through thickness

      depWidth 			    = depTrkWidth * depTrksPerLyr
      depThick 			    = depTrkThick * depNoOfLyrs
      depCent               = subsCent
      
      depLeft               = depCent - depWidth/2.0d0
      depRight              = depLeft + depWidth
      
      UndepLengthRear       = (pltLength-depLength)/2
      UndepLengthFront      = (pltLength-depLength)/2
       
      
      depPltRr              = pltRear + UndepLengthRear
      depPltFrt             = pltFront - UndepLengthFront  
      
      depSubsRr			    = subsRear
      depSubsFrt 			= subsFront
      depSubsBot			= subsTop
      depSubsTop 			= depSubsBot + depThick
            
      sprayNzzlVel          = {sprayNzzlVel}
      sprayNzzlAccel        = {sprayNzzlAccel}
C      
C This piece of code implements a waiting period to the PreHeat Step 
C Implemented by Salih Duran
C The durations etc are hardcoded
C
      t_step                 = time(1)*1.d0 
      t_total                = time(2)*1.d0
      t_0                    = 1000               ! Hot Plate initialization ~ 2000 s
      t_1                    = 0.1                ! time for step1                      see keynote
      t_2                    = 0.1                ! time for step2                      see keynote
      t_3                    = 0.1                ! time for step2.1                    see keynote      
      t_4                    = t_0+t_1+t_2+t_3    ! time for step1+ step2 and step2.1   initialization 
      t_5                    = t_0+PreHeatingTime  
 
      if      (t_total .gt. (t_0+t_1) .AND. t_total .lt. (t_0+t_1+t_2)) then
          t_raster	  = t_total-(t_0+t_1)
      end if 

      if      (t_total .gt. (t_4))  then
          t_raster	  = t_total-(t_4)
      end if      
 
      if      (t_total .gt. (t_5))  then
          t_raster	  = t_total-(t_5)
      end if   
      
      if      (t_total .gt. (t_0) .AND. t_total .lt. (t_0+t_1)) then
		  sprayNzzlVel          = 1.000d-6
          sprayNzzlAccel        = 1.000d-6  
      end if       
C
C End of additions for the Preheat Step
C 

C
C This piece of code sets the begining and end times of each step of the process
C Added by Sinan Muftu
C
        TimeTotal       = HotplateSSTime + {PreHeatingTime} + {DepositionTime} + {CoolingTime1} + {ReleaseFixturesTime} + {CoolingTime2}

        TimeStep01Begin = 0.0d0
        TimeStep01End   = {HotplateSSTime}

        TimeStep02Begin = {HotplateSSTime}
        TimeStep02End   = {HotplateSSTime} + {PreHeatingTime}

        TimeStep03Begin = {HotplateSSTime} + {PreHeatingTime}
        TimeStep03End   = {HotplateSSTime} + {PreHeatingTime} + {DepositionTime}

        TimeStep04Begin = {HotplateSSTime} + {PreHeatingTime} + {DepositionTime}
        TimeStep04End   = {HotplateSSTime} + {PreHeatingTime} + {DepositionTime} + {CoolingTime1}

        TimeStep05Begin = {HotplateSSTime} + {PreHeatingTime} + {DepositionTime} + {CoolingTime1}
        TimeStep05End   = {HotplateSSTime} + {PreHeatingTime} + {DepositionTime} + {CoolingTime1} + {ReleaseFixturesTime}

        TimeStep06Begin = {HotplateSSTime} + {PreHeatingTime} + {DepositionTime} + {CoolingTime1} + {ReleaseFixturesTime}
        TimeStep06End   = {HotplateSSTime} + {PreHeatingTime} + {DepositionTime} + {CoolingTime1} + {ReleaseFixturesTime} + {CoolingTime2} 
C        
C End of setting the begining and end times of each step of the process
C      
      sprayFrmsPerTrk	    = {sprayFrmsPerTrk}
      
      sprayTimePerTrk       = sprayNzzlVel/sprayNzzlAccel + depLength/sprayNzzlVel
      sprayTimePerFrm 	    = sprayTimePerTrk / sprayFrmsPerTrk
      sprayTimePerLyr       = depTrksPerLyr * sprayTimePerTrk
      
      sprayX0               = depLeft + depTrkWidth/2.0d0
      sprayZ0               = depPltRr
      
C SM corrected hard coded eig values (8/25/2025)
      eig11                 =  {eig11}
      eig22                 =  {eig22}
      eig33                 =  {eig33}
      eig12                 =  zero
      eig23                 =  zero
      eig31                 =  zero
      
C     -------------------------------------------------------------
      
      tTol                  = 0.001d0
      xTol                  = depElemWid/2.0d0
      yTol                  = depElemHt/2.0d0
      zTol                  = depElemLen/2.0d0

      wTrk                  = depTrkWidth
      hTrk                  = depTrkThick
      trksPerLyr            = depTrksPerLyr
      
      emiss                 = emissSubsDep
      boltz                 = stefBoltzman
      Tamb                  = ambientTemp
      
      frmsPerTrk            = sprayFrmsPerTrk
      v                     = sprayNzzlVel
      a                     = sprayNzzlAccel
      L                     = depLength
      tPerTrk               = sprayTimePerTrk
      tPerFrm               = sprayTimePerFrm
      
      x0                    = sprayX0
      z0                    = sprayZ0

   
      frmTot                = anint(t_raster / tPerFrm)
      trkTot                = ceiling(frmTot * 1.d0 / frmsPerTrk)
      lyr                   = ceiling(trkTot * 1.d0 / trksPerLyr)
      trkLyr                = trkTot - trksPerLyr * (lyr - 1)  
      frmTrk                = frmTot - frmsPerTrk * (trkTot - 1)
      tTrk                  = frmTrk * tPerFrm
    
      x0_trk  = x0 + (trkLyr-1) * wTrk
      z0_trk  = z0 + ((1 + (-1)**trkLyr) / 2.0d0) * L
      d_trk   = anint((-1)**(trkLyr-1))
      
      xn      = x0_trk
      
C     This part calculates the position of the nozzle along the long-rastering
C     (z) direction, based on the current time.

      t0  = 0.0d0
      t1  = v/a
      t2  = L/v
      t3  = (v/a + L/v)
    
      if      ((t0 - tTol) .lt. tTrk .and. tTrk .lt. (t1 + tTol)) then
          zn      = z0_trk + d_trk * 0.5d0 * a * (tTrk - t0)**2
      else if ((t1 - tTol) .lt. tTrk .and. tTrk .lt. (t2 + tTol)) then
          z1      = z0_trk + d_trk * 0.5d0 * a * (t1 - t0)**2
          zn      = z1 + d_trk * v * (tTrk - t1)
      else if ((t2 - tTol) .lt. tTrk .and. tTrk .lt. (t3 + tTol)) then
          z1      = z0_trk + d_trk * 0.5d0 * a * (t1 - t0)**2
          z2      = z1 + d_trk * v * (t2 - t1)
          zn      = z2 + d_trk * ( v*(tTrk - t2) - 
     *                0.5d0 * a * (tTrk - t2)**2 )          
      end if
      
      if      (t_total .lt. t_5) then
          trkSubsTop    = subsTop
          trkSubsBot    = subsTop
          trkPltTop     = pltTop
          trkPltBot     = pltTop
      else
          trkSubsTop    = subsTop + lyr * hTrk
          trkSubsBot    = subsTop + (lyr - 1) * hTrk
          trkPltTop     = pltTop + lyr * hTrk
          trkPltBot     = pltTop + (lyr - 1) * hTrk          
      end if
      

      
      trkRight      = xn + wTrk / 2.0d0
      trkLeft       = xn - wTrk / 2.0d0
      
      
      if     (d_trk .GT. zero) then
      
          trkPltNewRr   = depPltRr
          trkPltNewFrt  = zn
          trkPltOldRr   = zn
          trkPltOldFrt  = depPltFrt

          trkSubsNewRr  = depSubsRr
          trkSubsNewFrt = zn
          trkSubsOldRr  = zn
          trkSubsOldFrt = depSubsFrt
          
      elseif (d_trk .LT. zero) then
      
          trkPltNewRr   = zn
          trkPltNewFrt  = depPltFrt
          trkPltOldRr   = depPltRr
          trkPltOldFrt  = zn



          
          trkSubsNewRr  = zn
          trkSubsNewFrt = depSubsFrt
          trkSubsOldRr  = depSubsRr
          trkSubsOldFrt = zn
          
      end if
      
C       if     (d_trk .GT. zero) then
C           trkNewFrt  = zn
C           trkNewRr   = depPltRr
C           trkOldFrt  = depPltFrt
C           trkOldRr   = zn
C       elseif (d_trk .LT. zero) then
C           trkNewFrt  = depPltFrt
C           trkNewRr   = zn
C           trkOldFrt  = zn
C           trkOldRr   = depPltRr
C       end if

C     -------------------------------------------------------------
C     This part applies the nozzle heat flux to the top, exposed surfaces of 
C     the plate, substrate, and deposit.  These surfaces are broken down 
C     into the regions specified below, based on their coordinate ranges.

      x = COORDS(1)
      y = COORDS(2)
      z = COORDS(3)
      JLTYP = 0
      
C       if ((t1 - tTol) .lt. tTrk .and. tTrk .lt. (t2 + tTol)) then 
          if (
C                .true.
c
C               PLATE TOP - LEFT  OF FRONT DEP
     *         ( ((pltLeft       - xTol) .LT. x .AND. x .LT. (depLeft       + xTol)) .AND.
     *           ((pltTop        - yTol) .LT. y .AND. y .LT. (pltTop        + yTol)) .AND.
     *           ((subsFront     - zTol) .LT. z .AND. z .LT. (pltFront      + zTol))
     *         ) .OR.
C               PLATE TOP - RIGHT OF FRONT DEP
     *         ( ((depRight      - xTol) .LT. x .AND. x .LT. (pltRight      + xTol)) .AND.
     *           ((pltTop        - yTol) .LT. y .AND. y .LT. (pltTop        + yTol)) .AND.
     *           ((subsFront     - zTol) .LT. z .AND. z .LT. (pltFront      + zTol))
     *         ) .OR.
C               PLATE TOP - LEFT  OF REAR DEP
     *         ( ((pltLeft       - xTol) .LT. x .AND. x .LT. (depLeft       + xTol)) .AND.
     *           ((pltTop        - yTol) .LT. y .AND. y .LT. (pltTop        + yTol)) .AND.
     *           ((pltRear       - zTol) .LT. z .AND. z .LT. (subsRear      + zTol))
     *         ) .OR.
C               PLATE TOP - RIGHT OF REAR DEP
     *         ( ((depRight      - xTol) .LT. x .AND. x .LT. (pltRight      + xTol)) .AND.
     *           ((pltTop        - yTol) .LT. y .AND. y .LT. (pltTop        + yTol)) .AND.
     *           ((pltRear       - zTol) .LT. z .AND. z .LT. (subsRear      + zTol))
     *         ) .OR.
C               PLATE TOP - LEFT  OF SUBSTRATE
     *         ( ((pltLeft       - xTol) .LT. x .AND. x .LT. (subsLeft      + xTol)) .AND.
     *           ((pltTop        - yTol) .LT. y .AND. y .LT. (pltTop        + yTol)) .AND.
     *           ((subsRear      - zTol) .LT. z .AND. z .LT. (subsFront     + zTol))
     *         ) .OR.
C               PLATE TOP - RIGHT OF SUBSTRATE
     *         ( ((subsRight     - xTol) .LT. x .AND. x .LT. (pltRight      + xTol)) .AND.
     *           ((pltTop        - yTol) .LT. y .AND. y .LT. (pltTop        + yTol)) .AND.
     *           ((subsRear      - zTol) .LT. z .AND. z .LT. (subsFront     + zTol))
     *         ) .OR.
C               PLATE TOP - REAR OF DEP
     *         ( ((depLeft       - xTol) .LT. x .AND. x .LT. (depRight      + xTol)) .AND.
     *           ((pltTop        - yTol) .LT. y .AND. y .LT. (pltTop        + yTol)) .AND.
     *           ((pltRear       - zTol) .LT. z .AND. z .LT. (depPltRr      + zTol))
     *         ) .OR.
C               PLATE TOP - FRONT OF DEP
     *         ( ((depLeft       - xTol) .LT. x .AND. x .LT. (depRight      + xTol)) .AND.
     *           ((pltTop        - yTol) .LT. y .AND. y .LT. (pltTop        + yTol)) .AND.
     *           ((depPltFrt     - zTol) .LT. z .AND. z .LT. (pltFront      + zTol))
     *         ) .OR.
c
C               SUBS - REAR VERTICAL FACE
     *         ( ((subsLeft      - xTol) .LT. x .AND. x .LT. (subsRight     + xTol)) .AND.
     *           ((subsBot       - yTol) .LT. y .AND. y .LT. (subsTop       + yTol)) .AND.
     *           ((subsRear      - zTol) .LT. z .AND. z .LT. (subsRear      + zTol))
     *         ) .OR.
C               SUBS - FRONT VERTICAL FACE
     *         ( ((subsLeft      - xTol) .LT. x .AND. x .LT. (subsRight     + xTol)) .AND.
     *           ((subsBot       - yTol) .LT. y .AND. y .LT. (subsTop       + yTol)) .AND.
     *           ((subsFront     - zTol) .LT. z .AND. z .LT. (subsFront     + zTol))
     *         ) .OR.
C               SUBS - TOP LEFT OF DEPOSIT
     *         ( ((subsLeft      - xTol) .LT. x .AND. x .LT. (depLeft       + xTol)) .AND.
     *           ((subsTop       - yTol) .LT. y .AND. y .LT. (subsTop       + yTol)) .AND.
     *           ((subsRear      - zTol) .LT. z .AND. z .LT. (subsFront     + zTol))
     *         ) .OR.
c               SUBS - TOP RIGHT OF DEPOSIT
     *         ( ((depRight      - xTol) .LT. x .AND. x .LT. (subsRight     + xTol)) .AND.
     *           ((subsTop       - yTol) .LT. y .AND. y .LT. (subsTop       + yTol)) .AND.
     *           ((subsRear      - zTol) .LT. z .AND. z .LT. (subsFront     + zTol))
     *         ) .OR.
C               SUBS - TOP IN FRONT OF DEP  -   Omitted depSubsFrt and subsFront are always same
C               causing heating of the corners in each layer
C     *         ( ((depLeft       - xTol) .LT. x .AND. x .LT. (depRight      + xTol)) .AND.
C     *           ((subsTop       - yTol) .LT. y .AND. y .LT. (subsTop       + yTol)) .AND.
C     *           ((depSubsFrt    - zTol) .LT. z .AND. z .LT. (subsFront     + zTol))
C     *         ) .OR.
C               SUBS - TOP IN REAR OF DEP   -   Omitted subsRear and depSubsRr are always same
C               causing heating of the corners in each layer
C     *         ( ((depLeft       - xTol) .LT. x .AND. x .LT. (depRight      + xTol)) .AND.
C     *           ((subsTop       - yTol) .LT. y .AND. y .LT. (subsTop       + yTol)) .AND.
C     *           ((subsRear      - zTol) .LT. z .AND. z .LT. (depSubsRr     + zTol))
C     *         ) .OR.
c
c               SUBS DEP - TOP LEFT (LAID)
     *         ( ((depLeft       - xTol) .LT. x .AND. x .LT. (trkLeft       + xTol)) .AND.
     *           ((trkSubsTop    - yTol) .LT. y .AND. y .LT. (trkSubsTop    + yTol)) .AND.
     *           ((depSubsRr     - zTol) .LT. z .AND. z .LT. (depSubsFrt    + zTol))
     *         ) .OR.
c               SUBS DEP - TRACK NEW (LAID)
     *         ( ((trkLeft       - xTol) .LT. x .AND. x .LT. (trkRight      + xTol)) .AND.
     *           ((trkSubsTop    - yTol) .LT. y .AND. y .LT. (trkSubsTop    + yTol)) .AND.
     *           ((trkSubsNewRr  - zTol) .LT. z .AND. z .LT. (trkSubsNewFrt + zTol))
     *         ) .OR.
c               SUBS DEP - TRACK OLD (UNLAID)
     *         ( ((trkLeft       - xTol) .LT. x .AND. x .LT. (trkRight      + xTol)) .AND.
     *           ((trkSubsBot    - yTol) .LT. y .AND. y .LT. (trkSubsBot    + yTol)) .AND.
     *           ((trkSubsOldRr  - zTol) .LT. z .AND. z .LT. (trkSubsOldFrt + zTol))
     *         ) .OR.
c               SUBS DEP - TOP RIGHT (UNLAID)
     *         ( ((trkRight      - xTol) .LT. x .AND. x .LT. (depRight      + xTol)) .AND.
     *           ((trkSubsBot    - yTol) .LT. y .AND. y .LT. (trkSubsBot    + yTol)) .AND.
     *           ((depSubsRr     - zTol) .LT. z .AND. z .LT. (depSubsFrt    + zTol))
     *         ) .OR.
c
c               PLATE DEP - TOP LEFT (LAID) - Rear - New Track is included here
     *         ( ((depLeft       - xTol) .LT. x .AND. x .LT. (trkRight       + xTol)) .AND.
     *           ((trkPltTop     - yTol) .LT. y .AND. y .LT. (trkPltTop     + yTol)) .AND.
     *           ((depPltRr      - zTol) .LT. z .AND. z .LT. (subsRear     + zTol))
     *         ) .OR.
c               PLATE DEP - TOP LEFT (LAID) - Front - New Track is included here
     *         ( ((depLeft       - xTol) .LT. x .AND. x .LT. (trkRight       + xTol)) .AND.
     *           ((trkPltTop     - yTol) .LT. y .AND. y .LT. (trkPltTop     + yTol)) .AND.
     *           ((subsFront      - zTol) .LT. z .AND. z .LT. (depPltFrt     + zTol))
     *         ) .OR.
c               PLATE DEP - TRACK OLD (UNLAID)
     *         ( ((trkLeft       - xTol) .LT. x .AND. x .LT. (trkRight      + xTol)) .AND.
     *           ((trkPltBot     - yTol) .LT. y .AND. y .LT. (trkPltBot     + yTol)) .AND.
     *           ((trkPltOldRr   - zTol) .LT. z .AND. z .LT. (trkPltOldFrt  + zTol)) .AND.
     *           ((subsFront   - zTol) .LT. z .AND. z .LT. (subsRear  + zTol))
     *         ) .OR.
c               PLATE DEP - TOP RIGHT (UNLAID) - Rear
     *         ( ((trkRight      - xTol) .LT. x .AND. x .LT. (depRight      + xTol)) .AND.
     *           ((trkPltBot     - yTol) .LT. y .AND. y .LT. (trkPltBot     + yTol)) .AND.
     *           ((depPltRr      - zTol) .LT. z .AND. z .LT. (subsRear     + zTol))
     *         ) .OR.
c               PLATE DEP - TOP RIGHT (UNLAID) - Front
     *         ( ((trkRight      - xTol) .LT. x .AND. x .LT. (depRight      + xTol)) .AND.
     *           ((trkPltBot     - yTol) .LT. y .AND. y .LT. (trkPltBot     + yTol)) .AND.
     *           ((subsFront      - zTol) .LT. z .AND. z .LT. (depPltFrt     + zTol))
     *         )
c
     *       ) then
     
C
C This Piece of code was used by Salih Duran for the action described in his comments
C     
!           This section is a gas heating step for 170s at standby location                
			  if      (t_total .lt. t_0+t_1) then
				  xn        = -175
				  zn        = -100
				  P         = 0
			  end if     
!           This section is for powder feeder activation for 24s at standby location     
			  if      (t_total .gt. (t_0+t_1+t_2) .AND. t_total .lt. (t_4)) then
				  xn        = -175
				  zn        = -100
				  P         = 0
			  end if	       
C
C The end of the wait period for Salih's addition
C   


              r = sqrt((x-xn)**2 + (z-zn)**2)
			  Tr    = TrA1 * exp(TrB1 * r) + TrA2 * exp(TrB2 * r); ! 
              hr    = hrA1 * exp(hrB1  * r) + hrA2  * exp(hrB2 * r); ! the one with the plot
              
			  if      (r .gt. 100.0) then
				  Tr      = 310.0
			  end if

			  if      (t_total .lt. t_0+t_1) then
				  hr	  = 80.0         
			  end if             

			  if      (t_total .gt. (t_0+t_1+t_2) .AND. t_total .lt. (t_4)) then
				  hr	  = 150.0
			  end if  
C
C This piece of code was added by Sinan Muftu to prevent any type of heating during the PreHeating Period
C
               if (t_total.ge.TimeStep02Begin .AND. t_total.le.TimeStep02End) then
                   P  = P_preheat
                   hr = 10.0
               elseif (t_total.ge.TimeStep03Begin .AND. t_total.le.TimeStep03End) then
                   P  = P_deposition
               end if                  
C
C End of code that prevents any type of heating during the PreHeating Period
C              
              
              qconv = hr * (Tr-SOL)
              qrad = - emiss * boltz * (SOL**4 - Tamb**4)
              qlaser = (2.0 * P) / (pi * r0**2) * exp(-2.0 * (r**2) / (r0**2))
              
c              write(6,750)t_total, qconv, qrad, qlaser
750           format(E12.4, 1x, 3(E12.4, 1x))
              
              ! Outputting the results
              !WRITE(6, 454) 
              !write(6, 453)t_total, x, z, r, Tr, hr, SOL, qconv, qrad, qlaser
              !write(6, 455) TrA1,TrB1,TrA2,TrB2, hrA1,hrB1,hrA2,hrB2
453           format(F8.3,1x,'(',2(F9.3,1x),')',F9.3,1x,6(d12.4,1x))  
455           format(8(E11.3,1x))
454           format('-----------------')
              !WRITE(6, *) 'r = ', r
              !WRITE(6, *) 'Tr = ', Tr
              !WRITE(6, *) 'hr = ', hr
              !WRITE(6, *) 'SOL = ', SOL              
              !WRITE(6, *) 'qconv = ', qconv
              !WRITE(6, *) 'qrad = ', qrad
              !WRITE(6, *) 'qlaser = ', qlaser
              
!			  if      (r .gt. (10) .AND. r .lt. (11)) then
!				  WRITE(6, *) 'UFlux = ',r ,t_total, t_raster, xn, zn, Tr, hr,trkPltBot, trkPltTop, trkSubsTop, trkSubsBot
!			  end if 
!
!			  if      (r .gt. (1) .AND. r .lt. (2)) then
!				  WRITE(6, *) 'UFlux = ',r ,t_total, t_raster, xn, zn, Tr, hr,trkPltBot, trkPltTop, trkSubsTop, trkSubsBot
!			  end if 
!             
!			  if      (r .gt. (100) .AND. r .lt. (101)) then
!				  WRITE(6, *) 'UFlux = ',r ,t_total, t_raster, xn, zn, Tr, hr,trkPltBot, trkPltTop, trkSubsTop, trkSubsBot
!			  end if              
              
              FLUX(1) = qconv + qrad + qlaser
          else
              FLUX(1) = 0.0
          end if
C       end if
   
C       WRITE (7,*) "trkSubsTop", trkSubsTop, "trkSubsBot", trkSubsBot, 
     
C           if ( 
C      *         (SNAME == 'ASSEMBLY_SUBTOPLEFT' ) .OR.
C      *         (SNAME == 'ASSEMBLY_SUBTOPRIGHT') .OR.
C      *         (SNAME == 'ASSEMBLY_'//surfLyrI   .AND. x .LT. (trkLeft + xTol)) .OR.
C      *         (SNAME == 'ASSEMBLY_'//surfLyrIm1 .AND. x .GT. (trkRight - xTol)) .OR.
C      *         (SNAME == 'ASSEMBLY_'//surfLyrI   .AND.
C      *           ((trkLeft  - xTol) .LT. x .AND. x .LT. (trkRight  + xTol)) .AND.
C      *           ((subsTrkNewRr  - zTol) .LT. z .AND. z .LT. (trkNewFrnt + zTol))).OR.
C      *         (SNAME == 'ASSEMBLY_'//surfLyrIm1 .AND. 
C      *           ((trkLeft  - xTol) .LT. x .AND. x .LT. (trkRight  + xTol)) .AND.
C      *           ((subsTrkOldRr  - zTol) .LT. z .AND. z .LT. (subsTrkOldFrt + zTol)))
C      *        ) then
      
      RETURN
      END		      
      
"""

# Insert the values into the Fortran template

fortran_code = fortran_template.format(
    P_deposition="{:.3f}d0".format(P_deposition),
    P_preheat="{:.3f}d0".format(P_preheat), 
    r0="{:.3f}d0".format(r0),
    baseWidth="{:.3f}d0".format(baseWidth),
    baseLength="{:.3f}d0".format(baseLength), 
    baseThick="{:.3f}d0".format(baseThick),
    subsWidth="{:.3f}d0".format(subsWidth),
    subsLength="{:.3f}d0".format(subsLength), 
    subsThick="{:.3f}d0".format(subsThick),
    depTrkWidth="{:.3f}d0".format(depTrkWidth),
    depTrkThick="{:.3f}d0".format(depTrkThick), 
    depTrksPerLyr="{:.3f}d0".format(depTrksPerLyr),
    sprayNzzlVel="{:.3f}d0".format(sprayNzzlVel), 
    sprayNzzlAccel="{:.3f}d0".format(sprayNzzlAccel),
    sprayFrmsPerTrk="{:.3f}d0".format(sprayFrmsPerTrk), 
    depNoOfLyrs="{:.3f}d0".format(depNoOfLyrs),  
    PartitionThick="{:.3f}d0".format(PartitionThick),  
    PreHeatingTime="{:.3f}d0".format(PreHeatingTime),  
    PreHeatingTimeInc="{:.3f}d0".format(PreHeatingTimeInc),      
    DepositionTime="{:.3f}d0".format(DepositionTime),
    DepositionTimeInc="{:.3f}d0".format(DepositionTimeInc),
    CoolingTime1="{:.3f}d0".format(CoolingTime1), 
    CoolingTimeInc1="{:.3f}d0".format(CoolingTimeInc1),
    ReleaseFixturesTime="{:.3f}d0".format(ReleaseFixturesTime),  
    CoolingTime2="{:.3f}d0".format(CoolingTime2), 
    emissSubsDep="{:.3f}d0".format(emissSubsDep), 
    ambientTemp="{:.3f}d0".format(ambientTemp), 
    depLength="{:.3f}d0".format(depLength), 
    HotplateSSTime="{:.3f}d0".format(HotplateSSTime),
    TrA1="{:.3f}d0".format(TrA1),
    TrB1="{:.3f}d0".format(TrB1),
    TrA2="{:.3f}d0".format(TrA2),
    TrB2="{:.3f}d0".format(TrB2),
    hrA1="{:.3f}d0".format(hrA1),
    hrB1="{:.3f}d0".format(hrB1),
    hrA2="{:.3f}d0".format(hrA2),
    hrB2="{:.3f}d0".format(hrB2),   
    eig11="{:.3e}".format(eig11),
    eig22="{:.3e}".format(eig22),
    eig33="{:.3e}".format(eig33)
    #CoolingTimeInc2="{:.3f}d0".format(CoolingTimeInc2),   
    #clampWidthXplus="{:.3f}d0".format(clampWidthXplus), 
    #clampWidthXminus="{:.3f}d0".format(clampWidthXminus),  
    )
# C SM added eig values above (8/25/2025)
##---------------------------------------------------------------------
## Create 'heat_transfer.inp'
##
inp_file_name='heat_transfer'

# File name for the Fortran file
fortran_file_name = 'Generated_Subroutine.f'

# Writing the Fortran code to a file
with open(fortran_file_name, 'w') as file:
    file.write(fortran_code)

fortran_file_path = os.path.join(current_directory, fortran_file_name)
 
current_model_name = mdb.models.keys()[-1]  
##Job Create    
mdb.Job(name=inp_file_name, 
    model=current_model_name, 
    description='', 
    type=ANALYSIS, 
    atTime=None, 
    waitMinutes=0, 
    waitHours=0, 
    queue=None, 
    memory=90, 
    memoryUnits=PERCENTAGE, 
    getMemoryFromAnalysis=True, 
    explicitPrecision=SINGLE, 
    nodalOutputPrecision=SINGLE, 
    echoPrint=OFF, 
    modelPrint=OFF, 
    contactPrint=OFF, 
    historyPrint=OFF,  
    scratch='', 
    resultsFormat=ODB,
    numDomains=16, 
    activateLoadBalancing=False, 
    multiprocessingMode=DEFAULT, 
    numCpus=16, 
    numGPUs=0)
    
#Write input    
mdb.jobs[inp_file_name].writeInput(consistencyChecking=OFF)


##----------------------------------------------------------------------------
## STRESS related commands start here
##

### Conversion and deactivation of heat transfer related settings ####

mdb.Model(name='Stress', objectToCopy=mdb.models['Model-1'])

myModel=mdb.models['Stress']
# Tirza Peeters change 11-04-2025
if Run_step_1 == 1:
    del myModel.steps['HotplateSS']
# Tirza Peeters change 11-04-2025 move preheating to an if-statement
if Run_step_2 == 1:
    del myModel.steps['PreHeating']
del myModel.steps['Deposition']
del myModel.steps['Cooling1']
del myModel.steps['ReleaseFixtures']
del myModel.steps['Cooling2']

myModel.predefinedFields.delete(('BaseInitialTemp', 
    'Dep1InitialTemp', 'Dep2InitialTemp', 'Dep3InitialTemp', 'SubstrateTemp'))

del myModel.interactions['Conduction']

##---------------------------------------------------------------------
## Create Steps for the stress analysis
##

#PreHeating
# 
# SM modified (7/28/2025)
#
# defined these variables and made each staep automatic
initialIncStress = 1.0e-3
minIncStress     = 1.0e-9
#maxIncStress    : needs to be synchronized with the thermal max TimeInc values 
maxNumIncStress   = 100000
#
# Time_Method =0 FIXED; 
# Time_Method =1 AUTOMATIC
#
Time_Method = 1

if Time_Method == 1:
    # Tirza Peeters change 11-04-2025 move hotplateSS to an if-statement
    if Run_step_1 == 1:
        myModel.StaticStep(
            name       = 'HotplateSS', 
            previous   = 'Initial', 
            timePeriod = HotplateSSTime, 
            maxNumInc  = maxNumIncStress, 
            initialInc = initialIncStress, 
            minInc     = minIncStress, 
            maxInc     = HotplateSSTimeInc,
            nlgeom     = ON, 
            stabilizationMethod=DISSIPATED_ENERGY_FRACTION,
            stabilizationMagnitude=2e-4)

    # Tirza Peeters change 11-04-2025 move hotplateSS and preheating to an if-statement
    if Run_step_2 == 1:
        if Run_step_1 == 1:
            myModel.StaticStep(
                name       = 'PreHeating', 
                previous   = 'HotplateSS', 
                timePeriod = PreHeatingTime, 
                maxNumInc  = maxNumIncStress, 
                timeIncrementationMethod=AUTOMATIC, 
                initialInc = initialIncStress, 
                minInc     = minIncStress, 
                maxInc     = PreHeatingTimeInc,
                nlgeom     = ON, 
                stabilizationMethod=DISSIPATED_ENERGY_FRACTION,
                stabilizationMagnitude=2e-4)

        elif Run_step_1 == 0:
            myModel.StaticStep(
                name       = 'PreHeating', 
                previous   = 'Initial', 
                timePeriod = PreHeatingTime, 
                maxNumInc  = maxNumIncStress, 
                timeIncrementationMethod=AUTOMATIC, 
                initialInc = initialIncStress, 
                minInc     = minIncStress, 
                maxInc     = PreHeatingTimeInc,
                nlgeom     = ON, 
                stabilizationMethod=DISSIPATED_ENERGY_FRACTION,
                stabilizationMagnitude=2e-4)

        myModel.StaticStep(
            name       = 'Deposition', 
            previous   = 'PreHeating', 
            timePeriod = DepositionTime, 
            maxNumInc  = maxNumIncStress, 
            timeIncrementationMethod=AUTOMATIC, 
            initialInc = initialIncStress, 
            minInc     = minIncStress, 
            maxInc     = DepositionTimeInc,
            nlgeom     = ON, 
            stabilizationMethod=DISSIPATED_ENERGY_FRACTION,
            stabilizationMagnitude=2e-4)

    elif Run_step_2 == 0:
        if Run_step_1 == 1:
            myModel.StaticStep(
                name       = 'Deposition', 
                previous   = 'HotplateSS', 
                timePeriod = DepositionTime, 
                maxNumInc  = maxNumIncStress, 
                timeIncrementationMethod=AUTOMATIC, 
                initialInc = initialIncStress, 
                minInc     = minIncStress, 
                maxInc     = DepositionTimeInc,
                nlgeom     = ON, 
                stabilizationMethod=DISSIPATED_ENERGY_FRACTION,
                stabilizationMagnitude=2e-4)

        elif Run_step_1 == 0:
            myModel.StaticStep(
                name       = 'Deposition', 
                previous   = 'Initial', 
                timePeriod = DepositionTime, 
                maxNumInc  = maxNumIncStress, 
                timeIncrementationMethod=AUTOMATIC, 
                initialInc = initialIncStress, 
                minInc     = minIncStress, 
                maxInc     = DepositionTimeInc,
                nlgeom     = ON, 
                stabilizationMethod=DISSIPATED_ENERGY_FRACTION,
                stabilizationMagnitude=2e-4)


    myModel.StaticStep(
        name       = 'Cooling1', 
        previous   = 'Deposition', 
        timePeriod = CoolingTime1, 
        maxNumInc  = maxNumIncStress, 
        timeIncrementationMethod=AUTOMATIC, 
        initialInc = initialIncStress, 
        minInc     = minIncStress, 
        maxInc     = CoolingTimeInc1,
        nlgeom     = ON, 
        stabilizationMethod=DISSIPATED_ENERGY_FRACTION,
        stabilizationMagnitude=2e-4)

    #ReleaseFixtures
    myModel.StaticStep(
        name       = 'ReleaseFixtures', 
        previous   = 'Cooling1', 
        timePeriod = ReleaseFixturesTime, 
        maxNumInc  = 100000, 
        initialInc = 1e-3, 
        minInc     = 1.0e-09, 
        maxInc     = ReleaseFixturesTime,
        nlgeom     = ON, 
        stabilizationMethod=DISSIPATED_ENERGY_FRACTION,
        stabilizationMagnitude=2e-4)
    
    myModel.StaticStep(
        name='Cooling2', 
        previous   = 'ReleaseFixtures', 
        timePeriod = CoolingTime2, 
        maxNumInc  = maxNumIncStress, 
        timeIncrementationMethod=AUTOMATIC, 
        initialInc = initialIncStress, 
        minInc     = minIncStress, 
        maxInc     = CoolingTimeInc2,
        nlgeom     = ON, 
        stabilizationMethod=DISSIPATED_ENERGY_FRACTION,
        stabilizationMagnitude=2e-4)

elif Time_Method ==0:

    # Tirza Peeters change 11-04-2025 move hotplateSS to an if-statement
    if Run_step_1 == 1:
        myModel.StaticStep(
            name='HotplateSS', 
            previous='Initial', 
            timePeriod=HotplateSSTime, 
            maxNumInc=100000, 
            timeIncrementationMethod=FIXED, 
            initialInc=HotplateSSTimeInc,
            nlgeom     = ON, 
            stabilizationMethod=DISSIPATED_ENERGY_FRACTION,
            stabilizationMagnitude=2e-4)
    
    # Tirza Peeters change 11-04-2025 move preheating to an if-statement
    if Run_step_2 == 1:
        if Run_step_1 == 1:
            myModel.StaticStep(
                name='PreHeating', 
                previous='HotplateSS', 
                timePeriod=PreHeatingTime, 
                maxNumInc=100000, 
                timeIncrementationMethod=FIXED, 
                initialInc=PreHeatingTimeInc,
                nlgeom     = ON, 
                stabilizationMethod=DISSIPATED_ENERGY_FRACTION,
                stabilizationMagnitude=2e-4)
        elif Run_step_1 == 0:
            myModel.StaticStep(
                name='PreHeating', 
                previous='Initial', 
                timePeriod=PreHeatingTime, 
                maxNumInc=100000, 
                timeIncrementationMethod=FIXED, 
                initialInc=PreHeatingTimeInc,
                nlgeom     = ON, 
                stabilizationMethod=DISSIPATED_ENERGY_FRACTION,
                stabilizationMagnitude=2e-4)
    
        #Deposition
        myModel.StaticStep(
            name='Deposition', 
            previous='PreHeating', 
            timePeriod=DepositionTime, 
            maxNumInc=1000000, 
            timeIncrementationMethod=FIXED, 
            initialInc=DepositionTimeInc,
            nlgeom     = ON, 
            stabilizationMethod=DISSIPATED_ENERGY_FRACTION,
            stabilizationMagnitude=2e-4)

    elif Run_step_2 == 0:
        if Run_step_1 == 1:
            #Deposition
            myModel.StaticStep(
                name='Deposition', 
                previous='HotplateSS', 
                timePeriod=DepositionTime, 
                maxNumInc=1000000, 
                timeIncrementationMethod=FIXED, 
                initialInc=DepositionTimeInc,
                nlgeom     = ON, 
                stabilizationMethod=DISSIPATED_ENERGY_FRACTION,
                stabilizationMagnitude=2e-4)
        elif Run_step_1 == 0:
            myModel.StaticStep(
                name='Deposition', 
                previous='Initial', 
                timePeriod=DepositionTime, 
                maxNumInc=1000000, 
                timeIncrementationMethod=FIXED, 
                initialInc=DepositionTimeInc,
                nlgeom     = ON, 
                stabilizationMethod=DISSIPATED_ENERGY_FRACTION,
                stabilizationMagnitude=2e-4)

    #Cooling1
    myModel.StaticStep(
        name='Cooling1', 
        previous='Deposition', 
        timePeriod=CoolingTime1, 
        maxNumInc=100000, 
        timeIncrementationMethod=FIXED, 
        initialInc=CoolingTimeInc1,
        nlgeom     = ON, 
        stabilizationMethod=DISSIPATED_ENERGY_FRACTION,
        stabilizationMagnitude=2e-4)
    
    #ReleaseFixtures
    myModel.StaticStep(
        name='ReleaseFixtures', 
        previous='Cooling1', 
        timePeriod=ReleaseFixturesTime, 
        maxNumInc=100000, 
        initialInc=ReleaseFixturesTime/10, 
        minInc=1.0e-05, 
        maxInc=ReleaseFixturesTime,
        nlgeom     = ON, 
        stabilizationMethod=DISSIPATED_ENERGY_FRACTION,
        stabilizationMagnitude=2e-4)
    
    #Cooling2
    myModel.StaticStep(
        name='Cooling2', 
        previous='ReleaseFixtures', 
        timePeriod=CoolingTime2, 
        maxNumInc=100000, 
        timeIncrementationMethod=FIXED, 
        initialInc=CoolingTimeInc2,
        nlgeom     = ON, 
        stabilizationMethod=DISSIPATED_ENERGY_FRACTION,
        stabilizationMagnitude=2e-4)
    
#
# End of edits on 7/28/2025
#
  
#Element Type Assignment
myPart=myModel.parts['BasewithDep']
# Define the bounding box coordinates (xMin, yMin, zMin, xMax, yMax, zMax)
xMin, yMin, zMin = -baseWidth, 0, 0  # Adjust these values as per your model
xMax, yMax, zMax = baseWidth, baseThick+subsThick+dep2Thick, 2*baseLength     # Adjust these values as per your model

# Select cells within the bounding box
selected_cells = myPart.cells.getByBoundingBox(xMin, yMin, zMin, xMax, yMax, zMax)


# Define a reference region coordinate that is within the part
reference_point = (0, baseThick, baseLength/2)  # Ensure this point is valid within the part

# Find the face at the reference point
reference_face = myPart.faces.findAt(reference_point)


myPart.assignStackDirection(cells=selected_cells, referenceRegion=reference_face)

# Define element types (adjust these as per your requirements)
elemType1 = mesh.ElemType(elemCode=C3D8R, elemLibrary=STANDARD)
elemType2 = mesh.ElemType(elemCode=C3D8R, elemLibrary=STANDARD)
elemType3 = mesh.ElemType(elemCode=C3D8R, elemLibrary=STANDARD)

# Assign element types to the selected cells
myPart.setElementType(regions=(selected_cells,), elemTypes=(elemType1, elemType2, elemType3))



myPart.generateMesh()

#Element Type Assignment
myPart=myModel.parts['SubwithDep']
# Define the bounding box coordinates (xMin, yMin, zMin, xMax, yMax, zMax)
xMin, yMin, zMin = -baseWidth, 0, 0  # Adjust these values as per your model
xMax, yMax, zMax = baseWidth, baseThick+subsThick+dep2Thick, 2*baseLength     # Adjust these values as per your model

# Select cells within the bounding box
selected_cells = myPart.cells.getByBoundingBox(xMin, yMin, zMin, xMax, yMax, zMax)

# Define element types (adjust these as per your requirements)
elemType1 = mesh.ElemType(elemCode=C3D8R, elemLibrary=STANDARD)
elemType2 = mesh.ElemType(elemCode=C3D8R, elemLibrary=STANDARD)
elemType3 = mesh.ElemType(elemCode=C3D8R, elemLibrary=STANDARD)

# Assign element types to the selected cells
myPart.setElementType(regions=(selected_cells,), elemTypes=(elemType1, elemType2, elemType3))                      

myPart.generateMesh()



myPart=myModel.parts['SubwithDep']
# Define the bounding box coordinates (xMin, yMin, zMin, xMax, yMax, zMax)
xMin, yMin, zMin = subsWidth/2-clampWidthXplus, baseThick, dep1Length  # Adjust these values as per your model
xMax, yMax, zMax = subsWidth/2, baseThick+subsThick, dep1Length+subsLength     # Adjust these values as per your model
# Select cells within the bounding box
selected_cells = myPart.cells.getByBoundingBox(xMin, yMin, zMin, xMax, yMax, zMax)
myPart.Set(cells=selected_cells, name='Clamp1')


myPart=myModel.parts['SubwithDep']
# Define the bounding box coordinates (xMin, yMin, zMin, xMax, yMax, zMax)
xMin, yMin, zMin = -subsWidth/2, baseThick, dep1Length  # Adjust these values as per your model
xMax, yMax, zMax = -subsWidth/2+clampWidthXplus, baseThick+subsThick, dep1Length+subsLength     # Adjust these values as per your model
# Select cells within the bounding box
selected_cells = myPart.cells.getByBoundingBox(xMin, yMin, zMin, xMax, yMax, zMax)
myPart.Set(cells=selected_cells, name='Clamp2')


myModel.EncastreBC(createStepName='Initial', localCsys=None, name=
    'Clamp1', region=
    myModel.rootAssembly.instances['SubwithDep-1'].sets['Clamp1'])
myModel.EncastreBC(createStepName='Initial', localCsys=None, name=
    'Clamp2', region=
    myModel.rootAssembly.instances['SubwithDep-1'].sets['Clamp2'])


myModel.boundaryConditions['Clamp1'].deactivate('ReleaseFixtures')
myModel.boundaryConditions['Clamp2'].deactivate('ReleaseFixtures')
#





myAssembly=myModel.rootAssembly


#####

# Define the coordinates of the bounding box
x_min, y_min, z_min = -200, 0.0, -5  # Lower corner of the box
x_max, y_max, z_max = 200, 0.05, 400  # Upper corner of the box


# Get the mesh elements of the part
elements = part.elements

# Initialize a list to store the elements inside the box
elements_inside_box = []

# Iterate over the elements to find those with at least three nodes on the bottom surface
for element in elements:
    nodes = element.getNodes()
    count = 0
    for node in nodes:
        x, y, z = node.coordinates
        if x_min <= x <= x_max and y == 0 and z_min <= z <= z_max:
            count += 1
    if count >= 3:
        elements_inside_box.append(element)

# Create a set for the elements inside the box
element_labels = [element.label for element in elements_inside_box]


instance_name = 'BasewithDep-1'  # 


myAssembly.Surface(face1Elements=myAssembly.instances[instance_name].elements.sequenceFromLabels(element_labels), name='BaseBottomSurface') 




mdb.models['Stress'].rootAssembly.Set(faces=
    mdb.models['Stress'].rootAssembly.instances['BasewithDep-1'].faces.findAt((
    (45.333333, 0.0, 216.0), ), ((25.0, 0.0, 260.0), ), ), name=
    'BasebottomSurface')   


myAssembly.Set(name='PlateBottom', faces=
    myAssembly.instances['BasewithDep-1'].faces.findAt(
    ((0, 0.0, (baseLength-subsLength)/4), ), #1,2
    ((0, 0.0, baseLength/2), ), #2,2
    ((0, 0.0, baseLength-(baseLength-subsLength)/4), ), #3,2
    ((dep1Width/2+(baseWidth-dep1Width-subsWidth)/4, 0.0, (baseLength-subsLength)/4), ), #1,2
    ((dep1Width/2+(baseWidth-dep1Width-subsWidth)/4, 0.0, baseLength/2), ), #2,2
    ((dep1Width/2+(baseWidth-dep1Width-subsWidth)/4, 0.0, baseLength-(baseLength-subsLength)/4), ), #3,2
    ((-dep1Width/2-(baseWidth-dep1Width-subsWidth)/4, 0.0, (baseLength-subsLength)/4), ), #1,2
    ((-dep1Width/2-(baseWidth-dep1Width-subsWidth)/4, 0.0, baseLength/2), ), #2,2
    ((-dep1Width/2-(baseWidth-dep1Width-subsWidth)/4, 0.0, baseLength-(baseLength-subsLength)/4), ), #3,2 
    ((subsWidth/2-clampWidthXplus/2, 0.0, (baseLength-subsLength)/4), ), #1,2
    ((subsWidth/2-clampWidthXplus/2, 0.0, baseLength/2), ), #2,2
    ((subsWidth/2-clampWidthXplus/2, 0.0, baseLength-(baseLength-subsLength)/4), ), #3,2
    ((-subsWidth/2+clampWidthXplus/2, 0.0, (baseLength-subsLength)/4), ), #1,2
    ((-subsWidth/2+clampWidthXplus/2, 0.0, baseLength/2), ), #2,2
    ((-subsWidth/2+clampWidthXplus/2, 0.0, baseLength-(baseLength-subsLength)/4), ), #3,2
    )) #3,3


myModel.EncastreBC(createStepName='Deposition', localCsys=None, 
    name='BottomSurfaceFix', region=myAssembly.sets['PlateBottom'])
#

##--------------------------------------------------------------------------
## Contact Property: begin
##

myModel.ContactProperty('Frictionless-Hard-Contact')

# SM change (8/1/2025)
myModel.interactionProperties['Frictionless-Hard-Contact'].NormalBehavior(
    pressureOverclosure           = HARD, 
    allowSeparation               = ON, 
    contactStiffness              = DEFAULT, 
    contactStiffnessScaleFactor   = 1.5, 
    clearanceAtZeroContactPressure= 0.0, 
    stiffnessBehavior             = LINEAR, 
    constraintEnforcementMethod   = PENALTY)
# End of SM change
    
myModel.interactionProperties['Frictionless-Hard-Contact'].TangentialBehavior(
    formulation=FRICTIONLESS)

myModel.SurfaceToSurfaceContactStd(
    adjustMethod    = NONE, 
    clearanceRegion = None, 
    createStepName  = 'Initial', 
    datumAxis       = None, 
    initialClearance= OMIT, 
    interactionProperty= 'Frictionless-Hard-Contact', 
    main            = myAssembly.surfaces['SubYminus'], 
    name            = 'BasePlate-Substrate', 
    secondary       = myAssembly.surfaces['PlateTop'], 
    sliding         = FINITE, 
    thickness       = ON)
##
## Contact Property: end
##--------------------------------------------------------------------------
##
## *Control card(s): begin
##
#
# SM edits: This block is edited, 7/31/2025
#

# Tirza Peeters change 11-04-2025 move hotplateSS to an if-statement (not sure)
if Run_step_1 == 1:
    myModel.steps['HotplateSS'].control.setValues(
        resetDefaultValues=ON)
    
    myModel.steps['HotplateSS'].control.setValues(
        allowPropagation        =OFF, 
        resetDefaultValues      =OFF,
        displacementField       =(0.02, 1.0, 0.0, 0.0, 0.02, 1e-05, 0.001, 1e-08, 1.0, 1e-05, 1e-08), 
        timeIncrementation      =(6.0, 8.0, 9.0, 30.0, 10.0, 4.0, 12.0, 30.0, 6.0, 3.0, 50.0) )
elif Run_step_2 == 1:
    myModel.steps['PreHeating'].control.setValues(
        resetDefaultValues=ON)
    
    myModel.steps['PreHeating'].control.setValues(
        allowPropagation        =OFF, 
        resetDefaultValues      =OFF,
        displacementField       =(0.02, 1.0, 0.0, 0.0, 0.02, 1e-05, 0.001, 1e-08, 1.0, 1e-05, 1e-08), 
        timeIncrementation      =(6.0, 8.0, 9.0, 30.0, 10.0, 4.0, 12.0, 30.0, 6.0, 3.0, 50.0) )
else:
    myModel.steps['Deposition'].control.setValues(
        resetDefaultValues=ON)
    
    myModel.steps['Deposition'].control.setValues(
        allowPropagation        =OFF, 
        resetDefaultValues      =OFF,
        displacementField       =(0.02, 1.0, 0.0, 0.0, 0.02, 1e-05, 0.001, 1e-08, 1.0, 1e-05, 1e-08), 
        timeIncrementation      =(6.0, 8.0, 9.0, 30.0, 10.0, 4.0, 12.0, 30.0, 6.0, 3.0, 50.0) )
    
myModel.steps['ReleaseFixtures'].control.setValues(
    resetDefaultValues=ON)
    
myModel.steps['ReleaseFixtures'].control.setValues(
    allowPropagation        =OFF, 
    resetDefaultValues      =OFF,
    displacementField       =(0.02, 1.0, 0.0, 0.0, 0.02, 1e-05, 0.001, 1e-08, 1.0, 1e-05, 1e-08), 
    timeIncrementation      =(6.0, 8.0, 9.0, 30.0, 10.0, 4.0, 12.0, 30.0, 6.0, 3.0, 50.0) )    
#
# End of SM edits
#
##
## *Control card(s): end
##----------------------------------------------------------------------------

##Outputs

# Tirza Peeters change 11-04-2025 move hotplateSS to an if-statement
if Run_step_1 == 1:
    # Set field & history output requests
    myModel.FieldOutputRequest(
        name='F-Output-1', 
        createStepName='HotplateSS', 
        variables=('CF', 'CNAREA', 'CSTATUS', 'CSTRESS', 'RF', 'U', 'NT', 'LE', 'MISES', 'PE', 'PEEQ', 'PEMAG', 'S', 
        'TEMP', 'EACTIVE'))
    
    myModel.HistoryOutputRequest(
        name='H-Output-1', 
        createStepName='HotplateSS', 
        variables=PRESELECT)

elif Run_step_2 == 1:
    # Set field & history output requests
    myModel.FieldOutputRequest(
        name='F-Output-1', 
        createStepName='PreHeating', 
        variables=('CF', 'CNAREA', 'CSTATUS', 'CSTRESS', 'RF', 'U', 'NT', 'LE', 'MISES', 'PE', 'PEEQ', 'PEMAG', 'S', 
        'TEMP', 'EACTIVE'))
    
    myModel.HistoryOutputRequest(
        name='H-Output-1', 
        createStepName='PreHeating', 
        variables=PRESELECT)

else:
    # Set field & history output requests
    myModel.FieldOutputRequest(
        name='F-Output-1', 
        createStepName='Deposition', 
        variables=('CF', 'CNAREA', 'CSTATUS', 'CSTRESS', 'RF', 'U', 'NT', 'LE', 'MISES', 'PE', 'PEEQ', 'PEMAG', 'S', 
        'TEMP', 'EACTIVE'))
    
    myModel.HistoryOutputRequest(
        name='H-Output-1', 
        createStepName='Deposition', 
        variables=PRESELECT)


##Temp.Field

# Set initial substrate temp.


region = myAssembly.instances['SubwithDep-1'].sets['Deposition2']
myModel.Temperature(
    name            = 'Deposition2', 
    createStepName  = 'Initial', 
    region          = region, 
    distributionType= UNIFORM, 
    crossSectionDistribution=CONSTANT_THROUGH_THICKNESS, 
    magnitudes      = (DepInitialTemp,)
    )


region = myAssembly.instances['SubwithDep-1'].sets['Substrate']
myModel.Temperature(
    name             = 'Substrate', 
    createStepName   = 'Initial', 
    region           = region, 
    distributionType = UNIFORM, 
    crossSectionDistribution=CONSTANT_THROUGH_THICKNESS, 
    magnitudes       = (DepInitialTemp,)
    )


# Set initial deposit temp.
#
# SM Change: I think there was a mistake here "magnitude = DepInitialTemp"
#            I modifed it as "magnitude = BaseInitialTemp"
#            This atleast provides symmetry
#
region = myAssembly.instances['BasewithDep-1'].sets['Deposition3']
myModel.Temperature(
    name            = 'Deposition3', 
    createStepName  = 'Initial', 
    region          = region, 
    distributionType= UNIFORM, 
    crossSectionDistribution=CONSTANT_THROUGH_THICKNESS, 
       magnitudes      = (BaseInitialTemp, ) #magnitudes      = (DepInitialTemp, )
    )


# Set initial deposit temp.
region = myAssembly.instances['BasewithDep-1'].sets['Deposition1']
myModel.Temperature(
    name            = 'Deposition1', 
    createStepName  = 'Initial', 
    region          = region, 
    distributionType= UNIFORM, 
    crossSectionDistribution=CONSTANT_THROUGH_THICKNESS, 
    magnitudes      = (BaseInitialTemp,)
    )

# Set initial deposit temp.
region = myAssembly.instances['BasewithDep-1'].sets['Base']
myModel.Temperature(
    name            = 'Base', 
    createStepName  = 'Initial', 
    region          = region, 
    distributionType=UNIFORM, 
    crossSectionDistribution=CONSTANT_THROUGH_THICKNESS, 
    magnitudes      = (BaseInitialTemp,)
    )





# Tirza Peeters change 11-04-2025 move hotplateSS to an if-statement
if Run_step_1 == 1:
    # Disable these temps after Initial step.
    myModel.predefinedFields['Deposition2'].resetToInitial(stepName='HotplateSS')
    myModel.predefinedFields['Deposition1'].resetToInitial(stepName='HotplateSS')
    myModel.predefinedFields['Deposition3'].resetToInitial(stepName='HotplateSS')

    myModel.predefinedFields['Base'].resetToInitial(stepName='HotplateSS')
    myModel.predefinedFields['Substrate'].resetToInitial(stepName='HotplateSS')
elif Run_step_2 == 1:
    # Disable these temps after Initial step.
    myModel.predefinedFields['Deposition2'].resetToInitial(stepName='PreHeating')
    myModel.predefinedFields['Deposition1'].resetToInitial(stepName='PreHeating')
    myModel.predefinedFields['Deposition3'].resetToInitial(stepName='PreHeating')

    myModel.predefinedFields['Base'].resetToInitial(stepName='PreHeating')
    myModel.predefinedFields['Substrate'].resetToInitial(stepName='PreHeating')
else:
    # Disable these temps after Initial step.
    myModel.predefinedFields['Deposition2'].resetToInitial(stepName='Deposition')
    myModel.predefinedFields['Deposition1'].resetToInitial(stepName='Deposition')
    myModel.predefinedFields['Deposition3'].resetToInitial(stepName='Deposition')

    myModel.predefinedFields['Base'].resetToInitial(stepName='Deposition')
    myModel.predefinedFields['Substrate'].resetToInitial(stepName='Deposition')

workingDir          = os.getcwd()
heatTrfrODBFile     = 'heat_transfer.odb'
heatTrfrODBPath     = workingDir + '\\' + heatTrfrODBFile


#Restart
myModel.steps['Deposition'].Restart(frequency=0, 
numberIntervals=
    int(depNoOfLyrs), 
    overlay=OFF)

m = 0
# Tirza Peeters change 11-04-2025 move hotplateSS to an if-statement
if Run_step_1 == 1:
    ## Create import fields for all steps.
    myModel.Temperature(name='ImportTemp', 
        createStepName='HotplateSS', 
        distributionType=FROM_FILE, 
        fileName=heatTrfrODBPath, 
        beginStep=1, 
        beginIncrement=1,  
        interpolate=OFF, 
        absoluteExteriorTolerance=0.0, 
        exteriorTolerance=0.05)

    ### HotPlateSS
    m = m+1
    stepCurr = 'HotplateSS'
    myModel.predefinedFields['ImportTemp'].setValuesInStep(
        stepName=stepCurr, 
        beginStep=m, beginIncrement=1)

elif Run_step_2 == 1:
    ## Create import fields for all steps.
    myModel.Temperature(name='ImportTemp', 
        createStepName='PreHeating', 
        distributionType=FROM_FILE, 
        fileName=heatTrfrODBPath, 
        beginStep=1, 
        beginIncrement=1,  
        interpolate=OFF, 
        absoluteExteriorTolerance=0.0, 
        exteriorTolerance=0.05)
else:
    ## Create import fields for all steps.
    myModel.Temperature(name='ImportTemp', 
        createStepName='Deposition', 
        distributionType=FROM_FILE, 
        fileName=heatTrfrODBPath, 
        beginStep=1, 
        beginIncrement=1,  
        interpolate=OFF, 
        absoluteExteriorTolerance=0.0, 
        exteriorTolerance=0.05)

# Tirza Peeters change 11-04-2025 move preheating to an if-statement
if Run_step_2 == 1:
    m = m+1
    stepCurr = 'PreHeating'
    myModel.predefinedFields['ImportTemp'].setValuesInStep(
        stepName=stepCurr, 
        beginStep=m, beginIncrement=1)

m = m+1
stepCurr = 'Deposition'
myModel.predefinedFields['ImportTemp'].setValuesInStep(
    stepName=stepCurr, 
    beginStep=m, beginIncrement=1)


m = m+1
stepCurr = 'Cooling1'
myModel.predefinedFields['ImportTemp'].setValuesInStep(
    stepName=stepCurr, 
    beginStep=m, beginIncrement=1)


m = m+1
stepCurr = 'ReleaseFixtures'
myModel.predefinedFields['ImportTemp'].setValuesInStep(
    stepName=stepCurr, 
    beginStep=m, beginIncrement=1)


m = m+1
stepCurr = 'Cooling2'
myModel.predefinedFields['ImportTemp'].setValuesInStep(
    stepName=stepCurr, 
    beginStep=m, beginIncrement=1)


# -------------------------------------------------------
# Stress_createJob():
# -------------------------------------------------------

mdb.Job(name='Stress', 
    model='Stress', 
    description='', 
    type=ANALYSIS, 
    atTime=None, 
    waitMinutes=0, 
    waitHours=0, 
    queue=None, 
    memory=90, 
    memoryUnits=PERCENTAGE, 
    getMemoryFromAnalysis=True, 
    explicitPrecision=SINGLE, 
    nodalOutputPrecision=SINGLE,
    echoPrint=OFF, 
    modelPrint=OFF, 
    contactPrint=OFF, 
    historyPrint=OFF, 
    scratch='', 
    resultsFormat=ODB,  
    numDomains=16, 
    activateLoadBalancing=False, 
    multiprocessingMode=DEFAULT, 
    numCpus=16, 
    numGPUs=0)
    
        
# -------------------------------------------------------
# Stress_writeInput():
# -------------------------------------------------------

mdb.jobs['Stress'].writeInput(consistencyChecking=OFF)