from os import chdir, environ, system
from subprocess import call
from sys import exit

from setuptools import setup, find_packages, Command

from django_stormpath import __version__


class BaseCommand(Command):
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass


class TestCommand(BaseCommand):

    description = 'run self-tests'

    def run(self):
        chdir('testproject')
        ret = system('coverage run --source=django_stormpath manage.py test --settings=testproject.settings testapp && coverage html')

        if ret != 0:
            exit(-1)
        else:
            exit(0)


class TestDepCommand(BaseCommand):

    description = 'install test dependencies'

    def run(self):
        cmd = ['pip', 'install', 'coverage']
        ret = call(cmd)
        exit(ret)


class DocCommand(BaseCommand):

    description = 'generate documentation'

    def run(self):
        environ['DJANGO_SETTINGS_MODULE'] = 'testproject.settings'
        try:
            chdir('docs')
            ret = system('make html')
            exit(ret)
        except OSError as e:
            print(e)
            exit(-1)


setup(
    name = 'django-stormpath',
    version = __version__,
    author = 'Stormpath, Inc.',
    author_email = 'python@stormpath.com',
    description = 'Stormpath integration for Django.',
    license = 'Apache',
    url = 'https://github.com/stormpath/stormpath-django',
    zip_safe = False,
    classifiers = [
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    packages = find_packages(),
    install_requires = [
        'requests-oauthlib>=0.4.2',
        'stormpath>=1.2.7',
        'Django>=1.6',
    ],
    cmdclass = {
        'test': TestCommand,
        'testdep': TestDepCommand,
        'docs': DocCommand,
    },
)
