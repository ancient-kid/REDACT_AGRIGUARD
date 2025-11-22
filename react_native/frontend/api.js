// BASE URL must point to your FastAPI backend
const BASE_URL = "http://10.10.43.25:8000";  
// use your WiFi IP from ipconfig
// or 10.0.2.2 for Android emulator

export async function uploadImage(uri) {
  let filename = uri.split('/').pop();
  let match = /\.(\w+)$/.exec(filename);
  let type = match ? `image/${match[1]}` : 'image/jpeg';

  let formData = new FormData();
  formData.append("file", { uri, name: filename, type });

  let res = await fetch(`${BASE_URL}/validate-image`, {
    method: "POST",
    body: formData,
    headers: { "Content-Type": "multipart/form-data" }
  });

  return await res.json();
}

export async function sendForPrediction(uri) {
  let filename = uri.split('/').pop();
  let match = /\.(\w+)$/.exec(filename);
  let type = match ? `image/${match[1]}` : 'image/jpeg';

  let formData = new FormData();
  formData.append("file", { uri, name: filename, type });

  let res = await fetch(`${BASE_URL}/predict`, {
    method: "POST",
    body: formData,
    headers: { "Content-Type": "multipart/form-data" }
  });

  return await res.json();
}
