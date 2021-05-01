"""Calling this module will start the application.

Will import app (__init.py__) and call app.run,therefore kicking 
off the application. Be aware args dictate how Flask operates. 
In debug mode and additional instance is started to aide in 
debugging but this can lead to unexpected side-effects such as 
duplicate product checking thread.

Optional Args:
    debug (bool): False for production.
    use_reloader: Automatic reload of html upon code change and save.
    
Example:
    python run.py
"""

from productchecker import app

if __name__ == '__main__':
    app.run(debug=False, use_reloader=False)
