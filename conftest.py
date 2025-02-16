from pathlib import Path
import pytest

import os
import shutil
import sys

import pytest


def _win32_longpath(path):
    """
    Helper function to add the long path prefix for Windows, so that shutil.copytree
     won't fail while working with paths with 255+ chars.

    From: https://github.com/gabrielcnr/pytest-datadir/blob/4c6557e4b4e33dc1fc0645dfc43bbe0527733c17/src/pytest_datadir/plugin.py#L8-L30
    Pytest plugin: "pytest-datadir"
    Author of pytest plugin: "Gabriel Reis"
    License of plugin: MIT
    """
    if sys.platform == "win32":
        # The use of os.path.normpath here is necessary since "the "\\?\" prefix
        # to a path string tells the Windows APIs to disable all string parsing
        # and to send the string that follows it straight to the file system".
        # (See https://docs.microsoft.com/pt-br/windows/desktop/FileIO/naming-a-file)
        normalized = os.path.normpath(path)
        if not normalized.startswith("\\\\?\\"):
            is_unc = normalized.startswith("\\\\")
            # see https://en.wikipedia.org/wiki/Path_(computing)#Universal_Naming_Convention # noqa: E501
            if (
                is_unc
            ):  # then we need to insert an additional "UNC\" to the longpath prefix
                normalized = normalized.replace("\\\\", "\\\\?\\UNC\\")
            else:
                normalized = "\\\\?\\" + normalized
        return normalized
    else:
        return path


@pytest.fixture(autouse=True)
def gunittest_datadir(
    monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest, tmp_path: Path
):
    # breakpoint()
    # original_shared_path = request.path.parent / "data"
    original_shared_path = os.path.join(request.path.parent, "data")
    # if (original_shared_path.is_dir())
    # if os.path.isdir(original_shared_path) and os.path.dirname(original_shared_path) :
    if (
        os.path.isdir(original_shared_path)
        and os.path.basename(os.path.dirname(original_shared_path)) == "testsuite"
    ):
        # adirname = os.path.basename(os.path.dirname(original_shared_path))
        # print(adirname)
        # breakpoint()
        temp_path = tmp_path / "data"
        shutil.copytree(
            _win32_longpath(original_shared_path), _win32_longpath(str(temp_path))
        )
        # breakpoint()
        # return temp_path
        # monkeypatch.chdir(temp_path.parent)
    # else:
    #     request.cls.gunittest_datadir_dir = tmp_path
    monkeypatch.chdir(tmp_path)
    # pass
