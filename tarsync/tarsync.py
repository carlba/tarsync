import os
import sys
import json
import platform
import argparse
import shutil
import stat
import pprint

from warp.os.cygwinpath import CygwinPath
from warp.os import safe_remove_folder
from warp.config.confighandler import ConfigHandler
from warp.config.appdata import AppData

from exceptions import MissingPathError


import warp.logging
log = warp.logging.get_logger(__name__)

if "windows" in platform.system().lower():
    import tarfile
    import warp.os.os_extended
else:
    from tarfile_progress import tarfile_progress as tarfile

pp = pprint.PrettyPrinter(indent=4)


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
    info = {"system": "main"}
    app_path = os.path.abspath(__file__)
    app_name = os.path.splitext(os.path.basename(__file__))[0]

    log.debug("Starting log", **info)
    log.info("The application path is named %s" % app_path, **info)
    log.info("The application is named %s" % app_name, **info)

    appdata = AppData(app_name, app_path, develop=True)
    config = ConfigHandler(appdata.get_config_file_path("tarsync.json"))
    config.load()

    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-c", "--compress", nargs="*")
    group.add_argument("-d", "--decompress", nargs="*")
    group.add_argument("-s", "--symlink", nargs="*")
    group.add_argument("-l", "--list", action="store_true")
    group.add_argument("-i", "--install", nargs="*")

    # log.debug(repr(locals()))
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

    args_list = ["compress", "decompress", "symlink", "install"]

    for arg_name in args_list:
        arg = getattr(args, arg_name)
        if arg:
            programs = get_programs(config, arg)
            for program in programs:
                method = getattr(program, arg_name)
                method()

    if args.list:
        programs = get_programs(config, arg)
        for program in programs:
            print program.name

if __name__ == '__main__':
    main()
