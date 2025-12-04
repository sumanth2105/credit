
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Beneficiary, Profile
from unittest.mock import patch

class AuthTests(TestCase):

    def setUp(self):
        self.client = Client()

    @patch('api.views.send_otp_sms')
    def test_beneficiary_register_success(self, mock_send_otp):
        """
        Tests successful beneficiary registration and redirection to OTP verification.
        """
        response = self.client.post(reverse('beneficiary_register'), {
            'username': 'testuser',
            'password': 'password123',
            'name': 'Test User',
            'age': 30,
            'phone': '+1234567890',
            'consent_given': True
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('beneficiary_verify_otp'))
        self.assertTrue(User.objects.filter(username='testuser').exists())
        self.assertTrue(Beneficiary.objects.filter(phone='+1234567890').exists())
        beneficiary = Beneficiary.objects.get(phone='+1234567890')
        self.assertIsNotNone(beneficiary.otp_code)
        mock_send_otp.assert_called_once()
        self.assertIn('pending_beneficiary_user_id', self.client.session)

    def test_beneficiary_register_user_exists(self):
        """
        Tests registration with a username that already exists.
        """
        User.objects.create_user('testuser', 'test@example.com', 'password123')
        response = self.client.post(reverse('beneficiary_register'), {
            'username': 'testuser',
            'password': 'password123',
            'name': 'Test User',
            'age': 30,
            'phone': '+1234567890',
            'consent_given': True
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "This username is already taken")

    @patch('api.views.send_otp_sms')
    def test_beneficiary_verify_otp_success(self, mock_send_otp):
        """
        Tests successful OTP verification and user login.
        """
        # First, register a user to have a beneficiary to verify
        self.client.post(reverse('beneficiary_register'), {
            'username': 'testuser',
            'password': 'password123',
            'name': 'Test User',
            'age': 30,
            'phone': '+1234567890',
            'consent_given': True
        })
        
        beneficiary = Beneficiary.objects.get(phone='+1234567890')
        otp = beneficiary.otp_code
        
        response = self.client.post(reverse('beneficiary_verify_otp'), {'otp': otp})
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/beneficiary/profile/')
        
        beneficiary.refresh_from_db()
        self.assertTrue(beneficiary.is_phone_verified)
        
        user = User.objects.get(username='testuser')
        self.assertTrue(user.is_authenticated)
        
        self.assertNotIn('pending_beneficiary_user_id', self.client.session)

    @patch('api.views.send_otp_sms')
    def test_beneficiary_verify_otp_invalid(self, mock_send_otp):
        """
        Tests OTP verification with an invalid OTP.
        """
        self.client.post(reverse('beneficiary_register'), {
            'username': 'testuser',
            'password': 'password123',
            'name': 'Test User',
            'age': 30,
            'phone': '+1234567890',
            'consent_given': True
        })
        
        response = self.client.post(reverse('beneficiary_verify_otp'), {'otp': 'wrongotp'})
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid or expired OTP")
        
        beneficiary = Beneficiary.objects.get(phone='+1234567890')
        self.assertFalse(beneficiary.is_phone_verified)

    def test_beneficiary_verify_otp_no_session(self):
        """
        Tests accessing OTP verification page without a pending user in the session.
        """
        response = self.client.get(reverse('beneficiary_verify_otp'))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('beneficiary_register'))
