from django.test import TestCase, Client
from django.urls import reverse
from decimal import Decimal
from apps.accounts.models import User
from apps.donations.models import Donation


class DonationsTestCase(TestCase):
    """Tests for donation management functionality."""
    
    def setUp(self):
        """Set up test client, admin user, and sample donations."""
        self.client = Client()
        self.admin = User.objects.create_superuser(
            email='admin@test.com',
            password='testpass123'
        )
        self.client.login(username='admin@test.com', password='testpass123')
        
        # Create sample donations
        self.donation1 = Donation.objects.create(
            donor_name='John Doe',
            pet_name='Max',
            amount=Decimal('1000.00'),
            currency='PKR',
            payment_method='cash'
        )
        self.donation2 = Donation.objects.create(
            donor_name='Jane Smith',
            pet_name='Bella',
            amount=Decimal('500.00'),
            currency='PKR',
            payment_method='online'
        )
    
    def test_admin_can_access_dashboard(self):
        """Test that admin can access the dashboard."""
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Donation Dashboard')
    
    def test_admin_can_create_donation(self):
        """Test that admin can create a new donation."""
        initial_count = Donation.objects.count()
        
        response = self.client.post(reverse('donation_create'), {
            'donor_name': 'Test Donor',
            'pet_name': 'Fluffy',
            'amount': '250.00',
            'currency': 'PKR',
            'payment_method': 'bank',
        })
        
        # Should redirect to dashboard
        self.assertEqual(response.status_code, 302)
        
        # Should have one more donation
        self.assertEqual(Donation.objects.count(), initial_count + 1)
        
        # Verify the donation was created correctly
        donation = Donation.objects.get(donor_name='Test Donor')
        self.assertEqual(donation.pet_name, 'Fluffy')
        self.assertEqual(donation.amount, Decimal('250.00'))
    
    def test_csv_export_returns_csv_response(self):
        """Test that CSV export returns proper CSV file."""
        response = self.client.get(reverse('export_csv'))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertIn('donations_', response['Content-Disposition'])
        
        # Check that CSV contains donation data
        content = response.content.decode('utf-8')
        self.assertIn('Donor Name', content)  # Header
        self.assertIn('John Doe', content)    # Data
        self.assertIn('Max', content)
    
    def test_search_by_donor_name(self):
        """Test filtering donations by donor name."""
        response = self.client.get(reverse('dashboard'), {'search': 'John'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'John Doe')
        self.assertNotContains(response, 'Jane Smith')
    
    def test_search_by_pet_name(self):
        """Test filtering donations by pet name."""
        response = self.client.get(reverse('dashboard'), {'search': 'Bella'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Bella')
        self.assertNotContains(response, 'Max')
    
    def test_filter_by_payment_method(self):
        """Test filtering donations by payment method."""
        response = self.client.get(reverse('dashboard'), {'payment_method': 'cash'})
        self.assertEqual(response.status_code, 200)
        # Should show cash donations
        self.assertContains(response, 'John Doe')
    
    def test_amount_validation(self):
        """Test that negative amounts are not allowed."""
        response = self.client.post(reverse('donation_create'), {
            'donor_name': 'Test Donor',
            'pet_name': 'Fluffy',
            'amount': '-100.00',
            'currency': 'PKR',
            'payment_method': 'cash',
        })
        
        # Should not create the donation
        self.assertFalse(Donation.objects.filter(donor_name='Test Donor').exists())
