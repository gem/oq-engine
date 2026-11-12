#!/usr/bin/env bash
# The checks of a server installation, once the WebUI is running. They are
# shared by the server kind of server_install.yaml and by
# emulate_server_install.sh, which create the users they need: openquake,
# user2, user3 and user4, all with level 1 and password level_1_password.
#
# 1. archive_ok.zip is submitted through the WebUI by openquake (with
#    --journal the start-up lines are checked in the journal: needs root);
# 2. the same zip is submitted by user2;
# 3. user3 and user4 load the front page and the calc list together.
#
# Usage:
#   server_checks.sh --repo DIR --base URL --access-log-dir DIR [--journal]
# The exit status is 0 only if every check passes.
set -uo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
REPO= BASE= LOGDIR= JOURNAL=0
while [ $# -gt 0 ]; do
  case $1 in
    --repo) REPO=$2; shift 2 ;;
    --base) BASE=$2; shift 2 ;;
    --access-log-dir) LOGDIR=$2; shift 2 ;;
    --journal) JOURNAL=1; shift ;;
    *) echo "unknown option: $1"; exit 2 ;;
  esac
done
for var in REPO BASE LOGDIR; do
  [ -n "${!var}" ] || { echo "missing option for $var"; exit 2; }
done

ARCHIVE=$REPO/openquake/server/tests/data/archive_ok.zip
journal=()
[ "$JOURNAL" = 1 ] && journal=(--journal)

echo "== 1. archive_ok.zip by openquake"
"$HERE/webui_checks.sh" --base "$BASE" --user openquake \
  --password level_1_password --archive "$ARCHIVE" \
  --access-log-dir "$LOGDIR" "${journal[@]}" || exit 1

echo "== 2. archive_ok.zip by user2"
"$HERE/webui_checks.sh" --base "$BASE" --user user2 \
  --password level_1_password --archive "$ARCHIVE" \
  --access-log-dir "$LOGDIR" || exit 1

echo "== 3. user3 and user4 load the front page together"
python3 "$HERE/webui_concurrent_users.py" --base "$BASE" --rounds 3 \
  --timeout 60 --user user3:level_1_password \
  --user user4:level_1_password || exit 1

echo "PASS: server checks"
