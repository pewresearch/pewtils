from __future__ import absolute_import
import os
import re
import itertools
import json
import sys
import chardet
import copy
import warnings
import zipcodes

try:
    from importlib.machinery import SourceFileLoader
except ImportError:
    import imp

import pandas as pd
import numpy as np

from random import uniform
from contextlib import closing
from scandir import walk
from unidecode import unidecode
from hashlib import md5


def decode_text(text, throw_loud_fail=False):
    """
    Attempts to decode and re-encode text as ASCII; if this fails, it will attempt to detect the string's encoding,
    decode it, and convert it to ASCII. If both these attempts fail, it will attempt to use the "unidecode" package to
    transliterate into ASCII. And finally, if that doesn't work, it will forcibly encode the text as ASCII and ignore
    non-ASCII characters. In Python 3, the decode/encode attempts will fail by default, and the unidecode package will
    be used to transliterate. In general, you shouldn't need to use this function in Python 3, but it can be used to
    convert unicode strings to bytes if you need to do so. Please be warned, this function is potentially destructive
    to source input and should be used with some care. Input text which cannot be decoded may be stripped out, replaced
    with a similar ASCII character or other placeholder, potentially resulting in an empty string.

    :param text: text to process
    :param throw_loud_fail: bool - if True exceptions will be raised, otherwise the function will fail silently and return an empty string (default False)
    :return: decoded text, or empty string ''
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


def is_not_null(val, empty_lists_are_null=False, custom_nulls=None):
    """
    Checks whether the value is null, using a variety of potential string values, etc. The following values are always
    considered null: `None, "None", "nan", "", " ", "NaN", "none", "n/a", "NONE", "N/A"
    :param val: The value to check
    :param empty_lists_are_null: Whether or not an empty list or dataframe should be considered null (default=False)
    :param custom_nulls: an optional list of additional values to consider as null
    :return: True if the value is not null
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
            return type(val) != type(None)


def is_null(val, empty_lists_are_null=False, custom_nulls=None):
    """
    Returns the opposite of the outcome of is_not_null. The following values are always considered null:
    `None, "None", "nan", "", " ", "NaN", "none", "n/a", "NONE", "N/A"

    :param val: The value to check
    :param empty_lists_are_null: Whether or not an empty list or dataframe should be considered null (default=False)
    :param custom_nulls: an optional list of additional values to consider as null
    :return: True if the value is null
    """

    return not is_not_null(
        val, empty_lists_are_null=empty_lists_are_null, custom_nulls=custom_nulls
    )


def recursive_update(existing, new):
    """
    Takes an object and a dictionary representation of attributes and values, and recursively traverses through the
    new values and updates the object.  Doesn't care if the keys in the dictionary correspond to attribute names or
    dictionary keys; you can use this to iterate through a nested hierarchy of objects and dictionaries and update
    whatever you like.

    :param existing: An object or dictionary
    :param new: A dictionary where keys correspond to the names of keys in the existing dictionary or attributes on
    the existing object
    :return: A copy of the original object or dictionary, with the values updated based on the provided map
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


def chunk_list(seq, size):

    """
    Takes a sequence and groups values into smaller lists based on the specified size.

    :param seq: list or a list-like iterable
    :param size: int - Desired size of each sublist
    :return: list - A list of lists
    """

    return (seq[pos : (pos + size)] for pos in range(0, len(seq), size))


def extract_json_from_folder(
    folder_path, include_subdirs=False, concat_subdir_names=False
):

    """
    Takes a folder path and traverses it, looking for JSON files. When it finds one, it adds it to a dictionary,
    with the key being the name of the file and the value being the JSON itself.  Has options for recursively
    traversing a folder, and for optionally concatenating the subfolder names into the dictionary keys as prefixes.

    :param folder_path: The path of the folder to scan
    :param include_subdirs: Whether or not to recursively scan subfolders
    :param concat_subdir_names: Whether or not to prefix the dictionary keys with the names of subfolders
    :return: A dictionary containing all of the abstracted JSON files as values
    """

    attributes = {}
    subdirs = []
    if os.path.exists(folder_path):
        for path, subdir, files in walk(folder_path):
            if folder_path == path:
                for file in files:
                    if file.endswith(".json"):
                        key = re.sub(".json", "", file)
                        with closing(open(os.path.join(path, file), "r")) as input:
                            try:
                                attributes[key] = json.load(input)
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
    Similar to `extract_json_from_folder`, this function iterates over a folder and looks for Python files that
    contain an attribute (like a class, function, or variable) with a given name. It extracts those attributes and
    returns a dictionary where the keys are the names of the files that contained the attributes, and the values
    are the attributes themselves.
    NOTE: if you use Python 2.7 you will need to add `from __future__ import absolute_import` to the top of files that
    you want to scan and import using this function.

    :param folder_path: The path of a folder/module to scan
    :param attribute_name: The name of the attribute (class, function, variable, etc.) to extract from files
    :param include_subdirs: Whether or not to recursively scan subfolders
    :param concat_subdir_names: Whether or not to prefix the dictionary keys with the names of subfolders
    :param current_subdirs: Used to track location when recursively iterating a module
    :return: A dictionary with all of the extracted attributes as values
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


def zipcode_num_to_string(zip):

    """
    Attempts to standardize a string/integer/float that contains a zipcode.

    :param zip: Object that contains a sequence of digits (string, integer, float)
    :return: A 5-digit string, or None
    """

    if is_not_null(zip):

        try:
            zip = str(int(str(zip).strip()[:5].split(".")[0]))
        except (TypeError, ValueError):
            zip = None

        if zip:
            zip = zip.zfill(5)
            if zipcodes.is_real(zip):
                return zip
            else:
                return None
    else:

        zip = None

    return zip


def flatten_list(l):

    """
    Takes a list of lists and flattens it into a single list

    :param l: A list of lists
    :return: A flattened list of all of the elements contained in the original list of lists
    """

    return [item for sublist in l for item in sublist]


def get_hash(text, hash_function="ssdeep"):

    """
    Generates hashed text. The string will be passed through `decode_text` and the returned value will be used instead
    of the original value if it runs successfully, in order to ensure consistent hashing in both Python 2 and 3. By
    default the function uses the ssdeep algorithm, which generates context-triggered hashes that are useful for
    computing document similarities at scale. The other options are the Nilsimsa locally-sensitive hashing algorithm,
    and the more traditional MD5 algorithm.

    :param text: The string to hash
    :param hash_function: The specific algorithm to use (default = 'ssdeep'); \
    options are 'nilsimsa', 'md5', and 'ssdeep'
    :return: A hashed representation of the provided string
    """

    decoded_text = decode_text(text).encode("utf8").strip()
    if decoded_text == "":
        decoded_text = text
    text = decoded_text
    if hash_function == "nilsimsa":
        from nilsimsa import Nilsimsa

        hash = Nilsimsa(text).hexdigest()
    elif hash_function == "md5":
        hash = md5(text).hexdigest()
    else:
        import ssdeep

        hash = ssdeep.hash(text)

    return hash


def concat_text(*args):

    """
    A helper function for concatenating text values; useful for mapping onto a variable in Pandas. Text
    values are passed through `decode_text` before concatenation.

    :param args: A list of text values that will be returned as a single space-separated string
    :return: A single string of the values concatenated by spaces
    """

    strs = [decode_text(arg) for arg in args if not pd.isnull(arg)]
    return " ".join(strs) if strs else np.nan


def vector_concat_text(*args):

    """
    Takes a list of equal-length lists and returns a single list with the rows concatenated by spaces

    :param args: A list of lists or Pandas series that contain text values
    :return: A single list with all of the text values for each row concatenated
    """

    return np.vectorize(concat_text)(*args)



def cached_series_mapper(series, function):

    """
    Applies a function to all of the unique values in a series to avoid repeating the operation on duplicate values.
    Great if you're doing database lookups, etc.

    :param series: A Pandas Series
    :param function: A function to apply to values in the series
    :return: The resulting series
    """

    val_map = {}
    for val in series.unique():
        val_map[val] = function(val)

    return series.map(val_map)


def scale_range(old_val, old_min, old_max, new_min, new_max):

    """
    Scales a value from one range to another.  Useful for comparing values from different scales, for example.

    :param old_val: The value to convert
    :param old_min: The minimum of the old range
    :param old_max: The maximum of the old range
    :param new_min: The minimum of the new range
    :param new_max: The maximum of the new range
    :return:
    """

    return (((old_val - old_min) * (new_max - new_min)) / (old_max - old_min)) + new_min


class classproperty(object):

    """
    Borrowed from a StackOverflow post (https://stackoverflow.com/a/3203659), this decorator allows you to define
    functions on a class that are accessible directly from the class itself (rather than an instance of the class).
    Essentially, this allows you to access `classproperty` attributes directly, like `obj.property`, rather than as
    a function on a class instance (like `obj = Obj(); obj.property()`).  Use like so:

        class Foo(object):
            x = 4
            @classproperty
            def number(cls):
                return cls.x
        >>> Foo().number
        4
        >>> Foo.number
        4
    """

    def __init__(self, fget):
        self.fget = fget

    def __get__(self, owner_self, owner_cls):
        return self.fget(owner_cls)


def scan_dictionary(search_dict, field):

    """
    Takes a dictionary with nested lists and dictionaries, and searches recursively for a specific key. Since keys can
    occur more than once, the function returns a list of all of the found values along with a list of equal length
    that specifies the nested key path to each value.

    :param search_dict: The dictionary to search
    :param field: The field to find
    :return: A tuple of the found values and file path-style strings representing their locations
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


def new_random_number(attempt=1, minimum=1.0, maximum=10):

    """
    Returns a random number between `minimum` (default 1) and a computed upper bound that exponentially increases
    based on the `attempt` parameter. The upper bound is capped using the `maximum` parameter (default 10) but is
    otherwise determined by the function `minimum * 2 ** attempt`. In effect, this means that when `attempt` is 1,
    the number returned will be in the range of the minimum and twice the minimum's value.  As you increase `attempt`,
    the possible range of returned values expands exponentially until it hits the `maximum` ceiling. One useful
    application of this function is rate limiting: a script can pause in between requests at a reasonably fast pace,
    but then moderate itself and pause for longer periods if it begins encountering errors, simply by increasing the
    `attempt` variable (hence its name).

    :param attempt: Increasing attempt will expand the upper-bound of the range from which the random number is drawn
    :param minimum: The minimum allowed value that can be returned; must be greater than zero.
    :param maximum: The maximum allowed value that can be returned; must be greater than `minimum`.
    :return: A random number drawn uniformly from across the range determined by the provided arguments.
    """

    return uniform(minimum, min(maximum, minimum * 2 ** attempt))
