"""Tests for r.stream.basins stream-category bounds checking.

Regression tests for GH #1828: categories[] in basins_inputs.c is
allocated with exactly (highest stream category + 1) elements, so the
value one past the highest actual category (number_of_streams) is one
past the last valid index. The old bounds check let that value through
and wrote past the end of the allocation; the fix rejects it instead.
"""

import pytest

import grass.script as gs
from grass.tools import ToolError


def test_cats_at_max_category_creates_basin(basins_env):
    """The highest actual stream category is a valid cats value."""
    tools = basins_env.tools
    session = basins_env.session
    max_category = int(gs.raster_info("streams", env=session.env)["max"])

    tools.r_stream_basins(
        direction="direction",
        stream_rast="streams",
        cats=str(max_category),
        basins="basins",
    )

    info = gs.raster_info("basins", env=session.env)
    assert info["max"] is not None


def test_cats_above_max_category_is_rejected(basins_env):
    """One past the highest stream category must be rejected, not overflow."""
    tools = basins_env.tools
    session = basins_env.session
    max_category = int(gs.raster_info("streams", env=session.env)["max"])
    number_of_streams = max_category + 1

    with pytest.raises(ToolError, match="Stream category must be between 1 and"):
        tools.r_stream_basins(
            direction="direction",
            stream_rast="streams",
            cats=str(number_of_streams),
            basins="basins_invalid",
        )
