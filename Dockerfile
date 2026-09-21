FROM python:3.12-slim
WORKDIR /app
RUN pip install --no-cache-dir openpyxl pypdf python-docx python-pptx
COPY app.zip .
RUN python -c "import zipfile; zipfile.ZipFile('app.zip').extractall('.')" \
 && test -f core/appraisal.py && test -f core/committee.py && test -f ui/index.html && test -f ui/v05.js && test -f core/deck.py && test -f web.py
ENV MINERVA_HOME=/data PYTHONUNBUFFERED=1
EXPOSE 8080
CMD ["python", "web.py"]
