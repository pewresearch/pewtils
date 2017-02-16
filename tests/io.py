from __future__ import print_function
import unittest


class IOTests(unittest.TestCase):
    """
    To test, navigate to pewtils root folder and run `python -m unittest tests`
    """
    def setUp(self):
        import pandas as pd
        self.test_df = pd.DataFrame([
            {"test": 1},
            {"test": 2},
            {"test": 3},
            {"test": 5}
        ])
        self.test_json = {
            "test1": 1,
            "test2": 2,
            "test3": 3,
            "test4": 4
        }
        import json
        test_json = json.dumps(self.test_json)
        self.test_json = json.loads(test_json)

    def test_filehandler_iterate_path(self):
        from pewtils.io import FileHandler
        h = FileHandler("tests/files", use_s3=False)
        files = []
        for file in h.iterate_path():
            files.append(file)
        files = [f for f in files if not f.endswith(".pyc")]
        self.assertTrue(files == ['subfolder', '__init__.py', 'example.html', 'example_stripped_simple.html',
                                  'json.json', 'example_stripped.html', 'py.py'])

    def test_filehandler_clear_folder(self):
        from pewtils.io import FileHandler
        h = FileHandler("tests/files/temp", use_s3=False)
        from contextlib import closing
        with closing(open("tests/files/temp/temp.txt", "wb")) as output:
            output.write("test")
        h.clear_folder()
        files = []
        for file in h.iterate_path():
            files.append(file)
        self.assertTrue(len(files) == 0)
        import os
        os.rmdir("tests/files/temp")

    def test_filehandler_get_key_hash(self):
        from pewtils.io import FileHandler
        h = FileHandler("tests/files", use_s3=False)
        self.assertTrue(h.get_key_hash("temp") == "c51bf90ccb22befa316b7a561fe9d5fd9650180b14421fc6d71bcd57")

    def test_filehandler_read_write_pkl(self):
        from pewtils.io import FileHandler
        h = FileHandler("tests/files", use_s3=False)
        h.write("temp", self.test_df, format="pkl")
        read = h.read("temp", format="pkl")
        import os
        os.unlink("tests/files/temp.pkl")
        self.assertTrue(repr(self.test_df) == repr(read))

    def test_filehandler_read_write_csv(self):
        from pewtils.io import FileHandler
        h = FileHandler("tests/files", use_s3=False)
        h.write("temp", self.test_df, format="csv")
        read = h.read("temp", format="csv")
        del read['Unnamed: 0']
        import os
        os.unlink("tests/files/temp.csv")
        self.assertTrue(repr(self.test_df) == repr(read))

    def test_filehandler_read_write_txt(self):
        from pewtils.io import FileHandler
        h = FileHandler("tests/files", use_s3=False)
        h.write("temp", "test", format="txt")
        read = h.read("temp", format="txt")
        import os
        os.unlink("tests/files/temp.txt")
        self.assertTrue(read == "test")

    def test_filehandler_read_write_tab(self):
        from pewtils.io import FileHandler
        h = FileHandler("tests/files", use_s3=False)
        h.write("temp", self.test_df, format="tab")
        read = h.read("temp", format="tab")
        del read['Unnamed: 0']
        import os
        os.unlink("tests/files/temp.tab")
        self.assertTrue(repr(self.test_df) == repr(read))

    def test_filehandler_read_write_xlsx(self):
        from pewtils.io import FileHandler
        h = FileHandler("tests/files", use_s3=False)
        h.write("temp", self.test_df, format="xlsx")
        read = h.read("temp", format="xlsx")
        import os
        os.unlink("tests/files/temp.xlsx")
        self.assertTrue(repr(self.test_df) == repr(read))

    def test_filehandler_read_write_xls(self):
        from pewtils.io import FileHandler
        h = FileHandler("tests/files", use_s3=False)
        h.write("temp", self.test_df, format="xls")
        read = h.read("temp", format="xls")
        import os
        os.unlink("tests/files/temp.xls")
        self.assertTrue(repr(self.test_df) == repr(read))

    def test_filehandler_read_write_dta(self):
        from pewtils.io import FileHandler
        h = FileHandler("tests/files", use_s3=False)
        h.write("temp", self.test_df, format="dta")
        read = h.read("temp", format="dta")
        del read['index']
        import os
        os.unlink("tests/files/temp.dta")
        self.assertTrue(repr(self.test_df) == repr(read))

    def test_filehandler_read_write_json(self):
        from pewtils.io import FileHandler
        h = FileHandler("tests/files", use_s3=False)
        h.write("temp", self.test_json, format="json")
        read = h.read("temp", format="json")
        import os
        os.unlink("tests/files/temp.json")
        self.assertTrue(repr(self.test_json) == repr(dict(read)))

    def tearDown(self):
        pass