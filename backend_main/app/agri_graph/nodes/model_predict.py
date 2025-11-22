import logging
from app.model import run_prediction

LOGGER = logging.getLogger(__name__)

def model_predict(state):
    image_path = state["image_path"]
    
    LOGGER.info("ModelPredict node received image_path=%s", image_path)

    pred_class, confidence, prob_healthy, prob_diseased = run_prediction(image_path)

    state["prediction"] = {
        "class": pred_class,
        "confidence": confidence,
        "prob_healthy": prob_healthy,
        "prob_diseased": prob_diseased
    }
    state["pred_class"] = pred_class
    state["prob_healthy"] = prob_healthy
    state["prob_diseased"] = prob_diseased

    LOGGER.info("ModelPredict state updated: %s", state["prediction"])
    return state
