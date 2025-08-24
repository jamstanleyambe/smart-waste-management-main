import logging
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
from .user_management import log_login_attempt

logger = logging.getLogger(__name__)
User = get_user_model()

class EnhancedAuthenticationBackend(ModelBackend):
    """
    Enhanced authentication backend with security features:
    - Login attempt tracking
    - IP-based blocking
    - Account lockout protection
    - Audit logging
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        if not username or not password:
            return None
            
        # Check for IP-based blocking
        if self._is_ip_blocked(request):
            logger.warning(f"Login attempt from blocked IP: {self._get_client_ip(request)}")
            return None
            
        # Check for account lockout
        if self._is_account_locked(username):
            logger.warning(f"Login attempt for locked account: {username}")
            return None
            
        # Attempt authentication
        try:
            user = User.objects.get(username=username)
            
            # Check if user is active
            if not user.is_active:
                logger.warning(f"Login attempt for inactive user: {username}")
                return None
                
            # Verify password
            if user.check_password(password):
                # Reset failed attempts on successful login
                self._reset_failed_attempts(username, request)
                ip = self._get_client_ip(request)
                log_login_attempt(username, ip, success=True)
                logger.info(f"Successful login: {username} from {ip}")
                return user
            else:
                # Increment failed attempts
                self._increment_failed_attempts(username, request)
                ip = self._get_client_ip(request)
                log_login_attempt(username, ip, success=False)
                logger.warning(f"Failed login attempt: {username} from {ip}")
                return None
                
        except User.DoesNotExist:
            # Don't reveal if user exists or not
            self._increment_failed_attempts(username, request)
            ip = self._get_client_ip(request)
            log_login_attempt(username, ip, success=False)
            logger.warning(f"Login attempt for non-existent user: {username} from {ip}")
            return None
            
    def _get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
        
    def _get_cache_key(self, identifier, prefix):
        """Generate cache key for tracking"""
        return f"{prefix}:{identifier}"
        
    def _is_ip_blocked(self, request):
        """Check if IP is blocked due to too many failed attempts"""
        ip = self._get_client_ip(request)
        cache_key = self._get_cache_key(ip, 'ip_blocked')
        return cache.get(cache_key, False)
        
    def _is_account_locked(self, username):
        """Check if account is locked due to too many failed attempts"""
        cache_key = self._get_cache_key(username, 'account_locked')
        return cache.get(cache_key, False)
        
    def _increment_failed_attempts(self, username, request):
        """Increment failed login attempts"""
        ip = self._get_client_ip(request)
        
        # Track IP-based attempts
        ip_key = self._get_cache_key(ip, 'ip_attempts')
        ip_attempts = cache.get(ip_key, 0) + 1
        cache.set(ip_key, ip_attempts, 3600)  # 1 hour
        
        # Track user-based attempts
        user_key = self._get_cache_key(username, 'user_attempts')
        user_attempts = cache.get(user_key, 0) + 1
        cache.set(user_key, user_attempts, 3600)  # 1 hour
        
        # Block IP if too many attempts
        if ip_attempts >= 10:
            cache.set(self._get_cache_key(ip, 'ip_blocked'), True, 3600)  # 1 hour
            logger.warning(f"IP blocked due to too many failed attempts: {ip}")
            
        # Lock account if too many attempts
        if user_attempts >= 5:
            cache.set(self._get_cache_key(username, 'account_locked'), True, 1800)  # 30 minutes
            logger.warning(f"Account locked due to too many failed attempts: {username}")
            
    def _reset_failed_attempts(self, username, request):
        """Reset failed attempts on successful login"""
        ip = self._get_client_ip(request)
        
        # Reset IP attempts
        ip_key = self._get_cache_key(ip, 'ip_attempts')
        cache.delete(ip_key)
        
        # Reset user attempts
        user_key = self._get_cache_key(username, 'user_attempts')
        cache.delete(user_key)
        
        # Unblock IP and unlock account
        cache.delete(self._get_cache_key(ip, 'ip_blocked'))
        cache.delete(self._get_cache_key(username, 'account_locked'))
