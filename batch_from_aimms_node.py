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

Additional media files are retrieved from the takes table based on shot_id and starred values.

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
import time
import json
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


def _get_media_files(db_path: str, shot_id: int):
    """
    Retrieve media files from the takes table for a given shot_id.
    Returns a dictionary with paths for ref_image_1, ref_image_2, ref_image_3,
    video_file, and audio_vo.
    """
    media_files = {
        "ref_image_1": "",
        "ref_image_2": "",
        "ref_image_3": "",
        "video_file": "",
        "audio_vo": ""
    }
    
    if not os.path.isfile(db_path):
        return media_files
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get all takes for this shot_id
        cursor.execute("SELECT take_type, file_path, starred FROM takes WHERE shot_id = ?", (shot_id,))
        takes = cursor.fetchall()
        
        # Extract project root path from db_path
        # The db_path is expected to be something like: M:/AIMMS_Projects/project_BlackMagic/data/shots.db
        # We need to get: M:/AIMMS_Projects/project_BlackMagic to construct full paths
        project_root = os.path.dirname(os.path.dirname(db_path))
        
        for take in takes:
            take_type = take["take_type"]
            file_path = take["file_path"]
            starred = take["starred"]
            
            # Skip if file_path is empty
            if not file_path or not file_path.strip():
                continue
                
            # Construct full path
            full_path = os.path.join(project_root, file_path)
            
            # Check file size - skip if zero (placeholder)
            if os.path.isfile(full_path) and os.path.getsize(full_path) == 0:
                continue
                
            # Handle different take types
            if take_type == "base_image":
                if starred == 1:
                    media_files["ref_image_1"] = full_path
                elif starred == 2:
                    media_files["ref_image_2"] = full_path
                elif starred == 3:
                    media_files["ref_image_3"] = full_path
                # If starred is 0, it could still qualify as ref_image_1 if no other starred=1 exists
                elif starred == 0 and not media_files["ref_image_1"]:
                    media_files["ref_image_1"] = full_path
                    
            elif take_type == "final_video":
                # Video files can have starred=0 or 1, include if valid
                if not media_files["video_file"] or starred == 1:
                    media_files["video_file"] = full_path
                    
            elif take_type == "audio_vo":
                # Audio files include if present
                if not media_files["audio_vo"]:
                    media_files["audio_vo"] = full_path
                    
    except Exception as e:
        print(f"[ComfyUI_Batch_from_AIMMS] ERROR: Failed to retrieve media files: {e}")
    finally:
        if conn:
            conn.close()
            
    return media_files


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


def _get_state_path():
    """Returns path to state JSON in the custom node's own directory."""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "batch_aimms_state.json")


def _load_state(shot_ids_str: str) -> dict:
    """Load state JSON, resetting if shot_id list has changed."""
    state_path = _get_state_path()
    default = {"index": 0, "last_shot_ids": shot_ids_str, "reset_consumed": False}
    if not os.path.isfile(state_path):
        return default
    try:
        with open(state_path, "r") as f:
            state = json.load(f)
        # If the shot_id list changed, treat as fresh start
        if state.get("last_shot_ids") != shot_ids_str:
            return default
        return state
    except Exception:
        return default


def _save_state(state: dict):
    state_path = _get_state_path()
    try:
        with open(state_path, "w") as f:
            json.dump(state, f)
    except Exception as e:
        print(f"[ComfyUI_Batch_from_AIMMS] WARNING: Could not save state: {e}")


def _build_info(row: dict, shot_id: int, media_files: dict) -> str:
    """Build a human-readable summary of the current shot for debug/metadata embedding."""
    lines = [f"Shot ID : {shot_id}"]
    for key, val in row.items():
        if val and str(val).strip():
            lines.append(f"{key:20s}: {str(val).strip()}")
    
    # Add media file paths to the info output
    lines.append("")
    lines.append("Media Files:")
    for key, path in media_files.items():
        if path and path.strip():
            lines.append(f"{key:20s}: {str(path).strip()}")
    
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Node class
# ---------------------------------------------------------------------------

class BatchFromAIMMS:
    DESCRIPTION ="""
    ## Description
    A custom ComfyUI node for batch processing workflows from an AIMMS SQLite database. Each execution loads one shot based on the shot_id and provides all relevant data for AI image or video generation.

    ## Inputs
    - **db_path** (STRING): Path to the AIMMS SQLite database file
    - **shot_id** (STRING): Comma-separated list of shot IDs to process (e.g. '1,2,5,3')

    ## Database Fields Mapping (AIMMS shots.db)
    - **shot_id** → shot_id (STRING)
    - **order_number** → order_number (STRING)
    - **shot_name** → shot_name (STRING)
    - **colour_scheme** → colour_scheme_image (STRING)
    - **scene_context** → time_of_day, location, country, year (STRING)
    - **dialogue** → dialogue (STRING)
    - **lora_1/2/3** → lora_1/2/3 (STRING)
    - **ref_image_1/2/3** → (base_image (FF/MF/LF), starred=1/2/3) (IMAGE)
    - **video_file** → (starred video URL, starred=1) (STRING)
    - **audio_vo** → (audio_vo URL) (STRING)
    - **image_prompt** → image_prompt (STRING)
    - **image_negative** → image_negative (STRING)
    - **video_prompt** → video_prompt (STRING)
    - **video_negative** → video_negative (STRING)
    - **row_index** → shot_id (INT)
    - **info** → full shot summary (STRING)
    """

    CATEGORY = "Batch/AIMMS"
    FUNCTION = "load_shot"

    # IMPORTANT:
    # ComfyUI requires RETURN_TYPES to be a valid tuple at class load time
    # or the help popup (?) will NOT appear.
    # This placeholder is overwritten later in the file.
    RETURN_TYPES = ("STRING",)

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
        "image_prompt",
        "image_negative",
        "video_prompt",
        "video_negative",
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
            },
            "optional": {
                "reset_index": (
                    "BOOLEAN",
                    {
                        "default": False,
                        "tooltip": "Toggle ON to restart shot_id stepping from the first entry on the next run. Automatically self-locks after firing so the batch continues without interruption. Toggle OFF to re-arm for future resets."
                    }
                ),
            }
        }


    def load_shot(self, db_path: str, shot_id: str, reset_index: bool = False):
        blank = torch.zeros(1, 64, 64, 3, dtype=torch.float32)

        # Validate database path
        if not os.path.isfile(db_path):
            print(f"[ComfyUI_Batch_from_AIMMS] ERROR: Database file not found at: {db_path}")
            return ("", "", "", "", "", "", "", "", "", blank, blank, blank,
                    "", "", "", "", "", "", 0, "Database file not found.")
        
        # Parse shot_ids
        shot_ids = [int(x.strip()) for x in shot_id.split(",") if x.strip()]
        shot_ids_str = shot_id.strip()

        # Load persistent state
        state = _load_state(shot_ids_str)

        # Handle reset_index toggle with self-lock logic
        if reset_index:
            if not state.get("reset_consumed", False):
                # First run with reset=True: fire the reset
                state["index"] = 0
                state["reset_consumed"] = True
                print("[ComfyUI_Batch_from_AIMMS] Reset fired: stepping from shot_id index 0")
            # else: reset already consumed this session, continue stepping normally
        else:
            # Toggle is OFF: re-arm so it will fire again next time user turns it ON
            state["reset_consumed"] = False

        # Clamp index in case shot_id list shrank
        if state["index"] >= len(shot_ids):
            state["index"] = 0

        # Select current shot
        current_index = state["index"]
        current_shot_id = shot_ids[current_index]

        # Advance index for next run (wraps around)
        state["index"] = (current_index + 1) % len(shot_ids)
        state["last_shot_ids"] = shot_ids_str
        _save_state(state)
        
        print(f"[ComfyUI_Batch_from_AIMMS] Run {current_index + 1}/{len(shot_ids)}: shot_id={current_shot_id}")
        
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
        dialogue      = g("dialogue")
        
        # Create scene_context by concatenating time_of_day, location, country, and year fields
        scene_parts = [
            g("time_of_day"),
            g("location"),
            g("country"),
            g("year")
        ]
        
        # Filter out empty strings and join with comma delimiters
        scene_context = ", ".join(part for part in scene_parts if part and part.strip())

        # LoRA names — returned as relative paths for ComfyUI's LoRA loader 'lora_name' input.
        lora_1 = _lora_relative_name(g("lora_1"))
        lora_2 = _lora_relative_name(g("lora_2"))
        lora_3 = _lora_relative_name(g("lora_3"))

        # Get media files from takes table
        media_files = _get_media_files(db_path, current_shot_id)
        
        # Reference images — loaded as ComfyUI IMAGE tensors
        ref_image_1 = _load_image_as_tensor(media_files["ref_image_1"])
        ref_image_2 = _load_image_as_tensor(media_files["ref_image_2"])
        ref_image_3 = _load_image_as_tensor(media_files["ref_image_3"])

        # Video path
        video_file = _normalise_path(media_files["video_file"])
        if video_file and not os.path.isfile(video_file):
            print(f"[ComfyUI_Batch_from_AIMMS] WARNING: video_file not found: '{video_file}'")

        # Audio VO path — validated for extension and existence
        audio_vo = _validate_audio_path(media_files["audio_vo"])

        # Prompt fields
        image_prompt = g("image_prompt")
        image_negative = g("image_negative")
        video_prompt = g("video_prompt")
        video_negative = g("video_negative")

        row_index = current_shot_id  # exposed so users can pipe it for debugging
        info = _build_info(row, current_shot_id, media_files)

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
            image_prompt,
            image_negative,
            video_prompt,
            video_negative,
            row_index,
            info,
        )

    @classmethod
    def IS_CHANGED(cls, db_path, shot_id, reset_index=False):
        return float(time.time())
        # Always forces re-execution — required for stateful stepping to work.
        # Each queue slot = one step through the shot_id list.


# ---------------------------------------------------------------------------
# Set RETURN_TYPES dynamically so lora_1/2/3 outputs carry the COMBO type
# that ComfyUI's LoRA Loader expects on its lora_name input.
#
# A COMBO input/output in ComfyUI is identified by the *list object* itself —
# not by the string "COMBO" or "STRING". The frontend checks connector
# compatibility by comparing the type token: if both sides are lists, they
# match as COMBO. So we must use the same list that folder_paths provides.
# ---------------------------------------------------------------------------
  
# Initialize with empty list as fallback
_loras = []

# Try to get the actual LoRA list from ComfyUI's folder_paths
try:
    import folder_paths
    _loras = folder_paths.get_filename_list("loras")
except Exception as e:
    # Log a warning if we can't get the LoRA list, but continue with empty list
    print(f"[ComfyUI_Batch_from_AIMMS] WARNING: Could not load LoRA list from folder_paths: {e}")
    print("[ComfyUI_Batch_from_AIMMS] LoRA connectors will show as empty strings. Make sure your LoRA folder is properly configured.")

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
    "STRING",  # image_prompt
    "STRING",  # image_negative
    "STRING",  # video_prompt
    "STRING",  # video_negative
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