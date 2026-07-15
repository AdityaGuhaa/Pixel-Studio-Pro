// =============================
// PixelStudio Pro - app.js
// =============================

const API_BASE = '';

let selectedModel = 'e2b';

// --- Model toggle ---
document.querySelectorAll('.model-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.model-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    selectedModel = btn.dataset.model;
  });
});

// --- Generate ---
document.getElementById('generate-btn').addEventListener('click', async () => {
  const prompt = document.getElementById('user-prompt').value.trim();
  if (!prompt) {
    showStatus('Please enter a description first.');
    return;
  }

  setLoading(true);
  showStatus('Rewriting prompt with ' + selectedModel.toUpperCase() + '...');
  hideResult();

  try {
    const response = await fetch(`${API_BASE}/api/generate/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt, model: selectedModel })
    });

    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || 'Generation failed');
    }

    const data = await response.json();
    showStatus('Loading image...');

    await renderResult(data);
    hideStatus();

  } catch (err) {
    showStatus('Error: ' + err.message);
  } finally {
    setLoading(false);
  }
});

async function renderResult(data) {
  // Show image
  const imageUrl = `${API_BASE}/api/image/${data.image_filename}`;
  const img = document.getElementById('output-image');
  const placeholder = document.getElementById('output-placeholder');

  await new Promise((resolve, reject) => {
    img.onload = resolve;
    img.onerror = () => reject(new Error('Failed to load generated image'));
    img.src = imageUrl;
  });

  placeholder.classList.add('hidden');
  img.classList.remove('hidden');

  // Add download button
  const existingBtn = document.getElementById('download-btn');
  if (existingBtn) existingBtn.remove();

  const downloadBtn = document.createElement('a');
  downloadBtn.id = 'download-btn';
  downloadBtn.href = `${API_BASE}/api/image/${data.image_filename}`;
  downloadBtn.download = data.image_filename;
  downloadBtn.textContent = 'DOWNLOAD IMAGE →';
  downloadBtn.target = '_blank';
  document.getElementById('output-block').appendChild(downloadBtn);

  // Populate report
  document.getElementById('positive-prompt').textContent = data.positive_prompt;
  document.getElementById('negative-prompt').textContent = data.negative_prompt;
  document.getElementById('rewrite-latency').textContent = data.rewrite_latency_seconds + 's';
  document.getElementById('gen-latency').textContent = data.image_gen_latency_seconds + 's';
  document.getElementById('total-latency').textContent = data.total_latency_seconds + 's';
  document.getElementById('model-used').textContent = data.model_used.toUpperCase();

  // Show result section
  document.getElementById('result-section').classList.remove('hidden');
  document.getElementById('result-section').scrollIntoView({ behavior: 'smooth' });
}

function setLoading(state) {
  const btn = document.getElementById('generate-btn');
  const btnText = document.getElementById('btn-text');
  btn.disabled = state;
  btnText.textContent = state ? 'GENERATING...' : 'GENERATE IMAGE';
}

function showStatus(msg) {
  const el = document.getElementById('status');
  el.textContent = msg;
  el.classList.remove('hidden');
}

function hideStatus() {
  document.getElementById('status').classList.add('hidden');
}

function hideResult() {
  document.getElementById('result-section').classList.add('hidden');
}
// --- Auto-detect system info ---
async function loadSystemInfo() {
  try {
    const response = await fetch(`${API_BASE}/api/system`);
    const data = await response.json();
    const footer = document.querySelector('footer span:last-child');
    if (footer) footer.textContent = data.platform;
  } catch (err) {
    console.log('System info unavailable');
  }
}

loadSystemInfo();

// --- Theme toggle ---
const themeBtn = document.getElementById('theme-btn');
if (themeBtn) {
  themeBtn.addEventListener('click', () => {
    document.body.classList.toggle('light-theme');
  });
}