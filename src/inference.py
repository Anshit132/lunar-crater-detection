import os
from ultralytics import YOLO
from PIL import Image

MODEL_PATH = "yolov8Crater.pt"
IMAGE_DIR = "Tiles"
OUTPUT_DIR = "yolo_predictions"

def run_inference(model_path=MODEL_PATH, image_dir=IMAGE_DIR, output_dir=OUTPUT_DIR, conf=0.25):
    """
    Loads a YOLOv8 model and runs inference on all PNG images inside the tiles directory,
    saving the predicted bounding box coordinates in YOLO format (.txt).
    """
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Trained YOLO model weights not found at: {model_path}")
    if not os.path.exists(image_dir):
        raise FileNotFoundError(f"Image directory not found: {image_dir}")

    os.makedirs(output_dir, exist_ok=True)

    # Load YOLOv8 model
    model = YOLO(model_path)

    # Gather images
    image_files = sorted([f for f in os.listdir(image_dir) if f.endswith(".png")])
    if not image_files:
        print(f"⚠️ No PNG files found in {image_dir}")
        return

    print(f"🚀 Running YOLOv8 inference on {len(image_files)} tiles in '{image_dir}'...")

    for img_name in image_files:
        img_path = os.path.join(image_dir, img_name)
        result = model.predict(img_path, save=True, conf=conf, verbose=False)[0]

        # Save predictions in YOLO format: <class> <x_center> <y_center> <width> <height>
        if result.boxes is not None and result.boxes.xywhn is not None:
            preds = result.boxes.xywhn.cpu().numpy()  # normalized [x_center, y_center, w, h]
            classes = result.boxes.cls.cpu().numpy()  # class IDs

            output_txt = os.path.join(output_dir, img_name.replace(".png", ".txt"))
            with open(output_txt, "w") as f:
                for cls, box in zip(classes, preds):
                    line = f"{int(cls)} {' '.join(map(str, box))}\n"
                    f.write(line)

    print(f"✅ Inference complete. Predictions saved to '{output_dir}/'")

if __name__ == "__main__":
    run_inference()
