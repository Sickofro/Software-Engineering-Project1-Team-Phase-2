// API Configuration
// Use AWS deployed API
const API_BASE_URL = 'https://zqux1td8ae.execute-api.us-east-1.amazonaws.com';

// DOM Elements
const loadingOverlay = document.getElementById('loadingOverlay');
const apiStatus = document.getElementById('apiStatus');

// Tab Management
document.querySelectorAll('.tab-button').forEach(button => {
    button.addEventListener('click', () => {
        const tabId = button.dataset.tab;
        
        // Update button states
        document.querySelectorAll('.tab-button').forEach(btn => {
            btn.classList.remove('active');
        });
        button.classList.add('active');
        
        // Update content visibility
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        document.getElementById(tabId).classList.add('active');
    });
});

// Utility Functions
function showLoading() {
    loadingOverlay.classList.add('show');
}

function hideLoading() {
    loadingOverlay.classList.remove('show');
}

function showResult(containerId) {
    const container = document.getElementById(containerId);
    container.classList.add('show');
}

function clearResult(containerId) {
    const container = document.getElementById(containerId);
    container.innerHTML = '';
    container.classList.remove('show');
}

function displayError(containerId, error) {
    const container = document.getElementById(containerId);
    container.innerHTML = `
        <div class="error-message">
            <strong>Error</strong>
            ${error}
        </div>
    `;
    showResult(containerId);
}

function getMetricClass(value) {
    if (value >= 0.7) return 'high';
    if (value >= 0.4) return 'medium';
    return 'low';
}

function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// API Status Check
async function checkAPIStatus() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        if (response.ok) {
            apiStatus.classList.add('online');
            apiStatus.classList.remove('offline');
        } else {
            apiStatus.classList.add('offline');
            apiStatus.classList.remove('online');
        }
    } catch (error) {
        apiStatus.classList.add('offline');
        apiStatus.classList.remove('online');
    }
}

// Rating Form Handler
document.getElementById('ratingForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const url = document.getElementById('ratingUrl').value.trim();
    clearResult('ratingResult');
    showLoading();
    
    try {
        // Step 1: Create artifact first
        const createResponse = await fetch(`${API_BASE_URL}/artifact/model`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Authorization': 'frontend-user'
            },
            body: JSON.stringify({ url })
        });
        
        if (!createResponse.ok) {
            const errorData = await createResponse.json();
            throw new Error(errorData.detail || 'Failed to create artifact');
        }
        
        const artifact = await createResponse.json();
        const artifactId = artifact.metadata.id;
        
        // Step 2: Get rating for the artifact
        const ratingResponse = await fetch(`${API_BASE_URL}/artifact/model/${artifactId}/rate`, {
            method: 'GET',
            headers: {
                'X-Authorization': 'frontend-user'
            }
        });
        
        if (!ratingResponse.ok) {
            const errorData = await ratingResponse.json();
            throw new Error(errorData.detail || 'Failed to calculate rating');
        }
        
        const data = await ratingResponse.json();
        displayRatingResult(data);
    } catch (error) {
        displayError('ratingResult', error.message);
    } finally {
        hideLoading();
    }
});

function displayRatingResult(data) {
    const container = document.getElementById('ratingResult');
    
    // Build metrics from all individual scores
    const metrics = {
        'Net Score': data.net_score,
        'Ramp Up Time': data.ramp_up_time,
        'Bus Factor': data.bus_factor,
        'Performance Claims': data.performance_claims,
        'License': data.license,
        'Dataset & Code': data.dataset_and_code_score,
        'Dataset Quality': data.dataset_quality,
        'Code Quality': data.code_quality,
        'Reproducibility': data.reproducibility,
        'Reviewedness': data.reviewedness,
        'Tree Score': data.tree_score
    };
    
    const metricsHtml = Object.entries(metrics)
        .filter(([_, value]) => value !== undefined)
        .map(([name, value]) => `
            <div class="metric-item">
                <div class="metric-name">${name.toUpperCase()}</div>
                <div class="metric-value ${getMetricClass(value)}">${value.toFixed(3)}</div>
            </div>
        `).join('');
    
    // Size scores
    const sizeScoresHtml = data.size_score ? `
        <div class="card">
            <div class="card-header">Size Compatibility Scores</div>
            <div class="metric-grid">
                <div class="metric-item">
                    <div class="metric-name">RASPBERRY PI</div>
                    <div class="metric-value ${getMetricClass(data.size_score.raspberry_pi)}">${data.size_score.raspberry_pi.toFixed(3)}</div>
                </div>
                <div class="metric-item">
                    <div class="metric-name">JETSON NANO</div>
                    <div class="metric-value ${getMetricClass(data.size_score.jetson_nano)}">${data.size_score.jetson_nano.toFixed(3)}</div>
                </div>
                <div class="metric-item">
                    <div class="metric-name">DESKTOP PC</div>
                    <div class="metric-value ${getMetricClass(data.size_score.desktop_pc)}">${data.size_score.desktop_pc.toFixed(3)}</div>
                </div>
                <div class="metric-item">
                    <div class="metric-name">AWS SERVER</div>
                    <div class="metric-value ${getMetricClass(data.size_score.aws_server)}">${data.size_score.aws_server.toFixed(3)}</div>
                </div>
            </div>
        </div>
    ` : '';
    
    container.innerHTML = `
        <div class="net-score">
            <div class="net-score-value">${data.net_score.toFixed(3)}</div>
            <div class="net-score-label">Overall Net Score</div>
        </div>
        
        <div class="card">
            <div class="card-header">Model: ${data.name}</div>
            <p><strong>Category:</strong> ${data.category}</p>
        </div>
        
        <div class="card">
            <div class="card-header">Detailed Metrics</div>
            <div class="metric-grid">
                ${metricsHtml}
            </div>
        </div>
        
        ${sizeScoresHtml}
    `;
    
    showResult('ratingResult');
}

// Cost Form Handler
document.getElementById('costForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const url = document.getElementById('costUrl').value.trim();
    clearResult('costResult');
    showLoading();
    
    try {
        // Step 1: Create artifact first
        const createResponse = await fetch(`${API_BASE_URL}/artifact/model`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Authorization': 'frontend-user'
            },
            body: JSON.stringify({ url })
        });
        
        if (!createResponse.ok) {
            const errorData = await createResponse.json();
            throw new Error(errorData.detail || 'Failed to create artifact');
        }
        
        const artifact = await createResponse.json();
        const artifactId = artifact.metadata.id;
        const artifactType = artifact.metadata.type;
        
        // Step 2: Get cost for the artifact
        const costResponse = await fetch(`${API_BASE_URL}/artifact/${artifactType}/${artifactId}/cost`, {
            method: 'GET',
            headers: {
                'X-Authorization': 'frontend-user'
            }
        });
        
        if (!costResponse.ok) {
            const errorData = await costResponse.json();
            throw new Error(errorData.detail || 'Failed to calculate cost');
        }
        
        const data = await costResponse.json();
        displayCostResult(data, url);
    } catch (error) {
        displayError('costResult', error.message);
    } finally {
        hideLoading();
    }
});

function displayCostResult(data, url) {
    const container = document.getElementById('costResult');
    
    // Extract cost from response format: {id: {total_cost: X}}
    const artifactId = Object.keys(data)[0];
    const costData = data[artifactId] || {};
    const totalCostMB = costData.total_cost || 0;
    
    container.innerHTML = `
        <div class="card">
            <div class="card-header">Cost Analysis</div>
            <div class="cost-info">
                <div class="cost-item">
                    <div class="cost-value">${totalCostMB.toFixed(2)} MB</div>
                    <div class="cost-label">Total Size</div>
                </div>
                <div class="cost-item">
                    <div class="cost-value">${artifactId}</div>
                    <div class="cost-label">Artifact ID</div>
                </div>
            </div>
        </div>
        
        <div class="card">
            <div class="card-header">Details</div>
            <p><strong>URL:</strong> ${url}</p>
        </div>
    `;
    
    showResult('costResult');
}

// Lineage Form Handler
document.getElementById('lineageForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const url = document.getElementById('lineageUrl').value.trim();
    clearResult('lineageResult');
    showLoading();
    
    try {
        // Step 1: Create artifact first
        const createResponse = await fetch(`${API_BASE_URL}/artifact/model`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Authorization': 'frontend-user'
            },
            body: JSON.stringify({ url })
        });
        
        if (!createResponse.ok) {
            const errorData = await createResponse.json();
            throw new Error(errorData.detail || 'Failed to create artifact');
        }
        
        const artifact = await createResponse.json();
        const artifactId = artifact.metadata.id;
        
        // Step 2: Get lineage for the artifact
        const lineageResponse = await fetch(`${API_BASE_URL}/artifact/model/${artifactId}/lineage`, {
            method: 'GET',
            headers: {
                'X-Authorization': 'frontend-user'
            }
        });
        
        if (!lineageResponse.ok) {
            const errorData = await lineageResponse.json();
            throw new Error(errorData.detail || 'Failed to extract lineage');
        }
        
        const data = await lineageResponse.json();
        displayLineageResult(data, url);
    } catch (error) {
        displayError('lineageResult', error.message);
    } finally {
        hideLoading();
    }
});

function displayLineageResult(data, url) {
    const container = document.getElementById('lineageResult');
    
    const nodesHtml = data.nodes && data.nodes.length > 0 ? data.nodes.map(node => `
        <div class="node-item">
            <span class="node-type ${node.type || 'model'}">${node.type || 'model'}</span>
            <span><strong>${node.name}</strong></span>
            ${node.url ? `<a href="${node.url}" target="_blank" style="margin-left: auto;">🔗</a>` : ''}
        </div>
    `).join('') : '<p>No nodes found</p>';
    
    const edgesHtml = data.edges && data.edges.length > 0 ? data.edges.map(edge => `
        <div class="edge-item">
            <span class="edge-type">${edge.relationship || 'depends_on'}</span>
            <span>${edge.source} → ${edge.target}</span>
        </div>
    `).join('') : '<p>No relationships found</p>';
    
    container.innerHTML = `
        <div class="card">
            <div class="card-header">Dependency Graph</div>
            <p><strong>Nodes:</strong> ${data.nodes ? data.nodes.length : 0} | <strong>Edges:</strong> ${data.edges ? data.edges.length : 0}</p>
        </div>
        
        <div class="lineage-container">
            <div class="lineage-nodes">
                <h3 style="margin-bottom: 1rem;">Nodes</h3>
                ${nodesHtml}
            </div>
            
            <div class="lineage-edges">
                <h3 style="margin-bottom: 1rem;">Relationships</h3>
                ${edgesHtml}
            </div>
        </div>
        
        <div class="card">
            <div class="card-header">Artifact Information</div>
            <p><strong>Model:</strong> ${data.model_name || 'N/A'}</p>
            <p><strong>URL:</strong> ${url}</p>
        </div>
    `;
    
    showResult('lineageResult');
}

// License Form Handler
document.getElementById('licenseForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const artifactUrl = document.getElementById('licenseArtifactUrl').value.trim();
    const repoUrl = document.getElementById('licenseRepoUrl').value.trim();
    clearResult('licenseResult');
    showLoading();
    
    try {
        // Step 1: Create artifact first
        const createResponse = await fetch(`${API_BASE_URL}/artifact/model`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Authorization': 'frontend-user'
            },
            body: JSON.stringify({ url: artifactUrl })
        });
        
        if (!createResponse.ok) {
            const errorData = await createResponse.json();
            throw new Error(errorData.detail || 'Failed to create artifact');
        }
        
        const artifact = await createResponse.json();
        const artifactId = artifact.metadata.id;
        
        // Step 2: Check license compatibility
        const licenseResponse = await fetch(`${API_BASE_URL}/artifact/model/${artifactId}/license-check`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Authorization': 'frontend-user'
            },
            body: JSON.stringify({ repository_url: repoUrl })
        });
        
        if (!licenseResponse.ok) {
            const errorData = await licenseResponse.json();
            throw new Error(errorData.detail || 'Failed to check license compatibility');
        }
        
        const data = await licenseResponse.json();
        displayLicenseResult(data, artifactUrl, repoUrl);
    } catch (error) {
        displayError('licenseResult', error.message);
    } finally {
        hideLoading();
    }
});

function displayLicenseResult(data, artifactUrl, repoUrl) {
    const container = document.getElementById('licenseResult');
    
    const compatibilityClass = data.compatible ? 'compatible' : 
                               (data.model_license === 'unknown' || data.repository_license === 'unknown') ? 'unknown' : 
                               'incompatible';
    
    const statusText = data.compatible ? '✓ Compatible' : 
                      (data.model_license === 'unknown' || data.repository_license === 'unknown') ? '? Unknown' : 
                      '✗ Incompatible';
    
    container.innerHTML = `
        <div class="license-result ${compatibilityClass}">
            <div class="license-status ${compatibilityClass}">${statusText}</div>
            
            <div class="license-details">
                <div class="license-info">
                    <div class="license-info-label">Artifact License</div>
                    <div class="license-info-value">${data.model_license || data.artifact_license || 'Unknown'}</div>
                </div>
                <div class="license-info">
                    <div class="license-info-label">Repository License</div>
                    <div class="license-info-value">${data.repository_license || 'Unknown'}</div>
                </div>
            </div>
            
            ${data.explanation ? `
                <div style="margin-top: 1rem; padding: 1rem; background: white; border-radius: 6px;">
                    <strong>Explanation:</strong> ${data.explanation}
                </div>
            ` : ''}
        </div>
        
        <div class="card">
            <div class="card-header">Checked URLs</div>
            <p><strong>Artifact:</strong> ${artifactUrl}</p>
            <p><strong>Repository:</strong> ${repoUrl}</p>
        </div>
    `;
    
    showResult('licenseResult');
}

// Initialize
checkAPIStatus();
setInterval(checkAPIStatus, 30000); // Check every 30 seconds
