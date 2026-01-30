import numpy as np
import matplotlib.pyplot as plt
import keras
from keras import ops
from keras import layers
import tensorflow as tf
import logging
import pathlib

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

SEED = 42
keras.utils.set_random_seed(SEED)


class Config:
    def __init__(self, 
                 input_shape=(32, 32, 3), 
                 num_classes=10, 
                 batch_size=256, 
                 image_size=48, 
                 patch_size=4, 
                 projected_dim=96,
                 num_shift_blocks_per_stages=[2, 4, 8, 2],
                 stochastic_depth_rate=0.2,
                 mlp_dropout_rate=0.2,
                 lr_max=1e-3,
                 epochs=100):
        self.input_shape = input_shape
        self.num_classes = num_classes
        self.batch_size = batch_size
        self.buffer_size = batch_size * 2
        self.image_size = image_size
        self.patch_size = patch_size
        self.projected_dim = projected_dim
        self.num_shift_blocks_per_stages = num_shift_blocks_per_stages
        self.epsilon = 1e-5
        self.stochastic_depth_rate = stochastic_depth_rate
        self.mlp_dropout_rate = mlp_dropout_rate
        self.num_div = 12
        self.shift_pixel = 1
        self.mlp_expand_ratio = 2
        self.lr_start = 1e-5
        self.lr_max = lr_max
        self.weight_decay = 1e-4
        self.epochs = epochs

# --- Custom Layers ---

class MLP(layers.Layer):
    """Dense layers for feature transformation."""
    def __init__(self, mlp_expand_ratio, mlp_dropout_rate, **kwargs):
        super().__init__(**kwargs)
        self.mlp_expand_ratio = mlp_expand_ratio
        self.mlp_dropout_rate = mlp_dropout_rate

    def build(self, input_shape):
        input_channels = input_shape[-1]
        initial_filters = int(self.mlp_expand_ratio * input_channels)
        self.mlp = keras.Sequential([
            layers.Dense(units=initial_filters, activation="gelu"),
            layers.Dropout(rate=self.mlp_dropout_rate),
            layers.Dense(units=input_channels),
            layers.Dropout(rate=self.mlp_dropout_rate),
        ])

    def call(self, x):
        return self.mlp(x)

class DropPath(layers.Layer):
    """Stochastic Depth regularization."""
    def __init__(self, drop_path_prob, **kwargs):
        super().__init__(**kwargs)
        self.drop_path_prob = drop_path_prob
        self.seed_generator = keras.random.SeedGenerator(1337)

    def call(self, x, training=False):
        if training:
            keep_prob = 1 - self.drop_path_prob
            shape = (ops.shape(x)[0],) + (1,) * (len(ops.shape(x)) - 1)
            random_tensor = keep_prob + keras.random.uniform(shape, 0, 1, seed=self.seed_generator)
            random_tensor = ops.floor(random_tensor)
            return (x / keep_prob) * random_tensor
        return x

class ShiftViTBlock(layers.Layer):
    """
    Core ShiftViT Unit.
    Performs the channel shifting operation instead of Attention.
    """
    def __init__(self, epsilon, drop_path_prob, mlp_dropout_rate, num_div=12, shift_pixel=1, mlp_expand_ratio=2, **kwargs):
        super().__init__(**kwargs)
        self.shift_pixel = shift_pixel
        self.mlp_expand_ratio = mlp_expand_ratio
        self.mlp_dropout_rate = mlp_dropout_rate
        self.num_div = num_div
        self.epsilon = epsilon
        self.drop_path_prob = drop_path_prob

    def build(self, input_shape):
        self.H, self.W, self.C = input_shape[1], input_shape[2], input_shape[3]
        self.layer_norm = layers.LayerNormalization(epsilon=self.epsilon)
        self.drop_path = DropPath(drop_path_prob=self.drop_path_prob) if self.drop_path_prob > 0.0 else layers.Activation("linear")
        self.mlp = MLP(mlp_expand_ratio=self.mlp_expand_ratio, mlp_dropout_rate=self.mlp_dropout_rate)

    def get_shift_pad(self, x, mode):
        # Calculate crop offsets based on shift direction
        if mode == "left":
            oh, ow, th, tw = 0, 0, 0, self.shift_pixel
        elif mode == "right":
            oh, ow, th, tw = 0, self.shift_pixel, 0, self.shift_pixel
        elif mode == "up":
            oh, ow, th, tw = 0, 0, self.shift_pixel, 0
        else: # down
            oh, ow, th, tw = self.shift_pixel, 0, self.shift_pixel, 0
            
        crop = ops.image.crop_images(x, top_cropping=oh, left_cropping=ow, target_height=self.H - th, target_width=self.W - tw)
        return ops.image.pad_images(crop, top_padding=oh, left_padding=ow, target_height=self.H, target_width=self.W)

    def call(self, x, training=False):
        # 1. Split channels
        x_splits = ops.split(x, indices_or_sections=self.C // self.num_div, axis=-1)
        
        # 2. Shift specific channel groups
        x_splits[0] = self.get_shift_pad(x_splits[0], mode="left")
        x_splits[1] = self.get_shift_pad(x_splits[1], mode="right")
        x_splits[2] = self.get_shift_pad(x_splits[2], mode="up")
        x_splits[3] = self.get_shift_pad(x_splits[3], mode="down")
        
        # 3. Concatenate back
        x = ops.concatenate(x_splits, axis=-1)
        
        # 4. Residual + MLP
        shortcut = x
        x = shortcut + self.drop_path(self.mlp(self.layer_norm(x)), training=training)
        return x

class PatchMerging(layers.Layer):
    """Merges adjacent patches to reduce spatial dim and increase channels."""
    def __init__(self, epsilon, **kwargs):
        super().__init__(**kwargs)
        self.epsilon = epsilon

    def build(self, input_shape):
        filters = 2 * input_shape[-1]
        self.reduction = layers.Conv2D(filters=filters, kernel_size=2, strides=2, padding="same", use_bias=False)
        self.layer_norm = layers.LayerNormalization(epsilon=self.epsilon)

    def call(self, x):
        return self.reduction(self.layer_norm(x))

class StackedShiftBlocks(layers.Layer):
    """A stage containing multiple ShiftViT blocks."""
    def __init__(self, epsilon, mlp_dropout_rate, num_shift_blocks, stochastic_depth_rate, is_merge, **kwargs):
        super().__init__(**kwargs)
        self.epsilon = epsilon
        self.mlp_dropout_rate = mlp_dropout_rate
        self.num_shift_blocks = num_shift_blocks
        self.stochastic_depth_rate = stochastic_depth_rate
        self.is_merge = is_merge

    def build(self, input_shape):
        dpr = np.linspace(0, self.stochastic_depth_rate, self.num_shift_blocks)
        self.shift_blocks = [ShiftViTBlock(epsilon=self.epsilon, drop_path_prob=dpr[i], mlp_dropout_rate=self.mlp_dropout_rate) for i in range(self.num_shift_blocks)]
        if self.is_merge:
            self.patch_merge = PatchMerging(epsilon=self.epsilon)

    def call(self, x, training=False):
        for block in self.shift_blocks:
            x = block(x, training=training)
        if self.is_merge:
            x = self.patch_merge(x)
        return x

class WarmUpCosine(keras.optimizers.schedules.LearningRateSchedule):
    """Cosine Decay with Linear Warmup."""
    def __init__(self, lr_start, lr_max, warmup_steps, total_steps):
        super().__init__()
        self.lr_start = lr_start
        self.lr_max = lr_max
        self.warmup_steps = warmup_steps
        self.total_steps = total_steps
        self.pi = ops.array(np.pi)

    def __call__(self, step):
        if self.total_steps < self.warmup_steps:
             raise ValueError("Total steps must be >= warmup steps")
        
        cos_annealed_lr = ops.cos(self.pi * (ops.cast(step, "float32") - self.warmup_steps) / ops.cast(self.total_steps - self.warmup_steps, "float32"))
        learning_rate = 0.5 * self.lr_max * (1 + cos_annealed_lr)

        if self.warmup_steps > 0:
             slope = (self.lr_max - self.lr_start) / self.warmup_steps
             warmup_rate = slope * ops.cast(step, "float32") + self.lr_start
             learning_rate = ops.where(step < self.warmup_steps, warmup_rate, learning_rate)
             
        return ops.where(step > self.total_steps, 0.0, learning_rate)

# --- Main Classifier Class ---

class ShiftViTClassifier:
    def __init__(self, config):
        """Initializes the classifier with a Config object."""
        self.cfg = config
        self.model = None
        self.train_ds = None
        self.val_ds = None
        self.test_ds = None
        logger.info(f"Initialized ShiftViT Classifier for {self.cfg.num_classes} classes.")

    def get_augmentation_model(self):
        """Creates the augmentation pipeline."""
        return keras.Sequential([
            layers.Resizing(self.cfg.input_shape[0] + 20, self.cfg.input_shape[0] + 20),
            layers.RandomCrop(self.cfg.image_size, self.cfg.image_size),
            layers.RandomFlip("horizontal"),
            layers.Rescaling(1 / 255.0),
        ])

    def prepare_data(self, x_train, y_train, x_val, y_val, x_test=None, y_test=None):
        """Converts numpy arrays to tf.data.Datasets."""
        logger.info("Preparing data pipelines...")
        AUTO = tf.data.AUTOTUNE
        
        self.train_ds = tf.data.Dataset.from_tensor_slices((x_train, y_train))
        self.train_ds = self.train_ds.shuffle(self.cfg.buffer_size).batch(self.cfg.batch_size).prefetch(AUTO)
        self.train_len = len(x_train)

        self.val_ds = tf.data.Dataset.from_tensor_slices((x_val, y_val))
        self.val_ds = self.val_ds.batch(self.cfg.batch_size).prefetch(AUTO)

        if x_test is not None:
            self.test_ds = tf.data.Dataset.from_tensor_slices((x_test, y_test))
            self.test_ds = self.test_ds.batch(self.cfg.batch_size).prefetch(AUTO)
        
        logger.info("Data ready.")

    def build_model(self):
        """Constructs the ShiftViT Model."""
        logger.info("Building ShiftViT architecture...")
        inputs = keras.Input(shape=self.cfg.input_shape)
        
        # Augmentation
        data_aug = self.get_augmentation_model()
        x = data_aug(inputs)

        # Patch Projection
        x = layers.Conv2D(filters=self.cfg.projected_dim, kernel_size=self.cfg.patch_size, strides=self.cfg.patch_size, padding="same")(x)

        # Stages
        for index, num_blocks in enumerate(self.cfg.num_shift_blocks_per_stages):
            is_merge = index != len(self.cfg.num_shift_blocks_per_stages) - 1
            x = StackedShiftBlocks(
                epsilon=self.cfg.epsilon,
                mlp_dropout_rate=self.cfg.mlp_dropout_rate,
                num_shift_blocks=num_blocks,
                stochastic_depth_rate=self.cfg.stochastic_depth_rate,
                is_merge=is_merge
            )(x)

        # Head
        x = layers.GlobalAveragePooling2D()(x)
        outputs = layers.Dense(self.cfg.num_classes)(x)

        self.model = keras.Model(inputs=inputs, outputs=outputs, name="ShiftViT")
        logger.info("Model built successfully.")

    def train(self):
        """Compiles and trains the model."""
        if self.model is None:
            raise ValueError("Model not built. Call build_model() first.")
        if self.train_ds is None:
             raise ValueError("Data not ready. Call prepare_data() first.")

        # LR Schedule
        total_steps = int((self.train_len / self.cfg.batch_size) * self.cfg.epochs)
        warmup_steps = int(total_steps * 0.15)
        
        scheduled_lrs = WarmUpCosine(
            lr_start=self.cfg.lr_start,
            lr_max=self.cfg.lr_max,
            warmup_steps=warmup_steps,
            total_steps=total_steps
        )
        
        optimizer = keras.optimizers.AdamW(learning_rate=scheduled_lrs, weight_decay=self.cfg.weight_decay)
        
        self.model.compile(
            optimizer=optimizer,
            loss=keras.losses.SparseCategoricalCrossentropy(from_logits=True),
            metrics=[
                keras.metrics.SparseCategoricalAccuracy(name="accuracy"),
                keras.metrics.SparseTopKCategoricalAccuracy(5, name="top-5-accuracy"),
            ],
        )

        # Pass a sample to initialize weights (needed for custom layers in Functional API sometimes)
        sample_ds, _ = next(iter(self.train_ds))
        self.model(sample_ds, training=False)

        logger.info("Starting training...")
        history = self.model.fit(
            self.train_ds,
            epochs=self.cfg.epochs,
            validation_data=self.val_ds,
            callbacks=[keras.callbacks.EarlyStopping(monitor="val_accuracy", patience=5, mode="auto")]
        )
        return history

    def evaluate(self):
        """Evaluates on the test set."""
        if self.test_ds is None:
            logger.warning("No test data provided.")
            return
        
        logger.info("Evaluating on test set...")
        loss, top1, top5 = self.model.evaluate(self.test_ds)
        logger.info(f"Test Loss: {loss:.4f}")
        logger.info(f"Top-1 Accuracy: {top1*100:.2f}%")
        logger.info(f"Top-5 Accuracy: {top5*100:.2f}%")

    def save_model(self, path="ShiftViT"):
        """Saves the model artifact."""
        self.model.export(path)
        logger.info(f"Model saved to {path}")


if __name__ == "__main__":
    # 1. Initialize Configuration
    config = Config(
        input_shape=(32, 32, 3), 
        num_classes=10, 
        epochs=30, # Reduced for demo
        batch_size=128
    )

    # 2. Instantiate Classifier
    classifier = ShiftViTClassifier(config)

    # 3. Load Data (CIFAR-10 Example)
    logger.info("Loading CIFAR-10 dataset...")
    (x_train, y_train), (x_test, y_test) = keras.datasets.cifar10.load_data()
    
    # Split validation set
    val_split = 40000
    x_val, y_val = x_train[val_split:], y_train[val_split:]
    x_train, y_train = x_train[:val_split], y_train[:val_split]

    # 4. Inject Data
    classifier.prepare_data(x_train, y_train, x_val, y_val, x_test, y_test)

    # 5. Build Model
    classifier.build_model()

    # 6. Train
    history = classifier.train()

    # 7. Evaluate
    classifier.evaluate()