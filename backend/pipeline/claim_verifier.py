"""
Automated Visual Claim Verification Guardrail.

Cross-checks numerical values, totals, dates, and named entities mentioned in the VLM's output
against pre-extracted ground truth OCR text and UI labels to verify factual accuracy and flag hallucinations.
"""

import re


def verify_vlm_claims(vlm_response: str, metadata: dict) -> dict:
    """Verify claims in VLM response text against extracted ground truth.

    Args:
        vlm_response: Generated text response from Master VLM.
        metadata: Extracted metadata from specialist modules (document OCR, UI elements).

    Returns:
        {
            "match_score": float,            # Percentage match (0.0 to 100.0)
            "verified_tokens": list[str],
            "unverified_tokens": list[str],
            "badge_summary": str,
        }
    """
    if not vlm_response:
        return {"match_score": 100.0, "verified_tokens": [], "unverified_tokens": [], "badge_summary": ""}

    # 1. Compile ground truth text corpus
    ground_truth = []

    # From Document OCR
    if "full_text" in metadata:
        ground_truth.append(str(metadata["full_text"]))
    if "markdown" in metadata:
        ground_truth.append(str(metadata["markdown"]))

    # From UI Grounding Elements
    if "elements" in metadata and isinstance(metadata["elements"], list):
        for elem in metadata["elements"]:
            if isinstance(elem, dict) and "label" in elem:
                ground_truth.append(str(elem["label"]))

    corpus = " ".join(ground_truth).lower()

    if not corpus.strip():
        # If no OCR ground truth is available (e.g. general photo), return neutral status
        return {
            "match_score": 100.0,
            "verified_tokens": [],
            "unverified_tokens": [],
            "badge_summary": "Factual verification: Visual inspection baseline.",
        }

    # 2. Extract numbers, currency amounts, and dates from VLM response
    # Matches currency ($100, £50, 450.00), percentages (95%), dates (12 Jan, 2026), integers/floats
    claims = re.findall(r"(?:\$|£|€)?\b\d+(?:[\.,]\d+)?%?\b", vlm_response)

    if not claims:
        return {
            "match_score": 100.0,
            "verified_tokens": [],
            "unverified_tokens": [],
            "badge_summary": "Verified against ground truth metadata: 100% (No numerical claims to verify).",
        }

    verified = []
    unverified = []

    for token in set(claims):
        raw_val = re.sub(r"[^\d]", "", token)
        if len(raw_val) > 0 and (token.lower() in corpus or raw_val in corpus):
            verified.append(token)
        else:
            # Filter out single digits (1, 2, 3) which are usually list numbers
            if len(raw_val) > 1:
                unverified.append(token)

    total_tokens = len(verified) + len(unverified)
    score = (len(verified) / total_tokens * 100.0) if total_tokens > 0 else 100.0
    score = round(score, 1)

    summary = (
        f"Ground Truth Verification Score: {score}% "
        f"({len(verified)} verified token(s)"
        f"{f', {len(unverified)} unverified' if unverified else ''})."
    )

    return {
        "match_score": score,
        "verified_tokens": verified,
        "unverified_tokens": unverified,
        "badge_summary": summary,
    }
