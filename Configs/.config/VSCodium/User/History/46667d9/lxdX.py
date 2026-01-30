import logging
import keras
from keras import ops
from keras import layers
import numpy as np

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# --- Custom Layers ---

class TransformerBlock(layers.Layer):
    """
    The core Transformer block.
    Consists of Multi-Head Self-Attention, LayerNormalization, and Feed-Forward Network.
    """
    def __init__(self, embed_dim, num_heads, ff_dim, rate=0.1, **kwargs):
        super().__init__(**kwargs)
        self.att = layers.MultiHeadAttention(num_heads=num_heads, key_dim=embed_dim)
        self.ffn = keras.Sequential(
            [
                layers.Dense(ff_dim, activation="relu"),
                layers.Dense(embed_dim),
            ]
        )
        self.layernorm1 = layers.LayerNormalization(epsilon=1e-6)
        self.layernorm2 = layers.LayerNormalization(epsilon=1e-6)
        self.dropout1 = layers.Dropout(rate)
        self.dropout2 = layers.Dropout(rate)
        
        self.embed_dim = embed_dim
        self.num_heads = num_heads
        self.ff_dim = ff_dim
        self.rate = rate

    def call(self, inputs):
        # Multi-Head Attention with residual connection
        attn_output = self.att(inputs, inputs)
        attn_output = self.dropout1(attn_output)
        out1 = self.layernorm1(inputs + attn_output)
        
        # Feed-Forward with residual connection
        ffn_output = self.ffn(out1)
        ffn_output = self.dropout2(ffn_output)
        return self.layernorm2(out1 + ffn_output)
    
    def get_config(self):
        config = super().get_config()
        config.update({
            "embed_dim": self.embed_dim,
            "num_heads": self.num_heads,
            "ff_dim": self.ffn_dim,
            "rate": self.rate,
        })
        return config


class TokenAndPositionEmbedding(layers.Layer):
    """
    Combines token embeddings with learnable position embeddings.
    """
    def __init__(self, maxlen, vocab_size, embed_dim, **kwargs):
        super().__init__(**kwargs)
        self.token_emb = layers.Embedding(input_dim=vocab_size, output_dim=embed_dim)
        self.pos_emb = layers.Embedding(input_dim=maxlen, output_dim=embed_dim)
        self.maxlen = maxlen
        self.vocab_size = vocab_size
        self.embed_dim = embed_dim

    def call(self, x):
        maxlen = ops.shape(x)[-1]
        positions = ops.arange(start=0, stop=maxlen, step=1)
        positions = self.pos_emb(positions)
        x = self.token_emb(x)
        return x + positions

    def get_config(self):
        config = super().get_config()
        config.update({
            "maxlen": self.maxlen,
            "vocab_size": self.vocab_size,
            "embed_dim": self.embed_dim,
        })
        return config

# --- Main Classifier Class ---

class TransformerClassifier:
    def __init__(
        self,
        maxlen=200,
        vocab_size=20000,
        embed_dim=32,
        num_heads=2,
        ff_dim=32,
        num_classes=2
    ):
        """
        Initializes the Transformer Classifier configuration.
        """
        self.maxlen = maxlen
        self.vocab_size = vocab_size
        self.embed_dim = embed_dim
        self.num_heads = num_heads
        self.ff_dim = ff_dim
        self.num_classes = num_classes
        self.model = None
        
        logger.info(f"Initialized Transformer Classifier (Heads={num_heads}, EmbedDim={embed_dim})")

    def build_model(self):
        """
        Constructs the model architecture.
        Structure: Inputs -> Embedding -> Transformer Block -> GAP -> Dropout -> Dense -> Output
        """
        logger.info("Building model architecture...")
        inputs = layers.Input(shape=(self.maxlen,))
        
        # 1. Embedding Layer
        embedding_layer = TokenAndPositionEmbedding(self.maxlen, self.vocab_size, self.embed_dim)
        x = embedding_layer(inputs)
        
        # 2. Transformer Block
        transformer_block = TransformerBlock(self.embed_dim, self.num_heads, self.ff_dim)
        x = transformer_block(x)
        
        # 3. Classification Head
        x = layers.GlobalAveragePooling1D()(x)
        x = layers.Dropout(0.1)(x)
        x = layers.Dense(20, activation="relu")(x)
        x = layers.Dropout(0.1)(x)
        
        # Output logic based on number of classes
        if self.num_classes == 2:
            outputs = layers.Dense(2, activation="softmax")(x)
            loss = "sparse_categorical_crossentropy"
        else:
            # Assumes sparse integers for labels (0, 1, 2...)
            outputs = layers.Dense(self.num_classes, activation="softmax")(x)
            loss = "sparse_categorical_crossentropy"
            
        self.model = keras.Model(inputs=inputs, outputs=outputs)
        
        self.model.compile(
            optimizer="adam", 
            loss=loss, 
            metrics=["accuracy"]
        )
        logger.info("Model built and compiled.")

    def prepare_data(self, x_train, x_val):
        """
        Pads sequences to ensure they are all length `self.maxlen`.
        Assumes input is already integer-indexed (like IMDB dataset).
        """
        logger.info(f"Padding sequences to length {self.maxlen}...")
        x_train = keras.utils.pad_sequences(x_train, maxlen=self.maxlen)
        x_val = keras.utils.pad_sequences(x_val, maxlen=self.maxlen)
        return x_train, x_val

    def train(self, x_train, y_train, x_val, y_val, batch_size=32, epochs=2):
        """
        Trains the model on the provided data.
        """
        if self.model is None:
            raise ValueError("Model not built. Call build_model() first.")
        
        logger.info(f"Starting training for {epochs} epochs...")
        history = self.model.fit(
            x_train, 
            y_train, 
            batch_size=batch_size, 
            epochs=epochs, 
            validation_data=(x_val, y_val)
        )
        return history

    def evaluate(self, x_test, y_test):
        """
        Evaluates the model on test data.
        """
        logger.info("Evaluating on test set...")
        x_test = keras.utils.pad_sequences(x_test, maxlen=self.maxlen)
        loss, accuracy = self.model.evaluate(x_test, y_test)
        logger.info(f"Test Accuracy: {accuracy:.4f}")
        return accuracy


if __name__ == "__main__":
    # 1. Configuration
    VOCAB_SIZE = 20000  
    MAXLEN = 200
    
    # 2. Instantiate Classifier
    classifier = TransformerClassifier(
        maxlen=MAXLEN,
        vocab_size=VOCAB_SIZE,
        embed_dim=32,
        num_heads=2,
        ff_dim=32,
        num_classes=2
    )

    # 3. Load Data (Using IMDB as example)
    logger.info("Loading IMDB dataset...")
    (x_train, y_train), (x_val, y_val) = keras.datasets.imdb.load_data(num_words=VOCAB_SIZE)
    
    # 4. Prepare Data (Padding)
    x_train, x_val = classifier.prepare_data(x_train, x_val)

    # 5. Build Model
    classifier.build_model()

    # 6. Train
    history = classifier.train(x_train, y_train, x_val, y_val, epochs=2)

    # 7. Evaluate
    classifier.evaluate(x_val, y_val)