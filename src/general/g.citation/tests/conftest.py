"""Fixtures for the g.citation tests."""

import importlib.util
import os
import sys
from pathlib import Path

import pytest

import grass.script as gs
from grass.tools import Tools

TOOL_PATH = Path(__file__).parent.parent / "g.citation.py"


@pytest.fixture(scope="session")
def citation():
    """The g.citation script imported as a Python module

    The file name is not a valid module name, so the file is loaded by path.
    Importing the script gives the tests access to the parsing and formatting
    functions without running the tool.
    """
    spec = importlib.util.spec_from_file_location("g_citation", TOOL_PATH)
    module = importlib.util.module_from_spec(spec)
    # Registering the module makes doctest able to collect its tests.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    yield module
    del sys.modules[spec.name]


@pytest.fixture(scope="module")
def tools(tmp_path_factory):
    """Tools instance in an empty project

    g.citation reads only documentation files, so no data is needed.
    """
    project = tmp_path_factory.mktemp("g_citation") / "project"
    gs.create_project(project)
    with gs.setup.init(project, env=os.environ.copy()) as session:
        # Errors are checked in the tests, and a result object is needed also
        # for runs which produce no standard output.
        with Tools(
            session=session, errors="ignore", consistent_return_value=True
        ) as session_tools:
            yield session_tools
