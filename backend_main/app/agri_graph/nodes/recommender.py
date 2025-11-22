# nodes/recommender.py
def run(inputs: dict):
    """
    Simple rule-based suggestions by predicted class name.
    Inputs: pred_class (Healthy/Diseased), prob_healthy, maybe pred_raw
    """
    state = dict(inputs)  # preserve existing keys such as image_path

    pred_class = state.get("pred_class") or state.get("prediction", {}).get("class", "Unknown")
    prob_healthy = state.get("prob_healthy") or state.get("prediction", {}).get("prob_healthy", 0.0)
    prob_diseased = state.get("prob_diseased") or (1.0 - prob_healthy)

    recommendations = []
    severity = "Unknown"

    if isinstance(pred_class, str) and pred_class.lower() == "healthy":
        recommendations.append(
            "Plant appears healthy. Maintain regular monitoring, balanced irrigation, and proper nutrient supply."
        )
        severity = "None"
    else:
        disease_name = state.get("disease_name") or pred_class
        recommendations += [
            "Isolate affected plants to prevent spread.",
            "Inspect neighboring plants for similar symptoms.",
            "Remove severely affected leaves and dispose of them away from the field.",
            "Apply safe organic treatments (e.g., neem oil) or consult local extension officers for approved pesticides."
        ]
        if disease_name:
            recommendations.append(f"Document symptoms for {disease_name} and monitor progression daily.")
        if prob_diseased > 0.9:
            severity = "Severe"
        elif prob_diseased > 0.7:
            severity = "Moderate"
        else:
            severity = "Mild"

    state["recommendations"] = recommendations
    state["severity"] = severity
    return state