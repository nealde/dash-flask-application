from application import init_app


app = init_app()

if __name__ == "__main__":\
    # uvicorn.run("wsgi:app", host='127.0.0.1', port=5000, workers=4, reload=True)
    app.run()