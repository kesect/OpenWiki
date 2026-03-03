# OpenWiki
![Screenshot of OpenWiki](media/openwiki.avif)
**OpenWiki** is a lightweight, open source alternative frontend for [Wikipedia](https://wikipedia.org) designed to evade censorship. There is no tracking or cookies and Javascript is not required.

> [!WARNING]
> You should put OpenWiki behind a reverse proxy (such as nginx, apache, etc) on a obscene path.
 
## Installation
```
git clone https://github.com/kesect/OpenWiki
cd OpenWiki
pip install -r requirements.txt --break-system-packages
```

## Usage
All you have to run is ```python main.py``` or on some systems ```python3 main.py``` to start up OpenWiki.

Then visit ```http://localhost:9827``` through your web browser and your all done!
