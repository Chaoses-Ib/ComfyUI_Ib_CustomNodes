from .image import *

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']

NODE_CLASS_MAPPINGS = {
    'LoadImageFromPath': LoadImageFromPath,
    'PILToImage': PILToImage,
    'PILToMask': PILToMask,
    'ImageToPIL': ImageToPIL,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    'LoadImageFromPath': 'Load Image From Path',
    'PILToImage': 'PIL To Image',
    'PILToMask': 'PIL To Mask',
    'ImageToPIL': 'Image To PIL',
}

print("\033[34mIb Custom Nodes: \033[92mLoaded\033[0m")
