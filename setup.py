from setuptools import setup
setup(name='ethics',
      version='0.19.6',
      description = ("A python toolbox for ethical reasoning."),
      author='Felix Lindner',
      author_email='info@hera-project.com',
      url='http://www.hera-project.com',
      py_modules=['ethics.plans.semantics', 'ethics.plans.principles' , 'ethics.language', 'ethics.cam.semantics', 'ethics.cam.principles', 'ethics.tools', 'ethics.verbalizer', 'ethics.explanations', 'ethics.solver'],
      install_requires=['PyYAML', 'pyeda']
      )
