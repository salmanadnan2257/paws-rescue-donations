from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from .forms import EmailAuthenticationForm, AdminCreationForm
from .models import User


def is_admin(user):
    """Check if user is staff/admin."""
    return user.is_authenticated and user.is_staff


def login_view(request):
    """Handle user login with email and password."""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = EmailAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user and user.is_staff:
                login(request, user)
                messages.success(request, f'Welcome back, {user.email}!')
                return redirect('dashboard')
            else:
                messages.error(request, 'You do not have permission to access this application.')
        else:
            for error in form.non_field_errors():
                messages.error(request, error)
    else:
        form = EmailAuthenticationForm()
    
    return render(request, 'accounts/login.html', {'form': form})


@require_http_methods(["POST", "GET"])
def logout_view(request):
    """Handle user logout."""
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('login')


@login_required
@user_passes_test(is_admin, login_url='login')
def admin_list_view(request):
    """Display list of all admin users."""
    admins = User.objects.filter(is_staff=True).order_by('-created_at')
    return render(request, 'accounts/admin_list.html', {
        'admins': admins,
        'current_user_id': request.user.id
    })


@login_required
@user_passes_test(is_admin, login_url='login')
def admin_create_view(request):
    """Create a new admin user."""
    if request.method == 'POST':
        form = AdminCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f'Admin user {user.email} created successfully!')
            return redirect('admin_list')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = AdminCreationForm()
    
    return render(request, 'accounts/admin_form.html', {'form': form})


@login_required
@user_passes_test(is_admin, login_url='login')
@require_http_methods(["POST"])
def admin_delete_view(request, user_id):
    """Delete an admin user (cannot delete yourself)."""
    user_to_delete = get_object_or_404(User, id=user_id)
    
    # Prevent self-deletion
    if user_to_delete.id == request.user.id:
        messages.error(request, 'You cannot delete your own account.')
        return redirect('admin_list')
    
    email = user_to_delete.email
    user_to_delete.delete()
    messages.success(request, f'Admin user {email} has been deleted.')
    return redirect('admin_list')
