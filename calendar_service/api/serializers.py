
from django.core.urlresolvers import NoReverseMatch
from rest_framework import serializers, fields
from rest_framework.reverse import reverse

from api.fields import JSONSerializerField
from schedule.models.calendars import Calendar
from schedule.models.events import Event, Occurrence
from schedule.models.rules import Rule
from api.utils import get_detail_routes


class CalendarSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Calendar


class EventSerializer(serializers.HyperlinkedModelSerializer):
    occurrences = fields.SerializerMethodField()
    rule_params = JSONSerializerField(required=False) # required to make json field writable via api

    class Meta:
        model = Event
        
    def get_occurrences(self, event):
        return reverse('event-detail', args=[event.id], request=self._context['request']) + 'occurrences/'


class OccurrenceSerializer(serializers.HyperlinkedModelSerializer):
    id = fields.IntegerField(read_only=True)
    url = fields.SerializerMethodField()
    methods = fields.SerializerMethodField()
    _methods_cache = None # class attribute that caches methdos for the OccurrenceViewSet 
    
    class Meta:
        model = Occurrence
        
    def get_methods(self, occ):
        from views import OccurrenceViewSet  # @NoMove
        methods = OccurrenceSerializer._methods_cache or get_detail_routes(OccurrenceViewSet)
        OccurrenceSerializer._methods_cache = methods
        method_dict = {}
        lookups = occ.get_lookups()
        for method in methods:
            url_name = "occurrence-{0}".format(method)
            try:
                url = reverse(url_name, args=lookups.values(), request=self._context['request'])
            except NoReverseMatch:
                pass
            else:
                method_dict[method] = url
        return method_dict
            
    def get_url(self, occ):
        lookups = occ.get_lookups()
        return reverse('occurrence-detail', args=lookups.values(), request=self._context['request'])


class RuleSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Rule
