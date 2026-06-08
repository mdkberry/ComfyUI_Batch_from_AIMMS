"""
ComfyUI_Batch_from_CSV
A custom ComfyUI node for batch processing workflows from a CSV file.
Supports: prompts, three reference images (IMAGE), a video file path (STRING),
LoRA file paths (STRING), an audio VO file path (STRING), and various text
fields — all driven row-by-row via the seed widget.

CSV columns expected:

  shot_id          - unique identifier for the shot (STRING)
  order_number     - sort/execution order (STRING)
  shot_name        - label for the shot / output file naming (STRING)

  colour_scheme    - optional text describing colour palette (STRING)
  scene_context    - optional scene/environment description text (STRING)
  dialogue         - optional dialogue text (STRING)

  lora_1           - LoRA name as ComfyUI expects it (relative path within loras/ folder,
                     e.g. "LTX-23\ltx2.3-transition.safetensors") — plug into lora_name input
  lora_2           - second LoRA name (STRING)
  lora_3           - third LoRA name (STRING)

  ref_image_1      - path to a reference image (IMAGE tensor)
  ref_image_2      - path to a second reference image (IMAGE tensor)
  ref_image_3      - path to a third reference image (IMAGE tensor)

  video_file       - path to an .mp4 video file (STRING)

  audio_vo         - path to a voice-over audio file — mp3/m4a/flac/wav (STRING)
                     plug into an audio file loader node

  image_prompt     - positive prompt text for image generation (STRING)
  image_negative   - negative prompt text for image generation (STRING)
  video_prompt     - positive prompt text for video generation (STRING)
  video_negative   - negative prompt text for video generation (STRING)

  NOTE on prompt usage:
    image_prompt / image_negative are used for t2i and i2i workflows.
    video_prompt / video_negative are used for i2v, t2v, v2v workflows.
    colour_scheme, scene_context, dialogue are optional extra text fields
    the user can concatenate themselves in the workflow.
"""

import os
import csv
import numpy as np
import torch
from PIL import Image

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

AUDIO_EXTENSIONS = {".mp3", ".m4a", ".flac", ".wav"}


def _csv_dir() -> str:
    """Return the absolute path to the csv_files folder inside this node."""
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "csv_files")


def _list_csv_files() -> list:
    """Return a sorted list of CSV filenames found in csv_files/."""
    d = _csv_dir()
    if not os.path.isdir(d):
        return ["No CSV files found"]
    files = sorted(f for f in os.listdir(d) if f.lower().endswith(".csv"))
    return files if files else ["No CSV files found"]


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

    This function accepts whatever the CSV contains (absolute path or already-
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
            print(f"[ComfyUI_Batch_from_CSV] WARNING: could not load image '{norm}': {e}")
    if path and path.strip():
        print(
            f"[ComfyUI_Batch_from_CSV] WARNING: image not found or unreadable: '{path}'. "
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
            f"[ComfyUI_Batch_from_CSV] WARNING: audio_vo extension '{ext}' is not in "
            f"expected set {AUDIO_EXTENSIONS}. Path returned as-is: '{norm}'"
        )
    if not os.path.isfile(norm):
        print(f"[ComfyUI_Batch_from_CSV] WARNING: audio_vo file not found: '{norm}'")
    return norm


def _read_row(csv_filename: str, row_index: int) -> dict:
    """
    Read a single row (0-based index) from the given CSV file.
    Returns a dict keyed by column name.
    """
    filepath = os.path.join(_csv_dir(), csv_filename)
    if not os.path.isfile(filepath):
        print(f"[ComfyUI_Batch_from_CSV] ERROR: CSV file not found: {filepath}")
        return {}

    with open(filepath, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)

    if not rows:
        print(f"[ComfyUI_Batch_from_CSV] WARNING: CSV file is empty: {filepath}")
        return {}

    # Wrap around so the node loops cleanly when seed > number of rows
    idx = row_index % len(rows)
    return rows[idx]


def _build_info(row: dict, row_index: int) -> str:
    """Build a human-readable summary of the current row for debug/metadata embedding."""
    lines = [f"Row index : {row_index}"]
    for key, val in row.items():
        if val and str(val).strip():
            lines.append(f"{key:20s}: {str(val).strip()}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Node class
# ---------------------------------------------------------------------------

class BatchFromCSV:
    """
    Reads one row per execution from a CSV file (selected by seed / batch counter).

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
    image_prompt     STRING  – positive prompt for image generation (t2i / i2i)
    image_negative   STRING  – negative prompt for image generation
    video_prompt     STRING  – positive prompt for video generation (i2v / t2v / v2v)
    video_negative   STRING  – negative prompt for video generation
    row_index        INT     – the actual row that was loaded (useful for debugging)
    info             STRING  – full row summary — pipe into a Show Any node
    """

    CATEGORY = "Batch/CSV"
    FUNCTION = "load_row"

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
        "image_prompt",
        "image_negative",
        "video_prompt",
        "video_negative",
        "row_index",
        "info",
    )

    @classmethod
    def INPUT_TYPES(cls):
        csv_files = _list_csv_files()
        return {
            "required": {
                "csv_file": (csv_files, {"default": csv_files[0]}),
                "seed": (
                    "INT",
                    {
                        "default": 1,
                        "min": 0,
                        "max": 0xFFFFFFFFFFFFFFFF,
                        "control_after_generate": "increment",
                    },
                ),
            }
        }

    # Tell ComfyUI this node is NOT purely deterministic (seed changes output)
    @classmethod
    def IS_CHANGED(cls, csv_file, seed):
        return float(seed)

    def load_row(self, csv_file: str, seed: int):
        blank = torch.zeros(1, 64, 64, 3, dtype=torch.float32)

        if csv_file == "No CSV files found":
            print("[ComfyUI_Batch_from_CSV] ERROR: No CSV file selected or available.")
            return ("", "", "", "", "", "", "", "", "", blank, blank, blank,
                    "", "", "", "", "", "", 0, "No CSV file loaded.")

        row = _read_row(csv_file, seed)

        if not row:
            return ("", "", "", "", "", "", "", "", "", blank, blank, blank,
                    "", "", "", "", "", "", seed, f"Row {seed}: empty or file not found.")

        def g(key):
            """Get a stripped string value from the row, defaulting to empty."""
            return str(row.get(key, "") or "").strip()

        # Identity / metadata fields
        shot_id      = g("shot_id")
        order_number = g("order_number")
        shot_name    = g("shot_name")

        # Optional text fields (user concatenates these in workflow)
        colour_scheme = g("colour_scheme")
        scene_context = g("scene_context")
        dialogue      = g("dialogue")

        # LoRA names — returned as relative paths for ComfyUI's LoRA loader 'lora_name' input.
        # ComfyUI expects the path relative to its models/loras/ folder (e.g. "LTX-23\foo.safetensors").
        # _lora_relative_name() strips any absolute prefix up to and including the 'loras/' segment,
        # and passes through values that are already relative / bare names unchanged.
        lora_1 = _lora_relative_name(g("lora_1"))
        lora_2 = _lora_relative_name(g("lora_2"))
        lora_3 = _lora_relative_name(g("lora_3"))

        # Reference images — loaded as ComfyUI IMAGE tensors
        ref_image_1 = _load_image_as_tensor(g("ref_image_1"))
        ref_image_2 = _load_image_as_tensor(g("ref_image_2"))
        ref_image_3 = _load_image_as_tensor(g("ref_image_3"))

        # Video path
        video_file = _normalise_path(g("video_file"))
        if video_file and not os.path.isfile(video_file):
            print(f"[ComfyUI_Batch_from_CSV] WARNING: video_file not found: '{video_file}'")

        # Audio VO path — validated for extension and existence
        audio_vo = _validate_audio_path(g("audio_vo"))

        # Prompt fields
        image_prompt = g("image_prompt")
        image_negative = g("image_negative")
        video_prompt = g("video_prompt")
        video_negative = g("video_negative")

        row_index = seed  # exposed so users can pipe it for debugging
        info = _build_info(row, seed)

        print(
            f"[ComfyUI_Batch_from_CSV] Loaded row {seed}: "
            f"shot_id='{shot_id}' | shot_name='{shot_name}' | order='{order_number}' | "
            f"video='{video_file}' | audio_vo='{audio_vo}' | "
            f"lora_1='{lora_1}' | lora_2='{lora_2}' | lora_3='{lora_3}'"
        )

        return (
            shot_id,
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

BatchFromCSV.RETURN_TYPES = (
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
    "BatchFromCSV": BatchFromCSV,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "BatchFromCSV": "Batch from CSV 📋",
}