import platform
import re
import os
import subprocess




class CygwinPath(object):
    """docstring for CygwinPath"""
    def __init__(self, path):
        super(CygwinPath, self).__init__()
        self.path = path
        self.os = self.get_os()

    def convert_winenv_linenv(self, path):
        winenv_re=re.compile("(%.*?%)")
        matches = winenv_re.findall(path)
        for match in matches:
            path = path.replace(match,"$" + match[1:-1])
        return path

    def get_os(self):
        if "cygwin" in platform.system().lower():
            ret = "cygwin"
        else:
            ret = platform.system().lower()
        return ret

    def get_cygwin_path(self):
        if self.os == "cygwin":
            self.path = self.convert_winenv_linenv(self.path)
        else:
            pass
        self.path = os.path.expandvars(self.path)
        p = subprocess.Popen(['cygpath', self.path], stdout=subprocess.PIPE,
                                                     stderr=subprocess.PIPE)
        out, err = p.communicate()
        if err:
            print err
        return out.rstrip()



    def get_windows_path(self):
        self.path = os.path.expandvars(self.path)
        p = subprocess.Popen(['cygpath', '-w',self.path], stdout=subprocess.PIPE,
                                                          stderr=subprocess.PIPE)
        out, err = p.communicate()
        if err:
            print err
        return out.rstrip()

    def convert_linuxenv_winenv(self):
        pass






def main():
    path = os.path.expandvars("%APPDATA%\.purple")

    path = "%APPDATA%\.purple"

    cygpath = CygwinPath(path)

    print cygpath.get_cygwin_path()
    print cygpath.get_windows_path()








if __name__ == '__main__':
    main()

















