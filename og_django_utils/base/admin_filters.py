# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from django.core.exceptions import ImproperlyConfigured


class BaseAdminSelectFilter(admin.SimpleListFilter):
    title = None
    parameter_name = None
    template = 'base/admin/select_filter.html'
    field_to_filter_against = None  # set in init
    field_to_display = 'name'  # field that is used to create display title
    field_to_order = 'name'  # field that is used to create display title

    class Meta:
        model = None

    def __init__(self, request, params, model, model_admin):
        if not self.title:
            self.title = self.make_parameter_name()
        if not self.parameter_name:
            self.parameter_name = self.make_parameter_name()
        if not self.field_to_filter_against:
            self.field_to_filter_against = '{}_id'.format(self.parameter_name)
        super(BaseAdminSelectFilter, self).__init__(request, params, model, model_admin)

    def make_parameter_name(self):
        """
        :return: str of model name(lowercase)
        """
        model = self.Meta.model
        if model:
            parameter_name = '{}'.format(model.__name__.lower())
            return parameter_name
        raise ImproperlyConfigured('Meta.model is not set')

    def queryset(self, request, queryset):
        """
        filters based on (filter_field: str) parameter most likely should be xxxx_id unless lookups method is overriden

        :param request:
        :param queryset:
        :return: filtered QuerySet
        """
        filter_attrs = {self.field_to_filter_against: self.value()}
        if self.value():
            return queryset.filter(**filter_attrs)

    def lookups(self, request, model_admin):
        """
        default parameter used for lookup is id of single object whose model is defined in Meta.model
        default display on lost is set to '[$id] $field_to_display' can be overridden in create_display_title method

        default objects used for filter options is set Meta.model all objects can be overridden
        in get_queryset_for_lookup

        :param request:
        :param model_admin:
        :return: list of objects used for filtering
        """
        object_list = []

        objects = self.get_queryset_for_lookup()
        for single_object in objects:
            object_list.append((single_object.id, self.create_display_title(single_object)))
        return object_list

    def create_display_title(self, single_object):
        """
        :param single_object: single Meta.model object
        :return: str that defines displayed title of object on list
        """
        title = '[{}] {}'.format(single_object.id, getattr(single_object, self.field_to_display))
        return title

    def get_queryset_for_lookup(self):
        """
        :return: QuerySet of Meta.model ordered by $field_to_order
        """
        if not self.Meta.model:
            raise ImproperlyConfigured('Meta.model is not set')
        return self.Meta.model.objects.all().order_by(self.field_to_order)
