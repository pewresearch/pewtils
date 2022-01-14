Getting Started
===================================

Welcome to pewtils’s documentation!

About
---------------

Pewtils is a package of useful logging and management functions developed \
at the Pew Research Center over the years.


Installation
---------------

To install ::

    pip install https://github.com/pewresearch/pewtils#egg=pewtils

Or install from source ::

    git clone https://github.com/pewresearch/pewtils.git
    cd pewtils
    python setup.py install


.. note::
    This is a Python3 package. Though it's compatible with Python 2, its dependencies are \
    planning to drop support for earlier versions. We highly recommend you upgrade to Python3.


Example
---------------

(Use Cases)


PewTils
-----------------------

Core Functions
++++++++++++++++++++++++

.. automodule :: pewtils.__init__
    :noindex:
    :autosummary:
    :autosummary-members:


Http Utilities
++++++++++++++++++++++++

.. automodule :: pewtils.http
    :noindex:
    :autosummary:
    :autosummary-members:


File Handler
++++++++++++++++++++++++

.. automodule :: pewtils.io
    :autosummary:
    :autosummary-members:


Table of Contents
------------------
.. toctree::
   :maxdepth: 2

   Getting Started <index>
   pewtils Core <pewtils_core>
   HTTP Utilities <http>
   File Handles <file_handler>


Indices and Tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
