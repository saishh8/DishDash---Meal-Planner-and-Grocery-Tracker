#Dockerfile
FROM python:3.11-slim

#set workdir
WORKDIR /app

#copy requirements
COPY requirements.txt .

#install dependencies
RUN pip install --no-cache-dir -r requirements.txt

#copy app code
COPY . .


#expose port
EXPOSE 8000

#command to run FastAPI app

CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","8000","--reload"]