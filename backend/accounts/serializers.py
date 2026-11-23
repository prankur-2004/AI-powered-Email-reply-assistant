from django.contrib.auth.models import User
from rest_framework import serializers
import json

from .models import (
    Email,
    ConnectedEmailAccount,
    UserPreference,
    PersonalKnowledge,
    AIReply,
    ReplyFeedback
)


class RegisterSerializer(serializers.ModelSerializer):

    password = serializers.CharField(
        write_only=True,
        min_length=8
    )

    class Meta:
        model = User
        fields = [
            'username',
            'email',
            'password'
        ]

    def create(self, validated_data):

        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password']
        )

        return user


class EmailSerializer(serializers.ModelSerializer):

    analysis = serializers.SerializerMethodField()

    class Meta:
        model = Email

        fields = [
            'id',
            'conversation_id',
            'message_id',
            'sender',
            'recipient',
            'subject',
            'body',
            'analysis',
            'received_at',
            'is_read',
            'created_at'
        ]

        read_only_fields = [
            'id',
            'analysis',
            'received_at',
            'created_at'
        ]

    def get_analysis(self, obj):
        if hasattr(obj, 'analysis_json') and obj.analysis_json:
            try:
                return json.loads(obj.analysis_json)
            except Exception:
                return None
        return None


class ConnectedEmailAccountSerializer(serializers.ModelSerializer):

    password = serializers.CharField(
        write_only=True,
        required=True
    )

    class Meta:
        model = ConnectedEmailAccount

        fields = [
            'id',
            'email_address',
            'provider',
            'imap_host',
            'imap_port',
            'password',
            'use_ssl',
            'last_synced_at',
            'is_active',
            'created_at',
            'updated_at'
        ]

        read_only_fields = [
            'id',
            'last_synced_at',
            'created_at',
            'updated_at'
        ]


class UserPreferenceSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserPreference

        fields = [
            'id',
            'tone',
            'reply_length',
            'greeting',
            'sign_off'
        ]

        read_only_fields = [
            'id'
        ]


class PersonalKnowledgeSerializer(serializers.ModelSerializer):

    class Meta:
        model = PersonalKnowledge

        fields = [
            'id',
            'title',
            'content',
            'created_at',
            'updated_at'
        ]

        read_only_fields = [
            'id',
            'created_at',
            'updated_at'
        ]


class AIReplySerializer(serializers.ModelSerializer):

    email_id = serializers.IntegerField(
        source='email.id',
        read_only=True
    )

    subject = serializers.CharField(
        source='email.subject',
        read_only=True
    )

    class Meta:
        model = AIReply

        fields = [
            'id',
            'email_id',
            'subject',
            'generated_reply',
            'model',
            'is_accepted',
            'is_edited',
            'created_at'
        ]

        read_only_fields = [
            'id',
            'email_id',
            'subject',
            'generated_reply',
            'model',
            'created_at'
        ]


class ReplyFeedbackSerializer(
    serializers.ModelSerializer
):

    ai_reply_id = serializers.IntegerField(
        source='ai_reply.id',
        read_only=True
    )

    class Meta:
        model = ReplyFeedback

        fields = [
            'id',
            'ai_reply_id',
            'rating',
            'is_helpful',
            'comment',
            'created_at',
            'updated_at'
        ]

        read_only_fields = [
            'id',
            'ai_reply_id',
            'created_at',
            'updated_at'
        ]

    def validate_rating(self, value):

        if value is not None:

            if value < 1 or value > 5:

                raise serializers.ValidationError(
                    'Rating must be between 1 and 5.'
                )

        return value
