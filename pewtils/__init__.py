from __future__ import absolute_import
import chardet
import copy
import json
import multiprocessing
import os
import re
import signal
import sys
import time
import warnings
import zipcodes

try:
    from importlib.machinery import SourceFileLoader
except ImportError:
    import imp

import pandas as pd
import numpy as np

from contextlib import closing
from hashlib import md5
from random import uniform
from scandir import walk
from unidecode import unidecode


class classproperty(object):

    """
    This decorator allows you to define functions on a class that are accessible directly from the
    class itself (rather than an instance of the class). It allows you to access ``classproperty``
    attributes directly, such as ``obj.property``, rather than as a function on a class instance
    (like ``obj = Obj(); obj.property()``).

    Borrowed from a StackOverflow `post <https://stackoverflow.com/a/3203659>`_.

    Usage::

        from pewtils import classproperty

        class MyClass(object):
            x = 4

            @classproperty
            def number(cls):
                return cls.x

        >>> MyClass().number
        4
        >>> MyClass.number
        4
    """

    def __init__(self, fget):
        self.fget = fget

    def __get__(self, owner_self, owner_cls):
        return self.fget(owner_cls)


def is_not_null(val, empty_lists_are_null=False, custom_nulls=None):

    """
    Checks whether the value is null, using a variety of potential string values, etc. The following values are always
    considered null: ``numpy.nan, None, "None", "nan", "", " ", "NaN", "none", "n/a", "NONE", "N/A"``

    :param val: The value to check
    :param empty_lists_are_null: Whether or not an empty list or :py:class:`pandas.DataFrame` should be considered \
    null (default=False)
    :type empty_lists_are_null: bool
    :param custom_nulls: an optional list of additional values to consider as null
    :type custom_nulls: list
    :return: True if the value is not null
    :rtype: bool

    Usage::

        from pewtils import is_not_null

        >>> text = "Hello"
        >>> is_not_null(text)
        True
    """

    null_values = [None, "None", "nan", "", " ", "NaN", "none", "n/a", "NONE", "N/A"]
    if custom_nulls:
        null_values.extend(custom_nulls)
    if type(val) == list:
        if empty_lists_are_null and val == []:
            return False
        else:
            return True
    elif isinstance(val, pd.Series) or isinstance(val, pd.DataFrame):
        if empty_lists_are_null and len(val) == 0:
            return False
        else:
            return True
    else:
        try:
            try:
                good = val not in null_values
                if good:
                    try:
                        try:
                            good = not pd.isnull(val)
                        except IndexError:
                            good = True
                    except AttributeError:
                        good = True
                return good
            except ValueError:
                return val.any()
        except TypeError:
            return not isinstance(val, None)


def is_null(val, empty_lists_are_null=False, custom_nulls=None):

    """
    Returns the opposite of the outcome of :py:func:`pewtils.is_not_null`. The following values are always \
    considered null: ``numpy.nan, None, "None", "nan", "", " ", "NaN", "none", "n/a", "NONE", "N/A"``

    :param val: The value to check
    :param empty_lists_are_null: Whether or not an empty list or :py:class:`pandas.DataFrame` should be considered \
    null (default=False)
    :type empty_lists_are_null: bool
    :param custom_nulls: an optional list of additional values to consider as null
    :type custom_nulls: list
    :return: True if the value is null
    :rtype: bool

    Usage::

        from pewtils import is_null

        >>> empty_list = []
        >>> is_null(empty_list, empty_lists_are_null=True)
        True
    """

    return not is_not_null(
        val, empty_lists_are_null=empty_lists_are_null, custom_nulls=custom_nulls
    )


def decode_text(text, throw_loud_fail=False):

    """
    Attempts to decode and re-encode text as ASCII. In the case of failure, it will attempt to detect the string's \
    encoding, decode it, and convert it to ASCII. If both these attempts fail, it will attempt to use the \
    :py:mod:`unidecode` package to transliterate into ASCII. And finally, if that doesn't work, it will forcibly \
    encode the text as ASCII and ignore non-ASCII characters.

    .. warning:: This function is potentially destructive to source input and should be used with some care. \
        Input text that cannot be decoded may be stripped out, or replaced with a similar ASCII character or other \
        placeholder, potentially resulting in an empty string.

    :param text: The text to process
    :type text: str
    :param throw_loud_fail: If True, exceptions will be raised, otherwise the function will fail silently and \
    return an empty string (default False)
    :type throw_loud_fail: bool
    :return: Decoded text, or empty string
    :rtype: str

    .. note:: In Python 3, the decode/encode attempts will fail by default, and the :py:mod:`unidecode` package will \
        be used to transliterate. In general, you shouldn't need to use this function in Python 3, but it shouldn't \
        hurt anything if you do.

    """

    output_text = ""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        if is_not_null(text):
            try:
                text = u"{}".format(text)
                output_text = text.decode("ascii").encode("ascii")
            except (AttributeError, TypeError, UnicodeEncodeError, UnicodeDecodeError):
                try:
                    output_text = text.decode(chardet.detect(text)["encoding"])
                    output_text = output_text.encode("ascii")
                except (
                    AttributeError,
                    TypeError,
                    UnicodeEncodeError,
                    UnicodeDecodeError,
                ):
                    try:
                        output_text = unidecode(text)
                    except (
                        AttributeError,
                        TypeError,
                        UnicodeEncodeError,
                        UnicodeDecodeError,
                    ):
                        if throw_loud_fail:
                            output_text = text.decode("ascii", "ignore").encode("ascii")
                        else:
                            try:
                                output_text = text.decode("ascii", "ignore").encode(
                                    "ascii"
                                )
                            except (
                                AttributeError,
                                TypeError,
                                UnicodeEncodeError,
                                UnicodeDecodeError,
                            ):
                                print("Could not decode")
                                print(text)
                output_text = output_text.replace("\x00", "").replace("\u0000", "")

    return output_text


def get_hash(text, hash_function="ssdeep"):

    """
    Generates hashed text using one of several available hashing functions.

    :param text: The string to hash
    :type text: str
    :param hash_function: The specific algorithm to use; options are ``'nilsimsa'``, ``'md5'``, and ``'ssdeep'`` \
    (default)
    :type hash_function: str
    :return: A hashed representation of the provided string
    :rtype: str

    .. note:: The string will be passed through :py:func:`pewtils.decode_text` and the returned value will be used \
    instead of the original value if it runs successfully, in order to ensure consistent hashing in both Python 2 and \
    3. By default the function uses the :py:mod:`ssdeep` algorithm, which generates context-sensitive hashes that are \
    useful for computing document similarities at scale.

    .. note:: Using `hash_function='ssdeep'` requires the :py:mod:`ssdeep` library, which is not installed by default \
    because it requires the installation of additional system libraries on certain operating systems. For help \
    installing ssdeep, refer to the pewtils documentation installation section, which provides OS-specific instructions.

    Usage::

        from pewtils import get_hash

        >>> text = 'test_string'
        >>> get_hash(text)
        '3:HI2:Hl'
    """

    decoded_text = decode_text(text).encode("utf8").strip()
    if decoded_text == "":
        decoded_text = text
    text = decoded_text
    if hash_function == "nilsimsa":
        from nilsimsa import Nilsimsa

        hashed = Nilsimsa(text).hexdigest()
    elif hash_function == "md5":
        hashed = md5(text).hexdigest()
    else:
        try:
            import ssdeep
        except ImportError:
            raise Exception(
                """
                To use get_hash with hash_function='ssdeep' you need to install the ssdeep package. Try running: 
                    >> BUILD_LIB=1 pip install ssdeep
                If you encounter installation problems, refer to the pewtils documentation for troubleshooting help.
            """
            )
        hashed = ssdeep.hash(text)

    return hashed


def zipcode_num_to_string(zipcode):

    """
    Attempts to standardize a string/integer/float that contains a U.S. zipcode. Front-pads with zeroes and uses the \
    :py:mod:`zipcodes` library to ensure that the zipcode is real. If the zipcode doesn't validate successfully, \
    ``None`` will be returned.

    :param zip: Object that contains a sequence of digits (string, integer, float)
    :type zip: str or float or int
    :return: A 5-digit string, or None
    :rtype: str or NoneType

    Usage::

        from pewtils import zipcode_num_to_string

        >>> zipcode_number = 6463
        >>> zipcode_num_to_string(zipcode_number)
        '06463'
        >>> not_zipcode_number = 345678
        >>> zipcode_num_to_string(not_zipcode_number)
        >>>
    """

    if is_not_null(zipcode):

        try:
            zipcode = str(int(str(zipcode).strip()[:5].split(".")[0]))
        except (TypeError, ValueError):
            zipcode = None

        if zipcode:
            zipcode = zipcode.zfill(5)
            if zipcodes.is_real(zipcode):
                return zipcode
            else:
                return None
    else:

        zipcode = None

    return zipcode


def concat_text(*args):

    """
    A helper function for concatenating text values. Text values are passed through :py:func:`pewtils.decode_text` \
    before concatenation.

    :param args: A list of text values that will be returned as a single space-separated string
    :type args: list
    :return: A single string of the values concatenated by spaces
    :rtype: str

    Usage::

        from pewtils import concat_text

        >>> text_list = ['Hello', 'World', '!']
        >>> concat_text(text_list)
        'Hello World !'
    """

    strs = [decode_text(arg) for arg in args if is_not_null(arg)]
    return " ".join(strs) if is_not_null(strs, empty_lists_are_null=True) else ""


def vector_concat_text(*args):

    """
    Takes a list of equal-length lists and returns a single list with the rows concatenated by spaces. Useful for \
    merging multiple columns of text in Pandas.

    :param args: A list of lists or :py:class:`pandas.Series` s that contain text values
    :return: A single list or :py:class:`pandas.Series` with all of the text values for each row concatenated

    Usage with lists::

        from pewtils import vector_concat_text

        >>> text_lists = ["one", "two", "three"], ["a", "b", "c"]
        >>> vector_concat_text(text_lists)
        ['one a', 'two b', 'three c']

    Usage with Pandas::

        import pandas as pd
        from pewtils import vector_concat_text

        df = pd.DataFrame([
            {"text1": "one", "text2": "a"},
            {"text1": "two", "text2": "b"},
            {"text1": "three", "text2": "c"}
        ])

        >>> df['text'] = vector_concat_text(df['text1'], df['text2'])
        >>> df['text']
        0      one a
        1      two b
        2    three c
        Name: text, dtype: object
    """

    return np.vectorize(concat_text)(*args)


def scale_range(old_val, old_min, old_max, new_min, new_max):

    """
    Scales a value from one range to another.  Useful for comparing values from different scales, for example.

    :param old_val: The value to convert
    :type old_val: int or float
    :param old_min: The minimum of the old range
    :type old_min: int or float
    :param old_max: The maximum of the old range
    :type old_max: int or float
    :param new_min: The minimum of the new range
    :type new_min: int or float
    :param new_max: The maximum of the new range
    :type new_max: int or float
    :return: Value equivalent from the new scale
    :rtype: float

    Usage::

        from pewtils import scale_range

        >>> old_value = 5
        >>> scale_range(old_value, 0, 10, 0, 20)
        10.0
    """

    return (
        ((float(old_val) - float(old_min)) * (float(new_max) - float(new_min)))
        / (float(old_max) - float(old_min))
    ) + float(new_min)


def new_random_number(attempt=1, minimum=1.0, maximum=10):

    """
    Returns a random number between the boundary that exponentially increases with the number of ``attempt``.
    The upper bound is capped using the ``maximum`` parameter (default 10) but is otherwise determined by the
    function ``minimum * 2 ** attempt``.

    | In effect, this means that when ``attempt`` is 1, the number returned will be in the range of the minimum \
    and twice the minimum's value.  As you increase ``attempt``, the possible range of returned values expands \
    exponentially until it hits the ``maximum`` ceiling.

    :param attempt: Increasing attempt will expand the upper-bound of the range from which the random number is drawn
    :type attempt: int
    :param minimum: The minimum allowed value that can be returned; must be greater than zero.
    :type minimum: int or float
    :param maximum: The maximum allowed value that can be returned; must be greater than ``minimum``.
    :type maximum: int or float
    :return: A random number drawn uniformly from across the range determined by the provided arguments.
    :rtype: float

    .. note:: One useful application of this function is rate limiting: a script can pause in between requests at a \
        reasonably fast pace, but then moderate itself and pause for longer periods if it begins encountering errors, \
        simply by increasing the ``attempt`` variable (hence its name).

    Usage::

        from pewtils import new_random_number

        >>> new_random_number(attempt=1)
        1.9835581813820642
        >>> new_random_number(attempt=2)
        3.1022350739064
    """

    return uniform(minimum, min(maximum, minimum * 2 ** attempt))


def chunk_list(seq, size):

    """
    Takes a sequence and groups values into smaller lists based on the specified size.

    :param seq: List or a list-like iterable
    :type seq: list or iterable
    :param size: Desired size of each sublist
    :type size: int
    :return: A list of lists
    :rtype: list

    Usage::

        from pewtils import chunk_list

        >>> number_sequence = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        >>> chunk_list(number_sequence, 3)
        [[1, 2, 3], [4, 5, 6], [7, 8, 9], [10]]
    """

    return (seq[pos : (pos + size)] for pos in range(0, len(seq), size))


def flatten_list(l):

    """
    Takes a list of lists and flattens it into a single list. Nice shortcut to avoid having to deal with list \
    comprehension.

    :param l: A list of lists
    :type l: list
    :return: A flattened list of all of the elements contained in the original list of lists
    :rtype: list

    Usage::

        from pewtils import flatten_list

        >>> nested_lists = [[1, 2, 3], [4, 5, 6]]
        >>> flatten_list(nested_lists)
        [1, 2, 3, 4, 5, 6]
    """

    return [item for sublist in l for item in sublist]


def scan_dictionary(search_dict, field):

    """
    Takes a dictionary with nested lists and dictionaries, and searches recursively for a specific key. Since keys can
    occur more than once, the function returns a list of all of the found values along with a list of equal length
    that specifies the nested key path to each value.

    :param search_dict: The dictionary to search
    :type search_dict: dict
    :param field: The field to find
    :type field: str
    :return: A tuple of the found values and file path-style strings representing their locations
    :rtype: tuple

    Usage::

        from pewtils import scan_dictionary

        >>> test_dict = {"one": {"two": {"three": "four"}}}
        >>> scan_dictionary(test_dict, "three")
        (['four'], ['one/two/three/'])
        >>> scan_dictionary(test_dict, "five")
        ([], [])
    """

    fields_found = []
    key_path = []

    for key, value in search_dict.items():
        if key == field:
            fields_found.append(value)
            new_str = str(key) + "/"
            key_path.append(new_str)

        elif isinstance(value, dict):
            results, path = scan_dictionary(value, field)
            for result in results:
                fields_found.append(result)
            for road in path:
                new_str = str(key) + "/" + road
                key_path.append(new_str)

        elif isinstance(value, list):
            for item in value:
                if isinstance(item, dict):
                    more_results, more_path = scan_dictionary(item, field)
                    for another_result in more_results:
                        fields_found.append(another_result)
                    for another_road in more_path:
                        new_str = str(key) + "/" + another_road
                        key_path.append(new_str)

    return fields_found, key_path


def recursive_update(existing, new):

    """
    Takes an object and a dictionary representation of attributes and values, and recursively traverses through the
    new values and updates the object.

    | Regardless of whether or not the keys in the dictionary correspond to attribute names or dictionary keys; \
    you can use this to iterate through a nested hierarchy of objects and dictionaries and update whatever you like.

    :param existing: An object or dictionary
    :type existing: dict or object
    :param new: A dictionary where keys correspond to the names of keys in the existing dictionary or attributes on \
    the existing object
    :type new: dict or object
    :return: A copy of the original object or dictionary, with the values updated based on the provided map
    :rtype: dict or object

    Usage::

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

    """

    def _hasattr(obj, attr):
        if isinstance(obj, dict):
            return attr in obj
        else:
            return hasattr(obj, attr)

    def _setattr(obj, attr, val):
        if isinstance(obj, dict):
            obj[attr] = val
        else:
            setattr(obj, attr, val)
        return obj

    def _getattr(obj, attr):
        if isinstance(obj, dict):
            return obj[attr]
        else:
            return getattr(obj, attr)

    existing = copy.deepcopy(existing)
    if isinstance(new, dict):
        for k, v in new.items():

            if _hasattr(existing, k):
                _setattr(
                    existing,
                    k,
                    recursive_update(_getattr(existing, k), _getattr(new, k)),
                )
            else:
                _setattr(existing, k, _getattr(new, k))
        return existing
    else:
        return new


def cached_series_mapper(series, function):

    """
    Applies a function to all of the unique values in a :py:class:`pandas.Series` to avoid repeating the operation \
    on duplicate values.

    | Great if you're doing database lookups or something computationally intensive on a column that may contain \
    repeating values, etc.

    :param series: A :py:class:`pandas.Series`
    :type series: :py:class:`pandas.Series`
    :param function: A function to apply to values in the :py:class:`pandas.Series`
    :return: The resulting :py:class:`pandas.Series`
    :rtype: :py:class:`pandas.Series`

    Usage::

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
    """

    val_map = {}
    for val in series.unique():
        val_map[val] = function(val)

    return series.map(val_map)


def multiprocess_group_apply(grp, func, *args, **kwargs):
    """

    Apply arbitrary functions to groups or slices of a Pandas DataFrame using multiprocessing, to efficiently \
    map or aggregate data. Each group gets processed in parallel, and the results are concatenated together after \
    all processing has finished. If you pass a function that aggregates each group into a single value, you'll get \
    back a DataFrame with one row for each group, as though you had performed a `.agg` function. \
    If you pass a function that returns a value for each _row_ in the group, then you'll get back a DataFrame \
    in your original shape. In this case, you would simply be using grouping to efficiently apply a row-level operation.

    :param grp: A Pandas DataFrameGroupBy object
    :type grp: pandas.core.groupby.generic.DataFrameGroupBy
    :param func: A function that accepts a Pandas DataFrame representing a group from the original DataFrame
    :type func: function
    :param args: Arguments to be passed to the function
    :param kwargs: Keyword arguments to be passed to the function
    :return: The resulting DataFrame
    :rtype: pandas.DataFrame

    Usage::

        df = pd.DataFrame([
            {"group": 1, "value": "one two three"},
            {"group": 1, "value": "one two three four"},
            {"group": 2, "value": "one two"}
        ])

        ### For efficient aggregation

        def get_length(grp):
            # Simple function that returns the number of rows in each group
            return len(grp)

        >>> df.groupby("group_col").apply(lambda x: len(x))
        1    2
        2    1
        dtype: int64
        >>> multiprocess_group_apply(df.groupby("group_col"), get_length)
        1    2
        2    1
        dtype: int64

        ### For efficient mapping

        def get_value_length(grp):
            # Simple function that returns the word count of each row in the group
            return grp['value'].map(lambda x: len(x.split()))

        >>> df['value'].map(lambda x: len(x.split()))
        0    3
        1    4
        2    2
        Name: value, dtype: int64
        >>> multiprocess_group_apply(df.groupby("group_col"), get_value_length)
        0    3
        1    4
        2    2
        Name: value, dtype: int64

        # If you just want to efficiently map a function to your DataFrame and you want to evenly split your
        # DataFrame into groups, you could do the following:

        df["group_col"] = (df.reset_index().index.values / (len(df) / multiprocessing.cpu_count())).astype(int)
        df["mapped_value"] = multiprocess_group_apply(df.groupby("group_col"), get_value_length)
        del df["group_col"]

    """

    results = []
    pool = multiprocessing.Pool(processes=multiprocessing.cpu_count())
    for name, group in grp:
        results.append(pool.apply_async(func, (group,) + args, kwargs))
    pool.close()
    pool.join()
    results = [r.get() for r in results]

    if not hasattr(results[0], "__len__") or isinstance(results[0], str):
        # Assume it's an aggregation function
        return pd.Series(results, index=[g for g, _ in grp])
    else:
        # Assume you're just mapping the function normally and using the groups to split the data
        return pd.concat(results)


def extract_json_from_folder(
    folder_path, include_subdirs=False, concat_subdir_names=False
):

    """
    Takes a folder path and traverses it, looking for JSON files. When it finds one, it adds it to a dictionary,
    with the key being the name of the file and the value being the JSON itself. This is useful if you store \
    configurations or various metadata in a nested folder structure, which we do for things like content analysis \
    codebooks.

    | Has options for recursively traversing a folder, and for optionally concatenating the subfolder names \
    into the dictionary keys as prefixes.

    :param folder_path: The path of the folder to scan
    :type folder_path: str
    :param include_subdirs: Whether or not to recursively scan subfolders
    :type include_subdirs: bool
    :param concat_subdir_names: Whether or not to prefix the dictionary keys with the names of subfolders
    :type concat_subdir_names: bool
    :return: A dictionary containing all of the abstracted JSON files as values
    :rtype: dict

    Usage::

        # For example, let's say we have the following folder structure
        # with various JSON codebooks scattered about:
        #
        # /codebooks
        #     /logos
        #         /antipathy.json
        #     /atp_open_ends
        #         /w29
        #             /sources_of_meaning.json
        #
        # Here's what we'd get depending on the different parameters we use:

        from pewtils import extract_json_from_folder
        >>> extract_json_from_folder("codebooks", include_subdirs=False, concat_subdir_names=False)
        {}
        >>> extract_json_from_folder("codebooks", include_subdirs=True, concat_subdir_names=False)
        {
            "logos": {"antipathy": "json would be here"},
            "atp_open_ends": {"w29": {"sources_of_meaning": "json would be here"}}
        }
        >>> extract_json_from_folder("codebooks", include_subdirs=True, concat_subdir_names=True)
        {
            "logos_antipathy": "json would be here",
            "atp_open_ends_w29_sources_of_meaning": "json would be here"
        }
    """

    attributes = {}
    subdirs = []
    if os.path.exists(folder_path):
        for path, subdir, files in walk(folder_path):
            if folder_path == path:
                for file in files:
                    if file.endswith(".json"):
                        key = re.sub(".json", "", file)
                        with closing(open(os.path.join(path, file), "r")) as infile:
                            try:
                                attributes[key] = json.load(infile)
                            except ValueError:
                                print("JSON file is invalid: {}".format(file))
            if subdir:
                subdirs.append(subdir)

    if include_subdirs and len(subdirs) > 0:
        for subdir in subdirs[0]:
            if subdir != "__pycache__":
                results = extract_json_from_folder(
                    os.path.join(folder_path, subdir),
                    include_subdirs=True,
                    concat_subdir_names=concat_subdir_names,
                )
                if not concat_subdir_names:
                    attributes[subdir] = results
                else:
                    for subattr_name, subattr in results.items():
                        attributes["_".join([subdir, subattr_name])] = subattr

    return attributes


def extract_attributes_from_folder_modules(
    folder_path,
    attribute_name,
    include_subdirs=False,
    concat_subdir_names=False,
    current_subdirs=None,
):

    """
    Takes a folder path and traverses it, looking for Python files that contain an attribute (i.e., class, function,
    etc.) with a given name. It extracts those attributes and returns a dictionary where the keys are the names of the
    files that contained the attributes, and the values are the attributes themselves.

    This operates exactly the same as :py:func:`pewtils.extract_json_from_folder` except instead of reading JSON files
    and adding them as values in the dictionary that gets returned, this function will instead look for Python files
    that contain a function, class, method, or attribute with the name you provide in ``attribute_name`` and will load
    that attribute in as the values.

    :param folder_path: The path of a folder/module to scan
    :type folder_path: str
    :param attribute_name: The name of the attribute (class, function, variable, etc.) to extract from files
    :type attribute_name: str
    :param include_subdirs: Whether or not to recursively scan subfolders
    :type include_subdirs: bool
    :param concat_subdir_names: Whether or not to prefix the dictionary keys with the names of subfolders
    :type concat_subdir_names: bool
    :param current_subdirs: Used to track location when recursively iterating a module (do not use)
    :return: A dictionary with all of the extracted attributes as values
    :rtype: dict

    .. note:: if you use Python 2.7 you will need to add ``from __future__ import absolute_import`` to the top of files \
        that you want to scan and import using this function.
    """

    if not folder_path.startswith(os.getcwd()):
        folder_path = os.path.join(os.getcwd(), folder_path)
    test_path, _ = os.path.split(folder_path)
    while test_path != "/":
        if "__init__.py" not in os.listdir(test_path):
            break
        test_path, _ = os.path.split(test_path)
    module_location = test_path

    current_folder = folder_path.split("/")[-1]
    if not current_subdirs:
        current_subdirs = []

    attributes = {}
    subdirs = []
    if os.path.exists(folder_path):
        for path, subdir_list, files in walk(folder_path):
            if folder_path == path:
                for file in files:
                    if file.endswith(".py") and not file.startswith("__init__"):
                        file_name = file.split(".")[0]
                        module_name = re.sub(
                            "/",
                            ".",
                            re.sub(
                                module_location,
                                "",
                                os.path.splitext(os.path.join(path, file))[0],
                            ),
                        ).strip(".")
                        if module_name in sys.modules:
                            module = sys.modules[module_name]
                            # https://github.com/ansible/ansible/issues/13110
                        else:
                            try:
                                module = SourceFileLoader(
                                    module_name, os.path.join(path, file)
                                ).load_module()
                            except NameError:
                                file, pathname, description = imp.find_module(
                                    file_name, [path]
                                )
                                warnings.simplefilter("error", RuntimeWarning)
                                try:
                                    module = imp.load_module(
                                        module_name, file, pathname, description
                                    )
                                except RuntimeWarning:
                                    try:
                                        module = imp.load_module(
                                            module_name.split(".")[-1],
                                            file,
                                            pathname,
                                            description,
                                        )
                                    except RuntimeWarning:
                                        module = None
                                    except (ImportError, AttributeError):
                                        module = None
                                except (ImportError, AttributeError):
                                    module = None
                        if hasattr(module, attribute_name):
                            attributes[file_name] = getattr(module, attribute_name)

            if subdir_list:
                subdirs.extend(subdir_list)

    if include_subdirs:
        for subdir in set(subdirs):
            results = extract_attributes_from_folder_modules(
                os.path.join(folder_path, subdir),
                attribute_name,
                concat_subdir_names=concat_subdir_names,
                include_subdirs=True,
                current_subdirs=current_subdirs + [current_folder],
            )
            if not concat_subdir_names:
                attributes[subdir] = results
            else:
                for subattr_name, subattr in results.items():
                    attributes["_".join([subdir, subattr_name])] = subattr

    if is_null(current_subdirs, empty_lists_are_null=True):
        for name in attributes.keys():
            try:
                attributes[name]._name = name
            except AttributeError:
                pass

    return attributes


class timeout_wrapper:
    def __init__(self, seconds=1, error_message="Timeout"):
        """
        Context manager that will raise an error if it takes longer than the specified number of seconds to execute.
        Found via this very helpful Stack Overflow post:
        https://stackoverflow.com/questions/2281850/timeout-function-if-it-takes-too-long-to-finish

        :param seconds: Number of seconds allowed for the code to execute
        :param error_message: Optional custom error message to raise
        """
        self.seconds = seconds
        self.error_message = error_message

    def handle_timeout(self, signum, frame):
        raise Exception(self.error_message)

    def __enter__(self):
        signal.signal(signal.SIGALRM, self.handle_timeout)
        signal.alarm(self.seconds)

    def __exit__(self, t, value, traceback):
        signal.alarm(0)


class PrintExecutionTime(object):

    """
    Simple context manager to print the time it takes for a block of code to execute

    :param label: A label to print alongside the execution time
    :param stdout: a StringIO-like output stream (sys.stdout by default)

    Usage::

        from pewtils import PrintExecutionTime

        >>> with PrintExecutionTime(label="my function"): time.sleep(5)
        my function: 5.004292011260986 seconds

    """

    def __init__(self, label=None, stdout=None):
        self.start_time = None
        self.end_time = None
        self.label = label
        self.stdout = sys.stdout if not stdout else stdout

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.end_time = time.time()
        if self.label:
            self.stdout.write(
                "{}: {} seconds".format(self.label, self.end_time - self.start_time)
            )
        else:
            self.stdout.write("{} seconds".format(self.end_time - self.start_time))
