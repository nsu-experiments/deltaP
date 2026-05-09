// Global state
let pyodide = null;
let currentFile = null;
let fileSystem = {};
let zoomLevel = 100;
let isResizing = false;
let currentResizer = null;
let editor = null; 
let currentModule = null;

// Initialize on load
document.addEventListener('DOMContentLoaded', async () => {
    initCodeEditor();
    await initPyodide();
    await loadFileTree();
    setupEventListeners();
    setupResizers();
    setupZoom();

        // document.querySelector('[data-tab="charts"]').click();

});
// Connect to file watcher
const eventSource = new EventSource('/api/watch-projects');

eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log('File system change:', data);
    
    // Reload file tree
    loadFileTree();
};

eventSource.onerror = (error) => {
    console.error('SSE error:', error);
};
// Define custom .dp syntax mode
CodeMirror.defineMode("deltap", function() {
    return {
        token: function(stream, state) {
            // Comments first (highest priority)
            if (stream.match(/\/\/.*/)) {
                return "comment";
            }
            if (stream.match(/\/\*/)) {
                state.inComment = true;
                return "comment";
            }
            if (state.inComment) {
                if (stream.match(/.*?\*\//)) {
                    state.inComment = false;
                }
                return "comment";
            }
            
            // Keywords
            if (stream.match(/\b(sp|dp|decision|simulation|and|or|not|imply)\b/)) {
                return "keyword";
            }
            
            // Decorators (@dpSem, @spSem)
            if (stream.match(/@\w+/)) {
                return "meta";
            }
            
            // Constants (lowercase identifiers followed by :=)
            if (stream.match(/\b[a-z_][a-z0-9_]*(?=\s*:=)/)) {
                return "def"; // Constants in orange/yellow
            }
            
            // Type/Constructor names (Capitalized identifiers)
            if (stream.match(/\b[A-Z][a-zA-Z0-9_]*/)) {
                return "variable-3"; // Types in green/cyan
            }
            
            // Numbers (including floats)
            if (stream.match(/\b\d+\.?\d*\b/)) {
                return "number";
            }
            
            // Strings
            if (stream.match(/"(?:[^\\]|\\.)*?"/)) {
                return "string";
            }
            if (stream.match(/'(?:[^\\]|\\.)*?'/)) {
                return "string";
            }
            
            // Predicate/function names (before parentheses)
            if (stream.match(/\b[a-z_][a-z0-9_]*(?=\s*\()/i)) {
                return "variable-2";
            }
            
            // Operators
            if (stream.match(/(:=|[+\-*/%=<>!&|])/)) {
                return "operator";
            }
            
            stream.next();
            return null;
        },
        startState: function() {
            return { inComment: false };
        }
    };
});
function initCodeEditor() {
    editor = CodeMirror(document.getElementById('code-editor'), {
        mode: 'deltap',
        theme: 'monokai',
        lineNumbers: true,
        lineWrapping: false,
        indentUnit: 4,
        tabSize: 4
    });
    editor.setSize('100%', '100%');
}
// Initialize Pyodide
async function initPyodide() {
    log('Loading Python environment...', 'info');
    try {
        pyodide = await loadPyodide();
        await pyodide.loadPackage(['numpy', 'pandas']);
        log('Python environment ready', 'success');
    } catch (error) {
        log(`Failed to load Python: ${error.message}`, 'error');
    }
}

// Load file tree dynamically from projects folder
async function loadFileTree() {
    const treeContent = document.getElementById('tree-content');
    
    try {
        // Fetch project structure from backend
        const response = await fetch('/api/list-projects');
        const projects = await response.json();
        
        treeContent.innerHTML = renderTree(projects);
    } catch (error) {
        log('Failed to load projects. Using local examples.', 'error');
        // Fallback to scanning local structure
        treeContent.innerHTML = await scanLocalProjects();
    }
}
async function scanLocalProjects() {
    try {
        const response = await fetch('/api/scan-workspace');
        const structure = await response.json();
        return renderTree(structure);
    } catch {
        return '<div class="tree-file">No projects found. Run "dp init" in web/projects/</div>';
    }
}

function renderTree(obj, path = '', indent = 0) {
    let html = '';
    for (const [key, value] of Object.entries(obj)) {
        const indentStyle = `padding-left: ${indent * 1.5}rem`;
        
        if (key === 'files' && Array.isArray(value)) {
            // Files array
            value.forEach(file => {
                const fullPath = `${path}${file}`;
                html += `<div class="tree-file" data-path="${fullPath}" style="${indentStyle}">${file}</div>`;
            });
        } else if (typeof value === 'object' && value !== null) {
            // Folder - make it collapsible
            const folderId = `folder-${path.replace(/\//g, '-')}${key}`;
            html += `
                <div class="tree-folder" data-folder-id="${folderId}" style="${indentStyle}">
                    <span class="folder-icon">▶</span> ${key}
                </div>
                <div class="folder-content" id="${folderId}" style="display: none;">
                    ${renderTree(value, `${path}${key}/`, indent + 1)}
                </div>
            `;
        }
    }
    return html;
}

// Event listeners
function setupEventListeners() {
    // File selection AND folder expand/collapse
    document.getElementById('tree-content').addEventListener('click', async (e) => {
        // Handle folder clicks
        if (e.target.classList.contains('tree-folder') || e.target.closest('.tree-folder')) {
            const folder = e.target.classList.contains('tree-folder') ? e.target : e.target.closest('.tree-folder');
            const folderId = folder.dataset.folderId;
            const content = document.getElementById(folderId);
            const icon = folder.querySelector('.folder-icon');
            
            // Extract module name from folder ID (e.g., "folder--logistics" -> "logistics")
            const folderName = folderId.replace('folder--', '').replace(/-/g, '/').split('/')[0];
            
            if (content.style.display === 'none') {
                content.style.display = 'block';
                icon.textContent = '▼';
                // Set current module when opening root-level folder
                if (!folderName.includes('/')) {
                    currentModule = folderName;
                    updatePrompt();
                }
            } else {
                content.style.display = 'none';
                icon.textContent = '▶';
                // Clear module context if closing and it was the current one
                if (folderName === currentModule) {
                    currentModule = null;
                    updatePrompt();
                }
            }
        }
        // Handle file clicks
        if (e.target.classList.contains('tree-file')) {
            const filePath = e.target.dataset.path;
            
            // Check if it's a CSV file
            if (filePath.endsWith('.csv')) {
                await loadAndVisualizeCSV(filePath);
                // Switch to charts tab
                document.querySelector('[data-tab="charts"]').click();
            } else {
                await loadFile(filePath);
            }
            
            // Update active state
            document.querySelectorAll('.tree-file').forEach(f => f.classList.remove('active'));
            e.target.classList.add('active');
        }
    });

    // Run button
    document.getElementById('run-btn').addEventListener('click', runCode);

    // Tabs
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', () => {
            const targetTab = tab.dataset.tab;
            
            // Update active tab
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            
            // Update active content
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            document.getElementById(`${targetTab}-view`).classList.add('active');
        });
    });
    // Terminal input
    const terminalInput = document.getElementById('terminal-input');
    if (terminalInput) {
        terminalInput.addEventListener('keydown', async (e) => {
            if (e.key === 'Enter') {
                const command = e.target.value.trim();
                if (command) {
                    await executeTerminalCommand(command);
                    e.target.value = '';
                }
            }
        });
    }
}
function updatePrompt() {
    const prompt = document.querySelector('.prompt');
    if (currentModule) {
        prompt.textContent = `Δp/${currentModule}> `;
    } else {
        prompt.textContent = 'Δp> ';
    }
}
async function executeTerminalCommand(command) {
    const terminalOutput = document.getElementById('terminal-output');
    
    // Echo command with current context
    const promptText = currentModule ? `Δp/${currentModule}> ` : 'Δp> '; 
    const cmdLine = document.createElement('div');
    cmdLine.className = 'terminal-line command';
    cmdLine.textContent = `${promptText}${command}`; 
    terminalOutput.appendChild(cmdLine);
    
    // Parse command - handle 'dp' prefix or direct command
    let parts = command.trim().split(/\s+/);
    
    // Remove 'dp' prefix if present
    if (parts[0] === 'dp' || parts[0] === 'deltap') {
        parts = parts.slice(1);
    }
    
    const cmd = parts[0];
    const args = parts.slice(1);
    
    const output = document.createElement('div');
    
    // Handle commands matching actual CLI
    switch(cmd) {
        case '--help':
        case 'help':
        case '-h':
            output.className = 'terminal-line output';
            output.innerHTML = `ΔP - Probabilistic Programming Language

Usage: dp [COMMAND] [OPTIONS]

Commands:
  init [name]              Initialize new ΔP project
  add [type] [name]        Add module (generic/logistics)
  run [mode] [module]      Run decision/simulation
  populate [module]        Populate database
  list                     List installed modules
  install [package]        Install dp package
  sync                     Sync with dplib
  
Options:
  --help, -h              Show this help
  --version, -v           Show version`;
            break;
        case 'init':
            const projectName = args[0] || 'my-project';
            output.className = 'terminal-line output';
            output.textContent = `Initializing project '${projectName}'...
        Note: 'dp init' creates a new project directory.
        In the web playground, projects are virtual.
        Use the file tree to navigate existing examples.`;
        break;    
        case 'list':
        case 'ls':
            output.className = 'terminal-line output';
            output.textContent = `Modules in examples:
  logistics/ru_ch_bioethanol
    - config.dp
    - populate.dp
    - decision.dp
    - simulation.dp`;
            break;
            
        case 'run':
            const mode = args[0];
            let module = args[1] || currentModule;
            
            if (!module) {
                output.className = 'terminal-line error';
                output.textContent = 'No module specified. Use: dp run <mode> <module> or cd to a module first';
                break;
            }
            
            await runDeltaP(mode, module, output);
            break;
            
        case 'populate':
            let popModule = args[0] || currentModule;
            
            if (!popModule) {
                output.className = 'terminal-line error';
                output.textContent = 'No module specified. Use: dp populate <module> or cd to a module first';
                break;
            }
            
            await runDeltaP('populate', popModule, output);
            break;
            
        case '--version':
        case '-v':
            output.className = 'terminal-line output';
            output.textContent = 'ΔP v0.1.0 (web playground)';
            break;
        case 'cd':
            const targetModule = args[0];
            if (!targetModule || targetModule === '..') {
                currentModule = null;
                updatePrompt();
                output.className = 'terminal-line output';
                output.textContent = 'Cleared module context';
            } else {
                // Verify module exists
                const response = await fetch('/api/list-projects');
                const projects = await response.json();
                
                if (projects[targetModule]) {
                    currentModule = targetModule;
                    updatePrompt();
                    output.className = 'terminal-line output';
                    output.textContent = `Changed to module: ${targetModule}`;
                } else {
                    output.className = 'terminal-line error';
                    output.textContent = `Module '${targetModule}' not found`;
                }
            }
            break;
            
        default:
            output.className = 'terminal-line error';
            output.textContent = `dp: '${cmd}' is not a dp command. See 'dp --help'.`;
    }
    
    terminalOutput.appendChild(output);
    terminalOutput.scrollTop = terminalOutput.scrollHeight;
}

// Execute actual ΔP code
async function runDeltaP(mode, module, outputElement) {
    outputElement.className = 'terminal-line output';
    outputElement.textContent = `Running ${mode} for module ${module}...\n`;
    
    try {
        const response = await fetch('/api/run-deltap', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                mode: mode,
                module: module
            })
        });
        
        const result = await response.json();
        
        console.log('Backend response:', result);
        
        if (response.ok) {
            outputElement.textContent += '\n--- Output ---\n';
            outputElement.textContent += result.output || '(no output)';
            
            if (result.error) {
                outputElement.textContent += '\n\n--- Errors ---\n';
                outputElement.textContent += result.error;
            }
            
            outputElement.textContent += `\n\nExit code: ${result.code}`;
            
            // If there are results, show them in charts tab
            if (result.csv) {
                displayResults(result.csv);
            }
        } else {
            outputElement.className = 'terminal-line error';
            outputElement.textContent += `\nError: ${result.error || 'Request failed'}`;
        }
    } catch (error) {
        outputElement.className = 'terminal-line error';
        outputElement.textContent += `\nError: ${error.message}`;
    }
}
// // Display results in charts tab
// function displayResults(csvData) {
//     // Switch to charts tab
//     document.querySelector('[data-tab="charts"]').click();
    
//     // Parse and render
//     const parsed = parseResults(csvData);
//     const chartsView = document.getElementById('charts-view');
//     chartsView.innerHTML = '<div id="result-chart"></div>';
    
//     // Auto-detect chart type based on data
//     if (parsed.headers.includes('probability') || parsed.headers.includes('success_rate')) {
//         renderBarChart('result-chart', {
//             x: parsed.rows.map(r => r.route || r.scenario || r.month),
//             y: parsed.rows.map(r => parseFloat(r.probability || r.success_rate)),
//             title: 'Results'
//         });
//     }
    
//     log('Results rendered in Charts tab', 'success');
// }

// Load file content
async function loadFile(path) {
    try {
        console.log('=== loadFile called ===');
        console.log('Path:', path);
        console.log('Editor object:', editor);
        
        const response = await fetch(`/api/file/${path}`);
        console.log('Response status:', response.status);
        
        const content = await response.text();
        console.log('Content length:', content.length);
        console.log('First 100 chars:', content.substring(0, 100));
        
        // Use the global CodeMirror editor instance
        console.log('About to call editor.setValue...');
        editor.setValue(content);
        editor.refresh();
        console.log('setValue completed');
        
        const filename = path.split('/').pop();
        document.getElementById('current-file').textContent = filename;
        
        // Update run button based on file type
        const runBtn = document.getElementById('run-btn');
        const runLabel = runBtn.querySelector('span') || runBtn;
        
        if (filename === 'config.dp') {
            runBtn.disabled = true;
            runLabel.textContent = 'Run';
        } else if (filename === 'decision.dp') {
            runBtn.disabled = false;
            runLabel.textContent = 'Run Decision';
            runBtn.dataset.mode = 'decision';
        } else if (filename === 'simulation.dp') {
            runBtn.disabled = false;
            runLabel.textContent = 'Run Simulation';
            runBtn.dataset.mode = 'simulation';
        } else if (filename === 'populate.dp') {
            runBtn.disabled = false;
            runLabel.textContent = 'Run Populate';
            runBtn.dataset.mode = 'populate';
        } else {
            runBtn.disabled = true;
            runLabel.textContent = 'Run';
        }
        
        currentFile = { path, content, filename };
        const pathParts = path.split('/');
            if (pathParts.length > 0) {
                currentModule = pathParts[0];
                updatePrompt();
            }
        
    } catch (error) {
        log(`Failed to load file: ${error.message}`, 'error');
    }
}
// Run ΔP code
async function runCode() {
    const code = editor.getValue(); // Changed from document.getElementById
    const output = document.getElementById('output-console');
    const runBtn = document.getElementById('run-btn');
    const mode = runBtn.dataset.mode;
    
    if (!mode) {
        log('No execution mode set', 'error');
        return;
    }
    
    output.classList.add('show');
    output.textContent = 'Executing...\n';
    
    // Extract module from current file path
    const modulePath = currentFile.path.split('/');
    const module = modulePath[modulePath.length - 2]; // ru_ch_bioethanol
    
    // Use terminal command execution
    const terminalOutput = document.createElement('div');
    await runDeltaP(mode, module, terminalOutput);
    
    output.textContent = terminalOutput.textContent;
}

// Mock chart for testing
function renderMockChart() {
    const chartsView = document.getElementById('charts-view');
    chartsView.innerHTML = '<div id="mock-chart"></div>';
    
    Plotly.newPlot('mock-chart', [{
        x: ['Route A', 'Route B', 'Route C'],
        y: [0.65, 0.82, 0.71],
        type: 'bar',
        marker: { color: '#0e639c' }
    }], {
        title: 'Success Probability by Route',
        paper_bgcolor: '#1e1e1e',
        plot_bgcolor: '#1e1e1e',
        font: { color: '#d4d4d4' }
    });
}

// Logging utility
function log(message, type = 'info') {
    const terminalOutput = document.getElementById('terminal-output');
    const entry = document.createElement('div');
    entry.className = `log-entry ${type}`;
    entry.textContent = `[${new Date().toLocaleTimeString()}] ${message}`;
    terminalOutput.appendChild(entry);
    terminalOutput.scrollTop = terminalOutput.scrollHeight;
}

// Setup resize handles
function setupResizers() {
    const resizers = document.querySelectorAll('.resize-handle');
    
    resizers.forEach(resizer => {
        resizer.addEventListener('mousedown', (e) => {
            isResizing = true;
            currentResizer = resizer.dataset.direction;
            document.body.style.cursor = 'col-resize';
            e.preventDefault();
        });
    });
    
    document.addEventListener('mousemove', (e) => {
        if (!isResizing) return;
        
        const app = document.getElementById('app');
        const fileTree = document.getElementById('file-tree');
        const visualizer = document.getElementById('visualizer');
        const appWidth = app.offsetWidth;
        
        if (currentResizer === 'file-tree') {
            const newWidth = e.clientX;
            const minWidth = 150;
            const maxWidth = 600; // Increased from 400
            
            if (newWidth >= minWidth && newWidth <= maxWidth) {
                fileTree.style.width = `${newWidth}px`;
                app.style.gridTemplateColumns = `${newWidth}px 4px 1fr 4px ${visualizer.offsetWidth}px`;
            }
        } else if (currentResizer === 'visualizer') {
            const newWidth = appWidth - e.clientX;
            const minWidth = 200; // Decreased from 300
            const maxWidth = appWidth - 200; // Editor can go down to 200px
            
            if (newWidth >= minWidth && newWidth <= maxWidth) {
                visualizer.style.width = `${newWidth}px`;
                app.style.gridTemplateColumns = `${fileTree.offsetWidth}px 4px 1fr 4px ${newWidth}px`;
            }
        }
    });
    
    document.addEventListener('mouseup', () => {
        isResizing = false;
        currentResizer = null;
        document.body.style.cursor = 'default';
    });
}

// Setup zoom controls
function setupZoom() {
    const zoomInBtn = document.getElementById('zoom-in');
    const zoomOutBtn = document.getElementById('zoom-out');
    const zoomDisplay = document.getElementById('zoom-level');
    
    function updateZoom() {
        const fontSize = Math.round(14 * (zoomLevel / 100));
        editor.getWrapperElement().style.fontSize = `${fontSize}px`;
        editor.refresh();
        zoomDisplay.textContent = `${zoomLevel}%`;
    }
    
    zoomInBtn.addEventListener('click', () => {
        if (zoomLevel < 200) {
            zoomLevel += 10;
            updateZoom();
        }
    });
    
    zoomOutBtn.addEventListener('click', () => {
        if (zoomLevel > 50) {
            zoomLevel -= 10;
            updateZoom();
        }
    });
    
    // Ctrl/Cmd + scroll to zoom
    editor.getWrapperElement().addEventListener('wheel', (e) => {
        if (e.ctrlKey || e.metaKey) {
            e.preventDefault();
            if (e.deltaY < 0) {
                if (zoomLevel < 200) {
                    zoomLevel += 10;
                    updateZoom();
                }
            } else {
                if (zoomLevel > 50) {
                    zoomLevel -= 10;
                    updateZoom();
                }
            }
        }
    });
}
async function loadAndVisualizeCSV(path) {
    try {
        log(`Loading ${path.split('/').pop()}...`, 'info');
        
        const response = await fetch(`/api/file/${path}`);
        const csvText = await response.text();
        
        const parsed = Papa.parse(csvText, { header: true, skipEmptyLines: true });
        const data = parsed.data;
        
        if (!data.length) {
            log('No data in CSV', 'error');
            return;
        }
        
        const chartsView = document.getElementById('charts-view');
        const filename = path.split('/').pop();
        
        // Detect decision vs simulation
        const hasMonth = 'month' in data[0];
        const hasScenario = 'scenario' in data[0];
        const hasRoute = 'route' in data[0];
        
        if (!hasMonth && hasRoute) {
            // Decision results - bar chart
            chartsView.innerHTML = '<div id="csv-chart" style="width:100%; height:600px;"></div>';
            
            const routes = data.map(r => parseInt(r.route?.trim()));
            const composite = data.map(r => parseFloat(r.composite?.trim()));
            
            Plotly.newPlot('csv-chart', [{
                x: routes.map(r => `Route ${r}`),
                y: composite,
                type: 'bar',
                marker: { 
                    color: '#0e639c',
                    line: { color: '#1177bb', width: 2 }
                },
                text: composite.map(v => v.toFixed(3)),
                textposition: 'outside',
                textfont: { size: 12 }
            }], {
                title: {
                    text: 'Decision Analysis: Composite Score by Route',
                    font: { color: '#d4d4d4', size: 18 }
                },
                xaxis: {
                    title: 'Route',
                    gridcolor: '#3e3e3e',
                    tickfont: { color: '#d4d4d4', size: 12 }
                },
                yaxis: {
                    title: 'Composite Score',
                    gridcolor: '#3e3e3e',
                    tickfont: { color: '#d4d4d4', size: 12 },
                    range: [0, Math.max(...composite) * 1.2]
                },
                paper_bgcolor: '#1e1e1e',
                plot_bgcolor: '#252526',
                font: { color: '#d4d4d4' },
                showlegend: false,
                margin: { t: 60, r: 40, b: 60, l: 60 }
            }, {
                responsive: true,
                displayModeBar: true,
                modeBarButtonsToRemove: ['lasso2d', 'select2d'],
                toImageButtonOptions: {
                    format: 'png',
                    filename: filename.replace('.csv', ''),
                    height: 600,
                    width: 1000,
                    scale: 2
                }
            });
            
        } else if (hasMonth && hasScenario && hasRoute) {
            // Simulation results - multi-line chart
            chartsView.innerHTML = '<div id="csv-chart" style="width:100%; height:600px;"></div>';
            
            const scenarios = [...new Set(data.map(r => parseInt(r.scenario?.trim())))];
            const routes = [...new Set(data.map(r => parseInt(r.route?.trim())))].sort();
            const colors = ['#0e639c', '#e74c3c', '#2ecc71'];
            
            const traces = [];
            
            scenarios.forEach((scenario, sIdx) => {
                routes.forEach((route, rIdx) => {
                    const filtered = data.filter(r => 
                        parseInt(r.scenario?.trim()) === scenario && 
                        parseInt(r.route?.trim()) === route
                    );
                    
                    traces.push({
                        x: filtered.map(r => parseInt(r.month?.trim())),
                        y: filtered.map(r => parseFloat(r.composite?.trim())),
                        type: 'scatter',
                        mode: 'lines+markers',
                        name: `S${scenario} R${route}`,
                        line: { 
                            color: colors[rIdx % colors.length],
                            width: 2,
                            dash: sIdx > 0 ? 'dash' : 'solid'
                        },
                        marker: { size: 6 }
                    });
                });
            });
            
            Plotly.newPlot('csv-chart', traces, {
                title: {
                    text: 'Simulation Results: Monthly Composite Success',
                    font: { color: '#d4d4d4', size: 18 }
                },
                xaxis: {
                    title: 'Month',
                    gridcolor: '#3e3e3e',
                    tickfont: { color: '#d4d4d4', size: 12 },
                    dtick: 1
                },
                yaxis: {
                    title: 'Composite Success',
                    gridcolor: '#3e3e3e',
                    tickfont: { color: '#d4d4d4', size: 12 }
                },
                paper_bgcolor: '#1e1e1e',
                plot_bgcolor: '#252526',
                font: { color: '#d4d4d4' },
                legend: {
                    bgcolor: '#2d2d2d',
                    bordercolor: '#3e3e3e',
                    borderwidth: 1
                },
                margin: { t: 60, r: 40, b: 60, l: 80 }
            }, {
                responsive: true,
                displayModeBar: true,
                modeBarButtonsToRemove: ['lasso2d', 'select2d'],
                toImageButtonOptions: {
                    format: 'png',
                    filename: filename.replace('.csv', ''),
                    height: 600,
                    width: 1200,
                    scale: 2
                }
            });
        }
        
        log(`Visualized ${filename}`, 'success');
        
    } catch (error) {
        log(`Failed to visualize: ${error.message}`, 'error');
        console.error(error);
    }
}
// // Ensure charts tab is active on load
// window.addEventListener('load', () => {
//     const chartsTab = document.querySelector('[data-tab="charts"]');
//     const chartsView = document.getElementById('charts-view');
    
//     // Deactivate all tabs
//     document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
//     document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    
//     // Activate charts
//     chartsTab.classList.add('active');
//     chartsView.classList.add('active');
// });