from django.db import models
from django.conf import settings


class ChatSession(models.Model):
    """Chat session for user conversations"""
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='chat_sessions'
    )
    title = models.CharField(max_length=255, default="New Chat")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"


class Message(models.Model):
    """Individual message in a chat session"""
    
    class Role(models.TextChoices):
        USER = 'USER', 'User'
        ASSISTANT = 'ASSISTANT', 'Assistant'
    
    session = models.ForeignKey(
        ChatSession, 
        on_delete=models.CASCADE, 
        related_name='messages'
    )
    role = models.CharField(max_length=20, choices=Role.choices)
    content = models.TextField()
    sources = models.JSONField(null=True, blank=True)  # Store citation sources
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."

