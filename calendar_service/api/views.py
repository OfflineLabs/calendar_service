from datetime import timedelta
import itertools
from test.test_normalization import RangeError

from dateutil import parser
from django.core.exceptions import ObjectDoesNotExist
from django.http.response import HttpResponse, HttpResponseBadRequest
from django.utils import timezone
from django.utils.functional import cached_property
from rest_framework import viewsets
from rest_framework.decorators import detail_route
from rest_framework.response import Response

from api.serializers import CalendarSerializer, EventSerializer, RuleSerializer, \
    OccurrenceSerializer
from schedule.models.calendars import Calendar
from schedule.models.events import Event, Occurrence
from schedule.models.rules import Rule


class CalendarViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows calendars to be viewed or edited.
    """
    queryset = Calendar.objects.all()
    serializer_class = CalendarSerializer


class EventViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows events to be viewed or edited.
    """
    queryset = Event.objects.all()
    serializer_class = EventSerializer


class OccurrenceViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows occurrences to be viewed or edited.
    
        List Query Parameters
        ----------------
        start -- list occurrences starting at this datetime ex: start=2024-12-21T00:12:00Z
        end   -- list occurrences ending at or before this datetime ex: end=2024-12-21T00:12:00Z
        limit -- limit total number of occurrences returned ex:limit=500
    """
    queryset = Occurrence.objects.all()  # @UndefinedVariable
    serializer_class = OccurrenceSerializer
    default_end_delta = {'days': 31}
    default_limit = 1000
    
    @cached_property
    def event(self):
        return Event.objects.get(id=self.event_id)
    
    def __init__(self, *args, **kwargs):
        super(OccurrenceViewSet, self).__init__(*args, **kwargs)
        self.start = timezone.now()
        self.end = timezone.now() + timedelta(**self.default_end_delta)
    
    @detail_route(methods=['put', 'patch'])
    def cancel(self, request, **kwargs):
        return self.set_cancelled(True)
    
    def set_cancelled(self, cancelled):
        occ = self.get_object()
        occ.cancelled = cancelled
        occ.save()
        serializer = self.get_serializer(occ)
        return Response(serializer.data)
    
    def dispatch(self, request, event_id, **kwargs):
        self.event_id = event_id
        return super(OccurrenceViewSet, self).dispatch(request, **kwargs)
    
    def get_object(self):
        lookups = {'event_id': self.event_id,}
        try:
            pk = self.kwargs.pk
        except ValueError:
            start = parser.parse(self.kwargs['pk'])
            lookups['start': start]
        else:
            lookups['id':pk]
        try:
            p_occ = Occurrence.objects.get(**lookups)
        except ObjectDoesNotExist:
            occurrences = self.event.get_occurrences(start=start, end=start)
            if occurrences:
                return occurrences[0]
            else:
                raise
        else:
            return p_occ
    
    def get_queryset(self):
        if self.end:
            qs = self.event.get_occurrences(self.start, self.end)
        else:
            qs_gen = self.event.occurrences_after(self.start)
            qs = []
            for __ in range(self.limit): 
                try:
                    qs.append(qs_gen.next())
                except Exception:
                    raise
        return qs
    
    def get_serializer_context(self):
        context = super(OccurrenceViewSet, self).get_serializer_context()
        context['request'] = self.request
        return context
    
    def list(self, request, *args, **kwargs):
        start = request.GET.get('start', None)
        end = request.GET.get('end', None)
        limit = request.GET.get('limit', None)
        if limit and end:
            return HttpResponseBadRequest('you can specify an end date or limit but not both')
        if limit:
            self.end = None
            self.limit = int(limit)
        if start:
            try:
                start = parser.parse(start)
            except:
                raise HttpResponseBadRequest('datetime strings must be in the following format: ' + self.start)
            else:
                self.start = start
        if end:
            try:
                end = parser.parse(end)
            except:
                raise HttpResponseBadRequest('datetime strings must be in the following format: ' + self.start)
            else:
                self.end = end
        return viewsets.ModelViewSet.list(self, request, *args, **kwargs)
    
    @detail_route(methods=['patch','put', 'post'])
    def uncancel(self, request, **kwargs):
        return self.set_cancelled(False)



class RuleViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows rules to be viewed or edited.
    """
    queryset = Rule.objects.all()  # @UndefinedVariable
    serializer_class = RuleSerializer