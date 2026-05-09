const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

exports.handler = async (event, context) => {
    if (event.httpMethod !== 'POST') {
        return { statusCode: 405, body: 'Method Not Allowed' };
    }

    const { csvPath, chartType } = JSON.parse(event.body);
    
    const projectsDir = path.join(__dirname, '../../projects');
    const outputPath = `/tmp/chart_${Date.now()}.png`;
    
    // Find full path to CSV
    let fullCsvPath = null;
    const projects = fs.readdirSync(projectsDir, { withFileTypes: true });
    
    for (const project of projects) {
        if (!project.isDirectory()) continue;
        const testPath = path.join(projectsDir, project.name, 'src', csvPath);
        if (fs.existsSync(testPath)) {
            fullCsvPath = testPath;
            break;
        }
    }
    
    if (!fullCsvPath) {
        return {
            statusCode: 404,
            body: JSON.stringify({ error: 'CSV file not found' })
        };
    }
    
    // Call Python visualization
    const python = spawn('python', [
        path.join(__dirname, '../../scripts/visualize_results.py'),
        '--input', fullCsvPath,
        '--type', chartType || 'auto',
        '--output', outputPath
    ]);
    
    return new Promise((resolve) => {
        let stderr = '';
        
        python.stderr.on('data', (data) => {
            stderr += data.toString();
        });
        
        python.on('close', (code) => {
            if (code === 0 && fs.existsSync(outputPath)) {
                const imageData = fs.readFileSync(outputPath, 'base64');
                fs.unlinkSync(outputPath); // Cleanup
                
                resolve({
                    statusCode: 200,
                    headers: { 'Content-Type': 'image/png' },
                    body: imageData,
                    isBase64Encoded: true
                });
            } else {
                resolve({
                    statusCode: 500,
                    body: JSON.stringify({ error: stderr || 'Visualization failed' })
                });
            }
        });
    });
};