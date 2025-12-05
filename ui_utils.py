
CANVAS_JS ='''
<script>
// Sprite loading with GIF support
let beeSprite = null;
let queenSprite = null;
let imagesLoaded = 0;
let beeIsGif = false;
let queenIsGif = false;

// Store DOM elements for each bee GIF
let beeGifElements = new Map(); // Map beeId -> DOM element

// ================= LINK MANAGER CLASS =================
class LinkManager {
    constructor() {
        this.links = new Map(); // key: "fromId->toId", value: Link object
        this.pendingLinks = []; // Links queued to fade in sequentially
        this.fadeInDelay = 200; // ms between sequential link appearances
        this.fadeInDuration = 300; // ms for fade-in animation
        this.lastPhase = "idle";
        this.lastLinkCount = 0;
    }
    
    // Create a unique key for a link
    getLinkKey(fromId, toId) {
        return `${fromId}->${toId}`;
    }
    
    // Update links based on new animation state
    updateFromState(animState, beePositions) {
        const currentPhase = animState.phase;
        const targetLinks = animState.links || [];
        
        // Detect phase transition - clear all links
        if (currentPhase !== this.lastPhase) {
            if (this.lastPhase !== "idle" && currentPhase !== this.lastPhase) {
                // Phase changed, fade out all existing links
                this.fadeOutAll(currentPhase === "aggregation" ? 200 : this.fadeInDuration); // Faster fade for aggregation
            }
            this.lastPhase = currentPhase;
        }
        
        // Build set of target link keys
        const targetKeys = new Set();
        for (const link of targetLinks) {
            const key = this.getLinkKey(link.from, link.to);
            targetKeys.add(key);
            
            // Add link if it doesn't exist
            if (!this.links.has(key)) {
                this.addLink(link.from, link.to, link.type, beePositions);
            }
        }
        
        // Remove links that are no longer in target
        for (const [key, link] of this.links) {
            if (!targetKeys.has(key) && link.opacity > 0) {
                link.fadeOut = true;
            }
        }
        
        this.lastLinkCount = targetLinks.length;
        
        // Update positions for all links
        this.updatePositions(beePositions);
    }
    
    addLink(fromId, toId, type, beePositions) {
        const key = this.getLinkKey(fromId, toId);
        if (this.links.has(key)) return;
        
        const link = {
            fromId: fromId,
            toId: toId,
            type: type,
            opacity: 0,
            targetOpacity: 1,
            fadeOut: false,
            createdAt: Date.now(),
            fromPos: { x: 0, y: 0 },
            toPos: { x: 0, y: 0 }
        };
        
        this.links.set(key, link);
        this.updateLinkPosition(link, beePositions);
    }
    
    updatePositions(beePositions) {
        // Only update positions for visible links to reduce computation
        for (const [key, link] of this.links) {
            if (link.opacity > 0) {
                this.updateLinkPosition(link, beePositions);
            }
        }
    }
    
    updateLinkPosition(link, beePositions) {
        // Cache position calculations to avoid redundant lookups
        if (!link._lastBeePositions || link._lastBeePositions !== beePositions) {
            const fromPos = this.getEntityPosition(link.fromId, beePositions);
            const toPos = this.getEntityPosition(link.toId, beePositions);
            
            if (fromPos) link.fromPos = fromPos;
            if (toPos) link.toPos = toPos;
            
            // Cache bee positions reference to avoid recalculation
            link._lastBeePositions = beePositions;
        }
    }
    
    getEntityPosition(entityId, beePositions) {
        // Handle Queen specially
        if (entityId === "Queen") {
            for (const [id, bee] of Object.entries(beePositions)) {
                if (bee.name === "Queen") {
                    return { x: bee.x, y: bee.y };
                }
            }
        }
        
        // Find bee by ID
        if (beePositions[entityId]) {
            return { x: beePositions[entityId].x, y: beePositions[entityId].y };
        }
        
        return null;
    }
    
    fadeOutAll(duration = this.fadeInDuration) {
        for (const [key, link] of this.links) {
            link.fadeOut = true;
            link.fadeOutDuration = duration; // Custom fade duration
        }
    }
    
    update(dt) {
        const toRemove = [];
        
        for (const [key, link] of this.links) {
            if (link.fadeOut) {
                // Fade out using custom duration if set
                const fadeDuration = link.fadeOutDuration || this.fadeInDuration;
                link.opacity -= dt / (fadeDuration / 1000);
                if (link.opacity <= 0) {
                    toRemove.push(key);
                }
            } else {
                // Fade in
                link.opacity += dt / (this.fadeInDuration / 1000);
                if (link.opacity > link.targetOpacity) {
                    link.opacity = link.targetOpacity;
                }
            }
        }
        
        // Remove fully faded out links
        for (const key of toRemove) {
            this.links.delete(key);
        }
    }
    
    render(ctx) {
        for (const [key, link] of this.links) {
            if (link.opacity <= 0) continue;
            
            this.drawLink(ctx, link);
        }
    }
    
    drawLink(ctx, link) {
        const { fromPos, toPos, type, opacity } = link;
        
        if (!fromPos || !toPos) return;
        
        ctx.save();
        ctx.globalAlpha = opacity;
        
        // Set color based on link type
        let color;
        let lineWidth = 2;
        switch (type) {
            case 'discussion':
                color = '#F9FAFB';
                lineWidth = 2;
                break;
            case 'aggregation':
                color = '#B57EDC'; 
                lineWidth = 3;
                break;
            default:
                color = '#FFFFFF';
        }
        
        ctx.strokeStyle = color;
        ctx.lineWidth = lineWidth;
        ctx.lineCap = 'round';
        
        // Draw curved line (no shadow on full curve for performance)
        const dx = toPos.x - fromPos.x;
        const dy = toPos.y - fromPos.y;
        const dist = Math.sqrt(dx * dx + dy * dy);
        
        // Control point for curve (perpendicular offset)
        const midX = (fromPos.x + toPos.x) / 2;
        const midY = (fromPos.y + toPos.y) / 2;
        const perpX = -dy / dist * (dist * 0.15);
        const perpY = dx / dist * (dist * 0.15);
        const ctrlX = midX + perpX;
        const ctrlY = midY + perpY;
        
        ctx.beginPath();
        ctx.moveTo(fromPos.x, fromPos.y);
        ctx.quadraticCurveTo(ctrlX, ctrlY, toPos.x, toPos.y);
        ctx.stroke();
        
        // Draw arrow head at end with glow
        const arrowSize = 8;
        const angle = Math.atan2(toPos.y - ctrlY, toPos.x - ctrlX);
        
        ctx.fillStyle = color;
        ctx.shadowColor = color;
        ctx.shadowBlur = 8 * opacity;  
        ctx.beginPath();
        ctx.moveTo(toPos.x, toPos.y);
        ctx.lineTo(
            toPos.x - arrowSize * Math.cos(angle - Math.PI / 6),
            toPos.y - arrowSize * Math.sin(angle - Math.PI / 6)
        );
        ctx.lineTo(
            toPos.x - arrowSize * Math.cos(angle + Math.PI / 6),
            toPos.y - arrowSize * Math.sin(angle + Math.PI / 6)
        );
        ctx.closePath();
        ctx.fill();
        
        ctx.restore();
    }
    
    clear() {
        this.links.clear();
        this.pendingLinks = [];
    }
}

// Global link manager instance
const linkManager = new LinkManager();
let lastFrameTime = Date.now();

// Load bee sprite
function loadSprite(type, src) {
    const isGif = src.toLowerCase().endsWith('.gif');
    
    if (isGif) {
        const img = new Image();
        img.onload = () => {
            imagesLoaded++;
            if (type === 'bee') {
                beeSprite = img;
                beeIsGif = true;
            } else {
                queenSprite = img;
                queenIsGif = true;
                // Attach queen GIF to DOM so it can be positioned like bee GIFs
                img.style.position = 'absolute';
                img.style.pointerEvents = 'none';
                img.style.display = 'none';
                img.style.zIndex = '1000';
                document.body.appendChild(img);
            }
        };
        img.onerror = () => console.error(`Failed to load ${type} GIF from ${src}`);
        img.src = src;
    } else {
        const img = new Image();
        img.onload = () => {
            imagesLoaded++;
            if (type === 'bee') {
                beeSprite = img;
                beeIsGif = false;
            } else {
                queenSprite = img;
                queenIsGif = false;
            }
        };
        img.onerror = () => console.error(`Failed to load ${type} static image from ${src}`);
        img.src = src;
    }
}

// Create or update a DOM element for a bee GIF
function getOrCreateBeeGifElement(beeId, src) {
    let element = beeGifElements.get(beeId);
    
    if (!element) {
        element = document.createElement('img');
        element.style.position = 'absolute';
        element.style.pointerEvents = 'none';
        element.style.display = 'none';
        element.style.zIndex = '1000';
        document.body.appendChild(element);
        element.src = src;
        beeGifElements.set(beeId, element);
    }
    
    return element;
}

loadSprite('bee', './icons/bee.gif');
loadSprite('queen', './icons/queen.gif');

function renderBees(data) {
    if (imagesLoaded < 2) return;
    
    const canvas = document.getElementById('myCanvas');
    if (!canvas) return;
    
    const ctx = canvas.getContext('2d');
    
    // Calculate delta time for animations
    const now = Date.now();
    const dt = (now - lastFrameTime) / 1000;
    lastFrameTime = now;
    
    // Extract bee states and animation state from data
    const beeStates = data.bees || data;
    const animState = data.animation || { phase: "idle", links: [] };
    
    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Hide all existing bee GIF elements
    beeGifElements.forEach(element => {
        element.style.display = 'none';
    });
    
    // Get canvas position for GIF positioning
    const canvasRect = canvas.getBoundingClientRect();
    
    // Update link manager with current animation state
    linkManager.updateFromState(animState, beeStates);
    linkManager.update(dt);
    
    // Render links first (behind bees)
    linkManager.render(ctx);
    
    // Render each bee
    for (const [id, bee] of Object.entries(beeStates)) {
        const isQueen = bee.name === "Queen";
        const sprite = isQueen ? queenSprite : beeSprite;
        const isGif = isQueen ? queenIsGif : beeIsGif;
        
        if (!sprite) continue;
        
        const angle = Math.atan2(bee.vy, bee.vx);

        // Base sprite size
        const baseSize = bee.size * 2;

        // Apply sinusoidal pulsing
        let scale = 1.0;
        const lastLink = animState.links && animState.links.length > 0 ? animState.links[animState.links.length - 1] : null;
        
        if (bee.name === "Queen" && animState.phase === "retrieval") {
            // Queen pulses during retrieval
            const t = now / 1000;
            const amp = 0.1;
            const freq = 5.0;
            let phase = 0;
            for (let i = 0; i < id.length; i++) {
                phase += id.charCodeAt(i);
            }
            phase = (phase % 100) / 100 * Math.PI * 2;
            scale = 1 + amp * Math.sin(t * freq + phase);
        } else if (animState.phase === "discussion") {
            if (lastLink && id === lastLink.to) {
                // Last linked bee pulses
                const t = now / 1000;
                const amp = 0.1;
                const freq = 5.0;
                let phase = 0;
                for (let i = 0; i < id.length; i++) {
                    phase += id.charCodeAt(i);
                }
                phase = (phase % 100) / 100 * Math.PI * 2;
                scale = 1 + amp * Math.sin(t * freq + phase);
            } else if (!lastLink && bee.state === "thinking") {
                // First bee in discussion pulses when no links exist yet
                const t = now / 1000;
                const amp = 0.1;
                const freq = 5.0;
                let phase = 0;
                for (let i = 0; i < id.length; i++) {
                    phase += id.charCodeAt(i);
                }
                phase = (phase % 100) / 100 * Math.PI * 2;
                scale = 1 + amp * Math.sin(t * freq + phase);
            }
        }

        const imgSize = baseSize * scale;
        
        if (isGif && !isQueen) {
            const beeElement = getOrCreateBeeGifElement(id, './icons/bee.gif');
            beeElement.style.display = 'block';
            beeElement.style.width = imgSize + 'px';
            beeElement.style.height = imgSize + 'px';
            beeElement.style.left = (canvasRect.left + bee.x - imgSize/2) + 'px';
            beeElement.style.top = (canvasRect.top + bee.y - imgSize/2) + 'px';
            beeElement.style.transform = `rotate(${angle}rad)`;
            beeElement.style.transformOrigin = 'center';
        } else if (isGif && isQueen) {
            sprite.style.display = 'block';
            sprite.style.width = imgSize + 'px';
            sprite.style.height = imgSize + 'px';
            sprite.style.left = (canvasRect.left + bee.x - imgSize/2) + 'px';
            sprite.style.top = (canvasRect.top + bee.y - imgSize/2) + 'px';
            sprite.style.transform = `rotate(${angle}rad)`;
            sprite.style.transformOrigin = 'center';
        } else {
            ctx.save();
            ctx.translate(bee.x, bee.y);
            ctx.rotate(angle);
            ctx.drawImage(sprite, -imgSize/2, -imgSize/2, imgSize, imgSize);
            ctx.restore();
        }
    }
}
</script>
'''


STYLES = '''
<style>
    .no-stepper input[type=number]::-webkit-inner-spin-button, 
    .no-stepper input[type=number]::-webkit-outer-spin-button { 
        -webkit-appearance: none; 
        margin: 0; 
    }
    .no-stepper input[type=number] {
        -moz-appearance: textfield;
    }
    .white-text-select .q-field__native,
    .white-text-select .q-field__prefix,
    .white-text-select .q-field__suffix,
    .white-text-select .q-field__input,
    .white-text-select .q-field__append,
    .white-text-select .q-icon {
        color: white !important;
    }
    .text-brand-yellow {
        color: #FFC30B !important;
    }
    /* Chat input focus color */
    .q-field.chat-input.q-field--focused .q-field__control,
    .q-field.chat-input.q-field--focused .q-field__control::before,
    .q-field.chat-input.q-field--focused .q-field__control::after {
        border-color: #FFC30B !important;
        box-shadow: 0 0 0 1px #FFC30B !important;
    }
    /* Loading dots animation */
    .loading-dots::after {
        content: '';
        animation: dots 1.5s steps(4, end) infinite;
    }
    @keyframes dots {
        0%, 20% { content: ''; }
        40% { content: '.'; }
        60% { content: '..'; }
        80%, 100% { content: '...'; }
    }
    /* Pulse animation for assembling bees */
    .animate-pulse {
        animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; transform: scale(1); }
        50% { opacity: 0.6; transform: scale(1.1); }
    }
    /* Fix drawer styling */
    .q-drawer--right .q-drawer__content {
        border-left: none !important;
    }
    .q-drawer-container {
        position: absolute !important;
    }
    .q-drawer__backdrop {
        background: transparent !important;
    }
    /* Fixed height textarea */
    .fixed-textarea .q-field__control {
        min-height: 60px !important;
        max-height: 80px !important;
    }
    /* Drawer scrollbar to match chat */
    .drawer-scroll::-webkit-scrollbar {
        width: 6px;
    }
    .drawer-scroll::-webkit-scrollbar-track {
        background: transparent;
    }
    .drawer-scroll::-webkit-scrollbar-thumb {
        background: #3f3f46;
        border-radius: 3px;
    }
    .drawer-scroll::-webkit-scrollbar-thumb:hover {
        background: #52525b;
    }
    /* Hide horizontal scroll in expansions */
    .q-expansion-item__content {
        overflow-x: hidden !important;
    }
    /* Drawer border styling */
    .q-drawer--right {
        border-left: 5px solid #27272A !important;
    }
    /* Fix dialog styling */
    .q-dialog {
        background: transparent !important;
    }
    .q-dialog .q-card {
        background: #18181b !important;
        color: white !important;
        border: 1px solid #27272a !important;
    }
    .q-dialog .q-card .text-brand-yellow {
        color: #FFC30B !important;
    }
    overflow-x: hidden !important;
}
</style>
'''