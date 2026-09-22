FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
RUN test -f core/appraisal.py -a -f ui/index.html -a -f ui/v08.js -a -f ui/v09.js -a -f ui/v10.js -a -f ui/v11.js -a -f core/tax.py -a -f core/levies.py -a -f core/costplan.py -a -f core/listings.py -a -f core/sketch.py -a -f core/programme.py -a -f core/funding.py -a -f core/compset.py -a -f core/strategy.py -a -f core/history.py -a -f core/packs.py -a -f core/requirements.py -a -f API_REQUIREMENTS.md -a -f core/ppdfile.py -a -f ui/geomap.js -a -f core/layout.py -a -f core/screen.py || (echo "The core or ui folder is missing from the repository. Upload it to GitHub and redeploy." && exit 1)
ENV MINERVA_HOME=/data PYTHONUNBUFFERED=1
EXPOSE 8080
CMD ["python", "web.py"]
