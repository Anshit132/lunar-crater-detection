import pandas as pd
from osgeo import gdal, osr
import os

# ==== ✅ CONFIGURATION ====
input_tif = "ohrc_image.tif"
input_csv = "Input/Geometry/20190907/ch2_ohr_ncp_20190907T0438126359_g_grd_g26.csv"
output_vrt = "ohrc_with_gcps.vrt"
output_geotiff = "ohrc_georeferenced.tif"
# ===========================

# ✅ Load GCPs from CSV
df = pd.read_csv(input_csv)
gcps = [
    gdal.GCP(row["Longitude"], row["Latitude"], 0, row["Pixel"], row["Scan"])
    for _, row in df.iterrows()
]
print(f"✅ Loaded {len(gcps)} GCPs from {input_csv}")

# ✅ Define EPSG:4326 CRS
srs = osr.SpatialReference()
srs.ImportFromEPSG(4326)

# ✅ Open original dataset
src_ds = gdal.Open(input_tif, gdal.GA_ReadOnly)
driver = gdal.GetDriverByName("VRT")
vrt_ds = driver.CreateCopy(output_vrt, src_ds, 0)

# ✅ Assign GCPs and projection
vrt_ds.SetGCPs(gcps, srs.ExportToWkt())
vrt_ds.FlushCache()
vrt_ds = None
print(f"📌 VRT with GCPs saved as: {output_vrt}")

# ✅ Re-open to confirm
vrt_ds = gdal.Open(output_vrt)
print("📌 GCP Count in VRT:", len(vrt_ds.GetGCPs()))

# ✅ Estimate resolution from GCPs
long_min, long_max = df["Longitude"].min(), df["Longitude"].max()
lat_min, lat_max = df["Latitude"].min(), df["Latitude"].max()
pixel_min, pixel_max = df["Pixel"].min(), df["Pixel"].max()
scan_min, scan_max = df["Scan"].min(), df["Scan"].max()

xRes = abs((long_max - long_min) / (pixel_max - pixel_min))
yRes = abs((lat_max - lat_min) / (scan_max - scan_min))
print(f"📏 Estimated xRes: {xRes:.10f}, yRes: {yRes:.10f}")

# ✅ Warp using the VRT
gdal.Warp(
    output_geotiff,
    output_vrt,
    dstSRS="EPSG:4326",
    format="GTiff",
    xRes=xRes,
    yRes=yRes,
    resampleAlg="near"
)

print(f"✅ Warped and saved: {output_geotiff}")
