import torch

import hashlib
from pathlib import Path
from typing import Iterable
import os
import json
import shutil

from PIL import Image, ImageOps
import numpy as np

import folder_paths
from aiohttp import web
from server import PromptServer

# ===================================================================================
# ORIGINAL VERSION OF THE NODE
# ===================================================================================

class LoadImageFromPath:
    @classmethod
    def INPUT_TYPES(s):
        return {"required":
                    {"image": ("STRING", {"default": r"ComfyUI_00001_-assets\ComfyUI_00001_.png [output]"})},
                }

    CATEGORY = "image"

    RETURN_TYPES = ("IMAGE", "MASK")
    FUNCTION = "load_image"
    def load_image(self, image):
        image_path = LoadImageFromPath._resolve_path(image)

        i = Image.open(image_path)
        i = ImageOps.exif_transpose(i)
        image = i.convert("RGB")
        image = np.array(image).astype(np.float32) / 255.0
        image = torch.from_numpy(image)[None,]
        if 'A' in i.getbands():
            mask = np.array(i.getchannel('A')).astype(np.float32) / 255.0
            mask = 1. - torch.from_numpy(mask)
        else:
            mask = torch.zeros((64,64), dtype=torch.float32, device="cpu")
        return (image, mask)

    def _resolve_path(image) -> Path:
        image_path = Path(folder_paths.get_annotated_filepath(image))
        return image_path

    @classmethod
    def IS_CHANGED(s, image):
        image_path = LoadImageFromPath._resolve_path(image)
        m = hashlib.sha256()
        with open(image_path, 'rb') as f:
            m.update(f.read())
        return m.digest().hex()

    @classmethod
    def VALIDATE_INPUTS(s, image):
        # If image is an output of another node, it will be None during validation
        if image is None:
            return True

        image_path = LoadImageFromPath._resolve_path(image)
        if not image_path.exists():
            return "Invalid image path: {}".format(image_path)

        return True

class PILToImage:
    @classmethod
    def INPUT_TYPES(s):
        return {'required': 
                    {'images': ('PIL_IMAGE', )},
                }

    RETURN_TYPES = ('IMAGE',)
    FUNCTION = 'pil_images_to_images'

    CATEGORY = 'image/PIL'

    def pil_images_to_images(self, images: Iterable[Image.Image]) -> torch.Tensor:
        pil_images = images

        images = []
        for pil_image in pil_images:
            i = pil_image
            i = ImageOps.exif_transpose(i)
            if i.mode == 'I':
                i = i.point(lambda i: i * (1 / 255))
            image = i.convert("RGB")
            image = np.array(image).astype(np.float32) / 255.0
            image = torch.from_numpy(image)[None,]
            images.append(image)
        
        if len(images) > 1:
            images = torch.cat(images, dim=0)
        else:
            images = images[0]

        return (images,)

class PILToMask:
    @classmethod
    def INPUT_TYPES(s):
        return {'required': 
                    {'images': ('PIL_IMAGE', )},
                }

    RETURN_TYPES = ('IMAGE',)
    FUNCTION = 'pil_images_to_masks'

    CATEGORY = 'image/PIL'

    def pil_images_to_masks(self, images: Iterable[Image.Image]) -> torch.Tensor:
        pil_images = images

        masks = []
        for pil_image in pil_images:
            i = pil_image
            i = ImageOps.exif_transpose(i)
            if i.mode == 'I':
                i = i.point(lambda i: i * (1 / 255))
            if 'A' in i.getbands():
                mask = np.array(i.getchannel('A')).astype(np.float32) / 255.0
                mask = 1. - torch.from_numpy(mask)
            else:
                mask = torch.zeros((64,64), dtype=torch.float32, device="cpu")
            masks.append(mask)
        
        if len(masks) > 1:
            masks = torch.cat(masks, dim=0)
        else:
            masks = masks[0]

        return (masks,)

class ImageToPIL:
    @classmethod
    def INPUT_TYPES(s):
        return {'required': 
                    {'images': ('IMAGE', )},
                }

    RETURN_TYPES = ('PIL_IMAGE',)
    FUNCTION = 'images_to_pil_images'

    CATEGORY = 'image/PIL'

    def images_to_pil_images(self, images: torch.Tensor) -> list[Image.Image]:
        pil_images = []
        for image in images:
            i = 255. * image.cpu().numpy()
            img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
            pil_images.append(img)
        return (pil_images,)       

# =================================================================================================================
# ENHANCED VERSION WITH FILE BROWSER AND MASK EDITOR SUPPORT
# Features: Full file browser, sorting, preview, any path access, clipspace support and path as a string output
# =================================================================================================================

# Global cache to track image paths and clipspace mappings
_image_path_cache = {}
_clipspace_mappings = {}  # Maps expected filename -> actual filename

class LoadImageFromPathEnhanced(LoadImageFromPath):
    @classmethod
    def INPUT_TYPES(s):
        return {"required":
                    {"image": ("STRING", {"default": r"ComfyUI_00001_-assets\ComfyUI_00001_.png [output]"})},
                }

    CATEGORY = "image"
    RETURN_TYPES = ("IMAGE", "MASK", "STRING")
    RETURN_NAMES = ("IMAGE", "MASK", "path")
    FUNCTION = "load_image_enhanced"
    
    def load_image_enhanced(self, image):
        # Get the full path
        image_path = LoadImageFromPath._resolve_path(image)
        
        # Call the parent class's load_image method
        image_tensor, mask = super().load_image(image)
        
        # Register this image in our cache for mask editor support
        filename = os.path.basename(str(image_path))
        _image_path_cache[filename] = str(image_path)
        _image_path_cache[str(image_path)] = str(image_path)
        
        # Return image, mask, AND the original input path string
        return (image_tensor, mask, image)

# Middleware to handle clipspace file resolution
@web.middleware
async def clipspace_resolver_middleware(request, handler):
    """
    Middleware to intercept /api/view requests and resolve clipspace filename mismatches.
    This fixes the issue where mask editor looks for 'clipspace-mask-X.png' but 
    the actual file is 'clipspace-painted-masked-X.png'
    """
    if request.path == '/api/view':
        filename = request.query.get('filename', '')
        subfolder = request.query.get('subfolder', '')
        
        # Only intercept clipspace requests looking for 'clipspace-mask-' files
        if subfolder == 'clipspace' and filename.startswith('clipspace-mask-'):
            input_dir = folder_paths.get_input_directory()
            clipspace_dir = os.path.join(input_dir, 'clipspace')
            
            # Check if the requested file exists
            requested_path = os.path.join(clipspace_dir, filename)
            
            if not os.path.exists(requested_path):
                # Try to find the actual file with 'painted-masked' naming
                number = filename.replace('clipspace-mask-', '').replace('.png', '')
                alternative_filename = f'clipspace-painted-masked-{number}.png'
                alternative_path = os.path.join(clipspace_dir, alternative_filename)
                
                if os.path.exists(alternative_path):
                    # Create a symlink or copy to the expected filename
                    try:
                        # Try symlink first (faster)
                        if os.name != 'nt':  # Unix-like systems
                            if not os.path.exists(requested_path):
                                os.symlink(alternative_path, requested_path)
                        else:  # Windows - use copy instead
                            shutil.copy2(alternative_path, requested_path)
                    except Exception as e:
                        print(f"[IB] Could not create link/copy: {e}")
    
    # Continue with normal handling
    return await handler(request)

# Register middleware
PromptServer.instance.app.middlewares.append(clipspace_resolver_middleware)

# Server endpoints for file browsing
@PromptServer.instance.routes.get("/ib_custom_nodes/browse_directory")
async def browse_directory(request):
    """Browse directories and return file listings"""
    try:
        path = request.query.get('path', '')
        sort_method = request.query.get('sort', 'name_asc')
        
        if not path:
            if os.name == 'nt':  # Windows
                drives = [f"{d}:\\" for d in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' if os.path.exists(f"{d}:\\")]
                return web.json_response({
                    'directories': drives,
                    'files': [],
                    'current_path': ''
                })
            else:  # Unix-like
                path = os.path.expanduser('~')
        
        path = os.path.abspath(path)
        
        if not os.path.exists(path) or not os.path.isdir(path):
            return web.json_response({'error': 'Invalid path'}, status=400)
        
        directories = []
        files = []
        
        try:
            items = []
            for item in os.listdir(path):
                if item.startswith('.'):
                    continue
                    
                item_path = os.path.join(path, item)
                try:
                    if os.path.isdir(item_path):
                        item_type = 'directory'
                        stat = os.stat(item_path)
                    elif os.path.isfile(item_path):
                        ext = os.path.splitext(item)[1].lower()
                        if ext in ['.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp', '.tiff', '.tif']:
                            item_type = 'file'
                            stat = os.stat(item_path)
                        else:
                            continue
                    else:
                        continue
                except (PermissionError, OSError):
                    continue
                
                items.append({
                    'name': item,
                    'type': item_type,
                    'path': item_path,
                    'modified': stat.st_mtime
                })
                
            # Apply sorting
            if sort_method == 'name_asc':
                items.sort(key=lambda x: x['name'].lower())
            elif sort_method == 'name_desc':
                items.sort(key=lambda x: x['name'].lower(), reverse=True)
            elif sort_method == 'date_desc':
                items.sort(key=lambda x: x['modified'], reverse=True)
            elif sort_method == 'date_asc':
                items.sort(key=lambda x: x['modified'])
            
            for item in items:
                if item['type'] == 'directory':
                    directories.append(item['name'])
                else:
                    files.append(item['name'])
                    
        except PermissionError:
            return web.json_response({'error': 'Permission denied'}, status=403)
        
        parent_path = os.path.dirname(path) if path != os.path.dirname(path) else None
        
        return web.json_response({
            'directories': directories,
            'files': files,
            'current_path': path,
            'parent_path': parent_path,
            'sort_method': sort_method
        })
        
    except Exception as e:
        return web.json_response({'error': str(e)}, status=500)


@PromptServer.instance.routes.get("/ib_custom_nodes/get_image_preview")
async def get_image_preview(request):
    """Get a preview of an image at the given path"""
    try:
        image_path = request.query.get('path', '')
        
        if not image_path or not os.path.exists(image_path):
            return web.json_response({'error': 'Invalid image path'}, status=400)
        
        img = Image.open(image_path)
        img = ImageOps.exif_transpose(img)
        
        max_size = (512, 512)
        img.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        from io import BytesIO
        import base64
        
        buffer = BytesIO()
        img.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()
        
        return web.json_response({
            'preview': f'data:image/png;base64,{img_str}',
            'width': img.width,
            'height': img.height
        })
        
    except Exception as e:
        return web.json_response({'error': str(e)}, status=500)
        
@PromptServer.instance.routes.get("/ib_custom_nodes/serve_image")
async def serve_image(request):
    """Serve image file directly"""
    try:
        image_path = request.query.get('path', '')
        
        if not image_path or not os.path.exists(image_path):
            return web.Response(status=404, text='Image not found')
        
        response = web.FileResponse(image_path)
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = '*'
        return response
        
    except Exception as e:
        return web.Response(status=500, text=f'Error serving image: {str(e)}')