import imaplib
import poplib
import email
from email.header import decode_header
from email.utils import parsedate_to_datetime
from datetime import datetime, timezone
import re
import os


class POP3AsIMAP:
    """
    Minimal IMAP-like interface over POP3 for:
      - login(user, pwd)
      - select("inbox")  (no-op)
      - search(None, "ALL") -> ("OK", [b"1 2 3 ..."])
      - fetch(b"7", "(RFC822)") -> ("OK", [(b"7 (RFC822)", raw_bytes)])
      - logout() -> quit
    """
    def __init__(self, server: str, port: int = 995, timeout: int = 30):
        self._pop = poplib.POP3_SSL(server, port, timeout=timeout)

    def login(self, user: str, password: str):
        self._pop.user(user)
        self._pop.pass_(password)
        return "OK", [b""]

    def select(self, mailbox: str = "inbox"):
        # POP3 has no folders; always a single mailbox.
        return "OK", [b""]

    def search(self, charset, *criteria):
        # POP3 can’t server-side search like IMAP; for your use-case "ALL" means list everything.
        # items are like [b'1 1234', b'2 4567', ...]
        resp, items, _octets = self._pop.list()
        if not items:
            return "OK", [b""]
        ids = [line.split()[0] for line in items]  # b'1', b'2', ...
        return "OK", [b" ".join(ids)]

    def fetch(self, message_id, what):
        # Accept bytes/str/int message_id like IMAP code uses.
        if isinstance(message_id, (bytes, bytearray)):
            message_id = message_id.decode("ascii", "ignore")


# Configs
POP_SERVER = os.environ.get("POP_SERVER", "")
IMAP_SERVER = os.environ.get("IMAP_SERVER", "imap.gmail.com")
MESSAGE_COUNT = int(os.environ.get("MSG_COUNT", "30"))
EMAIL_USR = os.environ.get("EMAIL_USER")
EMAIL_PWD = os.environ.get("EMAIL_PASSWORD")
HEADER_REGEX_PATTERN = os.environ.get("HEADER_REGEX_PATTERN", r"OTP to Verify Email")
REGEX_PATTERN = os.environ.get("REGEX_PATTERN", r"(\b\d{4,6}\b)")


def is_not_expired(msg, ndt):
    dt = parsedate_to_datetime(msg.get("Date", ""))
    if dt is None:  # no/invalid Date header
        is_newer_than_now = False
    else:
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        is_newer_than_now = dt.astimezone(timezone.utc).timestamp() > ndt
    return is_newer_than_now


# OTP extraction function
def extract_otp(dt=None):
    try:
        if POP_SERVER:
            # Connect to POP server
            mail = POP3AsIMAP(POP_SERVER)
        else:
            # Connect to IMAP server
            mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL_USR, EMAIL_PWD)

        # Select the mailbox (inbox)
        mail.select("inbox")

        # Search for all emails in the inbox
        status, messages = mail.search(None, "ALL")

        if status != "OK":
            print("No messages found.")
            return

        # Get list of email IDs
        email_ids = messages[0].split()

        # Regular expression to match OTP (e.g., 123456)
        header_pattern = re.compile(HEADER_REGEX_PATTERN)
        otp_pattern = re.compile(REGEX_PATTERN)

        # Loop through emails (latest first)
        for email_id in email_ids[:-MESSAGE_COUNT:-1]:  # Check last 30 emails
            # Fetch the email
            status, msg_data = mail.fetch(email_id, "(RFC822)")
            if status != "OK":
                print("Failed to fetch email.")
                continue

            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    # Parse email content
                    msg = email.message_from_bytes(response_part[1])
                    if not dt or is_not_expired(msg, dt):
                        subject, encoding = decode_header(msg["subject"])[0]
                        if isinstance(subject, bytes):
                            subject = subject.decode(encoding if encoding else "utf-8")
                        otp_match = header_pattern.search(subject)
                        if otp_match:
                            parts = msg.walk() if msg.is_multipart() else [msg]
                            p = next((x for x in parts if
                                      x.get_content_type() in ("text/plain", "text/html") and "attachment" not in (
                                          x.get("Content-Disposition", ""))), msg)
                            body = ((p.get_payload(decode=True) or b"").decode(p.get_content_charset() or "utf-8", "replace"))
                            otp_match = otp_pattern.search(body)
                            if otp_match:
                                print(f"OTP Found: {otp_match.groups()[0]}")
                                print(f"Body: {body}")
                                mail.logout()
                                return otp_match.groups()[0]
        print("No OTP found in recent emails.")
        mail.logout()
    except Exception as e:
        print(f"An error occurred: {e}")


def main(dt=None):
    import io, contextlib

    sink = io.StringIO()
    with contextlib.redirect_stdout(sink), contextlib.redirect_stderr(sink):
        r = extract_otp(dt)
    print("" if r is None else r)


# Run the OTP extraction
if __name__ == "__main__":
    otp_code = extract_otp()
    if otp_code:
        print(f"Extracted OTP Code: {otp_code}")
    else:
        print("No OTP code extracted.")

    print("Main:")
    main(1766163600)