"""
Sending e-mail through Microsoft 365 with the Microsoft Graph API.

Microsoft is switching off password logins for SMTP (smtp.office365.com) at
the end of December 2026, so the site sends through Graph instead, with an
app registered in Microsoft Entra (Mail.Send, application permission):

    GRAPH_TENANT_ID=<Directory (tenant) ID>
    GRAPH_CLIENT_ID=<Application (client) ID>
    GRAPH_CLIENT_SECRET=<client secret value>
    GRAPH_SENDER=sito@axatel.it          the mailbox the e-mails come from

With these four in .env the site uses this backend (settings/production.py);
everything else (notifications, confirmations, error reports, attachments,
"Reply-To") works as with SMTP. Only the standard library is used.

Graph accepts at most about 3 MB of attachments in one message: above that
the file is left out and the e-mail says so (it is always in the CMS).
"""
import base64
import json
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from email.utils import parseaddr

from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend

GRAPH = "https://graph.microsoft.com/v1.0"
LOGIN = "https://login.microsoftonline.com"
MAX_ATTACHMENTS = 2_900_000  # bytes before base64; the whole request must stay under 4 MB
TOO_BIG_NOTE = {
    "text": "\n\n(Allegato non incluso: troppo grande per l'e-mail. Lo trovi nella richiesta, nel CMS.)\n",
    "html": "<p style='color:#c52317;font-size:12px'>Allegato non incluso: troppo grande per l'e-mail. "
            "Lo trovi nella richiesta, nel CMS.</p>",
}

_token = {"value": "", "expires": 0.0}
_lock = threading.Lock()


class GraphError(Exception):
    pass


def _post(url, data, headers, timeout):
    request = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, response.read()
    except urllib.error.HTTPError as error:
        return error.code, error.read()


def _explain(status, body) -> str:
    try:
        data = json.loads(body or b"{}")
        detail = data.get("error_description") or (data.get("error") or {}).get("message") or data.get("error")
    except ValueError:
        detail = (body or b"")[:300].decode("utf-8", "replace")
    return f"HTTP {status}: {detail}"


def get_token(timeout=15) -> str:
    """App-only token for Graph, reused until a minute before it expires."""
    with _lock:
        if _token["value"] and time.time() < _token["expires"] - 60:
            return _token["value"]
        tenant = settings.GRAPH_TENANT_ID
        form = urllib.parse.urlencode({
            "grant_type": "client_credentials",
            "client_id": settings.GRAPH_CLIENT_ID,
            "client_secret": settings.GRAPH_CLIENT_SECRET,
            "scope": "https://graph.microsoft.com/.default",
        }).encode()
        status, body = _post(f"{LOGIN}/{urllib.parse.quote(tenant)}/oauth2/v2.0/token", form,
                             {"Content-Type": "application/x-www-form-urlencoded"}, timeout)
        if status != 200:
            raise GraphError("Microsoft login refused the app (check GRAPH_TENANT_ID, GRAPH_CLIENT_ID, "
                             f"GRAPH_CLIENT_SECRET): {_explain(status, body)}")
        data = json.loads(body)
        _token.update(value=data["access_token"], expires=time.time() + int(data.get("expires_in", 3600)))
        return _token["value"]


def _people(addresses):
    people = []
    for address in addresses or []:
        name, email = parseaddr(address)
        if email:
            people.append({"emailAddress": {"address": email, **({"name": name} if name else {})}})
    return people


def build_payload(message, sender) -> dict:
    """The Graph sendMail body for a Django EmailMessage."""
    text = message.body or ""
    html = next((content for content, kind in getattr(message, "alternatives", []) if kind == "text/html"), None)
    if message.content_subtype == "html":
        html, text = text, None

    files, total = [], 0
    for attachment in message.attachments:
        if hasattr(attachment, "get_payload"):  # a MIME part
            name = attachment.get_filename() or "allegato"
            content = attachment.get_payload(decode=True) or b""
            kind = attachment.get_content_type()
        else:
            name, content, kind = attachment
            if isinstance(content, str):
                content = content.encode("utf-8")
            kind = kind or "application/octet-stream"
        files.append((name, content, kind))
        total += len(content)

    too_big = total > MAX_ATTACHMENTS
    if too_big:
        files = []
        if html is not None:
            html += TOO_BIG_NOTE["html"]
        if text is not None:
            text += TOO_BIG_NOTE["text"]

    mail = {
        "subject": message.subject,
        "body": {"contentType": "HTML", "content": html} if html is not None else {"contentType": "Text", "content": text},
        "toRecipients": _people(message.to),
        "ccRecipients": _people(message.cc),
        "bccRecipients": _people(message.bcc),
        "replyTo": _people(message.reply_to),
        "attachments": [
            {"@odata.type": "#microsoft.graph.fileAttachment", "name": name, "contentType": kind,
             "contentBytes": base64.b64encode(content).decode("ascii")}
            for name, content, kind in files
        ],
    }
    # Keep the display name ("Sito Axatel") when the sender address is the mailbox itself.
    name, address = parseaddr(message.from_email or "")
    if name and address.lower() == sender.lower():
        mail["from"] = {"emailAddress": {"name": name, "address": sender}}
    return {"message": mail, "saveToSentItems": True}


class GraphEmailBackend(BaseEmailBackend):
    def send_messages(self, email_messages):
        sent = 0
        timeout = getattr(settings, "EMAIL_TIMEOUT", 15) or 15
        sender = settings.GRAPH_SENDER
        for message in email_messages or []:
            if not message.recipients():
                continue
            try:
                token = get_token(timeout)
                payload = json.dumps(build_payload(message, sender)).encode("utf-8")
                status, body = _post(f"{GRAPH}/users/{urllib.parse.quote(sender)}/sendMail", payload,
                                     {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}, timeout)
                if status == 401:  # token revoked or expired early: one fresh try
                    _token["value"] = ""
                    token = get_token(timeout)
                    status, body = _post(f"{GRAPH}/users/{urllib.parse.quote(sender)}/sendMail", payload,
                                         {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}, timeout)
                if status != 202:
                    raise GraphError(f"Microsoft 365 did not send the e-mail from {sender}: {_explain(status, body)}")
                sent += 1
            except Exception:
                if not self.fail_silently:
                    raise
        return sent
