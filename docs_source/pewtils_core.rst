**************
Core Functions
**************

The main Pewtils module contains a variety of generally useful functions that make our researchers \
lives easier. For those still working in Python 2.x, the ``decode_text`` function can help alleviate \
headaches related to text encodings. The ``is_null`` and ``is_not_null`` functions provide an easy way \
to deal with the wide variety of possible null values that exist in the Python (and broader research \
universe) by using a best-guess approach. When working with dictionaries or JSON records that need \
to be updated, ``recursive_update`` makes it easy to map one version of an object onto another. While \
we strive to write efficient code that can cover every possible use-case, there are certainly some \
edge cases that we haven't encountered, and other existing Python libraries may very well provide \
many of these same features. This collection simply consists of functions we find ourselves using \
again and again, and we hope that Pewtils may help expand your daily toolkit in some way as well.

.. automodule :: pewtils.__init__
    :autosummary:
    :members:
