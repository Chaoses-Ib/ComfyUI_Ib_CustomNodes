from .image import LoadImageFromPath, PILToImage, PILToMask, ImageToPIL

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

WEB_DIRECTORY = "./web"

__version__ = "0.2.3"
__author__ = "Chaoses-Ib"
__title__ = "ComfyUI_Ib_CustomNodes"
__description__ = "Loads images, without creating a copy of the image to the input folder in your ComfyUI install directory."
__license__ = "MIT"
__changelog__ = [
    "v0.2.3 - Added a browse button and a image preview."
]

__all__ = ['NODE_CLASS_MAPPINGS',
    'NODE_DISPLAY_NAME_MAPPINGS',
    '__version__',
    '__author__',
    '__title__',
    '__description__'
]

print("\033[34mIb Custom Nodes: \033[92mLoaded\033[0m")
