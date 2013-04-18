#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name='django_stormpath',
    version='0.0.1',
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
        "stormpath-sdk>=0.2.0",
    ],
)
