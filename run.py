# run.py
from app import create_app

app = create_app()

if __name__ == '__main__':
    # debug=True не использовать в production!
    app.run(debug=True)