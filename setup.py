from setuptools import setup
setup(name='ethics',
      version='0.18.8',
      description = ("A python toolbox for ethical reasoning."),
      author='Felix Lindner',
      author_email='info@hera-project.com',
      url='http://www.hera-project.com',
      py_modules=['ethics.plan_semantics', 'ethics.plan_principles' , 'ethics.language', 'ethics.cam_semantics', 'ethics.cam_principles', 'ethics.tools', 'ethics.verbalizer', 'ethics.explanations', 'ethics.solver', 'ethics.primes', 'ethics.argumentation'],
      install_requires=['PyYAML', 'BinPy', 'pyeda']
      )
