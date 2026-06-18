import os
import rasterio
from rasterio.windows import Window
from PIL import Image
import json
from tqdm import tqdm

# CONFIG
input_tif = "ohrc_georeferenced.tif"
tile_size = 512
output_dir = "Tiles"
os.makedirs(output_dir, exist_ok=True)

metadata = {}

with rasterio.open(input_tif) as src:
    img_width, img_height = src.width, src.height
    transform = src.transform
    count = 0

    for y in tqdm(range(0, img_height, tile_size)):
        for x in range(0, img_width, tile_size):
            width = min(tile_size, img_width - x)
            height = min(tile_size, img_height - y)
            window = Window(x, y, width, height)

            tile = src.read(window=window)

            # Save as PNG
            tile_filename = f"tile_{count:05d}.png"
            tile_path = os.path.join(output_dir, tile_filename)
            Image.fromarray(tile[0]).save(tile_path)

            # Save metadata
            tile_transform = rasterio.windows.transform(window, transform)
            metadata[tile_filename] = {
                "tile_index": count,
                "origin_pixel": [x, y],
                "transform": tile_transform.to_gdal(),  # [a, b, c, d, e, f]
                "size": [width, height]
            }

            count += 1

# Save metadata JSON
with open(os.path.join(output_dir, "tile_metadata.json"), "w") as f:
    json.dump(metadata, f, indent=2)

print(f"✅ Tiling complete. {count} tiles saved to {output_dir}/")
