// api.js

export const BASE_URL = "http://10.10.3.54:8000"; // your backend IP

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

// ===== USER MANAGEMENT =====

export async function createOrGetUser(userData) {
  const res = await fetch(`${BASE_URL}/api/users`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(userData),
  });

  if (!res.ok) {
    throw new Error(`Failed to create/get user: ${res.status}`);
  }

  return await res.json();
}

// ===== UPLOAD MANAGEMENT =====

export async function createUpload(uploadData) {
  const res = await fetch(`${BASE_URL}/api/uploads`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(uploadData),
  });

  if (!res.ok) {
    throw new Error(`Failed to create upload: ${res.status}`);
  }

  return await res.json();
}

export async function getUserUploads(userId) {
  const res = await fetch(`${BASE_URL}/api/uploads/${userId}`);

  if (!res.ok) {
    throw new Error(`Failed to get uploads: ${res.status}`);
  }

  return await res.json();
}

export async function getUploadImage(uploadId) {
  const res = await fetch(`${BASE_URL}/api/images/${uploadId}`);

  if (!res.ok) {
    throw new Error(`Failed to get image: ${res.status}`);
  }

  return res.url; // Return the image URL
}

// ===== CHAT MANAGEMENT =====

export async function createChat(chatData) {
  const res = await fetch(`${BASE_URL}/api/chats`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(chatData),
  });

  if (!res.ok) {
    throw new Error(`Failed to create chat: ${res.status}`);
  }

  return await res.json();
}

export async function getUserChats(userId) {
  const res = await fetch(`${BASE_URL}/api/chats/${userId}`);

  if (!res.ok) {
    throw new Error(`Failed to get chats: ${res.status}`);
  }

  return await res.json();
}

export async function addChatMessage(messageData) {
  const res = await fetch(`${BASE_URL}/api/chat-messages`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(messageData),
  });

  if (!res.ok) {
    throw new Error(`Failed to add message: ${res.status}`);
  }

  return await res.json();
}

// ===== DASHBOARD =====

export async function getDashboardStats(userId) {
  const res = await fetch(`${BASE_URL}/api/dashboard-stats/${userId}`);

  if (!res.ok) {
    throw new Error(`Failed to get dashboard stats: ${res.status}`);
  }

  return await res.json();
}