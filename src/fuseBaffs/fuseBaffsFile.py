from control.controlBaffsFile import ControlBaffsFile


class FuseBaffsFile(object):
    def __init__(self, path, flags, *mode):
        self.controlFile = ControlBaffsFile(path, flags, mode)

        #            self.file = os.fdopen(os.open("." + path, flags, *mode),
        #                                  flag2mode(flags))
        self.fd = self.controlFile.getFd()

    def read(self, length, offset):
        return self.controlFile.read(length, offset)

    def write(self, buf, offset):
        return self.controlFile.write(buf, offset)

    def release(self, flags):
        self.controlFile.release(flags)

    def fsync(self, isfsyncfile):
        self.controlFile.fsync(isfsyncfile)

    def flush(self):
        self.controlFile.flush()

    def fgetattr(self):
        return self.controlFile.fgetattr()

    def ftruncate(self, len):
        self.controlFile.ftrucate(len)
