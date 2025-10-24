from django.urls import re_path
from openquake.server import views
from openquake.server import urls as main_urls

urlpatterns = [
    *main_urls.urlpatterns,
    re_path(r'^test/check_callback$', views.check_callback),
]
