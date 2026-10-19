"""Tests for parsing of documentation files by g.citation

The tool derives citations from the generated HTML manual pages, so the
tests feed it manual page fragments in the shape produced by the GRASS
documentation build.
"""

import builtins
import doctest

import pytest

SOURCE_CODE_SECTION = """
<h2>SOURCE CODE</h2>
<p>
  Available at:
  <a href="https://example.org/tree/x.fake">x.fake source code</a>
  (<a href="https://example.org/commits/x.fake">history</a>)
</p>
<p>
  Latest change: Monday Jun 28 11:54:09 2021 in commit: 1cfc0af029a35a5d
</p>
"""


def manual_page(authors):
    """Manual page with the given text as the content of the authors section"""
    return f"""<h2>NAME</h2>
<em><b>x.fake</b></em> - Does nothing
<h2><a name="authors">AUTHORS</a></h2>
{authors}
{SOURCE_CODE_SECTION}"""


def test_doctests(citation, monkeypatch):
    """The doctests of the tool pass

    The tool has its own doctests which are otherwise executed only when it
    is called with the --doctest option.
    """
    # The display hook used by doctest assigns the result of each example to
    # the builtin underscore which the tool uses for translations, so the
    # translation function is restored when the test ends.
    monkeypatch.setattr(builtins, "_", builtins._)
    results = doctest.testmod(citation)
    assert results.attempted
    assert not results.failed


def test_copyright_line_is_not_an_author(citation):
    assert citation.remove_non_author_lines(["Ann Doe", "&copy; 2012", "John Roe"]) == [
        "Ann Doe",
        "John Roe",
    ]


def test_html_tags_are_removed(citation):
    lines = ['<a href="https://example.org">Small University</a>', "Ann Doe<br>"]
    assert citation.remove_html_tags(lines) == ["Small University", "Ann Doe"]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        (" Ann Doe ", "Ann Doe"),
        (",Small University, ", "Small University"),
        ("Ann Doe,", "Ann Doe"),
    ],
)
def test_line_item_is_cleaned(citation, text, expected):
    assert citation.clean_line_item(text) == expected


@pytest.mark.parametrize(
    ("text", "expected_email", "expected_text"),
    [
        ("Ann Doe (ann.doe@example.org)", "ann.doe@example.org", "Ann Doe"),
        # Manual pages obfuscate emails to make harvesting them harder.
        ("Ann Doe (ann.doe example org)", "ann.doe@example.org", "Ann Doe"),
        ("Ann Doe (ann.doe example.org)", "ann.doe@example.org", "Ann Doe"),
        ("Ann Doe", None, "Ann Doe"),
        # Text in parentheses which is not an email is left alone.
        ("Ann Doe (University of Texas)", None, "Ann Doe (University of Texas)"),
    ],
)
def test_email_is_extracted(citation, text, expected_email, expected_text):
    assert citation.get_email(text) == (expected_email, expected_text)


@pytest.mark.parametrize(
    "text",
    [
        "Ann Doe (ORCID: 0000-0000-0000-0001)",
        "Ann Doe ORCID 0000-0000-0000-0001",
        "Ann Doe orcid:0000-0000-0000-0001",
        "Ann Doe https://orcid.org/0000-0000-0000-0001",
    ],
)
def test_orcid_is_extracted(citation, text):
    orcid, remaining_text = citation.get_orcid(text)
    assert orcid == "0000-0000-0000-0001"
    assert remaining_text.startswith("Ann Doe")
    assert "0000-0000-0000-0001" not in remaining_text


def test_text_without_orcid(citation):
    """Text which only mentions ORCID is returned unchanged"""
    text = "orcid: No ORCID here, no here: orcid.org."
    assert citation.get_orcid(text) == (None, text)


def test_single_author(citation):
    (author,) = citation.get_authors_from_documentation(manual_page("Ann Doe"))
    assert author["name"] == "Ann Doe"
    assert author["institute"] is None
    assert author["email"] is None
    assert author["orcid"] is None


def test_institute_follows_the_name(citation):
    (author,) = citation.get_authors_from_documentation(
        manual_page('Ann Doe, <a href="https://example.org">Small University</a>')
    )
    assert author["name"] == "Ann Doe"
    assert author["institute"] == "Small University"


def test_each_author_keeps_own_identifiers(citation):
    """Identifiers are taken from the line of the author they belong to"""
    authors = citation.get_authors_from_documentation(
        manual_page(
            "Ann Doe (ORCID: 0000-0000-0000-0001)<br>"
            "John Roe (john.roe@example.org)<br>"
            "Jane Poe (ORCID: 0000-0000-0000-0002)"
        )
    )
    assert [
        (author["name"], author["orcid"], author["email"]) for author in authors
    ] == [
        ("Ann Doe", "0000-0000-0000-0001", None),
        ("John Roe", None, "john.roe@example.org"),
        ("Jane Poe", "0000-0000-0000-0002", None),
    ]


@pytest.mark.parametrize("separator", [" and ", " &amp; ", " & "])
def test_two_authors_on_one_line(citation, separator):
    authors = citation.get_authors_from_documentation(
        manual_page(f"Ann Doe{separator}John Roe")
    )
    assert [author["name"] for author in authors] == ["Ann Doe", "John Roe"]


def test_academic_title_is_not_part_of_the_name(citation):
    (author,) = citation.get_authors_from_documentation(manual_page("Dr. Ann Doe"))
    assert author["name"] == "Ann Doe"


def test_contribution_is_recorded_as_feature(citation):
    authors = citation.get_authors_from_documentation(
        manual_page("Original version: Ann Doe<br>Improvements by John Roe")
    )
    assert [(author["name"], author["feature"]) for author in authors] == [
        ("Ann Doe", "Original version"),
        ("John Roe", "Improvements"),
    ]


def test_feature_heading_applies_to_following_authors(citation):
    authors = citation.get_authors_from_documentation(
        manual_page("Improvements:<br>Ann Doe<br>John Roe")
    )
    assert [author["feature"] for author in authors] == ["Improvements", "Improvements"]


def test_copyright_line_is_not_reported_as_author(citation):
    authors = citation.get_authors_from_documentation(
        manual_page("Ann Doe<br>&copy; 2012 Small University")
    )
    assert [author["name"] for author in authors] == ["Ann Doe"]


def test_missing_authors_section(citation):
    with pytest.raises(RuntimeError, match="Authors"):
        citation.get_authors_from_documentation(
            "<h2>NAME</h2>x.fake" + SOURCE_CODE_SECTION
        )


def test_date_of_latest_change(citation):
    text = "  Latest change: Monday Jun 28 11:54:09 2021 in commit: 1cfc0af029a3"
    assert citation.get_datetime_from_documentation(text).year == 2021


def test_date_of_access(citation):
    """Pages built outside of a Git repository record the build time instead"""
    text = "  Accessed: Monday Jun 28 11:54:09 2021"
    assert citation.get_datetime_from_documentation(text).year == 2021


def test_missing_date(citation):
    with pytest.raises(RuntimeError, match="latest change"):
        citation.get_datetime_from_documentation("<h2>SOURCE CODE</h2>")


def test_source_code_urls(citation):
    assert citation.get_code_urls_from_documentation(SOURCE_CODE_SECTION) == (
        "https://example.org/tree/x.fake",
        "https://example.org/commits/x.fake",
    )


def test_missing_source_code_urls(citation):
    with pytest.raises(RuntimeError, match="source code URLs"):
        citation.get_code_urls_from_documentation("<h2>SOURCE CODE</h2>")


def test_empty_source_code_urls(citation):
    """Addons installed from a local directory have no source code URL

    The link is present but empty, which the tool reports the same way as
    a missing link.
    """
    text = """<h2>SOURCE CODE</h2>
<a href="">x.fake source code</a> (<a href="">history</a>)"""
    with pytest.raises(RuntimeError, match="source code URLs"):
        citation.get_code_urls_from_documentation(text)


@pytest.mark.parametrize(
    ("name", "expected"),
    [
        (
            "Ann Doe",
            {"given": "Ann", "family": "Doe", "particle": None, "suffix": None},
        ),
        (
            "Ann B. Doe",
            {"given": "Ann B.", "family": "Doe", "particle": None, "suffix": None},
        ),
        (
            "Margherita Di Leo",
            {
                "given": "Margherita",
                "family": "Di Leo",
                "particle": None,
                "suffix": None,
            },
        ),
        (
            "Margherita di Leo",
            {"given": "Margherita", "family": "Leo", "particle": "di", "suffix": None},
        ),
        (
            "Richard G. Lathrop Jr.",
            {
                "given": "Richard G.",
                "family": "Lathrop",
                "particle": None,
                "suffix": "Jr.",
            },
        ),
        (
            "Richard G. Lathrop III",
            {
                "given": "Richard G.",
                "family": "Lathrop",
                "particle": None,
                "suffix": "III",
            },
        ),
    ],
)
def test_name_split_for_cff(citation, name, expected):
    assert citation.author_name_to_cff(name) == expected


@pytest.mark.parametrize("name", ["Ann", "Ann Barbara Doe Roe Poe"])
def test_name_which_cannot_be_split(citation, name):
    with pytest.raises(RuntimeError, match="Cannot split name"):
        citation.author_name_to_cff(name)


def test_name_with_ambiguous_middle_name(citation):
    """A middle name spelled out cannot be told apart from a family name"""
    with pytest.raises(NotImplementedError):
        citation.author_name_to_cff("Maria Antonia Brovelli")


def test_empty_values_are_removed(citation):
    data = {
        "module": "x.fake",
        "institute": "",
        "authors": [{"name": "Ann Doe", "orcid": None}],
        "references": [],
    }
    assert citation.remove_empty_values_from_dict(data) == {
        "module": "x.fake",
        "authors": [{"name": "Ann Doe"}],
    }


def test_false_is_kept_but_empty_list_items_are_removed(citation):
    data = {"complete": False, "keywords": ["gis", ""]}
    assert citation.remove_empty_values_from_dict(data) == {
        "complete": False,
        "keywords": ["gis"],
    }


def test_citation_for_module(citation, monkeypatch, tmp_path):
    """Citation is collected from the manual page of the tool"""
    html_directory = tmp_path / "docs" / "html"
    html_directory.mkdir(parents=True)
    (html_directory / "x.fake.html").write_text(
        manual_page("Ann Doe, Small University (ORCID: 0000-0000-0000-0001)")
    )
    monkeypatch.setenv("GISBASE", str(tmp_path))
    monkeypatch.setattr(
        citation.gs,
        "parse_command",
        lambda *args, **kwargs: {
            "version": "8.4.0",
            "build_date": "2024-01-31",
            "date": "2024",
        },
    )

    result = citation.citation_for_module("x.fake", add_grass=True)

    assert result["module"] == "x.fake"
    assert result["grass-version"] == "8.4.0"
    assert result["year"] == 2021
    assert result["access"] == "2021-06-28T11:54:09"
    assert result["code-url"] == "https://example.org/tree/x.fake"
    assert result["url-code-history"] == "https://example.org/commits/x.fake"
    assert result["authors"] == [
        {
            "name": "Ann Doe",
            "institute": "Small University",
            "feature": None,
            "email": None,
            "orcid": "0000-0000-0000-0001",
        }
    ]
    (reference,) = result["references"]
    assert reference["title"] == "GRASS GIS 8.4.0"


def test_citation_for_module_without_manual_page(citation, monkeypatch, tmp_path):
    monkeypatch.setenv("GISBASE", str(tmp_path))
    monkeypatch.delenv("GRASS_ADDON_BASE", raising=False)
    with pytest.raises(RuntimeError, match="No HTML manual page entry"):
        citation.citation_for_module("x.fake")
