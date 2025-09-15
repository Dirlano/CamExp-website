#!/usr/bin/env python3
"""
CamExp Admin Panel Setup Script
This script automates the initial setup of the CamExp admin panel.
"""

import os
import sys
import django
from pathlib import Path

def setup_django():
    """Configure Django settings and setup."""
    # Add the project directory to Python path
    project_dir = Path(__file__).resolve().parent
    sys.path.insert(0, str(project_dir))
    
    # Set Django settings module
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'camexp.settings')
    
    # Setup Django
    django.setup()
    
    print("✅ Django configured successfully")

def create_superuser():
    """Create a superuser account for admin access."""
    try:
        from django.contrib.auth.models import User
        from django.core.management import call_command
        
        # Check if superuser already exists
        if User.objects.filter(is_superuser=True).exists():
            print("ℹ️  Superuser already exists")
            return
        
        print("🔐 Creating superuser account...")
        call_command('createsuperuser', interactive=False)
        print("✅ Superuser created successfully")
        
    except Exception as e:
        print(f"❌ Error creating superuser: {e}")

def verify_setup():
    """Verify that the admin panel is properly configured."""
    try:
        from django.contrib.admin.sites import site
        from django.contrib.auth.models import User
        from accounts.models import Profile
        from services.models import ServiceListing, RequestPost, Reaction, Rating
        from chat.models import Message
        from payments.models import Payment
        from notifications.models import Notification
        from projects.models import Project, Event
        
        # Check if models are registered
        registered_models = site._registry.keys()
        
        expected_models = {
            User, Profile, ServiceListing, RequestPost, 
            Reaction, Rating, Message, Payment, 
            Notification, Project, Event
        }
        
        missing_models = expected_models - set(registered_models)
        
        if missing_models:
            print(f"⚠️  Missing models in admin: {missing_models}")
        else:
            print("✅ All models are registered in admin")
        
        # Check if superuser exists
        if User.objects.filter(is_superuser=True).exists():
            print("✅ Superuser account exists")
        else:
            print("❌ No superuser account found")
        
        print("✅ Admin panel setup verification completed")
        
    except Exception as e:
        print(f"❌ Error during verification: {e}")

def display_next_steps():
    """Display next steps for the user."""
    print("\n" + "="*60)
    print("🎉 ADMIN PANEL SETUP COMPLETE!")
    print("="*60)
    print("\n📋 Next Steps:")
    print("1. Start your Django development server:")
    print("   python manage.py runserver")
    print("\n2. Access the admin panel at:")
    print("   http://127.0.0.1:8000/admin/")
    print("\n3. Login with your superuser credentials")
    print("\n4. Explore the admin panel features:")
    print("   - User and Profile management")
    print("   - Service listings and requests")
    print("   - Chat message management")
    print("   - Payment tracking")
    print("   - Notification management")
    print("   - Project and event scheduling")
    print("\n5. Customize the admin interface as needed")
    print("\n📚 For detailed information, see: ADMIN_PANEL_GUIDE.md")
    print("="*60)

def main():
    """Main setup function."""
    print("🚀 Starting CamExp Admin Panel Setup...")
    print("="*50)
    
    try:
        # Setup Django first
        setup_django()
        
        # Create superuser
        create_superuser()
        
        # Verify setup
        verify_setup()
        
        # Display next steps
        display_next_steps()
        
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Make sure you're in the project root directory")
        print("2. Ensure Django is installed: pip install django")
        print("3. Check that all required apps are in INSTALLED_APPS")
        print("4. Verify your database migrations are up to date")
        sys.exit(1)

if __name__ == "__main__":
    main()
