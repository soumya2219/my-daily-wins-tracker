from django.shortcuts import render
from django.http import HttpResponse
from django.conf import settings
import os

# Create your views here.
def home(request):
    return render(request, "home.html")

def debug_info(request):
    """Debug view to see what's happening on Heroku"""
    debug_info = f"""
    <h1>Debug Info</h1>
    <p><strong>DEBUG:</strong> {settings.DEBUG}</p>
    <p><strong>ALLOWED_HOSTS:</strong> {settings.ALLOWED_HOSTS}</p>
    <p><strong>CSRF_TRUSTED_ORIGINS:</strong> {settings.CSRF_TRUSTED_ORIGINS}</p>
    <p><strong>DATABASE_URL set:</strong> {bool(os.environ.get('DATABASE_URL'))}</p>
    <p><strong>SECRET_KEY set:</strong> {bool(os.environ.get('SECRET_KEY'))}</p>
    <p><strong>Request Host:</strong> {request.get_host()}</p>
    <p><strong>Request Path:</strong> {request.path}</p>
    """
    return HttpResponse(debug_info)
