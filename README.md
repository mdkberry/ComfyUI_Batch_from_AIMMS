# ComfyUI_Batch_from_AIMMS 📋

***NOTE: This is a set of two nodes for ComfyUI batch processing.***

**Batch_from_CSV** - [documentation](docs/BatchFromCSV.md)

**Batch_from_AIMMS** - [documentation](docs/BatchFromAIMMS.md)

***This system provides two approaches for batch processing in ComfyUI: CSV-based processing and direct database integration with AIMMS. The CSV node remains fully functional, but the system now includes an additional node for processing directly from AIMMS databases without needing CSV export.*** - Mark, 6th June 2026.

## Overview

ComfyUI_Batch_from_AIMMS is a custom node system for ComfyUI that provides two methods for batch processing workflows:

1. **Batch from CSV 📋** - Processes shots from CSV files exported from AIMMS or other sources
2. **Batch from AIMMS 🎬** - Directly accesses shots from AIMMS SQLite databases

Both nodes support the same workflow types (t2i, i2i, i2v, t2v, v2v) and provide similar output connectors for integrating with your ComfyUI workflows.

## Key Features

- **Multi-node system** - Choose between CSV or database processing based on your needs
- **Batch processing** - Process multiple shots automatically in sequence
- **AIMMS integration** - Works seamlessly with AIMMS Storyboard Management System
- **Flexible workflows** - Supports image and video generation workflows
- **Reference image support** - Up to three reference images per shot
- **LoRA integration** - Direct support for up to three LoRA files
- **Audio support** - Voice-over audio file integration
- **Seed-driven batching** - CSV node uses seed increment for batch processing
- **Database-driven selection** - AIMMS node processes specific shot IDs

## Installation

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

## Folder Structure

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
├── README.md                    ← This file (main documentation)
└── docs/                        ← Detailed documentation for each node
    ├── BatchFromCSV.md          ← CSV node documentation
    └── BatchFromAIMMS.md        ← AIMMS node documentation
```

## Usage Guide

### For CSV Processing

1. See [BatchFromCSV.md](docs/BatchFromCSV.md) for detailed instructions on using the CSV-based node
2. Export your shots from AIMMS to CSV format
3. Place the CSV file in the `csv_files` directory
4. Use the "Batch from CSV 📋" node in your ComfyUI workflow

### For Database Processing

1. See [BatchFromAIMMS.md](docs/BatchFromAIMMS.md) for detailed instructions on using the database node
2. Point the node to your AIMMS SQLite database file
3. Specify the shot IDs you want to process
4. Use the "Batch from AIMMS 🎬" node in your ComfyUI workflow

## Common Output Connectors

Both nodes provide similar output connectors:

- `shot_id`, `order_number`, `shot_name` - Shot identification
- `colour_scheme`, `scene_context`, `dialogue` - Text fields for prompts
- `lora_1`, `lora_2`, `lora_3` - LoRA file paths (COMBO type)
- `ref_image_1`, `ref_image_2`, `ref_image_3` - Reference images (IMAGE type)
- `video_file`, `audio_vo` - Media file paths
- `positive_image`, `negative_image` - Image generation prompts
- `positive_video`, `negative_video` - Video generation prompts
- `row_index`, `info` - Debug and metadata information

## Integration with AIMMS Storyboard Management System

Both nodes are designed to work with [AIMMS Storyboard Management System (vrs 1.2.0)](https://markdkberry.com/software/):

- **CSV node** - Uses exported CSV data from AIMMS
- **Database node** - Directly accesses the AIMMS SQLite database

For more information about AIMMS integration, see the respective documentation files.

## Troubleshooting

### Common Issues

- **No nodes appearing** - Make sure you've restarted ComfyUI after installation
- **CSV not found** - Check your CSV file is in the `csv_files` directory
- **Database not found** - Verify the database path is correct
- **Missing media files** - Ensure all referenced files exist at the specified paths
- **LoRA not loading** - Confirm the LoRA paths are correct relative to your models/loras folder

### Getting Help

If you encounter issues not covered here:
1. Check the specific node documentation files
2. Review the troubleshooting sections in each node's documentation
3. Check the ComfyUI console for error messages

## Credits

This work was based on and inspired by https://github.com/TharindaMarasingha/ComfyUI-CSV-to-Prompt

## 📄 License

This project was originally released under the MIT License. As of version 2.1.0, the project has been relicensed under the GNU General Public License v3.0 (GPL‑3.0).

GPL‑3.0 is a copyleft license, which means:

You may use, modify, and redistribute this software
  
Any derivative works must also be licensed under GPL‑3.0
  
Source code for modified versions must be made available