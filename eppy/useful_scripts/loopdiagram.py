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

import itertools
import os
import sys

import argparse
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
    """Object representing the loop diagram of an IDF.
    """
    
    def __init__(self, fname, iddfile):
        """
        Parameters
        ----------
        fname : str
            Path to the IDF.
        iddfile : str
            Path to the IDD.
            
        """
        data, commdct, _ = readidf.readdatacommdct(fname, iddfile=iddfile)
        self.fname = fname
        self.data = data
        self.commdct = commdct
        self.makediagram()
    
    def makediagram(self):
        """Make the diagram.
        """
        edges = self.edges
        print("making the diagram")
        graph = pydot.Dot(graph_type='digraph')
        nodes = edges2nodes(edges)
        epnodes = [(node, 
            makeanode(node[0])) for node in nodes if nodetype(node)=="epnode"]
        epbranches = [
            (node, makeabranch(node)) for node in nodes if not istuple(node)]
        nodedict = dict(epnodes + epbranches)# + endnodes)
        for value in list(nodedict.values()):
            graph.add_node(value)
        for e1, e2 in edges:
            graph.add_edge(pydot.Edge(nodedict[e1], nodedict[e2]))
        self.graph = graph

    @property
    def edges(self):
        """Create the edges for a plant and air loop diagram.
        
        Returns
        -------
        list
        
        """
        print("constructing the loops")
        self.plantloop = PlantLoop(self.data, self.commdct)
        self.airloop = AirLoop(self.data, self.commdct)
        edges = self.plantloop.edges + self.airloop.edges
        print("cleaning edges")
        edges = clean_edges(edges)
    
        return edges
    
    def save(self):
        """Save the diagram as a PNG image and a DOT file.
        
        The files will be saved in the same folder as the original IDF.
        
        """
        dotname = '%s.dot' % (os.path.splitext(self.fname)[0])
        pngname = '%s.png' % (os.path.splitext(self.fname)[0])
        self.graph.write(dotname)
        print("saved file: %s" % (dotname))
        self.graph.write_png(pngname)
        print("saved file: %s" % (pngname))


class PlantLoop(object):
    
    def __init__(self, data, commdct):
        self.data = data
        self.commdct = commdct
        self.anode = "epnode"
    
    @property
    def edges(self):
        """Edges representing the plant loops.
        """
        # start with the components of the loop
        edges = self.components_edges()
        # connect splitters to component nodes
        splitters = loops.splitterfields(self.data, self.commdct)
        for splitter in splitters:
            edges.extend(self.splitter_edges(splitter))
        # connect mixers to component nodes
        mixers = loops.mixerfields(self.data, self.commdct)
        for mixer in mixers:
            edges.extend(self.mixer_edges(mixer))
        
        return edges
    
    def components_edges(self):
        """Edges joining the components of a branch"""
        data = self.data
        commdct = self.commdct
        edges = []
    
        cnamefield = "Component %s Name"
        inletfield = "Component %s Inlet Node Name"
        outletfield = "Component %s Outlet Node Name"
    
        numobjects = len(data.dt['BRANCH'])
        cnamefields = loops.repeatingfields(
            data, commdct, 'BRANCH', cnamefield)
        inletfields = loops.repeatingfields(
            data, commdct, 'BRANCH', inletfield)
        outletfields = loops.repeatingfields(
            data, commdct, 'BRANCH', outletfield)
    
        inlets = loops.extractfields(
            data, commdct, 'BRANCH', [inletfields] * numobjects)
        components = loops.extractfields(
            data, commdct, 'BRANCH', [cnamefields] * numobjects)
        outlets = loops.extractfields(
            data, commdct, 'BRANCH', [outletfields] * numobjects)
    
        zipped = list(zip(inlets, components, outlets))
        tzipped = [transpose2d(item) for item in zipped]
        for item in tzipped:
            for inlet, component, outlet in item:
                edges.append(((inlet, 'epnode'), component))  # inlet edge
                edges.append((component, (outlet, 'epnode')))  # outlet edge
        return edges

    def splitter_edges(self, splitter):
        """Edges connecting a splitter to component branches.
        """
        inlet = splitter[1]
        outletbranches = splitter[2:]
        splitter = splitter[0]

        branch_connectors = self.branch_connectors()
        splitter_inlet = branch_connectors[inlet]["outlet"]
        splitter_outlets = [
            branch_connectors[branch]["inlet"] for branch in outletbranches]
        edges = []
        edges.extend([((splitter_inlet, 'epnode'), splitter)])
        edges.extend([(splitter, (outlet, 'epnode')) 
                      for outlet in splitter_outlets])
        return edges
    
    def mixer_edges(self, mixer):
        """Edges connecting component branches to a mixer.
        """
        mixername = mixer[0]
        outletbranchname = mixer[1]
        inletbranches = mixer[2:]
        
        branch_connectors = self.branch_connectors()
        mixer_outlet = branch_connectors[outletbranchname]["inlet"]
        mixer_inlets = [branch_connectors[branch]["outlet"]
                        for branch in inletbranches]
        edges = []
        edges.extend([(mixername, (mixer_outlet, 'epnode'))])
        edges.extend([((inlet, 'epnode'), mixername) 
                      for inlet in mixer_inlets])    
        return edges

    def branch_connectors(self):
        """Mapping from branch names to their inlet and outlet connectors.
        
        Returns
        -------
        dict
        
        """
        branches = self.data.dt["BRANCH"]
        connectors = {}
        for branch in branches:
            branch_name = branch[1]
            in_out = loops.branch_inlet_outlet(
                self.data, self.commdct, branch_name)
            connectors[branch_name] = dict(
                list(zip(["inlet", "outlet"], in_out)))
        
        return connectors


class AirLoop(object):
    
    def __init__(self, data, commdct):
        self.data = data
        self.commdct = commdct
    
    @property
    def edges(self):
        """Edges representing the air loops.
        """
        edges = []
        # connect supplyplenum to nodes
        supplyplenums = loops.supplyplenumfields(self.data, self.commdct)
        for supplyplenum in supplyplenums:
            edges.extend(self.supplyplenum_edges(supplyplenum))
        
        # connect zonesplitter to nodes
        zonesplitters = loops.zonesplitterfields(self.data, self.commdct)
        for zonesplitter in zonesplitters:
            edges.extend(self.zonesplitter_edges(zonesplitter))
        
        # connect zonemixer to nodes
        zonemixers = loops.zonemixerfields(self.data, self.commdct)
        for zonemixer in zonemixers:
            edges.extend(self.zonemixer_edges(zonemixer))
        
        # connect returnplenums to nodes
        returnplenums = loops.returnplenumfields(self.data, self.commdct)
        for returnplenum in returnplenums:
            edges.extend(self.returnplenum_edges(returnplenum))
        
        # connect room to return node
        equipconnections = loops.equipmentconnectionfields(self.data, self.commdct)
        for equipconnection in equipconnections:
            zonename = equipconnection[0]
            returnnode = equipconnection[-1]
            edges.append((zonename, (returnnode, 'epnode')))
        
        # connect equips to room
        equipmentlist = loops.equipmentlistfields(self.data, self.commdct)
        for equipconnection in equipconnections:
            zonename = equipconnection[0]
            zequiplistname = equipconnection[1]
            for zequip in equipmentlist[zequiplistname]:
                edges.append((zequip, zonename))
        
        # airdistunit <- adistu_component
        airdistunits = loops.airdistunitfields(self.data, self.commdct)
        for airdistunit in airdistunits:
            unitname = airdistunit[0]
            compname = airdistunit[2]
            edges.append((compname, unitname))
        
        # airinlet -> adistu_component
        allairdist_comps = loops.allairdistcomponentfields(self.data, self.commdct)
        for airdist_comps in allairdist_comps:
            for airdist_comp in airdist_comps:
                name = airdist_comp[0]
                for airnode in airdist_comp[1:]:
                    edges.append(((airnode, 'epnode'), name))
        
        # supplyairnode -> uncontrolled
        uncontrolleds = loops.uncontrolledfields(self.data, self.commdct)
        for uncontrolled in uncontrolleds:
            name = uncontrolled[0]
            airnode = uncontrolled[1]
            edges.append(((airnode, 'epnode'), name))
        
        return edges

    def zonesplitter_edges(self, zonesplitter):
        name = zonesplitter[0]
        inlet = zonesplitter[1]
        outlets = zonesplitter[2:]
        edges = [((inlet, 'epnode'), name)]
        edges.extend([(name, (outlet, 'epnode')) for outlet in outlets])
        
        return edges
    
    def supplyplenum_edges(self, supplyplenum):
        name = supplyplenum[0]
        inlet = supplyplenum[3]
        outlets = supplyplenum[4:]
        edges = [((inlet, 'epnode'), name)]
        edges.extend([(name, (outlet, 'epnode')) for outlet in outlets])
        
        return edges
    
    def zonemixer_edges(self, zonemixer):
        name = zonemixer[0]
        outlet = zonemixer[1]
        inlets = zonemixer[2:]
        edges = [(name, (outlet, 'epnode'))]
        edges.extend([((inlet, 'epnode'), name) for inlet in inlets])
        
        return edges
    
    def returnplenum_edges(self, returnplenum):
        name = returnplenum[0]
        outlet = returnplenum[3]
        inlets = returnplenum[4:]
        edges = [(name, (outlet, 'epnode'))]
        edges.extend([((inlet, 'epnode'), name) for inlet in inlets])
        
        return edges


def edges2nodes(edges):
    """Gather the unique nodes from the edges and return as a sorted list.
    """
    nodes = itertools.chain(*edges)
    unique_nodes = list(set(nodes))
    
    def as_tuple(item):
        """Ensure the item is a tuple so it can be compared.
        
        Parameters
        ----------
        item : str or tuple
            The node to be sorted.
        
        Returns
        -------
        tuple
            
        """
        if isinstance(item, string_types):
            return (item, '')
        else:
            return item
        
    return sorted(unique_nodes, key=as_tuple)
    
    
def makeanode(name):
    """Make a standard pydot Node representing an EPlus node.
    """
    return pydot.Node(name, shape="plaintext", label=name)
    
    
def makeabranch(name):
    """Make a box-shaped pydot Node representing an EPlus branch.
    """
    return pydot.Node(name, shape="box3d", label=name)


def istuple(x):
    return type(x) == tuple


def nodetype(anode):
    """Return the type of node.
    
    Parameters
    ----------
    anode : tuple
    
    Returns
    -------
    str or None
    
    """
    try:
        return anode[1]
    except IndexError as e:
        return None


def transpose2d(mtx):
    """Transpose a 2d matrix
       [
            [1,2,3],
            [4,5,6]
            ]
        becomes
        [
            [1,4],
            [2,5],
            [3,6]
            ]
    """
    return zip(*mtx)


def getedges(fname, iddfile):
    """return the edges of the idf file fname"""
    diagram = LoopDiagram(fname, iddfile)
    return diagram.edges


def clean_edges(arg):
    if isinstance(arg, string_types):
        return replace_colon(arg)
    try:
        return tuple(clean_edges(x) for x in arg)
    except TypeError: # catch when for loop fails
        return replace_colon(arg) # not a sequence so just return repr

    
def replace_colon(s, replacewith='__'):
    """replace the colon with something"""
    return s.replace(":", replacewith)
    

def main():
    parser = argparse.ArgumentParser(usage=None, 
                description=__doc__, 
                formatter_class=argparse.RawTextHelpFormatter)
                # need the formatter to print newline from __doc__
    parser.add_argument('idd', type=str, action='store', 
        help='location of idd file = ./somewhere/eplusv8-0-1.idd')
    parser.add_argument('file', type=str, action='store', 
        help='location of idf file = ./somewhere/f1.idf')
    args = parser.parse_args()
    diagram = LoopDiagram(args.file, args.idd)
    diagram.save()


if __name__ == "__main__":
    sys.exit(main())
