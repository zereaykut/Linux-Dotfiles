import numpy as np
import pandas as pd
import tensorflow as tf
import transformers
import keras
from keras import layers
from keras import ops
import logging
import os
import shutil

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

class BertSimilarityClassifier:
    """
    A Transformer-based classifier for Semantic Similarity (NLI).
    Uses a pre-trained BERT model to determine the relationship between two sentences.
    """
    def __init__(
        self,
        model_name="bert-base-uncased",
        max_length=128,
        batch_size=32,
        learning_rate=2e-5,
        epochs=2,
        labels=["contradiction", "entailment", "neutral"]
    ):
        """
        Initialize configuration.
        """
        self.model_name = model_name
        self.max_length = max_length
        self.batch_size = batch_size
        self.learning_rate = learning_rate
        self.epochs = epochs
        self.labels = labels
        self.num_classes = len(labels)
        
        self.tokenizer = transformers.BertTokenizer.from_pretrained(model_name)
        self.model = None
        self.train_data = None
        self.val_data = None
        self.test_data = None
        
        logger.info(f"Initialized BERT Classifier with {model_name}")

    def _bert_encode(self, split_dict):
        """
        Encodes sentence pairs into BERT input format:
        - input_ids: Token indices
        - attention_mask: 1 for tokens, 0 for padding
        - token_type_ids: 0 for Sentence A, 1 for Sentence B
        """
        sentences1 = split_dict['sentence1']
        sentences2 = split_dict['sentence2']
        labels = split_dict['similarity']
        
        # Batch encode allows efficient parallel processing
        encoded = self.tokenizer(
            text=sentences1.tolist(),
            text_pair=sentences2.tolist(),
            add_special_tokens=True,
            max_length=self.max_length,
            return_attention_mask=True,
            return_token_type_ids=True,
            pad_to_max_length=True,
            return_tensors="tf",
            truncation=True
        )
        
        # Convert labels to one-hot encoding
        y = keras.utils.to_categorical(labels, num_classes=self.num_classes)
        
        return {
            'input_ids': encoded['input_ids'],
            'attention_mask': encoded['attention_mask'],
            'token_type_ids': encoded['token_type_ids']
        }, y

    def prepare_data(self, train_df, val_df, test_df):
        """
        Prepares raw dataframes for training.
        Expects dataframes to have columns: 'sentence1', 'sentence2', 'similarity' (int).
        """
        logger.info("Tokenizing and encoding data (this may take a moment)...")
        
        self.train_data = self._bert_encode(train_df)
        self.val_data = self._bert_encode(val_df)
        self.test_data = self._bert_encode(test_df)
        
        logger.info("Data preparation complete.")

    def build_model(self):
        """
        Constructs the Keras model with BERT backbone.
        """
        logger.info("Loading pre-trained BERT model...")
        
        # Inputs defined specifically for BERT
        input_ids = layers.Input(shape=(self.max_length,), dtype=tf.int32, name="input_ids")
        attention_masks = layers.Input(shape=(self.max_length,), dtype=tf.int32, name="attention_mask")
        token_type_ids = layers.Input(shape=(self.max_length,), dtype=tf.int32, name="token_type_ids")

        # Load Hugging Face Model
        bert_model = transformers.TFBertModel.from_pretrained(self.model_name)
        # We can choose to freeze BERT or fine-tune it. 
        # For NLI, fine-tuning (trainable=True) usually yields better results.
        bert_model.trainable = True

        # Forward pass through BERT
        bert_output = bert_model(
            input_ids, attention_mask=attention_masks, token_type_ids=token_type_ids
        )
        
        # Extract sequence output: (batch_size, sequence_length, hidden_size)
        sequence_output = bert_output.last_hidden_state
        
        # Pooling strategy: Average the sequence output
        pooled_output = layers.GlobalAveragePooling1D()(sequence_output)
        
        # Classification Head
        dropout = layers.Dropout(0.2)(pooled_output)
        output = layers.Dense(self.num_classes, activation="softmax")(dropout)

        self.model = keras.Model(
            inputs=[input_ids, attention_masks, token_type_ids], 
            outputs=output
        )

        self.model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=self.learning_rate),
            loss="categorical_crossentropy",
            metrics=["accuracy"],
        )
        logger.info("Model built successfully.")

    def train(self):
        """
        Trains the model.
        """
        if self.model is None:
            raise ValueError("Model not built.")
        if self.train_data is None:
             raise ValueError("Data not prepared.")

        logger.info(f"Starting training for {self.epochs} epochs...")
        
        # Unpack tuple for Keras fit
        x_train, y_train = self.train_data
        x_val, y_val = self.val_data
        
        history = self.model.fit(
            x_train,
            y_train,
            validation_data=(x_val, y_val),
            epochs=self.epochs,
            batch_size=self.batch_size
        )
        return history

    def predict_similarity(self, sentence1, sentence2):
        """
        Inference method for new sentence pairs.
        """
        # Tokenize input
        inputs = self.tokenizer(
            text=[sentence1],
            text_pair=[sentence2],
            add_special_tokens=True,
            max_length=self.max_length,
            return_attention_mask=True,
            return_token_type_ids=True,
            pad_to_max_length=True,
            return_tensors="tf",
            truncation=True
        )
        
        input_dict = {
            'input_ids': inputs['input_ids'],
            'attention_mask': inputs['attention_mask'],
            'token_type_ids': inputs['token_type_ids']
        }
        
        probs = self.model.predict(input_dict, verbose=0)[0]
        pred_idx = np.argmax(probs)
        pred_label = self.labels[pred_idx]
        confidence = probs[pred_idx]
        
        return pred_label, confidence

def load_snli_data():
    """
    Downloads and parses the SNLI dataset.
    Returns Train, Val, and Test DataFrames.
    """
    if not os.path.exists("SNLI_corpus"):
        logger.info("Downloading SNLI Dataset...")
        os.system("curl -LO https://raw.githubusercontent.com/MohamadMerchant/SNLI/master/data.tar.gz")
        os.system("tar -xvzf data.tar.gz")
        os.system("rm data.tar.gz")
    else:
        logger.info("SNLI dataset found locally.")

    # Helper to clean dataframe
    def clean_df(path, subset_name):
        df = pd.read_csv(path)
        # Drop rows with no consensus label ('-')
        df = df[df.similarity != "-"]
        # Map string labels to integers
        label_map = {"contradiction": 0, "entailment": 1, "neutral": 2}
        df["similarity"] = df["similarity"].map(label_map)
        # Convert columns to string to avoid float errors
        df["sentence1"] = df["sentence1"].astype(str)
        df["sentence2"] = df["sentence2"].astype(str)
        logger.info(f"{subset_name} size: {len(df)}")
        return df

    train_df = clean_df("SNLI_corpus/snli_1.0_train.csv", "Train")
    val_df = clean_df("SNLI_corpus/snli_1.0_dev.csv", "Validation")
    test_df = clean_df("SNLI_corpus/snli_1.0_test.csv", "Test")
    
    return train_df, val_df, test_df


if __name__ == "__main__":
    # 1. Load Data
    # Use a sampling strategy (iloc) to speed up this demonstration
    # In production, remove `.iloc[:1000]` to use the full dataset
    train_df, val_df, test_df = load_snli_data()
    
    # Reducing size for demonstration speed
    train_df = train_df.iloc[:2000]
    val_df = val_df.iloc[:500]
    test_df = test_df.iloc[:500]

    # 2. Instantiate Classifier
    classifier = BertSimilarityClassifier(
        model_name="bert-base-uncased",
        max_length=128,
        batch_size=32,
        epochs=2
    )
    
    # 3. Prepare Data
    classifier.prepare_data(train_df, val_df, test_df)
    
    # 4. Build Model
    classifier.build_model()
    
    # 5. Train
    classifier.train()
    
    # 6. Test on custom examples
    logger.info("Running custom predictions...")
    examples = [
        ("Two women are observing something together.", "Two women are standing with their eyes closed."),
        ("A smiling costumed woman is holding an umbrella", "A happy woman in a fairy costume holds an umbrella"),
        ("A soccer game with multiple males playing", "Some men are playing a sport")
    ]
    
    print("\n--- Predictions ---")
    for s1, s2 in examples:
        label, conf = classifier.predict_similarity(s1, s2)
        print(f"S1: {s1}\nS2: {s2}\nPrediction: {label} ({conf:.2%})\n")