
def review_evidence(
    required_evidence: str,
    submitted_evidence: str
):
    """
    Compare required evidence with submitted evidence.

    This is a basic demo comparison.
    It does not prove legal compliance or
    official BIS certification.
    """

    required = required_evidence.lower().strip()
    submitted = submitted_evidence.lower().strip()

    if not submitted:
        status = "Missing"

    elif required == submitted:
        status = "Matched"

    elif required in submitted or submitted in required:
        status = "Partially matched"

    else:
        status = "Needs review"

    if status == "Matched":
        evidence_status = "Evidence found"

    elif status == "Missing":
        evidence_status = "Not found"

    else:
        evidence_status = "Needs review"

    return {
        "required_evidence": required_evidence,
        "submitted_evidence": submitted_evidence,
        "status": status,
        "evidence_status": evidence_status,
        "message": (
            "This is a preliminary text comparison. "
            "Manual verification is required."
        )
    }