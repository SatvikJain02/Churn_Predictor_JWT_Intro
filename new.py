# Command prompt to run inside the treminal:
# uvicorn new:app --reload

from fastapi import FastAPI, HTTPException
import os
import joblib

app = FastAPI(
    title= "Customer Churn Prediction API",
    description= "An API to predict customer churn using machine learning models."
)

@app.get("/") #This is get method and root endpoint
def greet():
    return {'message': 'Whats up'}

# A variable which is defined in all caps, will be constant and will not be changed again.
MODEL_PATH = 'best_balanced_churn_model.pkl'    #This is a constant variable.

if not os.path.exists(MODEL_PATH):
    raise FileNotFoundError(f"Model file not found at {MODEL_PATH}")

model = joblib.load(MODEL_PATH) #Load  the model at startup

# Input Schema (Validation)
# PYDANTIC MODEL

from pydantic import BaseModel, Field, field_validator
from typing import Optional
import pandas as pd

class CustomerData(BaseModel):
    Gender: str = Field(..., example='Male')
    Age: int = Field(...,ge=18, le=100, example = 45)
    Tenure: int = Field(..., ge=0, le=100, example=12)
    Services_Subscribed: int = Field(..., ge=0, le=10, example=3)
    Contract_Type: str = Field(..., example='Month-to-month')
    MonthlyCharges: float = Field(..., gt=0, example=70.5)
    TotalCharges: float = Field(..., ge=0, example=500.5)
    TechSupport: str = Field(..., example='Yes')
    OnlineSecurity: str = Field(..., example='Yes')
    InternetService: str = Field(..., example='Fiber optic')

    @field_validator('Gender')
    @classmethod
    def validate_gender(cls, value):
        allowed = {'Male', 'Female'}
        if value not in allowed:
            raise ValueError(f"Gender must be {allowed}")
        return value
            
    @field_validator('Contract_Type')
    @classmethod
    def validate_contract(cls, value):
        allowed = {'Month-to-month', 'One year', 'Two year'}
        if value not in allowed:
            raise ValueError(f"Contract type must be {allowed}")
        return value

    @field_validator('TechSupport', 'OnlineSecurity')
    @classmethod
    def validate_support_security(cls, value):
        allowed = {'Yes', 'No'}
        if value not in allowed:
            raise ValueError(f"value must be {allowed}")
        return value

    @field_validator('InternetService')
    @classmethod
    def validate_internet(cls, value):
        allowed = {'DSL', 'Fiber optic', 'No'}
        if value not in allowed:
            raise ValueError(f"InternetService must be {allowed}")
        return value

# Output Schema
class PredictionResponse(BaseModel):
    churn_prediction: int
    churn_label: str
    churn_probability: Optional[float]

# Prediction Endpoint
@app.post('/Predict', response_model=PredictionResponse)
def predict(customer:CustomerData):
    try:

        # Convert request to dataframe
        input_df = pd.DataFrame([customer.model_dump()])

        # Model Prediction
        prediction = model.predict(input_df)[0]

        # Probability
        probability = None
        if hasattr(model, 'predict_proba'):
            probability = model.predict_proba(input_df)[0][1] #Probability

        # Churn Label
        return PredictionResponse(
            churn_prediction= prediction,
            churn_label= "Churn" if prediction == 1 else "No Churn",
            churn_probability= probability
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))