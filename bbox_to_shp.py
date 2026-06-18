import os
import json
import shapefile  # pyshp
from rasterio.transform import Affine

# CONFIG
tile_dir = "Tiles"
pred_dir = "yolo_predictions"
output_shapefile = "detected_boxes"

with open(os.path.join(tile_dir, "tile_metadata.json")) as f:
    metadata = json.load(f)

# Initialize shapefile writer
shp_writer = shapefile.Writer(output_shapefile)
shp_writer.field("tile", "C")
shp_writer.field("label", "C")  # Renamed from class
shp_writer.field("confidence", "F", decimal=4)

def denorm(val, max_val):
    return val * max_val

for pred_file in os.listdir(pred_dir):
    if not pred_file.endswith(".txt"):
        continue

    tile_name = pred_file.replace(".txt", ".png")
    tile_meta = metadata.get(tile_name)

    if tile_meta is None:
        continue

    transform_vals = tile_meta["transform"]
    affine = Affine(*transform_vals)
    tile_width, tile_height = tile_meta["size"]

    with open(os.path.join(pred_dir, pred_file), "r") as f:
        for line in f:
            parts = line.strip().split()
            if len(parts) < 5:
                continue

            _, x_center, y_center, w, h = map(float, parts[:5])

            x_center *= tile_width
            y_center *= tile_height
            w *= tile_width
            h *= tile_height

            x_min = x_center - w / 2
            x_max = x_center + w / 2
            y_min = y_center - h / 2
            y_max = y_center + h / 2

            corners = [
                (x_min, y_min),
                (x_min, y_max),
                (x_max, y_max),
                (x_max, y_min),
                (x_min, y_min)
            ]
            geo_corners = [affine * (x, y) for x, y in corners]

            shp_writer.poly([geo_corners])
            shp_writer.record(tile=tile_name, label="crater", confidence=1.0)

shp_writer.close()
# Save .prj file (WGS 84 - EPSG:4326)
prj_path = f"{output_shapefile}.prj"
wgs84_wkt = """GEOGCS["WGS 84",
    DATUM["WGS_1984",
        SPHEROID["WGS 84",6378137,298.257223563,
            AUTHORITY["EPSG","7030"]],
        AUTHORITY["EPSG","6326"]],
    PRIMEM["Greenwich",0,
        AUTHORITY["EPSG","8901"]],
    UNIT["degree",0.0174532925199433,
        AUTHORITY["EPSG","9122"]],
    AUTHORITY["EPSG","4326"]]"""

with open(prj_path, "w") as prj_file:
    prj_file.write(wgs84_wkt)

print(f"📌 Projection file saved as {prj_path}")

print(f"✅ Shapefile saved as {output_shapefile}.shp")
