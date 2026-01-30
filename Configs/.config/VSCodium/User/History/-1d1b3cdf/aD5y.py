import os
import random
import logging
import numpy as np
import tensorflow as tf
import keras
import keras_hub
from keras import layers
from keras import ops

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

class TranslatorSystem:
    def __init__(
        self,
        batch_size=64,
        num_epochs=1,
        vocab_size=15000,
        sequence_length=20,
        embed_dim=256,
        latent_dim=2048,
        num_heads=8,
    ):
        """
        Initializes hyperparameters for the Translation System.
        """
        self.batch_size = batch_size
        self.num_epochs = num_epochs
        self.vocab_size = vocab_size
        self.sequence_length = sequence_length
        self.embed_dim = embed_dim
        self.latent_dim = latent_dim
        self.num_heads = num_heads
        
        self.source_tokenizer = None
        self.target_tokenizer = None
        self.train_ds = None
        self.val_ds = None
        self.model = None
        
        logger.info("Initialized Translator System.")

    def _train_word_piece(self, text_samples, vocab_size):
        """
        Trains a WordPiece tokenizer on the provided text samples.
        """
        word_piece_ds = tf.data.Dataset.from_tensor_slices(text_samples)
        tokenizer = keras_hub.tokenizers.WordPieceTokenizer(
            trainable=True, 
            sequence_length=self.sequence_length,
            lowercase=True,
            strip_accents=True
        )
        # Add special tokens
        tokenizer.train(
            word_piece_ds, 
            vocab_size=vocab_size, 
            special_tokens=["[PAD]", "[UNK]", "[START]", "[END]"]
        )
        return tokenizer

    def _preprocess_batch(self, inputs, targets):
        """
        Tokenizes inputs and targets for training.
        Format: (encoder_inputs, decoder_inputs), decoder_outputs
        """
        # Tokenize source (English)
        source_tokens = self.source_tokenizer(inputs)
        
        # Tokenize target (Spanish)
        target_tokens = self.target_tokenizer(targets)
        
        # Decoder Input: [START] ... tokens ... [PAD]
        target_inputs = target_tokens[:, :-1]
        
        # Decoder Output: tokens ... [END] ... [PAD]
        target_labels = target_tokens[:, 1:]
        
        return (source_tokens, target_inputs), target_labels

    def prepare_data(self, source_texts, target_texts, val_split=0.2):
        """
        Trains tokenizers and builds TF Datasets.
        """
        logger.info("Training Source Tokenizer (English)...")
        self.source_tokenizer = self._train_word_piece(source_texts, self.vocab_size)
        
        logger.info("Training Target Tokenizer (Spanish)...")
        self.target_tokenizer = self._train_word_piece(target_texts, self.vocab_size)
        
        # Split Data
        total = len(source_texts)
        val_size = int(total * val_split)
        train_src, val_src = source_texts[:-val_size], source_texts[-val_size:]
        train_tgt, val_tgt = target_texts[:-val_size], target_texts[-val_size:]
        
        logger.info(f"Training on {len(train_src)} samples, Validating on {len(val_src)}.")

        # Build Datasets
        def make_dataset(src, tgt):
            ds = tf.data.Dataset.from_tensor_slices((src, tgt))
            ds = ds.batch(self.batch_size)
            ds = ds.map(self._preprocess_batch, num_parallel_calls=tf.data.AUTOTUNE)
            return ds.prefetch(tf.data.AUTOTUNE)

        self.train_ds = make_dataset(train_src, train_tgt)
        self.val_ds = make_dataset(val_src, val_tgt)

    def build_model(self):
        """
        Constructs the Transformer Encoder-Decoder model using KerasHub layers.
        """
        logger.info("Building Transformer model...")
        
        # 1. Encoder
        encoder_inputs = keras.Input(shape=(None,), dtype="int64", name="encoder_inputs")
        
        # Token + Position Embedding
        x = keras_hub.layers.TokenAndPositionEmbedding(
            vocabulary_size=self.vocab_size,
            sequence_length=self.sequence_length,
            embedding_dim=self.embed_dim,
        )(encoder_inputs)
        
        # Transformer Encoder Block
        encoder_outputs = keras_hub.layers.TransformerEncoder(
            intermediate_dim=self.latent_dim, num_heads=self.num_heads
        )(x)
        
        encoder = keras.Model(encoder_inputs, encoder_outputs)

        # 2. Decoder
        decoder_inputs = keras.Input(shape=(None,), dtype="int64", name="decoder_inputs")
        encoded_seq_inputs = keras.Input(shape=(None, self.embed_dim), name="decoder_state_inputs")
        
        x = keras_hub.layers.TokenAndPositionEmbedding(
            vocabulary_size=self.vocab_size,
            sequence_length=self.sequence_length,
            embedding_dim=self.embed_dim,
        )(decoder_inputs)
        
        x = keras_hub.layers.TransformerDecoder(
            intermediate_dim=self.latent_dim, num_heads=self.num_heads
        )(x, encoded_seq_inputs)
        
        decoder_outputs = layers.Dense(self.vocab_size, activation="softmax")(x)
        
        decoder = keras.Model(
            [decoder_inputs, encoded_seq_inputs], decoder_outputs
        )

        # 3. End-to-End Model
        decoder_outputs = decoder([decoder_inputs, encoder(encoder_inputs)])
        
        self.model = keras.Model(
            [encoder_inputs, decoder_inputs], decoder_outputs, name="transformer_nmt"
        )
        
        self.model.compile(
            optimizer="adam", 
            loss="sparse_categorical_crossentropy", 
            metrics=["accuracy"]
        )
        logger.info("Model built successfully.")

    def train(self):
        """
        Trains the model.
        """
        if not self.model:
            raise ValueError("Model not built.")
        
        logger.info(f"Starting training for {self.num_epochs} epochs...")
        history = self.model.fit(
            self.train_ds,
            epochs=self.num_epochs,
            validation_data=self.val_ds
        )
        return history

    def translate(self, input_sentence):
        """
        Translates a single sentence using Greedy Decoding (simplified for demo).
        """
        # 1. Tokenize Input
        tokenized_input = self.source_tokenizer([input_sentence])
        
        # 2. Prepare Decoder Start
        # Start with [START] token
        decoded_sentence = "[START]"
        tokenized_target = self.target_tokenizer([decoded_sentence])[:, :-1] 

        # 3. Decode Loop
        for i in range(self.sequence_length - 1):
            # Predict next token
            predictions = self.model.predict([tokenized_input, tokenized_target], verbose=0)
            
            # Get last token prediction
            sampled_token_index = np.argmax(predictions[0, i, :])
            
            # Decode back to string to append (inefficient but simple for demo)
            # In production, you'd keep indices and only decode at end
            vocab = self.target_tokenizer.get_vocabulary()
            sampled_token = vocab[sampled_token_index]
            
            if sampled_token == "[END]":
                break
                
            decoded_sentence += " " + sampled_token
            
            # Update target for next step
            tokenized_target = self.target_tokenizer([decoded_sentence])[:, :-1]
            
        clean_translation = decoded_sentence.replace("[START]", "").replace("[END]", "").strip()
        return clean_translation

# --- Data Helper ---

def load_anki_data():
    """
    Downloads and parses the English-Spanish dataset.
    """
    logger.info("Downloading dataset...")
    text_file = keras.utils.get_file(
        fname="spa-eng.zip",
        origin="http://storage.googleapis.com/download.tensorflow.org/data/spa-eng.zip",
        extract=True,
    )
    text_file = os.path.join(os.path.dirname(text_file), "spa-eng/spa.txt")
    
    with open(text_file) as f:
        lines = f.read().split("\n")[:-1]
        
    pairs = [line.split("\t") for line in lines]
    random.shuffle(pairs)
    
    english = [pair[0] for pair in pairs]
    spanish = [pair[1] for pair in pairs]
    return english, spanish


if __name__ == "__main__":
    # 1. Load Data
    eng_texts, spa_texts = load_anki_data()
    
    # Use a small subset for demonstration speed
    eng_subset = eng_texts[:5000]
    spa_subset = spa_texts[:5000]
    
    # 2. Initialize System
    translator = TranslatorSystem(
        batch_size=64,
        num_epochs=5, # Increase for better results
        vocab_size=5000, # Smaller vocab for demo
        sequence_length=20
    )
    
    # 3. Prepare Data
    translator.prepare_data(eng_subset, spa_subset)
    
    # 4. Build Model
    translator.build_model()
    
    # 5. Train
    translator.train()
    
    # 6. Test Translation
    test_sentence = "I love programming"
    translation = translator.translate(test_sentence)
    print(f"\nInput: {test_sentence}")
    print(f"Translation: {translation}")