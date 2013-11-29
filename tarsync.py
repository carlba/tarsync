import tarfile
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
    def __init__(self, settings_file):
        super(ProgramHandler, self).__init__()
        self.settings_file = settings_file
        self.os = platform.system()

    def store_dict_to_file(self, filename, thedict):
        with open(filename, "w+") as jsonfile:
            jsonfile.write(json.dumps(programs, indent =4))

    def read_dict_from_file(self, filename):
        with open(filename, "r+") as jsonfile:
            return json.loads(jsonfile.read())

    def handle_compression(self, compressed_fname, sfile):
        pass

    def handle_program(self, program):
        for path in program["paths"]:
            if self.os == "Linux":
                (spath,sfile) = os.path.split(path["linux"])
                #spath = path["linux"]
            elif self.os == "Windows":
                (spath,sfile) = os.path.split(path["windows"])
                #spath = path["windows"]
            #print "spath %s sfile %s" % (spath,sfile)
            self.old_dir = os.getcwd()
            os.chdir(spath)
            compressed_fname = "%s_%s.tar.gz" % (program["name"],path["name"])
            self.handle_compression(compressed_fname,sfile)
            os.chdir(self.old_dir)

    def handle_programs(self,programs):
        for program in programs:
            self.handle_program(program)

    def do_work(self):
        self.programs = self.read_dict_from_file(self.settings_file)
        self.handle_programs(self.programs)


class ProgramDecompresser(ProgramHandler):
    """docstring for ClassName"""

    def handle_compression(self, compressed_fname, sfile):
        tar = tarfile.open(os.path.join(self.old_dir, compressed_fname), "r:gz")
        #logging.debug(tar.getmembers())
        tar.extractall()
        tar.close()
	if os.path.exists(sfile):
	    safe_remove_folder(sfile)
        shutil.move(compressed_fname, sfile)


class ProgramCompresser(ProgramHandler):
    """docstring for ClassName"""

    def handle_compression(self, compressed_fname, sfile):
        tar = tarfile.open(compressed_fname, "w:gz")
        tar.add(sfile, arcname=compressed_fname)
        tar.close()
        shutil.move(compressed_fname, os.path.join(self.old_dir, compressed_fname))





def main():
    #programs = construct_dict()
    #store_dict_to_file("packer_settings.json",programs)
    #compress_programs(programs)
    #uncompress_programs(programs)
    logging.debug("Starting logging")

    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-d", "--compress", action="store_true")
    group.add_argument("-c", "--decompress", action="store_true")

    #logging.debug(repr(locals()))
    args = parser.parse_args()

    if not (args.compress or args.decompress):
        parser.error('No action requested, add --compress or --decompress')

    if args.compress:
        ph = ProgramCompresser("settings.json")
        ph.do_work()
    if args.decompress:
        ph = ProgramDecompresser("settings.json")
        ph.do_work()









if __name__ == '__main__':
    main()
    pass



