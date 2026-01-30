import os
import logging
import numpy as np
import matplotlib.pyplot as plt
import keras
from keras import layers
from keras import ops
import tensorflow as tf

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# --- Custom Layers ---

class Patches(layers.Layer):
    """
    Extracts patches from the image.
    input shape: (batch, height, width, channels)
    output shape: (batch, num_patches, patch_area * channels)
    """
    def __init__(self, patch_size, **kwargs):
        super().__init__(**kwargs)
        self.patch_size = patch_size

    def call(self, images):
        input_shape = ops.shape(images)
        batch_size = input_shape[0]
        height = input_shape[1]
        width = input_shape[2]
        channels = input_shape[3]
        num_patches_h = height // self.patch_size
        num_patches_w = width // self.patch_size
        patches = keras.ops.image.extract_patches(images, size=self.patch_size)
        patches = ops.reshape(
            patches,
            (
                batch_size,
                num_patches_h * num_patches_w,
                self.patch_size * self.patch_size * channels,
            ),
        )
        return patches

    def get_config(self):
        config = super().get_config()
        config.update({"patch_size": self.patch_size})
        return config


class PatchEncoder(layers.Layer):
    """
    Project patches to embedding dim and adds position embedding.
    """
    def __init__(self, num_patches, projection_dim, **kwargs):
        super().__init__(**kwargs)
        self.num_patches = num_patches
        self.projection = layers.Dense(units=projection_dim)
        self.position_embedding = layers.Embedding(
            input_dim=num_patches, output_dim=projection_dim
        )

    def call(self, patch):
        positions = ops.expand_dims(
            ops.arange(start=0, stop=self.num_patches, step=1), axis=0
        )
        projected_patches = self.projection(patch)
        encoded = projected_patches + self.position_embedding(positions)
        return encoded

    def get_config(self):
        config = super().get_config()
        config.update({"num_patches": self.num_patches})
        return config

# --- Main Classifier Class ---

class ViTClassifier:
    def __init__(
        self,
        input_shape,
        num_classes,
        image_size=72,
        patch_size=6,
        projection_dim=64,
        num_heads=4,
        transformer_layers=8,
        transformer_units=[128, 64],
        mlp_head_units=[2048, 1024],
        batch_size=256,
        learning_rate=0.001,
        weight_decay=0.0001
    ):
        """
        Initializes the Vision Transformer configuration.
        """
        self.input_shape = input_shape
        self.num_classes = num_classes
        self.image_size = image_size
        self.patch_size = patch_size
        self.projection_dim = projection_dim
        self.num_heads = num_heads
        self.transformer_layers = transformer_layers
        self.transformer_units = transformer_units
        self.mlp_head_units = mlp_head_units
        self.batch_size = batch_size
        self.learning_rate = learning_rate
        self.weight_decay = weight_decay

        # Derived parameters
        self.num_patches = (image_size // patch_size) ** 2
        self.model = None
        self.train_ds = None
        self.val_ds = None
        
        # Default Data Augmentation
        self.data_augmentation = keras.Sequential(
            [
                layers.Normalization(),
                layers.Resizing(image_size, image_size),
                layers.RandomFlip("horizontal"),
                layers.RandomRotation(factor=0.02),
                layers.RandomZoom(height_factor=0.2, width_factor=0.2),
            ],
            name="data_augmentation",
        )
        
        logger.info(f"Initialized ViT with {self.num_patches} patches.")

    def _mlp(self, x, hidden_units, dropout_rate):
        """Helper for Multilayer Perceptron blocks."""
        for units in hidden_units:
            x = layers.Dense(units, activation=keras.activations.gelu)(x)
            x = layers.Dropout(dropout_rate)(x)
        return x

    def prepare_data(self, x_train, y_train, x_test, y_test):
        """
        Prepares data: Normalization adaptation and Dataset creation.
        """
        logger.info("Adapting normalization layer to training data...")
        self.data_augmentation.layers[0].adapt(x_train)
        
        logger.info("Creating data pipelines...")
        self.x_train = x_train
        self.y_train = y_train
        self.x_test = x_test
        self.y_test = y_test
        
        logger.info(f"Data ready. Train samples: {len(x_train)}, Test samples: {len(x_test)}")

    def build_model(self):
        """
        Constructs the Vision Transformer architecture.
        """
        logger.info("Building ViT model...")
        
        inputs = keras.Input(shape=self.input_shape)
        
        # 1. Augment
        augmented = self.data_augmentation(inputs)
        
        # 2. Patchify
        patches = Patches(self.patch_size)(augmented)
        
        # 3. Encode
        encoded_patches = PatchEncoder(self.num_patches, self.projection_dim)(patches)

        # 4. Transformer Blocks
        for i in range(self.transformer_layers):
            # Norm 1
            x1 = layers.LayerNormalization(epsilon=1e-6)(encoded_patches)
            
            # Attention
            attention_output = layers.MultiHeadAttention(
                num_heads=self.num_heads, key_dim=self.projection_dim, dropout=0.1
            )(x1, x1)
            
            # Skip 1
            x2 = layers.Add()([attention_output, encoded_patches])
            
            # Norm 2
            x3 = layers.LayerNormalization(epsilon=1e-6)(x2)
            
            # MLP
            x3 = self._mlp(x3, hidden_units=self.transformer_units, dropout_rate=0.1)
            
            # Skip 2
            encoded_patches = layers.Add()([x3, x2])

        # 5. Output Head
        representation = layers.LayerNormalization(epsilon=1e-6)(encoded_patches)
        representation = layers.Flatten()(representation)
        representation = layers.Dropout(0.5)(representation)
        
        features = self._mlp(representation, hidden_units=self.mlp_head_units, dropout_rate=0.5)
        logits = layers.Dense(self.num_classes)(features)
        
        self.model = keras.Model(inputs=inputs, outputs=logits, name="ViT")
        logger.info("Model built successfully.")

    def train(self, epochs=10):
        """
        Compiles and trains the model.
        """
        if self.model is None:
            raise ValueError("Model not built. Call build_model() first.")
            
        logger.info("Compiling model...")
        optimizer = keras.optimizers.AdamW(
            learning_rate=self.learning_rate, weight_decay=self.weight_decay
        )

        self.model.compile(
            optimizer=optimizer,
            loss=keras.losses.SparseCategoricalCrossentropy(from_logits=True),
            metrics=[
                keras.metrics.SparseCategoricalAccuracy(name="accuracy"),
                keras.metrics.SparseTopKCategoricalAccuracy(5, name="top-5-accuracy"),
            ],
        )

        checkpoint_filepath = "/tmp/checkpoint.weights.h5"
        checkpoint_callback = keras.callbacks.ModelCheckpoint(
            checkpoint_filepath,
            monitor="val_accuracy",
            save_best_only=True,
            save_weights_only=True,
        )

        logger.info(f"Starting training for {epochs} epochs...")
        history = self.model.fit(
            x=self.x_train,
            y=self.y_train,
            batch_size=self.batch_size,
            epochs=epochs,
            validation_split=0.1,
            callbacks=[checkpoint_callback],
        )
        
        # Load best weights
        self.model.load_weights(checkpoint_filepath)
        logger.info("Training finished. Best weights loaded.")
        return history

    def evaluate(self):
        """
        Evaluates model on test data.
        """
        if self.model is None:
            raise ValueError("Model not trained.")
            
        logger.info("Evaluating on test set...")
        _, accuracy, top_5_accuracy = self.model.evaluate(self.x_test, self.y_test)
        
        logger.info(f"Test Accuracy: {accuracy * 100:.2f}%")
        logger.info(f"Top-5 Accuracy: {top_5_accuracy * 100:.2f}%")
        return accuracy

    def visualize_patches(self):
        """
        Helper to visualize what the patches look like.
        """
        logger.info("Visualizing sample patches...")
        image = self.x_train[np.random.choice(len(self.x_train))]
        
        # Resize image to model's image_size
        resized_image = ops.image.resize(
            ops.convert_to_tensor([image]), size=(self.image_size, self.image_size)
        )
        
        # Create patches
        patches_layer = Patches(self.patch_size)
        patches = patches_layer(resized_image)
        
        n = int(np.sqrt(patches.shape[1]))
        plt.figure(figsize=(4, 4))
        for i, patch in enumerate(patches[0]):
            ax = plt.subplot(n, n, i + 1)
            patch_img = ops.reshape(patch, (self.patch_size, self.patch_size, 3))
            plt.imshow(ops.convert_to_numpy(patch_img).astype("uint8"))
            plt.axis("off")
        plt.show()


if __name__ == "__main__":
    # 1. Load Data
    logger.info("Loading CIFAR-100 dataset...")
    (x_train, y_train), (x_test, y_test) = keras.datasets.cifar100.load_data()
    
    # 2. Instantiate Classifier with Custom Config
    vit = ViTClassifier(
        input_shape=(32, 32, 3),
        num_classes=100,
        image_size=72,
        patch_size=6,
        projection_dim=64,
        num_heads=4,
        transformer_layers=8,
        batch_size=256
    )

    # 3. Inject Data
    vit.prepare_data(x_train, y_train, x_test, y_test)

    # 4. Visualize (Optional)
    vit.visualize_patches()

    # 5. Build Model
    vit.build_model()

    # 6. Train
    # Set epochs=100 for real results, 5 for quick test
    history = vit.train(epochs=5)

    # 7. Evaluate
    vit.evaluate()