import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score



def model_lr(df:pd.DataFrame, target: str, train_start: str, train_end: str, pred_start: str, pred_end: str)->None:
    X_train y_train = df.loc[train_start:train_end].drop(columns=[target]), df.loc[train_start:train_end, [target]]
    X_pred y_pred = df.loc[pred_start:pred_end].drop(columns=[target]), df.loc[pred_start:pred_end, [target]]
    
    model = LinearRegression()
    model.fit(X_train, y_train)
    model = model.predict(X_pred)