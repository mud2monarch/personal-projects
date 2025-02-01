from PIL import Image
import os
from pathlib import Path

def resize_images(input_folder, output_folder=None, size=(800, 800), maintain_aspect=True):
    """
    Resize all PNG images in the input folder and save them to the output folder.
    
    Args:
        input_folder (str): Path to folder containing PNG images
        output_folder (str, optional): Path to save resized images. If None, overwrites original files
        size (tuple): Target size as (width, height)
        maintain_aspect (bool): If True, maintains aspect ratio and fits within target size
    """
    # Create output folder if specified and doesn't exist
    if output_folder:
        Path(output_folder).mkdir(parents=True, exist_ok=True)
    
    # Get all PNG files in the input folder
    png_files = Path(input_folder).glob('*.png')
    
    for image_path in png_files:
        try:
            # Open the image
            with Image.open(image_path) as img:
                # Calculate new size if maintaining aspect ratio
                if maintain_aspect:
                    img.thumbnail(size, Image.Resampling.LANCZOS)
                    resized_img = img
                else:
                    resized_img = img.resize(size, Image.Resampling.LANCZOS)
                
                # Determine output path
                if output_folder:
                    output_path = Path(output_folder) / image_path.name
                else:
                    output_path = image_path
                
                # Save the resized image
                resized_img.save(output_path, 'PNG')
                print(f"Resized {image_path.name}")
                
        except Exception as e:
            print(f"Error processing {image_path.name}: {e}")

if __name__ == "__main__":
    # Example usage
    input_folder = "/Users/zach.wong/Downloads/images_to_compress"  # Change this to your input folder path
    output_folder = None  # Change this to your output folder path, or set to None to overwrite
    target_size = (800, 1200)  # Change this to your desired size
    
    resize_images(input_folder, output_folder, target_size)