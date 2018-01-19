# Mamba text editor: fast, hackable, native, cross-platform and fun.


## Installation
### 1. Install dependencies
Mandatory:

* [Python 3](http://python.org/download)
* [PyQt5](http://www.riverbankcomputing.co.uk/software/pyqt/download). With SVG support.
* [Qutepart](https://github.com/rockiger/qutepart)
* [ctags](http://ctags.sourceforge.net/). For navigation in file

#### Debian and Debian based

```
   apt-get install python3 libqt5svg5 python3-pyqt5 python3-pyqt5.qtwebengine python3-qtconsole python3-markdown python3-docutils ctags
   pip3 install -r requirements.txt

```
   *If your repo doesn't contain **python3-pyqt5.qtwebengine**, remove **python3-pyqt5**, **python3-sip**, and do* `pip3 install PyQt5`

Install Qutepart from [sources](https://github.com/rockiger/qutepart).
#### Other Unixes
Find and install listed packages with your package manager.
Install Qutepart from [sources](https://github.com/rockiger/qutepart).
#### Other systems

Go to official pages of the projects, download packages and install according to instructions.

### 2. Get the sources

```
   git clone https://github.com/rockiger/mamba.git
   cd mamba
```

### 3. Install Mamba
    python3 setup.py install

### 4. Enjoy
Don't forget to send a bug report if you are having some problems.


## Running from the source tree
    python3 bin/Mamba

## License
[GPL v2](LICENSE.GPL2.html)

## Credits

Mamba is based on [Enki](http://enki-editor.org/), created by **Andrei Kopats**

* **Andrei Kopats** (aka **hlamer**) ported core and some plugins to Python, reworked it and released the result as *Mamba*
* **Filipe Azevedo**, **Andrei Kopats** and [Monkey Studio v2 team](http://monkeystudio.org/team) developed *Monkey Studio v2*
