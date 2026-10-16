from dotenv import load_dotenv


if __name__ == "__main__":
    load_dotenv() 
    from src.web import create_app   
    app = create_app()
    app.run(debug=True)