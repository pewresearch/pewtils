Welcome to pewtils's documentation!
===================================

First steps
-----------

Pewtils is a package of useful logging and management functions developed \
at the Pew Research Center over the years.

To install ::

    pip install https://github.com/pewresearch/pewtils#egg=pewtils

Or install from source ::

    git clone https://github.com/pewresearch/pewtils.git
    cd pewtils
    python setup.py install


.. note::
    This is a Python3 package. Though it's compatible with Python 2, its dependencies are \
    planning to drop support for earlier versions. We highly recommend you upgrade to Python3.


Tests ::

    pytest


Full Documentation
------------------

This contains everything you need to know about every function in the source code.


.. automodule :: pewtils.__init__
    :members:


File Handlers
------------

.. automodule :: pewtils.io
    :members:


AWS Handlers
------------

.. automodule :: pewtils.aws
    :members:


.. toctree::
   :maxdepth: 2
   :caption: Contents:

   How To Use <how_to_use>
   HTTP Utilities <http>


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
