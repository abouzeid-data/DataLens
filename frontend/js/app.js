// Wait for pywebview API to be ready
window.addEventListener('pywebviewready', async function() {
  await init();
  await checkForResetToken();
  setInterval(checkForResetToken, 1000);
});

// State
let currentView = 'upload';
let analysisData = null; // stores {kpis, charts, insights, forecast, dataInfo, cleaningSummary, columns}
let currentReportPath = null;
let currentLogoPath = null;

function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>"']/g, ch => ({
    '&': '&amp;',
    '<': '&lt;',
    '>': '&gt;',
    '"': '&quot;',
    "'": '&#39;'
  }[ch]));
}

function escapeJsStringAttr(value) {
  return escapeHtml(JSON.stringify(String(value ?? '')));
}

function safeElementId(value) {
  return String(value ?? '').replace(/[^a-zA-Z0-9_-]/g, '_');
}

async function checkForResetToken() {
  try {
    const res = await window.pywebview.api.get_startup_token();
    const data = JSON.parse(res);
    if (data.token) {
      document.getElementById('reset-token').value = data.token;
      document.getElementById('reset-password').value = '';
      showAuthView('reset');
      navigateTo('auth');
    }
  } catch(e) { console.error(e); }
}

// Navigation
async function init() {
  const savedLang = localStorage.getItem('datalens_lang') || 'en';
  setLanguage(savedLang);

  const langBtn = document.getElementById('lang-toggle');
  if (langBtn) langBtn.textContent = savedLang === 'en' ? 'عربي' : 'EN';
  try { window.pywebview.api.set_language(savedLang); } catch (e) {}

  document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', () => {
      const view = item.getAttribute('data-view');
      navigateTo(view);
    });
  });

  setupDropZone();
  
  try {
    const res = await window.pywebview.api.check_session();
    const session = JSON.parse(res);
    if (session.logged_in) {
      if (session.is_admin) {
        document.getElementById('nav-admin').style.display = 'flex';
        loadAdminUsers();
      }
      document.getElementById('app-sidebar').style.display = 'flex';
      loadHistory();
      loadSettings();
      loadSavedDatasets();
      navigateTo('upload');
    } else {
      navigateTo('auth');
    }
  } catch (e) {
    navigateTo('auth');
  }
}

async function loadSettings() {
  try {
    const res = await window.pywebview.api.get_settings();
    const settings = JSON.parse(res);
    if (settings.logo_path) {
      currentLogoPath = settings.logo_path;
      document.getElementById('settings-logo-path').textContent = currentLogoPath;
    }
    if (settings.brand_color) {
      document.getElementById('settings-brand-color').value = settings.brand_color;
    }
  } catch(e) {}
}

async function browseLogo() {
  try {
    const result = await window.pywebview.api.open_logo_dialog();
    if (result) {
      currentLogoPath = Array.isArray(result) ? result[0] : result;
      document.getElementById('settings-logo-path').textContent = currentLogoPath;
    }
  } catch (e) {}
}

async function saveSettings() {
  const color = document.getElementById('settings-brand-color').value;
  try {
    await window.pywebview.api.save_settings(currentLogoPath, color);
    showToast('Settings saved successfully', 'success');
  } catch(e) {
    showToast('Failed to save settings', 'error');
  }
}

function navigateTo(view) {
  currentView = view;
  document.querySelectorAll('.view').forEach(el => {
    el.style.display = 'none';
  });
  const targetEl = document.getElementById(`view-${view}`);
  if (targetEl) {
    targetEl.style.display = view === 'auth' ? 'flex' : 'block';
  }
  if (view !== 'auth') {
    document.querySelectorAll('.nav-item').forEach(item => {
      item.classList.remove('active');
      if (item.getAttribute('data-view') === view) {
        item.classList.add('active');
      }
    });
  }
}

function showAuthView(viewName) {
  const views = ['login', 'register', 'forgot', 'reset'];
  views.forEach(v => {
    const el = document.getElementById(`auth-${v}-box`);
    if (el) el.style.display = 'none';
  });
  const target = document.getElementById(`auth-${viewName}-box`);
  if (target) target.style.display = 'block';
}

function showResetWithPrompt() {
  const token = prompt("Please enter the reset token from your email link:");
  if (token) {
    document.getElementById('reset-token').value = token;
    showAuthView('reset');
  }
}

async function handleLogin() {
  const user = document.getElementById('login-username').value.trim();
  const pass = document.getElementById('login-password').value.trim();
  if (!user || !pass) return showToast('Please enter username and password', 'error');
  
  showLoading(true);
  try {
    const res = await window.pywebview.api.login(user, pass);
    const data = JSON.parse(res);
    showLoading(false);
    if (data.status === 'ok') {
      const sessionRes = await window.pywebview.api.check_session();
      const session = JSON.parse(sessionRes);
      if (session.is_admin) {
        document.getElementById('nav-admin').style.display = 'flex';
        loadAdminUsers();
      }
      document.getElementById('app-sidebar').style.display = 'flex';
      loadHistory();
      loadSettings();
      loadSavedDatasets();
      navigateTo('upload');
      showToast('Logged in successfully', 'success');
    } else {
      showToast(data.error || 'Login failed', 'error');
    }
  } catch (e) {
    showLoading(false);
    showToast('Error: ' + e, 'error');
  }
}

async function handleRegister() {
  const fname = document.getElementById('reg-firstname').value.trim();
  const lname = document.getElementById('reg-lastname').value.trim();
  const email = document.getElementById('reg-email').value.trim();
  const user = document.getElementById('reg-username').value.trim();
  const pass = document.getElementById('reg-password').value.trim();
  const usecase = document.getElementById('reg-usecase').value;

  if (!user || !pass) return showToast('Please enter username and password', 'error');
  
  showLoading(true);
  try {
    const res = await window.pywebview.api.register(user, pass, fname, lname, email, usecase);
    const data = JSON.parse(res);
    showLoading(false);
    if (data.status === 'ok') {
      const sessionRes = await window.pywebview.api.check_session();
      const session = JSON.parse(sessionRes);
      if (session.is_admin) {
        document.getElementById('nav-admin').style.display = 'flex';
        loadAdminUsers();
      }
      document.getElementById('app-sidebar').style.display = 'flex';
      loadHistory();
      loadSettings();
      loadSavedDatasets();
      navigateTo('upload');
      showToast('Registered successfully', 'success');
    } else {
      showToast(data.error || 'Registration failed', 'error');
    }
  } catch (e) {
    showLoading(false);
    showToast('Error: ' + e, 'error');
  }
}

async function handleForgotPassword() {
  const email = document.getElementById('forgot-email').value.trim();
  if (!email) return showToast('Please enter your email', 'error');

  showLoading(true);
  try {
    const res = await window.pywebview.api.request_password_reset(email);
    const data = JSON.parse(res);
    showLoading(false);
    if (data.status === 'ok') {
      showToast('Reset link sent to your email!', 'success');
      showAuthView('login');
    } else {
      showToast(data.error || 'Failed to send reset link', 'error');
    }
  } catch (e) {
    showLoading(false);
    showToast('Error: ' + e, 'error');
  }
}

async function handleResetPassword() {
  const token = document.getElementById('reset-token').value;
  const newPass = document.getElementById('reset-password').value.trim();
  if (!newPass) return showToast('Please enter a new password', 'error');

  showLoading(true);
  try {
    const res = await window.pywebview.api.reset_password(token, newPass);
    const data = JSON.parse(res);
    showLoading(false);
    if (data.status === 'ok') {
      showToast('Password reset successfully! Please login.', 'success');
      showAuthView('login');
    } else {
      showToast(data.error || 'Failed to reset password', 'error');
    }
  } catch (e) {
    showLoading(false);
    showToast('Error: ' + e, 'error');
  }
}

async function logout() {
  try {
    await window.pywebview.api.logout();
    document.getElementById('app-sidebar').style.display = 'none';
    const navAdmin = document.getElementById('nav-admin');
    if (navAdmin) navAdmin.style.display = 'none';
    document.getElementById('login-username').value = '';
    document.getElementById('login-password').value = '';
    showAuthView('login');
    navigateTo('auth');
    showToast('Logged out', 'success');
  } catch(e) {}
}

async function loadAdminUsers() {
  const tbody = document.getElementById('admin-users-tbody');
  if (!tbody) return;
  try {
    const res = await window.pywebview.api.admin_get_users();
    const data = JSON.parse(res);
    if (data.error) {
      tbody.innerHTML = `<tr><td colspan="5" class="empty-state">${escapeHtml(data.error)}</td></tr>`;
      return;
    }
    tbody.innerHTML = '';
    data.forEach(u => {
      const tr = document.createElement('tr');
      const role = u.is_admin ? '<span style="color: #fbbf24; font-weight: bold;">Admin</span>' : 'User';
      
      tr.innerHTML = `
        <td>${escapeHtml(u.id)}</td>
        <td>${escapeHtml(u.username)}</td>
        <td>${role}</td>
        <td>${escapeHtml(new Date(u.created_at).toLocaleString())}</td>
        <td>
          <button class="btn btn-secondary" style="padding: 4px 8px; font-size: 12px; margin-right: 8px;" onclick="promptResetPassword(${u.id})">Reset Pass</button>
          <button class="btn btn-secondary" style="padding: 4px 8px; font-size: 12px; color: #ef4444; border-color: rgba(239, 68, 68, 0.5);" onclick="confirmDeleteUser(${u.id}, ${escapeJsStringAttr(u.username)})">Delete</button>
        </td>
      `;
      tbody.appendChild(tr);
    });
  } catch(e) {
    console.error(e);
  }
}

async function promptResetPassword(userId) {
  const newPass = prompt("Enter new password for this user:");
  if (!newPass) return;
  showLoading(true);
  try {
    const res = await window.pywebview.api.admin_reset_password_api(userId, newPass);
    const data = JSON.parse(res);
    showLoading(false);
    if (data.status === 'ok') showToast('Password reset successfully', 'success');
    else showToast(data.error, 'error');
  } catch (e) {
    showLoading(false);
    showToast('Error resetting password', 'error');
  }
}

async function confirmDeleteUser(userId, username) {
  if (!confirm(`Are you absolutely sure you want to delete user '${username}' and all their data? This cannot be undone.`)) return;
  showLoading(true);
  try {
    const res = await window.pywebview.api.admin_delete_user_api(userId);
    const data = JSON.parse(res);
    showLoading(false);
    if (data.status === 'ok') {
      showToast('User deleted successfully', 'success');
      loadAdminUsers();
    } else {
      showToast(data.error, 'error');
    }
  } catch (e) {
    showLoading(false);
    showToast('Error deleting user', 'error');
  }
}

function setupDropZone() {
  const dropZone = document.getElementById('drop-zone');
  if (!dropZone) return;

  dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('drag-over');
  });

  dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('drag-over');
  });

  dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('drag-over');
  });
}

async function browseFile() {
  try {
    const result = await window.pywebview.api.open_file_dialog();
    if (result) {
      await processFile(result);
    }
  } catch (e) {
    showToast(t('error') + ': ' + e, 'error');
  }
}

async function processFile(filePath) {
  showLoading(true);
  try {
    const result = await window.pywebview.api.upload_file(filePath);
    analysisData = JSON.parse(result);

    if (analysisData.error) {
      showToast(analysisData.error, 'error');
      showLoading(false);
      return;
    }

    navigateTo('analysis');
    renderDataPreview();
    renderCleaningSummary();
    renderDetectedColumns();
    renderFilters();
    renderAnomalies();
    renderKPIs();
    renderCharts();
    renderInsights();
    renderForecast();

    loadAIInsight();

    showLoading(false);
    showToast(t('success'), 'success');
  } catch (e) {
    showLoading(false);
    showToast(t('error') + ': ' + e, 'error');
  }
}

function renderDataPreview() {
  if (!analysisData) return;
  const info = analysisData.data_info;

  // Update metrics
  document.getElementById('metric-rows').textContent = info.rows;
  document.getElementById('metric-cols').textContent = info.columns;
  document.getElementById('metric-missing').textContent = info.missing_values;
  document.getElementById('metric-duplicates').textContent = info.duplicate_rows;

  // Render preview table
  const table = document.getElementById('preview-table');
  if (table && info.preview) {
    let html = '<thead><tr>';
    info.column_names.forEach(col => {
      html += `<th>${escapeHtml(col)}</th>`;
    });
    html += '</tr></thead><tbody>';
    info.preview.forEach(row => {
      html += '<tr>';
      info.column_names.forEach(col => {
        let val = row[col];
        if (val !== null && val !== undefined) {
          // If it looks like an ISO date (e.g., 2023-01-01T00:00:00.000Z), format it nicely
          if (typeof val === 'string' && /^\d{4}-\d{2}-\d{2}T/.test(val)) {
            val = new Date(val).toLocaleDateString(currentLang === 'ar' ? 'ar-EG' : 'en-US', { 
              year: 'numeric', month: 'short', day: 'numeric' 
            });
          }
        } else {
          val = '';
        }
        html += `<td>${escapeHtml(val)}</td>`;
      });
      html += '</tr>';
    });
    html += '</tbody>';
    table.innerHTML = html;
  }
}

function renderCleaningSummary() {
  if (!analysisData?.cleaning_summary) return;
  const container = document.getElementById('cleaning-summary');
  if (!container) return;

  let html = '';
  for (const [key, value] of Object.entries(analysisData.cleaning_summary)) {
    html += `<div class="cleaning-item">✓ ${escapeHtml(key)}: ${escapeHtml(value)}</div>`;
  }
  container.innerHTML = html || `<div class="cleaning-item">${escapeHtml(t('cleaningDone'))}</div>`;
}

function renderDetectedColumns() {
  if (!analysisData?.detected_columns) return;
  const container = document.getElementById('detected-columns');
  if (!container) return;

  const labels = {
    date_column: t('dateColumn'),
    sales_column: t('salesColumn'),
    product_column: t('productColumn'),
    quantity_column: t('quantityColumn'),
    category_column: t('categoryColumn'),
    price_column: t('priceColumn'),
  };

  let html = '';
  for (const [key, value] of Object.entries(analysisData.detected_columns)) {
    const label = labels[key] || key;
    html += `<div class="column-item"><span class="column-label">${escapeHtml(label)}</span><span class="column-value">${escapeHtml(value || t('notDetected'))}</span></div>`;
  }
  container.innerHTML = html;
}

function renderFilters() {
  const filterSection = document.getElementById('filter-section');
  const container = document.getElementById('filter-container');
  if (!filterSection || !container) return;

  if (!analysisData?.filters || Object.keys(analysisData.filters).length === 0) {
    filterSection.style.display = 'none';
    return;
  }

  filterSection.style.display = 'block';
  let html = '';
  for (const [col, values] of Object.entries(analysisData.filters)) {
    const safeId = safeElementId(col);
    html += `
      <div class="filter-item">
        <label for="filter-${safeId}">${escapeHtml(col)}</label>
        <select id="filter-${safeId}" onchange="handleFilterChange(${escapeJsStringAttr(col)}, this.value)">
          <option value="ALL">All</option>
          ${values.map(v => `<option value="${escapeHtml(v)}">${escapeHtml(v)}</option>`).join('')}
        </select>
      </div>
    `;
  }
  container.innerHTML = html;
}

async function handleFilterChange(col, value) {
  showLoading(true);
  try {
    const result = await window.pywebview.api.apply_filter(col, value);
    const newData = JSON.parse(result);
    
    if (newData.error) {
      showToast(newData.error, 'error');
      showLoading(false);
      return;
    }
    
    // Update data safely without destroying the filters themselves
    analysisData.kpis = newData.kpis;
    analysisData.charts = newData.charts;
    analysisData.insights = newData.insights;
    analysisData.forecast = newData.forecast;
    analysisData.data_info = newData.data_info;
    analysisData.anomalies = newData.anomalies;
    analysisData.ai = newData.ai;
    
    renderAnomalies();
    renderKPIs();
    renderCharts();
    renderInsights();
    renderForecast();
    loadAIInsight(); // re-fetch AI insight with filtered data
    
    showLoading(false);
  } catch (e) {
    showLoading(false);
    showToast(t('error') + ': ' + e, 'error');
  }
}

function renderAnomalies() {
  const container = document.getElementById('anomaly-container');
  if (!container) return;
  
  if (!analysisData?.anomalies || analysisData.anomalies.length === 0) {
    container.style.display = 'none';
    return;
  }
  
  container.style.display = 'block';
  let html = '';
  analysisData.anomalies.forEach(anomaly => {
    html += `
      <div class="anomaly-warning" style="background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); color: #ef4444; padding: 12px 16px; border-radius: 8px; margin-bottom: 16px; display: flex; align-items: center; gap: 12px;">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/></svg>
        <span>${escapeHtml(anomaly)}</span>
      </div>
    `;
  });
  container.innerHTML = html;
}

function renderKPIs() {
  if (!analysisData?.kpis) return;
  const container = document.getElementById('kpi-container');
  if (!container) return;

  let html = '';
  for (const [label, value] of Object.entries(analysisData.kpis)) {
    // Determine if it's a number to add formatting if necessary
    const isNum = !isNaN(parseFloat(value)) && isFinite(value);
    let displayVal = value;
    if (isNum && typeof value === 'number') {
      displayVal = value.toLocaleString(undefined, {minimumFractionDigits: 0, maximumFractionDigits: 2});
    }

    html += `
      <div class="kpi-card">
        <span class="kpi-label">${escapeHtml(label)}</span>
        <span class="kpi-value">${escapeHtml(displayVal !== null && displayVal !== undefined ? displayVal : t('noData'))}</span>
      </div>
    `;
  }
  container.innerHTML = html || `<p class="empty-state">${t('noData')}</p>`;
}


function renderCharts() {
  if (!analysisData?.charts) return;
  const container = document.getElementById('charts-container');
  if (!container) return;

  let html = '';
  for (const [name, chartHtml] of Object.entries(analysisData.charts)) {
    const fullHtml = `<!DOCTYPE html><html><head><meta charset="utf-8"><style>body{margin:0;background:transparent;overflow:hidden;}</style></head><body>${chartHtml}</body></html>`;
    const encoded = escapeHtml(fullHtml);
    html += `<div class="chart-card"><h3>${escapeHtml(name)}</h3><div class="chart-frame"><iframe sandbox="allow-scripts" srcdoc="${encoded}" style="width:100%;height:350px;border:none;" scrolling="no"></iframe></div></div>`;
  }
  container.innerHTML = html || '<p class="empty-state">' + t('noData') + '</p>';
}

function renderInsights() {
  if (!analysisData?.insights) return;
  const container = document.getElementById('insights-container');
  if (!container) return;

  let html = '';
  analysisData.insights.forEach(insight => {
    html += `<div class="insight-item"><span class="insight-bullet">•</span><span>${escapeHtml(insight)}</span></div>`;
  });
  container.innerHTML = html || '<p class="empty-state">' + t('noData') + '</p>';
}

function renderForecast() {
  const container = document.getElementById('forecast-container');
  if (!container) return;

  if (analysisData?.forecast) {
    const fullHtml = `<!DOCTYPE html><html><head><meta charset="utf-8"><style>body{margin:0;background:transparent;overflow:hidden;}</style></head><body>${analysisData.forecast}</body></html>`;
    const encoded = escapeHtml(fullHtml);
    container.innerHTML = `<div class="chart-frame"><iframe sandbox="allow-scripts" srcdoc="${encoded}" style="width:100%;height:350px;border:none;" scrolling="no"></iframe></div>`;
  } else {
    container.innerHTML = `<p class="empty-state">${t('noForecast')}</p>`;
  }
}

async function sendChatMessage() {
  const inputEl = document.getElementById('chat-input');
  const historyEl = document.getElementById('chat-history');
  if (!inputEl || !historyEl) return;
  
  const query = inputEl.value.trim();
  if (!query) return;
  
  // Clear empty state if present
  const emptyState = historyEl.querySelector('.empty-state');
  if (emptyState) emptyState.remove();
  
  // Add user message
  historyEl.innerHTML += `
    <div style="display: flex; justify-content: flex-end; margin-bottom: 12px;">
      <div style="background: #0ea5e9; color: white; padding: 10px 14px; border-radius: 12px 12px 0 12px; max-width: 80%; font-size: 14px;">
        ${escapeHtml(query)}
      </div>
    </div>
  `;
  
  inputEl.value = '';
  historyEl.scrollTop = historyEl.scrollHeight;
  
  // Add loading
  const loadingId = 'loading-' + Date.now();
  historyEl.innerHTML += `
    <div id="${loadingId}" style="display: flex; justify-content: flex-start; margin-bottom: 12px;">
      <div style="background: #1e293b; color: #cbd5e1; padding: 10px 14px; border-radius: 12px 12px 12px 0; max-width: 80%; font-size: 14px; display: flex; gap: 8px; align-items: center;">
        <div class="spinner-small" style="width: 14px; height: 14px;"></div> Thinking...
      </div>
    </div>
  `;
  historyEl.scrollTop = historyEl.scrollHeight;
  
  try {
    const result = await window.pywebview.api.ask_chat_question(query);
    document.getElementById(loadingId).remove();
    
    // Add AI message
    historyEl.innerHTML += `
      <div style="display: flex; justify-content: flex-start; margin-bottom: 12px;">
        <div style="background: #1e293b; color: #f8fafc; padding: 10px 14px; border-radius: 12px 12px 12px 0; max-width: 80%; font-size: 14px;">
          ${escapeHtml(result).replace(/\n/g, '<br>')}
        </div>
      </div>
    `;
    historyEl.scrollTop = historyEl.scrollHeight;
  } catch (e) {
    document.getElementById(loadingId).remove();
    historyEl.innerHTML += `
      <div style="display: flex; justify-content: flex-start; margin-bottom: 12px;">
        <div style="background: rgba(239, 68, 68, 0.1); color: #ef4444; border: 1px solid rgba(239,68,68,0.3); padding: 10px 14px; border-radius: 12px 12px 12px 0; max-width: 80%; font-size: 14px;">
          Error connecting to AI.
        </div>
      </div>
    `;
    historyEl.scrollTop = historyEl.scrollHeight;
  }
}

async function loadAIInsight() {
  const container = document.getElementById('ai-insight-container');
  if (!container) return;

  const isOffline = analysisData?.ai?.mode === 'offline';
  container.innerHTML = isOffline
    ? `<div class="loading-inline"><span>${t('offlineMode')}</span></div>`
    : `<div class="loading-inline"><div class="spinner-small"></div><span>${t('aiLoading')}</span></div>`;

  try {
    const result = await window.pywebview.api.get_ai_insight();
    // Convert markdown-like text to HTML paragraphs
    const html = result.split('\n').filter(line => line.trim()).map(line => {
      // Bold text replacement
      line = escapeHtml(line).replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
      
      if (line.startsWith('#')) {
        return `<h4>${line.replace(/^#+\s*/, '')}</h4>`;
      }
      if (line.startsWith('- ') || line.startsWith('* ')) {
        return `<li>${line.substring(2)}</li>`;
      }
      if (line.match(/^\d+\./)) {
        return `<li>${line.replace(/^\d+\.\s*/, '')}</li>`;
      }
      return `<p>${line}</p>`;
    }).join('');
    const modeBadge = isOffline ? `<div class="offline-badge">${t('offlineMode')}</div>` : '';
    container.innerHTML = modeBadge + html;
  } catch (e) {
    container.innerHTML = `<p class="error-text">${escapeHtml(t('error'))}: ${escapeHtml(e)}</p>`;
  }
}

// Reports
async function generateReport() {
  const btn = document.getElementById('btn-generate-report');
  if (btn) btn.disabled = true;

  const status = document.getElementById('report-status');
  if (status) status.textContent = t('reportGenerating');

  try {
    const result = await window.pywebview.api.generate_report();
    const data = JSON.parse(result);
    if (data.path) {
      currentReportPath = data.path;

      const previewContainer = document.getElementById('report-preview-container');
      const previewFrame = document.getElementById('report-preview-frame');
      const previewPath = document.getElementById('report-preview-path');
      if (previewContainer && previewFrame && data.preview_html) {
        previewFrame.removeAttribute('src');
        previewFrame.srcdoc = data.preview_html;
        previewContainer.style.display = 'block';
      }
      if (previewPath) previewPath.textContent = data.path;

      if (status) status.innerHTML = `<span class="success-text">✓ ${escapeHtml(t('success'))}</span>`;
      const downloadBtn = document.getElementById('btn-download-report');
      if (downloadBtn) {
        downloadBtn.style.display = 'inline-flex';
        downloadBtn.onclick = () => window.pywebview.api.open_report(currentReportPath);
      }
    } else {
      if (status) status.innerHTML = `<span class="error-text">${escapeHtml(data.error || t('error'))}</span>`;
    }
  } catch (e) {
    if (status) status.innerHTML = `<span class="error-text">${escapeHtml(t('error'))}: ${escapeHtml(e)}</span>`;
  }
  if (btn) btn.disabled = false;
}

// History
async function loadHistory() {
  try {
    const result = await window.pywebview.api.get_history();
    const history = JSON.parse(result);
    const container = document.getElementById('history-table-body');
    if (!container) return;

    if (!history || history.length === 0) {
      container.innerHTML = `<tr><td colspan="5" class="empty-state">${t('historyEmpty')}</td></tr>`;
      return;
    }

    container.innerHTML = '';
    history.forEach(h => {
      const tr = document.createElement('tr');
      const revenue = h[6] !== null ? '$' + Number(h[6]).toLocaleString() : t('noData');
      tr.innerHTML = `
        <td>${escapeHtml(h[2])}</td>
        <td>${escapeHtml(new Date(h[3]).toLocaleString())}</td>
        <td>${escapeHtml(h[4])}</td>
        <td>${escapeHtml(h[5])}</td>
        <td>${escapeHtml(revenue)}</td>
      `;
      container.appendChild(tr);
    });
  } catch (e) {
    console.error("History load error:", e);
  }
}

// ---- Saved Datasets ----
async function loadSavedDatasets() {
  const container = document.getElementById('saved-datasets-list');
  if (!container) return;
  try {
    const res = await window.pywebview.api.get_saved_datasets();
    const datasets = JSON.parse(res);
    if (!datasets || datasets.length === 0) {
      container.innerHTML = '<p style="color: #64748b; text-align: center; margin-top: 40px;">No saved datasets yet.</p>';
      return;
    }
    
    container.innerHTML = '';
    datasets.forEach(d => {
      const el = document.createElement('div');
      el.style.cssText = 'background: rgba(15, 23, 42, 0.6); padding: 12px; border-radius: 8px; border: 1px solid #334155; display: flex; justify-content: space-between; align-items: center;';
      
      const info = document.createElement('div');
      info.innerHTML = `<strong style="color: #f8fafc; font-size: 14px;">${escapeHtml(d.name)}</strong><br/><span style="color: #64748b; font-size: 12px;">${escapeHtml(new Date(d.created_at).toLocaleDateString())}</span>`;
      
      const actions = document.createElement('div');
      actions.style.display = 'flex';
      actions.style.gap = '8px';
      
      const loadBtn = document.createElement('button');
      loadBtn.className = 'btn btn-primary';
      loadBtn.style.padding = '6px 12px';
      loadBtn.style.fontSize = '12px';
      loadBtn.innerText = 'Load';
      loadBtn.onclick = async () => {
        showLoading(true);
        try {
          const res = await window.pywebview.api.load_saved_dataset(d.id);
          analysisData = JSON.parse(res);
          showLoading(false);
          
          if (analysisData.error) {
            showToast(analysisData.error, 'error');
            return;
          }
          
          navigateTo('analysis');
          renderDataPreview();
          renderCleaningSummary();
          renderDetectedColumns();
          renderFilters();
          renderAnomalies();
          renderKPIs();
          renderCharts();
          renderInsights();
          renderForecast();
          loadAIInsight();
          
        } catch (e) {
          showLoading(false);
          showToast('Error loading dataset', 'error');
        }
      };
      
      const delBtn = document.createElement('button');
      delBtn.className = 'btn btn-secondary';
      delBtn.style.padding = '6px 12px';
      delBtn.style.fontSize = '12px';
      delBtn.style.color = '#ef4444';
      delBtn.style.borderColor = 'rgba(239, 68, 68, 0.5)';
      delBtn.innerText = 'Delete';
      delBtn.onclick = async () => {
        if (!confirm(`Delete saved dataset "${d.name}"?`)) return;
        try {
          await window.pywebview.api.delete_saved_dataset(d.id);
          loadSavedDatasets();
        } catch(e) {}
      };
      
      actions.appendChild(loadBtn);
      actions.appendChild(delBtn);
      
      el.appendChild(info);
      el.appendChild(actions);
      container.appendChild(el);
    });
  } catch(e) {
    console.error("Failed to load saved datasets", e);
  }
}

async function promptSaveDataset() {
  const name = prompt("Enter a friendly name for this dataset (e.g. 'Daily Sales'):");
  if (!name) return;
  
  showLoading(true);
  try {
    const res = await window.pywebview.api.save_current_dataset(name);
    const data = JSON.parse(res);
    showLoading(false);
    if (data.status === 'ok') {
      showToast('Dataset saved successfully!', 'success');
      loadSavedDatasets();
    } else {
      showToast(data.error || 'Failed to save dataset', 'error');
    }
  } catch (e) {
    showLoading(false);
    showToast('Error saving dataset', 'error');
  }
}

// Toast notifications
function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  container.appendChild(toast);

  setTimeout(() => toast.classList.add('show'), 10);
  setTimeout(() => {
    toast.classList.remove('show');
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}

// Loading overlay
function showLoading(show) {
  const overlay = document.getElementById('loading-overlay');
  if (overlay) {
    overlay.style.display = show ? 'flex' : 'none';
  }
}

// Language toggle
function toggleLanguage() {
  const newLang = currentLang === 'en' ? 'ar' : 'en';
  setLanguage(newLang);
  const langBtn = document.getElementById('lang-toggle');
  if (langBtn) langBtn.textContent = newLang === 'en' ? 'عربي' : 'EN';
  // Sync language to Python backend for report generation
  try {
    window.pywebview.api.set_language(newLang);
  } catch (e) { /* ignore if API not ready */ }
}

