FROM python:3.11-slim as backend

WORKDIR /app/backend

COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

EXPOSE 5000

CMD ["python", "app.py"]

FROM node:18-alpine as frontend

WORKDIR /app/frontend/react-app

COPY frontend/react-app/package.json frontend/react-app/package-lock.json ./
RUN npm install

COPY frontend/react-app/ .
RUN npm run build

FROM python:3.11-slim

WORKDIR /app

COPY --from=frontend /app/frontend/react-app/dist ./frontend/dist

COPY backend/ .

EXPOSE 5000

CMD ["python", "app.py"]