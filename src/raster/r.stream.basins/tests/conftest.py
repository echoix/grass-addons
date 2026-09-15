"""Fixtures for the r.stream.basins tests."""

import os
from types import SimpleNamespace

import pytest

import grass.script as gs
from grass.experimental import TemporaryMapsetSession
from grass.tools import Tools


@pytest.fixture(scope="module")
def streams_session(tmp_path_factory):
    """Project with a single-category stream and its flow direction map.

    Built directly with r.mapcalc rather than derived from r.watershed, so
    the stream's only category (1), and hence the exact valid range for
    r.stream.basins' cats option, is known rather than assumed: the bottom
    row of a 3x3 region is one stream flowing east off the map edge, which
    makes it an outlet (there is no cell east of the region to receive it).
    """
    project = tmp_path_factory.mktemp("r_stream_basins") / "project"
    gs.create_project(project, epsg="3358")
    with gs.setup.init(project, env=os.environ.copy()) as session:
        with Tools(session=session) as tools:
            tools.g_region(n=3, s=0, e=3, w=0, res=1)
            tools.r_mapcalc(expression="streams = if(row() == 3, 1, 0)")
            tools.r_mapcalc(expression="direction = 8")
        yield session


@pytest.fixture
def basins_env(streams_session):
    """Isolated per-test mapset over the module-scoped streams data."""
    with TemporaryMapsetSession(env=streams_session.env) as session:
        with Tools(session=session) as tools:
            yield SimpleNamespace(tools=tools, session=session)
