import numpy as np
import matplotlib.pyplot as plt
import keras
from keras import layers
from keras import ops
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

class DenoisingAutoencoder:
    """
    A Convolutional Autoencoder designed to remove noise from images.
    """
    def __init__(self, input_shape):
        """
        Initialize the model configuration.
        :param input_shape: Tuple, e.g., (28, 28, 1) for grayscale or (32, 32, 3) for RGB.
        """
        self.input_shape = input_shape
        self.model = None
        logger.info(f"Initialized Autoencoder with input shape: {self.input_shape}")

    def add_noise(self, data, noise_factor=0.5):
        """
        Applies Gaussian noise to the dataset.
        """
        logger.info(f"Adding noise to data (factor={noise_factor})...")
        noisy_data = data + noise_factor * np.random.normal(loc=0.0, scale=1.0, size=data.shape)
        # Clip values to ensure they stay within [0, 1] range
        return np.clip(noisy_data, 0.0, 1.0)

    def preprocess_data(self, data):
        """
        Normalizes and reshapes raw data to fit the model.
        Assumes input is a numpy array of integers [0, 255].
        """
        logger.info("Preprocessing data (Normalizing and Reshaping)...")
        data = data.astype("float32") / 255.0
        
        # Ensure data has channel dimension (e.g., 28, 28) -> (28, 28, 1)
        if len(data.shape) == 3 and self.input_shape[-1] == 1:
            data = np.reshape(data, (len(data),) + self.input_shape)
        return data

    def build_model(self):
        """
        Constructs the Encoder-Decoder architecture.
        """
        logger.info("Building model architecture...")
        input_img = layers.Input(shape=self.input_shape)

        # --- ENCODER ---
        # Compresses the input. 
        # 'same' padding ensures dimensions don't shrink unexpectedly during convolution.
        x = layers.Conv2D(32, (3, 3), activation="relu", padding="same")(input_img)
        x = layers.MaxPooling2D((2, 2), padding="same")(x)
        x = layers.Conv2D(32, (3, 3), activation="relu", padding="same")(x)
        encoded = layers.MaxPooling2D((2, 2), padding="same")(x)

        # --- DECODER ---
        # Reconstructs the input.
        x = layers.Conv2D(32, (3, 3), activation="relu", padding="same")(encoded)
        x = layers.UpSampling2D((2, 2))(x)
        x = layers.Conv2D(32, (3, 3), activation="relu", padding="same")(x)
        x = layers.UpSampling2D((2, 2))(x)
        
        # Final layer reconstructs original channels (1 for grayscale, 3 for RGB)
        # Sigmoid activation maps outputs to [0, 1]
        decoded = layers.Conv2D(self.input_shape[-1], (3, 3), activation="sigmoid", padding="same")(x)

        self.model = keras.Model(input_img, decoded)
        self.model.compile(optimizer="adam", loss="binary_crossentropy")
        logger.info("Model compiled successfully.")
        self.model.summary(print_fn=logger.info)

    def train(self, x_input, x_target, epochs=50, batch_size=128, validation_split=0.1):
        """
        Trains the autoencoder.
        To train for Denoising: x_input = noisy_data, x_target = clean_data
        To train for Reconstruction: x_input = clean_data, x_target = clean_data
        """
        if self.model is None:
            raise ValueError("Model not built. Call build_model() first.")

        logger.info(f"Starting training for {epochs} epochs...")
        history = self.model.fit(
            x=x_input,
            y=x_target,
            epochs=epochs,
            batch_size=batch_size,
            shuffle=True,
            validation_split=validation_split,
        )
        logger.info("Training finished.")
        return history

    def predict(self, data):
        """Runs inference on new data."""
        logger.info("Generating predictions...")
        return self.model.predict(data)

    def visualize_results(self, original, result, num_images=10):
        """
        Displays original vs reconstructed/denoised images.
        """
        logger.info("Visualizing results...")
        plt.figure(figsize=(20, 4))
        for i in range(num_images):
            # Display Original/Noisy
            ax = plt.subplot(2, num_images, i + 1)
            # Handle grayscale vs RGB for plotting
            if original.shape[-1] == 1:
                plt.imshow(original[i].reshape(self.input_shape[0], self.input_shape[1]))
                plt.gray()
            else:
                plt.imshow(original[i])
            ax.get_xaxis().set_visible(False)
            ax.get_yaxis().set_visible(False)

            # Display Reconstruction
            ax = plt.subplot(2, num_images, i + 1 + num_images)
            if result.shape[-1] == 1:
                plt.imshow(result[i].reshape(self.input_shape[0], self.input_shape[1]))
                plt.gray()
            else:
                plt.imshow(result[i])
            ax.get_xaxis().set_visible(False)
            ax.get_yaxis().set_visible(False)
        plt.show()


if __name__ == "__main__":
    # 1. Configuration
    # It can be changed to (32, 32, 3) for CIFAR-10, etc.
    INPUT_SHAPE = (28, 28, 1) 
    
    # 2. Instantiate Class
    autoencoder = DenoisingAutoencoder(input_shape=INPUT_SHAPE)

    # 3. Load Data (Using MNIST as example, but you can plug in any array)
    logger.info("Loading MNIST dataset...")
    (x_train, _), (x_test, _) = keras.datasets.mnist.load_data()

    # 4. Preprocess Data
    # The class handles normalization and reshaping
    clean_train = autoencoder.preprocess_data(x_train)
    clean_test = autoencoder.preprocess_data(x_test)

    # 5. Create Noisy Versions
    noisy_train = autoencoder.add_noise(clean_train, noise_factor=0.5)
    noisy_test = autoencoder.add_noise(clean_test, noise_factor=0.5)

    # 6. Build Model
    autoencoder.build_model()

    # 7. Train (Denoising Mode)
    # Input is Noisy, Target is Clean
    autoencoder.train(
        x_input=noisy_train, 
        x_target=clean_train, 
        epochs=10, # Reduced for demo speed
        batch_size=128
    )

    # 8. Predict & Visualize
    denoised_images = autoencoder.predict(noisy_test)
    
    # Show Noisy Input vs Denoised Output
    autoencoder.visualize_results(original=noisy_test, result=denoised_images)