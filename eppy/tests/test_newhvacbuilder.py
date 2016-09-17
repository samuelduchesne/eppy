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

from eppy.iddcurrent import iddcurrent
from eppy.modeleditor import IDF
from six import StringIO


iddfhandle = StringIO(iddcurrent.iddtxt)
if IDF.getiddname() == None:
    IDF.setiddname(iddfhandle)


class Loop(object):
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


class HalfLoop(object):
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


class Branch(object):
    """Branches contain one or more components in series.
    """
    
    def __init__(self, idf, branchname, components=None):
        """Make a branch with components, or just a pipe
        """
        if not components:
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
            # last one is the cn outlet
            # intermediate ones are named as c1_c2_inlet and c1_c2_outlet
            branch.Component_1_Object_Type = component.key
            branch.Component_1_Name = component.Name
            branch.Component_1_Inlet_Node_Name = component.Inlet_Node_Name
            branch.Component_1_Outlet_Node_Name = component.Outlet_Node_Name
            branch.Component_1_Branch_Control_Type = "Bypass"
    
        self.branch = branch


class PipeBranch(Branch):
    
    def __init__(self, idf, branchname):
        pass


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
    
    
class Component(object):
    """Components can be pipes, ducts, or an item of plant or demand equipment.
    """
    
    def __init__(self, idf, key, name, **kwargs):
        idf.newidfobject(key.upper(), name)
    
    def inlet_node(self):
        pass
    
    def outlet_node(self):
        pass

def pipecomponent(idf, pname):
    """make a pipe component
    generate inlet outlet names"""
    pipe = idf.newidfobject("Pipe:Adiabatic".upper(), pname)
    pipe.Inlet_Node_Name = "%s_inlet" % (pname, )
    pipe.Outlet_Node_Name = "%s_outlet" % (pname, )
    return pipe



def test_branch():
    idf = IDF()
    idf.new()
    branch = Branch(idf, 'default')
    assert len(branch.components) == 1
    assert len(branch) == 1
    assert branch.components[0].key == 'PIPE:ADIABATIC'
    assert branch.components[0].Name == 'default_pipe'
    
    print(branch.branch)