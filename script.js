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

// New features state
let isShapeRecogOn = false;
let currentStroke = [];

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

$('#shapeRecogBtn')?.addEventListener('click', (e) => {
    isShapeRecogOn = !isShapeRecogOn;
    e.currentTarget.classList.toggle('active', isShapeRecogOn);
    e.currentTarget.title = `Shape Recognition (${isShapeRecogOn ? 'On' : 'Off'})`;
    if(typeof QU !== 'undefined') QU.showToast(`Shape Recognition ${isShapeRecogOn ? 'Enabled' : 'Disabled'}`);
});

$('#replayBtn')?.addEventListener('click', async () => {
    if(undoStack.length < 2) {
        if(typeof QU !== 'undefined') QU.showToast('Not enough history to replay', 'error');
        return;
    }
    const stackCopy = [...undoStack];
    ctx.fillStyle = document.documentElement.dataset.theme === 'light' ? '#ffffff' : '#12121e';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    for(let i=0; i<stackCopy.length; i++) {
        await new Promise(r => setTimeout(r, 150));
        const img = new Image();
        img.src = stackCopy[i];
        await new Promise(r => { img.onload = r; });
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.drawImage(img, 0, 0);
    }
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
    currentStroke = [{x, y}];
    
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
        currentStroke.push({x, y});
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
    } else if (currentTool === 'pen' && isShapeRecogOn && currentStroke.length > 10) {
        const start = currentStroke[0];
        const end = currentStroke[currentStroke.length - 1];
        let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
        currentStroke.forEach(p => {
            if(p.x < minX) minX = p.x;
            if(p.x > maxX) maxX = p.x;
            if(p.y < minY) minY = p.y;
            if(p.y > maxY) maxY = p.y;
        });
        const w = maxX - minX;
        const h = maxY - minY;
        const distToStart = Math.sqrt(Math.pow(end.x - start.x, 2) + Math.pow(end.y - start.y, 2));
        
        restoreState(undoStack[undoStack.length - 1]);
        
        setTimeout(() => {
            ctx.beginPath();
            ctx.strokeStyle = $('#wbColor').value;
            ctx.lineWidth = $('#wbSize').value;
            ctx.lineCap = 'round';
            
            if (distToStart < 30 && Math.abs(w - h) < Math.max(w, h) * 0.3 && w > 20) {
                const cx = minX + w/2;
                const cy = minY + h/2;
                const r = (w + h) / 4;
                ctx.arc(cx, cy, r, 0, 2 * Math.PI);
                ctx.stroke();
                saveState();
                if(typeof QU !== 'undefined') QU.showToast('Recognized: Circle');
            } else if (distToStart > 30 && (w < 20 || h < 20 || Math.abs(w - h) > 30)) {
                ctx.moveTo(start.x, start.y);
                ctx.lineTo(end.x, end.y);
                ctx.stroke();
                saveState();
                if(typeof QU !== 'undefined') QU.showToast('Recognized: Line');
            } else if (distToStart < 30 && w > 20 && h > 20) {
                ctx.rect(minX, minY, w, h);
                ctx.stroke();
                saveState();
                if(typeof QU !== 'undefined') QU.showToast('Recognized: Rectangle');
            } else {
                ctx.moveTo(start.x, start.y);
                for(let i=1; i<currentStroke.length; i++){
                    ctx.lineTo(currentStroke[i].x, currentStroke[i].y);
                }
                ctx.stroke();
                saveState();
            }
        }, 50);
        return;
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
