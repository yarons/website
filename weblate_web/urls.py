# -*- coding: utf-8 -*-
#
# Copyright © 2012 - 2019 Michal Čihař <michal@cihar.com>
#
# This file is part of Weblate <https://weblate.org/>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#

import django.contrib.sitemaps.views
import django.views.static
from django.conf import settings
from django.conf.urls import include, url
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.contrib.sitemaps import Sitemap
from django.contrib.syndication.views import Feed
from django.urls import path
from django.utils import timezone
from django.views.decorators.cache import cache_page
from django.views.generic import RedirectView, TemplateView
from simple_sso.sso_client.client import Client

from weblate_web.models import Post
from weblate_web.views import (
    CompleteView,
    CustomerView,
    DonateRewardView,
    DonateView,
    EditLinkView,
    NewsView,
    PaymentView,
    PostView,
    disable_repeat,
    download_invoice,
    fetch_vat,
    process_donation,
    subscribe,
)


class LatestEntriesFeed(Feed):
    title = "Weblate blog"
    link = "/news/"
    description = "News about Weblate and localization."

    def items(self):
        # pylint: disable=no-self-use
        return Post.objects.filter(
            timestamp__lt=timezone.now()
        ).order_by('-timestamp')[:10]

    def item_title(self, item):
        # pylint: disable=no-self-use
        return item.title

    def item_description(self, item):
        # pylint: disable=no-self-use
        return item.body.rendered


class PagesSitemap(Sitemap):
    """Sitemap of static pages for one language."""

    def __init__(self, language):
        super().__init__()
        self.language = language

    def items(self):
        return (
            ('/', 1.0, 'weekly'),
            ('/features/', 0.9, 'weekly'),
            ('/download/', 0.5, 'daily'),
            ('/try/', 0.5, 'weekly'),
            ('/hosting/', 0.8, 'monthly'),
            ('/contribute/', 0.7, 'monthly'),
            ('/donate/', 0.7, 'weekly'),
            ('/support/', 0.7, 'monthly'),
            ('/thanks/', 0.2, 'monthly'),
            ('/terms/', 0.2, 'monthly'),
            ('/news/', 0.9, 'daily'),
        )

    def location(self, obj):
        return '/{0}{1}'.format(self.language, obj[0])

    def priority(self, obj):
        if self.language == 'en':
            return obj[1]
        return obj[1] * 3 / 4

    def changefreq(self, obj):
        # pylint: disable=no-self-use
        return obj[2]


class NewsSitemap(Sitemap):
    priority = 0.8

    def items(self):
        # pylint: disable=no-self-use
        return Post.objects.filter(
            timestamp__lt=timezone.now()
        ).order_by('-timestamp')

    def lastmod(self, item):
        # pylint: disable=no-self-use
        return item.timestamp


# create each section in all languages
SITEMAPS = {
    lang[0]: PagesSitemap(lang[0]) for lang in settings.LANGUAGES
}
SITEMAPS['news'] = NewsSitemap()
UUID = r'(?P<pk>[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})'


SSO_CLIENT = Client(
    settings.SSO_SERVER, settings.SSO_PUBLIC_KEY, settings.SSO_PRIVATE_KEY
)


urlpatterns = i18n_patterns(
    url(
        r'^$',
        TemplateView.as_view(template_name="index.html"),
        name='home'
    ),
    url(
        r'^features/$',
        TemplateView.as_view(template_name="features.html"),
        name='features'
    ),
    url(
        r'^tour/$',
        RedirectView.as_view(url='/try/', permanent=True)
    ),
    url(
        r'^download/$',
        TemplateView.as_view(template_name="download.html"),
        name='download'
    ),
    url(
        r'^try/$',
        TemplateView.as_view(template_name="try.html"),
        name='try'
    ),
    url(
        r'^hosting/$',
        TemplateView.as_view(template_name="hosting.html"),
        name='hosting'
    ),
    url(
        r'^hosting/free/$',
        TemplateView.as_view(template_name="hosting-free.html"),
        name='hosting-free'
    ),
    url(
        r'^hosting/ordered/$',
        TemplateView.as_view(template_name="hosting-ordered.html"),
        name='hosting-ordered'
    ),
    url(
        r'^contribute/$',
        TemplateView.as_view(template_name="contribute.html"),
        name='contribute'
    ),
    url(
        r'^donate/$',
        TemplateView.as_view(template_name="donate.html"),
        name='donate'
    ),
    url(
        r'^donate/process/$',
        process_donation,
        name='donate-process'
    ),
    url(
        r'^donate/new/$',
        DonateView.as_view(),
        name='donate-new'
    ),
    url(
        r'^donate/new/' + UUID + '/$',
        DonateRewardView.as_view(),
        name='donate-reward'
    ),
    url(
        r'^donate/edit/(?P<pk>[0-9]+)/$',
        EditLinkView.as_view(),
        name='donate-edit'
    ),
    url(
        r'^donate/invoice/' + UUID + '/$',
        download_invoice,
        name='donate-invoice'
    ),
    url(
        r'^donate/disable/(?P<pk>[0-9]+)/$',
        disable_repeat,
        name='donate-disable'
    ),
    url(
        r'^news/$',
        NewsView.as_view(),
        name='news'
    ),
    url(
        r'^news/archive/(?P<slug>[-a-zA-Z0-9_]+)/$',
        PostView.as_view(),
        name='post'
    ),
    url(
        r'^support/$',
        TemplateView.as_view(template_name="support.html"),
        name='support'
    ),
    url(
        r'^thanks/$',
        TemplateView.as_view(template_name="thanks.html"),
        name='thanks'
    ),
    url(
        r'^terms/$',
        TemplateView.as_view(template_name="terms.html"),
        name='terms'
    ),
    url(
        r'^payment/' + UUID + '/$',
        PaymentView.as_view(),
        name='payment'
    ),
    url(
        r'^payment/' + UUID + '/edit/$',
        CustomerView.as_view(),
        name='payment-customer'
    ),
    url(
        r'^payment/' + UUID + '/complete/$',
        CompleteView.as_view(),
        name='payment-complete'
    ),

    # Compatibility with disabled languages
    url(
        r'^[a-z][a-z]/$',
        RedirectView.as_view(url='/', permanent=False)
    ),
    url(
        r'^[a-z][a-z]_[A-Z][A-Z]/$',
        RedirectView.as_view(url='/', permanent=False)
    ),
    # Broken links
    url(
        r'^https?:/.*$',
        RedirectView.as_view(url='/', permanent=True)
    ),
    url(
        r'^index\.html$',
        RedirectView.as_view(url='/', permanent=True)
    ),
    url(
        r'^index\.([a-z][a-z])\.html$',
        RedirectView.as_view(url='/', permanent=True)
    ),
    url(
        r'^[a-z][a-z]/index\.html$',
        RedirectView.as_view(url='/', permanent=True)
    ),
    url(
        r'^[a-z][a-z]_[A-Z][A-Z]/index\.html$',
        RedirectView.as_view(url='/', permanent=True)
    ),
) + [
    url(
        r'^sitemap\.xml$',
        cache_page(3600)(django.contrib.sitemaps.views.index),
        {'sitemaps': SITEMAPS, 'sitemap_url_name': 'sitemap'},
        name='sitemap-index',
    ),
    url(
        r'^sitemap-(?P<section>.+)\.xml$',
        cache_page(1800)(django.contrib.sitemaps.views.sitemap),
        {'sitemaps': SITEMAPS},
        name='sitemap',
    ),
    path('feed/', LatestEntriesFeed(), name='feed'),
    url(
        r'^js/vat/$',
        fetch_vat
    ),
    url(r'^sso-login/', include(SSO_CLIENT.get_urls())),
    url(r'^subscribe/(?P<name>hosted|users)/', subscribe, name='subscribe'),
    url(r'^logout/$', LogoutView.as_view(next_page='/'), name='logout'),
    # Admin
    url(
        r'^admin/login/$',
        RedirectView.as_view(
            pattern_name='simple-sso-login', permanent=True, query_string=True
        )
    ),
    url(r'^admin/', admin.site.urls),

    # Media files on devel server
    url(
        r'^media/(?P<path>.*)$',
        django.views.static.serve,
        {'document_root': settings.MEDIA_ROOT}
    ),
]
