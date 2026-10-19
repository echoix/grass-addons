"""Tests for running the g.citation tool

These tests use the documentation installed with GRASS GIS, so they check
only what does not depend on the content of a particular manual page. The
parsing itself is tested in g_citation_parsing_test.py.
"""

import json
import os
import stat

import pytest

# Long-standing core tool used as an example of an installed manual page.
TOOL = "g.region"


def test_default_format_is_bibtex(tools):
    result = tools.g_citation(module=TOOL)
    assert result.returncode == 0
    assert result.text.startswith("@misc{g_region,")
    assert "title = {{GRASS GIS: g.region module}}," in result.text


def test_json_format(tools):
    citation = json.loads(tools.g_citation(module=TOOL, format="json").stdout)
    assert citation["module"] == TOOL
    assert citation["authors"]


def test_several_modules_in_one_run(tools):
    text = tools.g_citation(module=[TOOL, "g.list"], format="plain").text
    assert "GRASS GIS module g.region" in text
    assert "GRASS GIS module g.list" in text


def test_vertical_separator(tools):
    text = tools.g_citation(
        module=[TOOL, "g.list"], format="plain", vertical_separator="---"
    ).text
    assert text.count("---") == 2


def test_grass_as_reference(tools):
    """The -d flag adds GRASS GIS as a reference to the CFF output"""
    text = tools.g_citation(module=TOOL, format="cff", flags="d").text
    assert "references:" in text
    assert "name: The GRASS Development Team" in text


def test_output_file(tools, tmp_path):
    """The output file contains what would otherwise be printed"""
    output_file = tmp_path / "citation.bib"
    result = tools.g_citation(module=TOOL, output=output_file)
    assert result.returncode == 0
    assert not result.text
    assert output_file.read_text() == tools.g_citation(module=TOOL).stdout


def test_unknown_module(tools):
    result = tools.g_citation(module="x.does.not.exist")
    assert result.returncode != 0
    assert "No HTML manual page entry" in result.stderr


def test_output_file_in_missing_directory(tools, tmp_path):
    result = tools.g_citation(module=TOOL, output=tmp_path / "missing" / "citation.bib")
    assert result.returncode != 0
    assert "No such file or directory" in result.stderr


@pytest.mark.skipif(
    hasattr(os, "geteuid") and os.geteuid() == 0,
    reason="The root user can write to a read-only file",
)
def test_output_file_which_cannot_be_written(tools, tmp_path):
    output_file = tmp_path / "citation.bib"
    output_file.touch()
    output_file.chmod(stat.S_IRUSR)
    result = tools.g_citation(module=TOOL, output=output_file)
    assert result.returncode != 0
    assert "Permission denied" in result.stderr


def test_all_modules(tools):
    """Citations are collected for all tools of the installation

    The -s flag is used because a manual page which the tool cannot parse
    is a problem of that tool, not of g.citation, and because which tools
    are installed depends on the installation.
    """
    result = tools.g_citation(flags="as")
    assert result.returncode == 0
    assert result.text.count("@misc{") > 1
    assert "@misc{g_region," in result.text
