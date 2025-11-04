const form = document.getElementById("generate-form");
const statusEl = document.getElementById("status");
const submitBtn = document.getElementById("submit-btn");
const resultSection = document.getElementById("result");
const resultSummary = document.getElementById("result-summary");
const resultVideo = document.getElementById("result-video");

const API_ENDPOINT = "/api/generate";

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const fileInput = document.getElementById("model");
  if (!fileInput.files || fileInput.files.length === 0) {
    updateStatus("Please select a GLTF or GLB file to upload.", "error");
    return;
  }

  const file = fileInput.files[0];
  if (!file.name.toLowerCase().endsWith(".gltf") && !file.name.toLowerCase().endsWith(".glb")) {
    updateStatus("Only .gltf or .glb files are supported.", "error");
    return;
  }

  const prompt = document.getElementById("prompt").value.trim();

  const formData = new FormData();
  formData.append("model", file);
  if (prompt) {
    formData.append("prompt", prompt);
  }

  setLoading(true);
  updateStatus("Uploading model and requesting Google Veo…", "info");

  try {
    const response = await fetch(API_ENDPOINT, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const text = await response.text();
      throw new Error(text || `Request failed with status ${response.status}`);
    }

    const data = await response.json();
    handleSuccess(data);
  } catch (error) {
    console.error(error);
    updateStatus(`An error occurred: ${error.message}`, "error");
  } finally {
    setLoading(false);
  }
});

function handleSuccess(data) {
  const { videoUrl, jobId, status, usedPrompt, sourceModel } = data;

  updateStatus("Successfully created a Veo job!", "success");
  resultSection.classList.remove("hidden");

  resultSummary.innerHTML = `Job <strong>${jobId}</strong> for <strong>${sourceModel}</strong> is currently <strong>${status}</strong>.<br/>Prompt: <em>${escapeHtml(usedPrompt)}</em>`;

  if (videoUrl) {
    resultVideo.classList.remove("hidden");
    resultVideo.src = videoUrl;
  } else {
    resultVideo.classList.add("hidden");
    resultVideo.removeAttribute("src");
  }
}

function updateStatus(message, type = "info") {
  statusEl.textContent = message;
  statusEl.dataset.type = type;
}

function setLoading(isLoading) {
  submitBtn.disabled = isLoading;
  submitBtn.textContent = isLoading ? "Generating…" : "Generate video";
}

function escapeHtml(str) {
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
