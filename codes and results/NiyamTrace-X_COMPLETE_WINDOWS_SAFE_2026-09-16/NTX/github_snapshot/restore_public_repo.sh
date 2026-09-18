#!/usr/bin/env bash
set -euo pipefail
REPO=https://github.com/bnssaanirudh/NiyamTrace-X.git
COMMIT=c14661dbd11c42ebd1019b6a1a5c49b8643da137
git clone "$REPO" NiyamTrace-X-public
cd NiyamTrace-X-public
git checkout "$COMMIT"
printf 'Restored commit: '; git rev-parse HEAD
