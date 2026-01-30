import os
import shutil
import string
import re
import logging
import tensorflow as tf
import keras
from keras import layers
import matplotlib.pyplot as plt

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

class TextClassifier:
    """
    An end-to-end text classification system using Conv1D.
    Encapsulates vectorization, model building, and training.
    """
    def __init__(
        self,
        max_features=20000,
        embedding_dim=128,
        sequence_length=500,
        batch_size=32,
        seed=42
    ):
        """
        Initialize hyperparameters.
        """
        self.max_features = max_features
        self.embedding_dim = embedding_dim
        self.sequence_length = sequence_length
        self.batch_size = batch_size
        self.seed = seed
        
        self.vectorize_layer = None
        self.model = None
        self.end_to_end_model = None
        self.train_ds = None
        self.val_ds = None
        self.test_ds = None
        
        logger.info("Initialized Text Classifier.")

    def _custom_standardization(self, input_data):
        """
        Standardizes text: lowercase + strip HTML break tags + strip punctuation.
        """
        lowercase = tf.strings.lower(input_data)
        stripped_html = tf.strings.regex_replace(lowercase, "<br />", " ")
        return tf.strings.regex_replace(
            stripped_html, f"[{re.escape(string.punctuation)}]", ""
        )

    def prepare_data(self, data_dir, validation_split=0.2):
        """
        Loads data from directory structure (class_a/file.txt, class_b/file.txt).
        Prepares raw datasets and fits the TextVectorization layer.
        """
        logger.info(f"Loading data from {data_dir}...")
        
        # 1. Load Raw Training Data (and split for validation)
        # subset='both' returns (train, val) tuple
        raw_train_ds, raw_val_ds = keras.utils.text_dataset_from_directory(
            os.path.join(data_dir, "train"),
            batch_size=self.batch_size,
            validation_split=validation_split,
            subset="both",
            seed=self.seed
        )

        # 2. Load Raw Test Data
        raw_test_ds = keras.utils.text_dataset_from_directory(
            os.path.join(data_dir, "test"),
            batch_size=self.batch_size
        )
        
        logger.info(f"Found {len(raw_train_ds)} train batches and {len(raw_val_ds)} val batches.")

        # 3. Fit Text Vectorization
        logger.info("Adapting TextVectorization layer...")
        self.vectorize_layer = layers.TextVectorization(
            standardize=self._custom_standardization,
            max_tokens=self.max_features,
            output_mode="int",
            output_sequence_length=self.sequence_length,
        )
        
        # Make a text-only dataset (no labels) to adapt the layer
        text_ds = raw_train_ds.map(lambda x, y: x)
        self.vectorize_layer.adapt(text_ds)
        
        vocab_size = self.vectorize_layer.vocabulary_size()
        logger.info(f"Vocabulary size: {vocab_size}")

        # 4. Create Final Vectorized Datasets
        def vectorize_text(text, label):
            text = tf.expand_dims(text, -1)
            return self.vectorize_layer(text), label

        # Map vectorization and optimize performance
        self.train_ds = raw_train_ds.map(vectorize_text).cache().prefetch(tf.data.AUTOTUNE)
        self.val_ds = raw_val_ds.map(vectorize_text).cache().prefetch(tf.data.AUTOTUNE)
        self.test_ds = raw_test_ds.map(vectorize_text).cache().prefetch(tf.data.AUTOTUNE)
        
        # Keep raw test ds for end-to-end evaluation later
        self.raw_test_ds = raw_test_ds
        logger.info("Data pipelines ready.")

    def build_model(self):
        """
        Constructs the Conv1D-based classification model.
        Structure: Embedding -> Dropout -> Conv1D -> GlobalMax -> Dense -> Output
        """
        logger.info("Building model architecture...")
        
        inputs = keras.Input(shape=(None,), dtype="int64")
        
        # Embedding: Maps int indices to dense vectors
        x = layers.Embedding(self.max_features, self.embedding_dim)(inputs)
        x = layers.Dropout(0.5)(x)

        # Conv1D: Finds patterns (ngrams) in the sequence
        x = layers.Conv1D(128, 7, padding="valid", activation="relu", strides=3)(x)
        x = layers.Conv1D(128, 7, padding="valid", activation="relu", strides=3)(x)
        
        # GlobalMaxPool: Takes the strongest signal from the filters
        x = layers.GlobalMaxPooling1D()(x)

        # Hidden Layer
        x = layers.Dense(128, activation="relu")(x)
        x = layers.Dropout(0.5)(x)

        # Output Layer (Binary Classification)
        predictions = layers.Dense(1, activation="sigmoid", name="predictions")(x)

        self.model = keras.Model(inputs, predictions, name="text_classifier")
        
        self.model.compile(
            loss="binary_crossentropy", 
            optimizer="adam", 
            metrics=["accuracy"]
        )
        logger.info("Model built successfully.")

    def train(self, epochs=3):
        """
        Trains the compiled model.
        """
        if self.model is None:
            raise ValueError("Model not built.")
        
        logger.info(f"Starting training for {epochs} epochs...")
        history = self.model.fit(
            self.train_ds,
            validation_data=self.val_ds,
            epochs=epochs
        )
        return history

    def evaluate(self):
        """
        Evaluates the model on the test set.
        """
        if self.model is None:
             raise ValueError("Model not trained.")
        
        logger.info("Evaluating on test set...")
        loss, accuracy = self.model.evaluate(self.test_ds)
        logger.info(f"Test Accuracy: {accuracy:.4f}")
        return accuracy

    def export_end_to_end_model(self):
        """
        Creates a new model that accepts raw strings (not indices).
        Includes the TextVectorization layer inside the model.
        Useful for deployment.
        """
        logger.info("Creating end-to-end inference model...")
        inputs = keras.Input(shape=(1,), dtype="string")
        indices = self.vectorize_layer(inputs)
        outputs = self.model(indices)
        
        self.end_to_end_model = keras.Model(inputs, outputs)
        self.end_to_end_model.compile(
            loss="binary_crossentropy", optimizer="adam", metrics=["accuracy"]
        )
        return self.end_to_end_model

# --- Helper: Data Download & Cleanup ---

def setup_imdb_data():
    """
    Downloads and cleans the IMDB dataset structure.
    """
    if not os.path.exists("aclImdb"):
        logger.info("Downloading IMDB dataset...")
        os.system("curl -O https://ai.stanford.edu/~amaas/data/sentiment/aclImdb_v1.tar.gz")
        os.system("tar -xf aclImdb_v1.tar.gz")
        os.system("rm aclImdb_v1.tar.gz")
        
        # Remove unsupervised training data (not needed for this task)
        unsup_path = os.path.join("aclImdb", "train", "unsup")
        if os.path.exists(unsup_path):
            shutil.rmtree(unsup_path)
            
        logger.info("Download and cleanup complete.")
    else:
        logger.info("IMDB dataset found locally.")


if __name__ == "__main__":
    # 1. Download Data
    setup_imdb_data()
    
    # 2. Instantiate Classifier
    classifier = TextClassifier(
        max_features=20000, 
        embedding_dim=128, 
        sequence_length=500,
        batch_size=32
    )
    
    # 3. Prepare Data
    # Pointing to the extracted folder "aclImdb"
    classifier.prepare_data(data_dir="aclImdb")
    
    # 4. Build Model
    classifier.build_model()
    
    # 5. Train
    history = classifier.train(epochs=3)
    
    # 6. Evaluate
    classifier.evaluate()
    
    # 7. Test End-to-End Model (Raw String Input)
    inference_model = classifier.export_end_to_end_model()
    
    # Test on a few custom strings
    sample_reviews = [
        "This movie was fantastic! I loved the acting.",
        "Terrible film, completely wasted my time.",
        "It was okay, not great but not bad."
    ]
    predictions = inference_model.predict(sample_reviews)
    
    print("\n--- Custom Predictions ---")
    for review, pred in zip(sample_reviews, predictions):
        sentiment = "Positive" if pred[0] > 0.5 else "Negative"
        print(f"Review: '{review}' -> Sentiment: {sentiment} ({pred[0]:.4f})")