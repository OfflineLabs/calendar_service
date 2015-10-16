from datetime import timedelta
import json

from django.utils import timezone
from model_mommy import mommy
from rest_framework.reverse import reverse
from rest_framework.test import APITestCase

from schedule.models.events import Event
from schedule.models.rules import Rule


# Create your tests here.
class CalendarAPITestCase(APITestCase):
    event = None
    rule = None
    
    def setUp(self):
        self.rule = self.rule or mommy.make(Rule, frequency="WEEKLY") 
        self.event = self.event or mommy.make(
            Event, 
            rule_id=self.rule.id,
            start=timezone.now(),
            end=timezone.now() + timedelta(hours=2)
        )
    
    def test_event_endpoint(self):
        url = reverse('event-list')
        
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200, response.content)
                
        data = {
            'rule_id': self.rule.id,
            'start': self.event.start,
            'end': self.event.end,
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201, response.content)
        
    def test_occurrences_endpoint(self):
        url = reverse('occurrence-list', args=[self.event.id])
        
        # test list view
        response = self.client.get(url, content_type="application/json")
        self.assertEqual(response.status_code, 200, response.content)
        
        # test detail view for non-persisted occ
        occ_page = json.loads(response.content)
        occ1 = occ_page['results'][1]
        occ2 = occ_page['results'][2]
        detail_url = reverse('occurrence-detail', args=[self.event.id, occ1['start']])
        response = self.client.get(detail_url, media_type="application/json")
        self.assertEqual(response.status_code, 200, response.content)
        
        # test changing the start time and persisting the occurrence
        response = self.client.patch(
            detail_url, 
            data={'start': self.event.start + timedelta(hours=1)}, 
            format="json",
            media_type="application/json"
        )
        self.assertEqual(response.status_code, 200, response.content)
        occ1 = json.loads(response.content)
        
        # test getting the persisted occ with id instead of time
        detail_url = reverse('occurrence-detail', args=[self.event.id, occ1['id']])
        response = self.client.get(detail_url, content_type="application/json")
        self.assertEqual(response.status_code, 200, response.content)
        
        # test cancelling the persisted occurrence
        cancel_url = occ1['methods']['cancel']
        response = self.client.patch(cancel_url)
        self.assertEqual(response.status_code, 200, response.content)
        
        # test cancelling unpersisted occurrences
        cancel_url = occ2['methods']['cancel']
        response = self.client.patch(cancel_url)
        self.assertEqual(response.status_code, 200, response.content)
        
        # test uncancelling
        uncancel_url = occ2['methods']['uncancel']
        response = self.client.patch(uncancel_url)
        self.assertEqual(response.status_code, 200, response.content)
        
        # test that delete fails - can't delete occurrences, use cancel instead
        response = self.client.delete(detail_url)
        self.assertEqual(response.status_code, 405, response.content)
        
        
        
    def test_rule_endpoint(self):
        url = reverse('rule-list')
        
        data = {
            'frequency': 'WEEKLY',
            'name': 'WEEKLY',
            'description': 'WEEKLY',
        }
        response = self.client.post(url, data=data)
        self.assertEqual(response.status_code, 201, response.content)