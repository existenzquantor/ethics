from distutils.core import Extension
from setuptools import setup
setup(name='ethics',
      version='0.22.3',
      description = ("A python toolbox for ethical reasoning."),
      author='Felix Lindner',
      author_email='info@hera-project.com',
      url='http://www.hera-project.com',
      py_modules=['ethics.plans.semantics', 'ethics.plans.principles' , 'ethics.plans.concepts', 'ethics.plans.planner',
                        'ethics.language', 'ethics.cam.semantics', 'ethics.cam.principles', 'ethics.tools', 'ethics.verbalizer',
                        'ethics.explanations', 'ethics.solver'],
      install_requires=['PyYAML', 'pyeda'],
      ext_modules = [Extension(
            'mhsModule',
            ['extensions/mhsModule.cpp'],
            extra_compile_args=['-std=c++11'],
            extra_link_args=['-std=c++11']
        )]
      )
