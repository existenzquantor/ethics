from setuptools import setup
from setuptools.command.install import install
from distutils.core import Extension
import tarfile
import requests
import subprocess
import os

try:
    from Cython.Build import cythonize
    import Cython.Compiler.Options

    # This will tell Cython to generate annotated html files for every pyx file
    Cython.Compiler.Options.annotate = False
    CYTHON_AVAILABLE = True
except:
    print("Cython not found: Installing without Cython")
    CYTHON_AVAILABLE = False

# If set to False, it will use c files instead of pyx files.
# IMPORTANT: The c files have to already exist before this works!
USE_CYTHON = False

# Setup the file extensions
SOURCE_EXTENSION = ".pyx" if CYTHON_AVAILABLE and USE_CYTHON else ".c"

# Path to this file's directory
CURR_DIR = os.path.dirname(os.path.realpath(__file__))

# The path to the directory containing the extension files (.pyx and .c)
EXT_FILES_PATH = os.path.join(CURR_DIR, "ethics", "extensions")

# ====== CUDD ======
# URL to a CUDD mirror on github
CUDD_URL = "https://sourceforge.net/projects/cudd-mirror/files/cudd-3.0.0.tar.gz/download"

# Path to the directory that will contain the cudd C library
CUDD_DIR = os.path.join(CURR_DIR, "cudd-3.0.0/")

# The include directories needed to use CUDD
CUDD_INCLUDE = [os.path.join(CUDD_DIR, dir_name) for dir_name in
                ['.', 'cudd', 'epd', 'mtr', 'st', 'util']]

# The name of the CUDD library
CUDD_LIB = ["cudd"]

# The links needed to use CUDD
CUDD_LINKS = [os.path.join(CUDD_DIR, dir_name) for dir_name in ['cudd/.libs']]

# Some extra compile arguments
# These are taken from https://github.com/tulip-control/dd/blob/master/download.py
CUDD_COMPILE_ARGUMENTS = ['-fPIC', '-std=c99', '-DBSD', '-DHAVE_IEEE_754', '-mtune=native',
                          '-pthread', '-fwrapv', '-fno-strict-aliasing', '-Wall', '-W', '-O3']
# ====== ======


class InstallWrapper(install):
    def run(self):
        # Before running install, setup CUDD.
        self._setup_cudd()
        install.run(self)

    def _setup_cudd(self):
        self._download_cudd()
        self._configure_cudd()
        self._make_cudd()

    def _download_cudd(self):
        """Download CUDD and extract into the specified directory."""

        print("Downloading CUDD ... ", end='')

        # Don't download again if not necessary
        if os.path.isdir(CUDD_DIR):
            print("Already Downloaded -> Done")
            return

        cudd_zip_path = os.path.join(CURR_DIR, "cudd.zip")
        response = requests.get(CUDD_URL)

        with open(cudd_zip_path, "wb") as file:
            file.write(response.content)

        # Unzip Cudd
        with tarfile.open(cudd_zip_path) as tar_file:
            def is_within_directory(directory, target):
                
                abs_directory = os.path.abspath(directory)
                abs_target = os.path.abspath(target)
            
                prefix = os.path.commonprefix([abs_directory, abs_target])
                
                return prefix == abs_directory
            
            def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
            
                for member in tar.getmembers():
                    member_path = os.path.join(path, member.name)
                    if not is_within_directory(path, member_path):
                        raise Exception("Attempted Path Traversal in Tar File")
            
                tar.extractall(path, members, numeric_owner) 
                
            
            safe_extract(tar_file)

        os.remove(cudd_zip_path)

        print("Done")

    def _configure_cudd(self):
        """Run ./configure and reset the permissions so that make`will` work."""
        print("Configuring CUDD ... ", end='')

        # Without fPIC, the compiler will complain when building the cython extensions
        subprocess.run(['./configure', 'CFLAGS=-fPIC -std=c99'], cwd=CUDD_DIR)

        # Now give the created makefile execute permissions
        print("Done")

    def _make_cudd(self):
        """Compile CUDD."""
        print("Making CUDD ... ", end='')
        subprocess.run(['make', '-j4'], cwd=CUDD_DIR)
        print("Done")


MHS_EXTENSION = Extension(name="ethics.extensions.mhs",
                          sources=[os.path.join(
                              EXT_FILES_PATH, 'mhs' + SOURCE_EXTENSION)],
                          libraries=CUDD_LIB,
                          include_dirs=CUDD_INCLUDE,
                          library_dirs=CUDD_LINKS,
                          extra_compile_args=CUDD_COMPILE_ARGUMENTS,
                          )

PARSER_EXTENSION = Extension(name="ethics.extensions.parser",
                             sources=[os.path.join(
                                 EXT_FILES_PATH, 'parser' + SOURCE_EXTENSION)],
                             libraries=CUDD_LIB,
                             include_dirs=CUDD_INCLUDE,
                             library_dirs=CUDD_LINKS,
                             extra_compile_args=CUDD_COMPILE_ARGUMENTS,
                             )

SAT_EXTENSION = Extension(name="ethics.extensions.sat",
                          sources=[os.path.join(
                              EXT_FILES_PATH, 'sat' + SOURCE_EXTENSION)],
                          libraries=CUDD_LIB,
                          include_dirs=CUDD_INCLUDE,
                          library_dirs=CUDD_LINKS,
                          extra_compile_args=CUDD_COMPILE_ARGUMENTS,
                          )

OLD_MHS_EXTENSION = Extension(name='ethics.extensions.mhsModule',
                              sources=['ethics/extensions/mhsModule.cpp'],
                              extra_compile_args=['-std=c++11'],
                              extra_link_args=['-std=c++11']
                              )

# SETUP
EXTENSIONS = [MHS_EXTENSION, PARSER_EXTENSION,
              OLD_MHS_EXTENSION, SAT_EXTENSION]
EXT_MODULES = cythonize(
    EXTENSIONS) if CYTHON_AVAILABLE and USE_CYTHON else EXTENSIONS

setup(name='ethics',
      version='0.22.3',
      description=("A python toolbox for ethical reasoning."),
      author='Felix Lindner',
      author_email='info@hera-project.com',
      url='http://www.hera-project.com',
      py_modules=['ethics.plans.semantics', 'ethics.plans.principles', 'ethics.plans.concepts', 'ethics.plans.planner',
                  'ethics.language', 'ethics.cam.semantics', 'ethics.cam.principles', 'ethics.tools', 'ethics.verbalizer',
                  'ethics.explanations', 'ethics.solver', 'ethics.primes'],
      packages=['ethics.extensions'],
      zip_safe=False,  # Cython documentation recommends this when using cythonize()
      install_requires=['PyYAML', 'pyeda'],
      cmdclass={'install': InstallWrapper},  # Custom pre-install steps
      ext_modules=EXT_MODULES
      )
