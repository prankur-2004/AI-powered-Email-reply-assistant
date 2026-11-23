from django.db import models
from django.contrib.auth.models import User


class Email(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='emails'
    )

    conversation_id = models.CharField(
        max_length=100,
        blank=True,
        default=''
    )

    message_id = models.CharField(
        max_length=255,
        blank=True,
        default=''
    )

    analysis_json = models.TextField(
        blank=True,
        default=''
    )

    sender = models.EmailField()

    recipient = models.EmailField()

    subject = models.CharField(
        max_length=255
    )

    body = models.TextField()

    received_at = models.DateTimeField(
        auto_now_add=True
    )

    is_read = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.subject


class ConnectedEmailAccount(models.Model):

    PROVIDER_CHOICES = [
        ('gmail', 'Gmail'),
        ('outlook', 'Outlook / Hotmail / Office 365'),
        ('yahoo', 'Yahoo Mail'),
        ('icloud', 'iCloud Mail'),
        ('custom', 'Custom IMAP Server'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='email_accounts'
    )

    email_address = models.EmailField()

    provider = models.CharField(
        max_length=50,
        choices=PROVIDER_CHOICES,
        default='gmail'
    )

    imap_host = models.CharField(
        max_length=255,
        default='imap.gmail.com'
    )

    imap_port = models.PositiveIntegerField(
        default=993
    )

    password = models.CharField(
        max_length=255
    )

    use_ssl = models.BooleanField(
        default=True
    )

    last_synced_at = models.DateTimeField(
        null=True,
        blank=True
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.email_address} ({self.provider})"


class UserPreference(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='preferences'
    )

    tone = models.CharField(
        max_length=50,
        default='professional'
    )

    reply_length = models.CharField(
        max_length=50,
        default='concise'
    )

    greeting = models.CharField(
        max_length=100,
        default='Dear'
    )

    sign_off = models.CharField(
        max_length=100,
        default='Best regards'
    )

    def __str__(self):
        return f"{self.user.username}'s preferences"


class PersonalKnowledge(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='knowledge'
    )

    title = models.CharField(
        max_length=255
    )

    content = models.TextField()

    embedding = models.TextField(
        blank=True,
        default=''
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.title


class AIReply(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='ai_replies'
    )

    email = models.ForeignKey(
        Email,
        on_delete=models.CASCADE,
        related_name='ai_replies'
    )

    generated_reply = models.TextField()

    model = models.CharField(
        max_length=100,
        default='gemini-3.6-flash'
    )

    is_accepted = models.BooleanField(
        default=False
    )

    is_edited = models.BooleanField(
        default=False
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return (
            f"AI Reply for: {self.email.subject}"
        )


class ReplyFeedback(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reply_feedback'
    )

    ai_reply = models.OneToOneField(
        AIReply,
        on_delete=models.CASCADE,
        related_name='feedback'
    )

    rating = models.PositiveSmallIntegerField(
        null=True,
        blank=True
    )

    is_helpful = models.BooleanField(
        null=True,
        blank=True
    )

    comment = models.TextField(
        blank=True,
        default=''
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return (
            f"Feedback for AI Reply {self.ai_reply.id}"
        )
