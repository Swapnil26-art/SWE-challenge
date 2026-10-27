# Energy Utility Wind Power Forecast Application

## Overview
This application helps UK energy utilities evaluate wind power forecast accuracy for day-ahead market planning. It fetches actual wind generation data and forecasts from the Elexon UK electricity market APIs and calculates quantitative accuracy metrics.

## Features
- **Fetch Actual Generation**: Retrieves wind power actuals from Elexon FUELHH dataset
- **Fetch Forecasts**: Retrieves wind power forecasts from Elexon WINDFOR dataset  
- **Accuracy Analysis**: Calculates forecast error metrics including:
  - Average error (MW)
  - Average percentage error
  - Maximum percentage error
- **January 2026 Data**: Filtered data as specified in requirements
- **30-minute Resolution**: Data aligned to 30-minute intervals

## Files and Directories

```
.
├── Dockerfile           # Docker configuration for backend and frontend
├── backend/
│   ├── app.py          # Flask backend API
│   └── requirements.txt # Python dependencies
└── frontend/
    └── react-app/      # React Vite frontend
        ├── index.html
        ├── package.json
        ├── vite.config.js
        ├── index.jsx
        ├── src/
        │   ├── App.jsx     # Main application component
        │   ├── App.css     # Styling
        │   └── main.jsx    # Entry point
        └── public/
```

## How to Start the Application

### Using Docker (recommended)
```bash
docker build -t energy-forecast-app .
docker run -p 5000:5000 energy-forecast-app
```

### Manual Development

#### Backend (Python Flask)
```bash
cd backend
pip install -r requirements.txt
python app.py
```
Backend runs on `http://localhost:5000`

#### Frontend (React)
```bash
cd frontend/react-app
npm install
npm run dev
```
Frontend runs on `http://localhost:5173`

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | Serves the React frontend |
| `GET /api/actuals` | Fetches actual wind generation data from Elexon |
| `GET /api/forecasts` | Fetches wind power forecasts from Elexon |
| `GET /api/accuracy` | Calculates forecast accuracy vs actuals |

## Deployment

### Vercel
This application can be deployed to Vercel. The Python backend uses Flask and the frontend is a React Vite app.

### Heroku
Alternatively, deploy the Python Flask app to Heroku with the React frontend served as static files.

## AI Tools Used
This application was built with assistance from Claude Code, Anthropic's AI coding assistant.

## Video Demo
Please see the unlisted YouTube video for the product demonstration and technical review.

## Submission
Please verify access to the following URLs in incognito mode:
- GitHub Repository: [Repository URL]
- Vercel/Heroku App: [App URL]