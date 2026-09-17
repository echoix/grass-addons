#!/usr/bin/env bash

# Check that every installed tool has a manual page.
#
# The build installs a tool before it generates its documentation and only
# records a failing directory in the error log, so a tool whose manual page
# cannot be generated (for example because an import fails) still ends up in
# the installation. Tools which read the documentation, such as g.citation,
# then fail on it.

set -e

GISBASE="$(grass --config path)"

missing=$(
    find "${GISBASE}/bin" "${GISBASE}/scripts" -maxdepth 1 -type f -printf '%f\n' |
        sort |
        while IFS= read -r tool; do
            if [ ! -f "${GISBASE}/docs/html/${tool}.html" ]; then
                echo "${tool}"
            fi
        done
)

if [ -n "${missing}" ]; then
    echo "::error::Tools installed without a manual page: $(echo "${missing}" | tr '\n' ' ')"
    echo "The documentation of these tools failed to build:"
    echo "${missing}"
    exit 1
fi

echo "All installed tools have a manual page."
