#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Przerabia pojedynczy plik, wyciągnięty wcześniej z .dsk na .tap.
Użycie, np.
./dsk2tap.py PACKMAKE packmake.tap 
"""

import array
import sys

def save_data(f, data):

    d = array.array('B', [255])
    d.extend(data)
    ch = 0
    for i in d:
        ch ^= i
    d.append(ch)

    l = len(d)
    dd = array.array('B')
    dd.append(l & 255)
    dd.append(l / 256)

    dd.tofile(f)
    d.tofile(f)
    f.close()

def header_prefix(name, typ, length, start):

    header = array.array('B', [0,typ])
    name = name.split('/')[-1]
    if name[0] == '.':
        name = name[1:]
    name += "           "
    name = name[:10].lower()
    header.fromstring(name)
    header.append(length & 255)
    header.append(length / 256)

    header.extend(start)
    return header
    
     
def save_program(name, autostart, variables, program, data):

    for i in xrange(1, len(data) - 1):
        if data[i] == ord('*') and data[i - 1] == 239 and data[i + 1] == ord('"'):
            data[i] = 32

    header = header_prefix(name, 0, len(data), autostart)
    header.extend(program)
    checksum = 0
    for i in header:
        checksum ^= i
    header.append(checksum)

    #print "header", header

    l = len(header)
    hh = array.array('B')
    hh.append(l & 255)
    hh.append(l / 256)
    f = open(sys.argv[2], "wb")
    hh.tofile(f)
    header.tofile(f)
    save_data(f, data)

def save_array(name, typ, array_length, array_address, data):

    header = header_prefix(name, typ, len(data), array_address)

    header.append(0)
    header.append(128)
    checksum = 0
    for i in header:
        checksum ^= i
    header.append(checksum)

    #print "header", header

    l = len(header)
    hh = array.array('B')
    hh.append(l & 255)
    hh.append(l / 256)
    f = open(sys.argv[2], "wb")
    hh.tofile(f)
    header.tofile(f)
    save_data(f, data)

def save_code(name, l, address, data):

    header = header_prefix(name, 3, len(data), address)

    header.append(0)
    header.append(128)
    checksum = 0
    for i in header:
        checksum ^= i
    header.append(checksum)

    #print "header", header

    l = len(header)
    hh = array.array('B')
    hh.append(l & 255)
    hh.append(l / 256)
    f = open(sys.argv[2], "wb")
    hh.tofile(f)
    header.tofile(f)    
    save_data(f, data)
    
if __name__ == "__main__":
    #print sys.argv
    inp = array.array('B')
    inp.fromstring(open(sys.argv[1], "rb").read())
    #print "inp", inp
    if inp[0] == 0: #program
        save_program(sys.argv[1], inp[1:3], inp[3:5], inp[5:7], inp[7:])
    elif inp[0] == 1: # numeric array
        save_array(sys.argv[1], 1, inp[1:3], inp[3:5], inp[5:])
    elif inp[0] == 2: # alphanumeric array
        save_array(sys.argv[1], 2, inp[1:3], inp[3:5], inp[5:])
    elif inp[0] == 3: # code
        save_code(sys.argv[1], inp[1:3], inp[3:5], inp[5:])
    else:
        raise Exception, "Unknown type " + str(inp[0])
