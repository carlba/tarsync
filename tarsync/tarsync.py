import os
import sys
import json
import platform
import argparse
import shutil
import stat
import appdirs
import pprint


pp = pprint.PrettyPrinter(indent=4)


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


class MissingPathError(Exception):
    pass


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
        #import ipdb;ipdb.set_trace()
        self._config_file = os.path.basename(config_file)
        self._config = {}

    def __locate_config_directory(self, config_file):
        paths = []

        user_config_path = appdirs.user_config_dir("tarsync")
        paths.append(user_config_path)

        site_config_path = appdirs.site_config_dir("tarsync")
        paths.append(site_config_path)

        for path in paths:
            if os.path.exists(path):
                config_path = path
                break
        else:
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "config")
        logger.info("Looking for config in %s" % paths)
        logger.info("The configuration is read from %s" % config_path)

        return config_path

    def __store_dict_to_file(self, filename, thedict):
        with open(filename, "w+") as jsonfile:
            jsonfile.write(json.dumps(thedict, indent=4))

    def __read_dict_from_file(self, filename):
        with open(filename, "r+") as jsonfile:
            return json.loads(jsonfile.read())

    def load(self, config_file=None):
        if config_file:
            config_file = config_file
        else:
            config_file = self._config_file

        located_config_directory = self.__locate_config_directory(config_file)
        located_config_file = os.path.join(
            located_config_directory, config_file)

        self._config = self.__read_dict_from_file(located_config_file)

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


class Path(object):

    def __init__(self, os_paths, name=None):
        self._os_paths = os_paths
        self._os = self.__get_os()
        self._name = name

    def __get_os(self):
        if "cygwin" in platform.system().lower():
            ret = "cygwin"
        else:
            ret = platform.system().lower()
        return ret

    @property
    def path(self):
        try:
            path = self._os_paths[self._os]
        except KeyError as e:
            if self._os == "cygwin":
                win_path = self._os_paths["windows"]
                cygpath = CygwinPath(win_path)
                path = cygpath.get_cygwin_path()
            else:
                raise MissingPathError(
                    "The path for %s is missing in the config-file" % self._os)
        else:
            expanded_path = os.path.expandvars(path)

        return expanded_path

    def make(self):
        if not os.path.exists(self.path):
            os.makedirs(self.path)

    def __generate_name(self, program_name):
        #import ipdb;ipdb.set_trace()
        compressed_fname = "%s_%s.tar.gz" % (program_name, self._name)
        return compressed_fname

    def __prepare(self, out_path):
        (spath, sfile) = os.path.split(self.path)
        os.chdir(out_path.path)
        self.old_dir = os.getcwd()
        self.make()
        os.chdir(spath)

        return spath, sfile

    def compress(self, program_name, out_path):
        spath, sfile = self.__prepare(out_path)
        compressed_fname = self.__generate_name(program_name)
        tar = tarfile.open(compressed_fname, "w:gz")
        if "windows" in self._os:
            tar.add(sfile, arcname=compressed_fname)
        else:
            tar.add(sfile, arcname=compressed_fname, progress=progressprint)
        tar.close()
        shutil.move(
            compressed_fname, os.path.join(self.old_dir, compressed_fname))

    def decompress(self, program_name, out_path):
        spath, sfile = self.__prepare(out_path)
        compressed_fname = self.__generate_name(program_name)
        tar = tarfile.open(
            os.path.join(out_path.path, compressed_fname), "r:gz")
        if "windows" in self._os:
            tar.extractall()
        else:
            tar.extractall(progress=progressprint)
        tar.close()
        if os.path.exists(sfile):
            safe_remove_folder(sfile)
        shutil.move(compressed_fname, sfile)


class Program(object):

    """docstring for Program"""

    def __init__(self, **kwargs):
        super(Program, self).__init__()
        self.name = kwargs.pop("name")
        self.paths = kwargs.pop("paths")
        self.out_path = kwargs.pop("out_path")

    def install(self):
        for path_entry in self.paths:
            path = Path(os_paths=path_entry)
            out_path = Path(os_paths=self.out_path)
            out_path.make()

    def compress(self):
        for path_entry in self.paths:
            out_path = Path(os_paths=self.out_path)
            out_path.make()
            path = Path(os_paths=path_entry, name=path_entry["name"])
            path.compress(self.name, out_path)

    def decompress(self):
        for path_entry in self.paths:
            out_path = Path(os_paths=self.out_path)
            path = Path(os_paths=path_entry, name=path_entry["name"])
            path.decompress(self.name, out_path)


def main():
    #programs = construct_dict()
        # compress_programs(programs)
    # uncompress_programs(programs)

    app_name = os.path.splitext(os.path.basename(__file__))[0]

    logger.debug("Starting logger")
    logger.info("The application is named %s" % app_name)

    config = ConfigHandler(app_name + ".json")
    config.load()

    logger.debug(json.dumps(config.config, indent=4))

    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-c", "--compress", nargs="*")
    group.add_argument("-d", "--decompress", nargs="*")
    group.add_argument("-s", "--symlink", nargs="*")
    group.add_argument("-l", "--list", action="store_true")
    group.add_argument("-i", "--install", nargs="*")

    # logger.debug(repr(locals()))
    args = parser.parse_args()

    if not (args.compress or args.decompress or args.list or args.symlink or args.install):
        parser.error('No action requested, add --compress or --decompress')

    config_programs = config.config["programs"]
    dict_programs = {
        program["name"]: program for (index, program) in enumerate(config_programs)}

    def get_programs(config, filter=None):
        programs = []

        for program_name in dict_programs:
            if filter and not program_name in filter:
                continue
            program = Program(name=program_name,
                              paths=dict_programs[program_name]["paths"],
                              out_path=config.config["path"])
            programs.append(program)
        return programs

    args_list = ["compress", "decompress", "symlink", "list", "install"]

    for arg_name in args_list:
        arg = getattr(args, arg_name)
        if arg:
            programs = get_programs(config, arg)
            for program in programs:
                method = getattr(program, arg_name)
                method()


    # for program in programs:
    #     if args.compress:
    #         program.compress()
    #     if args.decompress:
    #         program.decompress()
    #     if args.symlink:
    #         ph = ProgramSymlinker(config, filter=args.symlink)
    #         ph.do_work()
    #     if args.list:
    #         print program.name
    #     if args.install:
    #         program.install()
if __name__ == '__main__':
    main()
    pass
