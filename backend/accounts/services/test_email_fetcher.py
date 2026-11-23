import sys
import email
from email.message import EmailMessage

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from .email_fetcher import (
    decode_mime_header,
    clean_html_to_text,
    extract_email_body,
    parse_sender_email,
    PROVIDER_CONFIGS,
    test_imap_credentials
)


def main():
    print("==================================================")
    print("      Testing Universal Email Fetcher Service     ")
    print("==================================================")

    # 1. Test Provider Configs
    print("1. Supported Providers:")
    for key, val in PROVIDER_CONFIGS.items():
        print(f"   - {val['name']} ({key}): {val['host'] or 'Custom Host'}:{val['port']}")

    # 2. Test MIME Header Decoding
    test_raw_header = "=?UTF-8?B?SGVsbG8gV29ybGQ=?="
    decoded = decode_mime_header(test_raw_header)
    assert decoded == "Hello World", f"Header decode failed: {decoded}"
    print("\n2. Header Decoding: PASS (Decoded: 'Hello World')")

    # 3. Test HTML Cleaning
    html_sample = "<p>Dear <b>User</b>,<br/>This is an <i>important</i> email.<br/></p>"
    cleaned = clean_html_to_text(html_sample)
    assert "Dear User" in cleaned and "important email" in cleaned
    print("3. HTML Stripping:  PASS")

    # 4. Test Multi-part Body Extraction
    msg = EmailMessage()
    msg['Subject'] = 'Test Subject'
    msg['From'] = 'John Doe <john@example.com>'
    msg['To'] = 'user@example.com'
    msg.set_content("This is the plain text body of the email.")
    extracted_body = extract_email_body(msg)
    assert "plain text body" in extracted_body
    print("4. Body Extraction: PASS")

    # 5. Test Sender Parsing
    sender_email, sender_name = parse_sender_email("Google Security <no-reply@accounts.google.com>")
    assert sender_email == "no-reply@accounts.google.com"
    print(f"5. Sender Parsing:  PASS (Parsed: {sender_email})")

    # 6. Test IMAP connection failure handling (expected failure for dummy creds)
    is_valid, msg = test_imap_credentials("dummy@example.com", "fake_pass", "127.0.0.1", 993, True)
    assert is_valid is False
    print(f"6. Credential Validation Handling: PASS (Returned expected error: {msg[:40]}...)")

    print("\n==================================================")
    print(" ALL EMAIL FETCHER INTEGRATION TESTS PASSED!      ")
    print("==================================================")


if __name__ == "__main__":
    main()

