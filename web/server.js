const express = require('express');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');
const chokidar = require('chokidar');

const app = express();
app.use(express.json());
app.use(express.static('.'));

// SSE clients for live updates
let sseClients = [];

// Watch projects directory for changes
const projectsDir = path.join(__dirname, 'projects');
const watcher = chokidar.watch(projectsDir, {
    ignored: /(^|[\/\\])\../,  // ignore dotfiles
    persistent: true,
    ignoreInitial: true
});

watcher
    .on('add', path => notifyClients('file_added', path))
    .on('unlink', path => notifyClients('file_deleted', path))
    .on('addDir', path => notifyClients('dir_added', path))
    .on('unlinkDir', path => notifyClients('dir_deleted', path));

function notifyClients(event, path) {
    console.log(`File change: ${event} - ${path}`);
    sseClients.forEach(client => {
        client.write(`data: ${JSON.stringify({ event, path })}\n\n`);
    });
}
// SSE endpoint for live updates
app.get('/api/watch-projects', (req, res) => {
    res.writeHead(200, {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive'
    });
    
    sseClients.push(res);
    
    req.on('close', () => {
        sseClients = sseClients.filter(client => client !== res);
    });
});

// Scan projects directory - return only modules from all projects
app.get('/api/list-projects', (req, res) => {
    const projectsDir = path.join(__dirname, 'projects');
    
    if (!fs.existsSync(projectsDir)) {
        fs.mkdirSync(projectsDir);
        return res.json({});
    }
    
    const allModules = {};
    const projects = fs.readdirSync(projectsDir, { withFileTypes: true });
    
    for (const project of projects) {
        if (!project.isDirectory() || project.name.startsWith('.')) continue;
        
        const srcPath = path.join(projectsDir, project.name, 'src');
        if (fs.existsSync(srcPath)) {
            // Get all modules from this project's src/
            const modules = scanDirectory(srcPath);
            Object.assign(allModules, modules);
        }
    }
    
    console.log('All modules:', JSON.stringify(allModules, null, 2));
    res.json(allModules);
});

function scanDirectory(dir) {
    const result = {};
    const entries = fs.readdirSync(dir, { withFileTypes: true });
    
    for (const entry of entries) {
        if (entry.name.startsWith('.')) continue;
        
        const fullPath = path.join(dir, entry.name);
        
        if (entry.isDirectory()) {
            result[entry.name] = scanDirectory(fullPath);
        } else {
            if (!result.files) result.files = [];
            result.files.push(entry.name);
        }
    }
    
    return result;
}

// Find and load file from any project's src/
app.get(/^\/api\/file\/(.*)$/, (req, res) => {
    const modulePath = req.params[0]; // e.g., "default/config.dp"
    const projectsDir = path.join(__dirname, 'projects');
    
    console.log('Looking for module path:', modulePath);
    
    // Search all projects for this module path
    const projects = fs.readdirSync(projectsDir, { withFileTypes: true });
    
    for (const project of projects) {
        if (!project.isDirectory() || project.name.startsWith('.')) continue;
        
        const fullPath = path.join(projectsDir, project.name, 'src', modulePath);
        console.log('Checking:', fullPath);
        console.log('Exists?', fs.existsSync(fullPath));
        
        if (fs.existsSync(fullPath)) {
            console.log('Found at:', fullPath);
            return res.sendFile(fullPath);
        }
    }
    
    console.log('File not found anywhere:', modulePath);
    res.status(404).send('File not found: ' + modulePath);
});

app.post('/api/run-deltap', async (req, res) => {
    const { mode, module } = req.body;
    
    console.log('Running dp:', mode, module);
    
    // Find the project that contains this module
    const projectsDir = path.join(__dirname, 'projects');
    const projects = fs.readdirSync(projectsDir, { withFileTypes: true });
    
    let projectPath = null;
    for (const project of projects) {
        if (!project.isDirectory() || project.name.startsWith('.')) continue;
        const modulePath = path.join(projectsDir, project.name, 'src', module);
        if (fs.existsSync(modulePath)) {
            projectPath = path.join(projectsDir, project.name);
            break;
        }
    }
    
    if (!projectPath) {
        return res.status(404).json({ 
            output: '', 
            error: `Module '${module}' not found in any project`,
            code: 1 
        });
    }
    
    console.log('Found project at:', projectPath);
    
    // Build command
    const command = mode === 'populate' ? ['populate', module] : ['run', mode, module];
    console.log('Executing: dp', command.join(' '));
    
    // Execute dp in the actual project directory w/ environment variable
    const dp = spawn('dp', command, { 
        cwd: projectPath,
        env: { 
            ...process.env,
        DELTAP_RESULTS_DIR: `src/${module}/data` 
        }
    });

    let output = '';
    let error = '';

    dp.stdout.on('data', (data) => {
        const text = data.toString();
        output += text;
        console.log('stdout:', text);
    });

    dp.stderr.on('data', (data) => {
        const text = data.toString();
        error += text;
        console.error('stderr:', text);
    });

    dp.on('close', (code) => {
        console.log('Process exited with code:', code);
        
        let csv = null;
        const resultsDir = path.join(projectPath, 'src', module, 'data');  
        if (fs.existsSync(resultsDir)) {
            const latestLink = path.join(resultsDir, 'latest');
            if (fs.existsSync(latestLink)) {
                try {
                    const latestDir = fs.realpathSync(latestLink);
                    const csvFiles = fs.readdirSync(latestDir).filter(f => f.startsWith(`${mode}_results_`));
                    if (csvFiles.length > 0) {
                        csv = fs.readFileSync(path.join(latestDir, csvFiles[0]), 'utf-8');
                    }
                } catch (e) {
                    console.error('Error reading results:', e);
                }
            }
        }
        
        res.json({ output, error, code, csv });
    });
});

app.post('/api/visualize', async (req, res) => {
    const { csvPath } = req.body;
    
    const projectsDir = path.join(__dirname, 'projects');
    
    // Extract module name from path (e.g., "logistics/data/..." -> "logistics")
    const module = csvPath.split('/')[0];
    
    // Find project containing this module
    let projectPath = null;
    const projects = fs.readdirSync(projectsDir, { withFileTypes: true });
    
    for (const project of projects) {
        if (!project.isDirectory()) continue;
        const modulePath = path.join(projectsDir, project.name, 'src', module);
        if (fs.existsSync(modulePath)) {
            projectPath = path.join(projectsDir, project.name);
            break;
        }
    }
    
    if (!projectPath) {
        return res.status(404).json({ error: 'Module not found' });
    }
    
    console.log('Running dp ink for module:', module);
    
    // Run dp ink command
    const dp = spawn('dp', ['ink', module], { cwd: projectPath });
    
    let stdout = '';
    let stderr = '';
    
    dp.stdout.on('data', (data) => {
        stdout += data.toString();
        console.log(data.toString());
    });
    
    dp.stderr.on('data', (data) => {
        stderr += data.toString();
        console.error(data.toString());
    });
    
    dp.on('close', (code) => {
        console.log('Python exit code:', code);
        
        if (code === 0) {
            // Find the PNG in the latest results directory
            const resultsDir = path.join(projectPath, 'src', module, 'data', module);
            
            if (fs.existsSync(resultsDir)) {
                const latestLink = path.join(resultsDir, 'latest');
                
                if (fs.existsSync(latestLink)) {
                    const latestDir = fs.realpathSync(latestLink);
                    const pngFiles = fs.readdirSync(latestDir).filter(f => f.endsWith('.png'));
                    
                    if (pngFiles.length > 0) {
                        const imagePath = path.join(latestDir, pngFiles[0]);
                        console.log('Sending PNG:', imagePath);
                        return res.sendFile(imagePath);
                    }
                }
            }
            
            res.status(404).json({ error: 'No PNG generated' });
        } else {
            res.status(500).json({ error: stderr || stdout });
        }
    });
});
app.listen(3000, () => console.log('ΔP Playground running on http://localhost:3000'));