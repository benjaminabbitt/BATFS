from fsops.fsOpsBaffsFile import FsOpsBaffsFile
from indirection.indirection import Indirection
from control import Control
from control import OP
import logging


class ControlBaffsFile(object):
    def __init__(self, path, flags, *mode):
        self.control = Control.getInstance()
        self.indirection = Indirection.getInstance()
        self.logger = logging.getLogger(str(self.__class__.__name__))
        self.logger.debug("getting storage name for %s" % (path))
        path, name = self.control._breakPath(path)
        tags = self.indirection._getCanonicalName(path)

        #get rid of the operators
        tags = list(set(tags).difference(set(OP)))
        path = self.control._makeStoragePath(list(tags), name)
        self.logger.debug("storage name is: %s" % (path))
        self.fsopsbaffsfile = FsOpsBaffsFile(path, flags, *mode)

        #finally, add the file to the database
        fid, tags = self.indirection.addFile(path, name)
        self.logger.debug("File added.  ID:%s, tags:%s" % (fid, tags))

    def read(self, length, offset):
        return self.fsopsbaffsfile.read(length, offset)

    def write(self, buf, offset):
        return self.fsopsbaffsfile.write(buf, offset)

    def release(self, flags):
        self.fsopsbaffsfile.release(flags)

    def fsync(self, isfsyncfile):
        self.fsopsbaffsfile.fsync(isfsyncfile)

    def flush(self):
        self.fsopsbaffsfile.flush()

    def fgetattr(self):
        return self.fsopsbaffsfile.fgetattr()

    def ftruncate(self, len):
        self.fsopsbaffsfile.ftrucate(len)

    def getFd(self):
        return self.fsopsbaffsfile.getFd()