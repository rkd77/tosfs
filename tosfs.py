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

from TOSDSK import *

fuse.fuse_python_api = (0, 2)

class TOSFS(fuse.Fuse):
    """
    """

    def __init__(self, *args, **kw):

        fuse.Fuse.__init__(self, *args, **kw)

        self.dsk = DSK(sys.argv[-2])
        self.dsk.show_header()

        self.tos = TOS(self.dsk)
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
        st.st_ino = 0
        st.st_size = 0

        c = path.count("/")
        if c == 1:
            nr_of_dir = 0
            filename = path[1:]
        else:
            dd = path.split("/")
            ff = "/".join(dd[1:-1])
            i = self.tos.names[ff]
            nr_of_dir = self.tos.entries[i][-1][0]
            filename = dd[-1]

        for i in self.tos.entries:
            if i[NR_OF_DIR] == nr_of_dir and filename == i[NAME]:
                if not i[NAME].endswith("DIR"):
                    st.st_mode = stat.S_IFREG | 0644
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
        if path == "/":
            nr_of_dir = 0
        else:
            i = self.tos.names[path[1:]]
            nr_of_dir = self.tos.entries[i][-1][0]
        print nr_of_dir
        entries = [fuse.Direntry("."), fuse.Direntry("..")]
        ee = filter(lambda x: x[NR_OF_DIR] == nr_of_dir and x[NO] == 0, self.tos.entries)
        e = map(lambda x: fuse.Direntry(x[NAME]), ee)
        #print ee
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
        log('*** open path=%s flags=%d' % (path, flags))
        return None

    def read ( self, path, length, offset ):
        log('*** read %s %d %d' % (path, length, offset))

        data = self.tos.read_file(path[1:])
        log("length = %d" % len(data))
        return data[offset:offset+length].tostring()

        #return -errno.ENOENT

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
