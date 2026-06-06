"""
ComfyUI_Batch_from_AIMMS
A custom ComfyUI node for batch processing workflows from an AIMMS SQLite database.
Supports: prompts, three reference images (IMAGE), a video file path (STRING),
LoRA file paths (STRING), an audio VO file path (STRING), and various text
fields — all driven by shot_id selection provided by the user.

Database columns expected (from shots table):

  shot_id          - unique identifier for the shot (INTEGER PRIMARY KEY)
  order_number     - sort/execution order (INTEGER)
  shot_name        - label for the shot / output file naming (TEXT)
  
  description      - optional scene/environment description text (TEXT)
  dialogue         - optional dialogue text (TEXT)
  image_prompt     - positive prompt text for image generation (TEXT)
  image_negative   - negative prompt text for image generation (TEXT)
  colour_scheme_image - optional text describing colour palette (TEXT)
  video_prompt     - positive prompt text for video generation (TEXT)
  video_negative   - negative prompt text for video generation (TEXT)
  
  lora_1           - LoRA name as ComfyUI expects it (relative path within loras/ folder,
                     e.g. "LTX-23\ltx2.3-transition.safetensors") — plug into lora_name input
  lora_2           - second LoRA name (TEXT)
  lora_3           - third LoRA name (TEXT)

  NOTE on prompt usage:
    image_prompt / image_negative are used for t2i and i2i workflows.
    video_prompt / video_negative are used for i2v, t2v, v2v workflows.
    colour_scheme_image, description, dialogue are optional extra text fields
    the user can concatenate themselves in the workflow.
"""

import os
import sqlite3
import numpy as np
import torch
from PIL import Image

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

AUDIO_EXTENSIONS = {".mp3", ".m4a", ".flac", ".wav"}


def _normalise_path(raw: str) -> str:
    """
    Convert a Windows-style path (with backslashes) to whatever the OS needs.
    Works transparently on both Windows and Linux.
    """
    return os.path.normpath(raw.strip()) if raw and raw.strip() else ""


def _lora_relative_name(raw: str) -> str:
    """
    ComfyUI's LoRA loader 'lora_name' widget expects a path relative to the
    ComfyUI models/loras/ folder — exactly as it appears in widgets_values,
    e.g. "LTX-23\\ltx2.3-transition.safetensors".

    This function accepts whatever the database contains (absolute path or already-
    relative name) and returns the correctly trimmed relative form:

      Absolute:  "M:\\...\\models\\loras\\LTX-23\\foo.safetensors"
                 → "LTX-23\\foo.safetensors"
      Already relative / bare name:  "LTX-23\\foo.safetensors"
                 → "LTX-23\\foo.safetensors"   (unchanged)
      Empty / blank → ""

    The separator in the returned string always matches the OS convention so
    ComfyUI can look it up in its internal model list on any platform.
    """
    if not raw or not raw.strip():
        return ""

    # Normalise separators to the OS style first
    norm = os.path.normpath(raw.strip())

    # Look for a 'loras' folder segment in the path and take everything after it.
    # os.path.normpath uses os.sep, so split on that.
    parts = norm.split(os.sep)
    # Search from the right so we match the last 'loras' segment in the path
    # (handles e.g. a user whose home dir happens to contain the word 'loras').
    for i in range(len(parts) - 1, -1, -1):
        if parts[i].lower() == "loras":
            # Everything after the 'loras' segment
            relative_parts = parts[i + 1:]
            if relative_parts:
                return os.path.join(*relative_parts)
            break

    # No 'loras' segment found — assume the value is already relative / a bare name
    return norm


def _load_image_as_tensor(path: str):
    """
    Load a PNG/JPG/etc. from *path* and return it as a ComfyUI IMAGE tensor
    [1, H, W, 3] float32 in [0, 1].
    Returns a 1×64×64 black image if the file is missing or unreadable.
    """
    norm = _normalise_path(path)
    if norm and os.path.isfile(norm):
        try:
            img = Image.open(norm).convert("RGB")
            arr = np.array(img).astype(np.float32) / 255.0
            return torch.from_numpy(arr).unsqueeze(0)  # [1, H, W, 3]
        except Exception as e:
            print(f"[ComfyUI_Batch_from_AIMMS] WARNING: could not load image '{norm}': {e}")
    if path and path.strip():
        print(
            f"[ComfyUI_Batch_from_AIMMS] WARNING: image not found or unreadable: '{path}'. "
            "Returning blank placeholder."
        )
    arr = np.zeros((64, 64, 3), dtype=np.float32)
    return torch.from_numpy(arr).unsqueeze(0)


def _validate_audio_path(path: str) -> str:
    """
    Normalise and validate an audio file path.
    Logs a warning if the file is missing or has an unexpected extension.
    Returns the normalised path string regardless (empty string if input blank).
    """
    norm = _normalise_path(path)
    if not norm:
        return ""
    ext = os.path.splitext(norm)[1].lower()
    if ext not in AUDIO_EXTENSIONS:
        print(
            f"[ComfyUI_Batch_from_AIMMS] WARNING: audio_vo extension '{ext}' is not in "
            f"expected set {AUDIO_EXTENSIONS}. Path returned as-is: '{norm}'"
        )
    if not os.path.isfile(norm):
        print(f"[ComfyUI_Batch_from_AIMMS] WARNING: audio_vo file not found: '{norm}'")
    return norm


def _read_shot_from_db(db_path: str, shot_id: int) -> dict:
    """
    Read a single shot from the given SQLite database based on shot_id.
    Returns a dict keyed by column name.
    """
    if not os.path.isfile(db_path):
        print(f"[ComfyUI_Batch_from_AIMMS] ERROR: Database file not found: {db_path}")
        return {}

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row  # Access columns by name
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM shots WHERE shot_id = ?", (shot_id,))
        row = cursor.fetchone()
        
        if row:
            return dict(row)
        else:
            print(f"[ComfyUI_Batch_from_AIMMS] WARNING: Shot with ID {shot_id} not found in database")
            return {}
            
    except Exception as e:
        print(f"[ComfyUI_Batch_from_AIMMS] ERROR: Database query failed: {e}")
        return {}
    finally:
        if conn:
            conn.close()


def _build_info(row: dict, shot_id: int) -> str:
    """Build a human-readable summary of the current shot for debug/metadata embedding."""
    lines = [f"Shot ID : {shot_id}"]
    for key, val in row.items():
        if val and str(val).strip():
            lines.append(f"{key:20s}: {str(val).strip()}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Node class
# ---------------------------------------------------------------------------

class BatchFromAIMMS:
    """
    Reads one shot per execution from an AIMMS SQLite database (selected by shot_id).

    Outputs
    -------
    shot_id          STRING  – unique shot identifier
    order_number     STRING  – execution order field
    shot_name        STRING  – shot label for output file naming
    colour_scheme    STRING  – colour palette description (optional, concatenate in workflow)
    scene_context    STRING  – scene/environment description (optional)
    dialogue         STRING  – dialogue text (optional)
    lora_1           STRING  – path to LoRA 1 .safetensors (plug into LoRA loader path)
    lora_2           STRING  – path to LoRA 2 .safetensors
    lora_3           STRING  – path to LoRA 3 .safetensors
    ref_image_1      IMAGE   – first reference image tensor
    ref_image_2      IMAGE   – second reference image tensor
    ref_image_3      IMAGE   – third reference image tensor
    video_file       STRING  – normalised path to the video file
    audio_vo         STRING  – path to VO audio file (mp3/m4a/flac/wav), plug into audio loader
    positive_image   STRING  – positive prompt for image generation (t2i / i2i)
    negative_image   STRING  – negative prompt for image generation
    positive_video   STRING  – positive prompt for video generation (i2v / t2v / v2v)
    negative_video   STRING  – negative prompt for video generation
    row_index        INT     – the actual shot_id that was loaded (useful for debugging)
    info             STRING  – full shot summary — pipe into a Show Any node
    """

    CATEGORY = "Batch/AIMMS"
    FUNCTION = "load_shot"

    # RETURN_TYPES is populated after class definition (see bottom of file)
    # so that lora_1/2/3 use the live folder_paths lora list — which gives
    # them a COMBO connector type that plugs into the LoRA Loader's lora_name.
    RETURN_TYPES = None  # overwritten below

    RETURN_NAMES = (
        "shot_id",
        "order_number",
        "shot_name",
        "colour_scheme",
        "scene_context",
        "dialogue",
        "lora_1",
        "lora_2",
        "lora_3",
        "ref_image_1",
        "ref_image_2",
        "ref_image_3",
        "video_file",
        "audio_vo",
        "positive_image",
        "negative_image",
        "positive_video",
        "negative_video",
        "row_index",
        "info",
    )

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "db_path": (
                    "STRING",
                    {
                        "default": "M:\\AIMMS_Projects\\project_BlackMagic\\data\\shots.db",
                        "tooltip": "Path to the AIMMS SQLite database file"
                    }
                ),
                "shot_id": (
                    "STRING",
                    {
                        "default": "1",
                        "tooltip": "Comma-separated list of shot IDs to process (e.g. '1,2,5,3')"
                    }
                ),
            }
        }

    def load_shot(self, db_path: str, shot_id: str):
        blank = torch.zeros(1, 64, 64, 3, dtype=torch.float32)

        # Validate database path
        if not os.path.isfile(db_path):
            print(f"[ComfyUI_Batch_from_AIMMS] ERROR: Database file not found at: {db_path}")
            return ("", "", "", "", "", "", "", "", "", blank, blank, blank,
                    "", "", "", "", "", "", 0, "Database file not found.")
        
        # Parse the shot_id string
        try:
            shot_ids = [int(id.strip()) for id in shot_id.split(",")]
        except ValueError:
            print(f"[ComfyUI_Batch_from_AIMMS] ERROR: Invalid shot_id format. Expected comma-separated integers.")
            return ("", "", "", "", "", "", "", "", "", blank, blank, blank,
                    "", "", "", "", "", "", 0, "Invalid shot_id format.")
        
        # Process the first shot_id in the list (we'll extend to support sequences later)
        current_shot_id = shot_ids[0]
        
        # Get shot data from database
        row = _read_shot_from_db(db_path, current_shot_id)

        if not row:
            return ("", "", "", "", "", "", "", "", "", blank, blank, blank,
                    "", "", "", "", "", "", current_shot_id, f"Shot {current_shot_id}: not found in database.")

        def g(key):
            """Get a stripped string value from the row, defaulting to empty."""
            return str(row.get(key, "") or "").strip()

        # Identity / metadata fields
        shot_id_val      = str(current_shot_id)
        order_number = g("order_number")
        shot_name    = g("shot_name")

        # Optional text fields (user concatenates these in workflow)
        colour_scheme = g("colour_scheme_image")  # Note: using colour_scheme_image from DB
        scene_context = g("description")  # Using description from DB as scene_context
        dialogue      = g("dialogue")

        # LoRA names — returned as relative paths for ComfyUI's LoRA loader 'lora_name' input.
        lora_1 = _lora_relative_name(g("lora_1"))
        lora_2 = _lora_relative_name(g("lora_2"))
        lora_3 = _lora_relative_name(g("lora_3"))

        # Reference images — loaded as ComfyUI IMAGE tensors
        # Note: Currently not directly supported in the DB schema, placeholder for future implementation
        ref_image_1 = blank  # Placeholder - no direct equivalent in DB
        ref_image_2 = blank  # Placeholder - no direct equivalent in DB
        ref_image_3 = blank  # Placeholder - no direct equivalent in DB

        # Video path - Note: Not directly supported in current DB schema
        video_file = ""
        # if video_file and not os.path.isfile(video_file):
        #     print(f"[ComfyUI_Batch_from_AIMMS] WARNING: video_file not found: '{video_file}'")

        # Audio VO path — validated for extension and existence
        # Note: Not directly supported in current DB schema
        audio_vo = ""

        # Prompt fields
        positive_image = g("image_prompt")
        negative_image = g("image_negative")
        positive_video = g("video_prompt")
        negative_video = g("video_negative")

        row_index = current_shot_id  # exposed so users can pipe it for debugging
        info = _build_info(row, current_shot_id)

        print(
            f"[ComfyUI_Batch_from_AIMMS] Loaded shot {current_shot_id}: "
            f"shot_id='{shot_id_val}' | shot_name='{shot_name}' | order='{order_number}' | "
            f"video='{video_file}' | audio_vo='{audio_vo}' | "
            f"lora_1='{lora_1}' | lora_2='{lora_2}' | lora_3='{lora_3}'"
        )

        return (
            shot_id_val,
            order_number,
            shot_name,
            colour_scheme,
            scene_context,
            dialogue,
            lora_1,
            lora_2,
            lora_3,
            ref_image_1,
            ref_image_2,
            ref_image_3,
            video_file,
            audio_vo,
            positive_image,
            negative_image,
            positive_video,
            negative_video,
            row_index,
            info,
        )

    @classmethod
    def IS_CHANGED(cls, db_path, shot_id):
        # Return a float to ensure ComfyUI handles this as a change
        try:
            shot_ids = [int(id.strip()) for id in shot_id.split(",")]
            return float(shot_ids[0])
        except ValueError:
            return 1.0  # Default to 1.0 if there's an error


# ---------------------------------------------------------------------------
# Set RETURN_TYPES dynamically so lora_1/2/3 outputs carry the COMBO type
# that ComfyUI's LoRA Loader expects on its lora_name input.
#
# A COMBO input/output in ComfyUI is identified by the *list object* itself —
# not by the string "COMBO" or "STRING". The frontend checks connector
# compatibility by comparing the type token: if both sides are lists, they
# match as COMBO. So we must use the same list that folder_paths provides.
# ---------------------------------------------------------------------------

try:
    import folder_paths as _fp
    _loras = _fp.get_filename_list("loras")
except Exception:
    _loras = []

BatchFromAIMMS.RETURN_TYPES = (
    "STRING",  # shot_id
    "STRING",  # order_number
    "STRING",  # shot_name
    "STRING",  # colour_scheme
    "STRING",  # scene_context
    "STRING",  # dialogue
    _loras,    # lora_1  — COMBO, connects directly to LoRA Loader lora_name
    _loras,    # lora_2
    _loras,    # lora_3
    "IMAGE",   # ref_image_1
    "IMAGE",   # ref_image_2
    "IMAGE",   # ref_image_3
    "STRING",  # video_file
    "STRING",  # audio_vo
    "STRING",  # positive_image
    "STRING",  # negative_image
    "STRING",  # positive_video
    "STRING",  # negative_video
    "INT",     # row_index
    "STRING",  # info
)

# ---------------------------------------------------------------------------
# ComfyUI registration
# ---------------------------------------------------------------------------

NODE_CLASS_MAPPINGS = {
    "BatchFromAIMMS": BatchFromAIMMS,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "BatchFromAIMMS": "Batch from AIMMS 🎬",
}