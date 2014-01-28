import os
import logging
import sys

from lib.singletonmixin import Singleton


def flag2mode(flags):
    md = {os.O_RDONLY: 'r', os.O_WRONLY: 'w', os.O_RDWR: 'w+'}
    m = md[flags & (os.O_RDONLY | os.O_WRONLY | os.O_RDWR)]

    if flags | os.O_APPEND:
        m = m.replace('w', 'a', 1)

    return m


class FsOps(Singleton):
    def __init__(self):
        self.logger = logging.getLogger(str(self.__class__.__name__))

    def set_root(self, root):
        try:
            os.chdir(root)
            self.logger.info("Setting Root File System: %s" % (root))
        except OSError:
            self.logger.error("can't enter root of underlying filesystem")
            sys.exit(1)

    def getattr(self, path):
        path = os.path.join(".", path)
        self.logger.debug("fsops:getattr: %s" % (path))
        return os.lstat(path)

    def readlink(self, path):
        return os.readlink(path)

    #    def readdir(self, path, offset):
    #        for e in os.listdir("." + path):
    #            yield fuse.Direntry(e)

    def unlink(self, path):
        path = os.path.join(".", path)
        os.unlink(path)

    def rmdir(self, path):
        path = os.path.join(".", path)
        os.rmdir(path)

    #    def symlink(self, path, path1):
    #        path = os.path.join(".", path)
    #        os.symlink(path, path1)

    def rename(self, path, path1):
        path = os.path.join(".", path)
        path1 = os.path.join(".", path1)
        base, name = os.path.split(path1)
        self.logger.debug("makedirs: %s" % (base))
        try:
            os.makedirs(base)
        except Exception, e:
            self.logger.debug(e)
        self.logger.debug("Rename: %s -> %s" % (path, path1))
        os.rename(path, path1)

    def link(self, path, path1):
        os.link("." + path, "." + path1)

    def chmod(self, path, mode):
        path = os.path.join(".", path)
        os.chmod(path, mode)

    def chown(self, path, user, group):
        path = os.path.join(".", path)
        os.chown(path, user, group)

    def truncate(self, path, len):
        path = os.path.join(".", path)
        f = open(path, "a")
        f.truncate(len)
        f.close()

    #    def mknod(self, path, mode, dev):
    #        os.mknod("." + path, mode, dev)

    def mkdir(self, path, mode):
        path = os.path.join(".", path)
        os.mkdir(path, mode)

    def utime(self, path, times):
        path = os.path.join(".", path)
        os.utime(path, times)

    def access(self, path, mode):
        path = os.path.join(".", path)
        if not os.access(path, mode):
            return -sys.EACCES


    #FS Ops
    def open(self, path, flags):
        self.logger.debug("open flags: %s, flag2mode: %s" % (flags, flag2mode(flags)))
        return open(path, flag2mode(flags))

    def create(self, path, flags, mode):
        base, name = os.path.split(path)
        self.logger.debug("makedirs: %s" % (base))
        try:
            os.makedirs(base)
        except Exception, e:
            self.logger.debug(e)

        self.logger.debug("flags: %s, flag2mode(flags): %s, mode: %s, flag2mode(mode): %s" % (
        flags, flag2mode(flags), mode, flag2mode(mode)))
        return open(path, flag2mode(flags))


    def read(self, path, length, offset, fh=None):
        if not fh:
            fh = open(path, "r")
        fh.seek(offset)
        return fh.read(length)

    def write(self, path, buf, offset, fh=None):
        if not fh:
            fh = open(path, "w")
        fh.seek(offset)
        fh.write(buf)
        return len(buf)

    def fgetattr(self, path, fh=None):
        self.logger.debug("path: %s, fh: %s" % (path, fh))
        if not fh:
            fh = open(path, "r")
            self.logger.debug("handle not passed in, opened.")
        self.logger.debug("fh: %s" % (fh))
        return os.fstat(fh.fileno())

    #
    #    def ftruncate(self, path, len, fh=None):
    #        return -errno.ENOINT
    #
    #    def flush(self, path, fh=None):
    #        return -errno.ENOINT
    #
    def release(self, path, mode, fh=None):
        self.logger.debug("releasing path: %s, mode: %s (%s), fh: %s" % (path, mode, flag2mode(mode), fh))
        if not fh:
            fh = open(path, flag2mode(mode))
        fh.close()

#
#    def fsync(path, fdatasync, fh=None):
#        self.control.fsync(fdatasync, fh)

