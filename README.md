# Syringe Pump Program - Feeding Module
This repository holds python code for and anything related to the syringe pump program 
that is part of a larger program that controls the microfluidic nanoparticle production system. 
The paper describing the system can be found here: 
Loy, D.M.; Krzysztoń, R.; Lächelt, U.; Rädler, J.O.; Wagner, E. 
Controlling Nanoparticle Formulation: A Low-Budget Prototype for the Automation of a Microfluidic Platform. Processes 2021, 9, 129. 
https://doi.org/10.3390/pr9010129

## Getting Started
1. Download all python files and save them to one dedicated folder on your raspberry pi.
2. Run main.py with a python interpreter (python version 3.x, tested on v. 3.7).
3. Follow the instructions printed to the screen.

### Prerequisites
The module **PySerial** (https://pythonhosted.org/pyserial/) needs to be installed before running the program. 
Installation guide: https://pythonhosted.org/pyserial/pyserial.html#installation.
With pip:
```
pip install pyserial
```
All other modules are part of the python standard library.

### Installing

1. Start the raspberry pi, connect to it via ssh or use it in desktop mode. 
2. Use the command line to navigate to the desired folder the program should be written to.
3. Use ‘git’ to copy the syringe pump program repository from GitHub to the Raspberry pi.
    ```
    git clone https://github.com/Dominikmloy/syringe-pump-program.git
    ```
    If the folder already exists, you will get an error.
    --> Either remove the folder (CAVE: It deletes all your logs!) and execute git clone again.
    ```
    rm -r syringe-pump-program
    git clone https://github.com/Dominikmloy/syringe-pump-program.git
    ```
    -->	Or update your repository:
    ```
    cd syringe-pump-program
    git pull origin master
     ```
4. open the repository and start the example program "main.py" to see how the feeding module works.
    ```
    sudo python3 main.py
    ```


## Built With
* PyCharm 2019.1.3

## Versioning
* Version 1.0

## Authors

* **Dominik Loy** 

## License
CC BY 4.0
https://creativecommons.org/licenses/by/4.0/
## Acknowledgments

* **Adrian Loy** - proof reading, answering millions of questions, python wizard - 