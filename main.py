import datetime
import time

def log(s, typ="log"):
   print(str(datetime.datetime.now()) + " [" + typ + "] " + s) 
   
log("starting up")
started = time.time()

import re
from urllib.parse import parse_qs, quote, urlparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import uuid
import requests
from bs4 import BeautifulSoup
import html
from minify_html import minify
from translations import languages
import time

unique = str(uuid.uuid4())

with open("search.html", "r") as file:
    index = minify(file.read().replace("uuid", unique[:8]), minify_js=True, minify_css=True)

with open("wiki.html", "r") as file:
    wiki = file.read()
    
with open("rubik.woff2", "rb") as file:
    rubik = file.read()
    
m = 0
c = 0
v = ""

log("querying wikipedia (this could take a while)")
    
for lang in languages:
    m = m + 1
    try:
        if requests.get("https://" + str(lang) + ".wikipedia.org/api/rest_v1/page/", headers={"User-Agent": "OpenWiki (" + unique + ")"}).status_code == 200:
            c = c + 1
            v = str(lang)
    except requests.exceptions.RequestException:
        pass
    
if c == 0:  
    log("wikipedia is being fully filtered either by your isp or firewall.", "fatal")
    raise SystemExit
elif c != m:
    log("wikipedia is being [partially] filtered wither by your isp or firewall", "warn")
    
log("queried " + str(m) + " wikipedia servers of which " + str(c) + " responded")

       
class handler(BaseHTTPRequestHandler):
    def log_message(*args):
        return
    def do_POST(self):
        content_length = int(self.headers["Content-Length"])
        post_data = self.rfile.read(content_length)
        form_data = parse_qs(post_data.decode("utf-8"))
        
        self.send_response(302)
        self.send_header("Location", form_data.get("q")[0])
        self.end_headers()
        return
    def do_GET(self):
        lang = "en"
        if self.headers.get("accept-language"):
            accepted = self.headers["accept-language"]
            accepted = accepted.split(';')[0]
            accepted = accepted.split(',')
            for alang in accepted:
                alang = alang.split('-')[0]
                alang = alang.lower()
                if alang in languages:
                    lang = alang
                    break
        if self.path == "/search?y":
            data = requests.get("https://" + lang + ".wikipedia.org/w/api.php?action=query&format=json&list=random&rnlimit=1&rnnamespace=0", headers={"User-Agent": "OpenWiki (" + unique + ")"}).json()
            if data.get("error"):
                self.send_response(404)
                self.end_headers()
                return
            self.send_response(302)
            self.send_header("Location", quote(data["query"]["random"][0]["title"]))
            self.end_headers()
            return
        if self.path.startswith("/search?q="):
            query = quote(urlparse(self.path).query[2:])
            data = requests.get("https://" + lang + ".wikipedia.org/w/rest.php/v1/search/title?q=" + query + "&limit=3", headers={"User-Agent": "OpenWiki (" + unique + ")"})
            self.send_response(data.status_code)
            self.send_header("Cache-Control", "no-cache") 
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(data.text.encode("utf-8"))
            return
        if self.path == "/":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            index2 = index.replace("TRANSLATE_1", languages[lang][0])
            index2 = index2.replace("TRANSLATE_3", languages[lang][2])
            index2 = index2.replace("TRANSLATE_4", languages[lang][3])
            self.wfile.write(index2.encode("utf-8"))
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
            if self.path.startswith("/Template+") or self.path.startswith("/Template:"):
                self.send_response(404)
                self.end_headers()
                return
            article = requests.get("https://" + lang + ".wikipedia.org/w/api.php?action=parse&page=" + self.path[1:].replace("+", ":") + "&prop=text&format=json", headers={"User-Agent": "OpenWiki (" + unique + ")"}).json()
            if article.get("error"):
                self.send_response(404)
                self.end_headers()
                return
            page_id = str(article["parse"]["pageid"])
            soup = BeautifulSoup(article["parse"]["text"]["*"], "html.parser")
            # check for redirects
            redirect = soup.find("ul", class_="redirectText")
            if redirect:
                self.send_response(302)
                self.send_header("Location", redirect.find("a", href=True)["href"].split("/")[-1])
                self.end_headers()
                return
            #for h2 in soup.find_all("h2"):
                #del h2["id"]
            for script in soup.find_all("script"):
                script.decompose()
            for element in soup.find_all(["figure", "table", "img", "svg", "form", "checkbox", "input", "button", "hr"]):
                element.decompose()
            for element in soup.find_all(class_=["mw-editsection", "portalbox", "side-box", "portal-bar", "thumb", "navbox", "side-box-flex", "barbox", "gallery", "sister-bar", "mw-empty-elt", "noprint"]):
                element.decompose()
            for anchor in soup.find_all("a", href=True):
                if anchor["href"].replace("File:", "") != anchor["href"]:
                    anchor.decompose()
                elif anchor["href"].replace("wikipedia.org", "") != anchor["href"]:
                    del anchor["href"]
                elif anchor.get_text() == "edit":
                    anchor.decompose()
                else:
                    anchor["href"] = anchor["href"].replace("/wiki/", "")
                    if not anchor["href"].startswith("http"):
                        anchor["href"] = anchor["href"].replace(":", "+")
            for style in soup.find_all("style"):
                style.string = re.sub(r"url\([^\)]*\)", "", style.string)
            description = soup.find("p")
            text = str(soup)
            title = article["parse"]["title"]
            fixed = '<h2 id="' + title + '" style="font-size:2.3rem;margin-bottom:20px">' + title + '</h2>\n' + text
            
            thestuff = ""
            for h2 in soup.find_all("h2", id=True):   
                #fixed = fixed.replace("<h2>" + h2.get_text() + "</h2>", '<h2 id="' + match.replace(" ", "-").lower() + '">' + match + "</h2>")
                thestuff = thestuff + '<a style="color:#878788;filter:brightness(0.9);font-size:0.9rem" class="sidebarm" href="#' + h2["id"] + '">' + h2.get_text() + '</a>'
            wiki2 = wiki.replace("TITLE_WIKI_PAGE", html.escape(title)) # title on sidebar for contents
            fixed = wiki2.replace("<!-- CONTENTS -->", fixed) # the description
            fixed = fixed.replace("<!-- SIDEBAR -->", thestuff)
            fixed = fixed.replace("TRANSLATE_1", languages[lang][0])
            fixed = fixed.replace("TRANSLATE_2", languages[lang][1])
            if description:
                for sup in description.find_all("sup"):
                    sup.decompose()
                fixed = fixed.replace("DESCRIPTION_WIKI_PAGE", html.escape(description.get_text()))
            else:
                fixed = fixed.replace("DESCRIPTION_WIKI_PAGE", "No description available.")
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(minify(fixed, minify_js=True, minify_css=True).encode("utf-8"))
            return
            
log("ready in " + str(round(time.time() - started, 2)) + "s")
log("listening on http://localhost:9827")
ThreadingHTTPServer(("127.0.0.1", 9827), handler).serve_forever()