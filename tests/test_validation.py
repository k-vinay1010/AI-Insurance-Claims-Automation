from backend.claim_service import validate_claim

def test_missing_fields_are_flagged():
    flags = validate_claim({})
    assert len(flags) == 5
    assert any("patient name" in f.lower() for f in flags)

def test_valid_fields_have_no_flags():
    fields = {
        "patient_name": "Test Patient",
        "policy_number": "POL-12345",
        "hospital_name": "Example Hospital",
        "claim_amount": 25000.0,
        "claim_date": "12/11/2026",
    }
    assert validate_claim(fields) == []

def test_nonpositive_amount_is_flagged():
    fields = {
        "patient_name": "Test Patient",
        "policy_number": "POL-12345",
        "hospital_name": "Example Hospital",
        "claim_amount": 0,
        "claim_date": "12/11/2026",
    }
    assert any("greater than zero" in f for f in validate_claim(fields))
