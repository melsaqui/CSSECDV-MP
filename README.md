Authors:
- Aquino, Melanie
- Campol, Russel

How to run the program:
1. Create database using the schema in `db_setup.sql` file found in the `sql` folder
2. Make .env file detailing the configurations of the database
3. Input in your console `cd web_app`
4. Install dependencies by entering `pip install -r requirements.txt` in console
5. Enter `flask --app app.py run` in console to run with debug turned off
6. To enter debug mode enter `flask --app app.py run --debug` in console
7. Alternately, you can enter `python app.py` to follow the debug mode in the config.py file