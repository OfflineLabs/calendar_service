from datetime import timedelta

from dateutil import parser
from django.core.exceptions import ObjectDoesNotExist
from django.http.response import HttpResponseBadRequest
from django.utils import timezone
from django.utils.functional import cached_property
from rest_framework import viewsets
from rest_framework.decorators import detail_route
from rest_framework.exceptions import MethodNotAllowed
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
    lookup_field = 'lookup' # lookup can be pk or occurrence start datetime
    
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
    
    def destroy(self, request, *args, **kwargs):
        raise MethodNotAllowed('DELETE')
    
    def dispatch(self, request, event_id, **kwargs):
        self.event_id = event_id
        return super(OccurrenceViewSet, self).dispatch(request, **kwargs)
    
    def get_object(self):
        lookups = {'event_id': self.event_id,}
        # determine if lookup is by id or 
        try:
            occ_id = int(self.kwargs['lookup'])
        except ValueError:
            start = parser.parse(self.kwargs['lookup'])
            lookups['start'] = start
        else:
            lookups['id'] = occ_id
        try:
            p_occ = Occurrence.objects.get(**lookups)
        except ObjectDoesNotExist:
            try:
                occ = self.event.get_occurrences(start=start, end=start)[0]
            except ValueError:
                raise
            else:
                return occ
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
    
    def set_cancelled(self, cancelled):
        occ = self.get_object()
        occ.cancelled = cancelled
        occ.save()
        serializer = self.get_serializer(occ)
        return Response(serializer.data)
    
    @detail_route(methods=['patch','put', 'post'])
    def uncancel(self, request, **kwargs):
        return self.set_cancelled(False)



class RuleViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows rules to be viewed or edited.
    """
    queryset = Rule.objects.all()  # @UndefinedVariable
    serializer_class = RuleSerializer