def run_consistency_check(input_text1, input_text2, threshold):
    """
    Run consistency check between two inputs.
    
    Returns one of: "ALLOW", "WARN", "BLOCK", "ERROR"
    """
    # Simple consistency logic based on text similarity and threshold
    if not input_text1 or not input_text2:
        return "ERROR"

    # Basic keyword-based consistency check
    text1_lower = input_text1.lower()
    text2_lower = input_text2.lower()

    # Check for complete overlap
    set1 = set(text1_lower.split())
    set2 = set(text2_lower.split())

    if not set1 or not set2:
        return "ERROR"

    overlap = len(set1 & set2) / max(len(set1), len(set2))

    if overlap == 1.0:
        return "BLOCK"  # Identical inputs
    elif overlap >= 0.8:
        return "ALLOW"  # High similarity
    elif overlap >= 0.5:
        return "WARN"  # Moderate similarity
    else:
        return "WARN"  # Low similarity (still above completely different)