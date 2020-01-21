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


pewtils Core Functions
-----------------------

Here are the list of information on pewtils core functions. 

.. automodule :: pewtils.__init__
    :autosummary:
    :members:


pewtils Documentation 
---------------------
.. toctree::
   :maxdepth: 2
   :caption: Contents:

   HTTP Utilities <http>
   File Handles <file_handler>


Indices and Tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`