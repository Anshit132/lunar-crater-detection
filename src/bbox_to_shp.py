import os
import json
import shapefile  # pyshp
from rasterio.transform import Affine

TILE_DIR = "Tiles"
PRED_DIR = "yolo_predictions"
OUTPUT_SHAPEFILE = "detected_boxes"

def generate_shapefile(tile_dir=TILE_DIR, pred_dir=PRED_DIR, output_shapefile=OUTPUT_SHAPEFILE):
    """
    Reads YOLO bounding box predictions, converts them from local tile coordinates
    to selenographic coordinates (longitude, latitude) using tile affine transforms,
    and writes them into a georeferenced GIS Shapefile.
    """
    metadata_path = os.path.join(tile_dir, "tile_metadata.json")
    if not os.path.exists(metadata_path):
        raise FileNotFoundError(f"Metadata file not found: {metadata_path}. Have you tiled the image?")
    if not os.path.exists(pred_dir):
        raise FileNotFoundError(f"Predictions directory not found: {pred_dir}. Have you run inference?")

    with open(metadata_path) as f:
        metadata = json.load(f)

    # Initialize shapefile writer
    shp_writer = shapefile.Writer(output_shapefile)
    shp_writer.field("tile", "C")
    shp_writer.field("label", "C")
    shp_writer.field("confidence", "F", decimal=4)

    prediction_files = [f for f in os.listdir(pred_dir) if f.endswith(".txt")]
    print(f"🚀 Parsing {len(prediction_files)} prediction files...")

    count = 0
    for pred_file in prediction_files:
        tile_name = pred_file.replace(".txt", ".png")
        tile_meta = metadata.get(tile_name)

        if tile_meta is None:
            continue

        # Correctly load the affine transform from GDAL parameters to fix QGIS coordinate scrambling
        transform_vals = tile_meta["transform"]
        affine = Affine.from_gdal(*transform_vals)
        tile_width, tile_height = tile_meta["size"]

        with open(os.path.join(pred_dir, pred_file), "r") as f:
            for line in f:
                parts = line.strip().split()
                if len(parts) < 5:
                    continue

                # YOLO normalized coords format: <class> <x_center> <y_center> <w> <h>
                _, x_center, y_center, w, h = map(float, parts[:5])

                # Denormalize to pixel values
                x_center *= tile_width
                y_center *= tile_height
                w *= tile_width
                h *= tile_height

                x_min = x_center - w / 2
                x_max = x_center + w / 2
                y_min = y_center - h / 2
                y_max = y_center + h / 2

                # Corner vertices in pixel coordinates (clockwise loop)
                corners = [
                    (x_min, y_min),
                    (x_min, y_max),
                    (x_max, y_max),
                    (x_max, y_min),
                    (x_min, y_min)
                ]

                # Map pixel coordinates to geographic coordinates (lon, lat)
                geo_corners = [affine * (x, y) for x, y in corners]

                # Save geometry polygon
                shp_writer.poly([geo_corners])
                shp_writer.record(tile=tile_name, label="crater", confidence=1.0)
                count += 1

    shp_writer.close()
    print(f"✅ Shapefile created with {count} detected craters.")

    # Save .prj file specifying WGS 84 (EPSG:4326) CRS
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

    print(f"📌 Projection metadata saved as {prj_path}")
    print(f"✅ Completed. Shapefile files generated: {output_shapefile}.shp/.shx/.dbf/.prj")

if __name__ == "__main__":
    generate_shapefile()
