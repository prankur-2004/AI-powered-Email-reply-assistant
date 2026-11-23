import imaplib
import email
from email.header import decode_header
import re
import html
import json
from datetime import datetime
from django.utils import timezone


PROVIDER_CONFIGS = {
    'gmail': {
        'name': 'Gmail',
        'host': 'imap.gmail.com',
        'port': 993,
        'ssl': True,
        'help': 'Use your Gmail address and a 16-character App Password (from myaccount.google.com/apppasswords).'
    },
    'outlook': {
        'name': 'Outlook / Hotmail / Office 365',
        'host': 'outlook.office365.com',
        'port': 993,
        'ssl': True,
        'help': 'Use your Microsoft account email and password or App Password.'
    },
    'yahoo': {
        'name': 'Yahoo Mail',
        'host': 'imap.mail.yahoo.com',
        'port': 993,
        'ssl': True,
        'help': 'Generate an App Password from your Yahoo Account Security page.'
    },
    'icloud': {
        'name': 'iCloud Mail',
        'host': 'imap.mail.me.com',
        'port': 993,
        'ssl': True,
        'help': 'Generate an app-specific password at appleid.apple.com.'
    },
    'custom': {
        'name': 'Custom IMAP Server',
        'host': '',
        'port': 993,
        'ssl': True,
        'help': 'Enter your custom IMAP host and credentials (e.g. Hostinger, cPanel, Zoho, corporate server).'
    }
}


def decode_mime_header(header_value):
    """
    Decodes RFC 2047 encoded email headers into clean unicode strings.
    """
    if not header_value:
        return ""
    try:
        decoded_chunks = decode_header(header_value)
        parts = []
        for chunk, encoding in decoded_chunks:
            if isinstance(chunk, bytes):
                parts.append(chunk.decode(encoding or 'utf-8', errors='replace'))
            else:
                parts.append(str(chunk))
        return " ".join(parts).strip()
    except Exception:
        return str(header_value).strip()


def clean_html_to_text(html_content):
    """
    Strips HTML tags and unescapes HTML entities to get clean readable text.
    """
    if not html_content:
        return ""
    # Remove script and style elements
    cleaned = re.sub(r'<(script|style)[^>]*>.*?</\1>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
    # Replace line breaks and paragraph ends with newlines
    cleaned = re.sub(r'<(br|p|div|tr)[^>]*>', '\n', cleaned, flags=re.IGNORECASE)
    # Remove all remaining HTML tags
    cleaned = re.sub(r'<[^>]+>', ' ', cleaned)
    # Unescape HTML entities (&nbsp;, &amp;, etc.)
    cleaned = html.unescape(cleaned)
    # Collapse multiple whitespaces and excessive newlines
    cleaned = re.sub(r'[ \t]+', ' ', cleaned)
    cleaned = re.sub(r'\n\s*\n', '\n\n', cleaned)
    return cleaned.strip()


def extract_email_body(msg):
    """
    Extracts text body from email message, preferring text/plain and falling back to text/html.
    """
    plain_text = ""
    html_text = ""

    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition", ""))

            # Skip attachments
            if "attachment" in content_disposition.lower():
                continue

            try:
                payload = part.get_payload(decode=True)
                if not payload:
                    continue
                charset = part.get_content_charset() or 'utf-8'
                decoded_str = payload.decode(charset, errors='replace')

                if content_type == 'text/plain' and not plain_text:
                    plain_text = decoded_str
                elif content_type == 'text/html' and not html_text:
                    html_text = decoded_str
            except Exception:
                continue
    else:
        content_type = msg.get_content_type()
        try:
            payload = msg.get_payload(decode=True)
            if payload:
                charset = msg.get_content_charset() or 'utf-8'
                decoded_str = payload.decode(charset, errors='replace')
                if content_type == 'text/html':
                    html_text = decoded_str
                else:
                    plain_text = decoded_str
        except Exception:
            pass

    if plain_text and plain_text.strip():
        return plain_text.strip()
    if html_text and html_text.strip():
        return clean_html_to_text(html_text)

    return "(No readable body content found in email)"


def parse_sender_email(raw_sender):
    """
    Extracts pure email address and sender name from 'Name <email@domain.com>'.
    """
    if not raw_sender:
        return "", ""
    match = re.search(r'<([^>]+)>', raw_sender)
    if match:
        email_addr = match.group(1).strip()
        name = raw_sender.split('<')[0].strip(' "\'')
        return email_addr, name
    match_plain = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', raw_sender)
    if match_plain:
        return match_plain.group(0), ""
    return raw_sender.strip(), ""


def connect_imap(email_address, password, host, port=993, use_ssl=True, timeout=15):
    """
    Establishes and authenticates an IMAP connection.
    """
    if use_ssl:
        server = imaplib.IMAP4_SSL(host, port, timeout=timeout)
    else:
        server = imaplib.IMAP4(host, port, timeout=timeout)

    server.login(email_address, password)
    return server


def test_imap_credentials(email_address, password, host, port=993, use_ssl=True):
    """
    Verifies IMAP credentials. Returns (is_success, message).
    """
    try:
        server = connect_imap(email_address, password, host, port, use_ssl, timeout=10)
        status, _ = server.select('INBOX', readonly=True)
        server.close()
        server.logout()
        return True, "Connection successful! Mailbox verified."
    except imaplib.IMAP4.error as e:
        err_str = str(e)
        if "AUTHENTICATIONFAILED" in err_str or "login failed" in err_str.lower() or "credentials" in err_str.lower():
            if "gmail" in host.lower():
                return False, (
                    "Authentication failed. Gmail requires a 16-character App Password. "
                    "Go to Google Account -> Security -> 2-Step Verification -> App Passwords to create one."
                )
            return False, f"Authentication failed: Invalid email or password. Details: {err_str}"
        return False, f"IMAP server error: {err_str}"
    except Exception as e:
        return False, f"Failed to connect to {host}:{port}: {str(e)}"


def sync_account_emails(account, max_emails=15, auto_analyze=True):
    """
    Connects to account IMAP server, downloads recent emails, saves them to Email model,
    and optionally runs AI analysis on them.
    """
    from ..models import Email
    from .email_analyzer import analyze_email
    from .email_preprocessor import preprocess_email

    host = account.imap_host
    port = account.imap_port
    use_ssl = account.use_ssl
    email_address = account.email_address
    password = account.password

    try:
        server = connect_imap(email_address, password, host, port, use_ssl, timeout=20)
    except Exception as err:
        return {
            'success': False,
            'error': f"Failed to connect to {host}: {str(err)}",
            'synced_count': 0
        }

    synced_emails = []
    skipped_count = 0

    try:
        server.select('INBOX', readonly=True)
        # Search all messages in inbox
        status, data = server.search(None, 'ALL')
        if status != 'OK' or not data or not data[0]:
            server.logout()
            account.last_synced_at = timezone.now()
            account.save(update_fields=['last_synced_at'])
            return {
                'success': True,
                'synced_count': 0,
                'message': 'Inbox is empty or no messages found.'
            }

        msg_ids = data[0].split()
        # Take the most recent messages (end of list)
        recent_ids = msg_ids[-max_emails:]
        # Reverse to process newest first
        recent_ids.reverse()

        for mid in recent_ids:
            try:
                res_status, msg_data = server.fetch(mid, '(RFC822)')
                if res_status != 'OK' or not msg_data:
                    continue

                raw_bytes = None
                for part in msg_data:
                    if isinstance(part, tuple) and len(part) > 1:
                        raw_bytes = part[1]
                        break

                if not raw_bytes:
                    continue

                msg = email.message_from_bytes(raw_bytes)

                raw_subject = msg.get('Subject', '')
                subject = decode_mime_header(raw_subject) or '(No Subject)'

                raw_sender = msg.get('From', '')
                sender_email, sender_name = parse_sender_email(decode_mime_header(raw_sender))
                if not sender_email:
                    sender_email = raw_sender

                raw_recipient = msg.get('To', '')
                recipient_email, _ = parse_sender_email(decode_mime_header(raw_recipient))
                if not recipient_email:
                    recipient_email = email_address

                message_id = msg.get('Message-ID', '').strip()
                if not message_id:
                    # Deterministic fallback id based on subject and sender
                    message_id = f"fallback-{abs(hash(f'{subject}:{sender_email}:{mid}'))}"

                # Deduplication check: check if already exists for this user
                already_exists = Email.objects.filter(
                    user=account.user,
                    message_id=message_id
                ).exists()

                if not already_exists and subject and sender_email:
                    # Also check subject + sender match within user's emails
                    already_exists = Email.objects.filter(
                        user=account.user,
                        subject=subject,
                        sender=sender_email
                    ).exists()

                if already_exists:
                    skipped_count += 1
                    continue

                body_text = extract_email_body(msg)

                # Generate conversation ID
                conv_id = f"conv-{abs(hash(subject.lower().strip())) % 100000}"

                analysis_result = {}
                analysis_json_str = ""

                if auto_analyze:
                    try:
                        cleaned = preprocess_email(body_text)
                        analysis_result = analyze_email(cleaned or body_text)
                        analysis_json_str = json.dumps(analysis_result)
                    except Exception as ai_err:
                        print(f"Warning: Auto-analysis error for email '{subject}': {ai_err}")

                # Create the Email record
                new_email = Email.objects.create(
                    user=account.user,
                    sender=sender_email,
                    recipient=recipient_email,
                    subject=subject,
                    body=body_text,
                    conversation_id=conv_id,
                    message_id=message_id,
                    analysis_json=analysis_json_str,
                    is_read=False
                )

                synced_emails.append({
                    'id': new_email.id,
                    'subject': new_email.subject,
                    'sender': new_email.sender,
                    'analysis': analysis_result
                })

            except Exception as single_msg_err:
                print(f"Error processing message id {mid}: {single_msg_err}")
                continue

        account.last_synced_at = timezone.now()
        account.save(update_fields=['last_synced_at'])

        try:
            server.close()
            server.logout()
        except Exception:
            pass

        return {
            'success': True,
            'synced_count': len(synced_emails),
            'skipped_count': skipped_count,
            'emails': synced_emails,
            'message': f"Synced {len(synced_emails)} new email(s). {skipped_count} existing email(s) were skipped."
        }

    except Exception as e:
        try:
            server.logout()
        except Exception:
            pass
        return {
            'success': False,
            'error': f"Error during IMAP sync: {str(e)}",
            'synced_count': len(synced_emails)
        }

