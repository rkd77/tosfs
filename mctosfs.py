#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Program pomocniczy do mc wyświetlający zawartość obrazów dysków TOSa.
"""
import array
import errno   # for error number codes (ENOENT, etc)
               # - note: these must be returned as negatives
import os
import stat    # for file properties
import sys

from TOSDSK import *

def show_list(path):

    dsk = DSK(path)
    tos = TOS(dsk)
    links = 1
    gid = "77"
    uid = "77"
    t = "Jan  1 1970"
    #print tos.entries
    lista = []
    for i in tos.entries:
        if i[NO] != 0:
            continue
        if i[NR_OF_DIR] == 255:
            continue
        #print i
        #continue
        if i[NAME].endswith('.DIR'):
            typ = "drwxrwxrwx"
        else:
            typ = "-rw-rw-rw-"
        size = tos.get_size(i)
        lista.append((typ, links, uid, gid, size, t, tos.get_name(i)))
    lista.sort(key = lambda x: x[-1])
    for i in lista:
        print "%s %4d %s %s %14d %s %s" % \
        (i[0], i[1], i[2], i[3], i[4], i[5], i[6])
         

def copyout(diskname, name, out):

    dsk = DSK(diskname)
    tos = TOS(dsk)
    data = tos.read_file(name)
    f = open(out, "wb")
    data.tofile(f)
    f.close()

if __name__ == "__main__":
    cmd = sys.argv[1]
    args = sys.argv[2:]
    if cmd == "list":
        show_list(args[0])
    elif cmd == "copyout":
        copyout(args[0], args[1], args[2])
