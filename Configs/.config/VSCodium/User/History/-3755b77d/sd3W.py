import os
import logging
import numpy as np
import matplotlib.pyplot as plt
import keras
from keras import layers

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

class TimeSeriesClassifier:
    """
    A Fully Convolutional Neural Network (FCN) for Time Series Classification.
    """
    def __init__(self, input_shape, num_classes, batch_size=32, epochs=500):
        """
        Initialize configuration.
        """
        self.input_shape = input_shape
        self.num_classes = num_classes
        self.batch_size = batch_size
        self.epochs = epochs
        
        self.model = None
        self.callbacks = []
        
        logger.info(f"Initialized Classifier for input {input_shape}")

    def build_model(self):
        """
        Constructs the 1D CNN architecture.
        Structure: 3x (Conv1D -> BN -> ReLU) -> GAP -> Dense
        """
        logger.info("Building model architecture...")
        inputs = keras.Input(shape=self.input_shape)

        # Block 1
        x = layers.Conv1D(filters=64, kernel_size=3, padding="same")(inputs)
        x = layers.BatchNormalization()(x)
        x = layers.ReLU()(x)

        # Block 2
        x = layers.Conv1D(filters=64, kernel_size=3, padding="same")(x)
        x = layers.BatchNormalization()(x)
        x = layers.ReLU()(x)

        # Block 3
        x = layers.Conv1D(filters=64, kernel_size=3, padding="same")(x)
        x = layers.BatchNormalization()(x)
        x = layers.ReLU()(x)

        # Classification Head
        x = layers.GlobalAveragePooling1D()(x)
        outputs = layers.Dense(self.num_classes, activation="softmax")(x)

        self.model = keras.Model(inputs=inputs, outputs=outputs)
        
        self.model.compile(
            optimizer="adam",
            loss="sparse_categorical_crossentropy",
            metrics=["sparse_categorical_accuracy"],
        )
        
        # Setup Callbacks
        self.callbacks = [
            keras.callbacks.ModelCheckpoint(
                "best_model.keras", save_best_only=True, monitor="val_loss"
            ),
            keras.callbacks.ReduceLROnPlateau(
                monitor="val_loss", factor=0.5, patience=20, min_lr=0.0001
            ),
            keras.callbacks.EarlyStopping(monitor="val_loss", patience=50, verbose=1),
        ]
        
        logger.info("Model built successfully.")

    def train(self, x_train, y_train, validation_split=0.2):
        """
        Trains the model.
        """
        if self.model is None:
            raise ValueError("Model not built. Call build_model() first.")
        
        logger.info(f"Starting training for {self.epochs} epochs...")
        history = self.model.fit(
            x_train,
            y_train,
            batch_size=self.batch_size,
            epochs=self.epochs,
            callbacks=self.callbacks,
            validation_split=validation_split,
            verbose=1,
        )
        return history

    def evaluate(self, x_test, y_test):
        """
        Evaluates the model (loads best checkpoint first).
        """
        logger.info("Loading best model checkpoint...")
        self.model = keras.models.load_model("best_model.keras")
        
        logger.info("Evaluating on test set...")
        loss, accuracy = self.model.evaluate(x_test, y_test)
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
    
    # Download if not exists (using Keras utility)
    # Note: Keras usually downloads to ~/.keras/datasets/
    # Here we simulate local file reading assuming files are present or downloaded
    
    # For this example, we assume files are downloaded to current directory or handle download manually
    # Let's download them if missing
    import urllib.request
    
    if not os.path.exists("FordA_TRAIN.tsv"):
        logger.info("Downloading FordA_TRAIN.tsv...")
        urllib.request.urlretrieve(root_url + "_TRAIN.tsv", "FordA_TRAIN.tsv")
    
    if not os.path.exists("FordA_TEST.tsv"):
        logger.info("Downloading FordA_TEST.tsv...")
        urllib.request.urlretrieve(root_url + "_TEST.tsv", "FordA_TEST.tsv")

    x_train, y_train = read_ucr("FordA_TRAIN.tsv")
    x_test, y_test = read_ucr("FordA_TEST.tsv")
    
    # Preprocessing
    # 1. Reshape to (N, T, 1) for Conv1D
    x_train = x_train.reshape((x_train.shape[0], x_train.shape[1], 1))
    x_test = x_test.reshape((x_test.shape[0], x_test.shape[1], 1))

    # 2. Fix Labels (FordA has -1 and 1, we map to 0 and 1)
    y_train[y_train == -1] = 0
    y_test[y_test == -1] = 0
    
    # 3. Standardization (Mean=0, Std=1)
    # Important: Fit on Train, Apply to Test
    idx = np.random.permutation(len(x_train))
    x_train = x_train[idx]
    y_train = y_train[idx]
    
    # Standardize
    # Note: For time series, usually standardizing each series individually is good,
    # or standardizing the whole dataset. Here we just return raw (normalized by sensor).
    # The FordA dataset is already z-normalized per sample.

    logger.info(f"Data loaded. Train shape: {x_train.shape}")
    return (x_train, y_train), (x_test, y_test)


if __name__ == "__main__":
    # 1. Load Data
    (x_train, y_train), (x_test, y_test) = load_data()
    
    num_classes = len(np.unique(y_train))
    input_shape = x_train.shape[1:]
    
    # 2. Instantiate Classifier
    classifier = TimeSeriesClassifier(
        input_shape=input_shape,
        num_classes=num_classes,
        batch_size=32,
        epochs=100 # Adjusted for demo
    )
    
    # 3. Build Model
    classifier.build_model()
    
    # 4. Train
    history = classifier.train(x_train, y_train)
    
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