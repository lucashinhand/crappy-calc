FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

ENV STREAMLIT_ENTRYPOINT="calc.py"

CMD streamlit run ${STREAMLIT_ENTRYPOINT} --server.port=8501 --server.address=0.0.0.0
