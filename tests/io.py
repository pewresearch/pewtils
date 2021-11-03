import unittest
import os
from contextlib import closing


class IOTests(unittest.TestCase):
    """
    To test, navigate to pewtils root folder and run `python -m unittest tests`
    """

    def setUp(self):
        import pandas as pd

        self.test_df = pd.DataFrame(
            [{"test": 1}, {"test": 2}, {"test": 3}, {"test": 4}]
        )
        self.test_json = {"test1": 1, "test2": 2, "test3": 3, "test4": 4}
        import json

        test_json = json.dumps(self.test_json)
        self.test_json = json.loads(test_json)

    def test_filehandler_iterate_path(self):
        from pewtils.io import FileHandler

        h = FileHandler("tests/files", use_s3=False)
        files = []
        for file in h.iterate_path():
            files.append(file)
        files = [
            f
            for f in files
            if not f.endswith(".pyc") and f not in ["__pycache__", ".DS_Store"]
        ]
        self.assertEqual(
            sorted(files),
            sorted(
                [
                    "subfolder",
                    "__init__.py",
                    "example.html",
                    "example_stripped_simple.html",
                    "json.json",
                    "example_stripped.html",
                    "py.py",
                ]
            ),
        )

    def test_filehandler_clear_folder(self):
        from pewtils.io import FileHandler

        h = FileHandler("tests/files/temp", use_s3=False)

        with closing(open("tests/files/temp/temp.txt", "wb")) as output:
            output.write(b"test")
        h.clear_folder()
        files = []
        for file in h.iterate_path():
            files.append(file)
        self.assertEqual(len(files), 0)
        os.rmdir("tests/files/temp")

    def test_clear_file(self):
        from pewtils.io import FileHandler

        h = FileHandler("tests/files/temp", use_s3=False)
        with closing(open("tests/files/temp/temp.txt", "wb")) as output:
            output.write(b"test")
        h.clear_file("temp", format="txt")
        files = []
        for file in h.iterate_path():
            files.append(file)
        self.assertNotIn("temp.txt", files)
        self.assertEqual(len(files), 0)
        os.rmdir("tests/files/temp")

        h = FileHandler("tests/files/temp", use_s3=False)
        key = h.get_key_hash("temp")
        with closing(open("tests/files/temp/{}.txt".format(key), "wb")) as output:
            output.write(b"test")
        h.clear_file("temp", format="txt", hash_key=True)
        files = []
        for file in h.iterate_path():
            files.append(file)
        self.assertNotIn("{}.txt".format(key), files)
        self.assertEqual(len(files), 0)
        os.rmdir("tests/files/temp")

    def test_filehandler_get_key_hash(self):
        from pewtils.io import FileHandler

        h = FileHandler("tests/files", use_s3=False)
        self.assertEqual(
            h.get_key_hash("temp"),
            "c51bf90ccb22befa316b7a561fe9d5fd9650180b14421fc6d71bcd57",
        )
        self.assertEqual(
            h.get_key_hash({"key": "value"}),
            "37e13e1116c86a6e9f3f8926375c7cb977ca74d2d598572ced03cd09",
        )

    def test_filehandler_get_key_hash_s3(self):
        from pewtils.io import FileHandler

        if os.environ.get("S3_BUCKET"):
            h = FileHandler("tests/files", use_s3=True)
            self.assertEqual(
                h.get_key_hash("temp"),
                "c51bf90ccb22befa316b7a561fe9d5fd9650180b14421fc6d71bcd57",
            )
            self.assertEqual(
                h.get_key_hash({"key": "value"}),
                "37e13e1116c86a6e9f3f8926375c7cb977ca74d2d598572ced03cd09",
            )

    def test_filehandler_read_write_pkl(self):
        from pewtils.io import FileHandler

        h = FileHandler("tests/files", use_s3=False)
        h.write("temp", self.test_df, format="pkl")
        read = h.read("temp", format="pkl")
        import os

        os.unlink("tests/files/temp.pkl")
        self.assertEqual(repr(self.test_df), repr(read))

    def test_filehandler_read_write_pkl_s3(self):
        from pewtils.io import FileHandler

        if os.environ.get("S3_BUCKET"):
            h = FileHandler("tests/files", use_s3=True)
            h.write("temp", self.test_df, format="pkl")
            read = h.read("temp", format="pkl")
            self.assertEqual(repr(self.test_df), repr(read))

    def test_filehandler_read_write_csv(self):
        from pewtils.io import FileHandler

        h = FileHandler("tests/files", use_s3=False)
        h.write("temp", self.test_df, format="csv")
        read = h.read("temp", format="csv")
        del read["Unnamed: 0"]
        import os

        os.unlink("tests/files/temp.csv")
        self.assertEqual(repr(self.test_df), repr(read))

    def test_filehandler_read_write_csv_s3(self):
        from pewtils.io import FileHandler

        if os.environ.get("S3_BUCKET"):
            h = FileHandler("tests/files", use_s3=True)
            h.write("temp", self.test_df, format="csv")
            read = h.read("temp", format="csv")
            del read["Unnamed: 0"]
            self.assertEqual(repr(self.test_df), repr(read))

    def test_filehandler_read_write_txt(self):
        from pewtils.io import FileHandler

        h = FileHandler("tests/files", use_s3=False)
        h.write("temp", "test", format="txt")
        read = h.read("temp", format="txt")
        import os

        os.unlink("tests/files/temp.txt")
        self.assertEqual(read, "test")

    def test_filehandler_read_write_txt_s3(self):
        from pewtils.io import FileHandler

        if os.environ.get("S3_BUCKET"):
            h = FileHandler("tests/files", use_s3=True)
            h.write("temp", "test", format="txt")
            read = h.read("temp", format="txt")
            self.assertEqual(read, "test")

    def test_filehandler_read_write_tab(self):
        from pewtils.io import FileHandler

        h = FileHandler("tests/files", use_s3=False)
        h.write("temp", self.test_df, format="tab")
        read = h.read("temp", format="tab")
        del read["Unnamed: 0"]
        import os

        os.unlink("tests/files/temp.tab")
        self.assertEqual(repr(self.test_df), repr(read))

    def test_filehandler_read_write_tab_s3(self):
        from pewtils.io import FileHandler

        if os.environ.get("S3_BUCKET"):
            h = FileHandler("tests/files", use_s3=True)
            h.write("temp", self.test_df, format="tab")
            read = h.read("temp", format="tab")
            del read["Unnamed: 0"]
            self.assertEqual(repr(self.test_df), repr(read))

    def test_filehandler_read_write_xlsx(self):
        from pewtils.io import FileHandler

        h = FileHandler("tests/files", use_s3=False)
        h.write("temp", self.test_df, format="xlsx")
        read = h.read("temp", format="xlsx")
        if "Unnamed: 0" in read.columns:
            del read["Unnamed: 0"]
        import os

        os.unlink("tests/files/temp.xlsx")
        self.assertEqual(repr(self.test_df), repr(read))

    def test_filehandler_read_write_xlsx_s3(self):
        from pewtils.io import FileHandler

        if os.environ.get("S3_BUCKET"):
            h = FileHandler("tests/files", use_s3=True)
            h.write("temp", self.test_df, format="xlsx")
            read = h.read("temp", format="xlsx")
            if "Unnamed: 0" in read.columns:
                del read["Unnamed: 0"]
            self.assertEqual(repr(self.test_df), repr(read))

    def test_filehandler_read_write_xls(self):
        from pewtils.io import FileHandler

        h = FileHandler("tests/files", use_s3=False)
        h.write("temp", self.test_df, format="xls")
        read = h.read("temp", format="xls")
        if "Unnamed: 0" in read.columns:
            del read["Unnamed: 0"]
        import os

        os.unlink("tests/files/temp.xls")
        self.assertEqual(repr(self.test_df), repr(read))

    def test_filehandler_read_write_xl_s3(self):
        from pewtils.io import FileHandler

        if os.environ.get("S3_BUCKET"):
            h = FileHandler("tests/files", use_s3=True)
            h.write("temp", self.test_df, format="xls")
            read = h.read("temp", format="xls")
            if "Unnamed: 0" in read.columns:
                del read["Unnamed: 0"]
            self.assertEqual(repr(self.test_df), repr(read))

    def test_filehandler_read_write_dta(self):
        from pewtils.io import FileHandler

        h = FileHandler("tests/files", use_s3=False)
        h.write("temp", self.test_df, format="dta")
        read = h.read("temp", format="dta")
        del read["index"]
        import os

        os.unlink("tests/files/temp.dta")
        self.assertEqual(repr(self.test_df), repr(read))

    def test_filehandler_read_write_dta_s3(self):
        from pewtils.io import FileHandler

        if os.environ.get("S3_BUCKET"):
            h = FileHandler("tests/files", use_s3=True)
            h.write("temp", self.test_df, format="dta")
            read = h.read("temp", format="dta")
            del read["index"]
            self.assertEqual(repr(self.test_df), repr(read))

    def test_filehandler_read_write_json(self):
        from pewtils.io import FileHandler

        h = FileHandler("tests/files", use_s3=False)
        h.write("temp", self.test_json, format="json")
        read = h.read("temp", format="json")
        import os

        os.unlink("tests/files/temp.json")
        self.assertEqual(repr(self.test_json), repr(dict(read)))

    def test_filehandler_read_write_json_s3(self):
        from pewtils.io import FileHandler

        if os.environ.get("S3_BUCKET"):
            h = FileHandler("tests/files", use_s3=True)
            h.write("temp", self.test_json, format="json")
            read = h.read("temp", format="json")
            self.assertEqual(repr(self.test_json), repr(dict(read)))

    def tearDown(self):

        import os

        try:
            os.unlink("tests/files/temp/temp.txt")
        except OSError:
            pass
        for format in ["pkl", "csv", "tab", "txt", "xlsx", "xls", "dta", "json"]:
            try:
                os.unlink("tests/files/temp.{}".format(format))
            except OSError:
                pass
        try:
            os.rmdir("tests/files/temp")
        except OSError:
            pass

        from pewtils.io import FileHandler

        if os.environ.get("S3_BUCKET"):
            h = FileHandler("tests/files", use_s3=True)
            for file in h.iterate_path():
                if "." in file:
                    filename, format = file.split(".")
                    h.clear_file(filename, format=format)
