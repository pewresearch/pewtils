import chardet

import os, re, itertools, json, sys
import imp

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
    if text:
        try:
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
    :return: bool (True if the value is null)
    """

    return (not is_not_null(val, empty_lists_are_null=empty_lists_are_null, custom_nulls=custom_nulls))


def recursive_update(existing, new):
    for k, v in new.items():
        if k in existing and type(new[k]) == dict and is_not_null(existing[k]):
            existing[k] = recursive_update(existing[k], new[k])
        else:
            existing[k] = new[k]
    return existing


def recursive_setattr(object, attr, value):
    if type(value) == dict:
        for subattr, value in value.items():
            recursive_setattr(getattr(object, attr), subattr, value)
    else:
        setattr(object, attr, value)


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
    :param folder_path: takes local or remote path
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

    if include_subdirs:
        for subdir in subdirs:
            if len(subdir) == 1:
                subdir = subdir[0]
                results = extract_json_from_folder(os.path.join(folder_path, subdir), include_subdirs=True)
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
    Returns folder attributes


    """

    # os.path.basename(os.path.dirname(folder_path))
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
                            #so it doesnt collide with other things

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
        except (UnicodeEncodeError, UnicodeDecodeError):
            hash = Nilsimsa(decode_text(text)).hexdigest()
    elif hash_function == "md5":
        try:
            hash = md5(text).hexdigest()
        except (UnicodeEncodeError, UnicodeDecodeError):
            hash = md5(decode_text(text)).hexdigest()
    else:
        try:
            import ssdeep
            try:
                hash = ssdeep.hash(text)
            except (UnicodeEncodeError, UnicodeDecodeError):
                hash = ssdeep.hash(decode_text(text))
        except ImportError:
            print("You need to install the ssdeep package in order to use this option")

    return hash


def concat(*args):
    strs = [decode_text(arg) for arg in args if not pd.isnull(arg)]
    return ' '.join(strs) if strs else np.nan


vector_concat = np.vectorize(concat)


def cached_series_mapper(series, function):
    """
    caches things in pandas DataFrame
    great if you're doing database lookups and have duplicates
    """

    val_map = {}
    for val in series.unique():
        val_map[val] = function(val)

    return series.map(val_map)


def scale_range(old_val, old_min, old_max, new_min, new_max):

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
