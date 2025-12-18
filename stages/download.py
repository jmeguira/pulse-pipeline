import json
import os

import yt_dlp
from tqdm import tqdm

from types.clip import ClipState
from types.stage import Stage
from utils.utils import get_date_range_str


class DownloadStage(Stage):
    INPUT_CLIP_STATE = ClipState.ELIGIBLE
    OUTPUT_CLIP_STATE = ClipState.DOWNLOADED

    @property
    def name(self):
        return "Download videos"

    def should_run(self):
        # e.g., skip if all files already exist
        return True

    def run(self):
        keyword = self.context.run_config.keyword
        output_path = os.path.join(
            self.context.run_config.OUTPUT_BASE_PATH,
            self.context.run_config.keyword,
            get_date_range_str(
                self.context.run_config.published_after,
                self.context.run_config.published_before,
            ),
        )
        os.makedirs(output_path, exist_ok=True)
        YDL_OPTS = {
            **self.context.run_config.YDL_OPTS,
            "outtmpl": os.path.join(output_path, "%(id)s.%(ext)s"),
        }

        metadata = []

        with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
            for video in tqdm(
                self.context.videos,
                desc=f"Downloading {len(self.context.videos)} videos for '{keyword}'",
                unit="video",
            ):
                try:
                    ydl.download([video["url"]])
                except Exception as e:
                    print(f"❌ Failed to download {video['url']}: {e}")
                    continue

                metadata_entry = {
                    "title": video["title"],
                    "uploader": video["uploader"],
                    "url": video["url"],
                    "upload_date": video["upload_date"],
                    "view_count": video["view_count"],
                    "duration": video["duration"],
                    "file_path": os.path.join(output_path, f"{video['id']}.mp4"),
                    "channel_id": video["channel_id"],
                    "channel_url": f"https://www.youtube.com/channel/{video['channel_id']}",
                }
                metadata.append(metadata_entry)

        if metadata:
            metadata_file = os.path.join(output_path, "metadata.json")
            with open(metadata_file, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=4)

            print(
                f"✅ Finished downloading {len(self.context.videos)} videos for keyword: '{keyword}' \nvideos saved in {output_path}"
            )
