# 1. base image
FROM python:3.13-slim

# 2. set working directory
WORKDIR /app

# 3. copy over files
COPY . .

# 4. install requirements
RUN pip install --no-cache-dir -r requirements.txt

# 5. launch app
CMD ["python", "node.py"]
