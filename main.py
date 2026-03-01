import re
from urllib.parse import parse_qs, quote, urlparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import uuid
import requests
from bs4 import BeautifulSoup

unique = str(uuid.uuid4())

with open("search.html", "r") as file:
    index = file.read().replace("uuid", unique[:8]).encode("utf-8")

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
                self.send_header("Location", pathf[1:])
                self.end_headers()
                return
            article = requests.get("https://en.wikipedia.org/w/api.php?action=parse&page=" + self.path[1:].replace("+", ":") + "&prop=text&format=json", headers={"User-Agent": "OpenWiki (" + unique + ")"}).json()
            if article.get("error"):
                self.send_response(404)
                self.end_headers()
                return
            soup = BeautifulSoup(article["parse"]["text"]["*"], "html.parser")
            # check for redirects
            redirect = soup.find("ul", class_="redirectText")
            if redirect:
                self.send_response(302)
                self.send_header("Location", redirect.find("a", href=True)["href"].split("/")[-1])
                self.end_headers()
                return
            for h2 in soup.find_all("h2"):
                del h2["id"]
            for element in soup.find_all(["figure", "table", "img", "svg", "form", "checkbox", "input", "button", "hr"]):
                element.decompose()
            for element in soup.find_all(class_=["mw-editsection", "portalbox", "side-box", "portal-bar", "thumb", "navbox", "side-box-flex", "barbox", "gallery", "sister-bar"]):
                element.decompose()
            for anchor in soup.find_all("a", href=True):
                if anchor["href"].replace("File:", "") != anchor["href"]:
                    anchor.decompose()
                elif anchor["href"].replace("wikipedia.org", "") != anchor["href"]:
                    del anchor["href"]
                else:
                    anchor["href"] = anchor["href"].replace("/wiki/", "").replace(":", "+")
            for style in soup.find_all("style"):
                style.string = re.sub(r"url\([^\)]*\)", "", style.string)
            text = str(soup)
            title = article["parse"]["title"]
            fixed = '<h2 id="' + title + '" style="font-size:2.3rem;margin-bottom:20px">' + title + '</h2>\n' + text
            matches = re.findall(r"<h2>(.*?)<\/h2>", fixed)
            thestuff = ""
            for match in matches:
                fixed = fixed.replace("<h2>" + match + "</h2>", '<h2 id="' + match.replace(" ", "-").lower() + '">' + match + "</h2>")
                thestuff = thestuff + '<a style="color:white;filter:brightness(0.9);font-size:0.9rem" href="#' + match.replace(" ", "-").lower() + '">' + match + '</a>'
            wiki2 = wiki.replace("TITLE_WIKI_PAGE", title) # title on sidebar for contents
            fixed = wiki2.replace("<!-- CONTENTS -->", fixed) # the description
            fixed = fixed.replace("<!-- SIDEBAR -->", thestuff)
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(fixed.encode("utf-8"))
            return
    
server_address = ("127.0.0.1", 9827)
httpd = ThreadingHTTPServer(server_address, handler)
httpd.serve_forever()
