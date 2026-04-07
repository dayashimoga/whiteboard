(() => {
'use strict';
const $ = s => document.querySelector(s);
const $$ = s => document.querySelectorAll(s);

const canvas = $('#wbCanvas');
const ctx = canvas.getContext('2d');
let isDrawing = false;
let currentTool = 'pen';
let startX, startY;
const undoStack = [];
const redoStack = [];

// Initialize canvas
ctx.fillStyle = '#12121e';
if (document.documentElement.dataset.theme === 'light') {
    ctx.fillStyle = '#ffffff';
}
ctx.fillRect(0, 0, canvas.width, canvas.height);
saveState();

// Tools
$$('.wb-tool[data-tool]').forEach(btn => {
    btn.addEventListener('click', () => {
        $$('.wb-tool[data-tool]').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentTool = btn.dataset.tool;
    });
});

function saveState() {
    undoStack.push(canvas.toDataURL());
    if (undoStack.length > 50) undoStack.shift();
    redoStack.length = 0;
}

function restoreState(url) {
    const img = new Image();
    img.src = url;
    img.onload = () => {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.drawImage(img, 0, 0);
    };
}

canvas.addEventListener('mousedown', e => {
    isDrawing = true;
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    startX = x; startY = y;
    
    ctx.beginPath();
    ctx.moveTo(x, y);
    ctx.strokeStyle = currentTool === 'eraser' ? (document.documentElement.dataset.theme === 'light' ? '#fff' : '#12121e') : $('#wbColor').value;
    ctx.lineWidth = currentTool === 'eraser' ? $('#wbSize').value * 4 : $('#wbSize').value;
    ctx.lineCap = 'round';
    
    if (currentTool === 'text') {
        const text = prompt('Enter text:');
        if (text) {
            ctx.font = `${$('#wbSize').value * 5 + 10}px Inter`;
            ctx.fillStyle = $('#wbColor').value;
            ctx.fillText(text, x, y);
            saveState();
        }
        isDrawing = false;
    }
});

canvas.addEventListener('mousemove', e => {
    if (!isDrawing) return;
    const rect = canvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    if (currentTool === 'pen' || currentTool === 'eraser') {
        ctx.lineTo(x, y);
        ctx.stroke();
    }
});

canvas.addEventListener('mouseup', e => {
    if (!isDrawing) return;
    isDrawing = false;
    
    if (['line', 'rect', 'circle'].includes(currentTool)) {
        const rect = canvas.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        
        ctx.beginPath();
        if (currentTool === 'line') {
            ctx.moveTo(startX, startY);
            ctx.lineTo(x, y);
        } else if (currentTool === 'rect') {
            ctx.rect(startX, startY, x - startX, y - startY);
        } else if (currentTool === 'circle') {
            const r = Math.sqrt(Math.pow(x - startX, 2) + Math.pow(y - startY, 2));
            ctx.arc(startX, startY, r, 0, 2 * Math.PI);
        }
        ctx.stroke();
    }
    
    if (currentTool !== 'text') saveState();
});

$('#undoBtn').addEventListener('click', () => {
    if (undoStack.length > 1) {
        redoStack.push(undoStack.pop());
        restoreState(undoStack[undoStack.length - 1]);
    }
});

$('#redoBtn').addEventListener('click', () => {
    if (redoStack.length > 0) {
        const state = redoStack.pop();
        undoStack.push(state);
        restoreState(state);
    }
});

$('#clearBtn').addEventListener('click', () => {
    ctx.fillStyle = document.documentElement.dataset.theme === 'light' ? '#ffffff' : '#12121e';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    saveState();
});

$('#downloadBtn').addEventListener('click', () => {
    const link = document.createElement('a');
    link.download = `whiteboard-${Date.now()}.png`;
    link.href = canvas.toDataURL();
    link.click();
});

$('#wbSize').addEventListener('input', e => {
    $('#wbSizeLabel').textContent = e.target.value + 'px';
});

// Theme
if (typeof QU !== 'undefined') QU.initTheme();
else {
    $('#themeBtn').addEventListener('click', () => { 
        const h = document.documentElement; 
        const d = h.dataset.theme === 'dark'; 
        h.dataset.theme = d ? 'light' : 'dark'; 
        $('#themeBtn').textContent = d ? '☀️' : '🌙'; 
        localStorage.setItem('theme', h.dataset.theme);
        // Refresh canvas bg color on theme change
        const imgData = ctx.getImageData(0,0,canvas.width,canvas.height);
        ctx.fillStyle = d ? '#ffffff' : '#12121e';
        ctx.fillRect(0,0,canvas.width,canvas.height);
        // We can't perfectly invert colors of drawing, but this is a simple approach
    });
    if (localStorage.getItem('theme') === 'light') { document.documentElement.dataset.theme = 'light'; $('#themeBtn').textContent = '☀️'; ctx.fillStyle = '#ffffff'; ctx.fillRect(0,0,canvas.width,canvas.height); saveState(); }
}
})();
