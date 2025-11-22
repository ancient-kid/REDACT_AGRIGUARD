from langgraph.graph import Graph
from nodes.image_input import image_input_node
from nodes.preprocess import preprocess_node
from nodes.model_predict import model_predict_node
from nodes.shap_explain import shap_node
from nodes.recommender import recommender_node
from nodes.llm_summarize import llm_node
from nodes.report_output import report_node
import sys, os
sys.path.append(os.path.dirname(__file__))
sys.path.append(os.path.join(os.path.dirname(__file__), "nodes"))

# Fake input for testing
test_data = {
    "image_path": "test.jpg",
    "corrupt": False,
    "preprocessed": True,
    "model_raw_output": {"status": "DISEASED", "confidence": 0.84},
    "shap_result": "Fake SHAP highlight example",
    "recommendation": "Increase air circulation, prune affected leaves",
    "summary": "Sample summary generated.",
}

def run():
    print("Running LangGraph test flow...")

    g = Graph()

    g.add_node("image_input", image_input_node)
    g.add_node("preprocess", preprocess_node)
    g.add_node("model", model_predict_node)
    g.add_node("shap", shap_node)
    g.add_node("reco", recommender_node)
    g.add_node("llm", llm_node)
    g.add_node("report", report_node)

    # Flow edges
    g.add_edge("image_input", "preprocess")
    g.add_edge("preprocess", "model")
    g.add_edge("model", "shap")
    g.add_edge("shap", "reco")
    g.add_edge("reco", "llm")
    g.add_edge("llm", "report")

    out = g.run(test_data)
    print("\nFinal Output:")
    print(out)

if __name__ == "__main__":
    run()
