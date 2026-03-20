#!/bin/bash
for file in $1/templates/registration/*.$2.tmpl; do
    cp -- "$file" "${file%.$2.tmpl}"
done

$1/manage.py migrate
$1/manage.py loaddata openquake/server/fixtures/0001_cookie_consent_required_plus_hide_cookie_bar.json
#$1/manage.py collectstatic --noinput
