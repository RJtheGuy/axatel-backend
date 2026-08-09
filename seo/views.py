from django.http import HttpResponse

ROBOTS = """\
User-agent: *
Allow: /
Disallow: /cms/
Disallow: /django-admin/

Sitemap: https://axatel.it/sitemap.xml
"""

def robots_txt(request):
    return HttpResponse(ROBOTS, content_type="text/plain")
