# Copyright (c) 2012 Santosh Philip
# Copyright (c) 2016 Jamie Bull
# =======================================================================
#  Distributed under the MIT License.
#  (See accompanying file LICENSE or copy at
#  http://opensource.org/licenses/MIT)
# =======================================================================
"""py.test for hvacbuilder"""
# idd is read only once in this test
# if it has already been read from some other test, it will continue with the old reading

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from eppy.hvacbuilder import getfieldnamesendswith
from eppy.iddcurrent import iddcurrent
from eppy.modeleditor import IDF
from six import StringIO


iddfhandle = StringIO(iddcurrent.iddtxt)
if IDF.getiddname() == None:
    IDF.setiddname(iddfhandle)

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
    
    def __init__(self, idf):
        pass
    
    def supply_side(self):
        pass
    
    def demand_side(self):
        pass


class HalfLoop(EppyHVAC):
    """A half-loop is either the demand or supply side of a loop.
    """
    
    def __init__(self, idf):
        pass
    
    def branches(self):
        """A list of branches on the half loop.
        """
        pass
    
    def connectors(self):
        """A list of connectors on the half loop.
        """
        pass


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
            # first one is the c1 inlet
            if i == 1:
                if component.inlet == '':
                    inlet_name = '%s_inlet' % component.Name
                else:
                    inlet_name = '%s_%s_inlet' % (
                        self.components[i].Name, self.components[i+1].Name)
                component.set_inlet(inlet_name)
            # last one is the cn outlet
            if i == len(self):
                if component.outlet == '':
                    outlet_name = '%s_outlet' % component.Name
                else:
                    outlet_name = '%s_%s_outlet' % (
                        self.components[i].Name, self.components[i+1].Name)
                component.set_outlet(outlet_name)
            # intermediate ones are named as c1_c2_inlet and c1_c2_outlet
            branch.Component_1_Object_Type = component.key
            branch.Component_1_Name = component.Name
            branch.Component_1_Inlet_Node_Name = component.inlet
            branch.Component_1_Outlet_Node_Name = component.outlet
            branch.Component_1_Branch_Control_Type = "Bypass"
    
        self.bunch = branch



class Connector(object):
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
    

def pipecomponent(idf, pname):
    """make a pipe component
    generate inlet outlet names"""
    pipe = Component(
        idf, key='PIPE:ADIABATIC', name=pname,
        Inlet_Node_Name="%s_inlet" % pname,
        Outlet_Node_Name="%s_outlet" % pname)
    return pipe


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
    print(branch.components[0])
    assert (branch.components[0].Boiler_Water_Inlet_Node_Name == 
            branch.components[0].inlet)
    assert (branch.components[0].Boiler_Water_Outlet_Node_Name ==
            branch.components[0].outlet)

    
