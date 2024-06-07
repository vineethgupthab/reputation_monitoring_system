from bing_image_downloader import downloader
import os
import shutil
from PIL import Image

def clean_member_name(member):
    """Clean the member name."""
    # return member.strip().replace(' ', '-')
    return member.strip()

def download_logo(member):
    """Download, rename, resize, and save the logo."""
    member_safe = clean_member_name(member)
    final_file_path = f"logos/{member_safe}.png"
    
    if os.path.exists(final_file_path):
        print(f"Logo for {member} is already present.")
        return
    
    downloader.download(f'"{member}" transparent logo', limit=1, output_dir='dataset', adult_filter_off=True, force_replace=False, timeout=60, verbose=True)
    download_dir = f'dataset/"{member}" transparent logo'
    temp_filename = f'{member_safe}.png'

    for file_name in os.listdir(download_dir):
        old_file_path = os.path.join(download_dir, file_name)
        temp_file_path = os.path.join('dataset', temp_filename)
        os.rename(old_file_path, temp_file_path)

    output_size = (700, 500)
    image_path = temp_file_path

    with Image.open(image_path) as img:
        img = img.resize(output_size, Image.LANCZOS)
        logos_dir = 'logos'
        os.makedirs(logos_dir, exist_ok=True)
        final_file_path = os.path.join(logos_dir, temp_filename)
        img.save(final_file_path)

    print(f"Image resized to {output_size} and saved as {final_file_path}")
    shutil.rmtree('dataset')
    print(f"Directory {download_dir} removed.")

def process_member_names(file_path):
    """Process member names from a file."""
    with open(file_path, 'r') as file:
        member_names = file.readlines()

    for member in member_names:
        download_logo(member)

if __name__ == "__main__":
    # Process member names from topics.txt
    process_member_names('topics.txt')
