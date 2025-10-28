import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

// Store last browsed path
let lastBrowsedPath = '';

// File browser dialog
class FileBrowserDialog {
    constructor() {
        this.currentPath = lastBrowsedPath || '';
        this.selectedFile = null;
        this.callback = null;
    }

    async show(callback) {
        this.callback = callback;
        
	// Create dialog overlay
	const overlay = document.createElement('div');
	overlay.style.cssText = `
		position: fixed;
		top: 0;
		left: 0;
		width: 100%;
		height: 100%;
		background: rgba(0, 0, 0, 0.8);
		display: flex;
		justify-content: center;
		align-items: center;
		z-index: 10000;
	`;

	// Make overlay focusable
	overlay.tabIndex = -1;
	overlay.focus();

	// Create dialog container
        const dialog = document.createElement('div');
        dialog.style.cssText = `
            background: #2a2a2a;
            border: 1px solid #555;
            border-radius: 6px;
            width: 85%;
            max-width: 900px;
            height: 75%;
            display: flex;
            flex-direction: column;
            color: #eee;
            font-family: system-ui, sans-serif;
            font-size: 13px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        `;
        
		// Create header with view controls
		const header = document.createElement('div');
		header.style.cssText = `
			padding: 12px 15px;
			border-bottom: 1px solid #444;
			display: flex;
			justify-content: space-between;
			align-items: center;
			background: #333;
		`;
		header.innerHTML = `
			<h3 style="margin: 0; font-size: 14px; font-weight: 600;">Select Image</h3>
			<div style="display: flex; gap: 8px; align-items: center;">
				<select id="sortMethod" style="background: #444; border: 1px solid #666; color: white; padding: 4px 8px; border-radius: 3px; font-size: 11px; cursor: pointer;">
					<option value="name_asc">A → Z</option>
					<option value="name_desc">Z → A</option>
					<option value="date_desc">Newest</option>
					<option value="date_asc">Oldest</option>
				</select>
				<button id="closeBrowser" style="background: #c00; border: none; color: white; padding: 4px 8px; cursor: pointer; border-radius: 3px; font-size: 12px; font-weight: bold;">✕</button>
			</div>
		`;
        
		// Create path display - EDITABLE VERSION
		const pathDisplay = document.createElement('div');
		pathDisplay.id = 'pathDisplay';
		pathDisplay.style.cssText = `
			padding: 8px 15px;
			background: #333;
			border-bottom: 1px solid #444;
			font-family: 'Courier New', monospace;
			font-size: 11px;
			display: flex;
			align-items: center;
			gap: 8px;
			color: #ccc;
		`;
        
        // Create browser content area
        const content = document.createElement('div');
        content.id = 'browserContent';
        content.style.cssText = `
            flex: 1;
            overflow-y: auto;
            padding: 4px;
            background: #1a1a1a;
        `;
        
        // Create preview area
        const previewArea = document.createElement('div');
        previewArea.id = 'previewArea';
        previewArea.style.cssText = `
            border-top: 1px solid #444;
            padding: 12px 15px;
            display: flex;
            gap: 12px;
            align-items: center;
            min-height: 80px;
            background: #2a2a2a;
            font-size: 12px;
        `;
        
        // Create footer with buttons
        const footer = document.createElement('div');
        footer.style.cssText = `
            padding: 12px 15px;
            border-top: 1px solid #444;
            display: flex;
            justify-content: flex-end;
            gap: 8px;
            background: #333;
        `;
        footer.innerHTML = `
            <button id="selectFile" style="background: #2a7a2a; border: none; color: white; padding: 6px 16px; cursor: pointer; border-radius: 3px; font-size: 12px;" disabled>Select</button>
            <button id="cancelBrowser" style="background: #555; border: none; color: white; padding: 6px 16px; cursor: pointer; border-radius: 3px; font-size: 12px;">Cancel</button>
        `;
        
        dialog.appendChild(header);
        dialog.appendChild(pathDisplay);
        dialog.appendChild(content);
        dialog.appendChild(previewArea);
        dialog.appendChild(footer);
        overlay.appendChild(dialog);
        document.body.appendChild(overlay);
        
        // ESC key handler
        const escHandler = (e) => {
            if (e.key === 'Escape') {
                close();
            }
        };
        document.addEventListener('keydown', escHandler);

        // Close function
        const close = () => {
            document.removeEventListener('keydown', escHandler);
            document.body.removeChild(overlay);
        };
        
        // Event handlers
        overlay.querySelector('#closeBrowser').onclick = close;
        overlay.querySelector('#cancelBrowser').onclick = close;
        
        const selectAndClose = () => {
            if (this.selectedFile) {
                const separator = this.selectedFile.includes('\\') ? '\\' : '/';
                lastBrowsedPath = this.selectedFile.substring(0, this.selectedFile.lastIndexOf(separator));
                this.callback(this.selectedFile);
                close();
            }
        };
        
        overlay.querySelector('#selectFile').onclick = selectAndClose;

		// Add the sort change handler
		const sortSelect = overlay.querySelector('#sortMethod');
		sortSelect.onchange = () => {
			this.loadDirectory(this.currentPath);
		};
 
		// Load initial directory
        await this.loadDirectory(this.currentPath);
    }
 
    async loadDirectory(path) {
        this.currentPath = path;
        const content = document.getElementById('browserContent');
        const pathDisplay = document.getElementById('pathDisplay');
        const previewArea = document.getElementById('previewArea');
        
        content.innerHTML = '<div style="text-align: center; padding: 40px; color: #888; font-size: 12px;">Loading...</div>';
        previewArea.innerHTML = '';
        this.selectedFile = null;
        document.getElementById('selectFile').disabled = true;
        
        try {
			const sortMethod = document.getElementById('sortMethod') ? document.getElementById('sortMethod').value : 'name_asc';
			const response = await api.fetchApi(`/ib_custom_nodes/browse_directory?path=${encodeURIComponent(path)}&sort=${encodeURIComponent(sortMethod)}`);
			const data = await response.json();
            
            if (data.error) {
                content.innerHTML = `<div style="color: #f55; padding: 20px; text-align: center; font-size: 12px;">Error: ${data.error}</div>`;
                return;
            }
			
		const sortSelect = document.getElementById('sortMethod');
			if (sortSelect && data.sort_method) {
				sortSelect.value = data.sort_method;
			}
            
            // Update path display
			pathDisplay.innerHTML = `
				<button id="goUp" style="background: #444; border: none; color: white; padding: 3px 8px; cursor: pointer; border-radius: 2px; font-size: 11px;">↑ Up</button>
				<input type="text" id="pathInput" value="${data.current_path || ''}" style="
					flex: 1;
					background: #1a1a1a;
					border: 1px solid #555;
					color: #eee;
					padding: 4px 8px;
					border-radius: 3px;
					font-family: 'Courier New', monospace;
					font-size: 11px;
				" />
				<button id="goPath" style="background: #444; border: none; color: white; padding: 3px 8px; cursor: pointer; border-radius: 2px; font-size: 11px;">Go</button>
			`;
            
			// Add event handler for the Go button and Enter key
			const pathInput = document.getElementById('pathInput');
			const goPathBtn = document.getElementById('goPath');

			const goToPath = () => {
				const newPath = pathInput.value.trim();
				if (newPath) {
					this.loadDirectory(newPath);
				}
			};

			goPathBtn.onclick = goToPath;
			pathInput.onkeypress = (e) => {
				if (e.key === 'Enter') {
					goToPath();
				}
			};
			
            const goUpBtn = document.getElementById('goUp');
            if (data.parent_path) {
                goUpBtn.onclick = () => this.loadDirectory(data.parent_path);
            } else {
                goUpBtn.disabled = true;
                goUpBtn.style.opacity = '0.4';
                goUpBtn.style.cursor = 'not-allowed';
            }
            
			// Build file list - LIST VIEW ONLY
			let html = '<div style="display: flex; flex-direction: column; gap: 2px;">';

			// Directories in list view
			for (const dir of data.directories) {
				const fullPath = data.current_path ? `${data.current_path}${data.current_path.endsWith('/') || data.current_path.endsWith('\\') ? '' : (path.includes('\\') ? '\\' : '/')}${dir}` : dir;
				html += `
					<div class="browser-item directory" data-path="${fullPath}" style="
						padding: 4px 8px;
						background: #333;
						border-radius: 3px;
						cursor: pointer;
						display: flex;
						align-items: center;
						gap: 6px;
						font-size: 12px;
						border: 1px solid transparent;
					">
						<span style="font-size: 16px;">📁</span>
						<span style="color: #eee;">${dir}</span>
					</div>
				`;
			}

			// Files in list view
			for (const file of data.files) {
				const fullPath = data.current_path ? `${data.current_path}${data.current_path.endsWith('/') || data.current_path.endsWith('\\') ? '' : (data.current_path.includes('\\') ? '\\' : '/')}${file}` : file;
				html += `
					<div class="browser-item file" data-path="${fullPath}" style="
						padding: 4px 8px;
						background: #2a2a2a;
						border-radius: 3px;
						cursor: pointer;
						display: flex;
						align-items: center;
						gap: 6px;
						font-size: 12px;
						border: 1px solid transparent;
					">
						<span style="font-size: 16px;">🖼️</span>
						<span style="color: #ccc;">${file}</span>
					</div>
				`;
			}

			html += '</div>';
			content.innerHTML = html;
			
            // Add click handlers
            this.attachEventHandlers(content);
            
        } catch (error) {
            content.innerHTML = `<div style="color: #f55; padding: 20px; text-align: center; font-size: 12px;">Error loading directory: ${error.message}</div>`;
        }
    }
    
    attachEventHandlers(content) {
        // Click handlers for directories
        content.querySelectorAll('.browser-item.directory').forEach(item => {
            item.onclick = () => {
                const path = item.getAttribute('data-path');
                this.loadDirectory(path);
            };
            item.onmouseenter = () => {
                item.style.background = '#3a3a3a';
                item.style.border = '1px solid #666';
            };
            item.onmouseleave = () => {
                item.style.background = '#333';
                item.style.border = '1px solid transparent';
            };
        });
        
        // Click handlers for files
        content.querySelectorAll('.browser-item.file').forEach(item => {
            let clickTimer;
            let clickCount = 0;
            
            const selectFile = async () => {
                // Remove selection from other items
                content.querySelectorAll('.browser-item.file').forEach(i => {
                    i.style.background = '#2a2a2a';
                    i.style.border = '1px solid transparent';
                });
                
                // Highlight this item
                item.style.background = '#2a4a2a';
                item.style.border = '1px solid #3a7a3a';
                
                const path = item.getAttribute('data-path');
                this.selectedFile = path;
                document.getElementById('selectFile').disabled = false;
                
                // Load preview
                await this.loadPreview(path);
            };
            
            // Click handler for both single and double click
            item.onclick = (e) => {
                clickCount++;
                
                if (clickCount === 1) {
                    clickTimer = setTimeout(() => {
                        // Single click behavior
                        selectFile();
                        clickCount = 0;
                    }, 300);
                } else if (clickCount === 2) {
                    // Double click behavior
                    clearTimeout(clickTimer);
                    const path = item.getAttribute('data-path');
                    this.selectedFile = path;
                    const separator = path.includes('\\') ? '\\' : '/';
                    lastBrowsedPath = path.substring(0, path.lastIndexOf(separator));
                    this.callback(path);
                    document.body.querySelector('[style*="z-index: 10000"]')?.remove();
                    clickCount = 0;
                }
            };
            
            item.onmouseenter = () => {
                if (item.style.background !== '#2a4a2a') {
                    item.style.background = '#3a3a3a';
                    item.style.border = '1px solid #666';
                }
            };
            item.onmouseleave = () => {
                if (item.style.background !== '#2a4a2a') {
                    item.style.background = '#2a2a2a';
                    item.style.border = '1px solid transparent';
                }
            };
        });
    }
    
    async loadPreview(path) {
        const previewArea = document.getElementById('previewArea');
        previewArea.innerHTML = '<div style="color: #888; font-size: 11px;">Loading preview...</div>';
        
        try {
            const response = await api.fetchApi(`/ib_custom_nodes/get_image_preview?path=${encodeURIComponent(path)}`);
            const data = await response.json();
            
            if (data.error) {
                previewArea.innerHTML = `<div style="color: #f55; font-size: 11px;">Preview error: ${data.error}</div>`;
                return;
            }
            
            previewArea.innerHTML = `
                <img src="${data.preview}" style="max-height: 60px; max-width: 100px; border: 1px solid #555; border-radius: 3px;" />
                <div style="font-size: 11px; color: #ccc;">
                    <div>${data.width} × ${data.height}</div>
                    <div style="margin-top: 3px; word-break: break-all; max-width: 400px; color: #999;">${path.split(/[\\/]/).pop()}</div>
                </div>
            `;
        } catch (error) {
            previewArea.innerHTML = `<div style="color: #f55; font-size: 11px;">Error loading preview</div>`;
        }
    }
}

app.registerExtension({
    name: "Ib.ImageLoader",
    
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "LoadImageFromPathEnhanced") {
            const onNodeCreated = nodeType.prototype.onNodeCreated;
            
            nodeType.prototype.onNodeCreated = function() {
                const result = onNodeCreated ? onNodeCreated.apply(this, arguments) : undefined;
                const node = this;
                
                // Add browse button - THIS WAS MISSING!
                node.addWidget("button", "🔍 Browse...", null, () => {
                    const browser = new FileBrowserDialog();
                    browser.show(async (filePath) => {
                        const pathWidget = node.widgets.find(w => w.name === "image");
                        if (pathWidget) {
                            pathWidget.value = filePath;
                            
                            // Load image using ComfyUI's proper system
							try {
								const filename = filePath.split(/[\\/]/).pop();
								const imgUrl = `/ib_custom_nodes/serve_image?path=${encodeURIComponent(filePath)}&filename=${encodeURIComponent(filename)}`;
								const img = new Image();
								
								// Add cache busting to prevent cached issues
								img.src = imgUrl + '&t=' + Date.now();
								
								img.onload = () => {
									// Ensure node.imgs exists and is properly set
									if (!node.imgs) {
										node.imgs = [];
									}
									node.imgs = [img];
									node.imageIndex = 0;
									
									// Force a more comprehensive refresh
									app.graph.setDirtyCanvas(true, true);
									
									// Also trigger node refresh specifically
									if (node.onDrawBackground) {
										node.onDrawBackground();
									}
								};
								
								img.onerror = () => {
									console.warn('Failed to load image preview:', filePath);
									// Clear any broken images but keep the node functional
									node.imgs = null;
									node.imageIndex = 0;
									app.graph.setDirtyCanvas(true, true);
								};
								
							} catch (e) {
								console.error('Failed to load image:', e);
								node.imgs = null;
								node.imageIndex = 0;
								app.graph.setDirtyCanvas(true, true);
							}
                        }
                    });
                });
                
                return result;
            };
        }
    }
});