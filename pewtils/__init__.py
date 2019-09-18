import os, re, itertools, json, sys, chardet, copy
try: from importlib.machinery import SourceFileLoader
except ImportError: import imp

import pandas as pd
import numpy as np

from contextlib import closing
from scandir import walk
from unidecode import unidecode
from hashlib import md5


NULL_VALUES = [None, "None", "nan", "", " ", "NaN", "none", "n/a", "NONE", "N/A"]


def decode_text(text, throw_loud_fail=False):
    """
    Attempts to decode and re-encode text as ASCII; if this fails, it will attempt to detect the string's encoding, decode it, and convert it to ASCII.
    If both these attempts fail, it will attempt to use the "unidecode" package to transliterate into ASCII.
    And finally, if that doesn't work, it will forcibly encode the text as ASCII and ignore non-ASCII characters.
    In Python 3, the decode/encode attempts will fail by default, and the unidecode package will be used to transliterate.
    In general, you shouldn't need to use this function in Python 3, but it can be used to convert unicode strings to bytes if you need to do so.
    Please be warned, this function is potentially destructive to source input and should be used with some care.
    Input text which cannot be decoded may be stripped out, replaced with a similar ASCII character or other placeholder,
    potentially resulting in an empty string.

    :param text: text to process
    :param throw_loud_fail: bool - if True will break on ascii
    :return: decoded text, or empty string ''
    """

    output_text = ''
    if is_not_null(text):
        try:
            text = u"{}".format(text)
            output_text = text.decode("ascii").encode("ascii")
        except:
            try:
                output_text = text.decode(
                    chardet.detect(text)['encoding']
                )
                output_text = output_text.encode("ascii")
            except:
                try:
                    output_text = unidecode(text)
                except:
                    if throw_loud_fail:
                        output_text = text.decode('ascii', 'ignore').encode("ascii")
                    else:
                        try: output_text = text.decode('ascii', 'ignore').encode("ascii")
                        except:
                            print("could not decode")
                            print(text)
    return output_text


def is_not_null(val, empty_lists_are_null=False, custom_nulls=None):

    """
    :param val: The value to check
    :param empty_lists_are_null: Whether or not an empty list or dataframe should be considered null (default=False)
    :param custom_nulls: list or None - if None defaults to global NULL_VALUES
    :return: True if the value is not null
    """

    if type(val) == list:
        if empty_lists_are_null and val == []: return False
        else: return True
    elif isinstance(val, pd.Series) or isinstance(val, pd.DataFrame):
        if empty_lists_are_null and len(val) == 0: return False
        else: return True
    else:
        try:
            try:
                good = val not in NULL_VALUES
                if custom_nulls:
                    good = good and (val not in custom_nulls)
                if good:
                    try:
                        try: good = not pd.isnull(val)
                        except IndexError:  good = True
                    except AttributeError: good = True
                return good
            except ValueError:
                return val.any()
        except TypeError:
            return type(val) != type(None)


def is_null(val, empty_lists_are_null=False, custom_nulls=None):

    """
    :param val: the value to check
    :param empty_lists_are_null: bool (default=False)
    :param custom_nulls: list or None - if None defaults to global NULL_VALUES
    :return: bool (True if the value is null)
    """

    return not is_not_null(val, empty_lists_are_null=empty_lists_are_null, custom_nulls=custom_nulls)


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
                _setattr(existing, k, recursive_update(_getattr(existing, k), _getattr(new, k)))
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

    return (seq[pos:pos + size] for pos in range(0, len(seq), size))


def extract_json_from_folder(folder_path, include_subdirs=False, concat_subdir_names=False):
    """
    Takes a folder path and traverses it, looking for JSON files. When it finds one, it adds it
    to a dictionary, with the key being the name of the file and the value being the JSON itself.  Has options for
    recursively traversing a folder, and for optionally concatenating the subfolder names into the dictionary keys
    as prefixes.
    :param folder_path: The path of the folder to scan
    :param include_subdirs: Whether or not to recursively scan subfolders
    :param concat_subdir_names: Whether or not to prefix the dictionary keys with the names of subfolders
    :return:
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
                            try: attributes[key] = json.load(input)
                            except ValueError:
                                print("JSON file is invalid: {}".format(file))
            if subdir:
                subdirs.append(subdir)

    if include_subdirs and len(subdirs) > 0:
        for subdir in subdirs[0]:
            if subdir != "__pycache__":
                results = extract_json_from_folder(os.path.join(folder_path, subdir), include_subdirs=True, concat_subdir_names=concat_subdir_names)
                if not concat_subdir_names:
                    attributes[subdir] = results
                else:
                    for subattr_name, subattr in results.items():
                        attributes["_".join([subdir, subattr_name])] = subattr

    return attributes


def extract_attributes_from_folder_modules(folder_path,
                            attribute_name,
                            include_subdirs=False,
                            concat_subdir_names=False,
                            current_subdirs=None):
    """
    Similar to `extract_json_from_folder`, this function iterates over a folder and looks for Python files that
    contain an attribute (like a class, function, or variable) with a given name. It extracts those attributes and
    returns a dictionary where the keys are the names of the files that contained the attributes, and the values
    are the attributes themselves.
    :param folder_path: The path of a folder/module to scan
    :param attribute_name: The name of the attribute (class, function, variable, etc.) to extract from files
    :param include_subdirs: Whether or not to recursively scan subfolders
    :param concat_subdir_names: Whether or not to prefix the dictionary keys with the names of subfolders
    :param current_subdirs: Used to track location when recursively iterating a module
    :return:
    """

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
                        module_name = file.split(".")[0]
                        unique_name = "_".join(current_subdirs + [current_folder, module_name])
                        try:
                            module = SourceFileLoader(unique_name, os.path.join(path, file)).load_module()
                        except NameError:
                            module = imp.load_source(
                                unique_name,
                                os.path.join(path, file)
                            )
                        if hasattr(module, attribute_name):
                            attributes[module_name] = getattr(module, attribute_name)
                            attributes[module_name].__file__ = module_name
                            # right now this is a hack so that django_queries Query objects
                            # can access their root name as they're referenced in this dictionary
                            # while preserving a more unique name for the actual imported module
                            # so it doesnt collide with other things

            if subdir_list:
                subdirs.extend(subdir_list)

    if include_subdirs:
        for subdir in set(subdirs):
            results = extract_attributes_from_folder_modules(os.path.join(folder_path, subdir),
                attribute_name, concat_subdir_names=concat_subdir_names, include_subdirs=True,
                current_subdirs=current_subdirs+[current_folder])
            if not concat_subdir_names:
                attributes[subdir] = results
            else:
                for subattr_name, subattr in results.items():
                    attributes["_".join([subdir, subattr_name])] = subattr

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
            if len(zip) == 3:
                zip = "00" + zip
            elif len(zip) == 4:
                zip = "0" + zip
            elif len(zip) < 3:
                zip = None
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
    Generate hashed text

    :param text: The string to hash
    :param hash_function: The specific algorithm to use (default = 'ssdeep'); \
    options are 'nilsimsa', 'md5', and 'ssdeep'
    :return: A hashed representation of the provided string
    """
    if hash_function == "nilsimsa":
        from nilsimsa import Nilsimsa
        try:
            hash = Nilsimsa(text).hexdigest()
        except (UnicodeEncodeError, UnicodeDecodeError, TypeError):
            hash = Nilsimsa(decode_text(text).encode("utf8")).hexdigest()
    elif hash_function == "md5":
        try:
            hash = md5(text).hexdigest()
        except (UnicodeEncodeError, UnicodeDecodeError, TypeError):
            hash = md5(decode_text(text).encode("utf8")).hexdigest()
    else:
        import ssdeep
        try:
            hash = ssdeep.hash(text)
        except (UnicodeEncodeError, UnicodeDecodeError, TypeError):
            hash = ssdeep.hash(decode_text(text).encode("utf8"))

    return hash


def concat_text(*args):
    """
    A helper function for concatenating text values; useful for mapping onto a variable in Pandas
    :param args: A list of text values that will be returned as a single space-separated string
    :return: A single string of the values concatenated by spaces
    """
    strs = [decode_text(arg) for arg in args if not pd.isnull(arg)]
    return ' '.join(strs) if strs else np.nan


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
    #galen found it on stackoverflow!
    https://stackoverflow.com/a/3203659

    #work on this
    this is a decorator that allows you to:::
        query.name rather than Query().name()
        evaluate names in models
    """

    def __init__(self, fget):
        self.fget = fget

    def __get__(self, owner_self, owner_cls):
        return self.fget(owner_cls)


def scan_dictionary(search_dict, field):

    """
    Takes a dict with nested lists and dicts,
    and searches all dicts for a key of the field
    provided.
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
