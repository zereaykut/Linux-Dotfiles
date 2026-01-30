import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import os

output_folder = "out"
os.makedirs(output_folder, exist_ok=True)


def model_lr(df:pd.DataFrame, target: str, train_start: str, train_end: str, pred_start: str, pred_end: str, test: bool = None)->None:
    X_train y_train = df.loc[train_start:train_end].drop(columns=[target]), df.loc[train_start:train_end, [target]]
    X_pred y_pred = df.loc[pred_start:pred_end].drop(columns=[target]), df.loc[pred_start:pred_end, [target]]
    
    model = LinearRegression()
    model.fit(X_train, y_train)
    pred = model.predict(X_pred)
    y_pred["Prediction"] = pred.squeeze()

    y_pred.to_csv("out/model_lr_prediction.csv", index=True)

    if test:
        mse = mean_squared_error(y_pred[target], y_pred["Prediction"])
        rmse = np.sqrt(mse)
        r2 = r2_score(y_pred[target], y_pred["Prediction"])

        mse = round(mse, 4)
        rmse = round(rmse, 4)
        r2 = round(r2, 4)




def model_lr(df:pd.DataFrame, target: str, train_start: str, train_end: str, pred_start: str, pred_end: str)->None:
    X_train y_train = df.loc[train_start:train_end].drop(columns=[target]), df.loc[train_start:train_end, [target]]
    X_pred y_pred = df.loc[pred_start:pred_end].drop(columns=[target]), df.loc[pred_start:pred_end, [target]]
    
    model = LinearRegression()
    model.fit(X_train, y_train)
    pred = model.predict(X_pred)
    y_pred["Prediction"] = pred.squeeze()

    y_pred.to_csv("out/model_lr_prediction.csv", index=True)

    