from osgeo import gdal

input_img = "Input/Data/20190907/ch2_ohr_ncp_20190907T0438126359_d_img_g26.xml"
output_tif = "ohrc_image.tif"

dataset = gdal.Open(input_img, gdal.GA_ReadOnly)
if dataset is None:
    raise RuntimeError("Error: Cannot open the input .img file!")

gdal.Translate(
    output_tif,
    dataset,
    format="GTiff",
    creationOptions=["COMPRESS=LZW", "PREDICTOR=2"],
    outputType=gdal.GDT_Byte
)
dataset = None
print(f"✅ Converted to GeoTIFF: {output_tif}")
