import eppy
from eppy import modeleditor
from eppy.modeleditor import IDF
import time

start = time.time()

folder = "./"
folder= "/Users/santosh/Dropbox/coolshadow/eppy/shared_files/"

iddfile = "{}{}".format(folder, "Energy+.idd")
idffile = "{}{}".format(folder, "test02.idf")
n = idffile.split(".")
idf_OUT = str(n[0] + "_OUT." + n[1])

IDF.setiddname(iddfile)
idf1 = IDF(idffile)

#idf1.printidf()

srf = idf1.idfobjects['BuildingSurface:Detailed'.upper()]
walls = []
#zones_to_check = []

#Surface type Wall, Roof, Ceiling, Floor
#surface_type = "Wall"
#construction_name = "IW"

for s in srf:
	#print(s)
	constr = s.Construction_Name
	type = s.Surface_Type
	zone_name = s.Zone_Name
	#print (outside)
	# check Surface Type: Wall, Roof, Ceiling, Floor
	if "Wall" in type:
		# check Outside Boundary: Outdoors, Surface
		if s.Outside_Boundary_Condition == "Outdoors":
			# check construction name
			if "IW" in constr:
				s.Outside_Boundary_Condition = "Surface"
				s.Outside_Boundary_Condition_Object = s.Name
				walls.append(s.Name)
				print (s)
				#print (constr, " ", type, " ", zone_name, " ", outside)
				#zones_to_check.append(zone_name)
			else:
				pass
		else:
			pass
	else:
		pass

print(walls)
fe = idf1.idfobjects['FenestrationSurface:Detailed'.upper()]

for f in fe:
	for i in walls:
		if i == f.Building_Surface_Name:
			print(f)
			idf1.removeidfobject(f)
		else:
			pass

#print (srf)

#idf1.saveas(idf_OUT, lineendings='default', encoding='latin-1')
print ("saving new file")
idf1.saveas(idf_OUT)
print ("\n", idf_OUT, "...saved")

'''
BuildingSurface:Detailed,
    01OGc:01OGc_Wall_5_0_0,    !- Name
    Wall,                     !- Surface Type
    AW01,                     !- Construction Name
    01OGc:01OGc,              !- Zone Name
    Outdoors,                 !- Outside Boundary Condition
    ,                         !- Outside Boundary Condition Object
    SunExposed,               !- Sun Exposure
    WindExposed,              !- Wind Exposure
    AutoCalculate,            !- View Factor to Ground
    4,                        !- Number of Vertices
    -2.4796436367,            !- Vertex 1 Xcoordinate
    -0.9610492679,            !- Vertex 1 Ycoordinate
    4.0,                      !- Vertex 1 Zcoordinate
    5.0116125484,             !- Vertex 2 Xcoordinate
    -0.9610492679,            !- Vertex 2 Ycoordinate
    4.0,                      !- Vertex 2 Zcoordinate
    5.0116125484,             !- Vertex 3 Xcoordinate
    -0.9610492679,            !- Vertex 3 Ycoordinate
    7.0,                      !- Vertex 3 Zcoordinate
    -2.4796436367,            !- Vertex 4 Xcoordinate
    -0.9610492679,            !- Vertex 4 Ycoordinate
    7.0;                      !- Vertex 4 Zcoordinate
'''


end = time.time()
print('{} seconds'.format(end - start))
print('{} minutes'.format((end - start)/60.))
