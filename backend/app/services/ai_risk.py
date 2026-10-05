from app.services.risk_analysis import calculate_trust_score


def generate_ai_risk_analysis(product, db):
    """
    Generates a structured AI-assisted risk analysis from
    the product's repair history.

    The current implementation is deterministic and uses
    project data instead of an external AI API.
    """

    result = calculate_trust_score(product, db)

    score = result["trust_score"]
    risk_flags = list(result["risk_flags"])

    if score >= 80:
        assessment = (
            "The product has a relatively trustworthy repair history "
            "with no major risk indicators detected."
        )

        recommendation = (
            "The repair history appears consistent. "
            "Normal verification is recommended before purchase."
        )

    elif score >= 50:
        assessment = (
            "The product has some repair-history indicators that "
            "should be reviewed before purchase or transfer."
        )

        recommendation = (
            "Review the repair records, documents and component "
            "replacement history carefully."
        )

    else:
        assessment = (
            "The product has significant risk indicators in its "
            "repair history."
        )

        recommendation = (
            "Further verification is strongly recommended before "
            "purchase or ownership transfer."
        )

    return {
        "trust_score": score,
        "risk_level": result["risk_level"],
        "risk_flags": risk_flags,
        "assessment": assessment,
        "recommendation": recommendation,
        "total_repairs": result["total_repairs"],
    }