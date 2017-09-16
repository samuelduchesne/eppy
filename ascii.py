"""deal with non-ascii files"""
import time

start = time.time()


import eppy
from eppy import modeleditor
from eppy.modeleditor import IDF

folder = "./"
folder= "/Users/santosh/Dropbox/coolshadow/eppy/shared_files/"

iddfile = "{}{}".format(folder, "Energy+.idd")
idffile = "{}{}".format(folder, "non_ascii2.idf")
n = idffile.split(".")
idf_OUT = str(n[0] + "_OUT." + n[1])

IDF.setiddname(iddfile)
idf1 = IDF(idffile)

print ("saving new file")
idf1.saveas(idf_OUT)#, encoding='iso-8859-1')




end = time.time()
print('{} seconds'.format(end - start))
print('{} minutes'.format((end - start)/60.))
