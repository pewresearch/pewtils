from builtins import object
from contextlib import closing
from pewtils import is_not_null
from scandir import scandir
import boto3
import datetime
import hashlib
import json
import os
import pandas as pd
import pickle as pickle
import time

try:
    from io import StringIO, BytesIO

except ImportError:
    from StringIO import StringIO as BytesIO
    from StringIO import StringIO


class FileHandler(object):

    """
    Read/write data files in a variety of formats, locally and in Amazon S3 buckets.

    :param path: A valid path to the folder in local or s3 directory where files will be written to or read from
    :type path: str
    :param use_s3: Whether the path is an S3 location or local location
    :type use_s3: bool
    :param bucket: The name of the S3 bucket, required if ``use_s3=True``; will also try to fetch from the environment \
    as S3_BUCKET
    :type bucket: str

    .. note:: Typical rectangular data files (i.e. ``csv``, ``tab``, ``xlsx``, ``xls``, ``dta`` file extension types) will be \
        read to/written from a :py:class:`pandas.DataFrame` object. The exceptions are `pkl` and `json` objects which \
        accept any serializable Python object and correctly-formatted JSON object respectively.

    .. tip:: You can configure your environment to make it easier to automatically connect to S3 by defining the \
        variable ``S3_BUCKET``.

    Usage::

        from pewtils.io import FileHandler

        >>> h = FileHandler("./", use_s3=False)  # current local folder
        >>> df = h.read("my_csv", format="csv")
        # Do something and save to Excel
        >>> h.write("my_new_csv", df, format="xlsx")

        >>> my_data = [{"key": "value"}]
        >>> h.write("my_data", my_data, format="json")

        >>> my_data = ["a", "python", "list"]
        >>> h.write("my_data", my_data, format="pkl")

        # To read/write to an S3 bucket
        # The FileHandler detects your AWS tokens using boto3's standard methods to find them in ~/.aws or defined as environment variables.
        >>> h = FileHandler("/my_folder", use_s3=True, bucket="my-bucket")
    """

    def __init__(self, path, use_s3=None, bucket=None):
        self.bucket = os.environ.get("S3_BUCKET", None) if bucket is None else bucket
        self.path = path
        self.use_s3 = use_s3 if is_not_null(self.bucket) else False
        if self.use_s3:
            s3_params = {}
            self.s3 = boto3.client("s3")

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
        :rtype: iterable

        Usage::

            from pewtils.io import FileHandler

            >>> h = FileHandler("./", use_s3=False)
            >>> for file in h.iterate_path(): print(file)
            file1.csv
            file2.pkl
            file3.json

        """

        if self.use_s3:
            for key in self.s3.list_objects(Bucket=self.bucket, Prefix=self.path)['Contents']:
                yield key["Key"]

        else:
            for f in scandir(self.path):
                yield f.name

    def clear_folder(self):
        """
        Deletes the path (if local) or unlinks all keys in the bucket folder (if S3)

        .. warning:: This is a destructive function, use with caution!

        Usage::

            from pewtils.io import FileHandler

            >>> h = FileHandler("./", use_s3=False)
            >>> len(list(h.iterate_path()))
            3
            >>> h.clear_folder()
            >>> len(list(h.iterate_path()))
            0

        """

        if self.use_s3:
            for key in self.s3.list_objects(Bucket=self.bucket, Prefix=self.path)['Contents']:
                self.s3.delete_object(Bucket=self.bucket, Prefix=key['Key'])

        else:
            for f in scandir(self.path):
                os.unlink(os.path.join(self.path, f.name))

    def clear_file(self, key, format="pkl", hash_key=False):
        """
        Deletes a specific file.

        .. warning:: This is a destructive function, use with caution!

        :param key: The name of the file to delete
        :type key: str
        :param format: The file extension
        :type format: str
        :param hash_key: If True, will hash the filename before looking it up; default is False.
        :type hash_key: bool

        Usage::

            from pewtils.io import FileHandler

            >>> h = FileHandler("./", use_s3=False)
            >>> for file in h.iterate_path(): print(file)
            file1.csv
            file2.pkl
            file3.json
            >>> h.clear_file("file1", format="csv")
            >>> for file in h.iterate_path(): print(file)
            file2.pkl
            file3.json

        """

        if hash_key:
            key = self.get_key_hash(key)

        if self.use_s3:
            filepath = "/".join([self.path, "{}.{}".format(key, format)])
            key = self.s3.delete_object(Bucket=self.bucket, Key=filepath)

        else:
            key += ".{}".format(format)
            path = os.path.join(self.path, key)
            os.unlink(path)

    def get_key_hash(self, key):

        """
        Converts a key to a hashed representation. Allows you to pass arbitrary objects and convert their string \
        representation into a shorter hashed key, so it can be useful for caching. You can call this method \
        directly to see the hash that a key will be converted into, but this method is mainly used in conjunction \
        with the :py:meth:`pewtils.FileHandler.write` and :py:meth:`pewtils.FileHandler.read` methods by passing in \
        ``hash_key=True``.

        :param key: A raw string or Python object that can be meaningfully converted into a string representation
        :type key: str or object
        :return: A SHA224 hash representation of that key
        :rtype: str

        Usage::

            from pewtils.io import FileHandler

            >>> h = FileHandler("tests/files", use_s3=False)
            >>> h.get_key_hash("temp")
            "c51bf90ccb22befa316b7a561fe9d5fd9650180b14421fc6d71bcd57"
            >>> h.get_key_hash({"key": "value"})
            "37e13e1116c86a6e9f3f8926375c7cb977ca74d2d598572ced03cd09"

        """

        try:
            return hashlib.sha224(key.encode("utf8")).hexdigest()
        except AttributeError:
            return hashlib.sha224(str(key).encode("utf8")).hexdigest()

    def write(
        self, key, data, format="pkl", hash_key=False, add_timestamp=False, **io_kwargs
    ):

        """
        Writes arbitrary data objects to a variety of file formats.


        :param key: The name of the file or key (without a file suffix!)
        :type key: str
        :param data: The actual data to write to the file
        :type data: object
        :param format: The format the data should be saved in (pkl/csv/tab/xlsx/xls/dta/json). Defaults to pkl. \
        This will be used as the file's suffix.
        :type format: str
        :param hash_key: Whether or not to hash the provided key before saving the file. (Default=False)
        :type hash_key: bool
        :param add_timestamp: Optionally add a timestamp to the filename
        :type add_timestamp: bool
        :param io_kwargs: Additional parameters to pass along to the Pandas save function, if applicable
        :return: None

        .. note:: When saving a ``csv``, ``tab``, ``xlsx``, ``xls``, or ``dta`` file, this function expects to receive a \
            Pandas :py:class:`pandas.DataFrame`. When you use these formats, you can also pass optional ``io_kwargs`` \
            which will be forwarded to the corresponding :py:mod:`pandas` method below:

                - `dta`: :py:meth:`pandas.DataFrame.to_stata`
                - `csv`: :py:meth:`pandas.DataFrame.to_csv`
                - `tab`: :py:meth:`pandas.DataFrame.to_csv`
                - `xlsx`: :py:meth:`pandas.DataFrame.to_excel`
                - `xls`: :py:meth:`pandas.DataFrame.to_excel`

            If you're trying to save an object to JSON, it assumes that you're passing it valid JSON. By default, \
            the handler attempts to use pickling, allowing you to save anything you want, as long as it's serializable.

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
            try:
                upload = BytesIO(data)

            except TypeError:
                upload = BytesIO(data.encode())

            self.s3.upload_fileobj(upload, Bucket=self.bucket, Key="/".join([self.path, key]))

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
        Reads a file from the directory or S3 path, returning its contents.

        :param key: The name of the file to read (without a suffix!)
        :type key: str
        :param format: The format of the file (pkl/json/csv/dta/xls/xlsx/tab); expects the file extension to match
        :type format: str
        :param hash_key: Whether the key should be hashed prior to looking for and retrieving the file.
        :type hash_key: bool
        :param io_kwargs: Optional arguments to be passed to the specific load function (dependent on file format)
        :return: The file contents, in the requested format

        .. note:: You can pass optional ``io_kwargs`` that will be forwarded to the function below that corresponds to \
            the format of the file you're trying to read in

            - `dta`: :py:meth:`pandas.DataFrame.read_stata`
            - `csv`: :py:meth:`pandas.DataFrame.read_csv`
            - `tab`: :py:meth:`pandas.DataFrame.read_csv`
            - `xlsx`: :py:meth:`pandas.DataFrame.read_excel`
            - `xls`: :py:meth:`pandas.DataFrame.read_excel`
        """

        format = format.strip(".")

        if hash_key:
            key = self.get_key_hash(key)

        data = None
        filepath = "/".join([self.path, "{}.{}".format(key, format)])

        if self.use_s3:
            try:
                data = StringIO()

            except TypeError:
                data = BytesIO()

            self.s3.download_fileobj(data, Bucket=self.bucket, Key=filepath)
            data = data.getvalue()
        else:
            if os.path.exists(filepath):
                try:
                    with closing(open(filepath, "r")) as infile:
                        data = infile.read()

                except:
                    # TODO: handle this exception more explicitly
                    with closing(open(filepath, "rb")) as infile:
                        data = infile.read()

        if is_not_null(data):
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
                        data = self.read(
                            key, format=format, hash_key=hash_key, **io_kwargs
                        )

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
                # https://stackoverflow.com/questions/64264563/attributeerror-elementtree-object-has-no-attribute-getiterator-when-trying
                if "engine" not in io_kwargs:
                    io_kwargs["engine"] = "openpyxl"

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

            elif format == "txt":
                if isinstance(data, bytes):
                    data = data.decode()

        return data
