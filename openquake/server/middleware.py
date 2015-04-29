from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from re import compile


class LoginRequiredMiddleware(object):

    white_list_paths = (
        reverse('login'),
    )

    white_list = map(
        compile,
        white_list_paths +
        getattr(
            settings,
            "AUTH_EXEMPT_URLS",
            ()))
    redirect_to = reverse('login')

    def process_request(self, request):
        if not request.user.is_authenticated():
            if not any(path.match(request.path) for path in self.white_list):
                return HttpResponseRedirect(
                    '{login_path}?next={request_path}'.format(
                        login_path=self.redirect_to,
                        request_path=request.path))
