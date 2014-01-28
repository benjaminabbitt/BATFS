import os

from control.control import Control


def flag2mode(flags):
    md = {os.O_RDONLY: 'r', os.O_WRONLY: 'w', os.O_RDWR: 'w+'}
    m = md[flags & (os.O_RDONLY | os.O_WRONLY | os.O_RDWR)]

    if flags | os.O_APPEND:
        m = m.replace('w', 'a', 1)

    return m


class FsOpsBaffsFile(object):
    def __init__(self, path, flags, *mode):
        self.control = Control.getInstance()
        print "attempting to open path: %s" % (path)
        base, name = os.path.split(path)
        print "makedirs: %s" % (base)
        os.makedirs(base)
        print path, flag2mode(flags)
        self.file = open(path, flag2mode(flags))
        self.fd = self.file.fileno()

    def read(self, length, offset):
        self.file.seek(offset)
        return self.file.read(length)

    def write(self, buf, offset):
        self.file.seek(offset)
        self.file.write(buf)
        return len(buf)

    def release(self, flags):
        self.file.close()

    def _fflush(self):
        if 'w' in self.file.mode or 'a' in self.file.mode:
            self.file.flush()

    def fsync(self, isfsyncfile):
        self._fflush()
        if isfsyncfile and hasattr(os, 'fdatasync'):
            os.fdatasync(self.fd)
        else:
            os.fsync(self.fd)

    def flush(self):
        self._fflush()
        # cf. xmp_flush() in fusexmp_fh.c
        os.close(os.dup(self.fd))

    def fgetattr(self):
        return os.fstat(self.fd)

    def ftruncate(self, len):
        self.file.truncate(len)

    def getFd(self):
        return self.fd
