# shots.db Database Schema

This document contains the schema of the SQLite database used by the batch_from_aimms node.

## Database Overview

The database is located at: $dbPath

## Tables

### Table: $tableName

`sql
CREATE TABLE shots (                 shot_id INTEGER PRIMARY KEY AUTOINCREMENT,                 order_number INTEGER,                 shot_name TEXT,                 section TEXT,                 description TEXT,                 dialogue TEXT,                 image_prompt TEXT,                 image_negative TEXT,                 colour_scheme_image TEXT,                 time_of_day TEXT,                 location TEXT,                 country TEXT,                 year TEXT,                 video_prompt TEXT,                 video_negative TEXT,                 lora_1 TEXT,                 lora_2 TEXT,                 lora_3 TEXT,                 created_date TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now', 'utc'))             ); CREATE INDEX idx_shots_shot_name ON shots(shot_name); CREATE INDEX idx_shots_order ON shots(order_number); CREATE INDEX idx_shots_section ON shots(section);
`

#### Columns

| Name | Type | Not Null | Default Value | Is Primary Key |
|------|------|----------|--------------|---------------|
| shot_id | INTEGER | 0 |  | 1 |
| order_number | INTEGER | 0 |  | 0 |
| shot_name | TEXT | 0 |  | 0 |
| section | TEXT | 0 |  | 0 |
| description | TEXT | 0 |  | 0 |
| dialogue | TEXT | 0 |  | 0 |
| image_prompt | TEXT | 0 |  | 0 |
| image_negative | TEXT | 0 |  | 0 |
| colour_scheme_image | TEXT | 0 |  | 0 |
| time_of_day | TEXT | 0 |  | 0 |
| location | TEXT | 0 |  | 0 |
| country | TEXT | 0 |  | 0 |
| year | TEXT | 0 |  | 0 |
| video_prompt | TEXT | 0 |  | 0 |
| video_negative | TEXT | 0 |  | 0 |
| lora_1 | TEXT | 0 |  | 0 |
| lora_2 | TEXT | 0 |  | 0 |
| lora_3 | TEXT | 0 |  | 0 |
| created_date | TEXT | 0 | strftime('%Y-%m-%dT%H:%M:%SZ', 'now', 'utc') | 0 |


#### Sample Data (First 5 Rows)

`
1|1|BW_01A_01A_establishing_london|01A - The Bookies|Establishing title card or graphic: London, present day. A grey wet Saturday afternoon. Sound of distant city.||POV camera at foot height. A grey wet Saturday afternoon. |deformed bodies, deformed limbs, anime, low quality image, text, subtitles,|Theme the image in a colour scheme with a strong ratio of black and gold.|afternoon|Soho, London|England in winter|2020|wide angle view of city of London, camera tracks slowly forward|subtitles, text, blurry, low quality, still frame, frames, watermark, overlay,||||2026-04-30T06:33:48.228821Z 2|4|BW_01A_02A_jack_pulpit_drunk|01A - The Bookies|JACK at the pulpit mid-sermon, visibly swaying. Congregation watches in horrified silence as he slurs his words.||A 40 year old male priest is stood at the raised pulpit in a cold church preaching to a Sunday crowd, he is mid-sermon.  The priest is flailing his arms getting carried away with his sermonising, because he is drunk. Camera shot from below looking slightly up.|deformed bodies, deformed limbs, anime, low quality image, text, subtitles,|Theme the image in a colour scheme ratio of 60:30:10 deep blue, burnished steel, black.|Overcast afternoon|Church|England in winter|2020|a priest is preaching from a lecturn to a church congregation, he is drunk and stumbles from the lecturn. The people look shocked.|subtitles, text, blurry, low quality, still frame, frames, watermark, overlay,||||2026-04-30T06:33:48.228821Z 3|5|BW_01A_03A_jack_falls_pulpit|01A - The Bookies|JACK crashes forward from the pulpit, grabbing the lectern on the way down. Bible pages scatter. A gasp from the congregation.||A 40 year old male priest crashes forward from the pulpit where he was delivering a Sunday sermon, grabbing the lectern on the way down. Bible pages scattering.|deformed bodies, deformed limbs, anime, low quality image, text, subtitles,|Theme the image in a colour scheme ratio of 60:30:10 deep blue, burnished steel, black|Overcast afternoon|Church|England in winter|2020|a priest is tearing pages from a bible while laughing drunk, he throws the pages in the air, then stumbles forward|subtitles, text, blurry, low quality, still frame, frames, watermark, overlay,||||2026-04-30T06:33:48.228821Z 4|6|BW_01A_04A_jack_collar_removed|01A - The Bookies|Close on JACK's face ∩┐╜∩┐╜∩┐╜ red, humiliated ∩┐╜∩┐╜∩┐╜ as his clerical collar is removed by an unseen hand. He is escorted out. He doesn't fight it.||Close up on a 40 year old male priest as he is being escorted out of a church by Police after an incident. He doesn't fight it. The congregation look on in shock.|deformed bodies, deformed limbs, anime, low quality image, text, subtitles,|Theme the image in a colour scheme ratio of 60:30:10 deep blue, burnished steel, black|Overcast afternoon|Church|England in winter|2020|a priest is being led through an angry crowd by the police, the priest is drunk, the crowd are angry at the priest. He removes his collar and throws it away.|subtitles, text, blurry, low quality, still frame, frames, watermark, overlay,||||2026-04-30T06:33:48.228821Z 5|9|BW_01A_05A_sam_boardroom|01A - The Bookies|SAM sharp and composed in a corporate boardroom setting. She belongs here. A woman in command of her life ∩┐╜∩┐╜∩┐╜ for now.||A 40 year old business woman, sharp and composed in a corporate boardroom setting. City of London outside window.|deformed bodies, deformed limbs, anime, low quality image, text, subtitles, african, asian,|Theme the image in a colour scheme ratio of 60:30:10 red, gold, black|Overcast afternoon|London|England in winter|2020|a woman is giving a presentation in an office, she is trying to hide her concern about something|subtitles, text, blurry, low quality, still frame, frames, watermark, overlay,||||2026-04-30T06:33:48.228821Z
`

### Table: $tableName

`sql
CREATE TABLE sqlite_sequence(name,seq);
`

#### Columns

| Name | Type | Not Null | Default Value | Is Primary Key |
|------|------|----------|--------------|---------------|
| name |  | 0 |  | 0 |
| seq |  | 0 |  | 0 |


#### Sample Data (First 5 Rows)

`
shots|79 deleted_shots|12
`

### Table: $tableName

`sql
CREATE TABLE takes (                 take_id TEXT PRIMARY KEY,                 shot_id INTEGER,                 take_type TEXT,                 file_path TEXT,                 starred INTEGER DEFAULT 0,                 created_date TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now', 'utc')),                 FOREIGN KEY (shot_id) REFERENCES shots(shot_id)             ); CREATE INDEX idx_takes_shot_id ON takes(shot_id); CREATE INDEX idx_takes_type ON takes(take_type); CREATE INDEX idx_takes_starred ON takes(starred); CREATE INDEX idx_takes_shot_type ON takes(shot_id, take_type);
`

#### Columns

| Name | Type | Not Null | Default Value | Is Primary Key |
|------|------|----------|--------------|---------------|
| take_id | TEXT | 0 |  | 1 |
| shot_id | INTEGER | 0 |  | 0 |
| take_type | TEXT | 0 |  | 0 |
| file_path | TEXT | 0 |  | 0 |
| starred | INTEGER | 0 | 0 | 0 |
| created_date | TEXT | 0 | strftime('%Y-%m-%dT%H:%M:%SZ', 'now', 'utc') | 0 |


#### Sample Data (First 5 Rows)

`
53d1509d-36b3-5c7b-94a5-54c01b197b53|1|base_image|media/1/base_01.png|0|2026-04-30T06:33:48.228821Z f07f62a9-e501-531c-8808-3847fe446579|1|final_video|media/1/video_01.mp4|0|2026-04-30T06:33:48.228821Z 6a443316-5ccc-5fb2-838d-a28259cb3f49|1|video_workflow|media/1/video_01.png|0|2026-04-30T06:33:48.228821Z 12653772-6e89-5b3b-82bd-aef006c0f0e6|2|base_image|media/2/base_01.png|0|2026-04-30T06:33:48.228821Z 32a22f3d-3421-5dce-9f37-0bc192d00237|2|final_video|media/2/video_01.mp4|0|2026-04-30T06:33:48.228821Z
`

### Table: $tableName

`sql
CREATE TABLE assets (                 id_key TEXT PRIMARY KEY,                 asset_name TEXT,                 asset_type TEXT,                 file_path TEXT,                 starred INTEGER DEFAULT 0,                 created_date TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now', 'utc'))             );
`

#### Columns

| Name | Type | Not Null | Default Value | Is Primary Key |
|------|------|----------|--------------|---------------|
| id_key | TEXT | 0 |  | 1 |
| asset_name | TEXT | 0 |  | 0 |
| asset_type | TEXT | 0 |  | 0 |
| file_path | TEXT | 0 |  | 0 |
| starred | INTEGER | 0 | 0 | 0 |
| created_date | TEXT | 0 | strftime('%Y-%m-%dT%H:%M:%SZ', 'now', 'utc') | 0 |


### Table: $tableName

`sql
CREATE TABLE meta (                 key TEXT PRIMARY KEY,                 value TEXT             );
`

#### Columns

| Name | Type | Not Null | Default Value | Is Primary Key |
|------|------|----------|--------------|---------------|
| key | TEXT | 0 |  | 1 |
| value | TEXT | 0 |  | 0 |


#### Sample Data (First 5 Rows)

`
schema_version|1.2.0 app_version|1.2 comfyui_output_path|C:/ComfyUI/output comfyui_URL|http://127.0.0.1:8188/ project_info|color scheme:  neither in shot: "Theme the image in a colour scheme with a strong ratio of black and gold" JACK shot: "Theme the image in a colour scheme ratio of 60:30:10 deep blue, burnished steel, black" SAM shot: "Theme the image in a colour scheme ratio of 60:30:10 red, gold, black" together, decide based on shot theme requirments who gets the accent. film look prompt: "shot on Super Panavision 70, Technicolor three-strip process, epic cinema, bleached highlights, lifted blacks, faded shadow detail, slightly desaturated midtones, optical print softness, low contrast but luminous, warm dust haze, photochemical color timing, analog film stock"
`

### Table: $tableName

`sql
CREATE TABLE deleted_shots (                 id INTEGER PRIMARY KEY AUTOINCREMENT,                 old_shot_id INTEGER NOT NULL,                 shot_name TEXT,                 created_date TEXT DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now', 'utc'))             ); CREATE INDEX idx_deleted_shots_old_id ON deleted_shots(old_shot_id);
`

#### Columns

| Name | Type | Not Null | Default Value | Is Primary Key |
|------|------|----------|--------------|---------------|
| id | INTEGER | 0 |  | 1 |
| old_shot_id | INTEGER | 1 |  | 0 |
| shot_name | TEXT | 0 |  | 0 |
| created_date | TEXT | 0 | strftime('%Y-%m-%dT%H:%M:%SZ', 'now', 'utc') | 0 |


#### Sample Data (First 5 Rows)

`
1|31|BW_01A_22A_jack_sings_1|2026-05-15T03:02:41.436108Z 2|46|BW_01B_02H_I_may_have|2026-05-29T03:03:17.012425Z 3|43|BW_01B_02E_waiting_lift_c_roll|2026-05-30T01:37:40.157344Z 4|47|BW_01B_02J_the_look|2026-05-30T02:31:41.403468Z 5|48|BW_01B_02K_are_you_joking|2026-05-30T02:31:41.409470Z
`


