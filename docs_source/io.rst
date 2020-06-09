**************
I/O Tools
**************

This module contains utilities related to reading and writing files in a variety of formats. \
Right now, it consists exclusively of the :py:class:`pewtils.io.FileHandler` class, which provides \
a standardized interface for loading and saving data both locally and on Amazon S3. It doesn't \
always work exactly as intended, but 99% of the time, it gives us a way to read and write files \
with just one or two lines of code - and accordingly, we use it everywhere. We hope you do too!

.. automodule :: pewtils.io
    :autosummary:
    :members:
