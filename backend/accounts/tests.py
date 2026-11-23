from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from accounts.models import Email, UserPreference, PersonalKnowledge


class AccountAPITestCase(APITestCase):

    def setUp(self):
        self.username = 'testuser'
        self.email = 'testuser@example.com'
        self.password = 'password123'
        self.user = User.objects.create_user(
            username=self.username,
            email=self.email,
            password=self.password
        )
        self.register_url = reverse('register')
        self.login_url = reverse('token_obtain_pair')
        self.profile_url = reverse('profile')
        self.emails_url = reverse('emails')
        self.preferences_url = reverse('preferences')
        self.knowledge_url = reverse('knowledge')

    def test_user_registration_success(self):
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'securepassword123'
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['username'], 'newuser')

    def test_user_registration_duplicate_username(self):
        data = {
            'username': self.username,
            'email': 'different@example.com',
            'password': 'password123'
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_user_login(self):
        data = {
            'username': self.username,
            'password': self.password
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_authenticated_profile(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], self.username)

    def test_create_and_list_emails(self):
        self.client.force_authenticate(user=self.user)
        data = {
            'sender': 'client@example.com',
            'recipient': self.email,
            'subject': 'Project Update',
            'body': 'Here is the update on our project progress.'
        }
        create_res = self.client.post(self.emails_url, data, format='json')
        self.assertEqual(create_res.status_code, status.HTTP_201_CREATED)

        list_res = self.client.get(self.emails_url)
        self.assertEqual(list_res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_res.data), 1)

    def test_user_preferences_get_and_update(self):
        self.client.force_authenticate(user=self.user)
        get_res = self.client.get(self.preferences_url)
        self.assertEqual(get_res.status_code, status.HTTP_200_OK)

        update_data = {
            'tone': 'professional',
            'reply_length': 'medium',
            'greeting': 'Dear Client,',
            'sign_off': 'Best regards,'
        }
        put_res = self.client.put(self.preferences_url, update_data, format='json')
        self.assertEqual(put_res.status_code, status.HTTP_200_OK)
        self.assertEqual(put_res.data['tone'], 'professional')

    def test_personal_knowledge_crud(self):
        self.client.force_authenticate(user=self.user)
        data = {
            'title': 'Experience',
            'content': '5 years of Python and Django development.'
        }
        res = self.client.post(self.knowledge_url, data, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        list_res = self.client.get(self.knowledge_url)
        self.assertEqual(list_res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_res.data), 1)

