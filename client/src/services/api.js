const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:5000/api";

export async function apiRequest(endpoint, options = {}) {
  const token = localStorage.getItem("token");

  const headers = {
    "Content-Type": "application/json",
    ...options.headers,
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers,
    });

    const contentType = response.headers.get("content-type") || "";
    let data = null;

    if (contentType.includes("application/json")) {
      data = await response.json();
    } else {
      data = { message: await response.text() };
    }

    if (!response.ok) {
      const error = new Error(data.error || data.message || "Something went wrong");
      error.status = response.status;
      throw error;
    }

    return data;
  } catch (error) {
    if (error instanceof Error && error.message.includes("Failed to fetch")) {
      throw new Error("The server is unavailable. Start the backend and try again.", { cause: error });
    }

    if (error instanceof Error) {
      throw error;
    }

    throw new Error("The server is unavailable. Start the backend and try again.", {
      cause: error,
    });
  }
}

export async function apiUploadRequest(endpoint, formData, options = {}) {
  const token = localStorage.getItem("token");
  const headers = { ...options.headers };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      method: options.method || "POST",
      body: formData,
      headers,
    });

    const contentType = response.headers.get("content-type") || "";
    let data = null;

    if (contentType.includes("application/json")) {
      data = await response.json();
    } else {
      data = { message: await response.text() };
    }

    if (!response.ok) {
      const error = new Error(data.error || data.message || "Something went wrong");
      error.status = response.status;
      throw error;
    }

    return data;
  } catch (error) {
    if (error instanceof Error && error.message.includes("Failed to fetch")) {
      throw new Error("The server is unavailable. Start the backend and try again.", { cause: error });
    }

    if (error instanceof Error) {
      throw error;
    }

    throw new Error("The server is unavailable. Start the backend and try again.", {
      cause: error,
    });
  }
}