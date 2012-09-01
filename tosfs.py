#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Program do montowania obrazów dysku .DSK z system TOS.
Użycie, np.
mkdir disk
./tosfs.py MUSIC.DSK disk
cd disk
ls
cd -
Odmontowanie:
fusermount -u disk
"""
import array
import errno   # for error number codes (ENOENT, etc)
               # - note: these must be returned as negatives
import fuse
import os
import stat    # for file properties
import sys

fuse.fuse_python_api = (0, 2)

NAME = 1
NR_OF_DIR = 2
NO = 3
LAST = 4
N128 = 5

SECTOR_SIZE = 0
NUMBER_OF_SECTORS = 1
FILLER_BYTE = 2
DATA_BEGIN = 3
DATA_END = 4

def dirFromList(list):
    """
    Return a properly formatted list of items suitable to a directory listing.
    [['a', 'b', 'c']] => [[('a', 0), ('b', 0), ('c', 0)]]
    """
    return [[(x, 0) for x in list]]

def getDepth(path):
    """
    Return the depth of a given path, zero-based from root ('/')
    """
    if path == '/':
        return 0
    else:
        return path.count('/')

def getParts(path):
    """
    Return the slash-separated parts of a given path as a list
    """
    if path == '/':
        return [['/']]
    else:
        return path.split('/')

def name(tekst):
    t = filter(lambda c: c != 32, tekst)
    return "".join(map(lambda x: chr(x & 127), t))


def get_size(entry):
    #if entry[LAST] == 0:
    #    return entry[N128] * 128
    return entry[N128] * 128 + entry[LAST]

class TOS:
    """
    """
    def __init__(self, dsk):
        self.dsk = dsk
        self.read_disk()

    def read_track_data(self, track):
        t = self.dsk.get_track_info(track, 0)
        print "read_track_data:", track, t
        return self.dsk.data[t[DATA_BEGIN]:t[DATA_END]]

    def read_disk(self):
        self.system = self.read_track_data(0) + \
        self.read_track_data(1) + \
        self.read_track_data(2) + \
        self.read_track_data(3)
        self.directory = self.read_track_data(4)


    def list_entry(self, entry, number):
        """
        Returns number, name, dir, no, size_of_last, n128, allocation
        """
        nazwa = name(entry[1:0x09])
        n2 = name(entry[0x09:0x0c])
        if n2:
            nazwa += "." + n2
        if entry[0xa] & 128:
            nazwa = "." + nazwa
        nr_of_dir = entry[0]
        no = entry[0x0c]
        size_of_last = entry[0x0d]
        n128 =  entry[0x0f]
        
        #print "Numer podkatalogu:", entry[0]
        #print "Nazwa:", name(entry[1:0x9]) + "." + name(entry[0x9:0xc])
        #if entry[0xa] & 128:
        #    print "hidden"
        #if entry[0xb] & 128:
        #    print "read only"
        #print "Numer kolejnego rekordu", entry[0xc]
        #print "Liczba bajtow w ostatnim sektorze", entry[0xd]
        #print "Liczba 128 *", entry[0xe], entry[0xf]
        #print "Alokacja", entry[0x10:]

        return (number, nazwa, nr_of_dir, no, size_of_last, n128, entry[0xe], entry[0x10:])

    def read_dir(self):
        self.entries = []
        for i in range(128):
            a = self.list_entry(self.directory[i * 32 : i * 32 + 32], i)
            print a
            self.entries.append(a)

    def read_block(self, numer, bytes):
        t = 4 + numer / 4
        n = numer % 4
        data = self.read_track_data(t)
        if bytes > 1024:
            bytes = 1024
        return (data[n * 1024: n * 1024 + bytes], bytes)

    def get_size(self, entry):
        e = filter(lambda x: (x[NAME] == entry[NAME]) and \
        (x[NR_OF_DIR] == entry[NR_OF_DIR]), self.entries)
        size = 0
        for i in e:
            size += get_size(i)
        return size

    def find_entry(self, name, nr):
        for e in self.entries:
            if e[NO] != nr:
                continue
            if e[NAME] == name:
                return e

    def read_file(self, name):
        d = array.array('B')
        nr = 0
        while True:
            entry = self.find_entry(name, nr)
            print "read_file:", entry
            left = get_size(entry)
            print "left", left
            for i in entry[-1]:
                if i == 0:
                    return d
                data, r = self.read_block(i, left)
                #print data, r
                left -= r
                d.extend(data)
            if entry[N128] == 128:
                nr += 1
            else:
                break
        return d

    def get_data(self, name, length, offset):
        print "get_data: name = ", name, "length =",length,"offset =",offset
        data = self.read_file(name)
        #print "data = ", data[offset:offset+length]
        return data[offset:offset+length].tostring()

class DSK:
    """
    """
    def __init__(self, path):
        self.readdisk(path)

    def readdisk(self, path):
        self.f = open(path, "rb").read()
        self.data = array.array('B', self.f)
        self.number_of_tracks = self.data[0x30]
        self.number_of_sides = self.data[0x31]
        self.size_of_track = self.data[0x32] + 256 * self.data[0x33]
        self.tracks = []
        n = 0x100
        for i in xrange(self.number_of_tracks):
            for j in xrange(self.number_of_sides):
                self.tracks.append(n)
                n += self.size_of_track
        self.tracks.append(n)

    def show_info(self, prefix, a):
        info = ''.join(map(chr, a))
        print prefix, info


    def show_track_info(self, number):
        t = self.data[self.tracks[number]:self.tracks[number]+0x18]
        self.show_info('Track info:', t[:0xc])
        print "Track number", t[0x10]
        print "Side number", t[0x11]
        print "Sector_size", t[0x14]
        print "Number of sectors",t[0x15]
        print "GAP#3 length", t[0x16]
        print "Filler byte",t[0x17]

    def get_track_info(self, number, side):
        """
        Returns sector_size, number_of_sectors, filler_byte, start_of_data, end_of_data
        """
        tn = number * self.number_of_sides + side
        begin = self.tracks[tn]
        return (self.data[begin + 0x14],
        self.data[begin + 0x15],
        self.data[begin + 0x17],
        begin + 0x100,
        self.tracks[tn+1])

    def show_header(self):
        self.show_info("", self.data[:0x22])
        self.show_info("Creator", self.data[0x22:0x30])
        #print "Number of tracks", self.number_of_tracks
        #print "Size of track", self.size_of_track
        #print "Rozmiar =", 0x100 + self.number_of_tracks * self.number_of_sides * self.size_of_track
        #for i in xrange(self.number_of_tracks):
        #    self.show_track_info(i)


class TOSFS(fuse.Fuse):
    """
    """

    def __init__(self, *args, **kw):

        fuse.Fuse.__init__(self, *args, **kw)

        self.dsk = DSK(sys.argv[-2])
        self.dsk.show_header()

        self.tos = TOS(self.dsk)
        self.tos.read_dir()
        print 'Init complete.'

    def getattr(self, path):
        """
        - st_mode (protection bits)
        - st_ino (inode number)
        - st_dev (device)
        - st_nlink (number of hard links)
        - st_uid (user ID of owner)
        - st_gid (group ID of owner)
        - st_size (size of file, in bytes)
        - st_atime (time of most recent access)
        - st_mtime (time of most recent content modification)
        - st_ctime (platform dependent; time of most recent metadata change on Unix,
                    or the time of creation on Windows).
        """

        st = fuse.Stat()
        st.st_mode = stat.S_IFDIR | 0755
        st.st_nlink = 2
        st.st_atime = 0
        st.st_mtime = st.st_atime
        st.st_ctime = st.st_atime
        st.st_uid = st.st_gid = 501

        for i in self.tos.entries:
            if path[1:] == i[NAME]:
                st.st_mode = stat.S_IFREG | 0755
                st.st_ino = i[0]
                st.st_size = self.tos.get_size(i)
                return st
        
        print '*** getattr', path
        #print 'self.dupa', self.dupa

        #depth = getDepth(path) # depth of path, zero-based from root
        #pathparts = getParts(path) # the actual parts of the path

        if path == "/":
            pass
        else:
            return -errno.ENOENT

        return st

    def readdir(self, path, offset):
        print "readdir: path =",path,"offset =",offset
        entries = [fuse.Direntry("."), fuse.Direntry("..")]
        ee = filter(lambda x: (x[NR_OF_DIR] < 128) and (x[NO] == 0), self.tos.entries)
        e = map(lambda x: fuse.Direntry(x[NAME]), ee)
        return entries + e

#    def getdir(self, path):
#        """
#        return: [[('file1', 0), ('file2', 0), ... ]]
#        """

#        print '*** getdir', path
#        return -errno.ENOSYS

#    def mythread ( self ):
#        print '*** mythread'
#        return -errno.ENOSYS

#    def chmod ( self, path, mode ):
#        print '*** chmod', path, oct(mode)
#        return -errno.ENOSYS

#    def chown ( self, path, uid, gid ):
#        print '*** chown', path, uid, gid
#        return -errno.ENOSYS

#    def fsync ( self, path, isFsyncFile ):
#        print '*** fsync', path, isFsyncFile
#        return -errno.ENOSYS

#    def link ( self, targetPath, linkPath ):
#        print '*** link', targetPath, linkPath
#        return -errno.ENOSYS

#    def mkdir ( self, path, mode ):
#        print '*** mkdir', path, oct(mode)
#        return -errno.ENOSYS

#    def mknod ( self, path, mode, dev ):
#        print '*** mknod', path, oct(mode), dev
#        return -errno.ENOSYS

    def open ( self, path, flags ):
        print '*** open', path, flags
        return None

    def read ( self, path, length, offset ):
        print '*** read', path, length, offset
        for i in self.tos.entries:
            if path[1:] == i[NAME]:
                return self.tos.get_data(i[NAME], length, offset)

        return -errno.ENOENT

#    def readlink ( self, path ):
#        print '*** readlink', path
#        return -errno.ENOSYS

#    def release ( self, path, flags ):
#        print '*** release', path, flags
#        return -errno.ENOSYS

#    def rename ( self, oldPath, newPath ):
#        print '*** rename', oldPath, newPath
#        return -errno.ENOSYS

#    def rmdir ( self, path ):
#        print '*** rmdir', path
#        return -errno.ENOSYS

#    def statfs ( self ):
#        print '*** statfs'
#        return -errno.ENOSYS

#    def symlink ( self, targetPath, linkPath ):
#        print '*** symlink', targetPath, linkPath
#        return -errno.ENOSYS

#    def truncate ( self, path, size ):
#        print '*** truncate', path, size
#        return -errno.ENOSYS

#    def unlink ( self, path ):
#        print '*** unlink', path
#        return -errno.ENOSYS

#    def utime ( self, path, times ):
#        print '*** utime', path, times
#        return -errno.ENOSYS

#    def write ( self, path, buf, offset ):
#        print '*** write', path, buf, offset
#        return -errno.ENOSYS


if __name__ == "__main__":
    fs = TOSFS()
    fs.parse(errex = 1)
    fs.main()
