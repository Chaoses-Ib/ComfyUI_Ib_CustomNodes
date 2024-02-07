import torch

import hashlib
from pathlib import Path
from typing import Iterable

from PIL import Image, ImageOps
import numpy as np

import folder_paths

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

    CATEGORY = 'image'

    def pil_images_to_images(images: Iterable[Image.Image]) -> torch.Tensor:
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

    CATEGORY = 'image'

    def pil_images_to_masks(images: Iterable[Image.Image]) -> torch.Tensor:
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

    CATEGORY = 'image'

    def images_to_pil_images(self, images: torch.Tensor) -> list[Image.Image]:
        pil_images = []
        for image in images:
            i = 255. * image.cpu().numpy()
            img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
            pil_images.append(img)
        return (pil_images,)