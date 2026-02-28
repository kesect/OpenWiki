import wikipediaapi
import re
from urllib.parse import parse_qs, quote, urlparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import uuid
import requests

unique = str(uuid.uuid4())

wiki_wiki = wikipediaapi.Wikipedia(user_agent="OpenWiki (" + unique + ")", language="en", extract_format=wikipediaapi.ExtractFormat.HTML)

with open("search.html", "r") as file:
    index = file.read().encode("utf-8")

with open("wiki.html", "r") as file:
    wiki = file.read()
    
with open("rubik.woff2", "rb") as file:
    rubik = file.read()
    
class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers["Content-Length"])
        post_data = self.rfile.read(content_length)
        form_data = parse_qs(post_data.decode("utf-8"))
        
        self.send_response(302)
        self.send_header("Location", form_data.get("q")[0])
        self.end_headers()
        return
    def do_GET(self):
        if self.path.startswith("/search"):
            query = quote(urlparse(self.path).query[2:])
            data = requests.get("https://en.wikipedia.org/w/rest.php/v1/search/title?q=" + query + "&limit=3", headers={"User-Agent": "OpenWiki (" + unique + ")"})
            self.send_response(data.status_code)
            self.send_header("Cache-Control", "public, max-age=86400") 
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(data.text.encode("utf-8"))
            return
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(index)
            return
        elif self.path == "/rubik.woff2":
            self.send_response(200)
            self.send_header("Content-Type", "application/octet-stream")
            self.send_header("Cache-Control", "public, max-age=2592000") 
            self.end_headers()
            self.wfile.write(rubik)
            return
        elif self.path == "/favicon.ico":
            self.send_response(404)
            self.end_headers()
            return
        elif self.path.startswith("/.well-known/"):
            self.send_response(404)
            self.end_headers()
            return            
        else:
            pathf = self.path.replace("%20", "_")
            if pathf != self.path:
                self.send_response(302)
                self.send_header("Location", pathf)
                self.end_headers()
                return
            page_py = wiki_wiki.page(self.path[1:])
            if page_py.exists():                
                fixed = '<h2 id="' + page_py.title + '" style="font-size:2.3rem;margin-bottom:20px">' + page_py.title + '</h2>\n' + page_py.text
                matches = re.findall(r'<h2>(.*?)<\/h2>', fixed)
                thestuff = ""
                for match in matches:
                    fixed = fixed.replace("<h2>" + match + "</h2>", '<h2 id="' + match.replace(" ", "-").lower() + '">' + match + "</h2>")
                    thestuff = thestuff + '<a style="color:white;filter:brightness(0.9)" href="#' + match.replace(" ", "-").lower() + '">' + match + '</a>'
                wiki2 = wiki.replace("TITLE_WIKI_PAGE", page_py.title) # title on sidebar for contents
                fixed = wiki2.replace("<!-- CONTENTS -->", fixed) # the description
                fixed = fixed.replace("<!-- SIDEBAR -->", thestuff)
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(fixed.encode("utf-8"))
                return
            else:
                self.send_response(404)
                self.end_headers()
                return

server_address = ("127.0.0.1", 9827)
httpd = ThreadingHTTPServer(server_address, handler)
httpd.serve_forever()