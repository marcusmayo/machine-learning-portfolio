# 🚴 Bike Rental Prediction - MLOps Pipeline

A complete end-to-end MLOps pipeline for predicting bike rental demand using machine learning, deployed on AWS with automated CI/CD through GitHub Actions.

Based on article from https://medium.com/analytics-vidhya/neural-network-to-predict-bike-sharing-rides-397e0358ba45

Vibe coded with Claude and ChatGPT

## 📊 Overview

This project implements a production-ready machine learning system that predicts hourly bike rental demand based on weather conditions, temporal features, and seasonal patterns. The model is deployed as a REST API on AWS EC2 and features automated testing, containerization, and continuous deployment.

## 🎯 What This Prediction Provides

The API predicts **hourly bike rental counts** - the number of bikes that will be rented in a given hour based on:
- Current weather conditions (temperature, humidity, wind speed)
- Temporal factors (hour of day, day of week, month, season)
- Calendar features (holiday, working day)
- Weather situation (clear, cloudy, rain, snow)

The prediction output is a normalized value that represents the expected bike rental demand, which can be used for:
- Inventory management and bike redistribution
- Staffing optimization
- Demand forecasting for business planning
- Dynamic pricing strategies

## 🔢 Feature Engineering & Requirements

### Input Features (53 Total)
The model requires exactly **53 preprocessed features** derived from the original bike-sharing dataset:

```python
# Original Raw Features:
- instant: Record index
- dteday: Date
- season: Season (1:spring, 2:summer, 3:fall, 4:winter)
- yr: Year (0: 2011, 1: 2012)
- mnth: Month (1 to 12)
- hr: Hour (0 to 23)
- holiday: Whether day is holiday or not
- weekday: Day of the week
- workingday: If day is neither weekend nor holiday
- weathersit: Weather situation (1-4 scale)
- temp: Normalized temperature in Celsius
- atemp: Normalized feeling temperature
- hum: Normalized humidity
- windspeed: Normalized wind speed
- casual: Count of casual users
- registered: Count of registered users
- cnt: Total count of rental bikes (target variable)
```

**Feature Transformation Process:**
- **Temporal Encoding**: Hour, day, month are one-hot encoded
- **Categorical Encoding**: Season and weather situation are encoded
- **Normalization**: All numerical features scaled between 0-1
- **Feature Expansion**: Creates 53 features through encoding and engineering

## 🏗️ Architecture

```
┌─────────────────┐     ┌──────────────┐     ┌─────────────┐
│  GitHub Repo    │────▶│ GitHub       │────▶│    AWS      │
│  (Source Code)  │     │ Actions      │     │    ECR      │
└─────────────────┘     │ (CI/CD)      │     └─────────────┘
                        └──────────────┘              │
                               │                      ▼
                               │              ┌─────────────┐
                               └─────────────▶│   AWS EC2   │
                                              │  (Docker)   │
                                              │  Port 80    │
                                              └─────────────┘
```

## 🚀 CI/CD Pipeline

**Automated Workflow:**
1. **Test** - Runs `ci_test.py` to validate code
2. **Build** - Creates Docker image
3. **Push** - Uploads to Amazon ECR
4. **Deploy** - Updates EC2 instance
5. **Integration Tests** - Validates deployed API

**Key Files:**
- `.github/workflows/main.yml` - CI/CD pipeline configuration
- `ci_test.py` - Basic CI tests
- `Dockerfile` - Container definition
- `requirements.txt` - Python dependencies

## 🔧 Technology Stack

### Why Flask Instead of MLflow:
We chose Flask over MLflow for model serving due to:
- **Permission Issues**: MLflow attempts to write to system paths (`/home/ubuntu`) causing permission denied errors in restricted environments like GitHub Actions runners
- **Simplicity**: Flask provides a lightweight, straightforward API server
- **Control**: Direct control over endpoints and error handling
- **Compatibility**: Works seamlessly in containerized environments without special permissions
- **Flexibility**: Easy to customize responses and add middleware

**Core Technologies:**
- **Model Training**: PyTorch
- **API Framework**: Flask
- **Containerization**: Docker
- **Cloud Platform**: AWS (EC2, ECR)
- **CI/CD**: GitHub Actions
- **Data Processing**: NumPy, Pandas, Scikit-learn

## 📡 API Endpoints

### 1. Root Endpoint
```bash
GET /
```
Returns API information and available endpoints

### 2. Health Check
```bash
GET /health
```
Returns: `{"status": "healthy"}`

### 3. Prediction
```bash
POST /predict
Content-Type: application/json

{
  "features": [0.1, 0.2, ..., 0.53]  # Array of 53 float values
}
```
Returns: `{"prediction": 0.456, "status": "success"}`

## 🌐 Different Ways to Access the API

### 1. Command Line (cURL)
```bash
# Health check
curl http://18.233.252.250/health

# Make prediction
curl -X POST http://18.233.252.250/predict \
  -H "Content-Type: application/json" \
  -d '{"features": [0.1, 0.2, 0.3, ..., 0.53]}'
```

### 2. Python
```python
import requests
import json

url = "http://18.233.252.250/predict"
data = {"features": [0.1] * 53}  # 53 features
response = requests.post(url, json=data)
print(response.json())
```

### 3. JavaScript/Node.js
```javascript
fetch('http://18.233.252.250/predict', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({features: Array(53).fill(0.1)})
})
.then(response => response.json())
.then(data => console.log(data));
```

### 4. Postman/Insomnia
- **Method**: POST
- **URL**: `http://18.233.252.250/predict`
- **Headers**: `Content-Type: application/json`
- **Body**: Raw JSON with 53 features

### 5. Web Application Integration
```html
<!-- HTML Form Example -->
<script>
async function predict() {
    const features = Array(53).fill(0.1); // Generate from form inputs
    const response = await fetch('http://18.233.252.250/predict', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({features})
    });
    const result = await response.json();
    console.log('Prediction:', result.prediction);
}
</script>
```

## 🧪 Testing

### Running CI Tests Locally:
```bash
python3 ci_test.py
```

The `ci_test.py` file performs basic validation:
- Environment setup verification
- Import checks
- Basic functionality tests

### Integration Testing:
Integration tests automatically run after deployment to verify:
- API accessibility
- Endpoint functionality
- Response format validation

## 🚀 Deployment

**Current Deployment:**
- **URL**: `http://18.233.252.250`
- **Platform**: AWS EC2 t2.large instance
- **Container**: Docker running Flask application
- **Port**: 80 (mapped to container port 1234)

### Manual Deployment:
```bash
# SSH to EC2
ssh -i your-key.pem ubuntu@18.233.252.250

# Pull latest image
docker pull 453553127570.dkr.ecr.us-east-1.amazonaws.com/bike-rental-prediction:latest

# Restart container
docker stop bike-rental-api
docker rm bike-rental-api
docker run -d --name bike-rental-api -p 80:1234 --restart unless-stopped \
  453553127570.dkr.ecr.us-east-1.amazonaws.com/bike-rental-prediction:latest
```

## 📁 Project Structure

```
bike_rental_prediction_fully_automated/
├── .github/
│   └── workflows/
│       └── main.yml          # CI/CD pipeline
├── bike_rental_prediction/
│   ├── src/
│   │   ├── train.py          # Model training
│   │   └── preprocess.py     # Data preprocessing
│   ├── app/
│   │   └── serve.py          # Flask API server
│   ├── data/
│   │   └── hour.csv          # Training data
│   ├── models/
│   │   └── .gitkeep
│   ├── Dockerfile            # Container definition
│   ├── requirements.txt      # Python dependencies
│   ├── ci_test.py           # CI tests
│   └── README.md            # This file
```

## 🔐 Environment Variables & Secrets

**Required GitHub Secrets:**
- `AWS_ACCESS_KEY_ID` - AWS credentials
- `AWS_SECRET_ACCESS_KEY` - AWS credentials
- `ECR_REGISTRY` - ECR repository URL
- `EC2_HOST` - EC2 instance IP
- `EC2_USER` - SSH username (ubuntu)
- `EC2_PRIVATE_KEY` - SSH private key

## 📈 Performance Metrics

- **Model Type**: Neural Network (PyTorch)
- **Architecture**: 3-layer feedforward network (53→64→32→1)
- **Training Time**: ~2 minutes for 100 epochs
- **Inference Time**: <50ms per prediction
- **API Response Time**: <100ms total

## 🛠️ Troubleshooting

### Common Issues:

**Permission Denied Errors:**
- **Solution**: Using Flask instead of MLflow
- All artifacts saved to `./runs/` directory

**GitHub Actions Failures:**
- Check GitHub Secrets are properly set
- Verify EC2 security group allows port 80

**Docker Container Issues:**
- Ensure ECR login is successful
- Check container logs: `docker logs bike-rental-api`

## 📚 Data Source

Original dataset from UCI Machine Learning Repository:
- **Dataset**: Bike Sharing Dataset
- **Records**: 17,379 hourly records
- **Period**: 2011-2012
- **Location**: Washington D.C., USA

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/NewFeature`)
3. Commit changes (`git commit -m 'Add NewFeature'`)
4. Push to branch (`git push origin feature/NewFeature`)
5. Open Pull Request

## 📄 License

This project is part of a machine learning portfolio for educational purposes.

## 👤 Author

**Marcus Mayo**
- GitHub: @marcusmayo
- Repository: machine-learning-portfolio

## 🎯 Future Improvements

- [ ] Add model versioning
- [ ] Implement A/B testing
- [ ] Add monitoring and logging
- [ ] Create web interface
- [ ] Add batch prediction endpoint
- [ ] Implement model retraining pipeline
- [ ] Add data drift detection

---

**API Status**: ✅ Operational
