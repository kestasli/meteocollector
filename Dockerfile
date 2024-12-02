FROM python:3.14-rc-slim-bookworm
ADD root-CA.crt meteo.py .
RUN pip install python-decouple paho-mqtt
CMD ["python", "./meteo.py"]
