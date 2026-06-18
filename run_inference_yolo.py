import os
from ultralytics import YOLO
from PIL import Image

# CONFIG
model_path = "yolov8Crater.pt"  # path to your trained YOLOv8 model
image_dir = "Tiles"  # directory containing tile PNGs
output_dir = "yolo_predictions"  # where to save .txt prediction files
os.makedirs(output_dir, exist_ok=True)

# Load YOLOv8 model
model = YOLO(model_path)

# Run inference on each image
image_files = [f for f in os.listdir(image_dir) if f.endswith(".png")]
for img_name in image_files:
    img_path = os.path.join(image_dir, img_name)
    result = model.predict(img_path, save=True, conf=0.25)[0]

    # Save predictions in YOLO format: <class> <x_center> <y_center> <width> <height>
    if result.boxes is not None and result.boxes.xywhn is not None:
        preds = result.boxes.xywhn.cpu().numpy()  # normalized [x_center, y_center, w, h]
        classes = result.boxes.cls.cpu().numpy()  # class IDs

        output_txt = os.path.join(output_dir, img_name.replace(".png", ".txt"))
        with open(output_txt, "w") as f:
            for cls, box in zip(classes, preds):
                line = f"{int(cls)} {' '.join(map(str, box))}\n"
                f.write(line)

print(f"✅ Inference complete. Predictions saved to '{output_dir}'")
