FROM python:3.11-slim
WORKDIR /app
COPY server_threaded.py /app/server_threaded.py
COPY server_threaded_lock.py /app/server_threaded_lock.py
COPY content /app/content
ENV VARIANT=server_threaded.py
EXPOSE 8080
# Choose variant by env VARIANT (server_threaded.py or server_threaded_lock.py)
CMD ["sh", "-c", "python ${VARIANT}"]
