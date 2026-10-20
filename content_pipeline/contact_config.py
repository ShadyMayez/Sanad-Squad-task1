"""Company contact configuration and CTA helpers for SanadSquad marketing posts.

Directive: SANADSQUAD_V3_OFFICIAL_BRAND_INTEGRATION_01

Enforces:
- Structured, editable company-contact.json
- Company name: SanadSquad
- Verified business inquiries email: frank@sanadsquad.com (from official website)
- Verified contact channels: https://sanadsquad.com/contact/, @castle_chain, @SanadSquad
- No fictional phone numbers (+1-555-0199 strictly banned)
- Recruitment email (career@sanadsquad.com) strictly barred from commercial CTAs
- Explicit approval status (approved: bool)
- Graceful handling of email-only and contact-form CTAs when no phone exists
- Pure metadata treatment (never evidence for technical claims)
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Literal
from pydantic import BaseModel, Field, model_validator

ROOT = Path(__file__).resolve().parent.parent

# Regex patterns for contact extraction
EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
PHONE_PATTERN = re.compile(r"\+?[1-9]\d{0,2}[-.\s]?(?:\(?\d{1,4}\)?[-.\s]?)?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}")

# Known demonstration / fictional placeholder contacts (NEVER authorized for publication)
SYNTHETIC_DEMO_CONTACTS = {
    "contact@sanadsquad.com",
    "+1-555-0199",
    "+1-555-9999",
}

# Recruitment emails (strictly barred from commercial business inquiries)
RECRUITMENT_EMAILS = {
    "career@sanadsquad.com",
}


def is_synthetic_contact(text: str) -> bool:
    """Return True if text contains synthetic demonstration contact placeholders."""
    for demo in SYNTHETIC_DEMO_CONTACTS:
        if demo.lower() in text.lower():
            return True
    return False


def is_recruitment_email(text: str) -> bool:
    """Return True if text contains recruitment email address."""
    for rec in RECRUITMENT_EMAILS:
        if rec.lower() in text.lower():
            return True
    return False


def extract_emails(text: str) -> list[str]:
    """Extract email addresses from text."""
    return EMAIL_PATTERN.findall(text)


def extract_phone_numbers(text: str) -> list[str]:
    """Extract genuine phone numbers, filtering out dates, version numbers, and URLs."""
    clean = re.sub(r"https?://[^\s)]+", "", text)
    clean = re.sub(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b", "", clean)
    clean = re.sub(r"\b\d{4}-\d{2}-\d{2}\b", "", clean)
    clean = re.sub(r"\b(?:0x[0-9a-fA-F]+|\d+\.\d+(?:\.\d+)?)\b", "", clean)
    candidates = PHONE_PATTERN.findall(clean)
    phones: list[str] = []
    for c in candidates:
        c_clean = c.strip().rstrip(".,;")
        digits = re.sub(r"\D", "", c_clean)
        if len(digits) >= 7 and (c_clean.startswith("+") or "phone" in text.lower()):
            phones.append(c_clean)
    return phones


class CompanyContactConfig(BaseModel):
    company_name: Literal["SanadSquad"] = "SanadSquad"
    business_inquiries_email: str = Field(default="", description="Verified business inquiries email.")
    business_phone_number: str | None = Field(default=None, description="Optional approved business phone number with country code.")
    contact_form_url: str | None = Field(default="https://sanadsquad.com/contact/", description="Verified official contact form URL.")
    telegram: str | None = Field(default="@castle_chain", description="Verified official Telegram handle.")
    x_handle: str | None = Field(default="@SanadSquad", description="Verified official X handle.")
    official_website: str | None = Field(default="https://sanadsquad.com", description="Official website URL.")
    approved: bool = Field(default=False, description="Explicit approval status. If False, contact details must not be used.")
    status: Literal["APPROVED", "AWAITING_OWNER_APPROVAL", "SUSPENDED"] = "AWAITING_OWNER_APPROVAL"
    approved_by: str | None = None
    approved_at: str | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def validate_approval_consistency(self) -> CompanyContactConfig:
        if self.approved:
            has_email = bool(self.business_inquiries_email and self.business_inquiries_email.strip())
            has_form = bool(self.contact_form_url and self.contact_form_url.strip())
            if not has_email and not has_form:
                raise ValueError("Approved contact configuration requires a non-empty business_inquiries_email or contact_form_url.")
            if has_email:
                email_clean = self.business_inquiries_email.strip().lower()
                if email_clean in {c.lower() for c in SYNTHETIC_DEMO_CONTACTS}:
                    raise ValueError(f"Fictional or unapproved contact placeholder '{self.business_inquiries_email}' cannot be approved.")
                if email_clean in {r.lower() for r in RECRUITMENT_EMAILS}:
                    raise ValueError(f"Recruitment email '{self.business_inquiries_email}' cannot be approved for commercial inquiries.")
            if self.business_phone_number and self.business_phone_number.strip():
                phone_clean = self.business_phone_number.strip()
                if phone_clean in SYNTHETIC_DEMO_CONTACTS:
                    raise ValueError(f"Fictional telephone number '{phone_clean}' cannot be approved.")
                if not phone_clean.startswith("+"):
                    raise ValueError(
                        f"Approved phone number '{phone_clean}' must include a country code starting with '+'."
                    )
            if self.status != "APPROVED":
                self.status = "APPROVED"
        else:
            if self.status == "APPROVED":
                self.status = "AWAITING_OWNER_APPROVAL"
        return self

    def is_operational(self) -> bool:
        """Returns True only if contact details are present and explicitly approved."""
        has_channel = bool(self.business_inquiries_email and self.business_inquiries_email.strip()) or \
                      bool(self.contact_form_url and self.contact_form_url.strip())
        return self.approved is True and has_channel

    def get_missing_fields(self) -> list[str]:
        """Returns the exact list of missing required fields."""
        missing = []
        if not (self.business_inquiries_email and self.business_inquiries_email.strip()) and \
           not (self.contact_form_url and self.contact_form_url.strip()):
            missing.append("business_inquiries_email or contact_form_url")
        if not self.approved:
            missing.append("approved (approval status)")
        return missing


def load_company_contact(path: Path | None = None) -> CompanyContactConfig:
    """Load company contact configuration from JSON file.
    
    If file is missing, returns an unapproved default configuration.
    """
    target = path or (ROOT / "company-contact.json")
    if not target.exists():
        return CompanyContactConfig(
            company_name="SanadSquad",
            business_inquiries_email="frank@sanadsquad.com",
            business_phone_number=None,
            contact_form_url="https://sanadsquad.com/contact/",
            telegram="@castle_chain",
            x_handle="@SanadSquad",
            official_website="https://sanadsquad.com",
            approved=False,
            status="AWAITING_OWNER_APPROVAL",
            notes="File company-contact.json not found on disk. Initialized with official public channels awaiting owner approval.",
        )
    with open(target, "r", encoding="utf-8") as f:
        data = json.load(f)
    return CompanyContactConfig.model_validate(data)


def build_contextual_cta(
    service_line: str,
    contact: CompanyContactConfig,
    offering_type: str | None = None,
    channel: str = "email",
) -> str:
    """Build a natural, contextual CTA string for a given service line using approved contact info.
    
    Supports the 5 approved official commercial offerings:
    - Blockchain security audits (web3-security)
    - Penetration testing (pentesting)
    - Agentic security tooling (agentic-security)
    - Agentic payments
    - Security consulting (consulting)
    
    Must NOT contain banned characters (no em dash '—', no separator en dash '–', no curly quotes).
    Gracefully formats email-only, contact form, or phone CTAs without fabricating telephone numbers.
    """
    if not contact.is_operational():
        raise ValueError("Cannot build contact CTA: Contact details are not approved or operational.")

    email = contact.business_inquiries_email.strip() if contact.business_inquiries_email else ""
    phone = contact.business_phone_number.strip() if contact.business_phone_number else ""
    form = contact.contact_form_url.strip() if contact.contact_form_url else ""

    ot = (offering_type or service_line).lower().strip()
    if "consult" in ot or "architecture" in ot:
        invitation = "Designing your protocol architecture? Request a security consultation with SanadSquad."
    elif "pay" in ot or "x402" in ot or "mpp" in ot:
        invitation = "Building a payment agent? SanadSquad reviews authorization and facilitator integrations."
    elif "tool" in ot or "agent" in ot or "detector" in ot:
        invitation = "Building protocol security tools? Consult SanadSquad on custom AI detectors."
    elif "pentest" in ot or "penetration" in ot or "infrastructure" in ot or "web2" in ot:
        invitation = "Assessing infrastructure risks? Request a SanadSquad penetration test."
    elif "audit" in ot or "web3" in ot or "blockchain" in ot or "contract" in ot:
        invitation = "Reviewing protocol security? Contact SanadSquad to discuss an audit."
    else:
        invitation = "Evaluating your protocol security? Contact SanadSquad."

    # Contact channel formatting
    if channel == "form" and form:
        return f"{invitation} Contact: {form}"
    if channel == "telegram" and contact.telegram:
        return f"{invitation} Telegram: {contact.telegram}"
    if channel == "x" and contact.x_handle:
        return f"{invitation} X: {contact.x_handle}"

    if email and phone:
        return f"{invitation} Email: {email} | Phone: {phone}"
    elif email:
        return f"{invitation} Email: {email}"
    elif form:
        return f"{invitation} Contact: {form}"
    else:
        return f"{invitation} Contact SanadSquad: https://sanadsquad.com/contact/"
