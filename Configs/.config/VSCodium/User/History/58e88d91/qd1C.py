import numpy as np
import keras
from keras import layers
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

class SimpleImageClassifier:
    """
    A wrapper class for a simple CNN image classifier.
    Designed to be reusable for different datasets with similar characteristics.
    """

    def __init__(self, input_shape=(28, 28, 1), num_classes=10):
        """
        Initialize the classifier configuration.
        """
        self.input_shape = input_shape
        self.num_classes = num_classes
        self.model = None
        self.x_train = None
        self.y_train = None
        self.x_test = None
        self.y_test = None
        logger.info(f"Initialized Classifier: Input={input_shape}, Classes={num_classes}")

    def prepare_data(self, x_train, y_train, x_test, y_test):
        """
        Preprocesses raw data: scales pixels, reshapes for channels, and one-hot encodes labels.
        Allows you to pass distinct datasets (e.g., MNIST, Fashion MNIST).
        """
        logger.info("Preprocessing data...")

        # Scale images to the [0, 1] range
        self.x_train = x_train.astype("float32") / 255
        self.x_test = x_test.astype("float32") / 255

        # Ensure images have shape (height, width, 1) if grayscale
        # Keras Conv2D expects a 4D tensor: (batch, height, width, channels)
        if len(self.x_train.shape) == 3:
            self.x_train = np.expand_dims(self.x_train, -1)
            self.x_test = np.expand_dims(self.x_test, -1)

        logger.info(f"x_train shape: {self.x_train.shape} - {self.x_train.shape[0]} samples")
        logger.info(f"x_test shape: {self.x_test.shape} - {self.x_test.shape[0]} samples")

        # Convert class vectors to binary class matrices (One-hot encoding)
        self.y_train = keras.utils.to_categorical(y_train, self.num_classes)
        self.y_test = keras.utils.to_categorical(y_test, self.num_classes)
        
        logger.info("Data preparation complete.")

    def build_model(self):
        """
        Constructs the Convolutional Neural Network architecture.
        Structure: Conv2D -> MaxPool -> Conv2D -> MaxPool -> Flatten -> Dropout -> Dense
        """
        logger.info("Building model architecture...")
        
        self.model = keras.Sequential(
            [
                keras.Input(shape=self.input_shape),
                layers.Conv2D(32, kernel_size=(3, 3), activation="relu"),
                layers.MaxPooling2D(pool_size=(2, 2)),
                layers.Conv2D(64, kernel_size=(3, 3), activation="relu"),
                layers.MaxPooling2D(pool_size=(2, 2)),
                layers.Flatten(),
                layers.Dropout(0.5),
                layers.Dense(self.num_classes, activation="softmax"),
            ]
        )
        # Log the model summary string for debugging
        self.model.summary(print_fn=logger.info)

    def train(self, batch_size=128, epochs=15, validation_split=0.1):
        """
        Compiles and fits the model to the training data.
        """
        if self.model is None:
            raise ValueError("Model not built. Call build_model() first.")
        
        logger.info(f"Starting training for {epochs} epochs with batch size {batch_size}...")

        self.model.compile(
            loss="categorical_crossentropy", 
            optimizer="adam", 
            metrics=["accuracy"]
        )

        history = self.model.fit(
            self.x_train, 
            self.y_train, 
            batch_size=batch_size, 
            epochs=epochs, 
            validation_split=validation_split
        )
        logger.info("Training complete.")
        return history

    def evaluate(self):
        """
        Evaluates the model on the held-out test set.
        """
        if self.model is None:
            raise ValueError("Model not built or trained.")
            
        logger.info("Evaluating on test set...")
        score = self.model.evaluate(self.x_test, self.y_test, verbose=0)
        
        logger.info(f"Test loss: {score[0]:.4f}")
        logger.info(f"Test accuracy: {score[1]:.4f}")
        return score

# --- Usage Example ---

if __name__ == "__main__":
    # 1. Instantiate the class
    classifier = SimpleImageClassifier(input_shape=(28, 28, 1), num_classes=10)

    # 2. Load Data (Here we use MNIST, but you could load Fashion MNIST or custom data)
    # (x_train, y_train), (x_test, y_test) = keras.datasets.fashion_mnist.load_data()
    logger.info("Loading MNIST dataset...")
    (raw_x_train, raw_y_train), (raw_x_test, raw_y_test) = keras.datasets.mnist.load_data()

    # 3. Inject Data
    classifier.prepare_data(raw_x_train, raw_y_train, raw_x_test, raw_y_test)

    # 4. Build
    classifier.build_model()

    # 5. Train
    classifier.train(batch_size=128, epochs=5) # Reduced epochs for demonstration speed

    # 6. Evaluate
    classifier.evaluate()