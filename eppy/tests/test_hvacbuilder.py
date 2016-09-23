# Copyright (c) 2012 Santosh Philip
# Copyright (c) 2016 Jamie Bull
# =======================================================================
#  Distributed under the MIT License.
#  (See accompanying file LICENSE or copy at
#  http://opensource.org/licenses/MIT)
# =======================================================================
"""py.test for hvacbuilder
"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os
import subprocess

from eppy.iddcurrent import iddcurrent
from eppy.modeleditor import IDF
from eppy.pytest_helpers import IDD_FILES
from six import StringIO

import eppy.hvacbuilder as hvacbuilder
from eppy.useful_scripts.loopdiagram import LoopDiagram


iddfhandle = StringIO(iddcurrent.iddtxt)
if IDF.getiddname() == None:
    IDF.setiddname(iddfhandle)


def show_graph(idf):
    idd = os.path.join(IDD_FILES, 'Energy+V8_5_0.idd')
    idf.save('tmp.idf')
    filepath = os.path.abspath('tmp.idf')
    diagram = LoopDiagram(filepath, idd)
    diagram.save()
    filepath = os.path.abspath('tmp.png')
    subprocess.call("start " + filepath, shell=True)
#    os.remove(os.path.abspath('tmp.idf'))
#    os.remove(os.path.abspath('tmp.png'))

def test_replace_zoneequipment():
    """Removing equipment from a zone and replacing it with a new system.
    """
    idf = IDF()
    idf.new('replace_zone_equipment.idf')
    # Air Loop Main Branch
    loopname = 'Air Loop'
    sloop = ['fan', ['coil 1 air', 'coil 2 air'], 'airloop_out']
    dloop = ['z_in',  ['Zone 1', 'Zone 2'], 'z_out']
    airloop = hvacbuilder.makeairloop(idf, loopname, sloop, dloop)
    
    zone = 'Zone 1'
    terminal = idf.newidfobject(
        'AIRTERMINAL:SINGLEDUCT:VAV:REHEAT', '%s VAV Reheat' % zone)
    exhaust_fan = idf.newidfobject('FAN:ZONEEXHAUST', '%s exhaust fan' % zone)
    components = [terminal, exhaust_fan]
    airloop.replace_zoneequipment(zone, components)
    #===========================================================================
    # idf.printidf()
    # show_graph(idf)
    #===========================================================================


def test_makeVAVSingleDuctReheat():
    """pytest to try and make a specific system.
    """
    idf = IDF()
    idf.new('myVAVSingleDuctReheat.idf')
    # Air Loop Main Branch
    loopname = 'Air Loop'
    sloop = ['fan', ['detailed cooling coil air'], 'airloop_out']
    dloop = ['z_in',  ['Zone 1', 'Zone 2', 'Zone 3'], 'z_out']
    airloop = hvacbuilder.makeairloop(idf, loopname, sloop, dloop)

    # Cold water loop
    loopname = 'CW'
    sloop = ['circ pump',
             ['big chiller cw', 'little chiller cw',
              'purchased cooling', 'cws bypass'],
             'cw supply outlet']
    dloop = ['cw demand inlet',
             ['cwd bypass', 'detailed cooling coil water'],
             'cw demand outlet']
    cwloop = hvacbuilder.makeplantloop(idf, loopname, sloop, dloop)
    
    # Condenser loop
    loopname = 'Condenser'
    sloop = ['cond circ pump',
             ['big tower', 'cond s bypass'],
             'cond supply outlet']
    dloop = ['cond demand inlet',
             ['big chiller cond', 'little chiller cond', 'cond d bypass'],
             'cond demand outlet']
    cond_loop = hvacbuilder.makeplantloop(idf, loopname, sloop, dloop)
    
    # Hot water loop
    loopname = 'HW'
    sloop = ['HW circ pump',
             ['purchased heating', 'hws bypass'],
             'hw supply outlet']
    dloop = ['hw demand inlet',
             ['Zone 1 heating coil', 'Zone 2 heating coil', 'Zone 3 heating coil',
              'reheat bypass'],
             'hw demand outlet']
    hw_loop = hvacbuilder.makeplantloop(idf, loopname, sloop, dloop)

    # replace the cw coil placeholder
    coil = idf.getmakeidfobject(
        'COIL:COOLING:WATER:DETAILEDGEOMETRY', 'detailed cooling coil')
    branch = idf.getobject('BRANCH', 'detailed cooling coil air')
    airloop.replacebranch(branch, [(coil, 'Air_')])
    branch = idf.getobject('BRANCH', 'detailed cooling coil water')
    cwloop.replacebranch(branch, [(coil, 'Water_')])
    
    # replace the reheat coils for each zone
    for zone in airloop.dloop[1]:
        hw_coil = idf.newidfobject('COIL:HEATING:WATER', '%s heating coil' % zone)
        branch = idf.getobject('BRANCH', '%s heating coil' % zone)
        hw_loop.replacebranch(branch, [(hw_coil, 'Water_')])
        terminal = idf.newidfobject(
            'AIRTERMINAL:SINGLEDUCT:VAV:REHEAT', '%s VAV Reheat' % zone)
        components = [terminal]
        airloop.replace_zoneequipment(
            zone, components)

    idf.save()
    idd = os.path.join(IDD_FILES,'Energy+V8_1_0.idd')
    diagram = LoopDiagram('myVAVSingleDuctReheat.idf', idd)
#    show_graph(idf)


def test_make5ZoneAutoDXVAV():
    """pytest to try and make a specific system.
    """
    loopname = 'VAV Sys 1'
    sloop = ['s_in', ['DX Cooling Coil System 1'], 's_out']
    dloop = ['d_in', 
             ['SPACE1-1','SPACE2-1','SPACE3-1','SPACE4-1','SPACE5-1'],
             'd_out']
    idf = IDF()
    idf.new('my5ZoneAutoDXVAV.idf')
    loop = hvacbuilder.makeairloop(idf, loopname, sloop, dloop)
    # replace components in demand side zones
    branch = idf.getobject('BRANCH', 'DX Cooling Coil System 1')
#    oa_sys = idf.newidfobject('AIRLOOPHVAC:OUTDOORAIRSYSTEM', 'OA Sys 1')
    coil_sys = idf.newidfobject(
        'COILSYSTEM:COOLING:DX', 'DX Cooling Coil System 1')
    heat_coil = idf.newidfobject('COIL:HEATING:GAS', 'Main Heating Coil 1')
    fan = idf.newidfobject('FAN:VARIABLEVOLUME', 'Supply Fan 1')
    new_components = [coil_sys, heat_coil, fan]
#    new_components = [oa_sys, coil_sys, heat_coil, fan]
    loop.replacebranch(branch, new_components)
    
    idf.save()
    idd = os.path.join(IDD_FILES,'Energy+V8_1_0.idd')
    diagram = LoopDiagram('my5ZoneAutoDXVAV.idf', idd)
    diagram.save()
    

def test_makeairloop():
    """pytest for makeairloop"""
    tdata = (
        "p_loop",
        ['sb0', ['sb1', 'sb2', 'sb3'], 'sb4'],
        ['db0', ['db1', 'db2', 'db3'], 'db4'],
        """AIRTERMINAL:SINGLEDUCT:UNCONTROLLED, db1 Direct Air, , 
        db1 Direct Air Zone_Supply_Air;  AIRTERMINAL:SINGLEDUCT:UNCONTROLLED, 
        db2 Direct Air, , db2 Direct Air Zone_Supply_Air;  
        AIRTERMINAL:SINGLEDUCT:UNCONTROLLED, db3 Direct Air, , 
        db3 Direct Air Zone_Supply_Air;  ZONEHVAC:EQUIPMENTLIST, db1 equip list,
        AIRTERMINAL:SINGLEDUCT:UNCONTROLLED, db1 Direct Air;  
        ZONEHVAC:EQUIPMENTLIST, db2 equip list, 
        AIRTERMINAL:SINGLEDUCT:UNCONTROLLED, db2 Direct Air;  
        ZONEHVAC:EQUIPMENTLIST, db3 equip list, 
        AIRTERMINAL:SINGLEDUCT:UNCONTROLLED, db3 Direct Air;  
        ZONEHVAC:EQUIPMENTCONNECTIONS, db1, db1 equip list, 
        db1 zone inlet nodes, , db1 Node, db1 Outlet Node;  
        ZONEHVAC:EQUIPMENTCONNECTIONS, db2, db2 equip list, 
        db2 zone inlet nodes, , db2 Node, db2 Outlet Node;  
        ZONEHVAC:EQUIPMENTCONNECTIONS, db3, db3 equip list, 
        db3 zone inlet nodes, , db3 Node, db3 Outlet Node;  AIRLOOPHVAC, 
        p_loop, , , 0, p_loop Branchs, p_loop Connectors, 
        p_loop Supply Side Inlet, p_loop Demand Outlet, p_loop Demand Inlet, 
        p_loop Supply Side Outlet;  AIRLOOPHVAC:ZONESPLITTER, 
        p_loop Demand Side Splitter, p_loop Demand Inlet, 
        db1 Direct Air Zone_Supply_Air, db2 Direct Air Zone_Supply_Air, 
        db3 Direct Air Zone_Supply_Air;  AIRLOOPHVAC:SUPPLYPATH, 
        p_loopSupplyPath, p_loop Demand Inlet, AirLoopHVAC:ZoneSplitter, 
        p_loop Demand Side Splitter;  AIRLOOPHVAC:ZONEMIXER, 
        p_loop Demand Side Mixer, p_loop Demand Outlet, db1 Outlet Node, 
        db2 Outlet Node, db3 Outlet Node;  AIRLOOPHVAC:RETURNPATH, 
        p_loopReturnPath, p_loop Demand Outlet, AirLoopHVAC:ZoneMixer, 
        p_loop Demand Side Mixer;  BRANCH, sb0, 0, , duct, sb0_duct, 
        sb0_duct_inlet, sb0_duct_outlet, Bypass;  BRANCH, sb1, 0, , duct, 
        sb1_duct, sb1_duct_inlet, sb1_duct_outlet, Bypass;  BRANCH, sb2, 0, , 
        duct, sb2_duct, sb2_duct_inlet, sb2_duct_outlet, Bypass;  BRANCH, sb3, 
        0, , duct, sb3_duct, sb3_duct_inlet, sb3_duct_outlet, Bypass;  BRANCH, 
        sb4, 0, , duct, sb4_duct, sb4_duct_inlet, sb4_duct_outlet, Bypass;  
        BRANCHLIST, p_loop Branchs, sb0, sb1, sb2, sb3, sb4;  
        CONNECTOR:SPLITTER, p_loop_supply_splitter, sb0, sb1, sb2, sb3;  
        CONNECTOR:MIXER, p_loop_supply_mixer, sb4, sb1, sb2, sb3;  
        CONNECTORLIST, p_loop Connectors, Connector:Splitter, 
        p_loop_supply_splitter, Connector:Mixer, p_loop_supply_mixer;  
        NODELIST, db1 zone inlet nodes, db1 Direct Air Zone_Supply_Air;  
        NODELIST, db2 zone inlet nodes, db2 Direct Air Zone_Supply_Air;  
        NODELIST, db3 zone inlet nodes, db3 Direct Air Zone_Supply_Air;  DUCT, 
        sb0_duct, sb0_duct_inlet, sb0_duct_outlet;  DUCT, sb1_duct, 
        sb1_duct_inlet, sb1_duct_outlet;  DUCT, sb2_duct, sb2_duct_inlet, 
        sb2_duct_outlet;  DUCT, sb3_duct, sb3_duct_inlet, sb3_duct_outlet;  
        DUCT, sb4_duct, sb4_duct_inlet, sb4_duct_outlet;  
        """
    ) # loopname, sloop, dloop, expected

    loopname, sloop, dloop, expected = tdata
    fhandle = StringIO("")
    idf1 = IDF(fhandle)
    hvacbuilder.makeairloop(idf1, loopname, sloop, dloop)
    idf2 = IDF(StringIO(expected))
    result = idf1.idfstr()
    expected = idf2.idfstr()
#    show_graph(idf1)
#    idf1.outputtype = 'compressed'
#    idf1.printidf()
#    show_graph(idf2)
    assert result == expected
    

def test_makeplantloop():
    """pytest for makeplantloop"""
    tdata = (
        "p_loop",
        ['sb0', ['sb1', 'sb2', 'sb3'], 'sb4'],
        ['db0', ['db1', 'db2', 'db3'], 'db4'],
        """BRANCH, sb0, 0, , Pipe:Adiabatic, sb0_pipe, p_loop Supply Inlet, 
        sb0_pipe_outlet, Bypass;  BRANCH, sb1, 0, , Pipe:Adiabatic, sb1_pipe, 
        sb1_pipe_inlet, sb1_pipe_outlet, Bypass;  BRANCH, sb2, 0, , 
        Pipe:Adiabatic, sb2_pipe, sb2_pipe_inlet, sb2_pipe_outlet, Bypass;  
        BRANCH, sb3, 0, , Pipe:Adiabatic, sb3_pipe, sb3_pipe_inlet, 
        sb3_pipe_outlet, Bypass;  BRANCH, sb4, 0, , Pipe:Adiabatic, sb4_pipe, 
        sb4_pipe_inlet, p_loop Supply Outlet, Bypass;  BRANCH, db0, 0, , 
        Pipe:Adiabatic, db0_pipe, p_loop Demand Inlet, db0_pipe_outlet, Bypass;  
        BRANCH, db1, 0, , Pipe:Adiabatic, db1_pipe, db1_pipe_inlet, 
        db1_pipe_outlet, Bypass;  BRANCH, db2, 0, , Pipe:Adiabatic, db2_pipe, 
        db2_pipe_inlet, db2_pipe_outlet, Bypass;  BRANCH, db3, 0, , 
        Pipe:Adiabatic, db3_pipe, db3_pipe_inlet, db3_pipe_outlet, Bypass;  
        BRANCH, db4, 0, , Pipe:Adiabatic, db4_pipe, db4_pipe_inlet, 
        p_loop Demand Outlet, Bypass;  BRANCHLIST, p_loop Supply Branchs, sb0, 
        sb1, sb2, sb3, sb4;  BRANCHLIST, p_loop Demand Branchs, db0, db1, db2, 
        db3, db4;  CONNECTOR:SPLITTER, p_loop_supply_splitter, sb0, sb1, sb2, 
        sb3;  CONNECTOR:SPLITTER, p_loop_demand_splitter, db0, db1, db2, db3;  
        CONNECTOR:MIXER, p_loop_supply_mixer, sb4, sb1, sb2, sb3;  
        CONNECTOR:MIXER, p_loop_demand_mixer, db4, db1, db2, db3;  
        CONNECTORLIST, p_loop Supply Connectors, Connector:Splitter, 
        p_loop_supply_splitter, Connector:Mixer, p_loop_supply_mixer;  
        CONNECTORLIST, p_loop Demand Connectors, Connector:Splitter, 
        p_loop_demand_splitter, Connector:Mixer, p_loop_demand_mixer;  
        PIPE:ADIABATIC, sb0_pipe, p_loop Supply Inlet, sb0_pipe_outlet;  
        PIPE:ADIABATIC, sb1_pipe, sb1_pipe_inlet, sb1_pipe_outlet;  
        PIPE:ADIABATIC, sb2_pipe, sb2_pipe_inlet, sb2_pipe_outlet;  
        PIPE:ADIABATIC, sb3_pipe, sb3_pipe_inlet, sb3_pipe_outlet;  
        PIPE:ADIABATIC, sb4_pipe, sb4_pipe_inlet, p_loop Supply Outlet;  
        PIPE:ADIABATIC, db0_pipe, p_loop Demand Inlet, db0_pipe_outlet;  
        PIPE:ADIABATIC, db1_pipe, db1_pipe_inlet, db1_pipe_outlet;  
        PIPE:ADIABATIC, db2_pipe, db2_pipe_inlet, db2_pipe_outlet;  
        PIPE:ADIABATIC, db3_pipe, db3_pipe_inlet, db3_pipe_outlet;  
        PIPE:ADIABATIC, db4_pipe, db4_pipe_inlet, p_loop Demand Outlet;  
        PLANTLOOP, p_loop, Water, , , , , , , 0.0, Autocalculate, 
        p_loop Supply Inlet, p_loop Supply Outlet, p_loop Supply Branchs, 
        p_loop Supply Connectors, p_loop Demand Inlet, p_loop Demand Outlet, 
        p_loop Demand Branchs, p_loop Demand Connectors, SequentialLoad, , 
        SingleSetpoint, None, None; """
    ) # loopname, sloop, dloop, expected

    loopname, sloop, dloop, expected = tdata
    fhandle = StringIO("")
    idf1 = IDF(fhandle)
    hvacbuilder.makeplantloop(idf1, loopname, sloop, dloop)
    idf2 = IDF(StringIO(expected))
    result = idf1.idfstr()
    expected = idf2.idfstr()
    assert result == expected

def test_makecondenserloop():
    """pytest for makecondenserloop"""
    tdata = (
        "c_loop",
        ['sb0', ['sb1', 'sb2', 'sb3'], 'sb4'],
        ['db0', ['db1', 'db2', 'db3'], 'db4'],
        """BRANCH, sb0, 0, , Pipe:Adiabatic, sb0_pipe,
        c_loop Cond_Supply Inlet, sb0_pipe_outlet, Bypass;  BRANCH, sb1, 0,
        , Pipe:Adiabatic, sb1_pipe, sb1_pipe_inlet, sb1_pipe_outlet,
        Bypass;  BRANCH, sb2, 0, , Pipe:Adiabatic, sb2_pipe,
        sb2_pipe_inlet, sb2_pipe_outlet, Bypass;  BRANCH, sb3, 0, ,
        Pipe:Adiabatic, sb3_pipe, sb3_pipe_inlet, sb3_pipe_outlet,
        Bypass;  BRANCH, sb4, 0, , Pipe:Adiabatic, sb4_pipe,
        sb4_pipe_inlet, c_loop Cond_Supply Outlet, Bypass;  BRANCH,
        db0, 0, , Pipe:Adiabatic, db0_pipe, c_loop Demand Inlet,
        db0_pipe_outlet, Bypass;  BRANCH, db1, 0, , Pipe:Adiabatic, db1_pipe,
        db1_pipe_inlet, db1_pipe_outlet, Bypass;  BRANCH, db2, 0, ,
        Pipe:Adiabatic, db2_pipe, db2_pipe_inlet, db2_pipe_outlet, Bypass;
        BRANCH, db3, 0, , Pipe:Adiabatic, db3_pipe, db3_pipe_inlet,
        db3_pipe_outlet, Bypass;  BRANCH, db4, 0, , Pipe:Adiabatic,
        db4_pipe, db4_pipe_inlet, c_loop Demand Outlet, Bypass;
        BRANCHLIST, c_loop Cond_Supply Branchs, sb0, sb1, sb2, sb3, sb4;
        BRANCHLIST, c_loop Condenser Demand Branchs, db0, db1, db2, db3,
        db4;  CONNECTOR:SPLITTER, c_loop_supply_splitter, sb0, sb1,
        sb2, sb3;  CONNECTOR:SPLITTER, c_loop_demand_splitter, db0, db1, db2,
        db3;  CONNECTOR:MIXER, c_loop_supply_mixer, sb4, sb1, sb2, sb3;
        CONNECTOR:MIXER, c_loop_demand_mixer, db4, db1, db2, db3;
        CONNECTORLIST, c_loop Cond_Supply Connectors, Connector:Splitter,
        c_loop_supply_splitter, Connector:Mixer, c_loop_supply_mixer;
        CONNECTORLIST, c_loop Condenser Demand Connectors,
        Connector:Splitter, c_loop_demand_splitter, Connector:Mixer,
        c_loop_demand_mixer;  PIPE:ADIABATIC, sb0_pipe,
        c_loop Cond_Supply Inlet, sb0_pipe_outlet;  PIPE:ADIABATIC,
        sb1_pipe, sb1_pipe_inlet, sb1_pipe_outlet;  PIPE:ADIABATIC, sb2_pipe,
        sb2_pipe_inlet, sb2_pipe_outlet;  PIPE:ADIABATIC, sb3_pipe,
        sb3_pipe_inlet, sb3_pipe_outlet;  PIPE:ADIABATIC, sb4_pipe,
        sb4_pipe_inlet, c_loop Cond_Supply Outlet;  PIPE:ADIABATIC,
        db0_pipe, c_loop Demand Inlet, db0_pipe_outlet;  PIPE:ADIABATIC,
        db1_pipe, db1_pipe_inlet, db1_pipe_outlet;  PIPE:ADIABATIC,
        db2_pipe, db2_pipe_inlet, db2_pipe_outlet;  PIPE:ADIABATIC,
        db3_pipe, db3_pipe_inlet, db3_pipe_outlet;  PIPE:ADIABATIC, db4_pipe,
        db4_pipe_inlet, c_loop Demand Outlet;  CONDENSERLOOP, c_loop, Water, ,
        , , , , , 0.0, Autocalculate, c_loop Cond_Supply Inlet,
        c_loop Cond_Supply Outlet, c_loop Cond_Supply Branchs,
        c_loop Cond_Supply Connectors, c_loop Demand Inlet,
        c_loop Demand Outlet, c_loop Condenser Demand Branchs,
        c_loop Condenser Demand Connectors, SequentialLoad, None;  """
        ) # loopname, sloop, dloop, expected

    loopname, sloop, dloop, expected = tdata
    fhandle = StringIO("")
    idf1 = IDF(fhandle)
    hvacbuilder.makecondenserloop(idf1, loopname, sloop, dloop)
    idf2 = IDF(StringIO(expected))
    result = idf1.idfstr()
    expected = idf2.idfstr()
    assert result == expected

def test_getbranchcomponents():
    """py.test for getbranchcomponents"""
    tdata = (
        (
            """BRANCH,
            sb1,
            0,
            ,
            PIPE:ADIABATIC,
            np1,
            np1_inlet,
            np1_np2_node,
            ,
            PIPE:ADIABATIC,
            np2,
            np1_np2_node,
            np2_outlet,
            ;
            """,
            True,
            [
                ('PIPE:ADIABATIC', 'np1'),
                ('PIPE:ADIABATIC', 'np2')
            ]), # idftxt, utest, componentlist
        (
            """BRANCH,
            sb1,
            0,
            ,
            PIPE:ADIABATIC,
            np1,
            np1_inlet,
            np1_np2_node,
            ,
            PIPE:ADIABATIC,
            np2,
            np1_np2_node,
            np2_outlet,
            ;
            PIPE:ADIABATIC,
            np1,
            np1_inlet,
            np1_np2_node;

            PIPE:ADIABATIC,
            np2,
            np1_np2_node,
            np2_outlet;

            """,
            False,
            [
                ['PIPE:ADIABATIC', 'np1', 'np1_inlet', 'np1_np2_node'],
                ['PIPE:ADIABATIC', 'np2', 'np1_np2_node', 'np2_outlet']]),
        # idftxt, utest, componentlist
        )
    for idftxt, utest, componentlist in tdata:
        fhandle = StringIO(idftxt)
        idf = IDF(fhandle)
        branch = idf.idfobjects['BRANCH'][0]
        result = hvacbuilder.getbranchcomponents(idf, branch, utest=utest)
        if utest:
            assert result == componentlist
        else:
            lresult = [item.obj for item in result]
            assert lresult == componentlist

def test_renamenodes():
    """py.test for renamenodes"""
    idftxt = """PIPE:ADIABATIC,
         np1,
         np1_inlet,
         np1_outlet;
         !- ['np1_outlet', 'np1_np2_node'];

    BRANCH,
         sb0,
         0,
         ,
         Pipe:Adiabatic,
         np1,
         np1_inlet,
         np1_outlet,
         Bypass;
    """
    outtxt = """PIPE:ADIABATIC,
         np1,
         np1_inlet,
         np1_np2_node;
         !- ['np1_outlet', 'np1_np2_node'];

    BRANCH,
         sb0,
         0,
         ,
         Pipe:Adiabatic,
         np1,
         np1_inlet,
         np1_np2_node,
         Bypass;
    """
    # !- ['np1_outlet', 'np1_np2_node'];
    fhandle = StringIO(idftxt)
    idf = IDF(fhandle)
    pipe = idf.idfobjects['PIPE:ADIABATIC'][0]
    pipe.Outlet_Node_Name = ['np1_outlet', 'np1_np2_node'] # this is the first step of the replace
    hvacbuilder.renamenodes(idf, fieldtype='node')
    outidf = IDF(StringIO(outtxt))
    result = idf.idfobjects['PIPE:ADIABATIC'][0].obj
    assert result == outidf.idfobjects['PIPE:ADIABATIC'][0].obj

def test_getfieldnamesendswith():
    """py.test for getfieldnamesendswith"""
    idftxt = """PIPE:ADIABATIC,
        np2,                      !- Name
        np1_np2_node,             !- Inlet Node Name
        np2_outlet;               !- Outlet Node Name

    """
    tdata = (
        ("Inlet_Node_Name", ["Inlet_Node_Name"]
        ), # endswith, fieldnames
        (
            "Node_Name",
            ["Inlet_Node_Name",
             "Outlet_Node_Name"]), # endswith, fieldnames
        (
            "Name",
            [
                "Name",
                "Inlet_Node_Name",
                "Outlet_Node_Name"]), # endswith, fieldnames
    )
    fhandle = StringIO(idftxt)
    idf = IDF(fhandle)
    idfobject = idf.idfobjects["PIPE:ADIABATIC"][0]
    for endswith, fieldnames in tdata:
        result = hvacbuilder.getfieldnamesendswith(idfobject, endswith)
        assert result == fieldnames

def test_getnodefieldname():
    """py.test for getnodefieldname"""
    tdata = (
        ('PIPE:ADIABATIC', 'pipe1', 'Inlet_Node_Name', '', 'Inlet_Node_Name'),
        # objtype, objname, endswith, fluid, nodefieldname
        ('CHILLER:ELECTRIC', 'pipe1', 'Inlet_Node_Name', '',
         'Chilled_Water_Inlet_Node_Name'),
        # objtype, objname, endswith, fluid, nodefieldname
        ('COIL:COOLING:WATER', 'pipe1', 'Inlet_Node_Name', 'Water',
         'Water_Inlet_Node_Name'),
        # objtype, objname, endswith, fluid, nodefieldname
        ('COIL:COOLING:WATER', 'pipe1', 'Inlet_Node_Name', 'Air',
         'Air_Inlet_Node_Name'),
        # objtype, objname, endswith, fluid, nodefieldname
        ('COIL:COOLING:WATER', 'pipe1', 'Outlet_Node_Name', 'Air',
         'Air_Outlet_Node_Name'),
        # objtype, objname, endswith, fluid, nodefieldname
        )
    for objtype, objname, endswith, fluid, nodefieldname in tdata:
        fhandle = StringIO("")
        idf = IDF(fhandle)
        idfobject = idf.newidfobject(objtype, objname)
        result = hvacbuilder.getnodefieldname(idfobject, endswith, fluid)
        assert result == nodefieldname

def test_connectcomponents():
    """py.test for connectcomponents"""
    fhandle = StringIO("")
    idf = IDF(fhandle)

    tdata = (
        (
            [(idf.newidfobject("PIPE:ADIABATIC", "pipe1"), None),
             (idf.newidfobject("PIPE:ADIABATIC", "pipe2"), None)],
            ["pipe1_Inlet_Node_Name", ["pipe2_Inlet_Node_Name",
                                       "pipe1_pipe2_node"]],
            [["pipe1_Outlet_Node_Name", "pipe1_pipe2_node"],
             "pipe2_Outlet_Node_Name"], '',
        ),
        # components_thisnodes, inlets, outlets, fluid
        (
            [(idf.newidfobject("Coil:Cooling:Water".upper(), "pipe1"),
              'Water_'),
             (idf.newidfobject("Coil:Cooling:Water".upper(), "pipe2"),
              'Water_')],
            ['pipe1_Water_Inlet_Node_Name', '',
             'pipe2_Water_Inlet_Node_Name',
             ['', 'pipe1_pipe2_node']],
            [['pipe1_Water_Outlet_Node_Name', 'pipe1_pipe2_node'], '',
             'pipe2_Water_Outlet_Node_Name', ''],
            'Air'
        ),
        # components_thisnodes, inlets, outlets, fluid
        (
            [(idf.newidfobject("PIPE:ADIABATIC".upper(), "pipe1"), None),
             (idf.newidfobject("Coil:Cooling:Water".upper(), "pipe2"),
              'Water_')],
            ["pipe1_Inlet_Node_Name", "pipe2_Water_Inlet_Node_Name",
             ['pipe2_Air_Inlet_Node_Name', 'pipe1_pipe2_node']],
            [['pipe1_Outlet_Node_Name', 'pipe1_pipe2_node'],
             "pipe2_Water_Outlet_Node_Name", ""],
            'Air'
        ),
        # components_thisnodes, inlets, outlets, fluid
    )
    for components_thisnodes, inlets, outlets, fluid in tdata:
        # init the nodes in the new components
        for component, thisnode in components_thisnodes:
            hvacbuilder.initinletoutlet(idf, component, thisnode)
        hvacbuilder.connectcomponents(idf, components_thisnodes, fluid)
        inresult = []
        for component, thisnode in components_thisnodes:
            fldnames = hvacbuilder.getfieldnamesendswith(component,
                                                         "Inlet_Node_Name")
            for name in fldnames:
                inresult.append(component[name])
        assert inresult == inresult
        outresult = []
        for component, thisnode in components_thisnodes:
            fldnames = hvacbuilder.getfieldnamesendswith(component,
                                                         "Outlet_Node_Name")
            for name in fldnames:
                outresult.append(component[name])
        assert outresult == outlets


def test_initinletoutlet():
    """py.test for initinletoutlet"""
    tdata = (
        (
            'PIPE:ADIABATIC',
            'apipe',
            None,
            True,
            ["apipe_Inlet_Node_Name"],
            ["apipe_Outlet_Node_Name"]
        ),
        # idfobjectkey, idfobjname, thisnode, force, inlets, outlets
        (
            'PIPE:ADIABATIC',
            'apipe',
            None,
            False,
            ["Gumby"],
            ["apipe_Outlet_Node_Name"]
        ),
        # idfobjectkey, idfobjname, thisnode, force, inlets, outlets
        (
            'Coil:Cooling:Water'.upper(),
            'acoil',
            'Water_',
            True,
            ["acoil_Water_Inlet_Node_Name", ""],
            ["acoil_Water_Outlet_Node_Name", ""]
        ),
        # idfobjectkey, idfobjname, thisnode, force, inlets, outlets
    )
    fhandle = StringIO("")
    idf = IDF(fhandle)
    for idfobjectkey, idfobjname, thisnode, force, inlets, outlets in tdata:
        idfobject = idf.newidfobject(idfobjectkey, idfobjname)
        inodefields = hvacbuilder.getfieldnamesendswith(
            idfobject,
            "Inlet_Node_Name")
        idfobject[inodefields[0]] = "Gumby"
        hvacbuilder.initinletoutlet(idf, idfobject, thisnode, force=force)
        inodefields = hvacbuilder.getfieldnamesendswith(idfobject,
                                                        "Inlet_Node_Name")
        for nodefield, inlet in zip(inodefields, inlets):
            result = idfobject[nodefield]
            assert result == inlet
        onodefields = hvacbuilder.getfieldnamesendswith(
            idfobject,
            "Outlet_Node_Name")
        for nodefield, outlet in zip(onodefields, outlets):
            result = idfobject[nodefield]
            assert result == outlet

def test_componentsintobranch():
    """py.test for componentsintobranch"""
    tdata = (
        (
            """BRANCH,
             sb0,
             0,
             ,
             Pipe:Adiabatic,
             sb0_pipe,
             p_loop Supply Inlet,
             sb0_pipe_outlet,
             Bypass;
             """,
            [
                ("PIPE:ADIABATIC", "pipe1", None),
                ("PIPE:ADIABATIC", "pipe2", None)
            ],
            '',
            [
                'PIPE:ADIABATIC', 'pipe1', 'pipe1_Inlet_Node_Name',
                'pipe1_Outlet_Node_Name', '', 'PIPE:ADIABATIC', 'pipe2',
                'pipe2_Inlet_Node_Name', 'pipe2_Outlet_Node_Name', ''
            ]
        ),
        # idftxt, complst, fluid, branchcomps
        (
            """BRANCH,
            sb0,
            0,
            ,
            Pipe:Adiabatic,
            sb0_pipe,
            p_loop Supply Inlet,
            sb0_pipe_outlet,
            Bypass;
            """,
            [
                ("PIPE:ADIABATIC", "pipe1", None),
                ('CHILLER:ELECTRIC', "chiller", "Chilled_Water_")
            ],
            '',
            [
                'PIPE:ADIABATIC', 'pipe1', 'pipe1_Inlet_Node_Name',
                'pipe1_Outlet_Node_Name', '', 'CHILLER:ELECTRIC', 'chiller',
                'chiller_Chilled_Water_Inlet_Node_Name',
                'chiller_Chilled_Water_Outlet_Node_Name', ''
            ]
        ),
        # idftxt, complst, fluid, branchcomps
    )
    for ii, (idftxt, complst, fluid, branchcomps) in enumerate(tdata):
        fhandle = StringIO(idftxt)
        idf = IDF(fhandle)
        components_thisnodes = [(idf.newidfobject(key, nm), thisnode)
                                for key, nm, thisnode in complst]
        fnc = hvacbuilder.initinletoutlet
        components_thisnodes = [(fnc(idf, cp, thisnode), thisnode)
                                for cp, thisnode in components_thisnodes]
        branch = idf.idfobjects['BRANCH'][0]
        branch = hvacbuilder.componentsintobranch(idf, branch,
                                                  components_thisnodes, fluid)
        assert branch.obj[4:] == branchcomps

def test_replacebranch():
    """py.test for replacebranch"""
    tdata = (
        (
            "p_loop", ['sb0', ['sb1', 'sb2', 'sb3'], 'sb4'],
            ['db0', ['db1', 'db2', 'db3'], 'db4'],
            'sb0',
            [
                ("Chiller:Electric".upper(), 'Central_Chiller',
                 'Chilled_Water_'),
                ("PIPE:ADIABATIC", 'np1', None),
                ("PIPE:ADIABATIC", 'np2', None)
            ],
            'Water',
            [
                'BRANCH', 'sb0', '0', '', 'CHILLER:ELECTRIC', 'Central_Chiller',
                'p_loop Supply Inlet', 'Central_Chiller_np1_node', '',
                'PIPE:ADIABATIC',
                'np1', 'Central_Chiller_np1_node', 'np1_np2_node', '',
                'PIPE:ADIABATIC',
                'np2', 'np1_np2_node', 'np2_Outlet_Node_Name', ''
            ]
        ), # loopname, sloop, dloop, branchname, componenttuple, fluid, outbranch
    )
    for (loopname, sloop, dloop, branchname,
         componenttuple, fluid, outbranch) in tdata:
        fhandle = StringIO("")
        idf = IDF(fhandle)
        loop = hvacbuilder.makeplantloop(idf, loopname, sloop, dloop)
        components_thisnodes = [(idf.newidfobject(key, nm), thisnode)
                                for key, nm, thisnode in componenttuple]
        branch = idf.getobject('BRANCH', branchname)
        newbr = loop.replacebranch(branch, components_thisnodes, fluid=fluid)
        assert newbr.obj == outbranch

def test_pipecomponent():
    """py.test for pipecomponent"""
    tdata = (
        (
            "apipe",
            ['PIPE:ADIABATIC', 'apipe',
             'apipe_inlet', 'apipe_outlet']), # pname, pipe_obj
        (
            "bpipe",
            ['PIPE:ADIABATIC', 'bpipe',
             'bpipe_inlet', 'bpipe_outlet']), # pname, pipe_obj
        )
    for pname, pipe_obj in tdata:
        fhandle = StringIO("")
        idf = IDF(fhandle)
        result = hvacbuilder.pipecomponent(idf, pname)
        assert result.obj == pipe_obj

def test_ductcomponent():
    """py.test for ductcomponent"""
    tdata = ((
        'aduct',
        ['DUCT', 'aduct', 'aduct_inlet', 'aduct_outlet']
        ), # dname, duct_obj
            )
    for dname, duct_obj in tdata:
        fhandle = StringIO("")
        idf = IDF(fhandle)
        result = hvacbuilder.ductcomponent(idf, dname)
        assert result.obj == duct_obj

def test_pipebranch():
    """py.test for pipebranch"""
    tdata = ((
        "p_branch",
        ['BRANCH',
         'p_branch',
         '0',
         '',
         'Pipe:Adiabatic',
         'p_branch_pipe',
         'p_branch_pipe_inlet',
         'p_branch_pipe_outlet',
         'Bypass'],
        [
            'PIPE:ADIABATIC',
            'p_branch_pipe',
            'p_branch_pipe_inlet',
            'p_branch_pipe_outlet']
        ), # pb_name, branch_obj, pipe_obj
            )
    for pb_name, branch_obj, pipe_obj in tdata:
        fhandle = StringIO("")
        idf = IDF(fhandle)
        result = hvacbuilder.pipebranch(idf, pb_name)
        assert result.obj == branch_obj
        thepipe = idf.getobject('PIPE:ADIABATIC', result.Component_1_Name)
        assert thepipe.obj == pipe_obj

def test_ductbranch():
    """py.test for ductbranch"""
    tdata = ((
        'd_branch',
        [
            'BRANCH',
            'd_branch',
            '0',
            '',
            'duct',
            'd_branch_duct',
            'd_branch_duct_inlet',
            'd_branch_duct_outlet',
            'Bypass'],
        [
            'DUCT',
            'd_branch_duct',
            'd_branch_duct_inlet',
            'd_branch_duct_outlet']), # db_name, branch_obj, duct_obj
            )
    for db_name, branch_obj, duct_obj in tdata:
        fhandle = StringIO("")
        idf = IDF(fhandle)
        result = hvacbuilder.ductbranch(idf, db_name)
        assert result.obj == branch_obj
        theduct = idf.getobject('DUCT', result.Component_1_Name)
        assert theduct.obj == duct_obj

def test_flattencopy():
    """py.test for flattencopy"""
    tdata = (([1, 2], [1, 2]), #lst , nlst -a
             ([1, 2, [3, 4]], [1, 2, 3, 4]), #lst , nlst
             ([1, 2, [3, [4, 5, 6], 7, 8]], [1, 2, 3, 4, 5, 6, 7, 8]),
             #lst , nlst
             ([1, 2, [3, [4, 5, [6, 7], 8], 9]], [1, 2, 3, 4, 5, 6, 7, 8, 9]),
             #lst , nlst
            )
    for lst, nlst in tdata:
        result = hvacbuilder.flattencopy(lst)
        assert result == nlst

def test__clean_listofcomponents():
    """py.test for _clean_listofcomponents"""
    data = (
        ([1, 2], [(1, None), (2, None)]), # lst, clst
        ([(1, None), 2], [(1, None), (2, None)]), # lst, clst
        ([(1, 'stuff'), 2], [(1, 'stuff'), (2, None)]), # lst, clst
    )
    for lst, clst in data:
        result = hvacbuilder._clean_listofcomponents(lst)
        assert result == clst

def test__clean_listofcomponents_tuples():
    """py.test for _clean_listofcomponents_tuples"""
    data = (
        ([(1, 2), (2, 3)], [(1, 2, None), (2, 3, None)]), #lst, clst
        ([(1, 2, None), (2, 3)], [(1, 2, None), (2, 3, None)]), #lst, clst
        ([(1, 2, 'stuff'), (2, 3)], [(1, 2, 'stuff'), (2, 3, None)]), #lst, clst
    )
    for lst, clst in data:
        result = hvacbuilder._clean_listofcomponents_tuples(lst)
        assert result == clst
        

        