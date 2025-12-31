from ultralytics import YOLO
from flask import request, Flask, jsonify
from waitress import serve
from PIL import Image, ImageDraw
import numpy as np
import cv2
from skimage.feature import local_binary_pattern
import logging

app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load models at startup
try:
    detection_model = YOLO("best.pt")
    segmentation_model = YOLO("segment_best.pt")
    logger.info(f"Detection model names: {detection_model.names}")
    logger.info(f"Segmentation model names: {segmentation_model.names}")
except Exception as e:
    logger.error(f"Model loading error: {e}")
    raise

@app.route("/")
def root():
    try:
        with open("index.html", encoding="utf-8") as file:
            return file.read()
    except Exception as e:
        logger.error(f"Error loading index.html: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/detect", methods=["POST"])
def detect():
    try:
        buf = request.files["image_file"]
        boxes = detect_objects_on_image(buf.stream)
        logger.info(f"Detection results: {boxes}")
        return jsonify(boxes)
    except Exception as e:
        logger.error(f"Detection error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/segment", methods=["POST"])
def segment():
    try:
        buf = request.files["image_file"]
        image = Image.open(buf.stream)
        polygons = segment_objects_on_image(image)
        # Log summary instead of full coordinates
        num_teeth = sum(1 for poly in polygons if poly[-1] == "Tooth")
        num_cavities = sum(1 for poly in polygons if poly[-1] == "Cavity")
        logger.info(f"Segmentation results: {num_teeth} Teeth, {num_cavities} Cavities")

        # Reset stream and draw predicted image
        buf.stream.seek(0)
        predicted_image = create_predicted_image(Image.open(buf.stream), polygons)

        # Save predicted image for frontend
        predicted_image.save("predicted_output.png")

        # Convert to OpenCV format for analysis
        image_np = np.array(predicted_image)
        image_bgr = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)
        hsv = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2HSV)

        # Extract mask from predicted image
        _, _, cavity_mask, _ = extract_masks_from_outlines(predicted_image)

        # Estimate depth
        depth_class, mean_intensity = estimate_lesion_depth(image_bgr, hsv, cavity_mask, polygons, num_cavities)
        depth_result = {"depth": depth_class, "intensity": float(mean_intensity)}

        logger.info(f"Depth estimation result: {depth_result}")
        return jsonify({"polygons": polygons, "depth": depth_result})

    except Exception as e:
        logger.error(f"Segmentation/depth error: {e}")
        return jsonify({"error": str(e)}), 500

def detect_objects_on_image(buf):
    results = detection_model.predict(Image.open(buf))
    result = results[0]
    output = []
    for box in result.boxes:
        x1, y1, x2, y2 = [round(x) for x in box.xyxy[0].tolist()]
        class_id = box.cls[0].item()
        class_name = result.names[class_id]
        if class_name == 'Cavitys': class_name = 'Cavity'
        if class_name == 'Tooths': class_name = 'Tooth'
        output.append([x1, y1, x2, y2, class_name])
    return output

def segment_objects_on_image(image):
    results = segmentation_model.predict(image, conf=0.4, iou=0.45, device='cpu')
    result = results[0]
    output = []
    if result.masks is not None:
        for mask_xy, class_id in zip(result.masks.xy, result.boxes.cls.cpu().numpy().astype(int)):
            if class_id >= len(result.names): continue
            class_name = result.names[class_id]
            if class_name == 'Cavitys': class_name = 'Cavity'
            if class_name == 'Tooths': class_name = 'Tooth'
            points = mask_xy.flatten().tolist()
            output.append([round(x) for x in points] + [class_name])
    return output

def create_predicted_image(image, polygons):
    """
    Draws the segmentation polygons using OpenCV (same as Colab).
    """
    img_np = np.array(image.convert("RGB"))
    img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
    overlay = img_bgr.copy()

    for poly in polygons:
        label = poly[-1]
        points = poly[:-1]
        if len(points) < 6:
            continue

        pts = np.array([[points[i], points[i + 1]] for i in range(0, len(points), 2)], dtype=np.int32)
        pts = pts.reshape((-1, 1, 2))

        # Blue for cavities, green for teeth
        color = (255, 0, 0) if label == "Cavity" else (0, 255, 0) if label == "Tooth" else (0, 0, 0)
        cv2.fillPoly(overlay, [pts], color, lineType=cv2.LINE_8)
        cv2.polylines(overlay, [pts], isClosed=True, color=color, thickness=2, lineType=cv2.LINE_8)

    # Save image for frontend
    cv2.imwrite("predicted_output.png", overlay)

    # Convert back to PIL.Image for return
    final_rgb = cv2.cvtColor(overlay, cv2.COLOR_BGR2RGB)
    return Image.fromarray(final_rgb)

def extract_masks_from_outlines(image):
    img_np = np.array(image.convert("RGB"))
    img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
    hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)

    # HSV ranges for blue (for cavities) and green (for teeth)
    blue_lower = np.array([100, 100, 100])
    blue_upper = np.array([140, 255, 255])
    green_lower = np.array([50, 100, 100])
    green_upper = np.array([70, 255, 255])

    blue_mask = cv2.inRange(hsv, blue_lower, blue_upper)
    green_mask = cv2.inRange(hsv, green_lower, green_upper)

    def fill_mask(mask):
        kernel = np.ones((5, 5), np.uint8)
        closed = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
        contours, _ = cv2.findContours(closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        filled = np.zeros_like(mask)
        cv2.drawContours(filled, contours, -1, 255, thickness=cv2.FILLED)
        return filled

    cavity_filled = fill_mask(blue_mask)
    tooth_filled = fill_mask(green_mask)
    return img_bgr, hsv, cavity_filled, tooth_filled

def extract_features(image, hsv, cavity_mask):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX)
    binary_mask = (cavity_mask > 127).astype(np.uint8)
    if np.sum(binary_mask) == 0:
        logger.info("No cavity detected in mask")
        return None, None, None, None, None, None

    cavity_area = np.sum(binary_mask) / 255
    radius = 3
    n_points = 8 * radius
    lbp = local_binary_pattern(gray, n_points, radius, method='uniform')
    lbp_vals = lbp[binary_mask == 1]
    texture_roughness = np.std(lbp_vals) if len(lbp_vals) > 0 else 0

    hsv_vals = hsv[binary_mask == 1]
    mean_hue = np.mean(hsv_vals[:, 0]) if len(hsv_vals) > 0 else 0
    mean_saturation = np.mean(hsv_vals[:, 1]) if len(hsv_vals) > 0 else 0

    lesion_pixels = gray[binary_mask == 1]
    mean_intensity = np.mean(lesion_pixels) if len(lesion_pixels) > 0 else 0
    intensity_variance = np.var(lesion_pixels) if len(lesion_pixels) > 0 else 0

    sobel = cv2.Sobel(gray, cv2.CV_64F, 1, 1, ksize=3)
    gradient = np.abs(sobel[binary_mask == 1])
    mean_gradient = np.mean(gradient) if len(gradient) > 0 else 0

    return mean_intensity, texture_roughness, mean_hue, mean_gradient, intensity_variance, cavity_area

def estimate_lesion_depth(image, hsv, cavity_mask, polygons, num_cavities):
    features = extract_features(image, hsv, cavity_mask)
    if features[0] is None:
        return "No lesion", 0.0

    mean_intensity, texture_roughness, mean_hue, mean_gradient, intensity_variance, cavity_area = features
    logger.info(f"Features - Intensity: {mean_intensity:.2f}, Texture Roughness: {texture_roughness:.3f}, "
                f"Hue: {mean_hue:.2f}, Gradient: {mean_gradient:.2f}, Intensity Variance: {intensity_variance:.2f}, "
                f"Area: {cavity_area:.0f} pixels")

    # Check for no lesion condition
    has_cavity = any(poly[-1] == "Cavity" for poly in polygons)
    if cavity_area == 0 or not has_cavity:
        return "No lesion", 0.0

    # Approximate average cavity area if multiple cavities
    avg_cavity_area = cavity_area / max(1, num_cavities) if num_cavities > 0 else cavity_area

    # Enamel classification with new rules
    if cavity_area < 10:  # Very small area
        return "Enamel (superficial lesion) ", mean_intensity
    if cavity_area > 50 and mean_intensity < 1.0:  # Large area, very low intensity
        return "Enamel (superficial lesion)", mean_intensity

    # Fallback Enamel conditions
    if cavity_area < 50 and (texture_roughness < 0.5 or intensity_variance < 50) and mean_gradient > 5:
        return "Enamel (superficial lesion)", mean_intensity

    # Dentin classification
    if cavity_area < 100 and intensity_variance > 50 and intensity_variance < 400 and \
       0.5 <= texture_roughness < 1.2 and mean_gradient > 5:
        return "Dentin (moderate lesion)", mean_intensity

    # Pulpal classification
    if (cavity_area > 50 and mean_gradient < 4) or (intensity_variance > 400 and mean_gradient < 5):
        return "Pulpal (deep lesion)", mean_intensity

    # Default to Pulpal
    return "Pulpal (deep lesion)", mean_intensity

if __name__ == "__main__":
    import os
    port = int(os.environ.get('PORT', 8080))
    serve(app, host='0.0.0.0', port=port)