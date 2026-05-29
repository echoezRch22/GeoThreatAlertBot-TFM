FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo el contenido del proyecto (incluyendo src/ y data/) al contenedor
COPY . .

# Comando actualizado: Corre main.py apuntando a la estructura de la carpeta src
CMD ["python", "src/main.py"]