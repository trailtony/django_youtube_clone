import logging
from django.shortcuts import redirect
from django.contrib.auth import login
from django.views.generic import CreateView
from django.urls import reverse_lazy
from .forms import CustomUserCreationForm

logger = logging.getLogger('accounts')

# Create your views here.
class RegisterView(CreateView):
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('accounts:login')
    template_name = "accounts/register.html"
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            logger.info(f"Authenticated user {request.user.username} attempted to access registration page")
            return redirect("/")
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        response = super().form_valid(form)
        logger.info(f"New user registered: {self.object.username} (email: {self.object.email})")
        login(self.request, self.object)
        logger.info(f"User {self.object.username} auto-logged in after registration")
        return redirect("/")
