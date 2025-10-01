import pytest
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.utils import timezone
from rest_framework.test import APITestCase
from rest_framework import status
from .models import VideoCallSession
from projects.models import Project
from notifications.models import Notification

User = get_user_model()

class VideoCallSessionModelTest(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin', email='admin@test.com',
            password='pass', user_type='admin'
        )
        self.client_user = User.objects.create_user(
            username='client', email='client@test.com',
            password='pass', user_type='client'
        )
        self.expert = User.objects.create_user(
            username='expert', email='expert@test.com',
            password='pass', user_type='expert'
        )
        self.project = Project.objects.create(
            client=self.client_user,
            expert=self.expert,
            title='Test Project'
        )

    def test_video_call_session_creation(self):
        session = VideoCallSession.objects.create(
            contract=self.project,
            initiated_by=self.admin
        )
        session.participants.add(self.admin, self.client_user, self.expert)

        self.assertEqual(session.contract, self.project)
        self.assertEqual(session.initiated_by, self.admin)
        self.assertEqual(session.status, 'pending')
        self.assertIsNotNone(session.room_id)
        self.assertIn(self.admin, session.participants.all())
        self.assertIn(self.client_user, session.participants.all())
        self.assertIn(self.expert, session.participants.all())

    def test_end_call_method(self):
        session = VideoCallSession.objects.create(
            contract=self.project,
            initiated_by=self.admin,
            status='active'
        )
        session.end_call()

        self.assertEqual(session.status, 'ended')
        self.assertIsNotNone(session.end_time)

    def test_str_method(self):
        session = VideoCallSession.objects.create(
            contract=self.project,
            initiated_by=self.admin
        )
        expected = f"Video Call for {self.project.title} - {session.room_id}"
        self.assertEqual(str(session), expected)


class VideoCallAPITest(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin', email='admin@test.com',
            password='pass', user_type='admin'
        )
        self.admin.user_permissions.add(
            Permission.objects.get(codename='can_create_video_call')
        )
        self.client_user = User.objects.create_user(
            username='client', email='client@test.com',
            password='pass', user_type='client'
        )
        self.expert = User.objects.create_user(
            username='expert', email='expert@test.com',
            password='pass', user_type='expert'
        )
        self.project = Project.objects.create(
            client=self.client_user,
            expert=self.expert,
            title='Test Project'
        )

    def test_create_video_call_as_admin(self):
        self.client.force_authenticate(user=self.admin)
        data = {'contract': self.project.id}

        response = self.client.post('/api/video-calls/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(VideoCallSession.objects.count(), 1)

        session = VideoCallSession.objects.first()
        self.assertEqual(session.contract, self.project)
        self.assertEqual(session.initiated_by, self.admin)

    def test_create_video_call_as_non_admin(self):
        self.client.force_authenticate(user=self.client_user)
        data = {'contract': self.project.id}

        response = self.client.post('/api/video-calls/', data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_video_call_details(self):
        session = VideoCallSession.objects.create(
            contract=self.project,
            initiated_by=self.admin
        )
        session.participants.add(self.client_user)

        self.client.force_authenticate(user=self.client_user)
        response = self.client.get(f'/api/video-calls/{session.id}/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], session.id)

    def test_end_video_call_as_initiator(self):
        session = VideoCallSession.objects.create(
            contract=self.project,
            initiated_by=self.admin,
            status='active'
        )

        self.client.force_authenticate(user=self.admin)
        response = self.client.post(f'/api/video-calls/{session.id}/end/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        session.refresh_from_db()
        self.assertEqual(session.status, 'ended')


class VideoCallIntegrationTest(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username='admin', email='admin@test.com',
            password='pass', user_type='admin'
        )
        self.admin.user_permissions.add(
            Permission.objects.get(codename='can_create_video_call')
        )
        self.client_user = User.objects.create_user(
            username='client', email='client@test.com',
            password='pass', user_type='client'
        )
        self.expert = User.objects.create_user(
            username='expert', email='expert@test.com',
            password='pass', user_type='expert'
        )
        self.project = Project.objects.create(
            client=self.client_user,
            expert=self.expert,
            title='Test Project'
        )

    def test_video_call_creation_creates_notifications(self):
        """Test that creating a video call creates notifications for participants"""
        from rest_framework.test import APIClient
        client = APIClient()
        client.force_authenticate(user=self.admin)

        data = {'contract': self.project.id}
        response = client.post('/api/video-calls/', data)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Notification.objects.count(), 2)  # One for client, one for expert

        notifications = Notification.objects.all()
        recipients = [n.recipient for n in notifications]
        self.assertIn(self.client_user, recipients)
        self.assertIn(self.expert, recipients)

        for notification in notifications:
            self.assertEqual(notification.notification_type, 'video_call')
            self.assertEqual(notification.title, 'Video Call Invitation')



