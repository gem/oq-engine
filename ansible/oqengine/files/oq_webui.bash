#!/usr/bin/env bash
/usr/bin/lsof -nP -iTCP -sTCP:LISTEN | grep oq-webui | awk '{print $2}' | sort -u
