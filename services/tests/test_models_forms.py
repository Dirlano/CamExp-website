from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from services.models import Rating, ServiceListing, RequestPost
from services.forms import RatingForm
from accounts.models import Profile

User = get_user_model()

class RatingModelTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            username='testuser1',
            email='test1@example.com',
            password='testpass123'
        )
        self.user1_profile = Profile.objects.create(
            user=self.user1,
            full_name='Test User 1',
            phone_number='1234567890'
        )
        
        self.user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123'
        )
        self.user2_profile = Profile.objects.create(
            user=self.user2,
            full_name='Test User 2',
            phone_number='0987654321'
        )
        
        self.service = ServiceListing.objects.create(
            expert=self.user1_profile,
            title='Test Service',
            description='Test description',
            price=100.00,
            category='it'
        )

    def test_create_rating(self):
        """Test creating a rating for a service"""
        rating = Rating.objects.create(
            reviewer=self.user1_profile,
            expert=self.user2_profile,
            score=5,
            review='Great service!',
            service=self.service
        )
        self.assertEqual(str(rating), '5 - Excellent - testuser1 for testuser2')
        self.assertEqual(rating.created_at.date(), timezone.now().date())


class RatingFormTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            username='testuser1',
            email='test1@example.com',
            password='testpass123'
        )
        self.user1_profile = Profile.objects.create(
            user=self.user1,
            full_name='Test User 1',
            phone_number='1234567890'
        )
        
        self.user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123'
        )
        self.user2_profile = Profile.objects.create(
            user=self.user2,
            full_name='Test User 2',
            phone_number='0987654321'
        )
        
        self.service = ServiceListing.objects.create(
            expert=self.user1_profile,
            title='Test Service',
            description='Test description',
            price=100.00,
            category='it'
        )

    def test_valid_rating_form(self):
        """Test the rating form with valid data"""
        form_data = {
            'score': 5,
            'title': 'Great service',
            'review': 'Excellent work, highly recommended!',
            'expert': self.user2_profile.id,
            'service': self.service.id
        }
        form = RatingForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_self_rating(self):
        """Test that users can't rate themselves"""
        form_data = {
            'score': 5,
            'title': 'Self rating',
            'review': 'I am rating myself',
            'expert': self.user1_profile.id,
            'service': self.service.id
        }
        form = RatingForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('You cannot rate yourself.', form.non_field_errors())

    def test_missing_required_fields(self):
        """Test form validation with missing required fields"""
        form_data = {
            'score': '',
            'review': '',
            'expert': self.user2_profile.id
        }
        form = RatingForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('score', form.errors)
        self.assertIn('review', form.errors)
