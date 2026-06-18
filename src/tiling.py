import os
import rasterio
from rasterio.windows import Window
from PIL import Image
import json
from tqdm import tqdm

INPUT_TIF = "ohrc_georeferenced.tif"
TILE_SIZE = 512
OUTPUT_DIR = "Tiles"

def tile_image(input_tif=INPUT_TIF, tile_size=TILE_SIZE, output_dir=OUTPUT_DIR):
    """
    Slices a large georeferenced GeoTIFF into smaller tiles (e.g. 512x512 PNGs)
    and saves their spatial transforms in a tile_metadata.json file.
    """
    if not os.path.exists(input_tif):
        raise FileNotFoundError(f"Georeferenced TIFF not found at: {input_tif}")

    os.makedirs(output_dir, exist_ok=True)
    metadata = {}

    with rasterio.open(input_tif) as src:
        img_width, img_height = src.width, src.height
        transform = src.transform
        count = 0

        # Loop through the grid
        for y in tqdm(range(0, img_height, tile_size), desc="Tiling rows"):
            for x in range(0, img_width, tile_size):
                width = min(tile_size, img_width - x)
                height = min(tile_size, img_height - y)
                window = Window(x, y, width, height)

                # Read only the window segment
                tile = src.read(window=window)

                # Save as PNG (using 1st band)
                tile_filename = f"tile_{count:05d}.png"
                tile_path = os.path.join(output_dir, tile_filename)
                Image.fromarray(tile[0]).save(tile_path)

                # Save metadata: window transform saved in GDAL order [c, a, b, f, d, e]
                tile_transform = rasterio.windows.transform(window, transform)
                metadata[tile_filename] = {
                    "tile_index": count,
                    "origin_pixel": [x, y],
                    "transform": tile_transform.to_gdal(),
                    "size": [width, height]
                }

                count += 1

    # Save metadata JSON
    metadata_path = os.path.join(output_dir, "tile_metadata.json")
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"✅ Tiling complete. {count} tiles saved to {output_dir}/")
    print(f"📌 Tile transform metadata saved to {metadata_path}")

if __name__ == "__main__":
    tile_image()
