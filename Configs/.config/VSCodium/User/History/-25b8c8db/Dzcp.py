import math
import logging
import numpy as np
import tensorflow as tf
import keras
from keras import ops
from keras import layers
import matplotlib.pyplot as plt

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# Set seed for reproducibility
SEED = 42
keras.utils.set_random_seed(SEED)

# --- Custom Layers ---

class ShiftedPatchTokenization(layers.Layer):
    """
    preprocessing layer that shifts images diagonally before patching.
    This helps the ViT capture more local spatial information (inductive bias).
    """
    def __init__(
        self,
        image_size,
        patch_size,
        num_patches,
        projection_dim,
        vanilla=False,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.vanilla = vanilla
        self.image_size = image_size
        self.patch_size = patch_size
        self.half_patch = patch_size // 2
        self.flatten_patches = layers.Reshape((num_patches, -1))
        self.projection = layers.Dense(units=projection_dim)
        self.layer_norm = layers.LayerNormalization(epsilon=1e-6)

    def crop_shift_pad(self, images, mode):
        # Build diagonally shifted images
        if mode == "left-up":
            crop_height, crop_width = self.half_patch, self.half_patch
            shift_height, shift_width = 0, 0
        elif mode == "left-down":
            crop_height, crop_width = 0, self.half_patch
            shift_height, shift_width = self.half_patch, 0
        elif mode == "right-up":
            crop_height, crop_width = self.half_patch, 0
            shift_height, shift_width = 0, self.half_patch
        else: # right-down
            crop_height, crop_width = 0, 0
            shift_height, shift_width = self.half_patch, self.half_patch

        # Crop and Pad
        crop = ops.image.crop_images(
            images,
            top_cropping=crop_height,
            left_cropping=crop_width,
            target_height=self.image_size - self.half_patch,
            target_width=self.image_size - self.half_patch,
        )
        return ops.image.pad_images(
            crop,
            top_padding=shift_height,
            left_padding=shift_width,
            target_height=self.image_size,
            target_width=self.image_size,
        )

    def call(self, images):
        if not self.vanilla:
            # Concatenate original + 4 shifted versions
            images = ops.concatenate(
                [
                    images,
                    self.crop_shift_pad(images, mode="left-up"),
                    self.crop_shift_pad(images, mode="left-down"),
                    self.crop_shift_pad(images, mode="right-up"),
                    self.crop_shift_pad(images, mode="right-down"),
                ],
                axis=-1,
            )
        
        # Patchify
        patches = ops.image.extract_patches(
            images=images,
            size=(self.patch_size, self.patch_size),
            strides=[1, self.patch_size, self.patch_size, 1],
            dilation_rate=1,
            padding="VALID",
        )
        flat_patches = self.flatten_patches(patches)
        
        if not self.vanilla:
            tokens = self.layer_norm(flat_patches)
            tokens = self.projection(tokens)
        else:
            tokens = self.projection(flat_patches)
        return tokens

class PatchEncoder(layers.Layer):
    """Adds learnable positional embeddings to the tokens."""
    def __init__(self, num_patches, projection_dim, **kwargs):
        super().__init__(**kwargs)
        self.num_patches = num_patches
        self.position_embedding = layers.Embedding(
            input_dim=num_patches, output_dim=projection_dim
        )
        self.positions = ops.arange(start=0, stop=self.num_patches, step=1)

    def call(self, encoded_patches):
        encoded_positions = self.position_embedding(self.positions)
        return encoded_patches + encoded_positions

class MultiHeadAttentionLSA(layers.MultiHeadAttention):
    """
    Locality Self Attention (LSA).
    Adds a learnable temperature scaling and diagonal masking to standard attention.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tau = keras.Variable(math.sqrt(float(self._key_dim)), trainable=True)

    def _compute_attention(self, query, key, value, attention_mask=None, training=None):
        query = ops.multiply(query, 1.0 / self.tau)
        attention_scores = ops.einsum(self._dot_product_equation, key, query)
        
        # Apply the diagonal mask (passed in via call)
        attention_scores = self._masked_softmax(attention_scores, attention_mask)
        attention_scores_dropout = self._dropout_layer(
            attention_scores, training=training
        )
        attention_output = ops.einsum(
            self._combine_equation, attention_scores_dropout, value
        )
        return attention_output, attention_scores

# --- Helper: Learning Rate Schedule ---

class WarmUpCosine(keras.optimizers.schedules.LearningRateSchedule):
    def __init__(self, learning_rate_base, total_steps, warmup_learning_rate, warmup_steps):
        super().__init__()
        self.learning_rate_base = learning_rate_base
        self.total_steps = total_steps
        self.warmup_learning_rate = warmup_learning_rate
        self.warmup_steps = warmup_steps
        self.pi = ops.array(np.pi)

    def __call__(self, step):
        if self.total_steps < self.warmup_steps:
            raise ValueError("Total_steps must be larger or equal to warmup_steps.")

        cos_annealed_lr = ops.cos(
            self.pi
            * (ops.cast(step, dtype="float32") - self.warmup_steps)
            / float(self.total_steps - self.warmup_steps)
        )
        learning_rate = 0.5 * self.learning_rate_base * (1 + cos_annealed_lr)

        if self.warmup_steps > 0:
            if self.learning_rate_base < self.warmup_learning_rate:
                raise ValueError("Base LR must be >= Warmup LR")
            slope = (self.learning_rate_base - self.warmup_learning_rate) / self.warmup_steps
            warmup_rate = slope * ops.cast(step, dtype="float32") + self.warmup_learning_rate
            learning_rate = ops.where(step < self.warmup_steps, warmup_rate, learning_rate)
            
        return ops.where(step > self.total_steps, 0.0, learning_rate)

# --- Main Classifier Class ---

class ViTSmallClassifier:
    def __init__(
        self,
        input_shape,
        num_classes,
        image_size=72,
        patch_size=6,
        projection_dim=64,
        num_heads=4,
        transformer_layers=8,
        batch_size=256,
    ):
        """Initialize the ViT configuration."""
        self.input_shape = input_shape
        self.num_classes = num_classes
        self.image_size = image_size
        self.patch_size = patch_size
        self.projection_dim = projection_dim
        self.num_heads = num_heads
        self.transformer_layers = transformer_layers
        self.batch_size = batch_size
        
        # Derived parameters
        self.num_patches = (image_size // patch_size) ** 2
        self.transformer_units = [projection_dim * 2, projection_dim]
        self.mlp_head_units = [2048, 1024]
        
        self.model = None
        
        # Augmentation pipeline
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
        logger.info(f"Initialized ViT with {num_patches} patches of size {patch_size}x{patch_size}")

    def _mlp(self, x, hidden_units, dropout_rate):
        for units in hidden_units:
            x = layers.Dense(units, activation="gelu")(x)
            x = layers.Dropout(dropout_rate)(x)
        return x

    def build_model(self, use_vanilla_vit=False):
        """
        Builds the Keras model.
        :param use_vanilla_vit: If True, uses standard ViT. If False, uses SPT and LSA.
        """
        logger.info(f"Building model (Vanilla={use_vanilla_vit})...")
        
        inputs = layers.Input(shape=self.input_shape)
        augmented = self.data_augmentation(inputs)
        
        

        # Tokenization
        tokens = ShiftedPatchTokenization(
            image_size=self.image_size,
            patch_size=self.patch_size,
            num_patches=self.num_patches,
            projection_dim=self.projection_dim,
            vanilla=use_vanilla_vit
        )(augmented)
        
        encoded_patches = PatchEncoder(self.num_patches, self.projection_dim)(tokens)

        # Create diagonal attention mask for LSA
        diag_attn_mask = 1 - ops.eye(self.num_patches)
        diag_attn_mask = ops.cast([diag_attn_mask], dtype="int8")

        

        # Transformer Blocks
        for _ in range(self.transformer_layers):
            x1 = layers.LayerNormalization(epsilon=1e-6)(encoded_patches)
            
            if not use_vanilla_vit:
                # Use LSA (Custom MultiHeadAttention)
                attention_output, _ = MultiHeadAttentionLSA(
                    num_heads=self.num_heads, key_dim=self.projection_dim, dropout=0.1
                )(x1, x1, attention_mask=diag_attn_mask)
            else:
                # Use Standard Attention
                attention_output = layers.MultiHeadAttention(
                    num_heads=self.num_heads, key_dim=self.projection_dim, dropout=0.1
                )(x1, x1)

            x2 = layers.Add()([attention_output, encoded_patches])
            x3 = layers.LayerNormalization(epsilon=1e-6)(x2)
            x3 = self._mlp(x3, self.transformer_units, dropout_rate=0.1)
            encoded_patches = layers.Add()([x3, x2])

        # Classification Head
        representation = layers.LayerNormalization(epsilon=1e-6)(encoded_patches)
        representation = layers.Flatten()(representation)
        representation = layers.Dropout(0.5)(representation)
        features = self._mlp(representation, self.mlp_head_units, dropout_rate=0.5)
        logits = layers.Dense(self.num_classes)(features)

        self.model = keras.Model(inputs=inputs, outputs=logits)
        logger.info("Model built successfully.")

    def train(self, x_train, y_train, epochs=50, learning_rate=0.001, validation_split=0.1):
        """Compiles and trains the model on the provided data."""
        if self.model is None:
            raise ValueError("Model not built. Call build_model() first.")

        # Adapt normalization layer to data statistics
        logger.info("Adapting augmentation layer to training data...")
        self.data_augmentation.layers[0].adapt(x_train)

        # LR Schedule
        total_steps = int((len(x_train) / self.batch_size) * epochs)
        warmup_steps = int(total_steps * 0.10)
        scheduled_lrs = WarmUpCosine(
            learning_rate_base=learning_rate,
            total_steps=total_steps,
            warmup_learning_rate=0.0,
            warmup_steps=warmup_steps,
        )

        optimizer = keras.optimizers.AdamW(
            learning_rate=scheduled_lrs, weight_decay=0.0001
        )

        self.model.compile(
            optimizer=optimizer,
            loss=keras.losses.SparseCategoricalCrossentropy(from_logits=True),
            metrics=[
                keras.metrics.SparseCategoricalAccuracy(name="accuracy"),
                keras.metrics.SparseTopKCategoricalAccuracy(5, name="top-5-accuracy"),
            ],
        )

        logger.info(f"Starting training for {epochs} epochs...")
        history = self.model.fit(
            x=x_train,
            y=y_train,
            batch_size=self.batch_size,
            epochs=epochs,
            validation_split=validation_split,
        )
        return history

    def evaluate(self, x_test, y_test):
        """Evaluates the model on test data."""
        logger.info("Evaluating on test set...")
        _, accuracy, top_5_accuracy = self.model.evaluate(x_test, y_test, batch_size=self.batch_size)
        logger.info(f"Test Accuracy: {accuracy * 100:.2f}%")
        logger.info(f"Top-5 Accuracy: {top_5_accuracy * 100:.2f}%")
        return accuracy


if __name__ == "__main__":
    # 1. Load CIFAR-100 (or any other dataset)
    logger.info("Loading CIFAR-100 dataset...")
    (x_train, y_train), (x_test, y_test) = keras.datasets.cifar100.load_data()
    
    NUM_CLASSES = 100
    INPUT_SHAPE = (32, 32, 3)

    # 2. Instantiate the Classifier
    vit_classifier = ViTSmallClassifier(
        input_shape=INPUT_SHAPE,
        num_classes=NUM_CLASSES,
        image_size=72,  # Resize inputs to this size
        patch_size=6,
        transformer_layers=4 # Reduced for demo speed (Paper uses 8)
    )

    # 3. Build Model (Set use_vanilla_vit=False to use SPT + LSA)
    vit_classifier.build_model(use_vanilla_vit=False)

    # 4. Train
    history = vit_classifier.train(x_train, y_train, epochs=20)

    # 5. Evaluate
    vit_classifier.evaluate(x_test, y_test)