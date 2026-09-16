"""Tests for the citation formats of g.citation

The formats are checked on a fixed citation, so that the tests do not
depend on the documentation of any particular tool.
"""

import io
import json

import pytest


@pytest.fixture
def entry():
    """Citation of a tool with two authors as collected from a manual page"""
    return {
        "module": "x.fake",
        "authors": [
            {
                "name": "Ann Doe",
                "institute": "Small University",
                "feature": None,
                "email": None,
                "orcid": "0000-0000-0000-0001",
            },
            {
                "name": "John Roe",
                "institute": None,
                "feature": "Speed improvements",
                "email": None,
                "orcid": None,
            },
        ],
        "year": 2021,
        "access": "2021-06-28T11:54:09",
        "code-url": "https://example.org/tree/x.fake",
        "url-code-history": "https://example.org/commits/x.fake",
        "grass-version": "8.4.0",
        "grass-build-date": "2024-01-31",
        "keywords": ["general", "citation"],
    }


def formatted(citation, entry, format, **kwargs):
    """Text produced by the tool for the given citation and format"""
    output = io.StringIO()
    citation.print_citation(entry, format, output, **kwargs)
    return output.getvalue()


def test_bibtex(citation, entry):
    assert formatted(citation, entry, "bibtex") == (
        "@misc{x_fake,\n"
        "  title = {{GRASS GIS: x.fake module}},\n"
        "  author = {Ann Doe and John Roe},\n"
        "  howpublished = {https://example.org/tree/x.fake},\n"
        "  year = {2021},\n"
        "  note = {Accessed: 2021-06-28T11:54:09},\n"
        "}\n"
    )


def test_cff(citation, entry):
    assert formatted(citation, entry, "cff") == (
        "cff-version: 1.0.3\n"
        'message: "If you use this software, please cite it as below."\n'
        "authors:\n"
        "  - family-names: Doe\n"
        "    given-names: Ann\n"
        "    orcid: 0000-0000-0000-0001\n"
        "  - family-names: Roe\n"
        "    given-names: John\n"
        'title: "GRASS GIS: x.fake module"\n'
        "version: 8.4.0\n"
        "date-released: 2024-01-31\n"
        "license: GPL-2.0-or-later\n"
        "keywords:\n"
        "  - general\n"
        "  - citation\n"
    )


def test_cff_with_grass_as_reference(citation, entry):
    """The -d flag adds GRASS GIS itself as a reference"""
    entry["references"] = [
        citation.grass_cff_reference(
            {"version": "8.4.0", "build_date": "2024-01-31", "date": "2024"},
            scope="Use the following to cite the whole GRASS GIS",
        )
    ]
    text = formatted(citation, entry, "cff")
    assert "references:\n" in text
    assert "  - scope: Use the following to cite the whole GRASS GIS\n" in text
    assert "    type: software\n" in text
    assert "    title: GRASS GIS 8.4.0\n" in text
    assert "      - name: The GRASS Development Team\n" in text


def test_plain(citation, entry):
    assert formatted(citation, entry, "plain") == (
        "GRASS GIS module x.fake\n"
        "Ann Doe, Small University\n"
        "John Roe (Speed improvements)\n"
    )


def test_chicago_footnote(citation, entry):
    assert formatted(citation, entry, "chicago-footnote") == (
        "Ann Doe, and John Roe, GRASS GIS module x.fake (8.4.0),"
        " computer software (2021).\n"
    )


def test_json(citation, entry):
    """Compact JSON is a dump of the collected citation without empty values"""
    text = formatted(citation, entry, "json")
    data = json.loads(text)
    # The compact format has no spaces after the separators.
    assert text == json.dumps(data, separators=(",", ":")) + "\n"
    assert data["module"] == "x.fake"
    assert data["authors"][0]["orcid"] == "0000-0000-0000-0001"
    assert "email" not in data["authors"][0]


def test_pretty_json_is_sorted(citation, entry):
    data = json.loads(formatted(citation, entry, "pretty-json"))
    assert data == json.loads(formatted(citation, entry, "json"))
    keys = list(data.keys())
    assert keys == sorted(keys)


def test_csl_json(citation, entry):
    data = json.loads(formatted(citation, entry, "csl-json"))
    assert data["id"] == "x.fake"
    assert data["type"] == "software"
    assert data["title"] == "GRASS GIS: x.fake module"
    assert data["author"] == [
        {"family": "Doe", "given": "Ann"},
        {"family": "Roe", "given": "John"},
    ]
    assert data["issued"]["date-parts"][0][0] == 2021


def test_dict(citation, entry):
    """The dict format shows everything which was collected, including gaps"""
    text = formatted(citation, entry, "dict")
    assert "'email': None" in text
    assert "'name': 'Ann Doe'" in text


def test_unsupported_format(citation, entry):
    with pytest.raises(RuntimeError, match="Unsupported format"):
        formatted(citation, entry, "no-such-format")
