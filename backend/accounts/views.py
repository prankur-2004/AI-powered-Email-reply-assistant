import os
from django.contrib.auth.models import User

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import (
    Email,
    ConnectedEmailAccount,
    UserPreference,
    PersonalKnowledge,
    AIReply,
    ReplyFeedback
)

from .serializers import (
    RegisterSerializer,
    EmailSerializer,
    ConnectedEmailAccountSerializer,
    UserPreferenceSerializer,
    PersonalKnowledgeSerializer,
    AIReplySerializer,
    ReplyFeedbackSerializer
)

from .services.email_preprocessor import preprocess_email
from .services.email_analyzer import analyze_email
from .services.gemini_service import generate_email_reply
from .services.rag_service import search_personal_knowledge
from .services.response_validator import validate_reply
from .services.conversation_service import (
    get_conversation_context,
    format_conversation_context
)
from .services.email_fetcher import (
    PROVIDER_CONFIGS,
    test_imap_credentials,
    sync_account_emails
)


class RegisterView(APIView):

    permission_classes = [AllowAny]

    def post(self, request):

        serializer = RegisterSerializer(
            data=request.data
        )

        if serializer.is_valid():

            user = serializer.save()

            return Response(
                {
                    'message': 'User registered successfully',
                    'username': user.username,
                    'email': user.email
                },
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class ProfileView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        return Response(
            {
                'message': 'You are authenticated',
                'username': request.user.username,
                'email': request.user.email
            }
        )


class EmailListCreateView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        emails = Email.objects.filter(
            user=request.user
        ).order_by('-created_at')

        serializer = EmailSerializer(
            emails,
            many=True
        )

        return Response(serializer.data)

    def post(self, request):

        serializer = EmailSerializer(
            data=request.data
        )

        if serializer.is_valid():

            email = serializer.save(
                user=request.user
            )

            return Response(
                EmailSerializer(email).data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class EmailDetailView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, email_id):

        try:

            email = Email.objects.get(
                id=email_id,
                user=request.user
            )

        except Email.DoesNotExist:

            return Response(
                {
                    'message': 'Email not found'
                },
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = EmailSerializer(email)

        return Response(serializer.data)

    def patch(self, request, email_id):

        try:

            email = Email.objects.get(
                id=email_id,
                user=request.user
            )

        except Email.DoesNotExist:

            return Response(
                {
                    'message': 'Email not found'
                },
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = EmailSerializer(
            email,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():

            serializer.save()

            return Response(
                serializer.data
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class EmailAnalyzeView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request, email_id):

        try:

            email = Email.objects.get(
                id=email_id,
                user=request.user
            )

        except Email.DoesNotExist:

            return Response(
                {
                    'message': 'Email not found'
                },
                status=status.HTTP_404_NOT_FOUND
            )

        cleaned_email = preprocess_email(
            email.body
        )

        if not cleaned_email:

            return Response(
                {
                    'message': (
                        'Email body is empty '
                        'after preprocessing.'
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        analysis = analyze_email(
            cleaned_email
        )

        try:
            import json
            email.analysis_json = json.dumps(analysis)
            email.save(update_fields=['analysis_json'])
        except Exception:
            pass

        return Response(
            {
                'email_id': email.id,
                'subject': email.subject,
                'original_body': email.body,
                'cleaned_body': cleaned_email,
                'analysis': analysis
            }
        )


class EmailReplyView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request, email_id):

        try:

            email = Email.objects.get(
                id=email_id,
                user=request.user
            )

        except Email.DoesNotExist:

            return Response(
                {
                    'message': 'Email not found'
                },
                status=status.HTTP_404_NOT_FOUND
            )

        cleaned_email = preprocess_email(
            email.body
        )

        if not cleaned_email:

            return Response(
                {
                    'message': (
                        'Email body is empty '
                        'after preprocessing.'
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        analysis = analyze_email(
            cleaned_email
        )

        preference = UserPreference.objects.filter(
            user=request.user
        ).first()

        if preference:

            user_preferences = {
                'tone': preference.tone,
                'reply_length': preference.reply_length,
                'greeting': preference.greeting,
                'sign_off': preference.sign_off
            }

        else:

            user_preferences = {
                'tone': 'professional',
                'reply_length': 'concise',
                'greeting': 'Dear',
                'sign_off': 'Best regards'
            }

        rag_query = f"""
Subject:
{email.subject}

Email:
{cleaned_email}

Intent:
{analysis['intent']}

Topic:
{analysis['topic']}

Summary:
{analysis['summary']}
"""

        try:
            relevant_knowledge = search_personal_knowledge(
                query=rag_query,
                user=request.user,
                top_k=3
            )
        except Exception as error:
            print("Warning: search_personal_knowledge failed:", error)
            relevant_knowledge = []

        personal_knowledge = []

        for item in relevant_knowledge:

            personal_knowledge.append(
                {
                    'title': item['title'],
                    'content': item['content'],
                    'similarity': round(
                        item['similarity'],
                        4
                    )
                }
            )

        conversation = get_conversation_context(
            conversation_id=email.conversation_id,
            user=request.user,
            current_email_id=email.id
        )

        conversation_context = format_conversation_context(
            conversation
        )

        try:

            generated_reply = generate_email_reply(
                email_text=cleaned_email,
                intent=analysis['intent'],
                sentiment=analysis['sentiment'],
                urgency=analysis['urgency'],
                topic=analysis['topic'],
                summary=analysis['summary'],
                user_preferences=user_preferences,
                personal_knowledge=personal_knowledge,
                conversation_context=conversation_context
            )

        except RuntimeError as error:

            return Response(
                {
                    'message': str(error),
                    'email_id': email.id
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        validation = validate_reply(
            generated_reply
        )

        if not validation['is_valid']:

            return Response(
                {
                    'message': (
                        'Generated reply '
                        'failed validation.'
                    ),
                    'email_id': email.id,
                    'validation': validation
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        ai_reply = AIReply.objects.create(
            user=request.user,
            email=email,
            generated_reply=validation['reply'],
            model=os.getenv('CUSTOM_API_MODEL', 'custom-api')
        )

        return Response(
            {
                'message': 'AI reply generated successfully',
                'email_id': email.id,
                'subject': email.subject,
                'generated_reply': ai_reply.generated_reply,
                'reply_id': ai_reply.id,
                'analysis': analysis,
                'retrieved_knowledge': personal_knowledge,
                'conversation_history_count': len(
                    conversation
                ),
                'validation': {
                    'is_valid': validation['is_valid'],
                    'issues': validation['issues']
                }
            },
            status=status.HTTP_201_CREATED
        )


class AIReplyHistoryView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        replies = AIReply.objects.filter(
            user=request.user
        ).select_related(
            'email'
        ).order_by('-created_at')

        serializer = AIReplySerializer(
            replies,
            many=True
        )

        return Response(
            serializer.data
        )


class AIReplyAcceptView(APIView):

    permission_classes = [IsAuthenticated]

    def patch(self, request, reply_id):

        try:

            reply = AIReply.objects.get(
                id=reply_id,
                user=request.user
            )

        except AIReply.DoesNotExist:

            return Response(
                {
                    'message': 'AI reply not found'
                },
                status=status.HTTP_404_NOT_FOUND
            )

        reply.is_accepted = True

        reply.save()

        return Response(
            {
                'message': (
                    'AI reply accepted successfully'
                ),
                'reply_id': reply.id,
                'email_id': reply.email.id,
                'generated_reply': (
                    reply.generated_reply
                ),
                'is_accepted': reply.is_accepted,
                'is_edited': reply.is_edited
            }
        )


class AIReplyEditView(APIView):

    permission_classes = [IsAuthenticated]

    def patch(self, request, reply_id):

        try:

            reply = AIReply.objects.get(
                id=reply_id,
                user=request.user
            )

        except AIReply.DoesNotExist:

            return Response(
                {
                    'message': 'AI reply not found'
                },
                status=status.HTTP_404_NOT_FOUND
            )

        new_reply = request.data.get(
            'generated_reply'
        )

        if not new_reply:

            return Response(
                {
                    'message': (
                        'generated_reply is required'
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        validation = validate_reply(
            new_reply
        )

        if not validation['is_valid']:

            return Response(
                {
                    'message': (
                        'Edited reply '
                        'failed validation.'
                    ),
                    'validation': validation
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        reply.generated_reply = validation['reply']
        reply.is_edited = True

        reply.save()

        return Response(
            {
                'message': (
                    'AI reply edited successfully'
                ),
                'reply_id': reply.id,
                'email_id': reply.email.id,
                'generated_reply': (
                    reply.generated_reply
                ),
                'is_accepted': reply.is_accepted,
                'is_edited': reply.is_edited,
                'validation_issues': (
                    validation['issues']
                )
            }
        )


class AIReplyRegenerateView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request, reply_id):

        try:

            old_reply = AIReply.objects.get(
                id=reply_id,
                user=request.user
            )

        except AIReply.DoesNotExist:

            return Response(
                {
                    'message': 'AI reply not found'
                },
                status=status.HTTP_404_NOT_FOUND
            )

        email = old_reply.email

        cleaned_email = preprocess_email(
            email.body
        )

        if not cleaned_email:

            return Response(
                {
                    'message': (
                        'Email body is empty '
                        'after preprocessing.'
                    )
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        analysis = analyze_email(
            cleaned_email
        )

        preference = UserPreference.objects.filter(
            user=request.user
        ).first()

        if preference:

            user_preferences = {
                'tone': preference.tone,
                'reply_length': preference.reply_length,
                'greeting': preference.greeting,
                'sign_off': preference.sign_off
            }

        else:

            user_preferences = {
                'tone': 'professional',
                'reply_length': 'concise',
                'greeting': 'Dear',
                'sign_off': 'Best regards'
            }

        rag_query = f"""
Subject:
{email.subject}

Email:
{cleaned_email}

Intent:
{analysis['intent']}

Topic:
{analysis['topic']}

Summary:
{analysis['summary']}
"""

        try:
            relevant_knowledge = search_personal_knowledge(
                query=rag_query,
                user=request.user,
                top_k=3
            )
        except Exception as error:
            print("Warning: search_personal_knowledge failed:", error)
            relevant_knowledge = []

        personal_knowledge = []

        for item in relevant_knowledge:

            personal_knowledge.append(
                {
                    'title': item['title'],
                    'content': item['content'],
                    'similarity': round(
                        item['similarity'],
                        4
                    )
                }
            )

        conversation = get_conversation_context(
            conversation_id=email.conversation_id,
            user=request.user,
            current_email_id=email.id
        )

        conversation_context = format_conversation_context(
            conversation
        )

        try:

            generated_reply = generate_email_reply(
                email_text=cleaned_email,
                intent=analysis['intent'],
                sentiment=analysis['sentiment'],
                urgency=analysis['urgency'],
                topic=analysis['topic'],
                summary=analysis['summary'],
                user_preferences=user_preferences,
                personal_knowledge=personal_knowledge,
                conversation_context=conversation_context
            )

        except RuntimeError as error:

            return Response(
                {
                    'message': str(error),
                    'email_id': email.id
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        validation = validate_reply(
            generated_reply
        )

        if not validation['is_valid']:

            return Response(
                {
                    'message': (
                        'Regenerated reply '
                        'failed validation.'
                    ),
                    'email_id': email.id,
                    'validation': validation
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        new_reply = AIReply.objects.create(
            user=request.user,
            email=email,
            generated_reply=validation['reply'],
            model=os.getenv('CUSTOM_API_MODEL', 'custom-api')
        )

        return Response(
            {
                'message': (
                    'AI reply regenerated successfully'
                ),
                'previous_reply_id': old_reply.id,
                'new_reply_id': new_reply.id,
                'email_id': email.id,
                'subject': email.subject,
                'generated_reply': (
                    new_reply.generated_reply
                ),
                'conversation_history_count': len(
                    conversation
                ),
                'validation': {
                    'is_valid': validation['is_valid'],
                    'issues': validation['issues']
                }
            },
            status=status.HTTP_201_CREATED
        )


class ReplyFeedbackView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request, reply_id):

        try:

            ai_reply = AIReply.objects.get(
                id=reply_id,
                user=request.user
            )

        except AIReply.DoesNotExist:

            return Response(
                {
                    'message': 'AI reply not found'
                },
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ReplyFeedbackSerializer(
            data=request.data
        )

        if not serializer.is_valid():

            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        feedback, created = (
            ReplyFeedback.objects.update_or_create(
                ai_reply=ai_reply,
                user=request.user,
                defaults={
                    'rating': serializer.validated_data.get(
                        'rating'
                    ),
                    'is_helpful': (
                        serializer.validated_data.get(
                            'is_helpful'
                        )
                    ),
                    'comment': (
                        serializer.validated_data.get(
                            'comment',
                            ''
                        )
                    )
                }
            )
        )

        response_serializer = ReplyFeedbackSerializer(
            feedback
        )

        if created:

            message = (
                'Feedback submitted successfully'
            )

        else:

            message = (
                'Feedback updated successfully'
            )

        return Response(
            {
                'message': message,
                'feedback': response_serializer.data
            },
            status=(
                status.HTTP_201_CREATED
                if created
                else status.HTTP_200_OK
            )
        )


class AIAnalyticsView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        replies = AIReply.objects.filter(
            user=request.user
        )

        total_replies = replies.count()

        accepted_replies = replies.filter(
            is_accepted=True
        ).count()

        edited_replies = replies.filter(
            is_edited=True
        ).count()

        pending_replies = replies.filter(
            is_accepted=False
        ).count()

        if total_replies > 0:

            acceptance_rate = round(
                (
                    accepted_replies /
                    total_replies
                ) * 100,
                2
            )

            edit_rate = round(
                (
                    edited_replies /
                    total_replies
                ) * 100,
                2
            )

        else:

            acceptance_rate = 0.0
            edit_rate = 0.0

        # -----------------------------
        # Feedback Analytics
        # -----------------------------

        feedback = ReplyFeedback.objects.filter(
            user=request.user
        )

        total_feedback = feedback.count()

        helpful_count = feedback.filter(
            is_helpful=True
        ).count()

        not_helpful_count = feedback.filter(
            is_helpful=False
        ).count()

        ratings = [
            item.rating
            for item in feedback
            if item.rating is not None
        ]

        if ratings:

            average_rating = round(
                sum(ratings) / len(ratings),
                2
            )

        else:

            average_rating = 0.0

        if total_feedback > 0:

            helpful_percentage = round(
                (
                    helpful_count /
                    total_feedback
                ) * 100,
                2
            )

        else:

            helpful_percentage = 0.0

        return Response(
            {
                'reply_analytics': {
                    'total_replies': total_replies,
                    'accepted_replies': accepted_replies,
                    'edited_replies': edited_replies,
                    'pending_replies': pending_replies,
                    'acceptance_rate': acceptance_rate,
                    'edit_rate': edit_rate
                },

                'feedback_analytics': {
                    'total_feedback': total_feedback,
                    'average_rating': average_rating,
                    'helpful_count': helpful_count,
                    'not_helpful_count': not_helpful_count,
                    'helpful_percentage': (
                        helpful_percentage
                    )
                }
            }
        )


class UserPreferenceView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        preference = UserPreference.objects.filter(
            user=request.user
        ).first()

        if not preference:

            preference = UserPreference.objects.create(
                user=request.user
            )

        serializer = UserPreferenceSerializer(
            preference
        )

        return Response(
            serializer.data
        )

    def post(self, request):

        preference = UserPreference.objects.filter(
            user=request.user
        ).first()

        if preference:

            serializer = UserPreferenceSerializer(
                preference,
                data=request.data,
                partial=True
            )

        else:

            serializer = UserPreferenceSerializer(
                data=request.data
            )

        if serializer.is_valid():

            if not preference:

                preference = serializer.save(
                    user=request.user
                )

            else:

                serializer.save()

            return Response(
                UserPreferenceSerializer(
                    preference
                ).data
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    def put(self, request):
        return self.post(request)

    def patch(self, request):
        return self.post(request)


class PersonalKnowledgeListCreateView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):

        knowledge = PersonalKnowledge.objects.filter(
            user=request.user
        ).order_by('-created_at')

        serializer = PersonalKnowledgeSerializer(
            knowledge,
            many=True
        )

        return Response(
            serializer.data
        )

    def post(self, request):

        serializer = PersonalKnowledgeSerializer(
            data=request.data
        )

        if serializer.is_valid():

            knowledge = serializer.save(
                user=request.user
            )

            try:
                from .services.embedding_service import (
                    generate_embedding
                )

                embedding = generate_embedding(
                    f"{knowledge.title}\n"
                    f"{knowledge.content}"
                )
            except Exception as error:
                print("Warning: Embedding generation skipped/failed:", error)
                embedding = []

            import json

            knowledge.embedding = json.dumps(
                embedding
            )

            knowledge.save(
                update_fields=['embedding']
            )

            return Response(
                PersonalKnowledgeSerializer(
                    knowledge
                ).data,
                status=status.HTTP_201_CREATED
            )

        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class ConversationHistoryView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request, conversation_id):

        emails = Email.objects.filter(
            user=request.user,
            conversation_id=conversation_id
        ).order_by('created_at')

        if not emails.exists():

            return Response(
                {
                    'message': (
                        'Conversation not found'
                    ),
                    'conversation_id': conversation_id,
                    'emails': []
                },
                status=status.HTTP_404_NOT_FOUND
            )

        conversation_emails = []

        for email in emails:

            replies = AIReply.objects.filter(
                user=request.user,
                email=email
            ).order_by('created_at')

            reply_data = []

            for reply in replies:

                reply_data.append(
                    {
                        'id': reply.id,
                        'generated_reply': (
                            reply.generated_reply
                        ),
                        'model': reply.model,
                        'is_accepted': (
                            reply.is_accepted
                        ),
                        'is_edited': (
                            reply.is_edited
                        ),
                        'created_at': (
                            reply.created_at
                        )
                    }
                )

            conversation_emails.append(
                {
                    'id': email.id,
                    'conversation_id': (
                        email.conversation_id
                    ),
                    'sender': email.sender,
                    'recipient': email.recipient,
                    'subject': email.subject,
                    'body': email.body,
                    'received_at': email.received_at,
                    'is_read': email.is_read,
                    'created_at': email.created_at,
                    'ai_replies': reply_data
                }
            )

        return Response(
            {
                'conversation_id': conversation_id,
                'email_count': len(
                    conversation_emails
                ),
                'emails': conversation_emails
            }
        )

class ConnectedEmailAccountListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        accounts = ConnectedEmailAccount.objects.filter(user=request.user)
        serializer = ConnectedEmailAccountSerializer(accounts, many=True)
        return Response({
            'accounts': serializer.data,
            'providers': {k: {'name': v['name'], 'help': v['help']} for k, v in PROVIDER_CONFIGS.items()}
        })

    def post(self, request):
        data = request.data.copy()
        provider = data.get('provider', 'gmail')
        email_address = data.get('email_address', '').strip()
        password = data.get('password', '').strip()

        if not email_address or not password:
            return Response(
                {'error': 'Email address and password (or App Password) are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if provider in PROVIDER_CONFIGS and provider != 'custom':
            data['imap_host'] = PROVIDER_CONFIGS[provider]['host']
            data['imap_port'] = PROVIDER_CONFIGS[provider]['port']
            data['use_ssl'] = PROVIDER_CONFIGS[provider]['ssl']
        else:
            if not data.get('imap_host'):
                return Response(
                    {'error': 'IMAP host is required for custom providers.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            data['imap_port'] = int(data.get('imap_port', 993) or 993)
            data['use_ssl'] = bool(data.get('use_ssl', True))

        is_valid, msg = test_imap_credentials(
            email_address=email_address,
            password=password,
            host=data['imap_host'],
            port=data['imap_port'],
            use_ssl=data['use_ssl']
        )

        if not is_valid:
            return Response({'error': msg}, status=status.HTTP_400_BAD_REQUEST)

        account, created = ConnectedEmailAccount.objects.update_or_create(
            user=request.user,
            email_address=email_address,
            defaults={
                'provider': provider,
                'imap_host': data['imap_host'],
                'imap_port': data['imap_port'],
                'password': password,
                'use_ssl': data['use_ssl'],
                'is_active': True,
            }
        )

        max_emails = int(request.data.get('max_emails', 10) or 10)
        auto_analyze = bool(request.data.get('auto_analyze', True))
        sync_result = sync_account_emails(account, max_emails=max_emails, auto_analyze=auto_analyze)

        account_serializer = ConnectedEmailAccountSerializer(account)
        return Response({
            'message': 'Email account successfully connected and verified!',
            'account': account_serializer.data,
            'sync_result': sync_result
        }, status=status.HTTP_201_CREATED)


class ConnectedEmailAccountDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, account_id):
        try:
            account = ConnectedEmailAccount.objects.get(id=account_id, user=request.user)
            account.delete()
            return Response({'message': 'Email account disconnected successfully.'})
        except ConnectedEmailAccount.DoesNotExist:
            return Response({'error': 'Email account not found.'}, status=status.HTTP_404_NOT_FOUND)


class SyncEmailAccountView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, account_id=None):
        max_emails = int(request.data.get('max_emails', 15) or 15)
        auto_analyze = bool(request.data.get('auto_analyze', True))

        if account_id:
            try:
                account = ConnectedEmailAccount.objects.get(id=account_id, user=request.user)
                accounts = [account]
            except ConnectedEmailAccount.DoesNotExist:
                return Response({'error': 'Email account not found.'}, status=status.HTTP_404_NOT_FOUND)
        else:
            accounts = ConnectedEmailAccount.objects.filter(user=request.user, is_active=True)
            if not accounts.exists():
                return Response({
                    'error': 'No connected email accounts found. Please connect your email account first.'
                }, status=status.HTTP_400_BAD_REQUEST)

        total_synced = 0
        total_skipped = 0
        results = []

        for acc in accounts:
            res = sync_account_emails(acc, max_emails=max_emails, auto_analyze=auto_analyze)
            results.append({
                'account': acc.email_address,
                'provider': acc.provider,
                'res': res
            })
            if res.get('success'):
                total_synced += res.get('synced_count', 0)
                total_skipped += res.get('skipped_count', 0)

        emails = Email.objects.filter(user=request.user).order_by('-created_at')
        email_data = EmailSerializer(emails, many=True).data

        return Response({
            'message': f'Synced {total_synced} new email(s).',
            'total_synced': total_synced,
            'total_skipped': total_skipped,
            'accounts_synced': len(accounts),
            'emails': email_data,
            'details': results
        })


class TestEmailConnectionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        provider = request.data.get('provider', 'gmail')
        email_address = request.data.get('email_address', '').strip()
        password = request.data.get('password', '').strip()

        if not email_address or not password:
            return Response({'error': 'Email address and password are required.'}, status=status.HTTP_400_BAD_REQUEST)

        if provider in PROVIDER_CONFIGS and provider != 'custom':
            host = PROVIDER_CONFIGS[provider]['host']
            port = PROVIDER_CONFIGS[provider]['port']
            ssl = PROVIDER_CONFIGS[provider]['ssl']
        else:
            host = request.data.get('imap_host', '').strip()
            port = int(request.data.get('imap_port', 993) or 993)
            ssl = bool(request.data.get('use_ssl', True))

        is_valid, msg = test_imap_credentials(email_address, password, host, port, ssl)
        if is_valid:
            return Response({'success': True, 'message': msg})
        else:
            return Response({'success': False, 'error': msg}, status=status.HTTP_400_BAD_REQUEST)
