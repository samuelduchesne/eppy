# Copyright (c) 2012 Santosh Philip
# Copyright (c) 2016 Jamie Bull
# =======================================================================
#  Distributed under the MIT License.
#  (See accompanying file LICENSE or copy at
#  http://opensource.org/licenses/MIT)
# =======================================================================
"""py.test for loopdiagram.py"""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os

from eppy.pytest_helpers import do_integration_tests
import pytest

from eppy.useful_scripts.loopdiagram import LoopDiagram
from eppy.useful_scripts.loopdiagram import clean_edges
from eppy.useful_scripts.loopdiagram import edges2nodes
from eppy.useful_scripts.loopdiagram import getedges
from eppy.useful_scripts.loopdiagram import replace_colon


THIS_DIR = os.path.dirname(os.path.abspath(__file__))

RESOURCES_DIR = os.path.join(THIS_DIR, os.pardir, 'resources')

IDD_FILES = os.path.join(RESOURCES_DIR, 'iddfiles')
IDF_FILES = os.path.join(RESOURCES_DIR, 'idffiles')


def test_edges2nodes():
    """py.test for edges2nodes"""
    thedata = (([("a", "b"), ("b", "c"), ("c", "d")],
    ["a", "b", "c", "d"]), # edges, nodes
    )
    for edges, nodes in thedata:
        result = edges2nodes(edges)   
        assert result == nodes
        

def test_replace_colon():
    """py.test for replace_colon"""
    data = (("zone:aap", '@', "zone@aap"),# s, r, replaced
    )    
    for s, r, replaced in data:
        result = replace_colon(s, r)
        assert result == replaced
        

def test_cleanedges():
    """py.test for cleanedges"""
    data = (([('a:a', 'a'), (('a', 'a'), 'a:a'), ('a:a', ('a', 'a'))],
    (('a__a', 'a'), (('a', 'a'), 'a__a'), ('a__a', ('a', 'a')))), 
    # edge, clean_edge
    )
    for edge, clean_edge in data:
        result = clean_edges(edge)
        assert result == clean_edge
        

@pytest.mark.skipif(
    not do_integration_tests(), reason="$EPPY_INTEGRATION env var not set")
def test_loopdiagram_simple_integration():
    """End-to-end smoke test on an example file"""
    idd = os.path.join(IDD_FILES, "Energy+V8_1_0.idd")
    fname = os.path.join(IDF_FILES, "V8_1_0/Boiler.idf")
    diagram = LoopDiagram(fname, idd)


@pytest.mark.skipif(
    not do_integration_tests(), reason="$EPPY_INTEGRATION env var not set")
def test_loopdiagram_airloop_integration():
    """End-to-end smoke test on an example file"""
    idd = os.path.join(IDD_FILES, "Energy+V8_1_0.idd")
    fname = os.path.join(IDF_FILES, "V8_1_0/AirLoopDiagramTest.idf")
    diagram = LoopDiagram(fname, idd)
