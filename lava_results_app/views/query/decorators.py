# -*- coding: utf-8 -*-
# Copyright (C) 2015-2018 Linaro Limited
#
# Author: Stevan Radakovic <stevan.radakovic@linaro.org>
#
# This file is part of LAVA.
#
# LAVA is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License version 3
# as published by the Free Software Foundation
#
# LAVA is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with LAVA.  If not, see <http://www.gnu.org/licenses/>.

from functools import wraps

from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from lava_results_app.models import Query


def ownership_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        report_name = kwargs.get("name")
        username = kwargs.get("username")
        query = get_object_or_404(Query, name=report_name, owner__username=username)
        if query.is_accessible_by(request.user):
            return view_func(request, *args, **kwargs)
        else:
            raise PermissionDenied

    return wrapper
