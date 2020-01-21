from builtins import object
import os
import hashlib
import datetime
import json
import time
import pandas as pd
import pickle as pickle
from scandir import scandir

try:
    from io import StringIO, BytesIO
except ImportError:
    from StringIO import StringIO as BytesIO
    from StringIO import StringIO

from contextlib import closing
from boto.s3.key import Key
from boto.s3.connection import S3Connection, OrdinaryCallingFormat

from pewtils import is_not_null


class FileHandler(object):

    """
    Read/write data files in a variety of formats, locally and in s3. File extensions are standardized to promote consistency (e.g., Pickle files must have the extension ".pkl", etc.).

    :param path: The path to the folder that you'll be writing to or reading from
    :param use_s3: Whether the path is an S3 location or local location
    :param aws_access: The AWS access key; will also try to fetch it from the environment parameter AWS_ACCESS_KEY_ID
    :param aws_secret: The AWS secret token; will also try to fetch from the environment as AWS_SECRET_ACCESS_KEY
    :param bucket: The name of the S3 bucket; required if use_s3=True; will also try to fetch from the environment as S3_BUCKET
    """

    def __init__(
        self, path, use_s3=None, aws_access=None, aws_secret=None, bucket=None
    ):

        if aws_access is None:
            aws_access = os.environ.get("AWS_ACCESS_KEY_ID", None)
        if aws_secret is None:
            aws_secret = os.environ.get("AWS_SECRET_ACCESS_KEY", None)
        if bucket is None:
            bucket = os.environ.get("S3_BUCKET", None)

        self.path = path

        self.use_s3 = use_s3 if is_not_null(bucket) else False
        if self.use_s3:

            s3_params = {}

            if aws_access is not None:
                s3_params["aws_access_key_id"] = aws_access
                s3_params["aws_secret_access_key"] = aws_secret

            if "." in bucket:
                s3_params["calling_format"] = OrdinaryCallingFormat()

            self.s3 = S3Connection(**s3_params).get_bucket(bucket)

        else:
            self.path = os.path.join(self.path)
            if not os.path.exists(self.path):
                try:
                    os.makedirs(self.path)
                except Exception as e:
                    print("Warning: couldn't make directory '{}'".format(self.path))
                    print(e)

    def iterate_path(self):

        """
        Iterates over the directory and returns a list of filenames or S3 object keys

        :return: Yields a list of filenames or S3 keys
        """

        if self.use_s3:
            for key in self.s3.list(prefix=self.path):
                yield key
        else:
            for f in scandir(self.path):
                yield f.name

    def clear_folder(self):

        """
        Deletes the path (if local) or unlinks all keys in the bucket folder (if S3)

        """

        if self.use_s3:
            for key in self.s3.list(prefix=self.path):
                key.delete()
        else:
            for f in scandir(self.path):
                os.unlink(os.path.join(self.path, f.name))

    def clear_file(self, key, format="pkl", hash_key=False):

        """
        Deletes a file.

        :param key: The name of the file.
        """

        if hash_key:
            key = self.get_key_hash(key)
        if self.use_s3:
            filepath = "/".join([self.path, "{}.{}".format(key, format)])
            key = self.s3.get_key(filepath)
            self.s3.delete_key(key.name)
        else:
            key += ".{}".format(format)
            path = os.path.join(self.path, key)
            os.unlink(path)

    def get_key_hash(self, key):

        """
        Converts a key to a hashed representation; useful for caching

        :param key: A raw string
        :return: A SHA224 hash representation of that key
        """

        return hashlib.sha224(key.encode("utf8")).hexdigest()

    def write(
        self, key, data, format="pkl", hash_key=False, add_timestamp=False, **io_kwargs
    ):

        """
        Writes arbitrary data objects to a variety of file formats.

        | If you save something to csv/tab/xlsx/xls/dta, it assumes you've passed it a Pandas DataFrame object. \
        If you're trying to save an object to JSON, it assumes that you're passing it valid JSON. By default, though, \
        the handler attempts to use pickling, allowing you to save (mostly) anything you want.

        :param key: The name of the file or key (without a file suffix!)
        :param data: The actual data to write to the file
        :param format: The format the data should be saved in (pkl/csv/tab/xlsx/xls/dta/json). Defaults to pkl. \
        This will be used as the file's suffix.
        :param hash_key: Whether or not to hash the provided key before saving the file. (Default=False)
        :param add_timestamp: Optionally add a timestamp to the filename
        :param io_kwargs: Additional parameters to pass along to the save function, which depends on the format of \
        the file you want to save.  The "dta" format uses `pandas.DataFrame.to_stata`; csv uses `to_csv`; pkl uses \
        `pickle.dumps`; json uses `json.dumps`
        :return: None
        """

        format = format.strip(".")

        if hash_key:
            key = self.get_key_hash(key)

        if add_timestamp:
            key = "{}_{}".format(key, datetime.datetime.now())

        def _get_output(output, data, io_kwargs):
            if format == "tab":
                io_kwargs["sep"] = "\t"
            if format in ["csv", "tab"]:
                data.to_csv(output, encoding="utf8", **io_kwargs)
            elif format == "dta":
                data.to_stata(output, **io_kwargs)
            elif format in ["xls", "xlsx"]:
                writer = pd.ExcelWriter(output, engine="xlsxwriter")
                data.to_excel(writer, **io_kwargs)
                writer.save()
            data = output.getvalue()
            return data

        if format in ["csv", "xls", "xlsx", "tab", "dta"]:
            try:
                data = _get_output(BytesIO(), data, io_kwargs)
            except Exception as e:
                print(e)
                try:
                    data = _get_output(StringIO(), data, io_kwargs)
                except:
                    raise Exception(
                        "Couldn't convert data into '{}' format".format(format)
                    )

        elif format == "pkl":
            data = pickle.dumps(data, **io_kwargs)
        elif format == "json":
            data = json.dumps(data, **io_kwargs)

        key += ".{}".format(format)

        if self.use_s3:

            k = Key(self.s3)
            k.key = "/".join([self.path, key])
            k.set_contents_from_string(data)

        else:

            path = os.path.join(self.path, key)
            if os.path.exists(self.path):
                try:
                    with closing(open(path, "w")) as output:
                        output.write(data)
                except:
                    with closing(open(path, "wb")) as output:
                        output.write(data)

    def read(self, key, format="pkl", hash_key=False, **io_kwargs):

        """
        Reads a file from the directory, returning its contents.

        :param key: The name of the file to read (without a suffix!)
        :param format: The format of the file (pkl/json/csv/dta/xls/xlsx/tab); expects the file extension to match
        :param hash_key: Whether the key should be hashed prior to looking for and retrieving the file.
        :param io_kwargs: Optional arguments to be passed to the specific load function (dependent on file format)
        :return: The file contents, in the requested format
        """

        format = format.strip(".")

        if hash_key:
            key = self.get_key_hash(key)

        data = None
        filepath = "/".join([self.path, "{}.{}".format(key, format)])

        if self.use_s3:

            k = self.s3.get_key(filepath)
            if k:
                try:
                    data = k.get_contents_as_string()
                except ValueError:
                    pass
        else:

            if os.path.exists(filepath):
                try:
                    with closing(open(filepath, "r")) as input:
                        data = input.read()
                except:
                    # TODO: handle this exception more explicitly
                    with closing(open(filepath, "rb")) as input:
                        data = input.read()

        if format == "pkl":

            try:
                data = pickle.loads(data)
            except TypeError:
                data = None
            except ValueError:
                if "attempt_count" not in io_kwargs:
                    io_kwargs["attempt_count"] = 1
                print(
                    "Insecure pickle string; probably a concurrent read-write, \
                    will try again in 5 seconds (attempt #{})".format(
                        io_kwargs["attempt_count"]
                    )
                )
                time.sleep(5)
                if io_kwargs["attempt_count"] <= 3:
                    io_kwargs["attempt_count"] += 1
                    data = self.read(key, format=format, hash_key=hash_key, **io_kwargs)
                else:
                    data = None
            except Exception as e:
                print("Couldn't load pickle!  {}".format(e))
                data = None

        elif format in ["tab", "csv"]:

            if format == "tab":
                io_kwargs["delimiter"] = "\t"
            try:
                data = pd.read_csv(BytesIO(data), **io_kwargs)
            except:
                data = pd.read_csv(StringIO(data), **io_kwargs)

        elif format in ["xlsx", "xls"]:
            try:
                data = pd.read_excel(BytesIO(data), **io_kwargs)
            except:
                data = pd.read_excel(StringIO(data), **io_kwargs)

        elif format == "json":
            try:
                data = json.loads(data)
            except:
                pass

        elif format == "dta":

            try:
                data = pd.read_stata(BytesIO(data), **io_kwargs)
            except:
                data = pd.read_stata(StringIO(data), **io_kwargs)

        return data
