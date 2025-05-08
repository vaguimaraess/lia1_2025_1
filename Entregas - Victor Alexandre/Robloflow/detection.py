from ultralytics import YOLO

# Load a COCO-pretrained YOLO12n model
model = YOLO("model/best100.pt")

# Run inference on the source
results = model(source="test1.mp4", show=True, conf=0.5, save=True)
