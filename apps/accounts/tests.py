from django.test import TestCase, Client
from django.urls import reverse
from apps.accounts.models import User


class AccountsTestCase(TestCase):
    """Tests for authentication and admin management."""
    
    def setUp(self):
        """Set up test client and create test admin user."""
        self.client = Client()
        self.admin = User.objects.create_superuser(
            email='admin@test.com',
            password='testpass123'
        )
    
    def test_unauthorized_user_redirected_to_login(self):
        """Test that unauthorized users are redirected to login page."""
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)
    
    def test_admin_can_login(self):
        """Test that admin users can login successfully."""
        response = self.client.post(reverse('login'), {
            'email': 'admin@test.com',
            'password': 'testpass123'
        })
        # Should redirect to dashboard after successful login
        self.assertEqual(response.status_code, 302)
    
    def test_admin_list_requires_login(self):
        """Test that admin list page requires authentication."""
        response = self.client.get(reverse('admin_list'))
        self.assertEqual(response.status_code, 302)
        
        # Login and try again
        self.client.login(username='admin@test.com', password='testpass123')
        response = self.client.get(reverse('admin_list'))
        self.assertEqual(response.status_code, 200)
    
    def test_cannot_delete_self(self):
        """Test that admins cannot delete their own account."""
        self.client.login(username='admin@test.com', password='testpass123')
        response = self.client.post(reverse('admin_delete', args=[self.admin.id]))
        
        # Should redirect with error message
        self.assertEqual(response.status_code, 302)
        
        # Admin should still exist
        self.assertTrue(User.objects.filter(id=self.admin.id).exists())
