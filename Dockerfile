FROM python:3.11-slim
#FROM python:3.11
# Or any preferred Python version.
ADD root-CA.crt meteo.py .
RUN pip install python-decouple paho-mqtt
CMD ["python", "./meteo.py"]