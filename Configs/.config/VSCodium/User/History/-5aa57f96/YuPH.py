import os
import logging
import numpy as np
import keras
from keras import layers
from tensorflow import data as tf_data
import matplotlib.pyplot as plt

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


class CustomImageClassifier:
    def __init__(self, image_size=(180, 180), batch_size=128, seed=1337):
        """
        Initialize the classifier configuration.
        """
        self.image_size = image_size
        self.batch_size = batch_size
        self.seed = seed
        self.model = None
        self.num_classes = None

        # Define augmentation layers
        # These are defined once here to be reused in the pipeline
        self.data_augmentation = keras.Sequential(
            [
                layers.RandomFlip("horizontal"),
                layers.RandomRotation(0.1),
            ]
        )

    def clean_corrupted_images(self, directory):
        """
        Scans the directory and removes images without a valid 'JFIF' header.
        This prevents the training loop from crashing on bad files.
        """
        logger.info(f"Scanning {directory} for corrupted images...")
        num_skipped = 0

        # Walk through all subdirectories (e.g., Class A, Class B)
        for root, dirs, files in os.walk(directory):
            for fname in files:
                fpath = os.path.join(root, fname)
                try:
                    fobj = open(fpath, "rb")
                    is_jfif = b"JFIF" in fobj.peek(10)
                except Exception as e:
                    logger.warning(f"Could not read {fpath}: {e}")
                    is_jfif = False
                finally:
                    fobj.close()

                if not is_jfif:
                    num_skipped += 1
                    # Delete corrupted image
                    os.remove(fpath)

        logger.info(f"Cleanup complete. Deleted {num_skipped} corrupted images.")

    def load_and_augment_data(self, directory, validation_split=0.2):
        """
        Generates training and validation datasets from a directory.
        Applies data augmentation to the training set asynchronously.
        """
        logger.info(f"Loading data from {directory}...")

        # Create base datasets
        train_ds, val_ds = keras.utils.image_dataset_from_directory(
            directory,
            validation_split=validation_split,
            subset="both",
            seed=self.seed,
            image_size=self.image_size,
            batch_size=self.batch_size,
        )

        # Infer number of classes dynamically from the folder structure
        self.num_classes = len(train_ds.class_names)
        logger.info(f"Detected {self.num_classes} classes: {train_ds.class_names}")

        # Optimize dataset performance (prefetching & augmentation)
        # Note: Augmentation is mapped only to training data
        train_ds = train_ds.map(
            lambda x, y: (self.data_augmentation(x, training=True), y),
            num_parallel_calls=tf_data.AUTOTUNE,
        )

        # Buffer the data to ensure the GPU never waits for the CPU
        train_ds = train_ds.prefetch(tf_data.AUTOTUNE)
        val_ds = val_ds.prefetch(tf_data.AUTOTUNE)

        return train_ds, val_ds

    def build_model(self):
        """
        Builds the Xception-style model architecture.
        Adjusts the output layer based on the number of classes detected.
        """
        if self.num_classes is None:
            raise ValueError(
                "Data must be loaded before building the model to determine output units."
            )

        logger.info("Building model architecture...")

        input_shape = self.image_size + (3,)
        inputs = keras.Input(shape=input_shape)

        # Entry block: Normalize [0,255] -> [0,1]
        x = layers.Rescaling(1.0 / 255)(inputs)
        x = layers.Conv2D(128, 3, strides=2, padding="same")(x)
        x = layers.BatchNormalization()(x)
        x = layers.Activation("relu")(x)

        previous_block_activation = x

        # Residual blocks
        for size in [256, 512, 728]:
            x = layers.Activation("relu")(x)
            x = layers.SeparableConv2D(size, 3, padding="same")(x)
            x = layers.BatchNormalization()(x)

            x = layers.Activation("relu")(x)
            x = layers.SeparableConv2D(size, 3, padding="same")(x)
            x = layers.BatchNormalization()(x)

            x = layers.MaxPooling2D(3, strides=2, padding="same")(x)

            # Project residual
            residual = layers.Conv2D(size, 1, strides=2, padding="same")(
                previous_block_activation
            )
            x = layers.add([x, residual])
            previous_block_activation = x

        # Exit block
        x = layers.SeparableConv2D(1024, 3, padding="same")(x)
        x = layers.BatchNormalization()(x)
        x = layers.Activation("relu")(x)

        x = layers.GlobalAveragePooling2D()(x)

        # Logic to handle Binary vs Multi-class
        if self.num_classes == 2:
            logger.info("Binary classification detected. Using 1 output unit.")
            units = 1
            activation = None  # Returns logits
        else:
            logger.info(
                f"Multi-class classification detected. Using {self.num_classes} output units."
            )
            units = self.num_classes
            activation = "softmax"

        x = layers.Dropout(0.25)(x)
        outputs = layers.Dense(units, activation=activation)(x)

        self.model = keras.Model(inputs, outputs)
        logger.info("Model built successfully.")

        return self.model

    def train(self, train_ds, val_ds, epochs=25, learning_rate=3e-4):
        """
        Compiles and trains the model.
        """
        logger.info(f"Starting training for {epochs} epochs...")

        # Determine loss function based on problem type
        if self.num_classes == 2:
            loss = keras.losses.BinaryCrossentropy(from_logits=True)
            metrics = [keras.metrics.BinaryAccuracy(name="acc")]
        else:
            # For multi-class (e.g., 0, 1, 2)
            loss = keras.losses.SparseCategoricalCrossentropy(from_logits=False)
            metrics = ["accuracy"]

        self.model.compile(
            optimizer=keras.optimizers.Adam(learning_rate),
            loss=loss,
            metrics=metrics,
        )

        callbacks = [
            keras.callbacks.ModelCheckpoint("save_at_{epoch}.keras"),
        ]

        history = self.model.fit(
            train_ds,
            epochs=epochs,
            callbacks=callbacks,
            validation_data=val_ds,
        )
        logger.info("Training finished.")
        return history

    def predict_single_image(self, image_path):
        """
        Loads a single image and runs inference.
        """
        if not self.model:
            raise ValueError("Model has not been built or trained yet.")

        logger.info(f"Running inference on: {image_path}")

        img = keras.utils.load_img(image_path, target_size=self.image_size)
        img_array = keras.utils.img_to_array(img)
        img_array = keras.ops.expand_dims(img_array, 0)  # Create batch axis

        predictions = self.model.predict(img_array)

        if self.num_classes == 2:
            score = float(keras.ops.sigmoid(predictions[0][0]))
            return {
                "score": score,
                "class_1_confidence": score,
                "class_0_confidence": 1 - score,
            }
        else:
            # Return raw probabilities for multi-class
            return predictions[0]


if __name__ == "__main__":
    # 1. Setup helper to download data (Same as original script)
    # Only needed if you don't have the data yet
    import shutil

    if not os.path.exists("PetImages"):
        logger.info("Downloading dataset...")
        os.system(
            "curl -O https://download.microsoft.com/download/3/E/1/3E1C3F21-ECDB-4869-8368-6DEBA77B919F/kagglecatsanddogs_5340.zip"
        )
        os.system("unzip -q kagglecatsanddogs_5340.zip")

    # 2. Instantiate the Classifier
    classifier = CustomImageClassifier(image_size=(180, 180), batch_size=128)

    # 3. Clean Data
    data_dir = "PetImages"
    classifier.clean_corrupted_images(data_dir)

    # 4. Load & Augment
    train_ds, val_ds = classifier.load_and_augment_data(data_dir)

    # 5. Build & Train
    classifier.build_model()
    classifier.train(train_ds, val_ds, epochs=25)

    # 6. Predict
    test_image = "PetImages/Cat/6779.jpg"
    if os.path.exists(test_image):
        result = classifier.predict_single_image(test_image)
        if classifier.num_classes == 2:
            print(
                f"Prediction: {100 * result['class_0_confidence']:.2f}% Class 0, {100 * result['class_1_confidence']:.2f}% Class 1"
            )
        else:
            print(f"Prediction Probabilities: {result}")
