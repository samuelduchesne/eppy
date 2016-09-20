# Copyright (c) 2012 Santosh Philip
# Copyright (c) 2016 Jamie Bull
# =======================================================================
#  Distributed under the MIT License.
#  (See accompanying file LICENSE or copy at
#  http://opensource.org/licenses/MIT)
# =======================================================================
"""Make EnergyPlus loops.
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import copy

from eppy.bunchhelpers import sanitizefieldname

import eppy.bunch_subclass as bunch_subclass
import eppy.modeleditor as modeleditor


class WhichLoopError(Exception):
    pass


def makeplantloop(idf, loopname, sloop, dloop):
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
    return PlantLoop(idf, loopname, sloop, dloop)


def makecondenserloop(idf, loopname, sloop, dloop):
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
    return  CondenserLoop(idf, loopname, sloop, dloop)


def makeairloop(idf, loopname, sloop, dloop):
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
    return AirLoopHVAC(idf, loopname, sloop, dloop)


class Loop(object):
    """Parent class for PlantLoop, CondenserLoop and AirLoopHVAC objects.
    """
    def __init__(self, idf, loopname, sloop, dloop):
        """Create all required objects in the IDF.
        
        Parameters
        ----------
        idf : IDF object
            The IDF.
        loopname : str
            Name for the loop.
        sloop : list
            Names for branches on the supply side of the loop.
        dloop : list
            Names for branches on the demand side of the loop.
        """
        self.idf = idf
        self.loopname = loopname
        self.sloop = sloop
        self.dloop = dloop
        self.makeloop()
    
    def __getattr__(self, name):
        return self.loop[name]
            
    def __setattr__(self, name, value):
        super(Loop, self).__setattr__(name, value)
    
    def __getitem__(self, name):
        return self.loop[name]
            
    def __setitem__(self, name, value):
        self.loop[name] = value
            
    @property
    def looptype(self):
        """The loop type, e.g. 'PLANTLOOP'.
        
        Returns
        -------
        str
        
        """
        return type(self).__name__.upper()
    
    def makeloop(self):
        """Make all the IDF objects and add them to the IDF.
        """
        self.loop = self.idf.newidfobject(self.looptype, self.loopname)
        self.initialise_loopfields()
        
        self.make_branchlists()        
        self.make_supply_branches()
        self.make_demand_branches()

        self.rename_endpoints()
        
        self.make_supply_connectorlists()
        self.make_demand_connectorlists()

        self.make_splitters_and_mixers()
    
    def initialise_loopfields(self):
        """Initialise fields in a loop.
        
        These vary by type of loop. The names are stored in each subclass's
        loopfields attribute.
        
        """
        # for use in bunch
        flnames = [sanitizefieldname(f) for f in self.loopfields]
        # simplify naming
        fields = simplify_names(self.loopfields)
        # make fieldnames in the loop
        fieldnames = ['%s %s' % (self.Name, field) for field in fields]
        for fieldname, thefield in zip(fieldnames, flnames):
            self[thefield] = fieldname

    def rename_endpoints(self):
        """Rename inlet and outlet of the endpoints of the loop.
        """
        # supply side
        # rename inlet outlet of endpoints of loop - rename in branch
        anode = "Component_1_Inlet_Node_Name"
        self.s_branches[0][anode] = self[self.supply_inletnode]
        anode = "Component_1_Outlet_Node_Name"
        self.s_branches[-1][anode] = self[self.supply_outletnode]
        # rename inlet outlet of endpoints of loop - rename in pipe
        pipe_name = self.s_branches[0]['Component_1_Name'] # get the pipe name
        apipe = self.idf.getobject('PIPE:ADIABATIC', pipe_name) # get pipe
        apipe.Inlet_Node_Name = self[self.supply_inletnode]
        pipe_name = self.s_branches[-1]['Component_1_Name'] # get the pipe name
        apipe = self.idf.getobject('PIPE:ADIABATIC', pipe_name) # get pipe
        apipe.Outlet_Node_Name = self[self.supply_outletnode]

        # demand side
        # rename inlet outlet of endpoints of loop - rename in branch
        anode = "Component_1_Inlet_Node_Name"
        sameinnode = "Demand_Side_Inlet_Node_Name"
        self.d_branches[0][anode] = self[sameinnode]
        anode = "Component_1_Outlet_Node_Name"
        sameoutnode = "Demand_Side_Outlet_Node_Name"
        self.d_branches[-1][anode] = self[sameoutnode]
        # rename inlet outlet of endpoints of loop - rename in pipe
        pipe_name = self.d_branches[0]['Component_1_Name'] # get the pipe name
        apipe = self.idf.getobject('PIPE:ADIABATIC', pipe_name) # get pipe
        apipe.Inlet_Node_Name = self[sameinnode]
        pipe_name = self.d_branches[-1]['Component_1_Name'] # get the pipe name
        apipe = self.idf.getobject('PIPE:ADIABATIC', pipe_name) # get pipe
        apipe.Outlet_Node_Name = self[sameoutnode]
            
    def make_supply_branches(self):
        """
        Make a pipe branch for all supply branches in the loop and add them to 
        the supply branchlist.
        
        """
        supply_branchnames = flattencopy(self.sloop)
        for branchname in supply_branchnames:
            self.supply_branchlist.obj.append(branchname)
        supply_branches = [pipebranch(self.idf, branchname) 
                           for branchname in supply_branchnames]
        self.s_branches = supply_branches
        
    def make_demand_branches(self):
        """
        Make a pipe branch for all demand branches in the loop and add them to
        the demand branchlist.
        
        """
        demand_branchnames = flattencopy(self.dloop)
        for branchname in demand_branchnames:
            self.demand_branchlist.obj.append(branchname)

        demand_branches = [pipebranch(self.idf, branch)
                           for branch in demand_branchnames]
        self.d_branches = demand_branches

    def make_splitters_and_mixers(self):
        """
        Make splitter and mixer objects for supply and demand sides of the loop
        and add them to the supply and demand connector lists.
        
        """
        supply_splitter = self.idf.newidfobject(
            "CONNECTOR:SPLITTER", 
            self.s_connlist.Connector_1_Name)
        supply_splitter.obj.extend([self.sloop[0]] + self.sloop[1])
        supply_mixer = self.idf.newidfobject(
            "CONNECTOR:MIXER", 
            self.s_connlist.Connector_2_Name)
        supply_mixer.obj.extend([self.sloop[-1]] + self.sloop[1])
    
        demand_splitter = self.idf.newidfobject(
            "CONNECTOR:SPLITTER", 
            self.d_connlist.Connector_1_Name)
        demand_splitter.obj.extend([self.dloop[0]] + self.dloop[1])
        demand_mixer = self.idf.newidfobject(
            "CONNECTOR:MIXER", 
            self.d_connlist.Connector_2_Name)
        demand_mixer.obj.extend([self.dloop[-1]] + self.dloop[1])
    
    def replacebranch(self, branch, newcomponents, fluid=None):
        """Replace the components in the branch.
        
        Parameters
        ----------
        branch : EpBunch
            The branch to be replaced.
        newcomponents : list
            List of EpBunch objects for the replacement components.
        fluid : str, optional
            The type of fluid used in the branch. Default is None, which
            equates to a blank fluid field in the BRANCH object.
        
        Returns
        -------
        EpBunch
            The updated BRANCH object.
            
        """
        if fluid is None:
            # TODO: unit test
            fluid = ''
        newcomponents = _clean_listofcomponents(newcomponents)
        # change the node names in the component
        connectcomponents(self.idf, newcomponents, fluid=fluid)
        # fill in the new components with the node names into this branch
        componentsintobranch(self.idf, branch, newcomponents, fluid=fluid)    
    
        # for use in bunch
        flnames = [field.replace(' ', '_') for field in self.loopfields]
        self.replace_supplyside(branch, fluid, flnames)
                                
        if fluid.upper() == 'WATER':
            self.replace_demandside(branch, fluid, flnames)
        renamenodes(self.idf, 'node')
    
        return branch
    
    def replace_supplyside(self, branch, fluid, flnames):
        """Rename components, nodes, etc on the supply side of the loop.
        
        Parameters
        ----------
        branch : EpBunch
            The branch to be replaced.
        fluid : str
            The type of fluid used in the branch.
        flnames : list
            Sanitised loop fieldnames for use when updating the LOOP object.
            
        """
        for i in range(1, 100000): # large range to hit end
            try:
                fieldname = 'Connector_%s_Object_Type' % (i, )
                ctype = self.s_connlist[fieldname]
            except bunch_subclass.BadEPFieldError:
                break
            if ctype.strip() == '':
                # TODO: unit test
                break  # this is never hit in unit tests
            fieldname = 'Connector_%s_Name' % (i, )
            cname = self.s_connlist[fieldname]
            connector = self.idf.getobject(ctype.upper(), cname)
            if connector.key == 'CONNECTOR:SPLITTER':
                firstbranchname = connector.Inlet_Branch_Name
                cbranchname = firstbranchname
                isfirst = True
            if connector.key == 'CONNECTOR:MIXER':
                lastbranchname = connector.Outlet_Branch_Name
                cbranchname = lastbranchname
                isfirst = False
            if cbranchname == branch.Name:
                # rename end nodes
                comps = getbranchcomponents(self.idf, branch)
                if isfirst:
                    comp = comps[0]
                    inletnodename = getnodefieldname(
                        comp,
                        "Inlet_Node_Name", fluid)
                    comp[inletnodename] = [
                        comp[inletnodename],
                        self[flnames[0]]] # Plant_Side_Inlet_Node_Name
                else:
                    # TODO: unit test
                    comp = comps[-1]
                    outletnodename = getnodefieldname(
                        comp,
                        "Outlet_Node_Name", fluid)
                    comp[outletnodename] = [
                        comp[outletnodename],
                        self[flnames[1]]] # .Plant_Side_Outlet_Node_Name
    
    def replace_demandside(self, branch, fluid, flnames):    
        """Rename components, nodes, etc on the demand side of the loop.
        
        Parameters
        ----------
        branch : EpBunch
            The branch to be replaced.
        fluid : str
            The type of fluid used in the branch.
        flnames : list
            Sanitised loop fieldnames for use when updating the LOOP object.
            
        """
        for i in range(1, 100000): # large range to hit end
            try:
                fieldname = 'Connector_%s_Object_Type' % (i, )
                ctype = self.d_connlist[fieldname]
            except bunch_subclass.BadEPFieldError:
                break
            if ctype.strip() == '':
                # TODO: unit test
                break
            fieldname = 'Connector_%s_Name' % (i, )
            cname = self.d_connlist[fieldname]
            connector = self.idf.getobject(ctype.upper(), cname)
            if connector.key == 'CONNECTOR:SPLITTER':
                firstbranchname = connector.Inlet_Branch_Name
                cbranchname = firstbranchname
                isfirst = True
            if connector.key == 'CONNECTOR:MIXER':
                lastbranchname = connector.Outlet_Branch_Name
                cbranchname = lastbranchname
                isfirst = False
            if cbranchname == branch.Name:
                # TODO: unit test
                # rename end nodes
                comps = getbranchcomponents(self.idf, branch)
                if isfirst:
                    comp = comps[0]
                    inletnodename = getnodefieldname(
                        comp,
                        "Inlet_Node_Name", fluid)
                    comp[inletnodename] = [
                        comp[inletnodename],
                        self[flnames[4]]] #.Demand_Side_Inlet_Node_Name
                if not isfirst:
                    comp = comps[-1]
                    outletnodename = getnodefieldname(
                        comp,
                        "Outlet_Node_Name", fluid)
                    comp[outletnodename] = [
                        comp[outletnodename],
                        self[flnames[5]]] # .Demand_Side_Outlet_Node_Name


class PlantLoop(Loop):
    """Object representing an EnergyPlus PLANTLOOP object.
    """
    
    loopfields = [
        'Plant Side Inlet Node Name',
        'Plant Side Outlet Node Name',
        'Plant Side Branch List Name',
        'Plant Side Connector List Name',
        'Demand Side Inlet Node Name',
        'Demand Side Outlet Node Name',
        'Demand Side Branch List Name',
        'Demand Side Connector List Name']
    
    supply_inletnode = "Plant_Side_Inlet_Node_Name"
    supply_outletnode = "Plant_Side_Outlet_Node_Name"

    def make_branchlists(self):
        """Initialise BRANCHLIST objects for supply and demand side.
        """
        self.supply_branchlist = self.idf.newidfobject(
            "BRANCHLIST", 
            self.Plant_Side_Branch_List_Name)
        self.demand_branchlist = self.idf.newidfobject(
            "BRANCHLIST", 
            self.Demand_Side_Branch_List_Name)

    def make_supply_connectorlists(self):
        """Initialise CONNECTORLIST object for supply side.
        """
        s_connlist = self.idf.newidfobject(
            "CONNECTORLIST", self.Plant_Side_Connector_List_Name)
        s_connlist.Connector_1_Object_Type = "Connector:Splitter"
        s_connlist.Connector_1_Name = "%s_supply_splitter" % self.Name
        s_connlist.Connector_2_Object_Type = "Connector:Mixer"
        s_connlist.Connector_2_Name = "%s_supply_mixer" % self.Name
        self.s_connlist = s_connlist
    
    def make_demand_connectorlists(self):
        """Initialise CONNECTORLIST object for demand side.
        """
        d_connlist = self.idf.newidfobject(
            "CONNECTORLIST", 
            self.Demand_Side_Connector_List_Name)
        d_connlist.Connector_1_Object_Type = "Connector:Splitter"
        d_connlist.Connector_1_Name = "%s_demand_splitter" % self.Name
        d_connlist.Connector_2_Object_Type = "Connector:Mixer"
        d_connlist.Connector_2_Name = "%s_demand_mixer" % self.Name
        self.d_connlist = d_connlist


class CondenserLoop(Loop):
    """Object representing an EnergyPlus CONDENSERLOOP object.
    """
    
    loopfields = [
        'Condenser Side Inlet Node Name',
        'Condenser Side Outlet Node Name',
        'Condenser Side Branch List Name',
        'Condenser Side Connector List Name',
        'Demand Side Inlet Node Name',
        'Demand Side Outlet Node Name',
        'Condenser Demand Side Branch List Name',
        'Condenser Demand Side Connector List Name']

    supply_inletnode = "Condenser_Side_Inlet_Node_Name"
    supply_outletnode = "Condenser_Side_Outlet_Node_Name"

    def make_branchlists(self):
        """Initialise BRANCHLIST objects for supply and demand side.
        """
        self.supply_branchlist = self.idf.newidfobject(
            "BRANCHLIST", 
            self.Condenser_Side_Branch_List_Name)
        self.demand_branchlist = self.idf.newidfobject(
            "BRANCHLIST", 
            self.Condenser_Demand_Side_Branch_List_Name)

    def make_supply_connectorlists(self):
        """Initialise CONNECTORLIST object for supply side.
        """
        s_connlist = self.idf.newidfobject(
            "CONNECTORLIST", self.Condenser_Side_Connector_List_Name)
        s_connlist.Connector_1_Object_Type = "Connector:Splitter"
        s_connlist.Connector_1_Name = "%s_supply_splitter" % self.Name
        s_connlist.Connector_2_Object_Type = "Connector:Mixer"
        s_connlist.Connector_2_Name = "%s_supply_mixer" % self.Name
        self.s_connlist = s_connlist

    def make_demand_connectorlists(self):
        """Initialise CONNECTORLIST object for demand side.
        """
        d_connlist = self.idf.newidfobject(
            "CONNECTORLIST", 
            self.Condenser_Demand_Side_Connector_List_Name)
        d_connlist.Connector_1_Object_Type = "Connector:Splitter"
        d_connlist.Connector_1_Name = "%s_demand_splitter" % self.Name
        d_connlist.Connector_2_Object_Type = "Connector:Mixer"
        d_connlist.Connector_2_Name = "%s_demand_mixer" % self.Name
        self.d_connlist = d_connlist


class AirLoopHVAC(Loop):
    """Object representing an EnergyPlus AIRLOOPHVAC object.
    """
    
    loopfields = [
        'Branch List Name',
        'Connector List Name',
        'Supply Side Inlet Node Name',
        'Demand Side Outlet Node Name',
        'Demand Side Inlet Node Names',
        'Supply Side Outlet Node Names']
    
    def make_branchlists(self):
        """Initialise BRANCHLIST object for supply side.
        """
        self.supply_branchlist = self.idf.newidfobject(
            "BRANCHLIST", 
            self.Branch_List_Name)
    
    def make_supply_branches(self):
        supply_branchnames = flattencopy(self.sloop)
        for branchname in supply_branchnames:
            self.supply_branchlist.obj.append(branchname)
        supply_branches = [ductbranch(self.idf, branchname) 
                           for branchname in supply_branchnames]
        self.s_branches = supply_branches
        
    def make_demand_branches(self):
        """Make components on the demand side of the loop.
        
        This is quite different from the method in the parent class since the
        way the EnergyPlus handles air loops is different for how it handles
        water loops (PLANTLOOP / CONDENSERLOOP objects).
        
        """
        self.d_branches = []  # this is intentionally set as an empty list
        _inlet, zones, _outlet = self.dloop
        #ZoneHVAC:EquipmentConnections
        for zone in zones:
            equipconn = self.idf.newidfobject("ZONEHVAC:EQUIPMENTCONNECTIONS")
            equipconn.Zone_Name = zone
            fldname = "Zone_Conditioning_Equipment_List_Name"
            equipconn[fldname] = "%s equip list" % (zone, )
            fldname = "Zone_Air_Inlet_Node_or_NodeList_Name"
            equipconn[fldname] = "%s Inlet Node" % (zone, )
            fldname = "Zone_Air_Node_Name"
            equipconn[fldname] = "%s Node" % (zone, )
            fldname = "Zone_Return_Air_Node_Name"
            equipconn[fldname] = "%s Outlet Node" % (zone, )
        
        # make ZoneHVAC:EquipmentList
        for zone in zones:
            z_equiplst = self.idf.newidfobject("ZONEHVAC:EQUIPMENTLIST")
            z_equipconn = modeleditor.getobjects(
                self.idf.idfobjects, self.idf.model, self.idf.idd_info, 
                "ZONEHVAC:EQUIPMENTCONNECTIONS",
                **dict(Zone_Name=zone))[0]
            z_equiplst.Name = z_equipconn.Zone_Conditioning_Equipment_List_Name
            fld = "Zone_Equipment_1_Object_Type"
            z_equiplst[fld] = "AirTerminal:SingleDuct:Uncontrolled"
            z_equiplst.Zone_Equipment_1_Name = "%sDirectAir" % (zone, )
            z_equiplst.Zone_Equipment_1_Cooling_Sequence = 1
            z_equiplst.Zone_Equipment_1_Heating_or_NoLoad_Sequence = 1
        
        # make AirTerminal:SingleDuct:Uncontrolled
        for zone in zones:
            z_equipconn = modeleditor.getobjects(
                self.idf.idfobjects, self.idf.model, self.idf.idd_info, 
                "ZONEHVAC:EQUIPMENTCONNECTIONS", #places=7,
                **dict(Zone_Name=zone))[0]
            key = "AIRTERMINAL:SINGLEDUCT:UNCONTROLLED"
            z_airterm = self.idf.newidfobject(key)
            z_airterm.Name = "%sDirectAir" % (zone, )
            fld1 = "Zone_Supply_Air_Node_Name"
            fld2 = "Zone_Air_Inlet_Node_or_NodeList_Name"
            z_airterm[fld1] = z_equipconn[fld2]
            z_airterm.Maximum_Air_Flow_Rate = 'autosize'
    
    def rename_endpoints(self):
        """Not implemented for AirLoopHVAC.
        """
        return
    
    def make_supply_connectorlists(self):
        """Initialise CONNECTORLIST object for supply side.
        """
        self.s_connlist = self.idf.newidfobject(
            "CONNECTORLIST", self.Connector_List_Name)
        self.s_connlist.Connector_1_Object_Type = "Connector:Splitter"
        self.s_connlist.Connector_1_Name = "%s_supply_splitter" % self.Name
        self.s_connlist.Connector_2_Object_Type = "Connector:Mixer"
        self.s_connlist.Connector_2_Name = "%s_supply_mixer" % self.Name

    def make_demand_connectorlists(self):
        """Not implemented for AirLoopHVAC.
        """
        return
    
    def make_splitters_and_mixers(self):
        """
        Make zone splitter and zone mixer objects for supply and demand sides
        of the loop, add them to the supply and demand connector lists, and
        make supply and return path objects.
        
        """
        supply_splitter = self.idf.newidfobject(
            "CONNECTOR:SPLITTER", 
            self.s_connlist.Connector_1_Name)
        supply_splitter.obj.extend([self.sloop[0]] + self.sloop[1])
        supply_mixer = self.idf.newidfobject(
            "CONNECTOR:MIXER", 
            self.s_connlist.Connector_2_Name)
        supply_mixer.obj.extend([self.sloop[-1]] + self.sloop[1])
    
        _inlet, zones, _outlet = self.dloop
        # make AirLoopHVAC:ZoneSplitter
        z_splitter = self.idf.newidfobject("AIRLOOPHVAC:ZONESPLITTER")
        z_splitter.Name = "%s Demand Side Splitter" % self.Name
        z_splitter.Inlet_Node_Name = self.Demand_Side_Inlet_Node_Names
        for i, zone in enumerate(zones):
            z_equipconn = modeleditor.getobjects(
                self.idf.idfobjects, self.idf.model, self.idf.idd_info, 
                "ZONEHVAC:EQUIPMENTCONNECTIONS",
                **dict(Zone_Name=zone))[0]
            fld = "Outlet_%s_Node_Name" % (i + 1, )
            z_splitter[fld] = z_equipconn.Zone_Air_Inlet_Node_or_NodeList_Name
        
        # make AirLoopHVAC:SupplyPath
        z_supplypth = self.idf.newidfobject("AIRLOOPHVAC:SUPPLYPATH")
        z_supplypth.Name = "%sSupplyPath" % self.Name
        fld1 = "Supply_Air_Path_Inlet_Node_Name"
        fld2 = "Demand_Side_Inlet_Node_Names"
        z_supplypth[fld1] = self[fld2]
        z_supplypth.Component_1_Object_Type = "AirLoopHVAC:ZoneSplitter"
        z_supplypth.Component_1_Name = z_splitter.Name
        
        # make AirLoopHVAC:ZoneMixer
        z_mixer = self.idf.newidfobject("AIRLOOPHVAC:ZONEMIXER")
        z_mixer.Name = "%s Demand Side Mixer" % self.Name
        z_mixer.Outlet_Node_Name = self.Demand_Side_Outlet_Node_Name
        for i, zone in enumerate(zones):
            z_equipconn = modeleditor.getobjects(
                self.idf.idfobjects, self.idf.model, self.idf.idd_info, 
                "ZONEHVAC:EQUIPMENTCONNECTIONS", #places=7,
                **dict(Zone_Name=zone))[0]
            fld = "Inlet_%s_Node_Name" % (i + 1, )
            z_mixer[fld] = z_equipconn.Zone_Return_Air_Node_Name
    
        # make AirLoopHVAC:ReturnPath
        z_returnpth = self.idf.newidfobject("AIRLOOPHVAC:RETURNPATH")
        z_returnpth.Name = "%sReturnPath" % self.Name
        fld1 = "Return_Air_Path_Outlet_Node_Name"
        fld2 = "Demand_Side_Outlet_Node_Name"
        z_returnpth[fld1] = self[fld2]
        z_returnpth.Component_1_Object_Type = "AirLoopHVAC:ZoneMixer"
        z_returnpth.Component_1_Name = z_mixer.Name
    
    
def pipebranch(idf, branchname):
    """Make a branch with a pipe using standard inlet and outlet names.
    
    Parameters
    ----------
    idf : IDF
        The IDF.
    branchname : str
        Name of the branch for the pipe.
    
    Returns
    -------
    EpBunch
        The BRANCH object.
        
    """
    # make the pipe component first
    pname = "%s_pipe" % (branchname, )
    pipe = pipecomponent(idf, pname)
    # now make the branch with the pipe in it
    branch = idf.getmakeidfobject("BRANCH", branchname)
    branch.Component_1_Object_Type = 'Pipe:Adiabatic'
    branch.Component_1_Name = pname
    branch.Component_1_Inlet_Node_Name = pipe.Inlet_Node_Name
    branch.Component_1_Outlet_Node_Name = pipe.Outlet_Node_Name
    branch.Component_1_Branch_Control_Type = "Bypass"
    return branch


def pipecomponent(idf, pname):
    """Make a pipe component using standard inlet and outlet names.
    
    Parameters
    ----------
    idf : IDF
        The IDF.
    pname : str
        Name of the pipe.
    
    Returns
    -------
    EpBunch
        The PIPE:ADIABATIC object.
        
    """
    pipe = idf.getmakeidfobject("PIPE:ADIABATIC", pname)
    pipe.Inlet_Node_Name = "%s_inlet" % (pname, )
    pipe.Outlet_Node_Name = "%s_outlet" % (pname, )
    return pipe


def ductbranch(idf, bname):
    """Make a branch with a duct using standard inlet and outlet names.
    
    Parameters
    ----------
    idf : IDF
        The IDF.
    bname : str
        Name of the branch.
    
    Returns
    -------
    EpBunch
        The BRANCH object.
        
    """
    # make the duct component first
    pname = "%s_duct" % (bname, )
    duct = ductcomponent(idf, pname)
    # now make the branch with the duct in it
    branch = idf.getmakeidfobject("BRANCH", bname)
    branch.Component_1_Object_Type = 'duct'
    branch.Component_1_Name = pname
    branch.Component_1_Inlet_Node_Name = duct.Inlet_Node_Name
    branch.Component_1_Outlet_Node_Name = duct.Outlet_Node_Name
    branch.Component_1_Branch_Control_Type = "Bypass"
    return branch


def ductcomponent(idf, dname):
    """Make a duct component using standard inlet and outlet names.
    
    Parameters
    ----------
    idf : IDF
        The IDF.
    dname : str
        Name of the duct.
    
    Returns
    -------
    EpBunch
        The DUCT object.
        
    """
    duct = idf.getmakeidfobject("DUCT", dname)
    duct.Inlet_Node_Name = "%s_inlet" % (dname, )
    duct.Outlet_Node_Name = "%s_outlet" % (dname, )
    return duct


def getbranchcomponents(idf, branch, utest=False):
    """Get the components of a branch.
    
    Parameters
    ----------
    idf : IDF
        The IDF.
    branch : EpBunch
        the branch to look on.
    utest : bool
        Flag whether we are in a unit test.
    
    Returns
    -------
    list
        Either a list of EpBunch objects, or a list of tuples if unit testing.
    
    """
    fobjtype = 'Component_%s_Object_Type'
    fobjname = 'Component_%s_Name'
    complist = []
    for i in range(1, 100000):
        try:
            objtype = branch[fobjtype % (i, )]
            if objtype.strip() == '':
                break
            objname = branch[fobjname % (i, )]
            complist.append((objtype, objname))
        except bunch_subclass.BadEPFieldError:
            # TODO: unit test
            # When should this be triggered?
            break
    if utest:
        return complist
    else:
        return [idf.getobject(ot, on) for ot, on in complist]


def renamenodes(idf, fieldtype):
    """Rename all changed nodes.
    
    This will be stored as a list.
    
    Parameters
    ----------
    idf : IDF
        The IDF.
    fieldtype : str
        TODO: What is this? node
        
    """
    # get the values to be replaced
    renameds = []
    for key in idf.model.dtls:
        for idfobject in idf.idfobjects[key]:
            for fieldvalue in idfobject.fieldvalues:
                if type(fieldvalue) is list:
                    if fieldvalue not in renameds:
                        cpvalue = copy.copy(fieldvalue)
                        renameds.append(cpvalue)

    # do the renaming
    for key in idf.model.dtls:
        for idfobject in idf.idfobjects[key]:
            for i, fieldvalue in enumerate(idfobject.fieldvalues):
                itsidd = idfobject.objidd[i]
                if 'type' in itsidd:
                    if itsidd['type'][0] == fieldtype:
                        tempdct = dict(renameds)
                        if type(fieldvalue) is list:
                            fieldvalue = fieldvalue[-1]
                            idfobject.fieldvalues[i] = fieldvalue
                        elif fieldvalue in tempdct:
                            fieldvalue = tempdct[fieldvalue]
                            idfobject.fieldvalues[i] = fieldvalue


def getfieldnamesendswith(idfobject, endswith):
    """Get fieldnames for an IDF object that end with a specified string.
    
    Parameters
    ----------
    idfobject : EpBunch
        The object to check.
    endswith : str
        The terminal string, e.g. 'Inlet_Node'.
    
    Returns
    -------
    list
    
    """
    fieldnames = idfobject.fieldnames
    return [name for name in fieldnames if name.endswith(endswith)]


def getnodefieldname(idfobject, endswith, fluid=None, startswith=None):
    """Return the field name of the node which meet the conditions.
    
    Parameters
    ----------
    idfobject : EpBunch
        The object to check.
    endswith : str
        The terminal string, e.g. 'Inlet_Node'.    
    fluid : str, optional
        Fluid is only needed if there are air and water nodes. Fluid is Air, 
        Water or ''. If the fluid is Steam, use Water.
    startswith : str, optional
        The start string, e.g. 'Supply'.    
    
    Returns
    -------
    list
    
    """
    if startswith is None:
        startswith = ''
    if fluid is None:
        # TODO: unit test
        fluid = ''
    nodenames = getfieldnamesendswith(idfobject, endswith)
    nodenames = [name for name in nodenames if name.startswith(startswith)]
    fnodenames = [nd for nd in nodenames if nd.find(fluid) != -1]
    fnodenames = [name for name in fnodenames if name.startswith(startswith)]
    if len(fnodenames) == 0:
        nodename = nodenames[0]
    else:
        nodename = fnodenames[0]
    return nodename


def connectcomponents(idf, components, fluid=None):
    """Rename nodes so that the components get connected.
    
    Names are np1_inlet -> np1 -> np1_np2_node -> np2 -> np2_outlet

    Parameters
    ----------
    idfobject : EpBunch
        The object to check.
    components : list
        A list of EpBunch objects.    
    fluid : str, optional
        Fluid is only needed if there are air and water nodes. Fluid is Air, 
        Water or ''. If the fluid is Steam, use Water.
    
    """
    if fluid is None:
        # TODO: unit test
        fluid = ''
    if len(components) == 1:
        # TODO: unit test
        thiscomp, thiscompnode = components[0]
        initinletoutlet(idf, thiscomp, thiscompnode, force=False)
        outletnodename = getnodefieldname(thiscomp, "Outlet_Node_Name",
                                          fluid=fluid, startswith=thiscompnode)
        thiscomp[outletnodename] = [thiscomp[outletnodename],
                                    thiscomp[outletnodename]]
        return components
    for i in range(len(components) - 1):
        thiscomp, thiscompnode = components[i]
        nextcomp, nextcompnode = components[i + 1]
        initinletoutlet(idf, thiscomp, thiscompnode, force=False)
        initinletoutlet(idf, nextcomp, nextcompnode, force=False)
        betweennodename = "%s_%s_node" % (thiscomp.Name, nextcomp.Name)
        outletnodename = getnodefieldname(thiscomp, "Outlet_Node_Name",
                                          fluid=fluid, startswith=thiscompnode)
        thiscomp[outletnodename] = [thiscomp[outletnodename], betweennodename]
        inletnodename = getnodefieldname(nextcomp, "Inlet_Node_Name", fluid)
        nextcomp[inletnodename] = [nextcomp[inletnodename], betweennodename]
    return components


def initinletoutlet(idf, idfobject, thisnode, force=False):
    """Initialize values for all the inlet and outlet nodes for the object.
    
    Parameters
    ----------
    idf : IDF
        The IDF.
    idfobject : EpBunch
        The object to have nodes renamed.
    thisnode : str
        ??
    force : bool
        If force is False, inlet and outlet node names will only be set if the
        field is empty.
    
    Returns
    -------
    EpBunch
    
    """
    def is_empty(fieldvalue):
        """Test for an empty field.
        """
        try:
            if fieldvalue.strip() == '':
                return True
            else:
                return False
        except AttributeError: # field may be a list
            return False
        
    def trimfields(fields, thisnode):
        """
        Parameters
        ----------
        fields : list
            ??
        thisnode : str
            ??
        """
        if len(fields) > 1:
            if thisnode is not None:
                fields = [field for field in fields
                          if field.startswith(thisnode)]
                return fields
            else:
                # TODO: unit test
                print("Where should this loop connect?")
                print("%s - %s" % (idfobject.key, idfobject.Name))
                print([field.split("Inlet_Node_Name")[0]
                       for field in inletfields])
                raise WhichLoopError
        else:
            return fields

    inletfields = getfieldnamesendswith(idfobject, "Inlet_Node_Name")
    inletfields = trimfields(inletfields, thisnode) # or warn with exception
    for inletfield in inletfields:
        if is_empty(idfobject[inletfield]) or force == True:
            idfobject[inletfield] = "%s_%s" % (idfobject.Name, inletfield)
    outletfields = getfieldnamesendswith(idfobject, "Outlet_Node_Name")
    outletfields = trimfields(outletfields, thisnode) # or warn with exception
    for outletfield in outletfields:
        if is_empty(idfobject[outletfield]) or force == True:
            idfobject[outletfield] = "%s_%s" % (idfobject.Name, outletfield)
    return idfobject


def componentsintobranch(idf, branch, listofcomponents, fluid=None):
    """Insert a list of components into a branch.
    
    Parameters
    ----------
    idf : IDF
        The IDF.
    branch : EpBunch
        The branch to be replaced.
    listofcomponents : list
        List of EpBunch objects for the components to insert.
    fluid : str, optional
        The type of fluid used in the branch. Default is None, which
        equates to a blank fluid field in the BRANCH object. Fluid is only
        needed if there are air and water nodes. Fluid is Air, Water or ''. If
        the fluid is Steam, use Water.
    
    Returns
    -------
    EpBunch
        The updated BRANCH.
        
    """    
    if fluid is None:
        # TODO: unit test
        fluid = ''
    componentlist = [item[0] for item in listofcomponents]
    # assumes that the nodes of the component connect to each other
    # empty branch if it has existing components
    branchname = branch.Name
    branch = idf.removeextensibles('BRANCH', branchname) # empty the branch
    # fill in the new components with the node names into this branch
        # find the first extensible field and fill in the data in obj.
    e_index = idf.getextensibleindex('BRANCH', branchname)
    theobj = branch.obj
    modeleditor.extendlist(theobj, e_index) # just being careful here
    for comp, compnode in listofcomponents:
        theobj.append(comp.key)
        theobj.append(comp.Name)
        inletnodename = getnodefieldname(comp, "Inlet_Node_Name", fluid=fluid,
                                         startswith=compnode)
        theobj.append(comp[inletnodename])
        outletnodename = getnodefieldname(comp, "Outlet_Node_Name",
                                          fluid=fluid, startswith=compnode)
        theobj.append(comp[outletnodename])
        theobj.append('')

    return branch


def simplify_names(fields):
    """Change names of loop elements.
    
    Parameters
    ----------
    fields : list
        List of field names.
    
    Returns
    -------
    list

    """
    fields = [f.replace('Condenser Side', 'Cond_Supply') for f in fields]
    fields = [f.replace('Plant Side', 'Supply') for f in fields]
    fields = [f.replace('Demand Side', 'Demand') for f in fields]
    fields = [f[:f.find('Name') - 1] for f in fields]
    fields = [f.replace(' Node', '') for f in fields]
    fields = [f.replace(' List', 's') for f in fields]
    
    return fields


def replacebranch1(idf, loop, branchname, listofcomponents_tuples, fluid=None):
    """
    
    Parameters
    ----------
    idf : IDF
        The IDF.
    loop : Loop
        An instance of a Loop object representing some type of EnergyPlus loop.
    branchname : str
        Name of the branch to replace.
    listofcomponents_tuples : list
        List of tuples to be used as replacements.
    fluid : str, optional
        The type of fluid used in the branch. Default is None, which
        equates to a blank fluid field in the BRANCH object. Fluid is only
        needed if there are air and water nodes. Fluid is Air, Water or ''. If
        the fluid is Steam, use Water.
    
    Returns
    -------
    EpBunch
        The new BRANCH.
        
    """
    # TODO: Unit test
    if fluid is None:
        fluid = ''
    listofcomponents_tuples = _clean_listofcomponents_tuples(
        listofcomponents_tuples)
    branch = idf.getobject('BRANCH', branchname) # args are (key, name)
    listofcomponents = []
    for comp_type, comp_name, compnode in listofcomponents_tuples:
        comp = idf.getmakeidfobject(idf, comp_type.upper(), comp_name)
        listofcomponents.append((comp, compnode))
    newbr = loop.replacebranch(branch, listofcomponents, fluid=fluid)

    return newbr


def _clean_listofcomponents(listofcomponents):
    """Force it to be a list of tuples.
    
    listofcomponents : ??
        ??
    """
    def totuple(item):
        """return a tuple"""
        if isinstance(item, (tuple, list)):
            return item
        else:
            return (item, None)
    return [totuple(item) for item in listofcomponents]


def _clean_listofcomponents_tuples(listofcomponents_tuples):
    """Force 3 items in the tuple.
    
    Parameters
    ----------
    listofcomponents_tuples : list
        A list of tuples representing branch components.
        
    """
    def pad(item, n):
        """Return an n-item tuple.
        """
        return item + (None, ) * (n - len(item))
    return [pad(item, 3) for item in listofcomponents_tuples]


def flattencopy(lst):
    """Flatten and return a copy of a list.

    This is inefficient on large lists.
    Modified from http://stackoverflow.com/questions/2158395/flatten-an-irregular-list-of-lists-in-python
    
    Parameters
    ----------
    lst : list
        A nested list of arbitrary size and depth.

    """
    thelist = copy.deepcopy(lst)
    list_is_nested = True
    while list_is_nested:                 #outer loop
        keepchecking = False
        atemp = []
        for element in thelist:         #inner loop
            if isinstance(element, list):
                atemp.extend(element)
                keepchecking = True
            else:
                atemp.append(element)
        list_is_nested = keepchecking     #determine if outer loop exits
        thelist = atemp[:]
    return thelist
