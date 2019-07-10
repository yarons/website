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
"""Remote data fetching and caching."""

import requests
import sentry_sdk
from django.conf import settings
from django.core.cache import cache
from wlc import Weblate

CONTRIBUTORS_URL = 'https://api.github.com/repos/{}/{}/stats/contributors'
WEBLATE_CONTRIBUTORS_URL = CONTRIBUTORS_URL.format('WeblateOrg', 'weblate')
EXCLUDE_USERS = {'nijel', 'weblate'}
ACTIVITY_URL = 'https://hosted.weblate.org/activity/month/'


def get_contributors(force=False):
    key = 'wlweb-contributors'
    results = cache.get(key)
    if not force and results is not None:
        return results
    # Perform request
    try:
        response = requests.get(WEBLATE_CONTRIBUTORS_URL)
    except IOError as error:
        sentry_sdk.capture_exception(error)
        response = None
    # Stats are not yet calculated
    if response is None or response.status_code != 200:
        return []

    stats = response.json()
    # Fill in ranking. This seems to best reflect people effort, but still
    # is not accurate at all. The problem is that commits stats are
    # misleading due to high number of commits generated by old Weblate
    # versions. Additions are heavily biased by adding new translation files.
    for stat in stats:
        if stat['author']['login'] in EXCLUDE_USERS:
            stat['rank'] = 0
            continue
        stat['rank'] = stat['total'] + sum(
            (week['a'] + week['d'] for week in stat['weeks'])
        )

    stats.sort(key=lambda x: -x['rank'])

    cache.set(key, stats[:8], timeout=3600)
    return stats[:8]


def get_activity(force=False):
    key = 'wlweb-activity-stats'
    results = cache.get(key)
    if not force and results is not None:
        return results
    # Perform request
    try:
        response = requests.get(ACTIVITY_URL)
    except IOError as error:
        sentry_sdk.capture_exception(error)
        response = None
    # Stats are not yet calculated
    if response is None or response.status_code != 200:
        return []

    stats = response.json()
    data = stats['series'][0][-25:]
    cache.set(key, data, timeout=3600)
    return data


def get_changes(force=False):
    key = 'wlweb-changes-list'
    results = cache.get(key)
    if not force and results is not None:
        return results
    wlc = Weblate(key=settings.CHANGES_KEY, url=settings.CHANGES_API)

    stats = [p.statistics() for p in wlc.list_projects()]
    stats = [p.get_data() for p in stats if p['last_change'] is not None]

    stats.sort(key=lambda x: x['last_change'], reverse=True)

    cache.set(key, stats[:10], timeout=3600)
    return stats[:10]
