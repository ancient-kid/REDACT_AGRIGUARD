# AgriGuard

AgriGuard is a full-stack farming companion that blends explainable computer vision, guided chat, and historical dashboards to help growers diagnose plant disease, explore actionable treatments, and keep a traceable record of interactions.

## Why it stands out

- **Explainable disease classification** – A PyTorch `SimpleCNNMulti` model (weights in `backend_main/best_disease_model.pth`) delivers multi-class plant disease predictions, then Grad-CAM + SHAP workflows highlight _where_ and _why_ the model decided.
- **Human-friendly reasoning** – LangGraph nodes orchestrate the pipeline: image upload → preprocessing → CNN prediction → SHAP explanation → LLM summarization. The final summary + recommendations are stored alongside SHAP gradients for the UI.
- **Interactive chat guardian** – A Gemini-backed assistant keeps conversations going about treatments, prevention, and follow-up care. Treatment-related queries automatically pull in Serper search snippets so answers cite fresh guidance without leaving your flow.
- **Historical intelligence** – Every authenticated upload and chat is saved in the SQL-backed dashboard (`backend_main/app/database.py`). The website’s `dashboardStorage` service syncs uploads, chats, and stats (`/dashboard/stats`) for growers who want trend visibility.

## Architecture snapshot

| Layer | Technologies | Highlights |
| --- | --- | --- |
| Backend | FastAPI + LangGraph + SQLAlchemy | exposes `/analyze`, `/analyze/gradcam`, `/chat/*`, `/api/*`; stores SHAP gradients via `shap_storage.py`; uses cached `SimpleCNNMulti` + GradCAM helpers defined near `agri_graph/nodes/multi_class_cnn.py`. |
| Model & explainability | PyTorch CNN, Grad-CAM, SHAP | `best_disease_model.pth` holds trained weights; Grad-CAM draws boxes; SHAP gradients archived per upload so the UI can render a heatmap plus annotation. |
| Web frontend | Vite + React + Clerk | `App.tsx` shows home/features/about, Clerk-authenticated `Dashboard`, streaming `ChatPanel` with slider, and `DashboardSystem` that talks to `agriGuardAPI`. |
| Mobile frontend | Expo / React Native | `ImageUploader` validates + runs the pipeline, saves upload history, and integrates the same chat experience used on the web. |

## Model-specific callouts

1. **Custom CNN**: `SimpleCNNMulti` is trained for multi-class disease detection. It runs on CPU/GPU (`DEVICE` flag) and lazily loads (cached in `_disease_model_cache`) to avoid repeated disk reads.
2. **Grad-CAM + bounding boxes**: The helper draws red boxes around the top 5% of influential activation regions, so users can visually confirm what part of the plant dictated the prediction.
3. **SHAP storage**: `store_shap_gradient` archives computed gradients to disk and optionally uploads them somewhere (see `backend_main/shap_storage.py`), letting the front-end render a transparent heatmap.
4. **LLM summaries & chat**: Gemini summarizes the analysis context inside LangGraph, and the chat assistant shares the same context + history to answer follow-up questions.
5. **Search augmentation**: Treatment-related chat prompts trigger Serper queries, and top snippets are appended to the Gemini prompt, ensuring therapy suggestions stay grounded in current best practices.

## Getting started (high level)

1. **Backend**: Install `backend_main/requirements.txt`, then run `uvicorn app.main:app --reload`. Set `GEMINI_API_KEY` (and optionally `SERPER_API_KEY`) in `.env`.
2. **Web**: From `website/`, install dependencies, set Clerk keys, and run `npm run dev`. The dashboard uses `agriGuardAPI` + `dashboardStorage` to maintain user history.
3. **Mobile**: From `react_native/`, install dependencies and run `npx expo start`. The ImageUploader component wires to `uploadImage`, `sendForPrediction`, and backend chat APIs.

## Next steps you could try

- Hook up real storage for SHAP artifacts (S3, Azure, etc.).
- Expand the Serper helper to cache search snippets per session to avoid repeated calls.
- Add E2E tests for the dashboard history and chat slider using Playwright or Detox.

Let me know if you want badges, installation commands, or a specific template for this README.