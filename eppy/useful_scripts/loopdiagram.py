# Copyright (c) 2012 Santosh Philip
# Copyright (c) 2016 Jamie Bull
# =======================================================================
#  Distributed under the MIT License.
#  (See accompanying file LICENSE or copy at
#  http://opensource.org/licenses/MIT)
# =======================================================================
"""Draw all the  loops in the IDF file.

There are two output files saved in the same location as the idf file:
- idf_file_location/idf_filename.dot
- idf_file_location/idf_filename.png

"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import argparse
import os
import sys

from eppy.EPlusInterfaceFunctions import readidf
from eppy.pytest_helpers import PATH_TO_EPPY
from six import string_types

import eppy.loops as loops


try:
    import pydot
except ImportError:
    import pydot3k as pydot


sys.path.append(PATH_TO_EPPY)

class LoopDiagram(object):
    
    def __init__(self, fname, iddfile):
        self.fname = fname
        data, commdct, _ = readidf.readdatacommdct(fname, iddfile=iddfile)
        self.data = data
        self.commdct = commdct      
    
    def make_diagram(self):
        """Create a plant and air loop diagram.
        """
        print("constructing the loops")
        edges = makeairplantloop(self.data, self.commdct)
        print("cleaning edges")
        edges = clean_edges(edges)
        print("making the diagram")
    
        self.diagram = makediagram(edges)
    
    def save(self):
        dotname = '%s.dot' % (os.path.splitext(self.fname)[0])
        pngname = '%s.png' % (os.path.splitext(self.fname)[0])
        self.diagram.write(dotname)
        print("saved file: %s" % (dotname))
        self.diagram.write_png(pngname)
        print("saved file: %s" % (pngname))

def make_and_save_diagram(fname, iddfile):
    """Create a plant and air loop diagram and save to a PNG and a DOT file.
    """
    g = process_idf(fname, iddfile)
    save_diagram(fname, g)


def process_idf(fname, iddfile):
    """Create a plant and air loop diagram.
    """
    data, commdct, _iddindex = readidf.readdatacommdct(fname, iddfile=iddfile)
    print("constructing the loops")
    edges = makeairplantloop(data, commdct)
    print("cleaning edges")
    edges = clean_edges(edges)
    print("making the diagram")

    return makediagram(edges)

    
def save_diagram(fname, g):
    """Save a plant and air loop diagram to a PNG and a DOT file.
    """
    dotname = '%s.dot' % (os.path.splitext(fname)[0])
    pngname = '%s.png' % (os.path.splitext(fname)[0])
    g.write(dotname)
    print("saved file: %s" % (dotname))
    g.write_png(pngname)
    print("saved file: %s" % (pngname))


def makeairplantloop(data, commdct):
    """Get a list of edges representing air loops and plant loops.
    """
    edges = []
    edges.extend(plantloop_edges(data, commdct))
    edges.extend(airloop_edges(data, commdct))
                
    return edges


def plantloop_edges(data, commdct):
    """Get a list of edges representing plant loops.
    """
    anode = "epnode"
    # start with the components of the branch
    edges = component_edges(data, commdct, anode)
    # then make the connections to splitters and mixers
    branch_connections = get_branch_connectors(data, commdct)
    # connect splitters to nodes
    splitters = loops.splitterfields(data, commdct)
    edges.extend(splitter_edges(splitter, branch_connections, anode)
                 for splitter in splitters)    
    # connect mixers to nodes
    mixers = loops.mixerfields(data, commdct)
    edges.extend(mixer_edges(mixer, branch_connections, anode)
                 for mixer in mixers)
    
    return edges


def get_branch_connectors(data, commdct):
    # get all branches
    branches = data.dt["BRANCH"]
    connectors = {}
    for branch in branches:
        branch_name = branch[1]
        in_out = loops.branch_inlet_outlet(data, commdct, branch_name)
        connectors[branch_name] = dict(list(zip(["inlet", "outlet"], in_out)))
    
    return connectors


def component_edges(data, commdct, anode):
    """Return the edges joining the components of a branch.
    """
    alledges = []

    cnamefield = "Component %s Name"
    inletfield = "Component %s Inlet Node Name"
    outletfield = "Component %s Outlet Node Name"

    numobjects = len(data.dt['BRANCH'])
    cnamefields = loops.repeatingfields(data, commdct, 'BRANCH', cnamefield)
    inletfields = loops.repeatingfields(data, commdct, 'BRANCH', inletfield)
    outletfields = loops.repeatingfields(data, commdct, 'BRANCH', outletfield)

    inlets = loops.extractfields(
        data, commdct, 'BRANCH', [inletfields] * numobjects)
    components = loops.extractfields(
        data, commdct, 'BRANCH', [cnamefields] * numobjects)
    outlets = loops.extractfields(
        data, commdct, 'BRANCH', [outletfields] * numobjects)

    zipped = list(zip(inlets, components, outlets))
    tzipped = [transpose2d(item) for item in zipped]
    for i in range(len(data.dt['BRANCH'])):
        tt = tzipped[i]
        edges = []
        for t0 in tt:
            edges = edges + [((t0[0], anode), t0[1]), (t0[1], (t0[2], anode))]
        alledges = alledges + edges
    return alledges


def splitter_edges(splitter, branch_connections, anode):
    # splitter_inlet = inletbranch.node
    splittername = splitter[0]
    inletbranchname = splitter[1]
    outletbranchnames = splitter[2:]
    
    splitter_inlet = branch_connections[inletbranchname]["outlet"]
    # edges = splitter_inlet -> splittername
    edges = [((splitter_inlet, anode), splittername)]
    # splitter_outlets = ouletbranches.nodes
    splitter_outlets = [branch_connections[br]["inlet"] for 
                        br in outletbranchnames]
    # edges = [splittername -> outlet for outlet in splitter_outlets]
    edges.extend([(splittername, 
            (outlet, anode)) for outlet in splitter_outlets])
    
    return edges


def mixer_edges(mixer, branch_connections, anode):
    # mixer_outlet = outletbranch.node
    mixername = mixer[0]
    outletbranchname = mixer[1]
    inletbranchnames = mixer[2:]
    
    mixer_outlet = branch_connections[outletbranchname]["inlet"]
    # edges = mixername -> mixer_outlet
    edges = [(mixername, (mixer_outlet, anode))]
    # mixer_inlets = inletbranches.nodes
    mixer_inlets = [branch_connections[br]["outlet"]
                    for br in inletbranchnames]
    # edges = [mixername -> inlet for inlet in mixer_inlets]
    edges.extend([((inlet, anode), mixername) for inlet in mixer_inlets])

    return edges


def hvac_supplyplenums(data, commdct):
    #   get Name, Zone Name, Zone Node Name, inlet, all outlets
    objkey = "AIRLOOPHVAC:SUPPLYPLENUM"
    singlefields = ["Name", "Zone Name", "Zone Node Name", "Inlet Node Name"]
    fld = "Outlet %s Node Name"
    outletfields = loops.repeatingfields(data, commdct, objkey, fld)
    fieldlist = singlefields + outletfields
    fieldlists = [fieldlist] * loops.objectcount(data, objkey)
    supplyplenums = loops.extractfields(data, commdct, objkey, fieldlists)

    return supplyplenums


def hvac_zonesplitters(data, commdct):
    #   get Name, inlet, all outlets
    objkey = "AIRLOOPHVAC:ZONESPLITTER"
    singlefields = ["Name", "Inlet Node Name"]
    fld = "Outlet %s Node Name"
    repeatfields = loops.repeatingfields(data, commdct, objkey, fld)
    fieldlist = singlefields + repeatfields
    fieldlists = [fieldlist] * loops.objectcount(data, objkey)
    zonesplitters = loops.extractfields(data, commdct, objkey, fieldlists)

    return zonesplitters


def hvac_zonemixers(data, commdct):
    #   get Name, outlet, all inlets
    objkey = "AIRLOOPHVAC:ZONEMIXER"
    singlefields = ["Name", "Outlet Node Name"]
    fld = "Inlet %s Node Name"
    repeatfields = loops.repeatingfields(data, commdct, objkey, fld)
    fieldlist = singlefields + repeatfields
    fieldlists = [fieldlist] * loops.objectcount(data, objkey)
    zonemixers = loops.extractfields(data, commdct, objkey, fieldlists)

    return zonemixers


def hvac_returnplenums(data, commdct):
    #   get Name, Zone Name, Zone Node Name, outlet, all inlets
    objkey = "AIRLOOPHVAC:RETURNPLENUM"
    singlefields = ["Name", "Zone Name", "Zone Node Name", "Outlet Node Name"]
    fld = "Inlet %s Node Name"
    repeatfields = loops.repeatingfields(data, commdct, objkey, fld)
    fieldlist = singlefields + repeatfields
    fieldlists = [fieldlist] * loops.objectcount(data, objkey)
    returnplenums = loops.extractfields(data, commdct, objkey, fieldlists)
    return returnplenums


def hvac_equipmentconnections(data, commdct):
    #   get Name, equiplist, zoneairnode, returnnode
    objkey = "ZONEHVAC:EQUIPMENTCONNECTIONS"
    singlefields = ["Zone Name", "Zone Conditioning Equipment List Name", 
                    "Zone Air Node Name", "Zone Return Air Node Name"]
    repeatfields = []
    fieldlist = singlefields + repeatfields
    fieldlists = [fieldlist] * loops.objectcount(data, objkey)
    equipconnections = loops.extractfields(data, commdct, objkey, fieldlists)
    return equipconnections


def hvac_equipmentlist(data, commdct):
    #   get Name, all equiptype, all equipnames
    objkey = "ZONEHVAC:EQUIPMENTLIST"
    singlefields = ["Name"]
    fieldlist = singlefields
    flds = ["Zone Equipment %s Object Type", "Zone Equipment %s Name"]
    repeatfields = loops.repeatingfields(data, commdct, objkey, flds)
    fieldlist = fieldlist + repeatfields
    fieldlists = [fieldlist] * loops.objectcount(data, objkey)
    equiplists = loops.extractfields(data, commdct, objkey, fieldlists)
    equiplistdct = dict([(ep[0], ep[1:]) for ep in equiplists])
    for key, equips in list(equiplistdct.items()):
        enames = [equips[i] for i in range(1, len(equips), 2)]
        equiplistdct[key] = enames
    
    return equiplistdct


def hvac_uncontrolleds(data, commdct):
    #   get Name, airinletnode
    objkey = "AIRTERMINAL:SINGLEDUCT:UNCONTROLLED"
    singlefields = ["Name", "Zone Supply Air Node Name"]
    repeatfields = []
    fieldlist = singlefields + repeatfields
    fieldlists = [fieldlist] * loops.objectcount(data, objkey)
    uncontrolleds = loops.extractfields(data, commdct, objkey, fieldlists)
    return uncontrolleds


def zonesplitter_edges(zonesplitter, anode):
    name = zonesplitter[0]
    inlet = zonesplitter[1]
    outlets = zonesplitter[2:]
    edges = [((inlet, anode), name)]
    edges.extend([(name, (outlet, anode)) for outlet in outlets])
    
    return edges


def supplyplenum_edges(supplyplenum, anode):
    name = supplyplenum[0]
    inlet = supplyplenum[3]
    outlets = supplyplenum[4:]
    edges = [((inlet, anode), name)]
    edges.extend([(name, (outlet, anode)) for outlet in outlets])
    
    return edges


def zonemixer_edges(zonemixer, anode):
    name = zonemixer[0]
    outlet = zonemixer[1]
    inlets = zonemixer[2:]
    edges = [(name, (outlet, anode))]
    edges.extend([((inlet, anode), name) for inlet in inlets])
    
    return edges


def returnplenum_edges(returnplenum, anode):
    name = returnplenum[0]
    outlet = returnplenum[3]
    inlets = returnplenum[4:]
    edges = [(name, (outlet, anode))]
    edges.extend([((inlet, anode), name) for inlet in inlets])
    
    return edges


def hvac_airdistunits(data, commdct):
    #   get Name, equiplist, zoneairnode, returnnode
    objkey = "ZoneHVAC:AirDistributionUnit".upper()
    singlefields = ["Name", "Air Terminal Object Type", "Air Terminal Name"]
    repeatfields = []
    fieldlist = singlefields + repeatfields
    fieldlists = [fieldlist] * loops.objectcount(data, objkey)
    adistuunits = loops.extractfields(data, commdct, objkey, fieldlists)
    return adistuunits


def hvac_allairdistcomponents(data, commdct):
    #   get Name, airinletnode
    adistuinlets = loops.makeadistu_inlets(data, commdct)
    alladistu_comps = []
    for key in list(adistuinlets.keys()):
        objkey = key.upper()
        singlefields = ["Name"] + adistuinlets[key]
        repeatfields = []
        fieldlist = singlefields + repeatfields
        fieldlists = [fieldlist] * loops.objectcount(data, objkey)
        adistu_components = loops.extractfields(data, commdct, objkey, fieldlists)
        alladistu_comps.append(adistu_components)
    
    return alladistu_comps



def airloop_edges(data, commdct):
    # -----------air loop stuff----------------------

    # adistuunit -> room    
    # adistuunit <- VAVreheat 
    # airinlet -> VAVreheat

    # code only for AirTerminal:SingleDuct:VAV:Reheat
    # get airinletnodes for vavreheats
    # in AirTerminal:SingleDuct:VAV:Reheat:
    anode = "epnode"
    edges = []
    # connect zonesplitter to nodes
    zonesplitters = hvac_zonesplitters(data, commdct)
    for zonesplitter in zonesplitters:
        edges.extend(zonesplitter_edges(zonesplitter, anode))
    
    # connect supplyplenum to nodes
    supplyplenums = hvac_supplyplenums(data, commdct)
    for supplyplenum in supplyplenums:
        edges.extend(supplyplenum_edges(supplyplenum, anode))
    
    # connect zonemixer to nodes
    zonemixers = hvac_zonemixers(data, commdct)
    for zonemixer in zonemixers:
        edges.extend(zonemixer_edges(zonemixer, anode))
    
    # connect returnplenums to nodes
    returnplenums = hvac_returnplenums(data, commdct)
    for returnplenum in returnplenums:
        edges.extend(returnplenum_edges(returnplenum, anode))
    
    # connect room to return node
    equipconnections = hvac_equipmentconnections(data, commdct)
    for equipconnection in equipconnections:
        zonename = equipconnection[0]
        returnnode = equipconnection[-1]
        edges.append((zonename, (returnnode, anode)))
    
    # connect equips to room
    equipmentlist = hvac_equipmentlist(data, commdct)
    for equipconnection in equipconnections:
        zonename = equipconnection[0]
        zequiplistname = equipconnection[1]
        for zequip in equipmentlist[zequiplistname]:
            edges.append((zequip, zonename))
    
    # airdistunit <- adistu_component
    airdistunits = hvac_airdistunits(data, commdct)
    for airdistunit in airdistunits:
        unitname = airdistunit[0]
        compname = airdistunit[2]
        edges.append((compname, unitname))
    
    # airinlet -> adistu_component
    allairdist_comps = hvac_allairdistcomponents(data, commdct)
    for airdist_comps in allairdist_comps:
        for airdist_comp in airdist_comps:
            name = airdist_comp[0]
            for airnode in airdist_comp[1:]:
                edges.append(((airnode, anode), name))
    
    # supplyairnode -> uncontrolled
    uncontrolleds = hvac_uncontrolleds(data, commdct)
    for uncontrolled in uncontrolleds:
        name = uncontrolled[0]
        airnode = uncontrolled[1]
        edges.append(((airnode, anode), name))
    
    return edges

def makediagram(edges):
    """make the diagram with the edges"""
    graph = pydot.Dot(graph_type='digraph')
    nodes = edges2nodes(edges)
    epnodes = [(node, 
        makeanode(node[0])) for node in nodes if nodetype(node)=="epnode"]
    endnodes = [(node, 
        makeendnode(node[0])) for node in nodes if nodetype(node)=="EndNode"]
    epbr = [(node, makeabranch(node)) for node in nodes if not istuple(node)]
    nodedict = dict(epnodes + epbr + endnodes)
    for value in list(nodedict.values()):
        graph.add_node(value)
    for e1, e2 in edges:
        graph.add_edge(pydot.Edge(nodedict[e1], nodedict[e2]))
    return graph


def edges2nodes(edges):
    """gather the nodes from the edges"""
    nodes = []
    for e1, e2 in edges:
        nodes.append(e1)
        nodes.append(e2)
    nodedict = dict([(n, None) for n in nodes])
    justnodes = list(nodedict.keys())
    # justnodes.sort()
    justnodes = sorted(justnodes, key=lambda x: str(x[0]))
    return justnodes
    
    
def makeanode(name):
    return pydot.Node(name, shape="plaintext", label=name)
    
    
def makeendnode(name):
    return pydot.Node(name, shape="doubleoctagon", label=name, 
        style="filled", fillcolor="#e4e4e4")
    
    
def makeabranch(name):
    return pydot.Node(name, shape="box3d", label=name)


def istuple(x):
    return type(x) == tuple


def nodetype(anode):
    """return the type of node"""
    try:
        return anode[1]
    except IndexError as e:
        return None


def transpose2d(mtx):
    """Transpose a 2d matrix.
    """
    return zip(*mtx)


def getedges(fname, iddfile):
    """return the edges of the idf file fname"""
    data, commdct, idd_index = readidf.readdatacommdct(fname, iddfile=iddfile)
    edges = makeairplantloop(data, commdct)
    return edges


def replace_colon(s, replacewith='__'):
    """replace the colon with something"""
    return s.replace(":", replacewith)
    

def clean_edges(arg):
    if isinstance(arg, string_types):
        return replace_colon(arg)
    try:
        return tuple(clean_edges(x) for x in arg)
    except TypeError: # catch when for loop fails
        return replace_colon(arg) # not a sequence so just return repr

    
def main():
    parser = argparse.ArgumentParser(usage=None, 
                description=__doc__, 
                formatter_class=argparse.RawTextHelpFormatter)
                # need the formatter to print newline from __doc__
    parser.add_argument('idd', type=str, action='store', 
        help='location of idd file = ./somewhere/eplusv8-0-1.idd',
        required=True)
    parser.add_argument('file', type=str, action='store', 
        help='location of idf file = ./somewhere/f1.idf',
        required=True)
    args = parser.parse_args()
    make_and_save_diagram(args.file, args.idd)


if __name__ == "__main__":
    sys.exit(main())
