class BatchFromAIMMS:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "sqlite_file": ("STRING", {"default": ""}),
                "table_name": ("STRING", {"default": "shots"}),
            }
        }

    RETURN_TYPES = ("STRING",)
    FUNCTION = "run"
    CATEGORY = "AIMMS/Batch"

    def run(self, sqlite_file, table_name):
        # TODO: implement SQLite logic
        return ("",)

