from .image import LoadImageFromPath, LoadImageFromPathEnhanced, PILToImage, PILToMask, ImageToPIL

__all__ = ['NODE_CLASS_MAPPINGS', 'NODE_DISPLAY_NAME_MAPPINGS']

NODE_CLASS_MAPPINGS = {
    'LoadImageFromPath': LoadImageFromPath,
    'LoadImageFromPathEnhanced': LoadImageFromPathEnhanced,
    'PILToImage': PILToImage,
    'PILToMask': PILToMask,
    'ImageToPIL': ImageToPIL,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    'LoadImageFromPath': 'Load Image From Path',
    'LoadImageFromPathEnhanced': 'Load Image From Path (Enhanced)',
    'PILToImage': 'PIL To Image',
    'PILToMask': 'PIL To Mask',
    'ImageToPIL': 'Image To PIL',
}

WEB_DIRECTORY = "./web"

print("\033[34mIb Custom Nodes: \033[92mLoaded\033[0m")
