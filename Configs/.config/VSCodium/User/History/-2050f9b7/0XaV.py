import os
import shutil
import re
import string
import logging
import random
import numpy as np
import matplotlib.pyplot as plt
import tensorflow as tf
import keras
from keras import layers
from keras import ops

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# --- Text Standardization ---

def custom_standardization(input_data):
    """
    Standardizes text: lowercase + strip HTML break tags + strip punctuation.
    """
    lowercase = tf.strings.lower(input_data)
    stripped_html = tf.strings.regex_replace(lowercase, "<br />", " ")
    return tf.strings.regex_replace(
        stripped_html, f"[{re.escape(string.punctuation)}]", ""
    )

# --- Main Manager Class ---

class ActiveLearningSystem:
    def __init__(
        self,
        max_features=20000,
        sequence_length=500,
        embedding_dim=128,
        batch_size=32,
        initial_train_split=0.1,  # Start with 10% of data
        pool_split=0.9,           # 90% in unlabeled pool
        sampling_size=5000,       # Number of samples to query per round
        num_iterations=5,         # Number of active learning rounds
        validation_split=0.1
    ):
        """
        Initializes hyperparameters for the Active Learning Loop.
        """
        self.max_features = max_features
        self.sequence_length = sequence_length
        self.embedding_dim = embedding_dim
        self.batch_size = batch_size
        
        self.initial_train_split = initial_train_split
        self.pool_split = pool_split
        self.sampling_size = sampling_size
        self.num_iterations = num_iterations
        self.validation_split = validation_split
        
        self.vectorize_layer = None
        self.model = None
        
        # Data containers (Lists of strings/int)
        self.train_sentences = []
        self.train_labels = []
        self.pool_sentences = []
        self.pool_labels = []
        self.val_sentences = []
        self.val_labels = []
        self.test_sentences = []
        self.test_labels = []
        
        # Tracking metrics
        self.history_log = []

        logger.info("Initialized Active Learning System.")

    def _vectorize_text(self, text, label):
        """Map function for TF Dataset."""
        text = tf.expand_dims(text, -1)
        return self.vectorize_layer(text), label

    def prepare_data_loaders(self):
        """
        Converts internal list data into highly optimized TF Datasets.
        Called at the start of every Active Learning Loop iteration.
        """
        # Training Data
        train_ds = tf.data.Dataset.from_tensor_slices((self.train_sentences, self.train_labels))
        train_ds = train_ds.map(self._vectorize_text, num_parallel_calls=tf.data.AUTOTUNE)
        train_ds = train_ds.batch(self.batch_size).prefetch(tf.data.AUTOTUNE)
        
        # Validation Data
        val_ds = tf.data.Dataset.from_tensor_slices((self.val_sentences, self.val_labels))
        val_ds = val_ds.map(self._vectorize_text, num_parallel_calls=tf.data.AUTOTUNE)
        val_ds = val_ds.batch(self.batch_size).prefetch(tf.data.AUTOTUNE)

        # Unlabeled Pool (No labels needed for prediction, but we keep them for oracle simulation)
        pool_ds = tf.data.Dataset.from_tensor_slices((self.pool_sentences, self.pool_labels))
        pool_ds = pool_ds.map(self._vectorize_text, num_parallel_calls=tf.data.AUTOTUNE)
        pool_ds = pool_ds.batch(self.batch_size).prefetch(tf.data.AUTOTUNE)
        
        # Test Data
        test_ds = tf.data.Dataset.from_tensor_slices((self.test_sentences, self.test_labels))
        test_ds = test_ds.map(self._vectorize_text, num_parallel_calls=tf.data.AUTOTUNE)
        test_ds = test_ds.batch(self.batch_size).prefetch(tf.data.AUTOTUNE)
        
        return train_ds, val_ds, pool_ds, test_ds

    def initialize_data(self, dataset_dir):
        """
        Loads raw data, vectorizes it, and creates the initial Train/Pool/Test splits.
        """
        logger.info(f"Loading data from {dataset_dir}...")
        
        # 1. Load Everything
        raw_full_ds = keras.utils.text_dataset_from_directory(
            os.path.join(dataset_dir, "train"),
            batch_size=None, # Load as individual samples
            shuffle=True,
            seed=42
        )
        
        sentences = []
        labels = []
        for text, label in raw_full_ds:
            sentences.append(text.numpy().decode("utf-8"))
            labels.append(label.numpy())
            
        sentences = np.array(sentences)
        labels = np.array(labels)
        
        # 2. Fit Vectorizer (on ALL data or large subset for robust vocab)
        logger.info("Fitting TextVectorization layer...")
        self.vectorize_layer = layers.TextVectorization(
            standardize=custom_standardization,
            max_tokens=self.max_features,
            output_mode="int",
            output_sequence_length=self.sequence_length,
        )
        self.vectorize_layer.adapt(
            tf.data.Dataset.from_tensor_slices(sentences).batch(128)
        )
        
        # 3. Create Splits
        total = len(sentences)
        n_train = int(total * self.initial_train_split)
        n_val = int(total * self.validation_split)
        n_test = 2000 # Fixed test set size for consistent reporting
        
        # Remaining goes to pool
        # Indices: [Train ... Val ... Test ... Pool]
        idx_train_end = n_train
        idx_val_end = n_train + n_val
        idx_test_end = n_train + n_val + n_test
        
        self.train_sentences = list(sentences[:idx_train_end])
        self.train_labels = list(labels[:idx_train_end])
        
        self.val_sentences = list(sentences[idx_train_end:idx_val_end])
        self.val_labels = list(labels[idx_train_end:idx_val_end])
        
        self.test_sentences = list(sentences[idx_val_end:idx_test_end])
        self.test_labels = list(labels[idx_val_end:idx_test_end])
        
        self.pool_sentences = list(sentences[idx_test_end:])
        self.pool_labels = list(labels[idx_test_end:])
        
        logger.info(f"Initial Splits -- Train: {len(self.train_sentences)}, Pool: {len(self.pool_sentences)}, Test: {len(self.test_sentences)}")

    def build_model(self):
        """
        Constructs a simple CNN for text classification.
        Re-initialized every loop to prove learning efficiency.
        """
        inputs = keras.Input(shape=(self.sequence_length,), dtype="int64")
        x = layers.Embedding(self.max_features, self.embedding_dim)(inputs)
        x = layers.Dropout(0.5)(x)
        x = layers.Conv1D(128, 7, padding="valid", activation="relu", strides=3)(x)
        x = layers.Conv1D(128, 7, padding="valid", activation="relu", strides=3)(x)
        x = layers.GlobalMaxPooling1D()(x)
        x = layers.Dense(128, activation="relu")(x)
        x = layers.Dropout(0.5)(x)
        predictions = layers.Dense(1, activation="sigmoid", name="predictions")(x)

        self.model = keras.Model(inputs, predictions, name="active_learning_model")
        self.model.compile(
            loss="binary_crossentropy", 
            optimizer="adam", 
            metrics=["accuracy"]
        )

    def query_oracle(self, pool_ds):
        """
        The core Active Learning logic (Least Confidence Sampling).
        Returns indices of the 'sampling_size' most uncertain samples in the pool.
        """
        logger.info("Querying model for uncertainty...")
        predictions = self.model.predict(pool_ds, verbose=0)
        
        # Calculate uncertainty: |p - 0.5|. 
        # Smaller value = closer to 0.5 = higher uncertainty.
        # We want the SMALLEST values.
        uncertainty = np.abs(predictions.squeeze() - 0.5)
        
        # Get indices of the smallest values
        # argsort gives indices that sort the array from low to high
        sorted_indices = np.argsort(uncertainty)
        selected_indices = sorted_indices[:self.sampling_size]
        
        return selected_indices

    def train_active_learning_loop(self):
        """
        Executes the full iterative training process.
        """
        if not self.train_sentences:
            raise ValueError("Data not initialized.")

        for i in range(self.num_iterations):
            logger.info(f"--- Iteration {i+1}/{self.num_iterations} ---")
            logger.info(f"Training set size: {len(self.train_sentences)}")
            
            # 1. Prepare DataLoaders
            train_ds, val_ds, pool_ds, test_ds = self.prepare_data_loaders()
            
            # 2. Re-build and Train Model
            # Re-build to ensure not just fine-tuning, but learning fresh from the larger dataset
            self.build_model()
            
            # Use Early Stopping to prevent overfitting on small data
            callback = keras.callbacks.EarlyStopping(monitor="val_loss", patience=3)
            
            self.model.fit(
                train_ds,
                validation_data=val_ds,
                epochs=20,
                callbacks=[callback],
                verbose=1
            )
            
            # 3. Evaluate
            loss, acc = self.model.evaluate(test_ds, verbose=0)
            logger.info(f"Test Accuracy: {acc:.4f}")
            self.history_log.append(acc)
            
            if i == self.num_iterations - 1:
                break
                
            # 4. Active Learning Step: Query Oracle
            # Note: pool_ds order matches self.pool_sentences order
            selected_indices = self.query_oracle(pool_ds)
            
            # 5. Update Datasets
            # Move selected items from Pool -> Train
            # Use a set for O(1) lookups during filtering
            selected_set = set(selected_indices)
            
            new_train_sent = []
            new_train_lbl = []
            remaining_pool_sent = []
            remaining_pool_lbl = []
            
            for idx, (sent, lbl) in enumerate(zip(self.pool_sentences, self.pool_labels)):
                if idx in selected_set:
                    new_train_sent.append(sent)
                    new_train_lbl.append(lbl)
                else:
                    remaining_pool_sent.append(sent)
                    remaining_pool_lbl.append(lbl)
            
            # Extend training data
            self.train_sentences.extend(new_train_sent)
            self.train_labels.extend(new_train_lbl)
            
            # Replace pool with remaining
            self.pool_sentences = remaining_pool_sent
            self.pool_labels = remaining_pool_lbl
            
            logger.info(f"Moved {len(new_train_sent)} samples from Pool to Train.")

    def plot_results(self):
        """Visualize accuracy improvement over iterations."""
        x = range(1, len(self.history_log) + 1)
        plt.plot(x, self.history_log, marker='o')
        plt.xlabel("Iteration")
        plt.ylabel("Test Accuracy")
        plt.title("Active Learning Performance")
        plt.grid()
        plt.show()

# --- Download Data ---

def setup_imdb_data():
    if not os.path.exists("aclImdb"):
        logger.info("Downloading IMDB dataset...")
        os.system("curl -O https://ai.stanford.edu/~amaas/data/sentiment/aclImdb_v1.tar.gz")
        os.system("tar -xf aclImdb_v1.tar.gz")
        os.system("rm aclImdb_v1.tar.gz")
        # Remove unsupervised training data
        unsup_path = os.path.join("aclImdb", "train", "unsup")
        if os.path.exists(unsup_path):
            shutil.rmtree(unsup_path)
    else:
        logger.info("IMDB dataset found locally.")


if __name__ == "__main__":
    # 1. Download Data
    setup_imdb_data()
    
    # 2. Instantiate System
    # 2000 new examples per round, for 5 rounds.
    system = ActiveLearningSystem(
        sampling_size=2000,
        num_iterations=5,
        initial_train_split=0.05 # Start very small (5%) to show benefit
    )
    
    # 3. Load Data
    system.initialize_data(dataset_dir="aclImdb")
    
    # 4. Run Active Learning Loop
    system.train_active_learning_loop()
    
    # 5. Visualize
    system.plot_results()