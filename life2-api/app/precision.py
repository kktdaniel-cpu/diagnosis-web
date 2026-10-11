"""Only confirmed, compatible facts may cross the precision entry boundary."""
from urllib.parse import urlsplit, urlunsplit

FIELDS = {
    "birth_year_self": ("profile.birth_year_self", "year", 1940, 2010),
    "birth_year_spouse": ("profile.birth_year_spouse", "year", 1940, 2010),
    "nps_monthly_self": ("pension.nps.monthly_self", "KRW_per_month", 0, 20000000),
    "nps_monthly_spouse": ("pension.nps.monthly_spouse", "KRW_per_month", 0, 20000000),
    "primary_job_exit_age": ("work.primary_job_exit_age", "age_years", 45, 80),
}

def precision_prefill(facts: dict, household: str) -> dict:
    out = {"household_type": household} if household in {"single", "couple"} else {}
    for name, (key, unit, lo, hi) in FIELDS.items():
        if household != "couple" and name.endswith("spouse"):
            continue
        fact = facts.get(key)
        if not isinstance(fact, dict) or fact.get("status") != "KNOWN" or fact.get("unit") != unit:
            continue
        value = fact.get("value")
        if type(value) is int and lo <= value <= hi:
            out[name] = value
    return out

def precision_entry_url(url: str) -> str:
    parts = urlsplit(url)
    # This companion page belongs to our precision site. Other configured URLs
    # retain their original entry behavior and receive no personal facts.
    if parts.scheme == "https" and parts.netloc == "diag.lpp20.com":
        return urlunsplit((parts.scheme, parts.netloc, "/life2-precision.html", "", ""))
    return url
