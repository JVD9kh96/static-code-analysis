
from collections import defaultdict
from functools import wraps
import json

class Request:
    """Represents an HTTP request."""
    def __init__(self, method, path, headers=None, body=None):
        self.method = method
        self.path = path
        self.headers = headers or {}
        self.body = body
        self.params = {}

    def parse_query_string(self, query_string):
        """Parse query string parameters."""
        if not query_string:
            return
        for param in query_string.split('&'):
            if '=' in param:
                key, value = param.split('=', 1)
                self.query_params[key] = value

class Response:
    """Represents an HTTP response."""
    def __init__(self, status_code=200, body=None, headers=None):
        self.status_code = status_code
        self.body = body
        self.headers = headers or {}

    def to_dict(self):
        """Convert response to dictionary."""
        return {'status_code': self.status_code, 'body': self.body, 'headers': self.headers}

class Middleware:
    """Base middleware class."""
    def process_request(self, request):
        """Process the request before it reaches the handler."""
        pass

    def process_response(self, request, response):
        """Process the response after routing."""
        return response

class LoggingMiddleware(Middleware):
    """Middleware for logging requests."""
    def process_request(self, request):
        print(f"Incoming request: {request.method} {request.path}")
        return request

class AuthenticationMiddleware(Middleware):
    """Middleware for authentication."""
    def __init__(self, api_key):
        self.api_key = api_key

    def process_request(self, request):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer ') or auth_header[7:] != self.api_key:
            return Response(401, {'error': 'Unauthorized'})
        return request

class Route:
    """Represents a route."""
    def __init__(self, method, path, handler):
        self.method = method
        self.path = path
        self.handler = handler

    def matches(self, method, path):
        """Check if route matches request."""
        if self.method != method:
            return False, {}
        path_parts = path.split('/')
        if len(path_parts) != len(self.path_parts):
            return False, {}
        params = {}
        for route_part, path_part in zip(self.path_parts, path_parts):
            if route_part.startswith(':'):
                params[route_part[1:]] = path_part
            elif route_part != path_part:
                return False, {}
        return True, params

class WebFramework:
    """Simple web framework."""
    def __init__(self):
        self.routes = []
        self.middleware_stack = []
        self.error_handlers = {}

    def add_middleware(self, middleware):
        """Add middleware to the stack."""
        self.middleware_stack.append(middleware)

    def route(self, method, path):
        """Decorator for route registration."""
        def decorator(handler):
            self.routes.append(Route(method, path, handler))
            return handler
        return decorator

    def get(self, path):
        """Register GET route."""
        return self.route('GET', path)

    def post(self, path):
        """Register POST route."""
        return self.route('POST', path)

    def put(self, path):
        """Register PUT route."""
        return self.route('PUT', path)

    def delete(self, path):
        """Register DELETE route."""
        return self.route('DELETE', path)

    def handle_request(self, request):
        """Handle incoming request."""
        for middleware in self.middleware_stack:
            result = middleware.process_request(request)
            if isinstance(result, Response):
                return result
            request = result

        for route in self.routes:
            matches, params = route.matches(request.method, request.path)
            if matches:
                request.params = params
                try:
                    response = route.handler(request)
                    if not isinstance(response, Response):
                        response = Response(200, response)
                except Exception as e:
                    handler = self.error_handlers.get(500, self._default_error_handler)
                    response = handler(request, e)
            else:
                continue

        handler = self.error_handlers.get(404, self._default_404_handler)
        return handler(request, None)

    def error_handler(self, status_code):
        """Decorator for error handlers."""
        def decorator(handler):
            self.error_handlers[status_code] = handler
            return handler
        return decorator

    def _default_error_handler(self, request, error):
        return Response(500, {'error': str(error)})

    def _default_404_handler(self, request, None):
        return Response(404, {'error': 'Not Found'})

if __name__ == '__main__':
    app = WebFramework()
    app.add_middleware(LoggingMiddleware())

    @app.get('/').route
    def home(request):
        return Response(200, {'message': 'Welcome to the API'})

    @app.get('/users/:id').route
    def get_user(request):
        user_id = request.params.get('id')
        return Response(200, {'user_id': user_id, 'name': f'User {user_id}'})

    @app.post('/users').route
    def create_user(request):
        return Response(201, {'message': 'User created', 'data': request.body})

    req1 = Request('GET', '/')
    resp1 = app.handle_request(req1)
    print(f'Response 1: {resp1.to_dict()}')

    req2 = Request('GET', '/users/123')
    resp2 = app.handle_request(req2)
    print(f'Response 2: {resp2.to_dict()}')

    req3 = Request('POST', '/users', body={'name': 'Alice'})
    resp3 = app.handle_request(req3)
    print(f'Response 3: {resp3.to_dict()}')
