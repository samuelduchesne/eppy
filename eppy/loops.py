# Copyright (c) 2012 Santosh Philip
# Copyright (c) 2016 Jamie Bull
# =======================================================================
#  Distributed under the MIT License.
#  (See accompanying file LICENSE or copy at
#  http://opensource.org/licenses/MIT)
# =======================================================================

"""get the loop data to draw the diagram
Other notes:
- tested for idd version 6.0
- when E+ is updated, run versionchangecheck.py for the following objects
uses the following objects
['plantloop', ]
"""
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals


def extractfields(data, commdct, objkey, fieldlists):
    """get all the objects of objkey.
    fieldlists will have a fieldlist for each of those objects.
    return the contents of those fields"""
    # TODO : this assumes that the field list identical for
    # each instance of the object. This is not true.
    # So we should have a field list for each instance of the object
    # and map them with a zip
    objindex = data.dtls.index(objkey)
    objcomm = commdct[objindex]
    objfields = []
    # get the field names of that object
    for dct in objcomm[0:]:
        try:
            thefieldcomms = dct['field']
            objfields.append(thefieldcomms[0])
        except KeyError as e:
            objfields.append(None)
    fieldindexes = []
    for fieldlist in fieldlists:
        fieldindex = []
        for item in fieldlist:
            if isinstance(item, int):
                fieldindex.append(item)
            else:
                fieldindex.append(objfields.index(item) + 0)
                # the index starts at 1, not at 0
        fieldindexes.append(fieldindex)
    theobjects = data.dt[objkey]
    fieldcontents = []
    for theobject, fieldindex in zip(theobjects, fieldindexes):
        innerlst = []
        for item in fieldindex:
            try:
                innerlst.append(theobject[item])
            except IndexError as err:
                break
        fieldcontents.append(innerlst)
    return fieldcontents


def branch_inlet_outlet(data, commdct, branchname):
    """return the inlet and outlet of a branch"""
    objkey = "BRANCH"
    theobjects = data.dt[objkey]
    theobject = [obj for obj in theobjects if obj[1] == branchname]
    theobject = theobject[0]
    inletindex = 6
    outletindex = len(theobject) - 2
    return [theobject[inletindex], theobject[outletindex]]


def splittermixerfieldlists(data, commdct, objkey):
    """docstring for splittermixerfieldlists
    """
    objkey = objkey.upper()
    theobjects = data.dt[objkey]
    fieldlists = []
    for theobject in theobjects:
        fieldlist = list(range(1, len(theobject)))
        fieldlists.append(fieldlist)
    return fieldlists


def splitterfields(data, commdct):
    """get splitter fields to diagram it

    - inlet
    - outlet1
    - outlet2
    
    """
    objkey = "CONNECTOR:SPLITTER"
    fieldlists = splittermixerfieldlists(data, commdct, objkey)
    return extractfields(data, commdct, objkey, fieldlists)


def mixerfields(data, commdct):
    """get mixer fields to diagram it
    
    - outlet
    - inlet1
    - inlet2

    """
    objkey = "CONNECTOR:MIXER"
    fieldlists = splittermixerfieldlists(data, commdct, objkey)
    return extractfields(data, commdct, objkey, fieldlists)


def repeatingfields(theidd, commdct, objkey, flds):
    """return a list of repeating fields
    fld is in format 'Component %s Name'
    so flds = [fld % (i, ) for i in range(n)]
    does not work for 'fields as indicated' """
    # TODO : make it work for 'fields as indicated'
    if type(flds) != list:
        flds = [flds] # for backward compatability
    objindex = theidd.dtls.index(objkey)
    objcomm = commdct[objindex]
    allfields = []
    for fld in flds:
        thefields = []
        indx = 1
        for i in range(len(objcomm)):
            try:
                thefield = fld % (indx, )
                if objcomm[i]['field'][0] == thefield:
                    thefields.append(thefield)
                    indx = indx + 1
            except KeyError as e:
                pass
        allfields.append(thefields)
    allfields = list(zip(*allfields))
    return [item for sublist in allfields for item in sublist]


def objectcount(data, key):
    """return the count of objects of key"""
    objkey = key.upper()
    return len(data.dt[objkey])


def getfieldindex(data, commdct, objkey, fname):
    """given objkey and fieldname, return its index"""
    objindex = data.dtls.index(objkey)
    objcomm = commdct[objindex]
    for i_index, item in enumerate(objcomm):
        try:
            if item['field'] == [fname]:
                break
        except KeyError as e:
            pass
    return i_index


def supplyplenumfields(data, commdct):
    #   get Name, Zone Name, Zone Node Name, inlet, all outlets
    objkey = "AIRLOOPHVAC:SUPPLYPLENUM"
    singlefields = ["Name", "Zone Name", "Zone Node Name", "Inlet Node Name"]
    fld = "Outlet %s Node Name"
    outletfields = repeatingfields(data, commdct, objkey, fld)
    fieldlist = singlefields + outletfields
    fieldlists = [fieldlist] * objectcount(data, objkey)
    supplyplenums = extractfields(data, commdct, objkey, fieldlists)

    return supplyplenums


def zonesplitterfields(data, commdct):
    #   get Name, inlet, all outlets
    objkey = "AIRLOOPHVAC:ZONESPLITTER"
    singlefields = ["Name", "Inlet Node Name"]
    fld = "Outlet %s Node Name"
    repeatfields = repeatingfields(data, commdct, objkey, fld)
    fieldlist = singlefields + repeatfields
    fieldlists = [fieldlist] * objectcount(data, objkey)
    zonesplitters = extractfields(data, commdct, objkey, fieldlists)

    return zonesplitters


def zonemixerfields(data, commdct):
    #   get Name, outlet, all inlets
    objkey = "AIRLOOPHVAC:ZONEMIXER"
    singlefields = ["Name", "Outlet Node Name"]
    fld = "Inlet %s Node Name"
    repeatfields = repeatingfields(data, commdct, objkey, fld)
    fieldlist = singlefields + repeatfields
    fieldlists = [fieldlist] * objectcount(data, objkey)
    zonemixers = extractfields(data, commdct, objkey, fieldlists)

    return zonemixers


def returnplenumfields(data, commdct):
    #   get Name, Zone Name, Zone Node Name, outlet, all inlets
    objkey = "AIRLOOPHVAC:RETURNPLENUM"
    singlefields = ["Name", "Zone Name", "Zone Node Name", "Outlet Node Name"]
    fld = "Inlet %s Node Name"
    repeatfields = repeatingfields(data, commdct, objkey, fld)
    fieldlist = singlefields + repeatfields
    fieldlists = [fieldlist] * objectcount(data, objkey)
    returnplenums = extractfields(data, commdct, objkey, fieldlists)
    return returnplenums


def equipmentconnectionfields(data, commdct):
    #   get Name, equiplist, zoneairnode, returnnode
    objkey = "ZONEHVAC:EQUIPMENTCONNECTIONS"
    singlefields = ["Zone Name", "Zone Conditioning Equipment List Name", 
                    "Zone Air Node Name", "Zone Return Air Node Name"]
    repeatfields = []
    fieldlist = singlefields + repeatfields
    fieldlists = [fieldlist] * objectcount(data, objkey)
    equipconnections = extractfields(data, commdct, objkey, fieldlists)
    return equipconnections


def equipmentlistfields(data, commdct):
    #   get Name, all equiptype, all equipnames
    objkey = "ZONEHVAC:EQUIPMENTLIST"
    singlefields = ["Name"]
    fieldlist = singlefields
    flds = ["Zone Equipment %s Object Type", "Zone Equipment %s Name"]
    repeatfields = repeatingfields(data, commdct, objkey, flds)
    fieldlist = fieldlist + repeatfields
    fieldlists = [fieldlist] * objectcount(data, objkey)
    equiplists = extractfields(data, commdct, objkey, fieldlists)
    equiplistdct = dict([(ep[0], ep[1:]) for ep in equiplists])
    for key, equips in list(equiplistdct.items()):
        enames = [equips[i] for i in range(1, len(equips), 2)]
        equiplistdct[key] = enames
    
    return equiplistdct


def uncontrolledfields(data, commdct):
    #   get Name, airinletnode
    objkey = "AIRTERMINAL:SINGLEDUCT:UNCONTROLLED"
    singlefields = ["Name", "Zone Supply Air Node Name"]
    repeatfields = []
    fieldlist = singlefields + repeatfields
    fieldlists = [fieldlist] * objectcount(data, objkey)
    uncontrolleds = extractfields(data, commdct, objkey, fieldlists)
    return uncontrolleds


def airdistunitfields(data, commdct):
    #   get Name, equiplist, zoneairnode, returnnode
    objkey = "ZONEHVAC:AIRDISTRIBUTIONUNIT"
    singlefields = ["Name", "Air Terminal Object Type", "Air Terminal Name"]
    repeatfields = []
    fieldlist = singlefields + repeatfields
    fieldlists = [fieldlist] * objectcount(data, objkey)
    adistuunits = extractfields(data, commdct, objkey, fieldlists)
    return adistuunits


def allairdistcomponentfields(data, commdct):
    #   get Name, airinletnode
    adistuinlets = makeadistu_inlets(data, commdct)
    alladistu_comps = []
    for key in list(adistuinlets.keys()):
        objkey = key.upper()
        singlefields = ["Name"] + adistuinlets[key]
        repeatfields = []
        fieldlist = singlefields + repeatfields
        fieldlists = [fieldlist] * objectcount(data, objkey)
        adistu_components = extractfields(data, commdct, objkey, fieldlists)
        alladistu_comps.append(adistu_components)
    
    return alladistu_comps


def getadistus(data, commdct):
    """docstring for fname"""
    objkey = "ZONEHVAC:AIRDISTRIBUTIONUNIT"
    objindex = data.dtls.index(objkey)
    objcomm = commdct[objindex]
    adistutypefield = "Air Terminal Object Type"
    ifield = getfieldindex(data, commdct, objkey, adistutypefield)
    adistus = objcomm[ifield]['key']
    return adistus


def makeadistu_inlets(data, commdct):
    """make the dict adistu_inlets"""
    adistus = getadistus(data, commdct)
    # assume that the inlet node has the words "Air Inlet Node Name"
    airinletnode = "Air Inlet Node Name"
    adistu_inlets = {}
    for adistu in adistus:
        objkey = adistu.upper()
        objindex = data.dtls.index(objkey)
        objcomm = commdct[objindex]
        airinlets = []
        for comm in objcomm:
            try:
                if comm['field'][0].find(airinletnode) != -1:
                    airinlets.append(comm['field'][0])
            except KeyError as e:
                pass
        adistu_inlets[adistu] = airinlets
    return adistu_inlets
