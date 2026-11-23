from django.urls import path

from .views import (
    RegisterView,
    ProfileView,
    EmailListCreateView,
    EmailDetailView,
    EmailAnalyzeView,
    EmailReplyView,
    AIReplyHistoryView,
    AIReplyAcceptView,
    AIReplyEditView,
    AIReplyRegenerateView,
    ReplyFeedbackView,
    AIAnalyticsView,
    UserPreferenceView,
    PersonalKnowledgeListCreateView,
    ConversationHistoryView,
    ConnectedEmailAccountListCreateView,
    ConnectedEmailAccountDetailView,
    SyncEmailAccountView,
    TestEmailConnectionView
)


urlpatterns = [

    path(
        'register/',
        RegisterView.as_view(),
        name='register'
    ),

    path(
        'profile/',
        ProfileView.as_view(),
        name='profile'
    ),

    path(
        'emails/',
        EmailListCreateView.as_view(),
        name='emails'
    ),

    path(
        'emails/<int:email_id>/',
        EmailDetailView.as_view(),
        name='email-detail'
    ),

    path(
        'emails/<int:email_id>/analyze/',
        EmailAnalyzeView.as_view(),
        name='email-analyze'
    ),

    path(
        'emails/<int:email_id>/reply/',
        EmailReplyView.as_view(),
        name='email-reply'
    ),

    path(
        'replies/',
        AIReplyHistoryView.as_view(),
        name='reply-history'
    ),

    path(
        'replies/<int:reply_id>/accept/',
        AIReplyAcceptView.as_view(),
        name='reply-accept'
    ),

    path(
        'replies/<int:reply_id>/edit/',
        AIReplyEditView.as_view(),
        name='reply-edit'
    ),

    path(
        'replies/<int:reply_id>/regenerate/',
        AIReplyRegenerateView.as_view(),
        name='reply-regenerate'
    ),

    path(
        'replies/<int:reply_id>/feedback/',
        ReplyFeedbackView.as_view(),
        name='reply-feedback'
    ),

    path(
        'analytics/',
        AIAnalyticsView.as_view(),
        name='analytics'
    ),

    path(
        'preferences/',
        UserPreferenceView.as_view(),
        name='preferences'
    ),

    path(
        'knowledge/',
        PersonalKnowledgeListCreateView.as_view(),
        name='knowledge'
    ),

    path(
        'conversations/<str:conversation_id>/',
        ConversationHistoryView.as_view(),
        name='conversation-history'
    ),

    path(
        'email-accounts/',
        ConnectedEmailAccountListCreateView.as_view(),
        name='email-accounts'
    ),

    path(
        'email-accounts/<int:account_id>/',
        ConnectedEmailAccountDetailView.as_view(),
        name='email-accounts-detail'
    ),

    path(
        'email-accounts/<int:account_id>/sync/',
        SyncEmailAccountView.as_view(),
        name='email-accounts-sync-one'
    ),

    path(
        'email-accounts/sync/',
        SyncEmailAccountView.as_view(),
        name='email-accounts-sync-all'
    ),

    path(
        'email-accounts/test/',
        TestEmailConnectionView.as_view(),
        name='email-accounts-test'
    ),
]