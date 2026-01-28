# JWT Authentication:
from new import app, CustomerData, PredictionResponse, predict
from fastapi.security import HTTPBearer

# Configuraton:
SECRET_KEY = 'Sample_key' #Will be changed in production.
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 38

# Security Scheme:
security = HTTPBearer()

from pydantic import BaseModel
# User Authentication Model:
class UserRegister(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str #Bearer
    expires_in: int

fake_users_db = {
    "admin":{
        'username': 'admin',
        'password': '0202',
        'disabled': False
    },
    "User1":{
        'username': 'User1',
        'password': 'user1pass',
        'disabled': False
    }
}

from datetime import datetime, timedelta
from typing import Optional
# JWT Access Token:
# expires_delta means token expiration time.
def create_access_token(data:dict, expires_delta:Optional[timedelta]=None):
    # 1. We will create copy of data dictionary to avoid mutation.
    to_encode = data.copy()

    # 2. We will check if expires_delta is provided otherwise, we will make default expiration time.
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else: #Creating default expire time:
        expire = datetime.utcnow() + timedelta(minutes=15)

    # 3. Data -> expiration time add karenge.
    to_encode.update({'exp':expire})

    # 4. encode copy data, secret key, algorithm.
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    # 5. return encoded token
    return encoded_jwt

import jwt
from fastapi import HTTPException
def verify_token(token:str):
    payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    username: str = payload.get('sub')
    if username is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    return username

def authenticate_user(username:str, password:str):
    user = fake_users_db.get(username)
    if not user or user['password'] != password:
        return None
    return user

# 1. Endpoint for user register
@app.post('/register', response_model=TokenResponse)
async def register_user(user:UserRegister):
    if user.username in fake_users_db:
        raise HTTPException(status_code=400, detail='Username already exists')
    
    # Register user
    fake_users_db[user.username] = {
        'username': user.username,
        'password': user.password,
        'disabled': False
    }

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={'sub':user.username}, expires_delta=access_token_expires)

    return{
        'access_token': access_token,
        'token_type': 'Bearer',
        'expires_in': ACCESS_TOKEN_EXPIRE_MINUTES * 60 # In seconds
    }

# 2. Endpoint for user login:
@app.post('/login', response_model=TokenResponse)
async def login_user(user: UserRegister):
    # 1. Verify if the user exists and password matches
    # We use the helper function 'authenticate_user' defined earlier.
    auth_user = authenticate_user(user.username, user.password)
    
    # 2. If authentication fails, throw a 401 (Unauthorized) error
    if not auth_user:
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    # 3. Define the token expiration time
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    # 4. Create the JWT token using the helper function
    # 'sub' (subject) is a standard JWT claim for the username.
    access_token = create_access_token(data={'sub': user.username}, expires_delta=access_token_expires)

    # 5. Return the token in the response model format
    return {
        "access_token": access_token,
        "token_type": "Bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }

from fastapi import Depends

class AuthenticatePredictionRequest(BaseModel):
    customer: CustomerData

# 3. Prediction Endpoint with JWT Authentication:

# a. post endpoint
@app.post('/predict/auth', response_model=PredictionResponse, dependencies=[Depends(security)])
# Depends extracts the authorization header, checks the formate of Bearer token

# b. response model
async def predict_auth(request:AuthenticatePredictionRequest, credentials=Depends(security)):

# c. verify token
    username = verify_token(credentials.credentials)

# d. log the authorised access
    print(f"User {username} accessed the prediction endpoint")

# e. Call the original prediction function which is in new.py file
    return predict(request.customer)    # We are extracting the customer data from the function.

# =================================================================================================

# # 2. Endpoint for user login:
# @app.post('/login', response_model=TokenResponse)
# async def login_user(user: UserRegister):

#     if authenticate_user(user.username, user.password) is None:
#         raise HTTPException()