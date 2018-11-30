# NYC Job Search Web-app
Designed by Chenyu Xi and Zhihan Bu<br/>
See Origin: https://github.com/Daniel-Bu/w4111-project1/tree/master/Web-app
**No Security method enabled for this login system**
## Environment
- Python 2.7
- Packages:  
```
pip install flask psycopg2 sqlalchemy click flask-login
```
## Other issues:
Some part of the Server.py haven't add SQL injection

## Files
- Server.py: Run to start the Server
- Database.py: Create Database engine
- User: Define user class, used for Flask-login (No ORM)
- happy: virtualenv happy for server
- templates: html
- static: css theme
