const fs = require('fs');
const vm = require('vm');
if (process.argv.length < 3) {
    console.error('Usage: node check_js_with_node.js <file>');
    process.exit(1);
}

const filePath = process.argv[2];
const content = fs.readFileSync(filePath, 'utf-8');

const regex = new RegExp('<script[^>]*>([\\s\\S]*?)<\\/script>', 'g');
const blocks = [...content.matchAll(regex)];
if (!blocks) {
    console.log('No script blocks found');
    process.exit(0);
}
blocks.forEach((m, i) => {
    const code = m[1];
    console.log('---- Block', i, 'length', code.length);
    try {
        // Try to compile
        new vm.Script(code);
        console.log('Compiled successfully');
    } catch (err) {
        console.error('Syntax error in block', i, err.message);
    }
});
