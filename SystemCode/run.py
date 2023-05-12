from frontend import app
<<<<<<< HEAD
from threading import Timer
import os
import webbrowser
    # some_file.py
from frontend import routes

def open_browser():
    if not os.environ.get("WERKZEUG_RUN_MAIN"):
        webbrowser.open_new('http://localhost:3000')

if __name__ == '__main__':
    Timer(1, open_browser).start();
  
    app.run(debug=True, host='0.0.0.0', port=3000)
 

    
=======

if __name__=="__main__":
    app.run(debug=True)
>>>>>>> 6c0e89db97f4816598271558c6e63692985f1fae
