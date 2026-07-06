import csv
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Sum, Count
from .models import Donation
from .forms import DonationForm, DonationFilterForm


def is_admin(user):
    """Check if user is staff/admin."""
    return user.is_authenticated and user.is_staff


@login_required
@user_passes_test(is_admin, login_url='login')
def dashboard_view(request):
    """Main dashboard with donations list, filtering, and analytics."""
    donations = Donation.objects.all()
    
    # Initialize filter form
    filter_form = DonationFilterForm(request.GET or None)
    
    # Apply filters
    if filter_form.is_valid():
        # Search by donor name or pet name
        search = filter_form.cleaned_data.get('search')
        if search:
            donations = donations.filter(
                Q(donor_name__icontains=search) | Q(pet_name__icontains=search)
            )
        
        # Date range filter
        date_from = filter_form.cleaned_data.get('date_from')
        if date_from:
            donations = donations.filter(donation_date__date__gte=date_from)
        
        date_to = filter_form.cleaned_data.get('date_to')
        if date_to:
            donations = donations.filter(donation_date__date__lte=date_to)
        
        # Payment method filter
        payment_method = filter_form.cleaned_data.get('payment_method')
        if payment_method:
            donations = donations.filter(payment_method=payment_method)
        
        # Currency filter
        currency = filter_form.cleaned_data.get('currency')
        if currency:
            donations = donations.filter(currency__iexact=currency)
        
        # Amount range filter
        amount_min = filter_form.cleaned_data.get('amount_min')
        if amount_min is not None:
            donations = donations.filter(amount__gte=amount_min)
        
        amount_max = filter_form.cleaned_data.get('amount_max')
        if amount_max is not None:
            donations = donations.filter(amount__lte=amount_max)
        
        # Sorting
        sort_by = filter_form.cleaned_data.get('sort_by') or '-donation_date'
        donations = donations.order_by(sort_by)
    else:
        donations = donations.order_by('-donation_date')
    
    # Calculate analytics
    total_all_time = Donation.objects.aggregate(total=Sum('amount'))['total'] or 0
    total_filtered = donations.aggregate(total=Sum('amount'))['total'] or 0
    
    # Top 5 pets by donation amount, within the current filters
    top_pets = (
        donations
        .values('pet_name')
        .annotate(total_amount=Sum('amount'), donation_count=Count('id'))
        .order_by('-total_amount')[:5]
    )
    
    # Pagination
    paginator = Paginator(donations, 20)  # 20 donations per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Store filtered queryset in session for CSV export
    request.session['filtered_donation_ids'] = list(donations.values_list('id', flat=True))
    
    context = {
        'page_obj': page_obj,
        'filter_form': filter_form,
        'total_all_time': total_all_time,
        'total_filtered': total_filtered,
        'top_pets': top_pets,
        'total_count': donations.count(),
    }
    
    return render(request, 'donations/dashboard.html', context)


@login_required
@user_passes_test(is_admin, login_url='login')
def donation_create_view(request):
    """Create a new donation."""
    if request.method == 'POST':
        form = DonationForm(request.POST)
        if form.is_valid():
            donation = form.save()
            messages.success(request, f'Donation from {donation.donor_name} created successfully!')
            return redirect('dashboard')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = DonationForm()
    
    return render(request, 'donations/donation_form.html', {
        'form': form,
        'title': 'Add New Donation'
    })


@login_required
@user_passes_test(is_admin, login_url='login')
def donation_update_view(request, pk):
    """Update an existing donation."""
    donation = get_object_or_404(Donation, pk=pk)
    
    if request.method == 'POST':
        form = DonationForm(request.POST, instance=donation)
        if form.is_valid():
            donation = form.save()
            messages.success(request, f'Donation from {donation.donor_name} updated successfully!')
            return redirect('dashboard')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = DonationForm(instance=donation)
    
    return render(request, 'donations/donation_form.html', {
        'form': form,
        'title': 'Edit Donation',
        'donation': donation
    })


@login_required
@user_passes_test(is_admin, login_url='login')
def donation_delete_view(request, pk):
    """Delete a donation with confirmation."""
    donation = get_object_or_404(Donation, pk=pk)
    
    if request.method == 'POST':
        donor_name = donation.donor_name
        donation.delete()
        messages.success(request, f'Donation from {donor_name} has been deleted.')
        return redirect('dashboard')
    
    return render(request, 'donations/donation_confirm_delete.html', {
        'donation': donation
    })


@login_required
@user_passes_test(is_admin, login_url='login')
def export_csv_view(request):
    """Export filtered donations to CSV file."""
    # Get filtered donation IDs from session
    filtered_ids = request.session.get('filtered_donation_ids', [])
    
    if filtered_ids:
        donations = Donation.objects.filter(id__in=filtered_ids).order_by('-donation_date')
    else:
        donations = Donation.objects.all().order_by('-donation_date')
    
    # Create CSV response
    timestamp = datetime.now().strftime('%Y-%m-%d')
    filename = f'donations_{timestamp}.csv'
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    # Create CSV writer
    writer = csv.writer(response, quoting=csv.QUOTE_ALL)
    
    # Write header
    writer.writerow([
        'ID',
        'Donor Name',
        'Donor Phone',
        'Donor Email',
        'Pet Name',
        'Amount',
        'Currency',
        'Payment Method',
        'Reference No',
        'Donation Date',
        'Notes',
        'Created At',
    ])
    
    # Write donation data
    for donation in donations:
        writer.writerow([
            donation.id,
            donation.donor_name,
            donation.donor_phone or '',
            donation.donor_email or '',
            donation.pet_name,
            str(donation.amount),
            donation.currency,
            donation.get_payment_method_display(),
            donation.reference_no or '',
            donation.donation_date.strftime('%Y-%m-%d %H:%M:%S'),
            donation.notes or '',
            donation.created_at.strftime('%Y-%m-%d %H:%M:%S'),
        ])
    
    return response
