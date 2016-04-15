# Copyright (c) 2012 Santosh Philip
# =======================================================================
#  Distributed under the MIT License.
#  (See accompanying file LICENSE or copy at
#  http://opensource.org/licenses/MIT)
# =======================================================================
"""
Module wrapping esoreader.

"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from StringIO import StringIO
from eppy.iddcurrent import iddcurrent
from eppy.modeleditor import IDF

from esoreader import EsoFile

from results import eso_data


iddfhandle = StringIO(iddcurrent.iddtxt)
if IDF.getiddname() == None:
    IDF.setiddname(iddfhandle)

esohandle = StringIO(eso_data.test_results)

results = EsoFile(esohandle)


def test_no_results():
    """Test that idf.results responds with None if no results.
    """
    idf = IDF()
    
    assert idf.results is None


def test_some_results():
    """Test that idf.results responds with something if results are set.
    """
    idf = IDF()
    idf.set_results(results)
    assert idf.results is not None


def test_esoreader_api():
    idf = IDF()
    idf.set_results(results)
    assert idf.results.find_variable('Cooling', frequency='Hourly')
