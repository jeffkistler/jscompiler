import os
import jscompiler as the_module
try:
    from setuptools import setup
    extra = {
        'install_requires': [
            'BigRig',
        ],
        'dependency_links': [
            'https://github.com/jeffkistler/BigRig/zipball/0c656c9e0f8d766da5f3122911ae04b02c70f483#egg=BigRig',
        ]
    }
except ImportError:
    try:
        import BigRig
    except ImportError:
        import warnings
        warnings.warn(
            '%s requires BigRig.' % the_module.__title__
        )
    from distutils.core import setup
    extra = {}

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = the_module.__title__,
    version = the_module.__version__,
    license = the_module.__license__,
    description = 'An experimental JavaScript-to-JavaScript compiler.',
    long_description = read('README.rst'),
    author = 'Jeff Kistler',
    author_email = 'jeff@jeffkistler.com',
    packages = ['jscompiler'],
    classifiers = [
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
    ],
    scripts = ['bin/jscompiler'],
    **extra
)
