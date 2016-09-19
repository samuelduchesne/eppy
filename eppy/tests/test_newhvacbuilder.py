# Copyright (c) 2012 Santosh Philip
# Copyright (c) 2016 Jamie Bull
# =======================================================================
#  Distributed under the MIT License.
#  (See accompanying file LICENSE or copy at
#  http://opensource.org/licenses/MIT)
# =======================================================================
"""py.test for hvacbuilder"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from eppy.bunch_subclass import EpBunch
from eppy.hvacbuilder import getfieldnamesendswith
from eppy.hvacbuilder import initialise_loop
from eppy.hvacbuilder import loopfields
from eppy.iddcurrent import iddcurrent
from eppy.modeleditor import IDF
from six import StringIO
from six import string_types

import modeleditor


iddfhandle = StringIO(iddcurrent.iddtxt)
if IDF.getiddname() == None:
    IDF.setiddname(iddfhandle)


def makeairloop(idf, name, sloop, dloop):
    """Make an airloop with pipe components.
    Parameters
    ----------
    idf : IDF object
        The IDF.
    loopname : str
        Name for the loop.
    sloop : list
        A list of names for each branch on the supply loop.
        Example: ['s_inlet', ['oa sys'], 's_outlet]
    dloop : list
        A list of names for each branch on the loop.
        Example: ['d_inlet', ['zone1', 'zone2'], 'd_outlet]
    
    Returns
    -------
    EPBunch

    """
    return AirLoop(idf, name, sloop, dloop)


def makeplantloop(idf, name, sloop, dloop):
    """Make plant loop with pipe components.
    
    Parameters
    ----------
    idf : IDF object
        The IDF.
    loopname : str
        Name for the loop.
    sloop : list
        A list of names for each branch on the supply loop.
        Example: ['s_inlet', ['boiler', 'bypass'], 's_outlet]
    dloop : list
        A list of names for each branch on the loop.
        Example: ['d_inlet', ['zone1', 'zone2'], 'd_outlet]
    
    Returns
    -------
    EPBunch

    """
    return PlantLoop(idf, name, sloop, dloop)


def makecondenserloop(idf, name, sloop, dloop):
    """Make loop with pipe components

    Parameters
    ----------
    idf : IDF object
        The IDF.
    loopname : str
        Name for the loop.
    sloop : list
        A list of names for each branch on the supply loop.
        Example: ['s_inlet', ['tower', 'supply bypass'], 's_outlet]
    dloop : list
        A list of names for each branch on the loop.
        Example: ['d_inlet', ['chiller condenser', 'demand bypass'], 'd_outlet]
    
    Returns
    -------
    EPBunch

    """
    return CondenserLoop(idf, name, sloop, dloop)


class EppyHVAC(object):
    
    def __getattr__(self, name):
        return self.bunch[name]
    
    def __getitem__(self, name):
        return self.bunch[name]
    
    def __str__(self):
        return str(self.bunch)
        

class Loop(EppyHVAC):
    """
    A loop has two halves: a supply half-loop and a demand half-loop.
    Loops can be plant loops, condenser loops, or air loops.

    """
    
    def __init__(self, idf, name, sloop, dloop):
        self.idf = idf
        self.name = name
        self.supply = initialise_components(idf, sloop)
        self.demand = initialise_components(idf, dloop)
        self.bunch = idf.newidfobject(self.objecttype, name)
        fields = loopfields[self.objecttype]
        initialise_loop(self.bunch, fields)
        self.set_supply_side()
        self.set_demand_side()
    
    def set_supply_side(self):
        self.supply_side = HalfLoop(self.idf, self.bunch, self.supply, 'supply')
    
    def set_demand_side(self):
        self.demand_side = HalfLoop(self.idf, self.bunch, self.demand, 'demand')

    def replace_branch(self, name, components):
        self.components = components
        new_branch = Branch(self.idf, name, components)
    
    def replace_component(self, old_component, new_component):
        pass
    
    
def initialise_components(idf, loop, components=None):
    if not components:
        components = []
    for item in loop:
        if isinstance(item, EpBunch):
            components.append(Component(idf, bunch=item))
        elif isinstance(item, string_types):
            components.append(pipecomponent(idf, item))
        else:
            components = initialise_components(idf, item, components)
    return components
                
                    
class PlantLoop(Loop):
    
    objecttype = 'PLANTLOOP'


class CondenserLoop(Loop):
    
    objecttype = 'CONDENSERLOOP'


class AirLoop(Loop):

    objecttype = 'AIRLOOPHVAC'
    
    def set_demand_side(self):
        """Set the demand side of an air loop.
        
        The demand side of an air loop is very different to that of a plant or
        condenser loop.
        
        """
        idf = self.idf
        zones = self.demand[1:-1]
        #ZoneHVAC:EquipmentConnections
        for zone in zones:
            equipconn = idf.newidfobject("ZONEHVAC:EQUIPMENTCONNECTIONS")
            equipconn.Zone_Name = zone.Name
            fldname = "Zone_Conditioning_Equipment_List_Name"
            equipconn[fldname] = "%s equip list" % (zone.Name, )
            fldname = "Zone_Air_Inlet_Node_or_NodeList_Name"
            equipconn[fldname] = "%s Inlet Node" % (zone.Name, )
            fldname = "Zone_Air_Node_Name"
            equipconn[fldname] = "%s Node" % (zone.Name, )
            fldname = "Zone_Return_Air_Node_Name"
            equipconn[fldname] = "%s Outlet Node" % (zone.Name, )
        
        # make ZoneHVAC:EquipmentList
        for zone in zones:
            z_equiplst = idf.newidfobject("ZONEHVAC:EQUIPMENTLIST")
            z_equipconn = modeleditor.getobjects(
                idf.idfobjects, idf.model, idf.idd_info,
                "ZONEHVAC:EQUIPMENTCONNECTIONS",
                **dict(Zone_Name=zone.Name))[0]
            z_equiplst.Name = z_equipconn.Zone_Conditioning_Equipment_List_Name
            fld = "Zone_Equipment_1_Object_Type"
            z_equiplst[fld] = "AirTerminal:SingleDuct:Uncontrolled"
            z_equiplst.Zone_Equipment_1_Name = "%sDirectAir" % (zone.Name, )
            z_equiplst.Zone_Equipment_1_Cooling_Sequence = 1
            z_equiplst.Zone_Equipment_1_Heating_or_NoLoad_Sequence = 1
        
        # make AirTerminal:SingleDuct:Uncontrolled
        for zone in zones:
            z_equipconn = modeleditor.getobjects(
                idf.idfobjects, idf.model, idf.idd_info, 
                "ZONEHVAC:EQUIPMENTCONNECTIONS",
                **dict(Zone_Name=zone.Name))[0]
            key = "AIRTERMINAL:SINGLEDUCT:UNCONTROLLED"
            z_airterm = idf.newidfobject(key)
            z_airterm.Name = "%sDirectAir" % (zone.Name, )
            fld1 = "Zone_Supply_Air_Node_Name"
            fld2 = "Zone_Air_Inlet_Node_or_NodeList_Name"
            z_airterm[fld1] = z_equipconn[fld2]
            z_airterm.Maximum_Air_Flow_Rate = 'autosize'
            
        self.demand_side = AirHalfLoop(
            self.idf, self.bunch, self.demand, 'demand')

class HalfLoop(EppyHVAC):
    """A half-loop is either the demand or supply side of a loop.
    """
    
    def __init__(self, idf, loop, components, side):
        self.idf = idf
        self.loop = loop
        self.components = components
        self.side = side
        self.set_branchlist()
        self.set_connectorlist()
        self.set_splitter()
        self.set_mixer()
    
    def set_branchlist(self):
        if self.loop.key == 'AIRLOOPHVAC':            
            if self.side == 'supply':
                branchlist = self.idf.getmakeidfobject(
                    "BRANCHLIST", self.loop.fieldvalues[5])
        elif self.loop.key in ['PLANTLOOP', 'CONDENSERLOOP']:
            if self.side == 'supply':
                branchlist = self.idf.getmakeidfobject(
                    "BRANCHLIST", self.loop.fieldvalues[13])    
            elif self.side == 'demand':
                branchlist = self.idf.getmakeidfobject(
                    "BRANCHLIST", self.loop.fieldvalues[17])
        for component in self.components:
            branchlist.obj.append(component.Name)
        self.branchlist = branchlist
    
    def set_connectorlist(self):
        """A list of connectors on the half loop.
        """
        if self.side == 'supply':
            connectorlist = self.idf.getmakeidfobject(
                "CONNECTORLIST", self.loop.fieldvalues[8])
        if self.side == 'demand':
            connectorlist = self.idf.getmakeidfobject(
                "CONNECTORLIST", self.loop.fieldvalues[12])
        connectorlist.Connector_1_Object_Type = "Connector:Splitter"
        connectorlist.Connector_1_Name = "%s_supply_splitter" % self.loop.Name
        connectorlist.Connector_2_Object_Type = "Connector:Mixer"
        connectorlist.Connector_2_Name = "%s_supply_mixer" % self.loop.Name
        
        self.connectorlist = connectorlist

    def set_splitter(self):
        splitter = self.idf.newidfobject(
            "CONNECTOR:SPLITTER", 
            self.connectorlist.Connector_1_Name)
        splitter.Inlet_Branch_Name = self.components[0].Name
        splitter.obj.extend(c.Name for c in self.components[1:-1])
        self.splitter = splitter
        
    def set_mixer(self):
        mixer = self.idf.newidfobject(
            "CONNECTOR:MIXER", 
            self.connectorlist.Connector_2_Name)
        mixer.Outlet_Branch_Name = self.components[-1].Name
        mixer.obj.extend(c.Name for c in self.components[1:-1])
        self.mixer = mixer


class AirHalfLoop(HalfLoop):
    
    def set_connectorlist(self):
        """A list of connectors on the half loop.
        """
        if self.side == 'supply':
            connectorlist = self.idf.getmakeidfobject(
                "CONNECTORLIST", self.loop.fieldvalues[6])
        connectorlist.Connector_1_Object_Type = "Connector:Splitter"
        connectorlist.Connector_1_Name = "%s_supply_splitter" % self.loop.Name
        connectorlist.Connector_2_Object_Type = "Connector:Mixer"
        connectorlist.Connector_2_Name = "%s_supply_mixer" % self.loop.Name
        
        self.connectorlist = connectorlist

    def set_splitter(self):
        """Make AirLoopHVAC:ZoneSplitter.
        """
        idf = self.idf
        zones = self.demand[1:-1]
        z_splitter = idf.newidfobject("AIRLOOPHVAC:ZONESPLITTER")
        z_splitter.Name = "%s Demand Side Splitter" % self.loop.Name
        z_splitter.Inlet_Node_Name = self.loop.Demand_Side_Inlet_Node_Names
        for i, zone in enumerate(zones):
            z_equipconn = modeleditor.getobjects(
                idf.idfobjects, idf.model, idf.idd_info, 
                "ZoneHVAC:EquipmentConnections".upper(),
                **dict(Zone_Name=zone.Name))[0]
            fld = "Outlet_%s_Node_Name" % (i + 1, )
            z_splitter[fld] = z_equipconn.Zone_Air_Inlet_Node_or_NodeList_Name
        

class Branch(EppyHVAC):
    """Branches contain one or more components in series.
    """
    
    def __init__(self, idf, branchname, components=None):
        """Make a branch with components, or just a pipe
        """
            
        if components:
            components = [Component(idf, bunch=c) for c in components]
        else:
            pipename = "%s_pipe" % branchname
            pipe = pipecomponent(idf, pipename)
            components = [pipe]
        self.components = components  # A list of components on the branch
        self.idf = idf
        self.name = branchname
        self.set_components()
    
    def __len__(self):
        return len(self.components)
    

    def set_components(self):
        branch = self.idf.newidfobject("BRANCH", self.name)
        
        for i, component in enumerate(self.components, 1):
            # get/set the inlet and outlet node names
            self.set_inlet_outlet_names(i, component)
            # intermediate ones are named as c1_c2_inlet and c1_c2_outlet
            branch['Component_%i_Object_Type' % i] = component.key
            branch['Component_%i_Name' % i] = component.Name
            branch['Component_%i_Inlet_Node_Name' % i] = component.inlet
            branch['Component_%i_Outlet_Node_Name' % i] = component.outlet
            branch['Component_%i_Branch_Control_Type' % i] = "Bypass"
    
        self.bunch = branch

    def set_inlet_outlet_names(self, i, component):
        """Set the names of inlets and outlets on a branch.
        
        Only if they are not already set.
        
        Paramaters
        ----------
        i : int
            Component number on branch.
        component : Component object
            The component to set node names for.
        
        """
        # first one is the c1 inlet
        if component.inlet == '':
            if i == 1:
                inlet_name = '%s_inlet' % component.Name
            else:
                inlet_name = '%s_%s_inlet' % (
                    self.components[i - 2].Name, self.components[i - 1].Name)
            component.set_inlet(inlet_name)
            # last one is the cn outlet
        if component.outlet == '':
            if i == len(self):
                outlet_name = '%s_outlet' % component.Name
            else:
                outlet_name = '%s_%s_outlet' % (
                    self.components[i - 1].Name, self.components[i].Name)
            component.set_outlet(outlet_name)


class Connector(EppyHVAC):
    """Connectors (splitters or mixers) join branches together.
    """
    def __init__(self, idf):
        pass
    
    def inlet_branches(self):
        """A list of inlet branches. Only one if a splitter.
        """
        pass
    
    def outlet_branches(self):
        """A list of outlet branches. Only one if a mixer.
        """
        pass
    
    
class Component(EppyHVAC):
    """Components can be pipes, ducts, or an item of plant or demand equipment.
    
    They should have an inlet node and an outlet node.
    
    """
    
    def __init__(self, idf, *args, **kwargs):
        self.idf = idf
        try:
            self.bunch = kwargs['bunch']
        except KeyError:
            key = kwargs.pop('key')
            name = kwargs.pop('name')
            self.bunch = self.idf.newidfobject(key, name, **kwargs)
    
    @property
    def inlet(self):
        field = getfieldnamesendswith(self.bunch, 'Inlet_Node_Name')[0]
        return self[field]
    
    def set_inlet(self, name):
        field = getfieldnamesendswith(self.bunch, 'Inlet_Node_Name')[0]
        self.bunch[field] = name
    
    @property
    def outlet(self):
        field = getfieldnamesendswith(self.bunch, 'Outlet_Node_Name')[0]
        return self[field]

    def set_outlet(self, name):
        field = getfieldnamesendswith(self.bunch, 'Outlet_Node_Name')[0]
        self.bunch[field] = name
    
    def __repr__(self):
        return "Component(%s, %s)" % (self.idf, self.bunch)
    

def pipecomponent(idf, pname):
    """make a pipe component
    generate inlet outlet names"""
    pipe = Component(
        idf, key='PIPE:ADIABATIC', name=pname,
        Inlet_Node_Name="%s_inlet" % pname,
        Outlet_Node_Name="%s_outlet" % pname)
    return pipe


def test_makeairloop():
    """pytest for makeairloop"""
    tdata = (
        "Air Loop",
        ['sb0', ['sb1', 'sb2', 'sb3'], 'sb4'],
        ['db0', ['z1', 'z2', 'z3'], 'db4'],
        """AIRTERMINAL:SINGLEDUCT:UNCONTROLLED, db1DirectAir, , db1 Inlet Node, autosize;  ZONEHVAC:EQUIPMENTLIST, db1 equip list, AirTerminal:SingleDuct:Uncontrolled, db1DirectAir, 1, 1;  ZONEHVAC:EQUIPMENTCONNECTIONS, db1, db1 equip list, db1 Inlet Node, , db1 Node, db1 Outlet Node;  AIRLOOPHVAC, p_loop, , , 0, p_loop Branchs, p_loop Connectors, p_loop Supply Side Inlet, p_loop Demand Outlet, p_loop Demand Inlet, p_loop Supply Side Outlet;  AIRLOOPHVAC:ZONESPLITTER, p_loop Demand Side Splitter, p_loop Demand Inlet, db1 Inlet Node;  AIRLOOPHVAC:SUPPLYPATH, p_loopSupplyPath, p_loop Demand Inlet, AirLoopHVAC:ZoneSplitter, p_loop Demand Side Splitter;  AIRLOOPHVAC:ZONEMIXER, p_loop Demand Side Mixer, p_loop Demand Outlet, db1 Outlet Node;  AIRLOOPHVAC:RETURNPATH, p_loopReturnPath, p_loop Demand Outlet, AirLoopHVAC:ZoneMixer, p_loop Demand Side Mixer;  BRANCH, sb0, 0, , Pipe:Adiabatic, sb0_pipe, sb0_pipe_inlet, sb0_pipe_outlet, Bypass;  BRANCH, sb1, 0, , Pipe:Adiabatic, sb1_pipe, sb1_pipe_inlet, sb1_pipe_outlet, Bypass;  BRANCH, sb2, 0, , Pipe:Adiabatic, sb2_pipe, sb2_pipe_inlet, sb2_pipe_outlet, Bypass;  BRANCH, sb3, 0, , Pipe:Adiabatic, sb3_pipe, sb3_pipe_inlet, sb3_pipe_outlet, Bypass;  BRANCH, sb4, 0, , Pipe:Adiabatic, sb4_pipe, sb4_pipe_inlet, sb4_pipe_outlet, Bypass;  BRANCHLIST, p_loop Branchs, sb0, sb1, sb2, sb3, sb4;  CONNECTOR:SPLITTER, p_loop_supply_splitter, sb0, sb1, sb2, sb3;  CONNECTOR:MIXER, p_loop_supply_mixer, sb4, sb1, sb2, sb3;  CONNECTORLIST, p_loop Connectors, Connector:Splitter, p_loop_supply_splitter, Connector:Mixer, p_loop_supply_mixer;  PIPE:ADIABATIC, sb0_pipe, sb0_pipe_inlet, sb0_pipe_outlet;  PIPE:ADIABATIC, sb1_pipe, sb1_pipe_inlet, sb1_pipe_outlet;  PIPE:ADIABATIC, sb2_pipe, sb2_pipe_inlet, sb2_pipe_outlet;  PIPE:ADIABATIC, sb3_pipe, sb3_pipe_inlet, sb3_pipe_outlet;  PIPE:ADIABATIC, sb4_pipe, sb4_pipe_inlet, sb4_pipe_outlet;  
"""
    ) # loopname, sloop, dloop, expected

    loopname, sloop, dloop, expected = tdata
    fhandle = StringIO("")
    idf1 = IDF(fhandle)
    loop = makeairloop(idf1, loopname, sloop, dloop)
    idf1.printidf()
    #===========================================================================
    # idf2 = IDF(StringIO(expected))
    # idf2.outputtype = 'compressed'
    # idf2.printidf()
    # result = idf1.idfstr()
    # expected = idf2.idfstr()
    # assert result == expected
    #===========================================================================
    

def test_branch_no_components():
    idf = IDF()
    idf.new()
    branch = Branch(idf, 'default')
    assert len(branch.components) == 1
    assert len(branch) == 1
    assert branch.components[0].key == 'PIPE:ADIABATIC'
    assert branch.components[0].Name == 'default_pipe'
    
    assert branch.components[0].Inlet_Node_Name == branch.components[0].inlet
    assert branch.components[0].Outlet_Node_Name == branch.components[0].outlet

    print(branch)

def test_branch_one_component():
    idf = IDF()
    idf.new()
    boiler = idf.newidfobject('BOILER:HOTWATER', 'boiler')
    components = [boiler] 
    branch = Branch(idf, 'boiler_branch', components)

    assert len(branch.components) == 1
    assert len(branch) == 1
    assert branch.components[0].key == 'BOILER:HOTWATER'
    assert branch.components[0].Name == 'boiler'
    assert (branch.components[0].Boiler_Water_Inlet_Node_Name == 
            branch.components[0].inlet)
    assert (branch.components[0].Boiler_Water_Outlet_Node_Name ==
            branch.components[0].outlet)
    
def test_branch_two_components():
    idf = IDF()
    idf.new()
    boiler = idf.newidfobject('BOILER:HOTWATER', 'boiler')
    pipe = idf.newidfobject('PIPE:ADIABATIC', 'pipe')
    components = [boiler, pipe] 
    branch = Branch(idf, 'boiler_and_pipe_branch', components)
    assert len(branch.components) == 2
    assert len(branch) == 2
    print(branch.components[0])
    print(branch)

def test_plantloop_with_components():
    idf = IDF()
    idf.new()
    boiler1 = idf.newidfobject('BOILER:HOTWATER', 'boiler1')
    boiler2 = idf.newidfobject('BOILER:HOTWATER', 'boiler2')
    sloop = ['s1', [boiler1, boiler2], 's2'] 
    baseboard = idf.newidfobject(
        'ZONEHVAC:BASEBOARD:CONVECTIVE:WATER', 'baseboard')
    dloop = ['d1', [baseboard], 'd2'] 
    loop = makeplantloop(idf, 'Plant Loop', sloop, dloop)
    idf.printidf()
    idf.run()
    