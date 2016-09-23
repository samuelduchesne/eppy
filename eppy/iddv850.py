# -*- coding: utf8 -*-
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import os

from eppy.pytest_helpers import IDD_FILES


with open(os.path.join(IDD_FILES, 'Energy+V8_5_0.idd'), 'rb') as idd_file:
    iddtxt = idd_file.read()