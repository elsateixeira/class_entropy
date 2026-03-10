from setuptools import setup
from setuptools import Extension
from Cython.Distutils import build_ext

import numpy as nm
import os
import re
import subprocess as sbp
import os.path as osp
import platform
import sysconfig

os.environ.setdefault("CC",  "/opt/homebrew/bin/gcc-11")
os.environ.setdefault("CXX", "/opt/homebrew/bin/g++-11")

# ---------- work around Apple-specific flags when using Homebrew GCC ----------
# Python/conda sysconfig embeds Clang flags like "-arch arm64" that GCC does
# not understand, producing empty object files.  Strip them when the compiler
# is GCC (not Apple Clang).
_cc = os.environ.get("CC", "gcc-11")
if "gcc" in os.path.basename(_cc) and "clang" not in os.path.basename(_cc):
    _arch_re = re.compile(r"\s*-arch\s+\S+")
    _cfg = sysconfig.get_config_vars()
    for _key in list(_cfg.keys()):
        if isinstance(_cfg[_key], str) and "-arch" in _cfg[_key]:
            _cfg[_key] = _arch_re.sub("", _cfg[_key])

# Align MACOSX_DEPLOYMENT_TARGET with the running system so the linker does
# not complain about objects built for a newer macOS.
os.environ["MACOSX_DEPLOYMENT_TARGET"] = platform.mac_ver()[0]

# Recover the gcc compiler
GCCPATH_STRING = sbp.Popen(
    ['gcc-11', '-print-libgcc-file-name'],
    stdout=sbp.PIPE).communicate()[0]
GCCPATH = osp.normpath(osp.dirname(GCCPATH_STRING)).decode()

liblist = ["class"]
MVEC_STRING = sbp.Popen(
    ['gcc-11', '-lmvec'],
    stderr=sbp.PIPE).communicate()[1]
if b"mvec" not in MVEC_STRING:
    liblist += ["mvec","m"]

# define absolute paths
root_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
include_folder = os.path.join(root_folder, "include")
classy_folder = os.path.join(root_folder, "python")
heat_folder = os.path.join(os.path.join(root_folder, "external"),"heating")
recfast_folder = os.path.join(os.path.join(root_folder, "external"),"RecfastCLASS")
hyrec_folder = os.path.join(os.path.join(root_folder, "external"),"HyRec2020")
hmcode_folder = os.path.join(os.path.join(root_folder, "external"),"HMcode")
halofit_folder = os.path.join(os.path.join(root_folder, "external"),"Halofit")

# Recover the CLASS version
with open(os.path.join(include_folder, 'common.h'), 'r') as v_file:
    for line in v_file:
        if line.find("_VERSION_") != -1:
            # get rid of the " and the v
            VERSION = line.split()[-1][2:-1]
            break

# Define cython extension and fix Python version
classy_ext = Extension("classy", [os.path.join(classy_folder, "classy.pyx")],
                           include_dirs=[nm.get_include(), include_folder, heat_folder, recfast_folder, hyrec_folder, hmcode_folder, halofit_folder],
                           libraries=liblist,
                           library_dirs=[root_folder, GCCPATH],
                           #extra_link_args=['-lgomp'],
                           language="c++",
                           extra_compile_args=["-std=c++11"]
                       )
import sys
classy_ext.cython_directives = {'language_level': "3" if sys.version_info.major>=3 else "2"}

setup(
    name='classy',
    version=VERSION,
    description='Python interface to the Cosmological Boltzmann code CLASS',
    url='http://www.class-code.net',
    cmdclass={'build_ext': build_ext},
    ext_modules=[classy_ext],
)
