#!/usr/bin/env python

#   Faceted-Userspace Navigation File System (FUNFS)
#   An application of the faceted search paradigm to file systems using postfix-
#   expression boolean descriptor searches.
#   Copyright (C) 2010 Benjamin Abbitt <benjamin.abbitt@gmail.com>

#   Portions based upon xmp.py
#   Copyright (C) 2001  Jeff Epler  <jepler@unpythonic.dhs.org>
#   Copyright (C) 2006  Csaba Henk  <csaba.henk@creo.hu>
#


from fuse import Fuse

from control.control import Control


class FuseBaffs(Fuse):
    """
    File System
    BAFFS
    """

    def __init__(self, *args, **kw):
        Fuse.__init__(self, *args, **kw)
        self.root = '/'
        #self.file_class = FuseBaffsFile
        self.control = Control.getInstance()

    def getattr(self, path):
        return self.control.getattr(path)

    def readlink(self, path):
        return self.control.readlink(path)

    def readdir(self, path, offset):
        return self.control.readdir(path, offset)

    def unlink(self, path):
        self.control.unlink(path)

    def rmdir(self, path):
        self.control.rmdir(path)

    def symlink(self, path, path1):
        self.control.symlink(path, path1)

    def rename(self, path, path1):
        self.control.rename(path, path1)

    def link(self, path, path1):
        self.control.link(path, path1)

    def chmod(self, path, mode):
        self.control.chmod(path, mode)

    def chown(self, path, user, group):
        self.control.chown(path, user, group)

    def truncate(self, path, len):
        self.control.truncate(path, len)

    def mknod(self, path, mode, dev):
        self.control.mknod(path, mode, dev)

    def mkdir(self, path, mode):
        self.control.mkdir(path, mode)

    def utime(self, path, times):
        self.control.utime(path, times)

    #    def access(self, path, mode):
    #        return self.control.access(path, mode)

    #file system methods
    def open(self, path, flags):
        return self.control.open(path, flags)

    def create(self, path, flags, mode):
        return self.control.create(path, flags, mode)

    def read(self, path, length, offset, fh=None):
        return self.control.read(path, length, offset, fh)

    def write(self, path, buf, offset, fh=None):
        return self.control.write(path, buf, offset, fh)

    def fgetattr(self, path, fh=None):
        return self.control.fgetattr(path, fh)

    #
    #    def ftruncate(self, path, len, fh=None):
    #        self.control.ftruncate(path, len, fh)
    #
    #    def flush(self, path, fh=None):
    #        self.control.flush(path, fh)
    #
    def release(self, path, mode, fh=None):
        return self.control.release(path, mode, fh)

#
#    def fsync(path, fdatasync, fh=None):
#        self.control.fsync(fdatasync, fh)

