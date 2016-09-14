#!/usr/bin/env python3

from setuptools import setup

setup(name='PyTMCL',
      version='1.0',
      description='Python TMCL interface',
      author='Leonardo Romor',
      author_email='leonardo.romor@gmail.com',
      url='https://github.com/Atrasoftware/PyTMCL',
      packages=['PyTMCL', 'PyTMCL.XY', 'PyTMCL.TMCL'],
      install_requires=['pyserial'],
      )
