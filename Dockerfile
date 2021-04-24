FROM python:3.6

COPY . .

RUN pip install --upgrade pipenv
RUN pipenv install

CMD ["pipenv", "run", "gunicorn", "--bind", ":8000", "--workers", "3", "wsgi:app" ]