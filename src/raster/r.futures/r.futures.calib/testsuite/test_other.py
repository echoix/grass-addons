# # import unittest
# import unittest
# import pytest


# class MyTest(unittest.TestCase):
#     @pytest.fixture(autouse=True)
#     def initdir(self, tmp_path, monkeypatch):
#         monkeypatch.chdir(tmp_path)  # change to pytest-provided temporary directory
#         tmp_path.joinpath("samplefile.ini").write_text("# testdata", encoding="utf-8")

#     def test_method(self):
#         with open("samplefile.ini", encoding="utf-8") as f:
#             s = f.read()
#         assert "testdata" in s


# @pytest.mark.usefixtures("datadir", "shared_datadir")
# class TestExample(unittest.TestCase):
#     def test_read_global(self):
#         contents = (self.shared_datadir / "hello.txt").read_text()
#         self.assertEqual(contents, "Hello World!\n")

#     def test_read_module(self):
#         contents = (self.datadir / "spam.txt").read_text()
#         self.assertEqual(contents, "eggs\n")


# # @pytest.mark.usefixtures("datadir", "shared_datadir")
# # class TestExample(unittest.TestCase):
# #     def test_read_global(self, shared_datadir):
# #         contents = (shared_datadir / "hello.txt").read_text()
# #         self.assertEqual(contents, "Hello World!\n")

# #     def test_read_module(self, datadir):
# #         contents = (datadir / "spam.txt").read_text()
# #         self.assertEqual(contents, "eggs\n")


# # class TestExample(unittest.TestCase):
# #     def test_read_global(self, shared_datadir):
# #         contents = (shared_datadir / "hello.txt").read_text()
# #         self.assertEqual(contents, "Hello World!\n")

# #     def test_read_module(self, datadir):
# #         contents = (datadir / "spam.txt").read_text()
# #         self.assertEqual(contents, "eggs\n")
