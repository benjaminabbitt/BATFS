from fuseBaffs import fuseBaffs
import fuse
from fuse import Fuse
import logging
from fsops.fsops import FsOps


def main():
    init_logging()
    fsops = init_fsops()
    server, root = init_baffs()
    fsops.set_root(root)
    #server.set_root(root)

    server.main()


def init_fsops():
    fso = FsOps.getInstance()
    return fso


def init_logging():
    LOG_FILENAME = '/tmp/baffs.log'
    # set up logging to file - see previous section for more details
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                        datefmt='%m-%d %H:%M',
                        filename=LOG_FILENAME,
                        filemode='w')
    # define a Handler which writes INFO messages or higher to the sys.stderr
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    # set a format which is simpler for console use
    formatter = logging.Formatter('%(name)-12s: %(levelname)-8s %(message)s')
    # tell the handler to use this format
    console.setFormatter(formatter)
    # add the handler to the root logger
    logging.getLogger('').addHandler(console)


def init_baffs():
    """
    Sets up file system, changes directory to the specified root.
    """
    usage = """
FunFS
""" + Fuse.fusage
    server = fuseBaffs.FuseBaffs(version="%prog " + fuse.__version__,
                                 usage=usage,
                                 dash_s_do='setsingle')

    server.parser.add_option(mountopt="root", metavar="PATH", default='/',
                             help="mirror filesystem from under PATH [default: %default]")
    server.parse(values=server, errex=1)

    return server, server.root


if __name__ == '__main__':
    main()
