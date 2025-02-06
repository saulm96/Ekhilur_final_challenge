FROM python:3.9 

# Establecer el directorio de trabajo dentro del contenedor
WORKDIR ./app
 
# Copiar primero el archivo de dependencias para aprovechar mejor la caché de Docker 
COPY requirements.txt .

# Instalar las dependencias antes de copiar el resto de los archivos 
RUN pip install --no-cache-dir -r requirements.txt 

# Copiar el resto de los archivos de la API al contenedor 
COPY . .

# Exponer el puerto en el que correrá Flask 
EXPOSE 5000 

# Comando para ejecutar la API 
CMD ["python", "app.py"]
