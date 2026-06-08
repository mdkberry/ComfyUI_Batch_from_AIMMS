# BatchFromAIMMS

## Description
A custom ComfyUI node for batch processing workflows from an AIMMS SQLite database. Each execution loads one shot based on the shot_id and provides all relevant data for AI image or video generation.

## Inputs
- **db_path** (STRING): Path to the AIMMS SQLite database file
- **shot_id** (STRING): Comma-separated list of shot IDs to process (e.g. '1,2,5,3')

## Outputs
- **shot_id** (STRING): Unique shot identifier
- **order_number** (STRING): Execution order field
- **shot_name** (STRING): Shot label for output file naming
- **colour_scheme** (STRING): Colour palette description (optional, concatenate in workflow)
- **scene_context** (STRING): Scene/environment description (optional)
- **dialogue** (STRING): Dialogue text (optional)
- **lora_1** (COMBO): Path to LoRA 1 .safetensors (plug into LoRA loader path)
- **lora_2** (COMBO): Path to LoRA 2 .safetensors
- **lora_3** (COMBO): Path to LoRA 3 .safetensors
- **ref_image_1** (IMAGE): First reference image tensor
- **ref_image_2** (IMAGE): Second reference image tensor
- **ref_image_3** (IMAGE): Third reference image tensor
- **video_file** (STRING): Normalised path to the video file
- **audio_vo** (STRING): Path to VO audio file (mp3/m4a/flac/wav), plug into audio loader
- **image_prompt** (STRING): Positive prompt for image generation (t2i / i2i)
- **image_negative** (STRING): Negative prompt for image generation
- **video_prompt** (STRING): Positive prompt for video generation (i2v / t2v / v2v)
- **video_negative** (STRING): Negative prompt for video generation
- **row_index** (INT): The actual shot_id that was loaded (useful for debugging)
- **info** (STRING): Full shot summary — pipe into a Show Any node

## Database Fields Mapping
- **shot_id** → shot_id (STRING)
- **order_number** → order_number (STRING)
- **shot_name** → shot_name (STRING)
- **colour_scheme** → colour_scheme_image (STRING)
- **scene_context** → time_of_day, location, country, year (STRING)
- **dialogue** → dialogue (STRING)
- **lora_1/2/3** → lora_1/2/3 (STRING)
- **ref_image_1/2/3** → takes table (base_image, starred=1/2/3) (IMAGE)
- **video_file** → takes table (final_video, starred=1) (STRING)
- **audio_vo** → takes table (audio_vo) (STRING)
- **image_prompt** → image_prompt (STRING)
- **image_negative** → image_negative (STRING)
- **video_prompt** → video_prompt (STRING)
- **video_negative** → video_negative (STRING)
- **row_index** → shot_id (INT)
- **info** → full shot summary (STRING)