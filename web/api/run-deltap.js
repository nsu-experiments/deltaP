const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');
const os = require('os');

exports.handler = async (event, context) => {
    if (event.httpMethod !== 'POST') {
        return { statusCode: 405, body: 'Method Not Allowed' };
    }

    const { mode, module, files } = JSON.parse(event.body);
    
    // Create temp workspace
    const workspaceDir = path.join(os.tmpdir(), `deltap-${Date.now()}`);
    const srcDir = path.join(workspaceDir, 'src', module);
    
    try {
        // Create directory structure
        fs.mkdirSync(srcDir, { recursive: true });
        
        // Write .dp files
        for (const [filename, content] of Object.entries(files)) {
            fs.writeFileSync(path.join(srcDir, filename), content);
        }
        
        // Write deltap.toml
        const toml = `[project]
name = "web-playground"
version = "0.1.0"

[database]
path = "delta_db.h5"
`;
        fs.writeFileSync(path.join(workspaceDir, 'deltap.toml'), toml);
        
        // Determine command
        let command;
        if (mode === 'populate') {
            command = ['populate', module];
        } else {
            command = ['run', mode, module];
        }
        
        // Execute deltap command
        const result = await runDeltaP(command, workspaceDir);
        
        // Read results if they exist
        let csv = null;
        const resultsDir = path.join(workspaceDir, 'results', module);
        if (fs.existsSync(resultsDir)) {
            const latestLink = path.join(resultsDir, 'latest');
            if (fs.existsSync(latestLink)) {
                const latestDir = fs.realpathSync(latestLink);
                const csvFile = path.join(latestDir, `${mode}_results_*.csv`);
                const csvFiles = fs.readdirSync(latestDir).filter(f => f.startsWith(`${mode}_results_`));
                if (csvFiles.length > 0) {
                    csv = fs.readFileSync(path.join(latestDir, csvFiles[0]), 'utf-8');
                }
            }
        }
        
        // Cleanup
        fs.rmSync(workspaceDir, { recursive: true, force: true });
        
        return {
            statusCode: 200,
            body: JSON.stringify({
                output: result.output,
                error: result.error,
                code: result.code,
                csv: csv
            })
        };
        
    } catch (error) {
        // Cleanup on error
        if (fs.existsSync(workspaceDir)) {
            fs.rmSync(workspaceDir, { recursive: true, force: true });
        }
        
        return {
            statusCode: 500,
            body: JSON.stringify({
                output: '',
                error: error.message,
                code: 1
            })
        };
    }
};

function runDeltaP(command, cwd) {
    return new Promise((resolve) => {
        const deltap = spawn('deltap', command, { cwd });
        
        let output = '';
        let error = '';
        
        deltap.stdout.on('data', (data) => {
            output += data.toString();
        });
        
        deltap.stderr.on('data', (data) => {
            error += data.toString();
        });
        
        deltap.on('close', (code) => {
            resolve({ output, error, code });
        });
    });
}