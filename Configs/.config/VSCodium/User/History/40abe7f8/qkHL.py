import numpy as np
import pandas as pd
import keras
from keras import layers
from matplotlib import pyplot as plt
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

class AnomalyDetector:
    """
    Detects anomalies in time series data using a Convolutional Autoencoder.
    The model learns the 'normal' pattern and flags deviations as anomalies.
    """
    def __init__(self, time_steps=288, batch_size=128, epochs=50):
        """
        Initialize hyperparameters.
        """
        self.time_steps = time_steps
        self.batch_size = batch_size
        self.epochs = epochs
        
        self.model = None
        self.threshold = None
        self.training_mean = None
        self.training_std = None
        
        logger.info(f"Initialized Anomaly Detector (Window Size={time_steps})")

    def normalize_data(self, df):
        """
        Standardizes data (Mean=0, Std=1).
        Stores stats from the first call (training data) to apply to subsequent data.
        """
        if self.training_mean is None:
            self.training_mean = df.mean()
            self.training_std = df.std()
            logger.info("Computed normalization stats from training data.")
            
        return (df - self.training_mean) / self.training_std

    def create_sequences(self, values):
        """
        Generates sliding window sequences (X) from the time series values.
        Shape: (Samples, TimeSteps, 1)
        """
        output = []
        for i in range(len(values) - self.time_steps):
            output.append(values[i : (i + self.time_steps)])
        return np.stack(output)

    def prepare_data(self, train_df, test_df):
        """
        Normalizes and sequences the raw dataframes.
        """
        logger.info("Normalizing data...")
        # Normalize
        # Note: We use training stats to normalize test data to avoid data leakage
        x_train_norm = self.normalize_data(train_df)
        x_test_norm = self.normalize_data(test_df) # Uses stored mean/std

        logger.info("Creating sequences...")
        # Create sliding windows
        self.x_train = self.create_sequences(x_train_norm.values)
        self.x_test = self.create_sequences(x_test_norm.values)
        
        # Reshape for Conv1D: (Samples, TimeSteps, Features)
        self.x_train = self.x_train.reshape((self.x_train.shape[0], self.x_train.shape[1], 1))
        self.x_test = self.x_test.reshape((self.x_test.shape[0], self.x_test.shape[1], 1))
        
        logger.info(f"Train sequences: {self.x_train.shape}")
        logger.info(f"Test sequences: {self.x_test.shape}")

    def build_model(self):
        """
        Constructs the Convolutional Autoencoder.
        Encoder -> Latent Space -> Decoder
        """
        logger.info("Building Autoencoder architecture...")
        
        model = keras.Sequential(
            [
                layers.Input(shape=(self.x_train.shape[1], self.x_train.shape[2])),
                # Encoder
                layers.Conv1D(filters=32, kernel_size=7, padding="same", strides=2, activation="relu"),
                layers.Dropout(rate=0.2),
                layers.Conv1D(filters=16, kernel_size=7, padding="same", strides=2, activation="relu"),
                # Latent Space (implicitly defined here)
                # Decoder (Upsampling via Conv1DTranspose)
                layers.Conv1DTranspose(filters=16, kernel_size=7, padding="same", strides=2, activation="relu"),
                layers.Dropout(rate=0.2),
                layers.Conv1DTranspose(filters=32, kernel_size=7, padding="same", strides=2, activation="relu"),
                layers.Conv1DTranspose(filters=1, kernel_size=7, padding="same"),
            ]
        )
        
        model.compile(optimizer=keras.optimizers.Adam(learning_rate=0.001), loss="mse")
        self.model = model
        logger.info("Model built successfully.")

    def train(self):
        """
        Trains the autoencoder to reconstruct the normal training data.
        """
        if self.model is None:
            raise ValueError("Model not built. Call build_model() first.")
        
        logger.info(f"Starting training for {self.epochs} epochs...")
        
        # Callback to save best model
        checkpoint = keras.callbacks.ModelCheckpoint(
            "best_model.keras", save_best_only=True, monitor="val_loss", verbose=0
        )
        
        history = self.model.fit(
            self.x_train,
            self.x_train, # Target is same as Input (Reconstruction)
            epochs=self.epochs,
            batch_size=self.batch_size,
            validation_split=0.1,
            callbacks=[keras.callbacks.EarlyStopping(patience=5), checkpoint],
            verbose=1
        )
        return history

    def determine_threshold(self):
        """
        Calculates the anomaly threshold based on training data reconstruction error.
        Threshold = Max MAE on training data.
        """
        logger.info("Calculating reconstruction error on training data...")
        x_train_pred = self.model.predict(self.x_train, verbose=0)
        train_mae_loss = np.mean(np.abs(x_train_pred - self.x_train), axis=1)

        # Set threshold to the max error found in "normal" training data
        self.threshold = np.max(train_mae_loss)
        logger.info(f"Anomaly Threshold set to: {self.threshold:.4f}")
        
        # Plot histogram of training losses
        plt.hist(train_mae_loss, bins=50)
        plt.xlabel("Train MAE loss")
        plt.ylabel("No of samples")
        plt.title("Reconstruction error on Normal Data")
        plt.show()

    def detect_anomalies(self):
        """
        Detects anomalies in the test set using the calculated threshold.
        """
        if self.threshold is None:
            raise ValueError("Threshold not set. Call determine_threshold() first.")
            
        logger.info("Detecting anomalies in test data...")
        x_test_pred = self.model.predict(self.x_test, verbose=0)
        test_mae_loss = np.mean(np.abs(x_test_pred - self.x_test), axis=1)
        test_mae_loss = test_mae_loss.reshape((-1))

        # Check against threshold
        anomalies = test_mae_loss > self.threshold
        
        logger.info(f"Number of anomaly samples found: {np.sum(anomalies)}")
        return anomalies, test_mae_loss

    def plot_anomalies(self, df_test, anomalies):
        """
        Visualizes the original time series with anomalies overlaid in red.
        """
        # Map sequence anomalies back to timestamps
        # Data i is an anomaly if samples [(i - timesteps + 1) to (i)] are anomalies
        # Simpler visualization: just highlight the indices
        
        # We need to slice the dataframe to match sequence length (loss length)
        # Sequence generation consumes `time_steps` samples from start
        subset_test = df_test.iloc[self.time_steps:] 
        
        # Convert boolean mask to indices
        anomaly_indices = []
        for data_idx in range(self.time_steps - 1, len(df_test) - self.time_steps + 1):
            if np.all(anomalies[data_idx - self.time_steps + 1 : data_idx]):
                anomaly_indices.append(data_idx)

        # Let's use a simpler visualization:
        # If a sequence is anomalous, mark the start time of that sequence
        
        # Get raw values and indices
        test_score_df = pd.DataFrame(index=subset_test.index)
        test_score_df['loss'] = self.model.evaluate(self.x_test, self.x_test, verbose=0) # dummy
        test_score_df['threshold'] = self.threshold
        test_score_df['anomaly'] = anomalies
        test_score_df['value'] = subset_test['value']
        
        anomalies_df = test_score_df[test_score_df.anomaly == True]

        plt.figure(figsize=(15, 5))
        plt.plot(test_score_df.index, test_score_df['value'], label='Value')
        plt.scatter(anomalies_df.index, anomalies_df['value'], color='r', label='Anomaly')
        plt.legend()
        plt.title("Detected Anomalies")
        plt.show()

# --- Helper: Data Loader ---

def load_nab_data():
    """
    Downloads Numenta Anomaly Benchmark data.
    """
    logger.info("Downloading NAB dataset...")
    master_url_root = "https://raw.githubusercontent.com/numenta/NAB/master/data/"

    # Normal Data (Training)
    df_small_noise_url = master_url_root + "artificialNoAnomaly/art_daily_small_noise.csv"
    df_small_noise = pd.read_csv(
        df_small_noise_url, parse_dates=True, index_col="timestamp"
    )

    # Anomaly Data (Testing)
    df_daily_jumpsup_url = master_url_root + "artificialWithAnomaly/art_daily_jumpsup.csv"
    df_daily_jumpsup = pd.read_csv(
        df_daily_jumpsup_url, parse_dates=True, index_col="timestamp"
    )
    
    return df_small_noise, df_daily_jumpsup


if __name__ == "__main__":
    # 1. Load Data
    df_train, df_test = load_nab_data()
    
    # 2. Instantiate Detector
    detector = AnomalyDetector(
        time_steps=288,  # 288 samples = 24 hours (given 5-min intervals)
        epochs=50,
        batch_size=128
    )
    
    # 3. Prepare Data
    detector.prepare_data(df_train, df_test)
    
    # 4. Build Model
    detector.build_model()
    
    # 5. Train
    detector.train()
    
    # 6. Set Threshold
    detector.determine_threshold()
    
    # 7. Detect
    anomalies, loss = detector.detect_anomalies()
    
    # 8. Visualize
    detector.plot_anomalies(df_test, anomalies)