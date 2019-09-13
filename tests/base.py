from __future__ import print_function
import unittest


class BaseTests(unittest.TestCase):

    """
    To test, navigate to pewtils root folder and run `python -m unittest tests`
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
        text = decode_text(u'ko\u017eu\u0161\u010dek')
        self.assertEqual(text, "kozuscek")
        text = decode_text(u'30 \U0001d5c4\U0001d5c6/\U0001d5c1')
        self.assertIn(text, ["30 km/h", "30 /"])
        # Python 2.7 does not have support for UTF-16 so it will fail on the above
        text = decode_text(u"\u5317\u4EB0")
        self.assertEqual(text, "Bei Jing ")
        text = decode_text(datetime.date(2019, 1, 1))
        self.assertEqual(text, "2019-01-01")
        text = decode_text(None)
        self.assertEqual(text, '')
        text = decode_text("")
        self.assertEqual(text, "")
        text = decode_text(np.nan)
        self.assertEqual(text, '')
        text = decode_text(FakeObject())
        self.assertEqual(text, 'str')


    def test_is_null(self):

        import numpy as np
        from pewtils import is_null, is_not_null
        for val in [None, "None", "nan", "", " ", "NaN", "none", "n/a", "NONE", "N/A"]:
            self.assertTrue(is_null(val))
        self.assertTrue(is_null(np.nan))
        self.assertTrue(is_not_null(0.0))
        self.assertTrue(is_null("-9", custom_nulls=["-9"]))
        self.assertTrue(is_null([], empty_lists_are_null=True))

    def test_recursive_update(self):
        from pewtils import recursive_update
        class TestObject(object):
            def __init__(self, val):
                self.val = val
                self.val_dict = {"key": "value"}
        test_obj = TestObject("1")
        base = {
            "level1": {
                "level2": {
                    "val2": "test2"
                },
                "val1": "test1",
                "val2": test_obj
            }
        }
        update = {
            "level1": {
                "level2": {
                    "val2": "test123456"
                },
                "val1": "test123",
                "val2": {
                    "val": "2",
                    "val_dict": {"key": "new_value"}
                }
            }
        }
        result = recursive_update(base, update)
        self.assertEqual(result['level1']['level2']['val2'], "test123456")
        self.assertEqual(result['level1']['val1'], "test123")
        self.assertEqual(result['level1']['val2'].val, "2")
        self.assertEqual(result['level1']['val2'].val_dict['key'], 'new_value')

    def test_chunk_list(self):
        from pewtils import chunk_list
        test = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        chunked = [c for c in chunk_list(test, 3)]
        self.assertTrue(len(chunked) == 4)
        self.assertTrue(chunked[-1] == [10])

    def test_extract_json_from_folder(self):
        from pewtils import extract_json_from_folder
        results = extract_json_from_folder("tests/files", include_subdirs=False, concat_subdir_names=False)
        self.assertTrue(results == {'json': {u'test_val': 1}})
        results = extract_json_from_folder("tests/files", include_subdirs=True, concat_subdir_names=False)
        self.assertTrue(results == {'json': {u'test_val': 1}, 'subfolder': {'subfolder': {u'test_val': 2}}})
        results = extract_json_from_folder("tests/files", include_subdirs=True, concat_subdir_names=True)
        self.assertTrue(results == {'json': {u'test_val': 1}, 'subfolder_subfolder': {u'test_val': 2}})

    def test_extract_attributes_from_folder_modules(self):
        from pewtils import extract_attributes_from_folder_modules
        results = extract_attributes_from_folder_modules("tests/files", "test")
        self.assertTrue(results['py']() == "test1")
        results = extract_attributes_from_folder_modules("tests/files", "test", include_subdirs=True)
        self.assertTrue(results['py']() == "test1")
        self.assertTrue(results['subfolder']['subfolder_py']() == "test2")
        results = extract_attributes_from_folder_modules("tests/files", "test", include_subdirs=True, concat_subdir_names=True)
        self.assertTrue(results['py']() == "test1")
        self.assertTrue(results['subfolder_subfolder_py']() == "test2")

    def test_flatten_list(self):
        from pewtils import flatten_list
        results = flatten_list([[1, 2, 3], [4, 5, 6]])
        self.assertTrue(results == [1, 2, 3, 4, 5, 6])

    def test_get_hash(self):
        from pewtils import get_hash
        text = "test_string"
        hash = get_hash(text, hash_function="nilsimsa")
        self.assertTrue(hash == "49c808104092202004009004800200084a0240a0c09040a1113a04a821210016")
        hash = get_hash(text, hash_function = "md5")
        self.assertTrue(hash == "3474851a3410906697ec77337df7aae4")
        hash = get_hash(text, hash_function = "ssdeep")
        self.assertTrue(hash == "3:HI2:Hl")

    def test_concat_text(self):
        from pewtils import concat_text
        result = concat_text(
            "one two three",
            u'ko\u017eu\u0161\u010dek',
            u"\u5317\u4EB0",
            None
        )
        self.assertEqual(result, "one two three kozuscek Bei Jing ")

    def test_cached_series_mapper(self):
        import pandas as pd
        from pewtils import cached_series_mapper
        df = pd.DataFrame([
            {"test": 1},
            {"test": 2},
            {"test": 3},
            {"test": 3}
        ])
        df['mapped'] = cached_series_mapper(df['test'], lambda x: str(float(x)))
        self.assertTrue(list(df['mapped'].values) == ["1.0", "2.0", "3.0", "3.0"])

    def test_scale_range(self):
        from pewtils import scale_range
        self.assertTrue(int(scale_range(10, 3, 12, 0, 20)) == 15)

    def test_scan_dictionary(self):
        from pewtils import scan_dictionary
        test_dict = {
            "one": {
                "two": {
                    "three": "woot"
                }
            }
        }
        vals, paths = scan_dictionary(test_dict, "three")
        self.assertEqual(vals[0], "woot")
        self.assertEqual(paths[0], "one/two/three/")

    def tearDown(self):
        pass


