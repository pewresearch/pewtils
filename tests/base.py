import unittest


class BaseTests(unittest.TestCase):

    """
    To test, navigate to pewtils root folder and run `python -m unittest tests`.
    To assess unit test coverage, run `coverage run -m unittest tests` and then `coverage report -m`.
    """

    def setUp(self):
        pass

    def test_decode_text(self):
        class FakeObject(object):
            def __str__(self):
                return "str"

            def __repr__(self):
                return "repr"

        import datetime
        import numpy as np
        from pewtils import decode_text

        text = decode_text("one two three")
        self.assertEqual(text, "one two three")
        # below examples taken from unidecode documentation
        text = decode_text(u"ko\u017eu\u0161\u010dek")
        self.assertEqual(text, "kozuscek")
        text = decode_text(u"30 \U0001d5c4\U0001d5c6/\U0001d5c1")
        self.assertIn(text, ["30 km/h", "30 /"])
        # Python 2.7 does not have support for UTF-16 so it will fail on the above
        text = decode_text(u"\u5317\u4EB0")
        self.assertEqual(text, "Bei Jing ")
        text = decode_text(datetime.date(2019, 1, 1))
        self.assertEqual(text, "2019-01-01")
        text = decode_text(None)
        self.assertEqual(text, "")
        text = decode_text("")
        self.assertEqual(text, "")
        text = decode_text(np.nan)
        self.assertEqual(text, "")
        text = decode_text(FakeObject())
        self.assertEqual(text, "str")

    def test_is_null(self):

        import numpy as np
        import pandas as pd
        from pewtils import is_null, is_not_null

        for val in [None, "None", "nan", "", " ", "NaN", "none", "n/a", "NONE", "N/A"]:
            self.assertTrue(is_null(val))
        self.assertTrue(is_null(np.nan))
        self.assertTrue(is_not_null(0.0))
        self.assertTrue(is_null("-9", custom_nulls=["-9"]))
        self.assertTrue(is_null([], empty_lists_are_null=True))
        self.assertFalse(is_null([], empty_lists_are_null=False))
        self.assertTrue(is_null(pd.Series(), empty_lists_are_null=True))
        self.assertFalse(is_null(pd.Series(), empty_lists_are_null=False))
        self.assertTrue(is_null(pd.DataFrame(), empty_lists_are_null=True))
        self.assertFalse(is_null(pd.DataFrame(), empty_lists_are_null=False))

    def test_recursive_update(self):
        from pewtils import recursive_update

        class TestObject(object):
            def __init__(self, val):
                self.val = val
                self.val_dict = {"key": "value"}

        test_obj = TestObject("1")
        base = {
            "level1": {"level2": {"val2": "test2"}, "val1": "test1", "val2": test_obj}
        }
        update = {
            "level1": {
                "level2": {"val2": "test123456"},
                "val1": "test123",
                "val2": {"val": "2", "val_dict": {"key": "new_value"}},
                "val3": {"test": "test"},
            }
        }
        result = recursive_update(base, update)
        self.assertEqual(result["level1"]["level2"]["val2"], "test123456")
        self.assertEqual(result["level1"]["val1"], "test123")
        self.assertEqual(result["level1"]["val2"].val, "2")
        self.assertEqual(result["level1"]["val2"].val_dict["key"], "new_value")
        self.assertEqual(result["level1"]["val3"]["test"], "test")

    def test_chunk_list(self):
        from pewtils import chunk_list

        test = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        chunked = [c for c in chunk_list(test, 3)]
        self.assertEqual(len(chunked), 4)
        self.assertEqual(chunked[-1], [10])

    def test_extract_json_from_folder(self):
        from pewtils import extract_json_from_folder

        results = extract_json_from_folder(
            "tests/files", include_subdirs=False, concat_subdir_names=False
        )
        self.assertEqual(results, {"json": {u"test_val": 1}})
        results = extract_json_from_folder(
            "tests/files", include_subdirs=True, concat_subdir_names=False
        )
        self.assertEqual(
            results,
            {"json": {u"test_val": 1}, "subfolder": {"subfolder": {u"test_val": 2}}},
        )
        results = extract_json_from_folder(
            "tests/files", include_subdirs=True, concat_subdir_names=True
        )
        self.assertEqual(
            results, {"json": {u"test_val": 1}, "subfolder_subfolder": {u"test_val": 2}}
        )

    def test_extract_attributes_from_folder_modules(self):
        from pewtils import extract_attributes_from_folder_modules

        results = extract_attributes_from_folder_modules("tests/files", "test")
        self.assertEqual(results["py"](), "test1")
        results = extract_attributes_from_folder_modules(
            "tests/files", "test", include_subdirs=True
        )
        self.assertEqual(results["py"](), "test1")
        self.assertEqual(results["subfolder"]["subfolder_py"](), "test2")
        results = extract_attributes_from_folder_modules(
            "tests/files", "test", include_subdirs=True, concat_subdir_names=True
        )
        self.assertEqual(results["py"](), "test1")
        self.assertEqual(results["subfolder_subfolder_py"](), "test2")

    def test_zipcode_num_to_string(self):

        from pewtils import zipcode_num_to_string

        for val in [20002, 20002.0, "20002", "20002.0"]:
            zip = zipcode_num_to_string(val)
            self.assertEqual(zip, "20002")
        for val in ["abcde", "12", "99999", "200", "1.0", None]:
            zip = zipcode_num_to_string(val)
            self.assertIsNone(zip)

    def test_flatten_list(self):
        from pewtils import flatten_list

        results = flatten_list([[1, 2, 3], [4, 5, 6]])
        self.assertEqual(results, [1, 2, 3, 4, 5, 6])

    def test_get_hash(self):
        from pewtils import get_hash

        for text, method, expected_value in [
            (
                "test_string",
                "nilsimsa",
                "49c808104092202004009004800200084a0240a0c09040a1113a04a821210016",
            ),
            ("test_string", "md5", "3474851a3410906697ec77337df7aae4"),
            ("test_string", "ssdeep", "3:HI2:Hl"),
            (
                u"\u5317\u4EB0",
                "nilsimsa",
                "0100000044110004290804002820001002844001200601000101002800394081",
            ),
            (u"\u5317\u4EB0", "md5", "3261ad50fccf7ced43d944bbfd2acb5c"),
            (u"\u5317\u4EB0", "ssdeep", "3:I2n:l"),
        ]:
            hash = get_hash(text, hash_function=method)
            self.assertEqual(hash, expected_value)

    def test_concat_text(self):
        from pewtils import concat_text

        result = concat_text(
            "one two three", u"ko\u017eu\u0161\u010dek", u"\u5317\u4EB0", None
        )
        self.assertEqual(result, "one two three kozuscek Bei Jing ")

    def test_vector_concat_text(self):
        from pewtils import vector_concat_text

        result = vector_concat_text(["one", "two", "three"], ["a", "b", "c"])
        self.assertEqual(result[0], "one a")
        self.assertEqual(result[1], "two b")
        self.assertEqual(result[2], "three c")

    def test_cached_series_mapper(self):
        import pandas as pd
        from pewtils import cached_series_mapper

        df = pd.DataFrame([{"test": 1}, {"test": 2}, {"test": 3}, {"test": 3}])
        df["mapped"] = cached_series_mapper(df["test"], lambda x: str(float(x)))
        self.assertEqual(list(df["mapped"].values), ["1.0", "2.0", "3.0", "3.0"])

    def test_multiprocess_group_apply(self):

        import pandas as pd
        from pewtils import multiprocess_group_apply

        df = pd.DataFrame([{"test": 1}, {"test": 2}, {"test": 3}, {"test": 3}])
        df["group"] = [1, 1, 2, 2]

        for add, multiply, expected in [(1, 2, 6), (1, 3, 9), (2, 2, 8)]:
            result = multiprocess_group_apply(
                df.groupby("group"), _test_function_agg, add, multiply=multiply
            )
            self.assertEqual(len(result), 2)
            self.assertEqual((result == expected).astype(int).sum(), 2)

        for add, multiply, expected in [
            (1, 2, [4, 6, 8, 8]),
            (1, 3, [6, 9, 12, 12]),
            (2, 2, [6, 8, 10, 10]),
        ]:

            result = multiprocess_group_apply(
                df.groupby("group"), _test_function_map, add, multiply=multiply
            )
            self.assertEqual(len(result), 4)
            self.assertEqual(list(result.values), expected)

    def test_scale_range(self):
        from pewtils import scale_range

        self.assertEqual(scale_range(10, 5, 25, 0, 10), 2.5)
        self.assertEqual(scale_range(5, 0, 10, 0, 20), 10.0)

    def test_scan_dictionary(self):
        from pewtils import scan_dictionary

        test_dict = {"one": {"two": {"three": "woot"}}}
        vals, paths = scan_dictionary(test_dict, "three")
        self.assertEqual(vals[0], "woot")
        self.assertEqual(paths[0], "one/two/three/")
        vals, paths = scan_dictionary(test_dict, "doesnt_exist")
        self.assertEqual(vals, [])
        self.assertEqual(vals, [])

        test_dict = {
            "one": {
                "two": {"three": "woot"},
                "three": {"four": "five"},
                "six": [{"three": "seven"}],
            }
        }
        vals, paths = scan_dictionary(test_dict, "three")
        self.assertEqual(len(vals), 3)
        self.assertEqual(len(paths), 3)
        self.assertIn("woot", vals)
        self.assertIn({"four": "five"}, vals)
        self.assertIn("seven", vals)
        self.assertIn("one/two/three/", paths)
        self.assertIn("one/three/", paths)
        self.assertIn("one/six/three/", paths)

    def test_new_random_number(self):
        from pewtils import new_random_number
        import numpy as np

        for attempt, minimum, maximum, avg in [
            (1, 1, 2, 1),
            (1, 1, 10, 1),
            (2, 1, 10, 2),
            (3, 1, 10, 4),
            (4, 1, 10, 5),
            (5, 1, 10, 5),
            (1, 2, 2, 2),
            (1, 2, 10, 3),
            (2, 2, 10, 4),
            (3, 2, 10, 5),
            (4, 2, 10, 5),
            (5, 2, 10, 5),
        ]:
            attempts = [
                new_random_number(attempt=attempt, minimum=minimum, maximum=maximum)
                for i in range(500)
            ]
            self.assertGreaterEqual(np.min(attempts), minimum)
            self.assertLessEqual(np.max(attempts), maximum)
            self.assertGreaterEqual(round(np.average(attempts)), avg)

    def test_timeout_wrapper(self):
        from pewtils import timeout_wrapper
        import time

        def test(sleep):
            try:
                with timeout_wrapper(2):
                    time.sleep(sleep)
                return True
            except:
                return False

        self.assertFalse(test(3))
        self.assertTrue(test(1))

    def test_print_execution_time(self):

        import re
        import time
        from io import StringIO
        from pewtils import PrintExecutionTime

        temp = StringIO()
        with PrintExecutionTime(label="my function", stdout=temp):
            time.sleep(5)
        temp.seek(0)
        output = temp.getvalue()
        self.assertIsNotNone(re.match(r"my function: 5\.[0-9]+ seconds", output))

    def tearDown(self):
        pass


def _test_function_agg(grp, add, multiply=1):
    return (len(grp) + add) * multiply


def _test_function_map(grp, add, multiply=1):
    return grp["test"].map(lambda x: (x + add) * multiply)
