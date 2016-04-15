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
from eppy.modeleditor import IDF

from eppy.results.readeso import EsoFile

from eppy.results import eso_data


esohandle = StringIO(eso_data.test_results)
esoresults = EsoFile(esohandle)


def test_no_results():
    """Test that idf.results responds with None if no results.
    """
    idf = IDF()
    
    assert idf.results is None


def test_some_results():
    """Test that idf.results responds with something if results are set.
    """
    idf = IDF()
    idf.set_results(esoresults)
    assert idf.results is not None


def test_esoreader_api():
    idf = IDF()
    idf.set_results(esoresults)
    cooling = idf.results.to_frame('Cooling', frequency='Hourly')
    # test for the expected number of columns
    assert len(cooling.columns) == 2
    # test for the expected values
    assert cooling['ZONE TEST 1'][0] == 10
    assert cooling['ZONE TEST 2'][0] == 20
    
    
