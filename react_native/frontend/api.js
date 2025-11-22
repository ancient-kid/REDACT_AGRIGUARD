// api.js

export const BASE_URL = "http://10.10.43.25:8000"; // your backend IP

// Build multipart form-data for image
function buildFormData(uri) {
  const filename = uri.split("/").pop();
  const ext = filename.split(".").pop();
  const mime = `image/${ext === "jpg" ? "jpeg" : ext}`;

  const form = new FormData();
  form.append("file", {
    uri,
    name: filename,
    type: mime,
  });

  return form;
}

// Validate image
export async function uploadImage(uri) {
  const formData = buildFormData(uri);

  const res = await fetch(`${BASE_URL}/validate-image`, {
    method: "POST",
    body: formData,
  });

  return await res.json();
}

// Full analysis
export async function sendForPrediction(uri) {
  const formData = buildFormData(uri);

  const res = await fetch(`${BASE_URL}/analyze`, {
    method: "POST",
    body: formData,
  });

  const json = await res.json();
  return json.result; // backend returns { result: {...} }
}

// Health check
export async function checkHealth() {
  const res = await fetch(`${BASE_URL}/health`);
  return await res.json();
}
