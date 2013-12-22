from tarfile_progress import tarfile_progress as tarfile
import os
import sys
import json
import platform
import argparse
import shutil
import sys
import subprocess
import stat


program_name = "tarsync"


import logging
logging.basicConfig(filename='%s.log' % program_name,level=logging.DEBUG)



def progressprint(complete, path=False):



    '''
    This is an example callback function. If you pass this as the
    progress callback then it will print a progress bar to stdout.
    '''
    barlen = complete / 2
    if path:
        print '\r|' + '#' * barlen + '-' * (50 - barlen) + '|', str(complete) + '% ' +path,
    else:
        print '\r|' + '#' * barlen + '-' * (50 - barlen) + '|', str(complete) + '%',

    if complete == 100:
        print 'File complete'



class ConfigHandler(object):
    def __init__(self, config_file):
        self.config_file = config_file
        self.config = {}

    def store_dict_to_file(self, filename, thedict):
        with open(filename, "w+") as jsonfile:
            jsonfile.write(json.dumps(programs, indent =4))

    def read_dict_from_file(self, filename):
        with open(filename, "r+") as jsonfile:
            return json.loads(jsonfile.read())

    def load_config(self,config_file=None):
        if config_file:
            self.config = self.read_dict_from_file(config_file)
        else:
            self.config = self.read_dict_from_file(self.config_file)

    def get_config(self):
        return self.config
    pass

    def print_config(self):
        print json.dumps(self.config,indent=2)
    pass

    def print_config_section(self,section, format="json"):
        if format==json:
            print json.dumps(self.config[section],indent=2)
    pass



def construct_dict():
    programs = []
    paths = []

    path = {"linux" : "/usr/bin", "windows" : "c:\\Program Files (x86)\\XBMC\\portable_data\\userdata"}
    paths.append(path)
    path = {"linux" : "/usr/bin", "windows" : "c:\\Program Files (x86)\\XBMC\\portable_data\\addons"}
    paths.append(path)

    program = {"name" : "xbmc",
               "paths" : paths
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
    def __init__(self,config_handler,filter=None):
        super(ProgramHandler, self).__init__()
        self.os = platform.system().lower()
        self.config = config_handler.get_config()
        self.filter = filter
        logging.debug("The filter contains:%s" % repr(self.filter))

    def handle_compression(self, compressed_fname, sfile):
        pass

    def handle_program(self, program):
        if program["name"] in self.filter:
            for path in program["paths"]:
                logging.debug("The path for %s is %s" % (program["name"], path))
                if path[self.os]:
                    (spath,sfile) = os.path.split(path[self.os])
                    os.chdir(self.out_path)
                    self.old_dir = os.getcwd()
                    if not os.path.exists(spath):
                        os.makedirs(spath)
                    os.chdir(spath)
                    compressed_fname = "%s_%s.tar.gz" % (program["name"],path["name"])
                    self.handle_compression(compressed_fname,sfile)
                    os.chdir(self.old_dir)
        else:
            logging.debug("The program %s is not in the filter." % repr(program["name"]))

    def handle_programs(self,programs):
        for program in programs:
        	self.handle_program(program)

    def do_work(self):
        self.out_path = self.config["path"][self.os]

        logging.debug("The outpath for tarsync is %s" % self.out_path)

        self.programs = self.config["programs"]
        self.handle_programs(self.programs)


class ProgramDecompresser(ProgramHandler):
    """docstring for ClassName"""

    def handle_compression(self, compressed_fname, sfile):
        tar = tarfile.open(os.path.join(self.out_path, compressed_fname), "r:gz")
        #logging.debug(tar.getmembers())
        tar.extractall(progress = tarfile.progressprint)
        tar.close()
	if os.path.exists(sfile):
	    safe_remove_folder(sfile)
        shutil.move(compressed_fname, sfile)


class ProgramCompresser(ProgramHandler):
    """docstring for ClassName"""

    def handle_compression(self, compressed_fname, sfile):
        tar = tarfile.open(compressed_fname, "w:gz")
        tar.add(sfile, arcname=compressed_fname, progress = progressprint)
        tar.close()
        shutil.move(compressed_fname, os.path.join(self.old_dir, compressed_fname))

class ProgramLister(ProgramHandler):
    """docstring for ClassName"""

    def handle_program(self, program):
        print program["name"]



def main():
    #programs = construct_dict()
    #store_dict_to_file("packer_config.json",programs)
    #compress_programs(programs)
    #uncompress_programs(programs)
    logging.debug("Starting logging")

    config = ConfigHandler("config.json")
    config.load_config()

    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-c", "--compress", nargs="*")
    group.add_argument("-d", "--decompress", nargs="*")
    group.add_argument("-l", "--list", action="store_true")

    #logging.debug(repr(locals()))
    args = parser.parse_args()

    if not (args.compress or args.decompress or args.list):
        parser.error('No action requested, add --compress or --decompress')

    if args.compress:
        logging.debug(args.compress)
        ph = ProgramCompresser(config,filter=args.compress)
        ph.do_work()
    if args.decompress:
        ph = ProgramDecompresser(config, filter=args.decompress)
        ph.do_work()
    if args.list:
        ph = ProgramLister(config)
        ph.do_work()

if __name__ == '__main__':
    main()
    pass



