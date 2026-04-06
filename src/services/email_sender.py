class EmailSender:
    """
    Handles routing emails. Per user request, this is set to Draft Mode ONLY preventing 
    unauthorized live sending.
    """
    def __init__(self, mode="draft"):
        self.mode = mode

    def save_to_drafts(self, to_email: str, subject: str, html_body: str):
        """
        Simulates interacting with Gmail API to create a draft in the user's inbox
        """
        print(f"[EmailSender] Saved DRAFT to inbox: To: {to_email} | Subject: {subject}")
        # In full prod, this uses googleapiclient.discovery.build('gmail', 'v1') and users.drafts().create(userId='me', body=draft)
        return {"status": "created", "folder": "Drafts"}

    def send_email(self, to_email: str, subject: str, html_body: str):
        if self.mode == "draft":
            print(f"[EmailSender] SAFETY BLOCK: Cannot send directly in draft mode. Rerouting to Drafts.")
            return self.save_to_drafts(to_email, subject, html_body)
        
        print(f"[EmailSender] LIVE SENDING to {to_email}")
        return {"status": "sent"}
