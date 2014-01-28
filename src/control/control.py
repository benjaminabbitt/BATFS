from indirection.indirection import Indirection
from fsops.fsops import FsOps
from lib.singletonmixin import Singleton
import os
from mystat import MyStat
import stat
import logging
import fuse
import errno

TRASHTAG = "Trash"
FSEPERATOR = "/"
OP = ["AND", "OR", "NOT"]


class Control(Singleton):
    def __init__(self):
        self.indirection = Indirection.getInstance()
        self.fsops = FsOps.getInstance()
        self.logger = logging.getLogger(str(self.__class__.__name__))
        self.logger.debug("Setup!")

    def getattr(self, path):
        opath = path
        path, name = self._breakPath(path)
        attr = MyStat()
        if ((self.indirection.isTag(name)) or (name in OP) or (name in [".", "..", "/", ""])):
            attr.st_mode = stat.S_IFDIR | 0755
            attr.st_nlink = 2
        else:
            try:
                path = self._getStoragePath(opath)
                self.logger.debug("getting attrs: %s" % (path))
                attr = self.fsops.getattr(path)
                self.logger.debug("path: %s, attrs:%s" % (path, attr))
            except IOError:
                return -errno.ENOENT

        return attr

    #    def readlink(self, path):
    #        cpath = self._getStoragePath(path)
    #        return cpath

    def readdir(self, path, offset):
        self.logger.debug("in readdir, reading path: %s" % (path))
        path, name = self._breakPath(path)
        #breakpath splits the name out of the path..good for queries, not for readdir
        if (path[0] == ""):
            del path[0]
        path.append(name)
        dirents = [".", ".."]
        dirents.extend(OP)
        self.logger.debug("readdir query path: %s" % (path))
        dirents.extend(list(self.indirection.getFiles(path, False)))
        self.logger.debug("readdir path:%s, files:%s" % (path, dirents))
        dirents.extend(list(self.indirection.getTags(path, False)))
        self.logger.debug("readdir path:%s, files and tags:%s" % (path, dirents))
        for entry in dirents:
            yield fuse.Direntry(entry)
            #return self.fsops.readdir(cpath, offset)

    def unlink(self, path):
        opath = path
        path, name = self._breakPath(path)
        if (self.indirection.isTag(name)):
            self.logger.debug("Unlink Tag: %s" % (name))
            #self.indirection.rmTags([name])
        else:
            #file
            self.logger.debug("Deleting File: %s" % (opath))
            tags = self.indirection.getTagsFromFile(path, name)
            self.logger.debug("found that it has tags: %s" % (tags))
            if (tags == set([TRASHTAG])):
                self.logger.debug("it has only the trash tag, unlinking")
                #remove from file system
                path = self._getStoragePath(opath)
                self.fsops.unlink(path)
            else:
                #write tags to file
                #self.fsops.writeTrash(fname, tags)
                #remove tags
                spath = self._getStoragePath(opath)
                path, name = self._breakPath(spath)
                self.logger.debug("storage path: %s" % (spath))
                file = self.indirection.getFile(path, name)
                self.logger.debug("file database id: %s" % (file))
                self.indirection.rmTagsFromFile(file, tags)
                #add TRASHTAG
                self.indirection.addTagsToFile(file, [TRASHTAG])
                path = spath
                path1 = self._makeStoragePath([TRASHTAG], name)
                self.logger.debug("more than just the trash tag, moving: %s -> %s" % (path, path1))
                self.fsops.rename(path, path1)

    def rmdir(self, path):
        #get all files that have the tag
        #remove the tag from the storage name of the files
        #remove the tag from the database
        pass
        #self.fsops.rmdir(path)

    #    def symlink(self, path, path1):
    #        self.fsops.symlink(path, path1)

    def rename(self, path, path1):
        self.logger.debug("Rename received: %s -> %s" % (path, path1))
        #store original path for use later
        opath = path
        path, name = self._breakPath(path)
        path1, name1 = self._breakPath(path1)

        self.logger.debug("rename before istag")

        if (self.indirection.isTag(name)):
            #tag rename
            self.logger.debug("have decided %s is a tag" % (name))
            #get list of files to change
            if (not self.indirection.isTag(name1)):
                self.indirection.addTags([name1])
            files = self.indirection.getFiles([name])
            for file in files:
                storageName = self._getStoragePath(self._joinPath([name], file))
                path, _ = self._breakPath(storageName)
                path1 = set(path).difference(set([name])).union([name1])
                spath = self._makeStoragePath(path, file)
                spath1 = self._makeStoragePath(path1, file)
                self.fsops.rename(spath, spath1)
                self.logger.debug("getting file id for: %s:%s" % (path, file))
                file_id = self.indirection.getFile(path, file)
                self.logger.debug("file id: %s" % (file_id))
                self.indirection.addTagsToFile(file_id, [name1])
                self.indirection.rmTagsFromFile(file_id, [name])
            self.indirection.rmTags([name])

        else:
            #file rename
            self.logger.debug("have decded %s is a file" % (name))
            storageName = self._getStoragePath(opath)
            self.logger.debug("storage name: %s" % (storageName))
            tagsRm, tagsAdd = self.indirection.retagFile(path, name, path1, name1)
            self.logger.debug("after indirection call: tagsRm: %s, tagsAdd: %s" % (tagsRm, tagsAdd))
            path, _ = self._breakPath(storageName)
            self.logger.debug("before set ops")
            if (tagsAdd != None or tagsRm != None):
                path1 = set(path).difference(tagsRm).union(tagsAdd)
            else:
                path1 = path
            path = self._makeStoragePath(path, name)
            path1 = self._makeStoragePath(path1, name1)
            self.logger.debug("before fsops call")
            self.fsops.rename(path, path1)


        #    def link(self, path, path1):
        #        self.fsops.link(path, path1)

    def chmod(self, path, mode):
        path = self._getStoragePath(path)
        self.fsops.chmod(path, mode)

    def chown(self, path, user, group):
        path = self._getStoragePath(path)
        self.fsops.chown(path, user, group)

    def truncate(self, path, len):
        path = self._getStoragePath(path)
        self.fsops.truncate(path, len)

    #    def mknod(self, path, mode, dev):
    #        I suspect mknod is depreciated, leaving it in for now, but need to evaluate later.  As of 4/18/2010 I have not seen it called.
    #        self.logger.debug("in mknod")
    #        path, name = self._breakPath(path)
    #        self.logger.debug("to indirection: %s, %s"%(path, name))
    #        fid, tags = self.indirection.addFile(path, name)
    #        tags = list(tags)
    #        tags.sort()
    #        #extend the now sorted facets list with the file name.  This puts the file name last in the list.
    #        path = tags.extend([name])
    #        #the * notation expldes the path list into a positional parameter list.
    #        path = os.path.join(*path)
    #        self.logger.debug("path being passed to fsops.mknod: %s"%(path))
    #        self.fsops.mknod(path, mode, dev)

    def mkdir(self, path, mode):
        self.logger.debug("mkdir path: %s, mode: %s", path, mode)
        tags, name = self._breakPath(path)
        self.logger.debug("adding tag: %s", name)
        self.indirection.addTags([name])

    def utime(self, path, times):
        path = self._getStoragePath(path)
        self.logger.debug("utime called.  Path: %s, times: %s" % (path, times))
        self.fsops.utime(path, times)

    def access(self, path, mode):
        path = self._getStoragePath(path)
        return self.fsops.access(path, mode)


    #file system methods
    def open(self, path, flags):
        path = self._getStoragePath(path)
        return self.fsops.open(path, flags)

    def create(self, path, flags, mode):
        self.logger.debug("getting storage name for %s" % (path))
        path, name = self._breakPath(path)
        #finally, add the file to the database
        fid, tags = self.indirection.addFile(path, name)
        self.logger.debug("File added.  ID:%s, tags:%s" % (fid, tags))

        #get rid of the operators
        tags = list(set(tags).difference(set(OP)))
        path = self._makeStoragePath(list(tags), name)
        self.logger.debug("storage name is: %s" % (path))
        print path, flags, mode
        return self.fsops.create(path, flags, mode)


    def read(self, path, length, offset, fh=None):
        path = self._getStoragePath(path)
        return self.fsops.read(path, length, offset, fh)

    def write(self, path, buf, offset, fh=None):
        path = self._getStoragePath(path)
        return self.fsops.write(path, buf, offset, fh)

    def fgetattr(self, path, fh=None):
        path = self._getStoragePath(path)
        return self.fsops.fgetattr(path, fh)

    #    def ftruncate(self, path, len, fh=None):
    #        self.control.ftruncate(path, len, fh)
    #
    #    def flush(self, path, fh=None):
    #        self.control.flush(path, fh)
    #
    def release(self, path, mode, fh=None):
        path = self._getStoragePath(path)
        self.fsops.release(path, mode, fh)

    #
    #    def fsync(path, fdatasync, fh=None):
    #        self.control.fsync(fdatasync, fh)




    def _getStoragePath(self, path):
        path, fname = self._breakPath(path)
        tags = list(self.indirection.getTagsFromFile(path, fname))
        return self._makeStoragePath(tags, fname)

    def _breakPath(self, path):
        self.logger.debug("Breaking path %s" % (path))
        path, name = os.path.split(path)
        path = path.split(FSEPERATOR)
        if (path[0] == ""):
            path = path[1:]
        return path, name

    def _joinPath(self, tags, name):
        path = []
        path.extend(tags)
        path.extend([name])
        return os.path.join(*path)

    def _makeStoragePath(self, tags, name):
        tags = list(tags)
        tags.sort()
        return self._joinPath(tags, name)