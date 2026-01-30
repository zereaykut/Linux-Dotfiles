import os
import logging
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import keras
from keras import layers

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

class WeatherForecaster:
    """
    A LSTM-based model for Time Series Forecasting.
    """
    def __init__(
        self,
        input_shape,
        output_units=1,
        lstm_units=32,
        batch_size=256,
        epochs=10,
        learning_rate=0.001
    ):
        """
        Initialize configuration.
        """
        self.input_shape = input_shape
        self.output_units = output_units
        self.lstm_units = lstm_units
        self.batch_size = batch_size
        self.epochs = epochs
        self.learning_rate = learning_rate
        
        self.model = None
        self.callbacks = []
        
        logger.info(f"Initialized Forecaster for input {input_shape}")

    def build_model(self):
        """
        Constructs the LSTM architecture.
        Structure: Input -> LSTM -> Dense (Output)
        """
        logger.info("Building model architecture...")
        inputs = keras.Input(shape=self.input_shape)
        
        # LSTM Layer
        # returns sequence only if needed, here we just want the last output
        x = layers.LSTM(self.lstm_units)(inputs)
        
        # Output Layer
        outputs = layers.Dense(self.output_units)(x)

        self.model = keras.Model(inputs=inputs, outputs=outputs)
        
        self.model.compile(
            optimizer=keras.optimizers.Adam(learning_rate=self.learning_rate),
            loss="mse" # Mean Squared Error for regression
        )
        
        # Setup Callbacks
        self.callbacks = [
            keras.callbacks.ModelCheckpoint(
                "best_model.keras", save_best_only=True, monitor="val_loss"
            ),
            keras.callbacks.EarlyStopping(monitor="val_loss", patience=5, verbose=1),
        ]
        
        logger.info("Model built successfully.")

    def train(self, dataset_train, dataset_val):
        """
        Trains the model.
        Expects tf.data.Dataset objects.
        """
        if self.model is None:
            raise ValueError("Model not built. Call build_model() first.")
        
        logger.info(f"Starting training for {self.epochs} epochs...")
        history = self.model.fit(
            dataset_train,
            epochs=self.epochs,
            validation_data=dataset_val,
            callbacks=self.callbacks,
            verbose=1,
        )
        return history

    def evaluate(self, dataset_test):
        """
        Evaluates the model (loads best checkpoint first).
        """
        logger.info("Loading best model checkpoint...")
        self.model = keras.models.load_model("best_model.keras")
        
        logger.info("Evaluating on test set...")
        loss = self.model.evaluate(dataset_test)
        logger.info(f"Test Loss (MSE): {loss:.4f}")
        return loss

    def predict(self, dataset_test):
        """
        Runs prediction on test set.
        """
        return self.model.predict(dataset_test)

    def plot_prediction(self, inputs, labels):
        """
        Visualizes a single prediction sample.
        """
        # Take one batch
        for x, y in inputs.take(1):
            pred = self.model.predict(x)[0]
            truth = y[0]
            
            plt.figure(figsize=(10, 6))
            plt.plot(x[0, :, 1], label="History (Temp)") # Assuming Temp is index 1
            plt.plot(len(x[0]), truth, "rx", label="True Future")
            plt.plot(len(x[0]), pred, "go", label="Predicted Future")
            plt.legend()
            plt.title("Single Step Prediction")
            plt.show()
            break


# --- Data Helper ---

def normalize_data(df, train_split_idx):
    """
    Standardizes dataframe based on training statistics.
    """
    train_data = df.iloc[:train_split_idx]
    mean = train_data.mean(axis=0)
    std = train_data.std(axis=0)
    return (df - mean) / std

def create_dataset_from_dataframe(
    df, 
    split_train=0.7, 
    split_val=0.2, 
    sequence_length=720, 
    future_target=72, 
    batch_size=256,
    step=6
):
    """
    Parses dataframe into tf.data.Datasets for Train, Val, and Test.
    """
    logger.info("Processing Dataframe...")
    
    # 1. Feature Selection (Specific to Jena Climate dataset)
    # Selecting specific columns helps reduce noise
    features = ['p (mbar)', 'T (degC)', 'Tpot (K)', 'Tdew (degC)', 'rh (%)',
                'VPmax (mbar)', 'VPact (mbar)', 'VPdef (mbar)', 'sh (g/kg)',
                'H2OC (mmol/mol)', 'rho (g/m**3)', 'wv (m/s)', 'max. wv (m/s)',
                'wd (deg)']
    
    # Check if columns exist (generic fallback)
    features = [c for c in features if c in df.columns]
    if not features:
        features = df.columns # Use all if specific ones not found
        
    df = df[features]
    
    # 2. Split Indices
    n = len(df)
    train_split = int(n * split_train)
    val_split = int(n * (split_train + split_val))
    
    # 3. Normalize
    df_norm = normalize_data(df, train_split)
    data = df_norm.values
    
    # 4. Create Datasets using keras.utils.timeseries_dataset_from_array
    # This utility efficiently creates sliding windows
    
    def make_ds(start_index, end_index):
        # We sample every `step` (e.g., every hour instead of every 10 mins)
        # Target is `future_target` steps ahead
        return keras.utils.timeseries_dataset_from_array(
            data=data[:-future_target],
            targets=data[future_target:, 1], # Index 1 is Temperature
            sequence_length=sequence_length,
            sequence_stride=1,
            sampling_rate=step,
            batch_size=batch_size,
            start_index=start_index,
            end_index=end_index,
            shuffle=True if start_index == 0 else False # Shuffle only train
        )
    
    train_ds = make_ds(0, train_split)
    val_ds = make_ds(train_split, val_split)
    test_ds = make_ds(val_split, None)
    
    logger.info(f"Datasets created. Features: {data.shape[1]}")
    return train_ds, val_ds, test_ds, data.shape[1]

def load_jena_climate_data():
    """
    Downloads Jena Climate dataset.
    """
    logger.info("Downloading dataset...")
    zip_path = keras.utils.get_file(
        origin="https://storage.googleapis.com/tensorflow/tf-keras-datasets/jena_climate_2009_2016.csv.zip",
        fname="jena_climate_2009_2016.csv.zip",
        extract=True,
    )
    csv_path, _ = os.path.splitext(zip_path)
    df = pd.read_csv(csv_path)
    return df


if __name__ == "__main__":
    # 1. Load Raw Data
    df = load_jena_climate_data()
    
    # Subsample for demonstration (take every 6th record = 1 hour)
    # df = df[5::6] 
    
    # 2. Prepare TF Datasets
    # sequence_length=120 -> Past 120 observations
    # step=6 -> Sample once per hour (original data is 10 mins)
    # future_target=72 -> Predict 12 hours into future (72 * 10 mins)
    train_ds, val_ds, test_ds, num_features = create_dataset_from_dataframe(
        df, 
        sequence_length=120, 
        step=6
    )
    
    # 3. Instantiate Forecaster
    forecaster = WeatherForecaster(
        input_shape=(120, num_features), # (TimeSteps, Features)
        lstm_units=32,
        batch_size=256,
        epochs=10
    )
    
    # 4. Build Model
    forecaster.build_model()
    
    # 5. Train
    history = forecaster.train(train_ds, val_ds)
    
    # 6. Evaluate
    forecaster.evaluate(test_ds)
    
    # 7. Visualize Result
    forecaster.plot_prediction(test_ds, None)
    
    # 8. Plot Training History
    plt.plot(history.history['loss'], label='train')
    plt.plot(history.history['val_loss'], label='validation')
    plt.legend()
    plt.show()