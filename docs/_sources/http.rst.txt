**************
HTTP Utilities
**************

In this module, you'll find a variety of useful functions for working with web data. \
The `canonical_link` function is our best attempt at standardizing and cleaning a URL without \
losing any information, and the `strip_html` function is useful for attempting to extract text \
from raw HTML data with minimal fine-tuning.

.. automodule :: pewtils.http
    :autosummary:
    :members:

+++++++++++++++
Link Shorteners
+++++++++++++++

List of link shorteners recognized by methods in this section.

General Link Shorteners
^^^^^^^^^^^^^^^^^^^^^^^

    A list of known :ref:`gen_link_shorteners`.

Vanity Link Shorteners
^^^^^^^^^^^^^^^^^^^^^^^

    A list of known URL shorteners for websites specific :ref:`vanity_link_shorteners` (primarily news websites).
