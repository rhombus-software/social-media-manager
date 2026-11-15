import subprocess
import os
import sys
from .StratusManager import StratusManager


class FileParser:
    def __init__(self, file_name):
        self.file_name = file_name
        self.output_file = f"{self.file_name.split(".")[0]}_compressed.mp4" or "compressed_video.mp4"
    
    def extreme_compress_video(self,target_resolution="640x360", crf="35", preset="veryfast"):
        """
        Extremely compresses a video by reducing resolution, lowering framerate, 
        and using a high CRF (Constant Rate Factor) for maximum size reduction.
        """
        if not os.path.exists(self.file_name):
            print(f"Error: Input file '{self.file_name}' not found.")
            return

        # FFmpeg command breakdown for extreme compression:
        # -i: input file
        # -vf scale: forces downscaling (e.g., 360p)
        # -r: lowers framerate to 20 fps to save bandwidth
        # -c:v libx264: H.264 video codec (change to libx265 for even smaller size if supported)
        # -crf: Quality factor (18-28 is normal, 35+ is heavily compressed/low quality)
        # -preset: encoding speed vs compression (veryfast, ultrafast)
        # -c:a aac -b:a 64k: compresses audio heavily down to 64 kbps
        
        command = [
            "ffmpeg",
            "-i", self.file_name,
            "-vf", f"scale={target_resolution}",
            "-r", "20",                          # Reduce framerate to 20 fps
            "-c:v", "libx264",
            "-crf", crf,                         # Higher CRF = smaller size, lower quality (try 32 to 40)
            "-preset", preset,
            "-c:a", "aac",
            "-b:a", "64k",                       # Low bitrate audio
            self.output_file
        ]

        print(f"Compressing '{self.file_name}'... Please wait.")
        
        try:
            # Run the command
            subprocess.run(command, check=True)
            
            # Compare file sizes
            original_size = os.path.getsize(self.file_name) / (1024 * 1024)
            new_size = os.path.getsize(self.output_file) / (1024 * 1024)
            
            print("\nCompression complete!")
            print(f"Original Size: {original_size:.2f} MB")
            print(f"Compressed Size: {new_size:.2f} MB")
            print(f"Saved: {((original_size - new_size) / original_size) * 100:.1f}%")
            return self.output_file
        except subprocess.CalledProcessError as e:
            print(f"An error occurred during compression: {e}")

# --- Example Usage ---
# if __name__ == "__main__":
#     file_name = sys.argv[1] if len(sys.argv) > 1  else "video1.mov"
    
#     print(file_name, output_file)
#     # crf=38 and scale=424x240 will result in extremely small files with noticeable quality loss
#     stratus = StratusManager(bucket_name="raw")
#     stratus.download_file(file_name, file_name)
#     extreme_compress_video(
#         input_path=file_name, 
#         self.output_file=output_file, 
#         target_resolution="424x240",  # 240p resolution
#         crf="46"                      # Extreme compression level
#     )
#     stratus.upload_file(output_file, output_file)