import os
import logging
import tensorflow as tf
import keras
from keras import layers
import numpy as np
import re

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# --- Custom Layers ---

class FNetEncoder(layers.Layer):
    """
    FNet Encoder Block.
    Replaces Self-Attention with a 2D Fourier Transform for token mixing.
    """
    def __init__(self, embed_dim, dense_dim, dropout_rate=0.1, **kwargs):
        super().__init__(**kwargs)
        self.embed_dim = embed_dim
        self.dense_dim = dense_dim
        self.dense_proj = keras.Sequential(
            [
                layers.Dense(dense_dim, activation="gelu"),
                layers.Dense(embed_dim),
            ]
        )
        self.layernorm_1 = layers.LayerNormalization()
        self.layernorm_2 = layers.LayerNormalization()
        self.dropout = layers.Dropout(dropout_rate)

    def call(self, inputs):
        # 1. Fourier Transform Mixing
        # Cast to complex, perform FFT, keep real part
        inp_complex = tf.cast(inputs, tf.complex64)
        fft = tf.math.real(tf.signal.fft2d(inp_complex))
        proj_input = self.layernorm_1(inputs + fft)
        
        # 2. Feed Forward
        proj_output = self.dense_proj(proj_input)
        return self.layernorm_2(proj_input + proj_output)


class PositionalEmbedding(layers.Layer):
    """Adds learnable position embeddings to tokens."""
    def __init__(self, sequence_length, vocab_size, embed_dim, **kwargs):
        super().__init__(**kwargs)
        self.token_embeddings = layers.Embedding(
            input_dim=vocab_size, output_dim=embed_dim
        )
        self.position_embeddings = layers.Embedding(
            input_dim=sequence_length, output_dim=embed_dim
        )
        self.sequence_length = sequence_length
        self.vocab_size = vocab_size
        self.embed_dim = embed_dim

    def call(self, inputs):
        length = tf.shape(inputs)[-1]
        positions = tf.range(start=0, limit=length, delta=1)
        embedded_tokens = self.token_embeddings(inputs)
        embedded_positions = self.position_embeddings(positions)
        return embedded_tokens + embedded_positions

    def compute_mask(self, inputs, mask=None):
        return tf.math.not_equal(inputs, 0)


class TransformerDecoder(layers.Layer):
    """Standard Transformer Decoder."""
    def __init__(self, embed_dim, latent_dim, num_heads, dropout_rate=0.1, **kwargs):
        super().__init__(**kwargs)
        self.embed_dim = embed_dim
        self.latent_dim = latent_dim
        self.num_heads = num_heads
        self.attention_1 = layers.MultiHeadAttention(
            num_heads=num_heads, key_dim=embed_dim
        )
        self.attention_2 = layers.MultiHeadAttention(
            num_heads=num_heads, key_dim=embed_dim
        )
        self.dense_proj = keras.Sequential(
            [
                layers.Dense(latent_dim, activation="gelu"),
                layers.Dense(embed_dim),
            ]
        )
        self.layernorm_1 = layers.LayerNormalization()
        self.layernorm_2 = layers.LayerNormalization()
        self.layernorm_3 = layers.LayerNormalization()
        self.dropout = layers.Dropout(dropout_rate)

    def call(self, inputs, encoder_outputs, mask=None):
        # Self Attention
        attention_output_1 = self.attention_1(
            query=inputs, value=inputs, key=inputs, use_causal_mask=True
        )
        out_1 = self.layernorm_1(inputs + attention_output_1)

        # Cross Attention
        attention_output_2 = self.attention_2(
            query=out_1, value=encoder_outputs, key=encoder_outputs
        )
        out_2 = self.layernorm_2(out_1 + attention_output_2)

        # Feed Forward
        proj_output = self.dense_proj(out_2)
        return self.layernorm_3(out_2 + proj_output)


# --- Main Generator Class ---

class FNetTextGenerator:
    def __init__(
        self,
        vocab_size=8192,
        max_length=40,
        embed_dim=256,
        latent_dim=512,
        num_heads=8,
        batch_size=64,
        epochs=1
    ):
        """Initialize hyperparameters."""
        self.vocab_size = vocab_size
        self.max_length = max_length
        self.embed_dim = embed_dim
        self.latent_dim = latent_dim
        self.num_heads = num_heads
        self.batch_size = batch_size
        self.epochs = epochs
        
        self.vectorizer = None
        self.model = None
        self.train_ds = None
        self.val_ds = None
        self.vocab = None
        
        logger.info("Initialized FNet Generator.")

    def _preprocess_text(self, sentence):
        """Cleans text."""
        sentence = tf.strings.lower(sentence)
        sentence = tf.strings.regex_replace(sentence, "([?.!,])", r" \1 ")
        sentence = tf.strings.regex_replace(sentence, r"[^a-z?.!,]+", " ")
        sentence = tf.strings.strip(sentence)
        return tf.strings.join(["[start]", sentence, "[end]"], separator=" ")

    def prepare_data(self, inputs, outputs, validation_split=0.15):
        """
        Tokenizes and prepares TF Datasets.
        inputs: List of strings (Source)
        outputs: List of strings (Target)
        """
        logger.info("Fitting vectorizer...")
        self.vectorizer = layers.TextVectorization(
            max_tokens=self.vocab_size,
            output_mode="int",
            output_sequence_length=self.max_length,
            standardize=self._preprocess_text,
        )
        self.vectorizer.adapt(tf.data.Dataset.from_tensor_slices(inputs + outputs).batch(128))
        self.vocab = self.vectorizer.get_vocabulary()
        
        logger.info("Building TF Datasets...")
        
        def format_dataset(inp, out):
            return (
                {
                    "encoder_inputs": self.vectorizer(inp),
                    "decoder_inputs": self.vectorizer(out)[:, :-1],
                },
                self.vectorizer(out)[:, 1:],
            )

        def make_dataset(inp, out):
            ds = tf.data.Dataset.from_tensor_slices((inp, out))
            ds = ds.batch(self.batch_size)
            ds = ds.map(format_dataset, num_parallel_calls=tf.data.AUTOTUNE)
            return ds.prefetch(tf.data.AUTOTUNE)

        # Split
        split_idx = int(len(inputs) * (1 - validation_split))
        self.train_ds = make_dataset(inputs[:split_idx], outputs[:split_idx])
        self.val_ds = make_dataset(inputs[split_idx:], outputs[split_idx:])
        
        logger.info("Data pipelines ready.")

    def build_model(self):
        """Constructs the FNet Seq2Seq model."""
        logger.info("Building model architecture...")
        
        # Encoder
        encoder_inputs = keras.Input(shape=(None,), dtype="int64", name="encoder_inputs")
        x = PositionalEmbedding(self.max_length, self.vocab_size, self.embed_dim)(encoder_inputs)
        encoder_outputs = FNetEncoder(self.embed_dim, self.latent_dim)(x)
        
        # Decoder
        decoder_inputs = keras.Input(shape=(None,), dtype="int64", name="decoder_inputs")
        encoded_seq_inputs = keras.Input(shape=(None, self.embed_dim), name="decoder_state_inputs")
        x = PositionalEmbedding(self.max_length, self.vocab_size, self.embed_dim)(decoder_inputs)
        x = TransformerDecoder(self.embed_dim, self.latent_dim, self.num_heads)(x, encoded_seq_inputs)
        decoder_outputs = layers.Dense(self.vocab_size, activation="softmax")(x)
        
        decoder = keras.Model([decoder_inputs, encoded_seq_inputs], decoder_outputs, name="decoder")
        
        # Full Model
        decoder_outputs = decoder([decoder_inputs, encoder_outputs])
        self.model = keras.Model(
            [encoder_inputs, decoder_inputs], decoder_outputs, name="fnet_seq2seq"
        )
        
        self.model.compile(
            optimizer="adam", 
            loss="sparse_categorical_crossentropy", 
            metrics=["accuracy"]
        )
        logger.info("Model built successfully.")

    def train(self):
        """Trains the model."""
        if self.model is None:
            raise ValueError("Model not built.")
        
        logger.info(f"Starting training for {self.epochs} epochs...")
        history = self.model.fit(
            self.train_ds,
            epochs=self.epochs,
            validation_data=self.val_ds
        )
        return history

    def generate_response(self, input_text):
        """
        Generates a response using Greedy Decoding.
        """
        tokenized_input = self.vectorizer([input_text])
        decoded_sentence = "[start]"
        
        # Encode input once (sub-model extraction)
        # Note: For efficiency in full implementation, we'd extract the encoder model separately
        # Here we just run prediction iteratively which is fine for demo
        
        vocab_lookup = dict(zip(range(len(self.vocab)), self.vocab))
        
        for i in range(self.max_length):
            tokenized_target = self.vectorizer([decoded_sentence])[:, :-1]
            predictions = self.model.predict(
                {"encoder_inputs": tokenized_input, "decoder_inputs": tokenized_target},
                verbose=0
            )
            
            sampled_token_index = np.argmax(predictions[0, i, :])
            sampled_token = vocab_lookup.get(sampled_token_index, "[UNK]")
            
            if sampled_token == "[end]":
                break
                
            decoded_sentence += " " + sampled_token
            
        return decoded_sentence.replace("[start]", "").strip()

# --- Data Helper ---

def load_cornell_data():
    """Downloads and parses Cornell Movie Dialog Corpus."""
    logger.info("Downloading Cornell Movie Dataset...")
    path = keras.utils.get_file(
        "cornell_movie_dialogs.zip",
        origin="http://www.cs.cornell.edu/~cristian/data/cornell_movie_dialogs_corpus.zip",
        extract=True,
    )
    path = os.path.join(os.path.dirname(path), "cornell movie-dialogs corpus")
    
    # Load Lines
    with open(os.path.join(path, "movie_lines.txt"), errors="ignore") as f:
        lines = f.read().split("\n")
        
    id2line = {}
    for line in lines:
        parts = line.split(" +++$+++ ")
        if len(parts) == 5:
            id2line[parts[0]] = parts[4]

    # Load Conversations
    with open(os.path.join(path, "movie_conversations.txt"), errors="ignore") as f:
        conversations = f.read().split("\n")
        
    questions, answers = [], []
    for conv in conversations:
        parts = conv.split(" +++$+++ ")
        if len(parts) == 4:
            # The list of line IDs is a string "['L194', 'L195', ...]"
            # We treat it as string manipulation to avoid evaluating code
            line_ids = parts[3][1:-1].replace("'", "").replace(" ", "").split(",")
            
            for i in range(len(line_ids) - 1):
                questions.append(id2line.get(line_ids[i]))
                answers.append(id2line.get(line_ids[i + 1]))
                
    # Filter Nones
    pairs = [(q, a) for q, a in zip(questions, answers) if q and a]
    return [p[0] for p in pairs], [p[1] for p in pairs]


if __name__ == "__main__":
    # 1. Load Data
    questions, answers = load_cornell_data()
    # Use subset for demo speed
    questions, answers = questions[:5000], answers[:5000]
    
    # 2. Instantiate Generator
    fnet_gen = FNetTextGenerator(
        vocab_size=8192,
        max_length=40,
        epochs=5,
        batch_size=64
    )
    
    # 3. Prepare Data
    fnet_gen.prepare_data(questions, answers)
    
    # 4. Build Model
    fnet_gen.build_model()
    
    # 5. Train
    fnet_gen.train()
    
    # 6. Test Generation
    test_q = "How are you doing?"
    response = fnet_gen.generate_response(test_q)
    print(f"\nQ: {test_q}\nA: {response}")