from django.test import TestCase
from democracy.models import ContactPerson
from django.utils import timezone
from django.test import tag

# models test
class SectionCommentModelTest(TestCase):

    def create_ContactPerson(self, name="Testi Kontakti", phone="12345678911"):
        return ContactPerson.objects.create(name=name, phone=phone,  created_at=timezone.now())
    
    @tag('unit')
    def test_ContactPerson_creation(self):
        w = self.create_ContactPerson()
        self.assertTrue(isinstance(w, ContactPerson))