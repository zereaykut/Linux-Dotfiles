import os
import numpy as np
import keras
from keras import layers
import matplotlib.pyplot as plt
import logging

# --- Configuration & Setup ---

OUTPUT_DIR = "cct_out"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Configure Logging to write to both File and Console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S',
    handlers=[
        logging.FileHandler(os.path.join(OUTPUT_DIR, "training.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# --- Helper Layers (Same as before) ---

class CCTTokenizer(layers.Layer):
    def __init__(
        self,
        kernel_size=3,
        stride=1,
        padding=1,
        pooling_kernel_size=3,
        pooling_stride=2,
        num_conv_layers=2,
        num_output_channels=[64, 128],
        positional_emb=True,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.conv_model = keras.Sequential()
        for i in range(num_conv_layers):
            self.conv_model.add(
                layers.Conv2D(
                    num_output_channels[i],
                    kernel_size,
                    stride,
                    padding="valid",
                    use_bias=False,
                    activation="relu",
                    kernel_initializer="he_normal",
                )
            )
            self.conv_model.add(layers.ZeroPadding2D(padding))
            self.conv_model.add(
                layers.MaxPooling2D(pooling_kernel_size, pooling_stride, "same")
            )
        self.positional_emb = positional_emb

    def call(self, images):
        outputs = self.conv_model(images)
        reshaped = keras.ops.reshape(
            outputs,
            (
                -1,
                keras.ops.shape(outputs)[1] * keras.ops.shape(outputs)[2],
                keras.ops.shape(outputs)[-1],
            ),
        )
        return reshaped

class PositionEmbedding(layers.Layer):
    def __init__(self, sequence_length, initializer="glorot_uniform", **kwargs):
        super().__init__(**kwargs)
        if sequence_length is None:
            raise ValueError("`sequence_length` must be an Integer, received `None`.")
        self.sequence_length = int(sequence_length)
        self.initializer = keras.initializers.get(initializer)

    def build(self, input_shape):
        feature_size = input_shape[-1]
        self.position_embeddings = self.add_weight(
            name="embeddings",
            shape=[self.sequence_length, feature_size],
            initializer=self.initializer,
            trainable=True,
        )
        super().build(input_shape)

    def call(self, inputs, start_index=0):
        shape = keras.ops.shape(inputs)
        feature_length = shape[-1]
        sequence_length = shape[-2]
        position_embeddings = keras.ops.convert_to_tensor(self.position_embeddings)
        position_embeddings = keras.ops.slice(
            position_embeddings,
            (start_index, 0),
            (sequence_length, feature_length),
        )
        return keras.ops.broadcast_to(position_embeddings, shape)

class SequencePooling(layers.Layer):
    def __init__(self):
        super().__init__()
        self.attention = layers.Dense(1)

    def call(self, x):
        attention_weights = keras.ops.softmax(self.attention(x), axis=1)
        attention_weights = keras.ops.transpose(attention_weights, axes=(0, 2, 1))
        weighted_representation = keras.ops.matmul(attention_weights, x)
        return keras.ops.squeeze(weighted_representation, -2)

class StochasticDepth(layers.Layer):
    def __init__(self, drop_prop, **kwargs):
        super().__init__(**kwargs)
        self.drop_prob = drop_prop
        self.seed_generator = keras.random.SeedGenerator(1337)

    def call(self, x, training=None):
        if training:
            keep_prob = 1 - self.drop_prob
            shape = (keras.ops.shape(x)[0],) + (1,) * (len(x.shape) - 1)
            random_tensor = keep_prob + keras.random.uniform(
                shape, 0, 1, seed=self.seed_generator
            )
            random_tensor = keras.ops.floor(random_tensor)
            return (x / keep_prob) * random_tensor
        return x

# --- Main Classifier Class ---

class CCTClassifier:
    def __init__(
        self,
        output_dir=OUTPUT_DIR,
        input_shape=(32, 32, 3),
        num_classes=10,
        image_size=32,
        projection_dim=128,
        num_heads=2,
        transformer_layers=2,
        stochastic_depth_rate=0.1,
    ):
        self.output_dir = output_dir
        self.input_shape = input_shape
        self.num_classes = num_classes
        self.image_size = image_size
        self.projection_dim = projection_dim
        self.num_heads = num_heads
        self.transformer_units = [projection_dim, projection_dim]
        self.transformer_layers = transformer_layers
        self.stochastic_depth_rate = stochastic_depth_rate
        
        self.model = None
        self.x_train = None
        self.y_train = None
        self.x_test = None
        self.y_test = None
        
        logger.info(f"Initialized CCT Classifier. Outputs will be saved to: {self.output_dir}")

    def prepare_data(self, x_train, y_train, x_test, y_test):
        logger.info("Preprocessing data...")
        self.x_train = x_train
        self.x_test = x_test
        self.y_train = keras.utils.to_categorical(y_train, self.num_classes)
        self.y_test = keras.utils.to_categorical(y_test, self.num_classes)
        logger.info(f"Data ready. Train shape: {self.x_train.shape}")

    def _mlp(self, x, hidden_units, dropout_rate):
        for units in hidden_units:
            x = layers.Dense(units, activation=keras.ops.gelu)(x)
            x = layers.Dropout(dropout_rate)(x)
        return x

    def build_model(self):
        logger.info("Building CCT model architecture...")
        inputs = layers.Input(self.input_shape)

        data_augmentation = keras.Sequential(
            [
                layers.Rescaling(scale=1.0 / 255),
                layers.RandomCrop(self.image_size, self.image_size),
                layers.RandomFlip("horizontal"),
            ],
            name="data_augmentation",
        )
        augmented = data_augmentation(inputs)

        cct_tokenizer = CCTTokenizer()
        encoded_patches = cct_tokenizer(augmented)

        sequence_length = encoded_patches.shape[1]
        encoded_patches += PositionEmbedding(sequence_length=sequence_length)(
            encoded_patches
        )

        dpr = [x for x in np.linspace(0, self.stochastic_depth_rate, self.transformer_layers)]

        for i in range(self.transformer_layers):
            x1 = layers.LayerNormalization(epsilon=1e-5)(encoded_patches)
            
            attention_output = layers.MultiHeadAttention(
                num_heads=self.num_heads, key_dim=self.projection_dim, dropout=0.1
            )(x1, x1)
            
            attention_output = StochasticDepth(dpr[i])(attention_output)
            x2 = layers.Add()([attention_output, encoded_patches])

            x3 = layers.LayerNormalization(epsilon=1e-5)(x2)
            x3 = self._mlp(x3, hidden_units=self.transformer_units, dropout_rate=0.1)

            x3 = StochasticDepth(dpr[i])(x3)
            encoded_patches = layers.Add()([x3, x2])

        representation = layers.LayerNormalization(epsilon=1e-5)(encoded_patches)
        weighted_representation = SequencePooling()(representation)
        logits = layers.Dense(self.num_classes)(weighted_representation)

        self.model = keras.Model(inputs=inputs, outputs=logits)
        logger.info("Model built successfully.")

    def train(self, learning_rate=0.001, weight_decay=0.0001, batch_size=128, epochs=30):
        if self.model is None:
            raise ValueError("Model not built. Call build_model() first.")
            
        logger.info(f"Starting training for {epochs} epochs...")
        
        optimizer = keras.optimizers.AdamW(learning_rate=learning_rate, weight_decay=weight_decay)

        self.model.compile(
            optimizer=optimizer,
            loss=keras.losses.CategoricalCrossentropy(
                from_logits=True, label_smoothing=0.1
            ),
            metrics=[
                keras.metrics.CategoricalAccuracy(name="accuracy"),
                keras.metrics.TopKCategoricalAccuracy(5, name="top-5-accuracy"),
            ],
        )

        # Save weights specifically to the output folder
        checkpoint_path = os.path.join(self.output_dir, "best_weights.weights.h5")
        checkpoint_callback = keras.callbacks.ModelCheckpoint(
            checkpoint_path,
            monitor="val_accuracy",
            save_best_only=True,
            save_weights_only=True,
        )

        history = self.model.fit(
            x=self.x_train,
            y=self.y_train,
            batch_size=batch_size,
            epochs=epochs,
            validation_split=0.1,
            callbacks=[checkpoint_callback],
        )
        
        self.model.load_weights(checkpoint_path)
        logger.info(f"Training finished. Best weights saved to {checkpoint_path}")
        return history

    def evaluate(self):
        logger.info("Evaluating on test set...")
        _, accuracy, top_5_accuracy = self.model.evaluate(self.x_test, self.y_test)
        logger.info(f"Test accuracy: {round(accuracy * 100, 2)}%")
        logger.info(f"Test top 5 accuracy: {round(top_5_accuracy * 100, 2)}%")
        return accuracy

    def save_plot(self, history):
        """Generates and saves the loss plot to the output directory."""
        plt.figure(figsize=(10, 6))
        plt.plot(history.history["loss"], label="train_loss")
        plt.plot(history.history["val_loss"], label="val_loss")
        plt.xlabel("Epochs")
        plt.ylabel("Loss")
        plt.title("Train and Validation Losses")
        plt.legend()
        plt.grid()
        
        plot_path = os.path.join(self.output_dir, "loss_curve.png")
        plt.savefig(plot_path)
        logger.info(f"Loss plot saved to {plot_path}")
        plt.close() # Close to free memory

if __name__ == "__main__":
    # 1. Instantiate (Output dir is set globally but can be overridden here)
    cct = CCTClassifier(
        output_dir="cct_out",
        input_shape=(32, 32, 3),
        num_classes=10,
        transformer_layers=2, 
        projection_dim=128
    )

    # 2. Load Data
    logger.info("Loading CIFAR-10 dataset...")
    (x_train, y_train), (x_test, y_test) = keras.datasets.cifar10.load_data()

    # 3. Inject Data
    cct.prepare_data(x_train, y_train, x_test, y_test)

    # 4. Build Model
    cct.build_model()

    # 5. Train
    history = cct.train(epochs=30, batch_size=128)

    # 6. Save Plot
    cct.save_plot(history)

    # 7. Final Evaluation
    cct.evaluate()