import os
import logging
import numpy as np
import keras
from keras import layers
import matplotlib.pyplot as plt

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

class TransformerTimeSeriesClassifier:
    """
    A Transformer-based model for Time Series Classification.
    Adapted from 'Attention Is All You Need' for univariate time series.
    """
    def __init__(
        self,
        input_shape,
        n_classes,
        head_size=256,
        num_heads=4,
        ff_dim=4,
        num_transformer_blocks=4,
        mlp_units=[128],
        dropout=0,
        mlp_dropout=0,
        learning_rate=1e-4
    ):
        """
        Initialize model hyperparameters.
        """
        self.input_shape = input_shape
        self.n_classes = n_classes
        self.head_size = head_size
        self.num_heads = num_heads
        self.ff_dim = ff_dim
        self.num_transformer_blocks = num_transformer_blocks
        self.mlp_units = mlp_units
        self.dropout = dropout
        self.mlp_dropout = mlp_dropout
        self.learning_rate = learning_rate
        
        self.model = None
        self.callbacks = []
        
        logger.info(f"Initialized Transformer Classifier for input {input_shape}")

    def _transformer_encoder(self, inputs):
        """
        Internal helper: Creates a single Transformer Encoder block.
        Normalization -> Attention -> Add -> Normalization -> FeedForward -> Add
        """
        # Attention Block
        x = layers.LayerNormalization(epsilon=1e-6)(inputs)
        x = layers.MultiHeadAttention(
            key_dim=self.head_size, num_heads=self.num_heads, dropout=self.dropout
        )(x, x)
        x = layers.Dropout(self.dropout)(x)
        res = x + inputs

        # Feed Forward Block
        x = layers.LayerNormalization(epsilon=1e-6)(res)
        x = layers.Conv1D(filters=self.ff_dim, kernel_size=1, activation="relu")(x)
        x = layers.Dropout(self.dropout)(x)
        x = layers.Conv1D(filters=inputs.shape[-1], kernel_size=1)(x)
        return x + res

    def build_model(self):
        """
        Constructs the full Transformer architecture.
        """
        logger.info("Building Transformer architecture...")
        inputs = keras.Input(shape=self.input_shape)
        x = inputs
        
        # Stack Transformer Blocks
        for _ in range(self.num_transformer_blocks):
            x = self._transformer_encoder(x)

        # Classification Head
        # Use channels_last to average over the time dimension
        x = layers.GlobalAveragePooling1D(data_format="channels_last")(x)
        
        for dim in self.mlp_units:
            x = layers.Dense(dim, activation="relu")(x)
            x = layers.Dropout(self.mlp_dropout)(x)
            
        outputs = layers.Dense(self.n_classes, activation="softmax")(x)
        
        self.model = keras.Model(inputs, outputs)
        
        self.model.compile(
            loss="sparse_categorical_crossentropy",
            optimizer=keras.optimizers.Adam(learning_rate=self.learning_rate),
            metrics=["sparse_categorical_accuracy"],
        )
        
        self.callbacks = [
            keras.callbacks.EarlyStopping(patience=10, restore_best_weights=True)
        ]
        
        logger.info("Model built successfully.")

    def train(self, x_train, y_train, epochs=150, batch_size=64, validation_split=0.2):
        """
        Trains the model.
        """
        if self.model is None:
            raise ValueError("Model not built. Call build_model() first.")
        
        logger.info(f"Starting training for {epochs} epochs...")
        history = self.model.fit(
            x_train,
            y_train,
            validation_split=validation_split,
            epochs=epochs,
            batch_size=batch_size,
            callbacks=self.callbacks,
            verbose=1,
        )
        return history

    def evaluate(self, x_test, y_test):
        """
        Evaluates model performance on test set.
        """
        logger.info("Evaluating on test set...")
        loss, accuracy = self.model.evaluate(x_test, y_test, verbose=1)
        logger.info(f"Test Accuracy: {accuracy:.4f}")
        logger.info(f"Test Loss: {loss:.4f}")
        return accuracy

# --- Data Helper ---

def load_data(url="https://raw.githubusercontent.com/hfawaz/cd-diagram/master/FordA"):
    """
    Downloads and parses UCR-style TSV data (FordA).
    """
    def read_ucr(filename):
        data = np.loadtxt(filename, delimiter="\t")
        y = data[:, 0]
        x = data[:, 1:]
        return x, y.astype(int)

    logger.info("Checking dataset...")
    root_url = url
    
    # Download logic (simulated for simplicity, assumes files exist or handles manually)
    import urllib.request
    
    # URL suffixes
    train_url = root_url + "_TRAIN.tsv" if not root_url.endswith(".tsv") else root_url
    test_url = root_url + "_TEST.tsv" if not root_url.endswith(".tsv") else root_url.replace("TRAIN", "TEST")
    
    if not os.path.exists("FordA_TRAIN.tsv"):
        logger.info("Downloading FordA_TRAIN.tsv...")
        urllib.request.urlretrieve("https://raw.githubusercontent.com/hfawaz/cd-diagram/master/FordA/FordA_TRAIN.tsv", "FordA_TRAIN.tsv")
        
    if not os.path.exists("FordA_TEST.tsv"):
        logger.info("Downloading FordA_TEST.tsv...")
        urllib.request.urlretrieve("https://raw.githubusercontent.com/hfawaz/cd-diagram/master/FordA/FordA_TEST.tsv", "FordA_TEST.tsv")

    x_train, y_train = read_ucr("FordA_TRAIN.tsv")
    x_test, y_test = read_ucr("FordA_TEST.tsv")
    
    # Preprocessing
    x_train = x_train.reshape((x_train.shape[0], x_train.shape[1], 1))
    x_test = x_test.reshape((x_test.shape[0], x_test.shape[1], 1))
    
    n_classes = len(np.unique(y_train))

    # Fix labels (-1 -> 0, 1 -> 1) if binary
    if n_classes == 2:
        y_train[y_train == -1] = 0
        y_test[y_test == -1] = 0
    
    # Shuffle Train
    idx = np.random.permutation(len(x_train))
    x_train = x_train[idx]
    y_train = y_train[idx]

    logger.info(f"Data loaded. Train shape: {x_train.shape}")
    return (x_train, y_train), (x_test, y_test), n_classes


if __name__ == "__main__":
    # 1. Load Data
    (x_train, y_train), (x_test, y_test), n_classes = load_data()
    
    input_shape = x_train.shape[1:]
    
    # 2. Instantiate Classifier
    classifier = TransformerTimeSeriesClassifier(
        input_shape=input_shape,
        n_classes=n_classes,
        head_size=256,
        num_heads=4,
        ff_dim=4,
        num_transformer_blocks=4,
        mlp_units=[128],
        mlp_dropout=0.4,
        dropout=0.25,
    )
    
    # 3. Build Model
    classifier.build_model()
    
    # 4. Train
    # Using fewer epochs for demo purposes
    history = classifier.train(x_train, y_train, epochs=50, batch_size=64)
    
    # 5. Evaluate
    classifier.evaluate(x_test, y_test)
    
    # 6. Plot Results
    metric = "sparse_categorical_accuracy"
    plt.figure()
    plt.plot(history.history[metric])
    plt.plot(history.history["val_" + metric])
    plt.title("Model Accuracy")
    plt.ylabel("Accuracy")
    plt.xlabel("Epoch")
    plt.legend(["Train", "Val"], loc="best")
    plt.show()