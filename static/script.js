// ============================================================
//  RESUME ANALYZER — FRONTEND SCRIPT
//  Handles: drag-drop, file reading, API calls, result render
// ============================================================

const dropZone    = document.getElementById('dropZone');
const fileInput   = document.getElementById('fileInput');
const resumeText  = document.getElementById('resumeText');
const filePill    = document.getElementById('filePill');
const fileNameEl  = document.getElementById('fileNameDisplay');
const analyzeBtn  = document.getElementById('analyzeBtn');
const errorMsg    = document.getElementById('errorMsg');
const loadingOverlay = document.getElementById('loadingOverlay');
const loaderMsg   = document.getElementById('loaderMsg');

let uploadedFile  = null;

// ---------- Drag & Drop ----------
dropZone.addEventListener('click', () => fileInput.click());

dropZone.addEventListener('dragover', e => {
  e.preventDefault();
  dropZone.classList.add('drag-over');
});

dropZone.addEventListener('dragleave', () => {
  dropZone.classList.remove('drag-over');
});

dropZone.addEventListener('drop', e => {
  e.preventDefault();
  dropZone.classList.remove('drag-over');
  const file = e.dataTransfer.files[0];
  if (file) setFile(file);
});

fileInput.addEventListener('change', () => {
  if (fileInput.files[0]) setFile(fileInput.files[0]);
});

function setFile(file) {
  uploadedFile = file;
  fileNameEl.textContent = file.name;
  filePill.style.display = 'inline-flex';
  dropZone.style.opacity = '0.5';
}

document.getElementById('removeFile').addEventListener('click', () => {
  uploadedFile = null;
  fileInput.value = '';
  filePill.style.display = 'none';
  dropZone.style.opacity = '1';
});

// ---------- Loading messages ----------
const loadingSteps = [
  'Extracting text from resume...',
  'Running spaCy NLP pipeline...',
  'Detecting skills and entities...',
  'Scoring against job profiles...',
  'Calculating ATS compatibility...',
  'Generating your report...'
];
let loadingInterval;

function startLoading() {
  let i = 0;
  loaderMsg.textContent = loadingSteps[0];
  loadingOverlay.style.display = 'flex';
  loadingInterval = setInterval(() => {
    i = (i + 1) % loadingSteps.length;
    loaderMsg.textContent = loadingSteps[i];
  }, 1400);
}

function stopLoading() {
  clearInterval(loadingInterval);
  loadingOverlay.style.display = 'none';
}

// ---------- Main analyze function ----------
async function analyzeResume() {
  const text = resumeText.value.trim();
  const jd   = document.getElementById('jdText').value.trim();

  hideError();

  if (!uploadedFile && text.length < 50) {
    showError('Please upload a file or paste at least 50 characters of resume text.');
    return;
  }

  const formData = new FormData();
  if (uploadedFile) {
    formData.append('file', uploadedFile);
  } else {
    formData.append('resume_text', text);
  }
  if (jd) formData.append('job_description', jd);

  analyzeBtn.disabled = true;
  startLoading();

  try {
    const response = await fetch('/analyze', {
      method: 'POST',
      body: formData
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || 'Server error. Please try again.');
    }

    stopLoading();
    analyzeBtn.disabled = false;
    renderResults(data);

  } catch (err) {
    stopLoading();
    analyzeBtn.disabled = false;
    showError(err.message);
  }
}

// ---------- Render results ----------
function renderResults(d) {
  document.getElementById('upload-section').style.display = 'none';
  const section = document.getElementById('resultsSection');
  section.style.display = 'block';
  section.scrollIntoView({ behavior: 'smooth' });

  // ATS score ring animation
  const score = Math.min(100, Math.max(0, d.ats_score));
  const circumference = 314;
  const offset = circumference * (1 - score / 100);
  const arc = document.getElementById('atsArc');
  arc.setAttribute('stroke-dashoffset', circumference);
  const ringColor = score >= 75 ? '#00c48c' : score >= 50 ? '#f59e0b' : '#ef4444';
  arc.setAttribute('stroke', ringColor);

  setTimeout(() => {
    arc.style.transition = 'stroke-dashoffset 1s ease';
    arc.setAttribute('stroke-dashoffset', offset);
  }, 100);

  // Animate number count-up
  animateNumber('atsNum', score, 1000);

  document.getElementById('atsVerdict').textContent = d.verdict || '';
  document.getElementById('atsDetail').textContent  = d.ats_detail || '';

  // Summary cards
  const summaryData = [
    { label: 'Top role match', value: d.top_role || '—' },
    { label: 'Experience level', value: d.experience_level || '—' },
    { label: 'Skills detected', value: (d.found_skills || []).length + ' skills' }
  ];
  document.getElementById('summaryCards').innerHTML = summaryData.map(c => `
    <div class="summary-card">
      <div class="sc-label">${c.label}</div>
      <div class="sc-value">${c.value}</div>
    </div>`).join('');

  // Role compatibility bars
  document.getElementById('rolesList').innerHTML = (d.role_matches || []).map(r => `
    <div class="role-row">
      <div class="role-name">${r.role}</div>
      <div class="role-bar-bg">
        <div class="role-bar-fill" style="width:0%" data-target="${r.score}%"></div>
      </div>
      <div class="role-pct">${r.score}%</div>
    </div>`).join('');

  setTimeout(() => {
    document.querySelectorAll('.role-bar-fill').forEach(bar => {
      bar.style.width = bar.dataset.target;
    });
  }, 150);

  // Missing skills
  const missing = d.missing_skills || [];
  document.getElementById('skillsCloud').innerHTML = missing.length
    ? missing.map(s => `<span class="skill-tag">${s}</span>`).join('')
    : '<span style="color:#6b7280;font-size:14px">No critical gaps detected — great job!</span>';

  // Found skills
  const found = d.found_skills || [];
  document.getElementById('foundSkills').innerHTML = found.length
    ? found.map(s => `<span class="skill-tag">${s}</span>`).join('')
    : '<span style="color:#6b7280;font-size:14px">No skills detected — try adding a Skills section.</span>';

  // Tips
  document.getElementById('tipsList').innerHTML = (d.tips || []).map(t =>
    `<li>💡 ${t}</li>`).join('');
}

// ---------- Helpers ----------
function animateNumber(id, target, duration) {
  const el = document.getElementById(id);
  const start = performance.now();
  function step(now) {
    const progress = Math.min((now - start) / duration, 1);
    el.textContent = Math.round(progress * target);
    if (progress < 1) requestAnimationFrame(step);
  }
  requestAnimationFrame(step);
}

function showError(msg) {
  errorMsg.textContent = msg;
  errorMsg.style.display = 'block';
}

function hideError() {
  errorMsg.style.display = 'none';
}

function resetApp() {
  document.getElementById('resultsSection').style.display = 'none';
  document.getElementById('upload-section').style.display = 'block';
  document.getElementById('upload-section').scrollIntoView({ behavior: 'smooth' });
}