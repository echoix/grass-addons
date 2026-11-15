#!/usr/bin/env python3

"""Check that every tool in the repository has its documentation files

Each tool needs a <tool>.md documentation file and a <tool>.html file with
the same content in HTML markup. A tool without them is built and installed
without a manual page, which breaks the tools reading the documentation,
such as g.citation.

SPDX-License-Identifier: GPL-2.0-or-later
"""

import re
import sys
from pathlib import Path

# A tool is a directory whose Makefile names the tool and builds it as a
# tool, not as a library, a test or a set of files to install.
TOOL_NAME = re.compile(r"^PGM\s*=\s*(\S+)", re.MULTILINE)
TOOL_BUILD = re.compile(r"include .*Make/(Module|Script|ShScript)\.make")

# Tools which have no documentation and predate this check. Remove an entry
# together with adding the documentation, do not add new ones.
KNOWN_WITHOUT_DOCUMENTATION = {
    "src/imagery/i.pr/i.pr.blob",
    "src/imagery/i.pr/i.pr.classify",
    "src/imagery/i.pr/i.pr.features",
    "src/imagery/i.pr/i.pr.features_additional",
    "src/imagery/i.pr/i.pr.features_extract",
    "src/imagery/i.pr/i.pr.features_selection",
    "src/imagery/i.pr/i.pr.model",
    "src/imagery/i.pr/i.pr.sites_aggregate",
    "src/imagery/i.pr/i.pr.statistics",
    "src/imagery/i.pr/i.pr.subsets",
    "src/imagery/i.pr/i.pr.training",
    "src/imagery/i.pr/i.pr.uxb",
    # A test program built with Module.make, not a tool.
    "src/imagery/i.spec.unmix/test",
}


def find_tools(source_directory):
    """Yield the directory and name of each tool of the repository"""
    for makefile in sorted(source_directory.rglob("Makefile")):
        text = makefile.read_text()
        name = TOOL_NAME.search(text)
        if name and TOOL_BUILD.search(text):
            yield makefile.parent, name.group(1)


def main():
    repository = Path(__file__).parent.parent
    missing = []
    excluded_and_documented = []
    for directory, name in find_tools(repository / "src"):
        relative_directory = directory.relative_to(repository).as_posix()
        files = [
            file
            for file in (f"{name}.md", f"{name}.html")
            if not (directory / file).exists()
        ]
        if relative_directory in KNOWN_WITHOUT_DOCUMENTATION:
            if not files:
                excluded_and_documented.append(relative_directory)
        elif files:
            missing.append((relative_directory, files))

    for directory, files in missing:
        for file in files:
            print(f"{directory}/{file} is missing")
    if missing:
        print(
            f"\nTools missing documentation files: {len(missing)}."
            " Each tool needs a <tool>.md file and a <tool>.html file with"
            " the same content.",
            file=sys.stderr,
        )
    for directory in excluded_and_documented:
        print(
            f"{directory} has documentation now and can be removed from"
            " KNOWN_WITHOUT_DOCUMENTATION in this script",
            file=sys.stderr,
        )
    return 1 if missing or excluded_and_documented else 0


if __name__ == "__main__":
    sys.exit(main())
