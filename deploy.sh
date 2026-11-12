#!/bin/bash

set -euo pipefail

source bin/activate

ruff check

gh actions-lock

zizmor .github/workflows/

exit 0