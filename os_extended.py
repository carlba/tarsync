import os
import ctypes
import platform


def IsSymlink(path):
      FILE_ATTRIBUTE_REPARSE_POINT = 0x0400
      if path.isdir(path) and \
        (ctypes.windll.kernel32.GetFileAttributesW(unicode(path)) & FILE_ATTRIBUTE_REPARSE_POINT):
        return True
      else:
        return False

def unlink(path):
    return ctypes.windll.kernel32.UnlockFile(unicode(path))

def symlink(src,dst):
    if os.path.isdir(src):
        ctypes.windll.kernel32.CreateSymbolicLinkW(unicode(dst), unicode(src), 1)
    else:
        ctypes.windll.kernel32.CreateSymbolicLinkW(unicode(dst), unicode(src), 0)


if "windows" in platform.system().lower():
    os.path.islink = IsSymlink
    os.unlink = unlink
    os.symlink = symlink

