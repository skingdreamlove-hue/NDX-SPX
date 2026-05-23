import http.server,functools,socket
port=5000
for _ in range(100):
    try:
        s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        s.settimeout(0.5)
        s.bind(('',port))
        s.close()
        break
    except:
        port+=1
else:
    print('No port!')
    exit(1)
print(f'Server running at http://localhost:{port}')
handler=functools.partial(http.server.SimpleHTTPRequestHandler,directory='.')
http.server.HTTPServer(('0.0.0.0',port),handler).serve_forever()