import os
import re
import numpy as np
import matplotlib.pyplot as plt
import tensorflow as tf
import keras
from keras import layers
from keras import ops
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# --- Custom Layers ---

class TransformerDecoderLayer(layers.Layer):
    def __init__(self, embed_dim, num_heads, ff_dim, rate=0.1, **kwargs):
        super().__init__(**kwargs)
        self.ffn = keras.Sequential(
            [layers.Dense(ff_dim, activation="relu"), layers.Dense(embed_dim)]
        )
        self.layernorm1 = layers.LayerNormalization(epsilon=1e-6)
        self.layernorm2 = layers.LayerNormalization(epsilon=1e-6)
        self.layernorm3 = layers.LayerNormalization(epsilon=1e-6)
        self.self_att = layers.MultiHeadAttention(num_heads=num_heads, key_dim=embed_dim)
        self.enc_dec_att = layers.MultiHeadAttention(num_heads=num_heads, key_dim=embed_dim)
        self.dropout1 = layers.Dropout(rate)
        self.dropout2 = layers.Dropout(rate)

    def call(self, inputs, encoder_outputs, training=False, mask=None):
        out1 = self.self_att(inputs, inputs, attention_mask=mask)
        out1 = self.layernorm1(inputs + out1)
        out2 = self.enc_dec_att(out1, encoder_outputs)
        out2 = self.layernorm2(out1 + out2)
        ffn_out = self.ffn(out2)
        ffn_out = self.dropout1(ffn_out, training=training)
        return self.layernorm3(out2 + ffn_out)


class PositionalEmbedding(layers.Layer):
    def __init__(self, sequence_length, vocab_size, embed_dim, **kwargs):
        super().__init__(**kwargs)
        self.token_embeddings = layers.Embedding(input_dim=vocab_size, output_dim=embed_dim)
        self.position_embeddings = layers.Embedding(input_dim=sequence_length, output_dim=embed_dim)
        self.sequence_length = sequence_length
        self.vocab_size = vocab_size
        self.embed_dim = embed_dim

    def call(self, inputs):
        length = ops.shape(inputs)[-1]
        positions = ops.arange(start=0, stop=length, step=1)
        embedded_tokens = self.token_embeddings(inputs)
        embedded_positions = self.position_embeddings(positions)
        return embedded_tokens + embedded_positions

    def compute_mask(self, inputs, mask=None):
        return ops.not_equal(inputs, 0)


class ImageCaptioningModel(keras.Model):
    def __init__(self, encoder, decoder, num_captions_per_image=5, image_aug=None, **kwargs):
        super().__init__(**kwargs)
        self.encoder = encoder
        self.decoder = decoder
        self.loss_tracker = keras.metrics.Mean(name="loss")
        self.acc_tracker = keras.metrics.Mean(name="accuracy")
        self.num_captions_per_image = num_captions_per_image
        self.image_aug = image_aug

    def calculate_loss(self, y_true, y_pred, mask):
        loss = self.loss(y_true, y_pred)
        mask = ops.cast(mask, dtype=loss.dtype)
        loss *= mask
        return ops.sum(loss) / ops.sum(mask)

    def calculate_accuracy(self, y_true, y_pred, mask):
        accuracy = ops.equal(y_true, ops.argmax(y_pred, axis=2))
        accuracy = ops.logical_and(mask, accuracy)
        accuracy = ops.cast(accuracy, dtype="float32")
        mask = ops.cast(mask, dtype="float32")
        return ops.sum(accuracy) / ops.sum(mask)

    def train_step(self, batch_data):
        batch_img, batch_seq = batch_data
        batch_loss = 0
        batch_acc = 0

        if self.image_aug:
            batch_img = self.image_aug(batch_img)

        with tf.GradientTape() as tape:
            img_features = self.encoder(batch_img)
            for i in range(self.num_captions_per_image):
                inp = batch_seq[:, i, :-1]
                true = batch_seq[:, i, 1:]
                mask = ops.not_equal(inp, 0)
                pred = self.decoder(inp, img_features, training=True, mask=mask)
                batch_loss += self.calculate_loss(true, pred, mask)
                batch_acc += self.calculate_accuracy(true, pred, mask)

            total_loss = batch_loss / self.num_captions_per_image
            total_acc = batch_acc / self.num_captions_per_image

        train_vars = (self.encoder.trainable_variables + self.decoder.trainable_variables)
        gradients = tape.gradient(total_loss, train_vars)
        self.optimizer.apply_gradients(zip(gradients, train_vars))

        self.loss_tracker.update_state(total_loss)
        self.acc_tracker.update_state(total_acc)
        return {"loss": self.loss_tracker.result(), "acc": self.acc_tracker.result()}

    def test_step(self, batch_data):
        batch_img, batch_seq = batch_data
        batch_loss = 0
        batch_acc = 0

        img_features = self.encoder(batch_img)
        for i in range(self.num_captions_per_image):
            inp = batch_seq[:, i, :-1]
            true = batch_seq[:, i, 1:]
            mask = ops.not_equal(inp, 0)
            pred = self.decoder(inp, img_features, training=False, mask=mask)
            batch_loss += self.calculate_loss(true, pred, mask)
            batch_acc += self.calculate_accuracy(true, pred, mask)

        total_loss = batch_loss / self.num_captions_per_image
        total_acc = batch_acc / self.num_captions_per_image

        self.loss_tracker.update_state(total_loss)
        self.acc_tracker.update_state(total_acc)
        return {"loss": self.loss_tracker.result(), "acc": self.acc_tracker.result()}

    @property
    def metrics(self):
        return [self.loss_tracker, self.acc_tracker]


# --- Main Manager Class ---

class ImageCaptioningSystem:
    def __init__(
        self,
        image_size=(299, 299),
        vocab_size=10000,
        seq_length=25,
        embed_dim=128,
        num_heads=2,
        ff_dim=512,
        batch_size=64,
        num_captions_per_image=5
    ):
        self.image_size = image_size
        self.vocab_size = vocab_size
        self.seq_length = seq_length
        self.embed_dim = embed_dim
        self.num_heads = num_heads
        self.ff_dim = ff_dim
        self.batch_size = batch_size
        self.num_captions_per_image = num_captions_per_image
        
        self.vectorization = None
        self.model = None
        self.train_ds = None
        self.val_ds = None
        self.vocab = None
        self.index_lookup = None
        
        logger.info("Initialized Image Captioning System.")

    def _custom_standardization(self, input_string):
        lowercase = tf.strings.lower(input_string)
        return tf.strings.regex_replace(lowercase, "[%s]" % re.escape(r"!\"#$%&'()*+,-./:;<=>?@[\]^_`{|}~"), "")

    def _load_image(self, img_path):
        img = tf.io.read_file(img_path)
        img = tf.io.decode_jpeg(img, channels=3)
        img = tf.image.resize(img, self.image_size)
        return img / 255.0

    def _process_input(self, img_path, captions):
        return self._load_image(img_path), self.vectorization(captions)

    def prepare_data(self, image_paths, captions_list, validation_split=0.2):
        logger.info("Fitting text vectorizer...")
        self.vectorization = layers.TextVectorization(
            max_tokens=self.vocab_size,
            output_mode="int",
            output_sequence_length=self.seq_length,
            standardize=self._custom_standardization,
        )
        flat_captions = [cap for caps in captions_list for cap in caps]
        
        # Adapt on a subset to save time if dataset is huge, otherwise adapt on all
        text_ds = tf.data.Dataset.from_tensor_slices(flat_captions).batch(1024)
        self.vectorization.adapt(text_ds)
        
        self.vocab = self.vectorization.get_vocabulary()
        self.index_lookup = dict(zip(range(len(self.vocab)), self.vocab))
        logger.info(f"Vocab size: {len(self.vocab)}")

        split_idx = int(len(image_paths) * (1 - validation_split))
        train_imgs, val_imgs = image_paths[:split_idx], image_paths[split_idx:]
        train_caps, val_caps = captions_list[:split_idx], captions_list[split_idx:]

        logger.info(f"Training on {len(train_imgs)} images, Validating on {len(val_imgs)} images.")

        def make_dataset(imgs, caps):
            ds = tf.data.Dataset.from_tensor_slices((imgs, caps))
            ds = ds.map(self._process_input, num_parallel_calls=tf.data.AUTOTUNE)
            ds = ds.batch(self.batch_size).prefetch(tf.data.AUTOTUNE)
            return ds

        self.train_ds = make_dataset(train_imgs, train_caps)
        self.val_ds = make_dataset(val_imgs, val_caps)

    def build_model(self):
        logger.info("Building model architecture...")
        
        # Encoder (CNN)
        cnn_base = keras.applications.EfficientNetB0(
            input_shape=(*self.image_size, 3), include_top=False, weights="imagenet"
        )
        cnn_base.trainable = False 
        
        encoder_input = layers.Input(shape=(*self.image_size, 3))
        x = cnn_base(encoder_input) 
        x = layers.Reshape((-1, x.shape[-1]))(x) 
        encoder_output = layers.Dense(self.embed_dim, activation="relu")(x)
        encoder = keras.Model(encoder_input, encoder_output, name="encoder")

        # Decoder (Transformer)
        decoder_input = layers.Input(shape=(self.seq_length,), dtype="int64")
        x = PositionalEmbedding(self.seq_length, self.vocab_size, self.embed_dim)(decoder_input)
        img_features_input = layers.Input(shape=(None, self.embed_dim))
        x = TransformerDecoderLayer(self.embed_dim, self.num_heads, self.ff_dim)(x, img_features_input)
        decoder_output = layers.Dense(self.vocab_size, activation="softmax")(x)
        decoder = keras.Model([decoder_input, img_features_input], decoder_output, name="decoder")

        self.model = ImageCaptioningModel(
            encoder=encoder,
            decoder=decoder,
            num_captions_per_image=self.num_captions_per_image,
            image_aug=self._get_aug_layer()
        )
        
        self.model.compile(optimizer="adam", loss="sparse_categorical_crossentropy")

    def _get_aug_layer(self):
        return keras.Sequential([
            layers.RandomFlip("horizontal"),
            layers.RandomRotation(0.02),
            layers.RandomContrast(0.2),
        ])

    def train(self, epochs=20):
        if not self.model:
            raise ValueError("Model not built.")
        
        early_stopping = keras.callbacks.EarlyStopping(patience=5, restore_best_weights=True)
        
        history = self.model.fit(
            self.train_ds,
            epochs=epochs,
            validation_data=self.val_ds,
            callbacks=[early_stopping]
        )
        return history

    def generate_caption(self, image_path):
        logger.info(f"Generating caption for {image_path}")
        img = self._load_image(image_path)
        img = tf.expand_dims(img, 0)
        img_features = self.model.encoder(img)
        
        decoded_caption = "<start>"
        for i in range(self.seq_length - 1):
            tokenized_caption = self.vectorization([decoded_caption])[:, :-1]
            mask = ops.not_equal(tokenized_caption, 0)
            predictions = self.model.decoder(
                tokenized_caption, img_features, training=False, mask=mask
            )
            sampled_token_index = np.argmax(predictions[0, i, :])
            sampled_token = self.index_lookup[sampled_token_index]
            if sampled_token == "<end>":
                break
            decoded_caption += " " + sampled_token
            
        result = decoded_caption.replace("<start> ", "").replace(" <end>", "").strip()
        return result

# --- Data Loading Helper ---

def download_and_load_flickr8k():
    """
    Downloads Flickr8k dataset and parses the tokens file.
    """
    # 1. Download Data
    if not os.path.exists("Flicker8k_Dataset"):
        logger.info("Downloading Flickr8k Dataset...")
        os.system("wget -q https://github.com/jbrownlee/Datasets/releases/download/Flickr8k/Flickr8k_Dataset.zip")
        os.system("wget -q https://github.com/jbrownlee/Datasets/releases/download/Flickr8k/Flickr8k_text.zip")
        os.system("unzip -qq Flickr8k_Dataset.zip")
        os.system("unzip -qq Flickr8k_text.zip")
        os.system("rm Flickr8k_Dataset.zip Flickr8k_text.zip")
        logger.info("Download complete.")
    else:
        logger.info("Flickr8k Dataset found locally.")

    # 2. Parse Text
    text_file = "Flickr8k.token.txt"
    images_dir = "Flicker8k_Dataset"
    
    logger.info(f"Parsing {text_file}...")
    
    with open(text_file, "r") as f:
        lines = f.readlines()

    captions_mapping = {}
    for line in lines:
        tokens = line.split("\t")
        image_id, caption = tokens[0], tokens[1]
        image_name = image_id.split("#")[0] # Remove caption number (e.g., #0)
        
        # Remove extension from name just in case, or keep it depending on file structure
        # Flickr8k names in token file usually match the filenames in folder
        
        if image_name not in captions_mapping:
            captions_mapping[image_name] = []
        
        # Add start and end tokens
        # Removing punctuation is handled by the TextVectorization layer later
        clean_caption = f"<start> {caption.strip()} <end>"
        captions_mapping[image_name].append(clean_caption)

    # Convert to Lists
    img_paths = []
    captions_list = []
    
    for img_name, caps in captions_mapping.items():
        full_path = os.path.join(images_dir, img_name)
        # Ensure we have exactly 5 captions per image (some have minor errors)
        if len(caps) == 5 and os.path.exists(full_path):
            img_paths.append(full_path)
            captions_list.append(caps)

    return img_paths, captions_list


if __name__ == "__main__":
    # 1. Load Real Data
    img_paths, captions = download_and_load_flickr8k()
    
    # 2. Initialize System
    # Note: Reduced batch size/vocab for demonstration if running on limited hardware
    captioner = ImageCaptioningSystem(
        batch_size=64,
        vocab_size=10000, 
        num_captions_per_image=5,
        seq_length=25
    )
    
    # 3. Prepare Data
    captioner.prepare_data(img_paths, captions)
    
    # 4. Build Model
    captioner.build_model()
    
    # 5. Train
    # Using 10 epochs as a reasonable starting point for Flickr8k
    captioner.train(epochs=10)
    
    # 6. Test on a random validation image
    # Grab a random image from validation set (we split them internally, so let's just pick from the source list)
    test_img = img_paths[-1] 
    generated = captioner.generate_caption(test_img)
    
    print(f"\nTest Image: {test_img}")
    print(f"Generated Caption: {generated}")
    
    # Show the image
    plt.imshow(plt.imread(test_img))
    plt.title(f"Pred: {generated}")
    plt.axis("off")
    plt.show()