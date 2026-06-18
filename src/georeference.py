import os
import pandas as pd
from osgeo import gdal, osr

# Configurable paths
INPUT_TIF = "ohrc_image.tif"
INPUT_CSV = "data/Geometry/20190907/ch2_ohr_ncp_20190907T0438126359_g_grd_g26.csv"
OUTPUT_VRT = "ohrc_with_gcps.vrt"
OUTPUT_GEOTIFF = "ohrc_georeferenced.tif"

def georeference_image(tif_path=INPUT_TIF, csv_path=INPUT_CSV, vrt_path=OUTPUT_VRT, geotiff_path=OUTPUT_GEOTIFF):
    """
    Applies Ground Control Points (GCPs) from a CSV file to a raw lunar TIFF image
    and warps it to produce a georeferenced GeoTIFF in EPSG:4326.
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"GCP file not found at: {csv_path}")
    if not os.path.exists(tif_path):
        raise FileNotFoundError(f"Input TIFF not found at: {tif_path}")

    # Load GCPs from CSV
    df = pd.read_csv(csv_path)
    gcps = [
        gdal.GCP(row["Longitude"], row["Latitude"], 0, row["Pixel"], row["Scan"])
        for _, row in df.iterrows()
    ]
    print(f"✅ Loaded {len(gcps)} GCPs from {csv_path}")

    # Define EPSG:4326 CRS (WGS 84 geographic CRS mapping directly to selenographic decimal degrees)
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(4326)

    # Open original dataset and create a Virtual Raster (VRT) copy
    src_ds = gdal.Open(tif_path, gdal.GA_ReadOnly)
    driver = gdal.GetDriverByName("VRT")
    vrt_ds = driver.CreateCopy(vrt_path, src_ds, 0)

    # Assign GCPs and projection to VRT
    vrt_ds.SetGCPs(gcps, srs.ExportToWkt())
    vrt_ds.FlushCache()
    vrt_ds = None
    print(f"📌 VRT with GCPs saved as: {vrt_path}")

    # Re-open VRT to confirm and estimate resolution
    vrt_ds = gdal.Open(vrt_path)
    print("📌 GCP Count in VRT:", len(vrt_ds.GetGCPs()))

    # Estimate resolution from GCP bounds
    long_min, long_max = df["Longitude"].min(), df["Longitude"].max()
    lat_min, lat_max = df["Latitude"].min(), df["Latitude"].max()
    pixel_min, pixel_max = df["Pixel"].min(), df["Pixel"].max()
    scan_min, scan_max = df["Scan"].min(), df["Scan"].max()

    xRes = abs((long_max - long_min) / (pixel_max - pixel_min))
    yRes = abs((lat_max - lat_min) / (scan_max - scan_min))
    print(f"📏 Estimated resolution -> xRes: {xRes:.10f}, yRes: {yRes:.10f}")

    # Warp using the VRT to produce the georeferenced GeoTIFF
    print("🚀 Warping image (this might take a moment)...")
    gdal.Warp(
        geotiff_path,
        vrt_path,
        dstSRS="EPSG:4326",
        format="GTiff",
        xRes=xRes,
        yRes=yRes,
        resampleAlg="near"
    )
    print(f"✅ Warped and georeferenced GeoTIFF saved as: {geotiff_path}")

if __name__ == "__main__":
    georeference_image()
