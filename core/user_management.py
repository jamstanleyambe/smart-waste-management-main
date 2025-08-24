import logging
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_protect
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
from .models import Role

logger = logging.getLogger(__name__)
User = get_user_model()

def is_admin(user):
    """Check if user is admin"""
    return user.is_authenticated and user.is_staff

@login_required
@user_passes_test(is_admin)
def user_dashboard(request):
    """User management dashboard"""
    users = User.objects.all().order_by('-date_joined')
    roles = Role.objects.all()
    
    # Get user statistics
    total_users = users.count()
    active_users = users.filter(is_active=True).count()
    inactive_users = users.filter(is_active=False).count()
    staff_users = users.filter(is_staff=True).count()
    
    # Get recent login attempts
    recent_logins = cache.get('recent_logins', [])
    
    context = {
        'users': users,
        'roles': roles,
        'total_users': total_users,
        'active_users': active_users,
        'inactive_users': inactive_users,
        'staff_users': staff_users,
        'recent_logins': recent_logins,
    }
    
    return render(request, 'admin/user_dashboard.html', context)

@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
@csrf_protect
def toggle_user_status(request, user_id):
    """Toggle user active status"""
    try:
        user = get_object_or_404(User, id=user_id)
        user.is_active = not user.is_active
        user.save()
        
        action = "activated" if user.is_active else "deactivated"
        logger.info(f"User {user.username} {action} by {request.user.username}")
        
        messages.success(request, f"User {user.username} has been {action}.")
        
        return JsonResponse({
            'success': True,
            'message': f"User {user.username} has been {action}.",
            'is_active': user.is_active
        })
        
    except Exception as e:
        logger.error(f"Error toggling user status: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'An error occurred while updating user status.'
        }, status=500)

@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
@csrf_protect
def reset_user_password(request, user_id):
    """Reset user password"""
    try:
        user = get_object_or_404(User, id=user_id)
        
        # Generate temporary password
        import secrets
        import string
        temp_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
        
        # Set password
        user.set_password(temp_password)
        user.save()
        
        # Clear any account locks
        cache.delete(f'user_attempts:{user.username}')
        cache.delete(f'account_locked:{user.username}')
        
        logger.info(f"Password reset for user {user.username} by {request.user.username}")
        
        messages.success(request, f"Password reset for {user.username}. Temporary password: {temp_password}")
        
        return JsonResponse({
            'success': True,
            'message': f"Password reset for {user.username}.",
            'temp_password': temp_password
        })
        
    except Exception as e:
        logger.error(f"Error resetting password: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'An error occurred while resetting password.'
        }, status=500)

@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
@csrf_protect
def unlock_user_account(request, user_id):
    """Unlock user account"""
    try:
        user = get_object_or_404(User, id=user_id)
        
        # Clear account locks
        cache.delete(f'user_attempts:{user.username}')
        cache.delete(f'account_locked:{user.username}')
        
        logger.info(f"Account unlocked for user {user.username} by {request.user.username}")
        
        messages.success(request, f"Account unlocked for {user.username}.")
        
        return JsonResponse({
            'success': True,
            'message': f"Account unlocked for {user.username}."
        })
        
    except Exception as e:
        logger.error(f"Error unlocking account: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'An error occurred while unlocking account.'
        }, status=500)

@login_required
@user_passes_test(is_admin)
def user_activity_log(request):
    """View user activity log"""
    # Get recent login attempts from cache
    recent_logins = cache.get('recent_logins', [])
    
    # Get failed login attempts
    failed_attempts = []
    for key in cache.keys('*attempts*'):
        attempts = cache.get(key)
        if attempts:
            failed_attempts.append({
                'identifier': key,
                'attempts': attempts
            })
    
    context = {
        'recent_logins': recent_logins,
        'failed_attempts': failed_attempts,
    }
    
    return render(request, 'admin/user_activity_log.html', context)

@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
@csrf_protect
def clear_ip_block(request):
    """Clear IP block"""
    try:
        ip_address = request.POST.get('ip_address')
        
        if ip_address:
            # Clear IP blocks
            cache.delete(f'ip_attempts:{ip_address}')
            cache.delete(f'ip_blocked:{ip_address}')
            
            logger.info(f"IP block cleared for {ip_address} by {request.user.username}")
            
            messages.success(request, f"IP block cleared for {ip_address}.")
            
            return JsonResponse({
                'success': True,
                'message': f"IP block cleared for {ip_address}."
            })
        else:
            return JsonResponse({
                'success': False,
                'message': 'IP address is required.'
            }, status=400)
            
    except Exception as e:
        logger.error(f"Error clearing IP block: {str(e)}")
        return JsonResponse({
            'success': False,
            'message': 'An error occurred while clearing IP block.'
        }, status=500)

def log_login_attempt(username, ip_address, success=True):
    """Log login attempt"""
    log_entry = {
        'username': username,
        'ip_address': ip_address,
        'success': success,
        'timestamp': timezone.now().isoformat(),
    }
    
    # Store in cache (last 100 attempts)
    recent_logins = cache.get('recent_logins', [])
    recent_logins.append(log_entry)
    
    # Keep only last 100 entries
    if len(recent_logins) > 100:
        recent_logins = recent_logins[-100:]
    
    cache.set('recent_logins', recent_logins, 86400)  # 24 hours
