"Contains functions that are useful when debugging."

from functools import wraps
from time import perf_counter




def timer(func):
    "Times how long a function takes to execute."
    
    if not DEBUGGING:
        return func
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = perf_counter()
        value = func(*args, *kwargs)
        time_taken = perf_counter() - start_time
        print(f"\033[33m{func.__name__}\033[0m took {time_taken:.4f}s")
        return value
    
    return wrapper





def get_args(func):
    "Prints the arguments passed into a function or method."

    if not DEBUGGING:
        return func
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        print(f"\033[33m{func.__name__}\033[0m({args = }, {kwargs = })")
        return func(*args, **kwargs)
    
    return wrapper



def get_return(func):
    "Prints the return values of a function or method."
    
    if not DEBUGGING:
        return func
    
    @wraps(func)
    def wrapper(*args, **kwargs):
        value = func(*args, **kwargs)

        print(f"\033[33m{func.__name__}\033[0m returned {value}")

        return value

    return wrapper



def log(level: int, message: str) -> None:
    "Outut a logging message to the console."

    if DEBUGGING: # Only show logging messages if in debugging mode
        print(f"{message_styles.get(level, '')}{message}\033[0m")






# The four types of logging messages
STATE_INFO = 10
GAME_INFO = 20
WARNING = 30
CRITICAL = 50



message_styles = { # Sets the style for each type of logging message
    STATE_INFO: "--- \033[36m",
    GAME_INFO: "- \033[32m",
    WARNING: "\033[31mWarning: ",
    CRITICAL: "\033[1m\033[31m"
}


DEBUGGING = False
# Determines weather the game should run in debug mode or not