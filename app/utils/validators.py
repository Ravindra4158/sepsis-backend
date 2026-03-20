import re
from typing import Optional

VALID_ROLES = {"doctor", "nurse", "admin"}
VALID_WARDS = ["ICU-A","ICU-B","ICU-C","ICU-D","CCU","PICU","NICU"]
VALID_GENDERS = ["M","F","O"]

def is_valid_email(email: str) -> bool:
    return bool(re.match(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$", email))

def is_strong_password(pw: str) -> tuple[bool, Optional[str]]:
    if len(pw) < 8: return False, "Minimum 8 characters"
    if not re.search(r"[A-Z]", pw): return False, "Need at least one uppercase letter"
    if not re.search(r"[0-9]", pw): return False, "Need at least one number"
    return True, None
