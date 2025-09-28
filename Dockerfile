# Usa una imagen base oficial de Python
FROM python:3.11-slim

# Establece el directorio de trabajo dentro del contenedor
WORKDIR /app

# Copia los archivos de dependencia y luego instala las dependencias
# Esto optimiza el caché de Docker: si app.py cambia, no reinstala las dependencias.
# Crea un archivo requirements.txt con las dependencias de tu proyecto.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el resto de la aplicación (en este caso, solo app.py)
COPY app.py .

# Streamlit por defecto se ejecuta en el puerto 8501.
# Cloud Run requiere que el contenedor escuche en el puerto definido por la variable de entorno $PORT (que suele ser 8080).
# Es crucial pasar la opción --server.port $PORT a Streamlit.
# Define el comando para ejecutar la aplicación Streamlit
CMD ["streamlit", "run", "app.py", "--server.port", "8080", "--server.address", "0.0.0.0"]

# Opcional: Documenta el puerto en el que la aplicación escucha, aunque Cloud Run usa $PORT.
EXPOSE 8080