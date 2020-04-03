**************
Examples
**************

Check for null values
-----------------------------------------------------

You can use the :py:func:`pewtils.is_null` and :py:func:`pewtils.is_not_null` to quickly check for a \
variety of common null values.

.. code-block:: python

    from pewtils import is_null
    from pewtils import is_not_null
    import numpy as np

    >>> is_null(None)
    True
    >>> is_null("None")
    True
    >>> is_null("nan")
    True
    >>> is_null("")
    True
    >>> is_null(" ")
    True
    >>> is_null("NaN")
    True
    >>> is_null("none")
    True
    >>> is_null("NONE")
    True
    >>> is_null("n/a")
    True
    >>> is_null("N/A")
    True
    >>> is_null(np.nan)
    True
    >>> is_null("-9", custom_nulls=["-9"])
    True
    >>> is_null("Hello World")
    False
    >>> is_null(0.0)
    False

Collapse documents into context-sensitive hashes
-----------------------------------------------------

When working with large documents, you can use the :py:func:`pewtils.get_hash` function to convert \
them into a variety of different hashed representations. By default, this function uses SSDEEP, which \
produced context-sensitive hashes that can be useful for searching for similar documents.

.. code-block:: python

    from pewtils import get_hash

    >>> doc1 = "This is a document."
    >>> doc2 = "This is a document. But this one is longer."
    >>> get_hash(doc1)
    '3:hMCE+RL:hu+t'
    >>> get_hash(doc2)
    '3:hMCE+RGreCQHCAb:hu+0rLkb'
    # Notice that both hashes start the same way, corresponding to their overlapping text.

Flatten nested lists
-----------------------------------------------------

Easily flatten lists of lists:

.. code-block:: python

    from pewtils import flatten_list

    >>> nested_lists = [[1, 2, 3], [4, 5, 6]]
    >>> flatten_list(nested_lists)
    [1, 2, 3, 4, 5, 6]

Recursively update dictionaries and object attributes
-----------------------------------------------------

Map a dictionary or object onto another version of itself to update overlapping attributes:

.. code-block:: python

    from pewtils import recursive_update

    class TestObject(object):
        def __init__(self, value):
            self.value = value
            self.dict = {"obj_key": "original"}
        def __repr__(self):
            return("TestObject(value='{}', dict={})".format(self.value, self.dict))

    original = {
        "object": TestObject("original"),
        "key1": {"key2": "original"}
    }
    update = {
        "object": {"value": "updated", "dict": {"obj_key": "updated"}},
        "key1": {"key3": "new"}
    }

    >>> recursive_update(original, update)
    {'object': TestObject(value='updated', dict={'obj_key': 'updated'}),
     'key1': {'key2': 'original', 'key3': 'new'}}


Efficiently map a function onto a Pandas Series
-----------------------------------------------------

Avoid repeating database lookups or expensive computations when applying a function to a Pandas \
Series by using the :py:func:`pewtils.cached_series_mapper` function, which caches the results \
for each value in the series as it iterates.

.. code-block:: python

    import pandas as pd
    from pewtils import cached_series_mapper

    values = ["value"]*10
    def my_function(x):
        print(x)
        return x

    df = pd.DataFrame(values, columns=['column'])
    >>> mapped = df['column'].map(my_function)
    value
    value
    value
    value
    value
    value
    value
    value
    value
    value
    >>> mapped = cached_series_mapper(df['column'], my_function)
    value

Read and write data in a variety of formats
-----------------------------------------------------

The :py:class:`pewtils.io.FileHandler` class lets you easily read and write files in a variety of \
formats with minimal code, and it has support for Amazon S3 too:

.. code-block: python

    from pewtils.io import FileHandler

    >>> h = FileHandler("./", use_s3=False)  # current local folder
    >>> df = h.read("my_csv", format="csv")
    # Do something and save to Excel
    >>> h.write("my_new_csv", df, format="xlsx")

    >>> my_data = [{"key": "value"}]
    >>> h.write("my_data", my_data, format="json")

    >>> my_data = ["a", "python", "list"]
    >>> h.write("my_data", my_data, format="pkl")


Quickly extract text from raw HTML
-----------------------------------------------------

It's not always perfect, but the :py:func:`pewtils.http.strip_html` function can often be used to \
extract most of the valuable text data from a raw HTML documents - useful for quick exploratory \
analysis after scraping a bunch of webpages.

.. code-block:: python

    from pewtils.http import strip_html

    >>> my_html = "<html><head>Header text</head><body>Body text</body></html>"
    >>> strip_html(my_html)
    'Header text\n\nBody text'

Standardize URLs and extract domains
-----------------------------------------------------

The :py:func:`pewtils.http.canonical_link` function is our best attempt at resolving URLs to their \
true form: it follows shortened URLs, removes unnecessary GET parameters, and tries to avoid returning \
incorrect 404 pages in favor of the most informative last-known version of a URL. Once links have been \
standardized, you can also use the :py:func:`pewtils.http.extract_domain_from_url` function to pull \
out domains and subdomains.

.. code-block:: python

    from pewtils.http import canonical_link

    >>> canonical_link("https://pewrsr.ch/2lxB0EX?unnecessary_param=1")
    "https://www.pewresearch.org/interactives/how-does-a-computer-see-gender/"

    from pewtils.http import extract_domain_from_url

    >>> extract_domain_from_url("http://forums.bbc.co.uk", include_subdomain=False)
    "bbc.co.uk"
    >>> extract_domain_from_url("http://forums.bbc.co.uk", include_subdomain=True)
    "forums.bbc.co.uk"
