from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer


class webserverHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        try:
            if self.path.endswith("/hello"):
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()

                output = ""
                output += "<html><body>Hello!</body></html>"
                self.wfile.write(output)
                print output
                return
        except IOError:
            self.send_error(404, "File not found %s" % self.path)

    def do_POST(self):
    	try :
    		self.send_response(301)
    		self.end_headers()

    		ctype , pdict = cgi.parse_header(self.headers.getheader('content-type'))
    		if ctype=='multipart/form-data':
    			fields = cgi.parse_multipart(self.rfile,pdict)
    			messagecontent = fields.get('message')
    		output = ""
    		output += "<html><body>"
    		output += "okay how about this "
    		output += "<h1>%s</h1>" % messagecontent[0]


    	except :
    		pass 

def main():
    try:
        port = 8000
        server = HTTPServer(('', port),webserverHandler)
        print "Web server running on port %s" % port
        server.serve_forever()
    except KeyboardInterrupt:
        print "stopping web service"
        server.socket.close()


if __name__ == '__main__':
    main()
