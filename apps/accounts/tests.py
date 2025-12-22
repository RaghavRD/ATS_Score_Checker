from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from apps.analyzer.models import AnalysisResult

class AuthenticationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.signup_url = reverse('signup')
        self.login_url = reverse('login')
        self.history_url = reverse('analyzer:history')
        self.home_url = reverse('analyzer:home')
        self.user_data = {
            'username': 'testuser',
            'password': 'testpassword123',
            'password_confirmation': 'testpassword123'
        }

    def test_signup_view(self):
        response = self.client.get(self.signup_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/signup.html')

    def test_signup_creates_user(self):
        # UserCreationForm requires password1 and password2
        signup_data = {
            'username': self.user_data['username'],
            'password1': self.user_data['password'],
            'password2': self.user_data['password'],
        }
        
        response = self.client.post(self.signup_url, signup_data)
        
        # Check if form error prints
        if response.status_code == 200:
             print(response.context['form'].errors)

        self.assertTrue(User.objects.filter(username='testuser').exists())
        self.assertEqual(response.status_code, 302) 

    def test_login_view(self):
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/login.html')

    def test_login_functionality(self):
        user_data_for_create = self.user_data.copy()
        if 'password_confirmation' in user_data_for_create:
            user_data_for_create.pop('password_confirmation')
            
        User.objects.create_user(**user_data_for_create)
        
        # Login needs original data (without confirmation usually, but Client.login needs username/password)
        login_data = {
            'username': self.user_data['username'],
            'password': self.user_data['password']
        }
        response = self.client.post(self.login_url, login_data)
        self.assertEqual(response.status_code, 302) # Redirects to home
        # Verify authenticated session
        response = self.client.get(self.home_url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['user'].is_authenticated)

    def test_home_access_denied_anonymous(self):
        response = self.client.get(self.home_url)
        self.assertEqual(response.status_code, 302)
        # Should redirect to login? Or generic login? standard is /accounts/login/ or settings.LOGIN_URL
        # We need to ensure it redirects to our login page
        self.assertTrue(self.login_url in response.url)

    def test_history_access_denied_anonymous(self):
        response = self.client.get(self.history_url)
        self.assertNotEqual(response.status_code, 200)
        # Should redirect to login
        self.assertEqual(response.status_code, 302)

    def test_history_access_allowed_authenticated(self):
        user_data_for_create = self.user_data.copy()
        if 'password_confirmation' in user_data_for_create:
            user_data_for_create.pop('password_confirmation')
        user = User.objects.create_user(**user_data_for_create)
        self.client.force_login(user)
        response = self.client.get(self.history_url)
        self.assertEqual(response.status_code, 200)

    def test_analysis_saved_to_user(self):
        user_data_for_create = self.user_data.copy()
        if 'password_confirmation' in user_data_for_create:
            user_data_for_create.pop('password_confirmation')
        user = User.objects.create_user(**user_data_for_create)
        self.client.force_login(user)
        
        # Simulate a post request to upload resume (mocking file upload is complex, so we just check model behavior directly if view logic is standard, 
        # but let's try a simple flow or just creating object linked to user to ensure model works)
        
        # Test Model directly
        result = AnalysisResult.objects.create(
            user=user,
            job_description_snippet="test",
            resume_filename="test.pdf",
            final_score=50,
            keyword_score=50,
            semantic_score=50,
            formatting_score=50,
            data={}
        )
        self.assertEqual(result.user, user)
