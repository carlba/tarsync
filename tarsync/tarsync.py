import os
import sys
import json
import platform
import argparse
import shutil
import stat
import appdirs


if "windows" in platform.system().lower():
    import tarfile
    import warp.os.os_extended
else:
    from tarfile_progress import tarfile_progress as tarfile

from warp.os.cygwinpath import CygwinPath

import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


#import logging
#logging.basicConfig(filename='%s.log' % program_name,level=logging.DEBUG)
def progressprint(complete, path=False):
    '''
    This is an example callback function. If you pass this as the
    progress callback then it will print a progress bar to stdout.
    '''
    barlen = complete / 2
    if path:
        print '\r|' + '#' * barlen + '-' * (50 - barlen) + '|', str(complete) + '% ' + path,
    else:
        print '\r|' + '#' * barlen + '-' * (50 - barlen) + '|', str(complete) + '%',

    if complete == 100:
        print 'File complete'


class ConfigHandler(object):

    def __init__(self, config_file):
        self._config_file = config_file
        self._config = {}

    def __store_dict_to_file(self, filename, thedict):
        with open(filename, "w+") as jsonfile:
            jsonfile.write(json.dumps(thedict, indent=4))

    def __read_dict_from_file(self, filename):
        with open(filename, "r+") as jsonfile:
            return json.loads(jsonfile.read())

    def load(self, config_file=None):
        if config_file:
            self._config = self.__read_dict_from_file(config_file)
        else:
            self._config = self.__read_dict_from_file(self._config_file)

    @property
    def config(self):
        return self._config

    def output(self):
        print json.dumps(self._config, indent=2)
    pass

    def output_section(self, section, format="json"):
        if format == json:
            print json.dumps(self._config[section], indent=2)
    pass


def construct_dict():
    programs = []
    paths = []

    path = {"linux": "/usr/bin", "windows":
            "c:\\Program Files (x86)\\XBMC\\portable_data\\userdata"}
    paths.append(path)
    path = {"linux": "/usr/bin",
            "windows": "c:\\Program Files (x86)\\XBMC\\portable_data\\addons"}
    paths.append(path)

    program = {"name": "xbmc",
               "paths": paths
               }

    programs.append(program)

    return programs


def safe_remove_folder(folder):
    if sys.platform.startswith('win'):
        if os.path.exists(folder):
            for root, dirs, files in os.walk(folder, topdown=False):
                for name in files:
                    filename = os.path.join(root, name)
                    os.chmod(filename, stat.S_IWRITE)
                    os.remove(filename)
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
            os.rmdir(folder)
    else:
        shutil.rmtree(folder)


class ProgramHandler(object):

    """Does something"""

    def __init__(self, config_handler, filter=None):
        super(ProgramHandler, self).__init__()
        self.os = self.get_os()
        self._config = config_handler.config
        self.filter = filter
        logger.debug("The filter contains:%s" % repr(self.filter))

    def get_os(self):
        if "cygwin" in platform.system().lower():
            ret = "cygwin"
        else:
            ret = platform.system().lower()
        return ret

    def handle_compression(self, compressed_fname, sfile):
        pass

    def handle_programs(self, programs):
        for program in programs:
            self.handle_program(program)

    def handle_program(self, program):
        if program["name"] in self.filter:
            for path in program["paths"]:
                logger.debug("The path for %s is %s" % (program["name"], path))
                logger.debug("self.os is %s" % (self.os))

                if self.os == "cygwin":
                    win_path = path["windows"]
                    cygpath = CygwinPath(win_path)
                    path["cygwin"] = cygpath.get_cygwin_path()

                if self.os in path.keys():
                    logger.debug("test")
                    expanded_path = os.path.expandvars(path[self.os])
                    self.handle_program_path(program, path, expanded_path)

        else:
            logger.debug("The program %s is not in the filter." %
                         repr(program["name"]))

    def handle_program_path(self, program, path, program_path):
        (spath, sfile) = os.path.split(program_path)
        os.chdir(self.out_path)
        self.old_dir = os.getcwd()
        if not os.path.exists(spath):
            os.makedirs(spath)
        os.chdir(spath)
        compressed_fname = "%s_%s.tar.gz" % (program["name"], path["name"])
        self.handle_compression(compressed_fname, sfile)
        os.chdir(self.old_dir)

    def do_work(self):
        if self.os == "cygwin":
            win_path = os.path.expandvars(self._config["path"]["windows"])
            cygpath = CygwinPath(win_path)
            self.out_path = cygpath.get_cygwin_path()
        else:
            self.out_path = os.path.expandvars(self._config["path"][self.os])
        self.symlink_path = os.path.expandvars(
            self._config["symlink_path"][self.os])
        logger.debug("The outpath for tarsync is %s" % self.out_path)
        self.programs = self._config["programs"]
        self.handle_programs(self.programs)


class ProgramDecompresser(ProgramHandler):

    """docstring for ClassName"""

    def handle_compression(self, compressed_fname, sfile):
        tar = tarfile.open(
            os.path.join(self.out_path, compressed_fname), "r:gz")
        # logger.debug(tar.getmembers())
        if "windows" in self.os:
            tar.extractall()
        else:
            tar.extractall(progress=progressprint)
        tar.close()
        if os.path.exists(sfile):
            safe_remove_folder(sfile)
        shutil.move(compressed_fname, sfile)


class ProgramCompresser(ProgramHandler):

    """docstring for ClassName"""

    def handle_compression(self, compressed_fname, sfile):
        tar = tarfile.open(compressed_fname, "w:gz")
        if "windows" in self.os:
            tar.add(sfile, arcname=compressed_fname)
        else:
            tar.add(sfile, arcname=compressed_fname, progress=progressprint)
        tar.close()
        shutil.move(
            compressed_fname, os.path.join(self.old_dir, compressed_fname))


class ProgramLister(ProgramHandler):

    """A class that lists all programs in a config-file"""

    def handle_program(self, program):
        print program["name"]


class ProgramSymlinker(ProgramHandler):

    """A class that symlinks programs specified in the config-file"""

    def handle_program_path(self, program, path, program_path):
        (spath, sfile) = os.path.split(program_path)

        if os.path.exists(program_path):
            if os.path.islink(program_path):
                if "windows" in platform.system().lower():
                    os.rmdir(program_path)
                else:
                    os.remove(program_path)
            else:
                os.rename(program_path, program_path + ".bak")

        os.symlink("%s/%s" % (self.symlink_path, sfile), program_path)


def main():
    #programs = construct_dict()
        # compress_programs(programs)
    # uncompress_programs(programs)

    app_name = os.path.splitext(os.path.basename(__file__))[0]

    logger.debug("Starting logger")
    logger.info("The application is named %s" % app_name)

    paths = []

    user_config_path = appdirs.user_data_dir("tarsync")
    paths.append(user_config_path)

    site_config_path = appdirs.site_data_dir("tarsync")
    if "xdg" in site_config_path:
        site_config_path = site_config_path.replace("/xdg", "")
    paths.append(site_config_path)

    found = False
    for path in paths:
        if os.path.exists(path):
            config_path = path
            break
    else:
        config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "config")

    logger.info("The configuration is read from %s" % config_path)

    logger.debug("APPNAME: %s" % app_name)

    config = ConfigHandler(os.path.join(config_path, app_name + ".json"))
    config.load()

    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-c", "--compress", nargs="*")
    group.add_argument("-d", "--decompress", nargs="*")
    group.add_argument("-s", "--symlink", nargs="*")
    group.add_argument("-l", "--list", action="store_true")

    # logger.debug(repr(locals()))
    args = parser.parse_args()

    if not (args.compress or args.decompress or args.list or args.symlink):
        parser.error('No action requested, add --compress or --decompress')

    if args.compress:
        logger.debug(args.compress)
        ph = ProgramCompresser(config, filter=args.compress)
        ph.do_work()
    if args.decompress:
        ph = ProgramDecompresser(config, filter=args.decompress)
        ph.do_work()
    if args.symlink:
        ph = ProgramSymlinker(config, filter=args.symlink)
        ph.do_work()
    if args.list:
        ph = ProgramLister(config)
        ph.do_work()

if __name__ == '__main__':
    main()
    pass
