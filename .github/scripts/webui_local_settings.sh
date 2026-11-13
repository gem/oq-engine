#!/usr/bin/env bash
# Write the local_settings.py of a server or devel installation: the settings
# of the WebUI in production mode, with the SMTP server and the access log.
#
# Usage: webui_local_settings.sh SERVER_DIR   (the directory openquake/server)
set -euo pipefail
cat > "$1/local_settings.py" << 'EOT'
APPLICATION_MODE = "RESTRICTED"
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = "admin@reply.com"
EMAIL_HOST_PASSWORD = "polhjuih@"
EMAIL_SUPPORT = "noreply@reply.com"
WEBUI_ACCESS_LOG_DIR = "/var/log/oq-engine"
EOT
