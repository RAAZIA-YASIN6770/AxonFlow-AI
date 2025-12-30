from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from .models import User


class UserRegistrationForm(UserCreationForm):
    """Custom registration form"""
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


def register(request):
    """User registration view"""
    if request.user.is_authenticated:
        return redirect('document_list')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.role = User.Roles.USER  # Default role
            user.save()
            
            # Log the user in
            login(request, user)
            messages.success(request, f'Welcome {user.username}! Your account has been created.')
            return redirect('document_list')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'registration/register.html', {'form': form})
