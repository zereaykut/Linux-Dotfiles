# Modular Deep Learning Examples with Keras

This repository contains a collection of state-of-the-art Deep Learning models implemented in **Keras 3** and **TensorFlow** from https://keras.io/examples/. 

Unlike standard tutorials, these scripts have been refactored into **Object-Oriented classes**. This modular design separates model architecture from data loading, making it easy to:
1.  **Reuse** the models on your own custom datasets.
2.  **Import** the classes into other production pipelines.
3.  **Experiment** with hyperparameters without rewriting training loops.
4.  **Log** training progress professionally using Python's `logging` module.

---

## 📂 Project Structure & Module Details

### 1. Generative Models (`Generative/`)
Models focused on generating new data (text) based on learned patterns.

| File | Class Name | Description | Key Dependencies |
| :--- | :--- | :--- | :--- |
| `text_generation_fnet.py` | `FNetTextGenerator` | **Seq2Seq Chatbot**. Replaces standard Self-Attention with Fourier Transforms for faster mixing of tokens. | `tensorflow`, `keras` |
| `text_generation_gpt.py` | `GPTTextGenerator` | **Mini-GPT**. A causal decoder-only Transformer for text generation. Uses `KerasHub` for tokenization and sampling. | `keras-hub` |

### 2. Natural Language Processing (`NLP/`)
Solutions for classification, translation, and semantic understanding.

| File | Class Name | Description | Key Dependencies |
| :--- | :--- | :--- | :--- |
| `active_learning_review_classification.py` | `ActiveLearningSystem` | **Active Learning Loop**. iteratively trains a model by querying an "oracle" (simulated) for labels on the most uncertain data points. | `tensorflow`, `keras` |
| `neural_machine_translation_with_keras_hub.py` | `TranslatorSystem` | **Machine Translation**. A Transformer Encoder-Decoder architecture for translating text (e.g., English to Spanish). Uses WordPiece tokenization. | `keras-hub` |
| `semantic_similarity_with_bert.py` | `BertSimilarityClassifier` | **BERT NLI**. Fine-tunes a pre-trained BERT model to determine if sentence pairs contradict or entail each other. | `transformers` |
| `text_classification_from_scratch.py` | `TextClassifier` | **Conv1D Baseline**. A lightweight text classifier using 1D convolutions and Global Max Pooling. Includes an end-to-end exportable model. | `tensorflow` |
| `text_classification_with_transformer.py` | `TransformerClassifier` | **Transformer Encoder**. Uses Multi-Head Self-Attention and Positional Embeddings for text classification. | `tensorflow` |

### 3. Time Series (`Timeseries/`)
Forecasting and classification for sequential sensor or financial data.

| File | Class Name | Description | Key Dependencies |
| :--- | :--- | :--- | :--- |
| `timeseries_anomaly_detection.py` | `AnomalyDetector` | **Anomaly Detection**. Uses a Convolutional Autoencoder to learn "normal" patterns. Flags anomalies based on reconstruction error thresholding. | `pandas`, `matplotlib` |
| `timeseries_classification_from_scratch.py` | `TimeSeriesClassifier` | **FCN**. A Fully Convolutional Network with 3 blocks of `Conv1D -> BN -> ReLU` followed by Global Average Pooling. | `numpy` |
| `timeseries_classification_transformer.py` | `TransformerTimeSeriesClassifier` | **Transformer**. Adapts the "Attention Is All You Need" architecture for univariate time series classification. | `keras`, `numpy` |
| `timeseries_weather_forecasting.py` | `WeatherForecaster` | **LSTM Forecasting**. Uses Long Short-Term Memory layers to predict future values in multivariate time series (e.g., weather data). | `pandas` |

### 4. Computer Vision (`Vision/`)
Image classification, reconstruction, and captioning.

| File | Class Name | Description | Key Dependencies |
| :--- | :--- | :--- | :--- |
| `autoencoder.py` | `DenoisingAutoencoder` | **Denoising**. A standard Conv2D Encoder-Decoder that learns to remove noise from images. | `matplotlib` |
| `bit.py` | `BiTClassifier` | **BigTransfer (BiT)**. Uses a ResNet backbone pre-trained on ImageNet-21k for few-shot transfer learning. | `tensorflow_hub` |
| `cct.py` | `CCTClassifier` | **Compact Conv Transformer**. A hybrid architecture that tokenizes images using CNNs before passing them to a Transformer. Efficient for small datasets. | `keras` |
| `image_captioning.py` | `ImageCaptioningSystem` | **Image Captioning**. Combines an EfficientNet (CNN) encoder with a Transformer decoder to generate text descriptions of images. | `keras`, `tensorflow` |
| `image_classification_from_scratch.py` | `CustomImageClassifier` | **Xception-style CNN**. A robust CNN built from scratch with Residual connections and Separable Convolutions. | `keras` |
| `image_classification_with_vision_transformer.py` | `ViTClassifier` | **Standard ViT**. Implementation of the original "An Image is Worth 16x16 Words" paper. | `keras`, `keras.ops` |
| `mnist_convnet.py` | `SimpleImageClassifier` | **Basic CNN**. A simple Conv2D -> MaxPool architecture, perfect for MNIST/Fashion-MNIST benchmarking. | `numpy` |
| `shiftvit.py` | `ShiftViTClassifier` | **ShiftViT**. An attention-free ViT variant that uses zero-parameter shift operations to mix spatial information. | `keras` |
| `vit_small_ds.py` | `ViTSmallClassifier` | **ViT for Small Data**. Enhances standard ViT with Shifted Patch Tokenization (SPT) and Locality Self-Attention (LSA) to work on small datasets. | `keras` |

---

## 🚀 Usage Guide

### 1. Installation

Create a virtual environment and install the dependencies:

```bash
# Create env
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install requirements
pip install -r requirements.txt