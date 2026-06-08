from .batch_from_csv_node import BatchFromCSV
from .batch_from_aimms_node import BatchFromAIMMS

NODE_CLASS_MAPPINGS = {
    "BatchFromCSV": BatchFromCSV,
    "BatchFromAIMMS": BatchFromAIMMS,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "BatchFromCSV": "Batch From CSV",
    "BatchFromAIMMS": "Batch From AIMMS",
}

WEB_DIRECTORY = "./web"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]