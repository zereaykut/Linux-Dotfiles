import os
import logging
import tensorflow as tf
import keras
import keras_hub
from keras import layers
import numpy as np

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

class GPTTextGenerator:
    """
    A Miniature GPT model for text generation using KerasHub.
    """
    def __init__(
        self,
        vocab_size=5000,
        sequence_length=128,
        embed_dim=256,
        feed_forward_dim=256,
        num_heads=2,
        num_layers=2,
        batch_size=64,
        epochs=5
    ):
        """
        Initialize configuration.
        """
        self.vocab_size = vocab_size
        self.sequence_length = sequence_length
        self.embed_dim = embed_dim
        self.feed_forward_dim = feed_forward_dim
        self.num_heads = num_heads
        self.num_layers = num_layers
        self.batch_size = batch_size
        self.epochs = epochs
        
        self.tokenizer = None
        self.model = None
        self.train_ds = None
        
        logger.info("Initialized GPT Generator.")

    def _train_tokenizer(self, text_samples):
        """
        Trains a WordPiece tokenizer on the provided text.
        """
        logger.info("Training tokenizer...")
        # Create a dataset from the raw text list
        raw_ds = tf.data.Dataset.from_tensor_slices(text_samples)
        
        tokenizer = keras_hub.tokenizers.WordPieceTokenizer(
            trainable=True,
            sequence_length=self.sequence_length,
            lowercase=True,
            strip_accents=True,
        )
        # Train on the dataset
        tokenizer.train(
            raw_ds, 
            vocab_size=self.vocab_size,
            special_tokens=["[PAD]", "[UNK]", "[START]", "[END]"]
        )
        return tokenizer

    def _preprocess(self, text):
        """
        Tokenizes text and splits into inputs (x) and targets (y).
        x: tokens 0 to N-1
        y: tokens 1 to N
        """
        tokens = self.tokenizer(text)
        return tokens[:, :-1], tokens[:, 1:]

    def prepare_data(self, text_samples):
        """
        Trains tokenizer and builds the TF Dataset.
        """
        if not text_samples:
            raise ValueError("No text samples provided.")

        # 1. Train Tokenizer
        self.tokenizer = self._train_tokenizer(text_samples)
        
        # 2. Build Dataset
        logger.info("Building dataset pipeline...")
        ds = tf.data.Dataset.from_tensor_slices(text_samples)
        ds = ds.batch(self.batch_size)
        ds = ds.map(self._preprocess, num_parallel_calls=tf.data.AUTOTUNE)
        self.train_ds = ds.prefetch(tf.data.AUTOTUNE)
        
        logger.info("Data ready.")

    def build_model(self):
        """
        Constructs the GPT model using KerasHub layers.
        """
        logger.info("Building GPT model architecture...")
        inputs = keras.Input(shape=(None,), dtype="int32")
        
        # 1. Embedding (Token + Position)
        x = keras_hub.layers.TokenAndPositionEmbedding(
            vocabulary_size=self.vocab_size,
            sequence_length=self.sequence_length,
            embedding_dim=self.embed_dim,
        )(inputs)
        
        # 2. Transformer Decoder Blocks (Stacked)
        for _ in range(self.num_layers):
            x = keras_hub.layers.TransformerDecoder(
                intermediate_dim=self.feed_forward_dim,
                num_heads=self.num_heads,
            )(x)
            
        # 3. Output Layer
        outputs = layers.Dense(self.vocab_size, activation="softmax")(x)
        
        self.model = keras.Model(inputs, outputs)
        
        loss_fn = keras.losses.SparseCategoricalCrossentropy(from_logits=False)
        perplexity = keras_hub.metrics.Perplexity(from_logits=False, mask_token_id=0)
        
        self.model.compile(optimizer="adam", loss=loss_fn, metrics=[perplexity])
        logger.info("Model built successfully.")

    def train(self):
        """
        Trains the model.
        """
        if self.model is None:
            raise ValueError("Model not built. Call build_model() first.")
        
        logger.info(f"Starting training for {self.epochs} epochs...")
        
        # Optional: Callback to generate text during training
        gen_callback = self.TextGenCallback(self, prompt="The quick brown fox")
        
        history = self.model.fit(
            self.train_ds,
            epochs=self.epochs,
            callbacks=[gen_callback]
        )
        return history

    def generate_text(self, prompt, max_length=50):
        """
        Generates text using Greedy Search (via KerasHub Sampler).
        """
        # Tokenize prompt
        tokenized_prompt = self.tokenizer([prompt])[:, :-1] # Remove end token if added
        
        # KerasHub GreedySampler
        sampler = keras_hub.samplers.GreedySampler()
        
        # Function wrapper for sampler
        # The sampler expects a 'next' function that returns probabilities
        def next_token_fn(prompt_tokens, cache=None, index=0):
            logits = self.model(prompt_tokens)
            # Return probabilities for the last token
            return logits[:, index-1, :]

        output_tokens = sampler(
            next=next_token_fn,
            prompt=tokenized_prompt,
            index=1 # Start index inside prompt? Actually typically handled inside wrapper
            # Note: KerasHub Samplers usage can vary slightly by version.
            # Simplified manual loop below for robustness across versions if simpler:
        )
        
        # Let's stick to a robust manual generation loop using the trained model
        # if KerasHub sampler API is complex to wrap in one line
        
        curr_tokens = tokenized_prompt
        
        for _ in range(max_length):
            preds = self.model(curr_tokens)
            # Greedily pick next token
            next_token = np.argmax(preds[:, -1, :], axis=-1)
            next_token = next_token[np.newaxis, :] # Add batch dim
            curr_tokens = np.concatenate([curr_tokens, next_token], axis=1)
            
        decoded = self.tokenizer.detokenize(curr_tokens)
        return decoded.numpy()[0].decode("utf-8")

    # Inner class for callback
    class TextGenCallback(keras.callbacks.Callback):
        def __init__(self, generator, prompt):
            self.generator = generator
            self.prompt = prompt
            
        def on_epoch_end(self, epoch, logs=None):
            txt = self.generator.generate_text(self.prompt, max_length=20)
            print(f"\nGenerated text (epoch {epoch+1}): {txt}\n")


# --- Data Helper ---

def load_simple_books_data():
    """
    Downloads simplebooks dataset.
    """
    logger.info("Downloading dataset...")
    # Using keras.utils.get_file to download dataset
    file_path = keras.utils.get_file(
        origin="https://dldata-public.s3.us-east-2.amazonaws.com/simplebooks.zip",
        extract=True,
    )
    dir_path = os.path.dirname(file_path)
    with open(os.path.join(dir_path, "simplebooks/simplebooks-92-raw/train.txt"), "r", encoding="utf-8") as f:
        text_samples = f.read().split("\n")
        
    # Filter short lines
    text_samples = [x for x in text_samples if len(x) > 20]
    return text_samples


if __name__ == "__main__":
    # 1. Load Data
    text_data = load_simple_books_data()
    # Use subset for demo
    text_data = text_data[:1000] 
    
    # 2. Instantiate Generator
    gpt = GPTTextGenerator(
        vocab_size=5000,
        sequence_length=64, # Short sequence for demo
        num_layers=2,
        epochs=5,
        batch_size=32
    )
    
    # 3. Prepare Data
    gpt.prepare_data(text_data)
    
    # 4. Build Model
    gpt.build_model()
    
    # 5. Train
    gpt.train()
    
    # 6. Generate
    prompt = "Once upon a time"
    generated = gpt.generate_text(prompt, max_length=30)
    print(f"\nFinal Result:\n{generated}")