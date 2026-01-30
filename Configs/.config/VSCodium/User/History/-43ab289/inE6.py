import os
import logging
import numpy as np
import matplotlib.pyplot as plt
import keras
from keras import ops
import tensorflow as tf
import tensorflow_hub as hub
import tensorflow_datasets as tfds

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

os.environ["KERAS_BACKEND"] = "tensorflow"

class BiTClassifier:
    """
    A wrapper for the BigTransfer (BiT) model for image classification.
    """
    def __init__(self, num_classes, image_size=384, crop_size=224, batch_size=64):
        """
        Initialize the classifier configuration.
        """
        self.num_classes = num_classes
        self.resize_to = image_size
        self.crop_to = crop_size
        self.batch_size = batch_size
        
        self.model = None
        self.train_ds = None
        self.val_ds = None
        self.steps_per_epoch = 10
        self.schedule_length = 500
        
        # Load the BiT model URL (using the R50x1 variant)
        self.bit_model_url = "https://tfhub.dev/google/bit/m-r50x1/1"
        self.bit_module = None
        
        logger.info(f"Initialized BiT Classifier for {num_classes} classes.")

    def _preprocess_train(self, image, label):
        """Internal helper: Augmentation pipeline for training."""
        # Random flip and crop are standard BiT augmentations
        image = tf.image.random_flip_left_right(image)
        image = tf.image.resize(image, [self.resize_to, self.resize_to])
        image = tf.image.random_crop(image, [self.crop_to, self.crop_to, 3])
        image = image / 255.0
        return image, label

    def _preprocess_test(self, image, label):
        """Internal helper: Preprocessing for validation/test (no augmentation)."""
        image = tf.image.resize(image, [self.resize_to, self.resize_to])
        image = tf.cast(image, dtype=tf.float32)
        image = image / 255.0
        return image, label

    def prepare_data(self, train_ds, val_ds, steps_per_epoch=10, schedule_length=500):
        """
        Prepares the data pipelines.
        Accepts tf.data.Dataset objects.
        """
        logger.info("Setting up data pipelines...")
        self.steps_per_epoch = steps_per_epoch
        self.schedule_length = schedule_length
        
        # Optimize pipeline performance
        auto = tf.data.AUTOTUNE
        
        # Determine repeat count based on schedule length logic from BiT paper
        # Repeat the dataset to match the training schedule
        dataset_cardinality = train_ds.cardinality().numpy()
        if dataset_cardinality < 0:
             # Handle infinite datasets if necessary, or default to estimation
             dataset_cardinality = 1000 
             
        repeat_count = int(schedule_length * self.batch_size / dataset_cardinality * steps_per_epoch)
        repeat_count += 50 + 1 # Safety buffer
        
        self.train_ds = (
            train_ds.shuffle(10000)
            .repeat(repeat_count)
            .map(self._preprocess_train, num_parallel_calls=auto)
            .batch(self.batch_size)
            .prefetch(auto)
        )

        self.val_ds = (
            val_ds.map(self._preprocess_test, num_parallel_calls=auto)
            .batch(self.batch_size)
            .prefetch(auto)
        )
        logger.info("Data pipelines ready.")

    def build_model(self):
        """
        Loads the BiT backbone and adds a zero-initialized head.
        """
        logger.info(f"Loading BiT model from {self.bit_model_url}...")
        self.bit_module = hub.load(self.bit_model_url)
        
        class BiTModelWrapper(keras.Model):
            def __init__(self, num_classes, module, **kwargs):
                super().__init__(**kwargs)
                self.num_classes = num_classes
                # Zero initialization is crucial for BiT fine-tuning stability
                self.head = keras.layers.Dense(num_classes, kernel_initializer="zeros")
                self.bit_model = module

            def call(self, images):
                bit_embedding = self.bit_model(images)
                return self.head(bit_embedding)

        self.model = BiTModelWrapper(num_classes=self.num_classes, module=self.bit_module)
        logger.info("Model built successfully.")

    def train(self):
        """
        Compiles and trains the model using BiT-specific optimizer settings.
        """
        if self.model is None:
            raise ValueError("Model not built. Call build_model() first.")
            
        logger.info("Configuring optimizer and schedule...")
        
        # BiT Hyperparameters
        lr_base = 0.003 * self.batch_size / 512
        schedule_boundaries = [200, 300, 400] # Epochs to decay LR
        
        lr_schedule = keras.optimizers.schedules.PiecewiseConstantDecay(
            boundaries=schedule_boundaries,
            values=[
                lr_base,
                lr_base * 0.1,
                lr_base * 0.01,
                lr_base * 0.001,
            ],
        )
        
        optimizer = keras.optimizers.SGD(learning_rate=lr_schedule, momentum=0.9)
        loss_fn = keras.losses.SparseCategoricalCrossentropy(from_logits=True)
        
        self.model.compile(optimizer=optimizer, loss=loss_fn, metrics=["accuracy"])
        
        callbacks = [
            keras.callbacks.EarlyStopping(
                monitor="val_accuracy", patience=2, restore_best_weights=True
            )
        ]
        
        logger.info("Starting training...")
        history = self.model.fit(
            self.train_ds,
            batch_size=self.batch_size,
            epochs=int(self.schedule_length / self.steps_per_epoch),
            steps_per_epoch=self.steps_per_epoch,
            validation_data=self.val_ds,
            callbacks=callbacks,
        )
        logger.info("Training finished.")
        return history

    def evaluate(self):
        """Evaluates on validation set."""
        if self.model is None:
             raise ValueError("Model not trained.")
        
        logger.info("Evaluating model...")
        accuracy = self.model.evaluate(self.val_ds)[1] * 100
        logger.info(f"Validation Accuracy: {accuracy:.2f}%")
        return accuracy

    def plot_history(self, history):
        """Helper to plot training curves."""
        plt.figure(figsize=(12, 4))
        
        plt.subplot(1, 2, 1)
        plt.plot(history.history["accuracy"], label="train_acc")
        plt.plot(history.history["val_accuracy"], label="val_acc")
        plt.title("Accuracy")
        plt.legend()
        
        plt.subplot(1, 2, 2)
        plt.plot(history.history["loss"], label="train_loss")
        plt.plot(history.history["val_loss"], label="val_loss")
        plt.title("Loss")
        plt.legend()
        
        plt.show()


if __name__ == "__main__":
    # 1. Load Data (Here we use Flowers, but you can swap this!)
    logger.info("Loading generic dataset (Flowers)...")
    (train_ds, val_ds), dataset_info = tfds.load(
        "tf_flowers",
        split=["train[:85%]", "train[85%:]"],
        as_supervised=True,
        with_info=True
    )
    
    num_classes = dataset_info.features['label'].num_classes
    
    # 2. Instantiate Classifier
    classifier = BiTClassifier(num_classes=num_classes, batch_size=64)
    
    # 3. Inject Data
    classifier.prepare_data(train_ds, val_ds)
    
    # 4. Build Model
    classifier.build_model()
    
    # 5. Train
    history = classifier.train()
    
    # 6. Evaluate & Plot
    classifier.evaluate()
    classifier.plot_history(history)