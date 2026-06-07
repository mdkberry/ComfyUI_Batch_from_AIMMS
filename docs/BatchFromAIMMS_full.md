# ComfyUI_Batch_from_AIMMS 🎬

***NOTE: This is part of a multi-node system for ComfyUI batch processing. The original CSV functionality remains unchanged, but the overall system now includes an additional node for processing directly from AIMMS databases. See the main [README.md](../README.md) for more information about the complete system.*** - Mark, 1st June 2026.

A custom ComfyUI node for **batch/bulk workflow processing** driven directly from an AIMMS SQLite database.
Each shot is selected by shot_id and processed individually, making it perfect for automating large batches across any workflow type — t2i, i2i, i2v, t2v, v2v, or anything else.

---

**Example database schema**:

The node accesses two tables in the AIMMS database:
- `shots` table containing shot metadata
- `takes` table containing media files associated with each shot

---

**ComfyUI custom node screenshot (v2.0.3)**

<img width="1842" height="921" alt="screenshot_connections_v2 0 3" src="https://github.com/user-attachments/assets/175497be-0583-4780-b032-e675227b2c39" />

_The above screenshot shows viable connections you can use and examples of connector outputs for reference. The actual node is on the left. It will load shot data from the AIMMS database based on the shot_id you provide._

---

## ✨ Output Connectors

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
| `row_index`       | INT    | The shot ID that was loaded — handy for debugging |
| `info`            | STRING | Full shot summary — pipe into a **Show Any** node to embed all shot data in PNG workflow metadata |

**Notes on the text/prompt fields:**
- `positive_image` / `negative_image` — use for image-based workflows (t2i, i2i).
- `positive_video` / `negative_video` — use for video-based workflows (i2v, t2v, v2v).
- `colour_scheme`, `scene_context`, `dialogue` — optional helper fields. Concatenate any combination of these with a prompt in your workflow using a **String Concatenate** or similar node.
- LoRA and audio paths are returned as plain strings — blank if not set in the database. Connect to the appropriate loader's file path input.

---

## ✅ Key Features

- **Direct database access** — reads directly from AIMMS SQLite database without needing CSV export
- **Shot ID selection** — specify exactly which shots to process using comma-separated shot IDs
- **Media file handling** — automatically retrieves reference images, videos, and audio from the takes table
- **Read-only database access** — safely reads from the database without modifying it
- **Graceful fallback** — missing image files produce a blank 64×64 black tensor (no crash); missing video/audio/LoRA paths log a warning and return the path string as-is
- **Windows paths supported** — backslashes are normalised automatically on all OS
- **Mixed workflow support** — image and video prompts are separate outputs; use whichever your workflow needs

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
├── csv_files/                  ← PUT YOUR CSV FILES HERE (for CSV node)
│   ├── example_batch.csv
│   └── my_project.csv
│
├── __init__.py
├── batch_from_csv_node.py        ← CSV processing node
├── batch_from_aimms_node.py     ← AIMMS database processing node
├── pyproject.toml
├── README.md                    ← Main documentation for the entire system
└── docs/                        ← Detailed documentation for each node
    ├── BatchFromCSV_full.md          ← CSV node documentation
    └── BatchFromAIMMS_full.md        ← This file (AIMMS node documentation)
```

---

## 📝 Database Schema

The node expects an AIMMS database with the following table structure:

### shots table

| Column                | Type   | Description |
|-----------------------|--------|-------------|
| `shot_id`             | INT    | Unique shot identifier (PRIMARY KEY) |
| `order_number`        | INT    | Sort/execution order |
| `shot_name`           | TEXT   | Shot label for output file naming |
| `description`         | TEXT   | Scene/environment description (optional) |
| `dialogue`            | TEXT   | Dialogue text (optional) |
| `image_prompt`        | TEXT   | Positive prompt for image generation |
| `image_negative`      | TEXT   | Negative prompt for image generation |
| `colour_scheme_image` | TEXT   | Colour palette description (optional) |
| `video_prompt`        | TEXT   | Positive prompt for video generation |
| `video_negative`      | TEXT   | Negative prompt for video generation |
| `lora_1`              | TEXT   | LoRA name (relative path) |
| `lora_2`              | TEXT   | Second LoRA name (relative path) |
| `lora_3`              | TEXT   | Third LoRA name (relative path) |
| `time_of_day`         | TEXT   | Time of day (e.g. "morning", "night") |
| `location`            | TEXT   | Location description |
| `country`             | TEXT   | Country |
| `year`                | TEXT   | Year/time period |

### takes table

| Column      | Type   | Description |
|-------------|--------|-------------|
| `shot_id`   | INT    | Foreign key to shots table |
| `take_type` | TEXT   | Type of media ("base_image", "final_video", "audio_vo") |
| `file_path` | TEXT   | Path to the media file (relative to project root) |
| `starred`   | INT    | Priority indicator (1-3 for images, 0-1 for video/audio) |

---

## 🚀 How to Use (Batch Generation)

### Step 1 — Add the node

Double-click the canvas → search for **"Batch from AIMMS"** (category: `Batch/AIMMS`).

For CSV processing, search for **"Batch from CSV"** (category: `Batch/CSV`).

### Step 2 — Select your database

Enter the path to your AIMMS SQLite database file in the `db_path` field. The default path is `M:\AIMMS_Projects\project_BlackMagic\data\shots.db`.

### Step 3 — Specify shot IDs

Enter comma-separated shot IDs in the `shot_id` field (e.g. "1,2,5,3").

### Step 4 — Connect outputs

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
| `info`            | Show Any node → embed all shot data in PNG metadata |

### Step 5 — Configure for batch

1. In the ComfyUI menu, set **Batch count** to the number of shot IDs you specified.
2. Click **Queue Prompt** — ComfyUI will run once per shot ID, automatically loading each shot from the database.

---

## ❓ Troubleshooting

| Problem | Fix |
|---------|-----|
| Database file not found | Check the path in `db_path` is correct and the file exists |
| Shot ID not found | Verify the shot ID exists in your database |
| Image outputs are blank/black | Check the media file paths in the takes table are correct and the files exist |
| Video/audio path warning in console | The path is returned as a string even if missing — check spelling |
| LoRA not loading | Confirm the full path is correct; the node returns the path as a string only |
| Info shows empty paths | Make sure the relevant fields exist in your database tables |
| No outputs being made after first run | Make sure you have set the shot IDs back to your desired list to start over |
| Second runs are slow | You may need to offload models between batch runs to clear the memory for VRAM and RAM |
| OOMs cause failures | Try setting switches for ComfyUI to aid with avoiding OOMs during batch processing and add memory clearing features to the workflow. |

---

## Integration with AIMMS Storyboard Management System

This node provides direct integration with [AIMMS Storyboard Management System (vrs 1.2.0)](https://markdkberry.com/software/) by accessing the SQLite database directly.

For CSV-based processing from AIMMS exports, see the companion node [Batch from CSV 📋](BatchFromCSV.md).

_AIMMS (vrs 1.2.0) screenshot of shot details page, showing popup entries for shot management:_

<img width="1914" height="1076" alt="AIMMS_shot_details" src="https://github.com/user-attachments/assets/1e281f07-ffd1-4fa3-87fd-c9cc6906f54d" />

---

## Credits

This work was based on and inspired by https://github.com/TharindaMarasingha/ComfyUI-CSV-to-Prompt and the existing Batch from CSV 📋 node.

## 📄 License

This project was originally released under the MIT License. As of version 2.1.0, the project has been relicensed under the GNU General Public License v3.0 (GPL‑3.0).

GPL‑3.0 is a copyleft license, which means:

You may use, modify, and redistribute this software
  
Any derivative works must also be licensed under GPL‑3.0
  
Source code for modified versions must be made available