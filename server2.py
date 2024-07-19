from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from urllib.parse import urlparse, parse_qs

# Sample data structure to store groups
groups = []


class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):

    def do_POST(self):
        if self.path == '/v1/group/':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                group_data = json.loads(post_data.decode('utf-8'))

                # Validate that group_data contains the required fields
                if 'groupId' not in group_data:
                    self.send_response(400)  # Bad Request
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    response = {'message': 'groupId is required in the request body'}
                    self.wfile.write(json.dumps(response).encode('utf-8'))
                    return

                groups.append(group_data)

                self.send_response(201)  # Created
                self.send_header('Content-type', 'application/json')
                self.end_headers()

                response = {'message': 'Group created successfully', 'group': group_data}
                self.wfile.write(json.dumps(response).encode('utf-8'))
            except json.JSONDecodeError:
                self.send_response(400)  # Bad Request
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {'message': 'Invalid JSON format'}
                self.wfile.write(json.dumps(response).encode('utf-8'))
        else:
            self.send_response(404)  # Not Found
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {'message': 'Endpoint not found'}
            self.wfile.write(json.dumps(response).encode('utf-8'))

    def do_DELETE(self):
        if self.path.startswith('/v1/group/'):
            try:
                content_length = int(self.headers['Content-Length'])
                delete_data = self.rfile.read(content_length)
                delete_data_json = json.loads(delete_data.decode('utf-8'))

                group_id = delete_data_json.get('groupId')

                if group_id is None:
                    self.send_response(400)  # Bad Request
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    response = {'message': 'groupId is required in the request body'}
                    self.wfile.write(json.dumps(response).encode('utf-8'))
                    return

                # Check if the group_id exists in groups
                for group in groups:
                    if group.get('groupId') == group_id:
                        groups.remove(group)
                        self.send_response(200)  # OK
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        response = {'message': f'Group with groupId {group_id} deleted successfully'}
                        self.wfile.write(json.dumps(response).encode('utf-8'))
                        return

                # If group_id not found
                self.send_response(404)  # Not Found
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {'message': f'Group with groupId {group_id} not found'}
                self.wfile.write(json.dumps(response).encode('utf-8'))
            except json.JSONDecodeError:
                self.send_response(400)  # Bad Request
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                response = {'message': 'Invalid JSON format'}
                self.wfile.write(json.dumps(response).encode('utf-8'))
        else:
            self.send_response(404)  # Not Found
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {'message': 'Endpoint not found'}
            self.wfile.write(json.dumps(response).encode('utf-8'))

    def do_GET(self):
        # Parse URL path to extract groupId
        path = urlparse(self.path).path
        if path.startswith('/v1/group/'):
            group_id = path[len('/v1/group/'):-1]  # Extract the groupId from URL

            # Search for the groupId in groups
            for group in groups:
                if group.get('groupId') == group_id:
                    self.send_response(200)  # OK
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    response = {'groupId': group_id}
                    self.wfile.write(json.dumps(response).encode('utf-8'))
                    return

            # If group_id not found
            self.send_response(404)  # Not Found
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {'message': f'Group with groupId {group_id} not found'}
            self.wfile.write(json.dumps(response).encode('utf-8'))
        else:
            self.send_response(404)  # Not Found
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = {'message': 'Endpoint not found'}
            self.wfile.write(json.dumps(response).encode('utf-8'))


def run(server_class=HTTPServer, handler_class=SimpleHTTPRequestHandler, port=8001):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f'Starting HTTP server on port {port}...')
    httpd.serve_forever()


if __name__ == '__main__':
    run()