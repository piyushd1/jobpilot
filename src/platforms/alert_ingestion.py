import email
import imaplib
import re


class AlertIngestionService:
    """
    Connects to email via IMAP+AppPasswords (fallback for full OAuth).
    Constantly polls inbox for matching filters (e.g., Naukri Job Alert).
    """
    def __init__(self, username, password, imap_url="imap.gmail.com"):
        self.username = username
        self.password = password
        self.imap_url = imap_url

    def connect(self):
        try:
            self.mail = imaplib.IMAP4_SSL(self.imap_url)
            self.mail.login(self.username, self.password)
        except Exception as e:
            print(f"IMAP Connection failed: {e}")

    def fetch_recent_alerts(self, limit=10) -> list[str]:
        """
        Fetch emails and extract raw URLs containing jobs.
        """
        urls_found = []
        try:
            self.mail.select('inbox')
            # Search for typical alert senders
            status, messages = self.mail.search(None, '(OR FROM "naukri.com" FROM "indeed.com") UNSEEN')

            if status != "OK":
                return urls_found

            mail_ids = messages[0].split()[-limit:]
            for mail_id in mail_ids:
                res, msg_data = self.mail.fetch(mail_id, '(RFC822)')
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        # Extra logic to parse HTML/Text body and extract hrefs
                        body = str(msg.get_payload(decode=True))
                        # Basic URL extraction regex
                        extracted = re.findall(r'(https?://[^\s]+)', body)
                        urls_found.extend(extracted)
        except Exception as e:
            print(f"Error fetching alerts: {e}")

        return urls_found
