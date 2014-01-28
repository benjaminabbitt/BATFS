import logging


class IndirectionFile:
    def __init__(self, id, name):
        self.id = id
        self.name = name

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        if (type(other) != type(self)):
            logging.error("Tried to perform equality check on invalid type: %s" % (other))
            raise TypeError

        if (self.id == other.getId()):
            return True
        else:
            return False

    def __repr__(self):
        return "%s(%s)" % (self.name, self.id)

    def getId(self):
        return self.id

    def getName(self):
        return self.name

    def setName(self, name):
        self.name = name


