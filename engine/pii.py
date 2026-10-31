"""Personal-data guard. Runs BEFORE anything reaches the model.

Phase 1 (row 6b, decision 4.3): teams describe data, they do not upload it.
Messages or attachments containing customer identifiers or record-level data
are blocked, never sent to the model, and never stored.

Detects: Pakistani CNIC (with or without dashes), Pakistani IBAN, payment card
numbers (Luhn-checked), Pakistani mobile numbers, labelled bank account
numbers, e-mail addresses of individuals, passport-number labels, and pasted
tabular records (many delimited rows).
"""
import re

CNIC = re.compile(r"(?<!\d)\d{5}-\d{7}-\d(?!\d)")
CNIC_PLAIN = re.compile(r"(?<![\d.])(?:3|4|5|6|7|1)\d{12}(?![\d.])")
IBAN_PK = re.compile(r"\bPK\d{2}\s?[A-Z]{4}\s?(?:\d{4}\s?){3}\d{4}\b", re.I)
CARD = re.compile(r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)")
MOBILE_PK = re.compile(r"(?<!\d)(?:\+92[ -]?|0092[ -]?|0)3\d{2}[ -]?\d{7}(?!\d)")
ACCOUNT_LABELLED = re.compile(r"\b(?:a/?c|acct|account)\s*(?:no\.?|number|#|:)\s*[:#]?\s*\d[\d -]{7,}\d", re.I)
EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+\.[A-Za-z]{2,})\b")
RESERVED_DOMAINS = re.compile(r"(?:^|\.)(?:example|test|invalid|localhost)(?:\.|$)|^example\.(?:com|org|net)$", re.I)
PASSPORT = re.compile(r"\bpassport\s*(?:no\.?|number|#)\s*[:#]?\s*[A-Z]{2}\d{7}\b", re.I)


def _luhn(digits: str) -> bool:
    s, alt = 0, False
    for ch in reversed(digits):
        d = int(ch)
        if alt:
            d *= 2
            if d > 9:
                d -= 9
        s += d
        alt = not alt
    return s % 10 == 0


def _tabular_records(text: str) -> bool:
    """Five or more delimited rows that look like records with many digits."""
    rows = [ln for ln in text.splitlines() if ln.count(",") >= 3 or ln.count("\t") >= 3 or ln.count("|") >= 4]
    if len(rows) < 5:
        return False
    digit_rows = sum(1 for r in rows if sum(c.isdigit() for c in r) >= 6)
    return digit_rows >= 5


def scan(text: str) -> list[dict]:
    """Return a list of findings (type + masked sample). Empty list = clean."""
    findings = []

    def add(kind, m):
        s = m.group(0)
        masked = s[:2] + "*" * max(0, len(s) - 4) + s[-2:] if len(s) > 4 else "****"
        findings.append({"type": kind, "sample": masked})

    for m in CNIC.finditer(text):
        add("CNIC number", m)
    for m in CNIC_PLAIN.finditer(text):
        add("CNIC number (no dashes)", m)
    for m in IBAN_PK.finditer(text):
        add("IBAN", m)
    for m in CARD.finditer(text):
        digits = re.sub(r"\D", "", m.group(0))
        if 13 <= len(digits) <= 19 and _luhn(digits) and not CNIC_PLAIN.fullmatch(digits):
            add("Payment card number", m)
    for m in MOBILE_PK.finditer(text):
        add("Mobile number", m)
    for m in ACCOUNT_LABELLED.finditer(text):
        add("Bank account number", m)
    for m in EMAIL.finditer(text):
        if not RESERVED_DOMAINS.search(m.group(1)):
            add("E-mail address", m)
    for m in PASSPORT.finditer(text):
        add("Passport number", m)
    if _tabular_records(text):
        findings.append({"type": "Record-level data (pasted table)", "sample": "multiple delimited rows"})
    return findings


BLOCK_MESSAGE = (
    "I could not accept that message because it appears to contain customer data ({kinds}). "
    "It has not been sent to the AI model and has not been stored. Please describe the data instead "
    "(for example: \"customer CNIC, monthly salary and repayment history\") rather than pasting records or identifiers."
)
