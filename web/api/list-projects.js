const fs = require('fs');
const path = require('path');

exports.handler = async (event, context) => {
    const projectsDir = path.join(__dirname, '../../projects');
    
    if (!fs.existsSync(projectsDir)) {
        return {
            statusCode: 404,
            body: JSON.stringify({ error: 'Projects directory not found' })
        };
    }
    
    const structure = scanDirectory(projectsDir);
    
    return {
        statusCode: 200,
        body: JSON.stringify(structure)
    };
};

function scanDirectory(dir, basePath = '') {
    const result = {};
    const entries = fs.readdirSync(dir, { withFileTypes: true });
    
    for (const entry of entries) {
        if (entry.name.startsWith('.')) continue; // Skip hidden files
        
        const fullPath = path.join(dir, entry.name);
        
        if (entry.isDirectory()) {
            result[entry.name] = scanDirectory(fullPath, `${basePath}${entry.name}/`);
        } else {
            if (!result.files) result.files = [];
            result.files.push(entry.name);
        }
    }
    
    return result;
}