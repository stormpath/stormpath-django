#!/usr/bin/env python

from setuptools import setup, find_packages, Command
import os
import sys


class BaseCommand(Command):
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass


class TestCommand(BaseCommand):

    description = "run self-tests"

    def run(self):
        os.chdir('testproject')
        ret = os.system('make test')
        if ret != 0:
            sys.exit(-1)

setup(
    name='django_stormpath',
    version='0.0.2',
    author='',
    author_email='goran.cetusic@dobarkod.hr',
    description='Django Stormpath API integration',
    license='MIT',
    url='http://goodcode.io/',
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Web Environment",
        "Framework :: Django",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    packages=find_packages(),
    install_requires=[
        "stormpath-sdk>=1.0.0",
        "django"
    ],
    cmdclass={
        'test': TestCommand
    },
)
