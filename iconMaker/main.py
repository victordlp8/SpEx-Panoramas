import argparse
from pathlib import Path
from PIL import Image
from tqdm import tqdm
import requests
from io import BytesIO


def find_panorama_directories(base_path):
    """Find all panorama directories in the given path."""
    panorama_dirs = []
    base_path = Path(base_path)
    
    if not base_path.exists():
        print(f"Error: Path {base_path} does not exist")
        return panorama_dirs
    
    # Look for panorama directories
    for item in base_path.iterdir():
        if item.is_dir() and item.name.startswith('panorama_'):
            panorama_dirs.append(item)
    
    # Sort by panorama number
    panorama_dirs.sort(key=lambda x: int(x.name.split('_')[1]))
    return panorama_dirs


def create_icon_from_panoramas(panorama_dirs, output_path):
    """Create a dynamic-sized icon by scaling and pasting panorama images."""
    num_panoramas = len(panorama_dirs)
    
    # Calculate minimum square size that can fit all panoramas as 2x2 blocks
    # Each block is 2x2, so we need ceil(sqrt(num_panoramas)) blocks per side
    import math
    blocks_per_side = math.ceil(math.sqrt(num_panoramas))
    icon_size = blocks_per_side * 2  # Each block is 2x2 pixels
    
    print(f"Creating {icon_size}x{icon_size} icon for {num_panoramas} panoramas")
    print(f"Grid: {blocks_per_side}x{blocks_per_side} blocks of 2x2 pixels")
    
    # Create dynamic-sized icon
    icon = Image.new('RGB', (icon_size, icon_size))
    
    # Calculate total blocks in the icon
    total_blocks = blocks_per_side * blocks_per_side
    
    # Process each block position, repeating panoramas as needed
    for i in tqdm(range(total_blocks), desc="Building icon blocks"):
        # Determine which panorama to use (with repetition)
        panorama_index = i % num_panoramas
        panorama_dir = panorama_dirs[panorama_index]
        
        panorama_1_path = panorama_dir / "panorama_1.png"
        if panorama_1_path.exists():
            # Scale image to 2x2
            with Image.open(panorama_1_path) as img:
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                img_2x2 = img.resize((2, 2), Image.Resampling.LANCZOS)
                
                # Calculate position in the grid
                block_row = i // blocks_per_side
                block_col = i % blocks_per_side
                
                # Paste the 2x2 image at the calculated position
                x = block_col * 2
                y = block_row * 2
                icon.paste(img_2x2, (x, y))
        else:
            print(f"Warning: {panorama_1_path} not found")
    
    # Scale to 512x512 with pixel perfect (nearest neighbor)
    print("Scaling to 512x512...")
    icon_512 = icon.resize((512, 512), Image.Resampling.NEAREST)
    
    # Download and add Modrinth logo
    try:
        print("Adding Modrinth logo...")
        modrinth_url = "https://cdn.modrinth.com/data/tOtFEyiq/c21f48620053ac5f5a72eb9ee318b3bd1093bfc1_96.webp"
        response = requests.get(modrinth_url)
        modrinth_logo = Image.open(BytesIO(response.content))
        
        # Convert to RGBA if needed
        if modrinth_logo.mode != 'RGBA':
            modrinth_logo = modrinth_logo.convert('RGBA')
        
        # Resize logo to very large size (256x256)
        logo_size = 256
        modrinth_logo = modrinth_logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)
        
        # Calculate position (bottom-right corner with some margin)
        margin = 8
        x = 512 - logo_size - margin
        y = 512 - logo_size - margin
        
        # Paste logo onto the icon
        icon_512.paste(modrinth_logo, (x, y), modrinth_logo)
        print("Modrinth logo added successfully")
        
    except Exception as e:
        print(f"Warning: Could not add Modrinth logo: {e}")
        print("Saving icon without logo...")
    
    # Save the final icon
    icon_512.save(output_path)
    print(f"Icon saved as {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Create a 16x16 icon from panorama images")
    parser.add_argument("panorama_path", help="Path to the panoramas directory (e.g., e2w1)")
    args = parser.parse_args()
    
    panorama_path = Path(args.panorama_path)
    
    # Try different possible structures
    possible_paths = [
        panorama_path / "assets" / "spex_e2w1" / "panoramas",
        panorama_path / "panoramas",
        panorama_path
    ]
    
    # If running from iconMaker directory, try parent directory paths
    if not panorama_path.exists():
        possible_paths.extend([
            Path("../e2w1") / "assets" / "spex_e2w1" / "panoramas",
            Path("../e2w1") / "panoramas",
            Path("../e2w1")
        ])
    
    # Find panoramas
    panorama_dirs = []
    panorama_base_path = None
    for path in possible_paths:
        if path.exists():
            panorama_dirs = find_panorama_directories(path)
            if panorama_dirs:
                print(f"Found panoramas in: {path}")
                panorama_base_path = path
                break
    
    if not panorama_dirs:
        print(f"No panorama directories found in {panorama_path}")
        print("Tried paths:")
        for path in possible_paths:
            print(f"  - {path}")
        return
    
    # Determine output path
    if panorama_base_path and ".." in str(panorama_base_path):
        output_path = Path("../e2w1") / "pack.png"
    else:
        output_path = panorama_path / "pack.png"
    
    print(f"Found {len(panorama_dirs)} panorama directories")
    create_icon_from_panoramas(panorama_dirs, str(output_path))


if __name__ == "__main__":
    main()
