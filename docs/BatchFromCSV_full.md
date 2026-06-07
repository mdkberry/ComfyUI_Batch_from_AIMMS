# ComfyUI_Batch_from_CSV 📋

***NOTE: This is part of a multi-node system for ComfyUI batch processing. The original CSV functionality remains unchanged, but the overall system now includes an additional node for processing directly from AIMMS databases. See the main [README.md](../README.md) for more information about the complete system.*** - Mark, 1st June 2026.

A custom ComfyUI node for **batch/bulk workflow processing** driven entirely from a CSV file.
Each row in the CSV represents one "shot" or generation job. The node reads one row per execution, making it perfect for automating large batches across any workflow type — t2i, i2i, i2v, t2v, v2v, or anything else.

---

**Example csv row**:

<img width="1860" height="115" alt="example-row-csv" src="https://github.com/user-attachments/assets/c902990c-c26e-4583-9d41-86e914439c1b" />


---

**ComfyUI custom node screenshot (v2.0.3)**

<img width="1842" height="921" alt="screenshot_connections_v2 0 3" src="https://github.com/user-attachments/assets/175497be-0583-4780-b032-e675227b2c39" />

_The above screenshot shows viable connections you can use and examples of connector outputs for reference. The actual node is on the left. It will load the rows from csv one at a time based on seed number relating to row number of the csv._

---

## ✨ Output Connectors

_(Field names relate to [AIMMS Storyboard Management](https://markdkberry.com/software/)  csv export feature)_

| Output connector  | Type   | Description |
|-------------------|--------|-------------|
| `shot_id`         | STRING | Unique shot identifier |
| `order_number`    | STRING | Execution order field |
| `shot_name`       | STRING | Label for the shot — use to rename your output file |
| `colour_scheme`   | STRING | Optional colour palette description — concatenate into prompt in workflow |
| `scene_context`   | STRING | Optional scene/environment description — concatenate into prompt in workflow |
| `dialogue`        | STRING | Optional dialogue text — concatenate into prompt in workflow e.g. VibeVoice, or add "quotes" if prompt driven |
| `lora_1`          | COMBO  | LoRA name — wire directly into the **lora_name** input on a standard LoRA Loader node |
| `lora_2`          | COMBO  | LoRA name — wire directly into a second LoRA Loader |
| `lora_3`          | COMBO  | LoRA name — wire directly into a third LoRA Loader |
| `ref_image_1`     | IMAGE  | First reference image loaded as a ComfyUI IMAGE tensor e.g FF |
| `ref_image_2`     | IMAGE  | Second reference image loaded as a ComfyUI IMAGE tensor e.g. MF |
| `ref_image_3`     | IMAGE  | Third reference image loaded as a ComfyUI IMAGE tensor e.g. LF |
| `video_file`      | STRING | Normalised path to your `.mp4` video file input for v2v based workflows |
| `audio_vo`        | STRING | Path to voice-over/dialogue audio file (`.mp3`, `.m4a`, `.flac`, `.wav`) — plug into **Audio File Loader** path input |
| `positive_image`  | STRING | Positive prompt text for image generation (t2i / i2i) |
| `negative_image`  | STRING | Negative prompt text for image generation |
| `positive_video`  | STRING | Positive prompt text for video generation (i2v / t2v / v2v) |
| `negative_video`  | STRING | Negative prompt text for video generation |
| `row_index`       | INT    | The row number that was loaded — handy for debugging |
| `info`            | STRING | Full row summary — pipe into a **Show Any** node to embed all row data in PNG workflow metadata |

**Notes on the text/prompt fields:**
- `positive_image` / `negative_image` — use for image-based workflows (t2i, i2i).
- `positive_video` / `negative_video` — use for video-based workflows (i2v, t2v, v2v).
- `colour_scheme`, `scene_context`, `dialogue` — optional helper fields. Concatenate any combination of these with a prompt in your workflow using a **String Concatenate** or similar node.
- LoRA and audio paths are returned as plain strings — blank if not set in the CSV. Connect to the appropriate loader's file path input.

---

## ✅ Key Features

- **Auto-scan** — any `.csv` file dropped in the `csv_files` folder is picked up automatically _(press R to refresh nodes if ComfyUI is open)_ .
- **Seed-driven batching** — set seed to *increment* and queue N runs to process N rows _(set to 1 will begin with row below column headings in csv)_ .
- **Loop-safe** — if seed exceeds the number of rows the node wraps around.
- **Graceful fallback** — missing image files produce a blank 64×64 black tensor (no crash); missing video/audio/LoRA paths log a warning and return the path string as-is.
- **Windows paths supported** — backslashes are normalised automatically on all OS.
- **Mixed workflow support** — image and video prompts are separate outputs; use whichever your workflow needs.

---

## 📥 Installation

### Manual (recommended)

1. For ComfyUI portable, git clone the `ComfyUI_Batch_from_AIMMS` folder into your ComfyUI `custom_nodes` directory:
   ```
   ComfyUI/custom_nodes/git clone https://github.com/mdkberry/ComfyUI_Batch_from_AIMMS.git
   ```
2. Restart ComfyUI.
3. The nodes appear under:
   - **Batch/CSV → Batch from CSV 📋** (for CSV processing)
   - **Batch/AIMMS → Batch from AIMMS 🎬** (for database processing)

### Via ComfyUI Manager

1. Open **ComfyUI Manager → Install via Git URL**.
2. Paste: `https://github.com/mdkberry/ComfyUI_Batch_from_AIMMS`
3. Restart ComfyUI.

---

## 📁 Folder Structure

```
ComfyUI/custom_nodes/ComfyUI_Batch_from_AIMMS/
│
├── csv_files/                  ← PUT YOUR CSV FILES HERE
│   ├── example_batch.csv
│   └── my_project.csv
│
├── __init__.py
├── batch_from_csv_node.py        ← CSV processing node
├── batch_from_aimms_node.py     ← AIMMS database processing node
├── pyproject.toml
├── README.md                    ← Main documentation for the entire system
└── docs/                        ← Detailed documentation for each node
    ├── BatchFromCSV_full.md          ← This file (CSV node documentation)
    └── BatchFromAIMMS_full.md        ← AIMMS node documentation
```

---

## 📝 CSV Format

Your CSV must use these **exact column headers** (order doesn't matter, all are optional except what your workflow needs):

| Column           | Type   | Description |
|------------------|--------|-------------|
| `shot_id`        | string | Unique identifier for the shot |
| `order_number`   | string | Execution order |
| `shot_name`      | string | Shot label for output file naming |
| `colour_scheme`  | string | Colour palette description (optional — concatenate in workflow) |
| `scene_context`  | string | Scene/environment description (optional) |
| `dialogue`       | string | Dialogue text (optional) |
| `lora_1`         | path   | Full path to a LoRA `.safetensors` file |
| `lora_2`         | path   | Full path to a second LoRA |
| `lora_3`         | path   | Full path to a third LoRA |
| `ref_image_1`    | path   | Full path to a reference image (PNG/JPG etc.) |
| `ref_image_2`    | path   | Full path to a second reference image |
| `ref_image_3`    | path   | Full path to a third reference image |
| `video_file`     | path   | Full path to a `.mp4` video file |
| `audio_vo`       | path   | Full path to a VO audio file (`.mp3`, `.m4a`, `.flac`, `.wav`) |
| `positive_image` | string | Positive prompt for image generation |
| `negative_image` | string | Negative prompt for image generation |
| `positive_video` | string | Positive prompt for video generation |
| `negative_video` | string | Negative prompt for video generation |

> **Tip:** Wrap cell values in double quotes if they contain commas.
> Leave a cell blank (not absent) if that field isn't needed for a particular row.

---

## 🚀 How to Use (Batch Generation)

### Step 1 — Add the node

Double-click the canvas → search for **"Batch from CSV"** (category: `Batch/CSV`).

For database processing from AIMMS, search for **"Batch from AIMMS"** (category: `Batch/AIMMS`).

### Step 2 — Select your CSV

Choose your file from the `csv_file` dropdown. Click **Refresh** in the ComfyUI menu if a newly added file doesn't appear.

### Step 3 — Connect outputs

| Node output       | Connect to |
|-------------------|------------|
| `positive_image`  | CLIP Text Encode (Positive) → text (for image workflows) |
| `negative_image`  | CLIP Text Encode (Negative) → text (for image workflows) |
| `positive_video`  | CLIP Text Encode (Positive) → text (for video workflows) |
| `negative_video`  | CLIP Text Encode (Negative) → text (for video workflows) |
| `colour_scheme`   | String Concatenate → input (combine with positive prompt as needed) |
| `scene_context`   | String Concatenate → input |
| `dialogue`        | String Concatenate → input |
| `lora_1/2/3`      | Standard **Load LoRA** node → `lora_name` input (wire directly — the output is COMBO type, matching the LoRA Loader's socket) |
| `ref_image_1/2/3` | Any node that accepts an IMAGE (IPAdapter, Load Image passthrough, etc.) |
| `video_file`      | Any node that accepts a STRING path (e.g. VHS Load Video → video path) |
| `audio_vo`        | Audio File Loader → file path input |
| `shot_name`       | Save Image → filename_prefix |
| `row_index`       | Optional — debug display or logging |
| `info`            | Show Any node → embed all row data in PNG metadata |

### Step 4 — Configure for batch

1. On the **Batch from CSV** node, set the `seed` widget control to **increment** and the seed to 1 _(starts at row below the header)_ .
2. In the ComfyUI menu set **Batch count** to the number of rows in your CSV _(excluding column header)_ .
3. Click **Queue Prompt** — ComfyUI will run once per row, automatically loading the next row each time.

---

## ❓ Troubleshooting

| Problem | Fix |
|---------|-----|
| No CSV files in dropdown | Make sure your `.csv` is inside `csv_files/`, then click **Refresh** or press R to reload nodes inside comfyUI  |
| Image outputs are blank/black | Check the path in the CSV is correct and the file exists |
| Video/audio path warning in console | The path is returned as a string even if missing — check spelling |
| LoRA not loading | Confirm the full path is correct; the node returns the path as a string only |
| Row not advancing | Ensure the seed is set to **increment**, not fixed |
| Info shows empty paths | Make sure the relevant columns exist in your CSV header row |
| No outputs being made after first run | Make sure you have set the seed back to 1 to start over |
| Second runs are slow | You may need to offload models between batch runs to clear the memory for VRAM and RAM |
| OOMs cause failures | Try setting switches for ComfyUI to aid with avoiding OOMS during batch processing and add memory clearing features to the workflow. |

---

## Integration with AIMMS Storyboard Management System

This node is specifically designed to work with [AIMMS Storyboard Management System (vrs 1.2.0)](https://markdkberry.com/software/) when exporting shots to CSV format. 

For direct integration with AIMMS project databases (without CSV export), see the companion node [Batch from AIMMS 🎬](BatchFromAIMMS.md).

_AIMMS (vrs 1.2.0) screenshot of shot details page, showing popup entries for shot management:_

<img width="1914" height="1076" alt="AIMMS_shot_details" src="https://github.com/user-attachments/assets/1e281f07-ffd1-4fa3-87fd-c9cc6906f54d" />

_AIMMS (vrs 1.2.0) screenshot of option to export shots to CSV format that works directly with this custom node:_

<img width="1916" height="1080" alt="AIMMS_export_to_csv" src="https://github.com/user-attachments/assets/4e472a5-b5b1-4322-835b-7b278ebafef4" />

---

## Credits

This work was based on and inspired by https://github.com/TharindaMarasingha/ComfyUI-CSV-to-Prompt

## 📄 License

This project was originally released under the MIT License. As of version 2.1.0, the project has been relicensed under the GNU General Public License v3.0 (GPL‑3.0).

GPL‑3.0 is a copyleft license, which means:

You may use, modify, and redistribute this software
  
Any derivative works must also be licensed under GPL‑3.0
  
Source code for modified versions must be made available