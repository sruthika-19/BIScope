# BIScope
BIScope — An AI-powered intelligent assistant for Indian Standards and BIS services, helping industries and consumers discover relevant standards, requirements, terminology, evidence, and certification information

## Run locally

Start the existing FastAPI service from `backend/`:

```powershell
cd backend
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload
```

In a second terminal, start the frontend:

```powershell
cd frontend
npm install
npm run dev
```

The frontend uses `http://localhost:8000` for the API by default. Set `VITE_API_BASE` in a frontend `.env` file to use a different API origin.

The frontend includes Home, Explore, Check Requirements, Review Evidence, and Services views. Browser-native voice input requires a supported browser and microphone permission.
