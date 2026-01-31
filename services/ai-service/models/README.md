# Models Directory

This directory stores ML models for the AI service.

## Models

- `symptom-analyzer/` - NLP model for symptom extraction
- `image-classifier/` - CNN for medical image classification  
- `diagnosis-generator/` - Ensemble model for diagnosis prediction

## Usage

Models are loaded at service startup and cached in memory.

## Note

Large model files (`.bin`, `.pt`, `.onnx`, `.h5`) are excluded from Git.
Download models separately or use the model download script.
