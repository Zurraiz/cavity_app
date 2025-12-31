# AI-Powered Dental Caries Detection System

An intelligent web application that leverages deep learning to detect and analyze dental cavities in teeth photographic images. This system provides automated dental diagnosis assistance using state-of-the-art computer vision techniques.

## 🎯 What This Project Does

This application helps dentists, dental professionals and common people identify and assess tooth decay (caries) by:

1. **Detecting Cavities**: Automatically identifies locations of cavities in dental images
2. **Segmenting Lesions**: Provides precise pixel-level outlines of affected areas for detailed analysis
3. **Estimating Depth**: Classifies cavity severity into three clinical stages:
   - **Enamel** (superficial lesion) - Early-stage decay
   - **Dentin** (moderate lesion) - Mid-stage decay requiring intervention
   - **Pulpal** (deep lesion) - Advanced decay, potential root canal needed

## 🧠 Technology Stack

### Core AI/ML Technologies
- **YOLOv8** (You Only Look Once v8) - State-of-the-art real-time object detection and segmentation
- **OpenCV** - Computer vision library for image processing and analysis
- **scikit-image** - Advanced image processing (Local Binary Pattern texture analysis)
- **NumPy** - Numerical computing for feature extraction

### Backend & Deployment
- **Flask** - Lightweight Python web framework for REST API
- **Gunicorn** - Production-grade WSGI HTTP server
- **Docker** - Containerization for consistent deployment
- **Google Cloud Run** - Serverless deployment platform 

### Frontend
- **Vanilla JavaScript** - Interactive web interface
- **HTML5 Canvas API** - Real-time image visualization and annotation

## 🔬 How It Works (High-Level Architecture)

```
User Upload Image 
    ↓
Flask REST API Endpoints
    ↓
┌─────────────────────────────────────┐
│  Detection Mode: YOLOv8 Detection   │
│  - Bounding boxes around cavities   │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  Segmentation Mode: YOLOv8 Segment  │
│  - Precise cavity outlines          │
│  - Color-coded visualization        │
└─────────────────────────────────────┘
    ↓
┌─────────────────────────────────────┐
│  Feature Extraction & Analysis      │
│  - HSV color space analysis         │
│  - LBP texture features             │
│  - Intensity & gradient metrics     │
└─────────────────────────────────────┘
    ↓
Depth Classification Algorithm
    ↓
Results Returned to Frontend
```

### Technical Details

**Model Training**:
- Trained on **DentalAI dataset** (https://datasetninja.com/dentalai)
- 30 epochs using YOLOv8 medium architecture
- Custom dataset from real dentists
- Custom dataset conversion from Supervisely to YOLOv8 format

**Depth Estimation Algorithm**:
Uses multi-feature analysis combining:
- Mean pixel intensity (darkness of lesion)
- Texture roughness via Local Binary Patterns (LBP)
- HSV color space metrics (hue, saturation)
- Gradient analysis (edge sharpness)
- Cavity area measurement

**Two Pre-trained Models**:
- `best.pt` (49.62 MB) - Object detection model
- `segment_best.pt` (137 MB) - Segmentation model

*
## 🚀 Quick Start


### Docker Deployment (Recommended)

```bash
# Build the image
docker build -t dental-ai .

# Run the container
docker run -p 8080:8080 dental-ai
```

### Cloud Deployment

See **[DEPLOYMENT.md](DEPLOYMENT.md)** for complete Google Cloud Run deployment instructions.

**Quick deploy command**:
```bash
gcloud run deploy yolov8-caries-detector \
  --source . \
  --region us-central1 \
  --platform managed \
  --allow-unauthenticated \
  --memory 2Gi \
  --cpu 2
```

## 💡 Use Cases

- **Dental Clinics**: Automated preliminary diagnosis assistance
- **Telehealth**: Remote dental consultations with AI-powered analysis
- **Education**: Teaching tool for dental students to learn cavity identification
- **Research**: Dental disease pattern analysis and epidemiological studies
- **Dental Insurance**: Automated claim verification for cavity-related procedures

## 🎓 Learning Outcomes

This project demonstrates:
- **Deep Learning**: Transfer learning with YOLOv8 for medical image analysis
- **Computer Vision**: Object detection, semantic segmentation, feature extraction
- **Web Development**: REST API design, real-time image processing
- **DevOps**: Containerization with Docker, cloud deployment strategies
- **Medical AI**: Clinical decision support system development

## 📊 Model Performance

- **Detection Model**: Trained for 30 epochs on DentalAI dataset
- **Classes Detected**: Tooth, Cavity, Caries, Crack
- **Inference Time**: ~1-3 seconds per image (CPU)
- **Segmentation Confidence**: 0.4 threshold, 0.45 IOU

## 🔧 API Endpoints

### POST `/detect`
Performs object detection with bounding boxes.

**Request**: multipart/form-data with `image_file`  
**Response**: JSON array of `[x1, y1, x2, y2, class_name]`

### POST `/segment`
Performs precise segmentation and depth analysis.

**Request**: multipart/form-data with `image_file`  
**Response**: JSON with `polygons` and `depth` estimation

## 🛠️ Customization & Retraining

### Train Your Own Model

1. Download DentalAI dataset: https://datasetninja.com/dentalai
2. Convert dataset using `convert.ipynb`
3. Train model using `train.ipynb`
4. Replace `best.pt` and `segment_best.pt` with your trained weights

### Modify Depth Classification

Edit the `estimate_lesion_depth()` function in `object_detector.py` to adjust classification thresholds based on your clinical requirements.

## ⚠️ Disclaimer

This is an educational and research tool. It should **NOT** be used as a substitute for professional dental diagnosis. Always consult with qualified dental professionals for medical advice and treatment decisions.

## 📄 License
