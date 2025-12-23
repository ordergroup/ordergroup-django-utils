# -*- coding: utf-8 -*-
from __future__ import absolute_import, division, print_function

from django.utils.decorators import method_decorator


def class_view_decorator(function_decorator):
    def simple_decorator(view_klass):
        view_klass.dispatch = method_decorator(function_decorator)(view_klass.dispatch)
        return view_klass

    return simple_decorator

# def require_company_administrator(view_func):
#     def wrapped(request, *args, **kwargs):
#         if request.user.is_anonymous():
#             path = request.build_absolute_uri()
#             return redirect_to_login(path, reverse_lazy('companies:login'))
#         else:
#             if not isinstance(request.user, CompanyAdministrator):
#                 return redirect('companies:login')
#             return view_func(request, *args, **kwargs)
#     return wrapped
#
# company_administrator_required = class_view_decorator(require_company_administrator)
