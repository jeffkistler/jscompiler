JavaScript Compiler
===================

This is an experimental JavaScript-to-JavaScript compiler project. Mostly for
minification experimentation purposes.


Usage
-----

Invoke the compiler with the command ``jscompiler``. Compile a JavaScript source
file ``myscript.js`` like so::

    jscompiler myscript.js

For more options try this::

    jscompiler --help


Installation
------------

Installation from Source
~~~~~~~~~~~~~~~~~~~~~~~~

Unpack the archive, ``cd`` into the unpacked source directory and run the
following command::

    python setup.py install

Installation from Source with pip
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Skip a step by using pip to download and install the package source for the
latest version::

   pip install https://github.com/jeffkistler/jscompiler/zipball/master#egg=jscompiler

Installation with pip and git
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Run the following command::

    pip install -e git+git://github.com/jeffkister/jscompiler.git#egg=jscompiler

