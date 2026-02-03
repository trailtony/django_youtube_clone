"""
Logging utilities for structured logging and sensitive data filtering.
"""
import logging
import re
from typing import Any, Dict


class SensitiveDataFilter(logging.Filter):
    """
    Filter to redact sensitive information from logs.
    Prevents PII (Personally Identifiable Information) leaks.
    """
    
    SENSITIVE_PATTERNS = [
        (re.compile(r'password["\']?\s*[:=]\s*["\']?([^"\'&\s]+)', re.IGNORECASE), r'password=***REDACTED***'),
        (re.compile(r'token["\']?\s*[:=]\s*["\']?([^"\'&\s]+)', re.IGNORECASE), r'token=***REDACTED***'),
        (re.compile(r'api[_-]?key["\']?\s*[:=]\s*["\']?([^"\'&\s]+)', re.IGNORECASE), r'api_key=***REDACTED***'),
        (re.compile(r'secret["\']?\s*[:=]\s*["\']?([^"\'&\s]+)', re.IGNORECASE), r'secret=***REDACTED***'),
        # Email partial redaction
        (re.compile(r'([a-zA-Z0-9._%+-]+)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'), r'\1***@\2'),
    ]
    
    def filter(self, record):
        if isinstance(record.msg, str):
            for pattern, replacement in self.SENSITIVE_PATTERNS:
                record.msg = pattern.sub(replacement, record.msg)
        return True


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with sensitive data filtering applied.
    
    Args:
        name: Logger name (usually __name__)
    
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.addFilter(SensitiveDataFilter())
    return logger


def log_with_context(logger: logging.Logger, level: str, message: str, **context):
    """
    Log a message with structured context.
    
    Args:
        logger: Logger instance
        level: Log level ('debug', 'info', 'warning', 'error', 'critical')
        message: Log message
        **context: Additional context as key-value pairs
    
    Example:
        log_with_context(logger, 'info', 'Video uploaded', 
                        user_id=user.id, video_id=video.id, size_mb=file_size)
    """
    log_func = getattr(logger, level.lower())
    
    if context:
        context_str = ' '.join(f'{k}={v}' for k, v in context.items())
        log_func(f'{message} | {context_str}')
    else:
        log_func(message)


def log_exception(logger: logging.Logger, message: str, exc: Exception, **context):
    """
    Log an exception with context and full traceback.
    
    Args:
        logger: Logger instance
        message: Error message
        exc: Exception instance
        **context: Additional context
    """
    context['exception_type'] = exc.__class__.__name__
    context['exception_message'] = str(exc)
    
    log_with_context(logger, 'error', message, **context)
    logger.exception(exc)


class RequestLogger:
    """
    Middleware-compatible logger for HTTP requests.
    Adds request ID and user context to logs.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = get_logger('django.request')
    
    def __call__(self, request):
        # Add request ID for correlation
        import uuid
        request.request_id = str(uuid.uuid4())
        
        # Log request
        user_info = f'user={request.user.username if request.user.is_authenticated else "anonymous"}'
        log_with_context(
            self.logger,
            'info',
            f'{request.method} {request.path}',
            request_id=request.request_id,
            user=request.user.username if request.user.is_authenticated else 'anonymous',
            ip=self.get_client_ip(request)
        )
        
        response = self.get_response(request)
        
        # Log response
        log_with_context(
            self.logger,
            'info',
            f'{request.method} {request.path} -> {response.status_code}',
            request_id=request.request_id,
            status=response.status_code
        )
        
        return response
    
    @staticmethod
    def get_client_ip(request):
        """Get client IP address from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
