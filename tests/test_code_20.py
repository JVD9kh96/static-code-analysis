"""Tests for genCodes.code_20 (Request, Response, Route, WebFramework)."""
import pytest
from genCodes import code_20


def test_request_creation():
    req = code_20.Request("GET", "/users", headers={"Accept": "application/json"})
    assert req.method == "GET"
    assert req.path == "/users"
    assert req.headers.get("Accept") == "application/json"
    assert req.params == {}


def test_request_parse_query_string():
    req = code_20.Request("GET", "/search")
    req.parse_query_string("q=hello&page=2")
    assert req.params["q"] == "hello"
    assert req.params["page"] == "2"


def test_response_to_dict():
    resp = code_20.Response(200, {"message": "OK"}, {"Content-Type": "application/json"})
    d = resp.to_dict()
    assert d["status_code"] == 200
    assert d["body"]["message"] == "OK"
    assert d["headers"]["Content-Type"] == "application/json"


def test_route_matches():
    def handler(request):
        return code_20.Response(200, {})

    route = code_20.Route("GET", "/users/:id", handler)
    matches, params = route.matches("GET", "/users/123")
    assert matches is True
    assert params.get("id") == "123"

    matches, _ = route.matches("POST", "/users/123")
    assert matches is False


def test_authentication_middleware_unauthorized():
    auth = code_20.AuthenticationMiddleware(api_key="secret")
    req = code_20.Request("GET", "/", headers={})
    result = auth.process_request(req)
    assert isinstance(result, code_20.Response)
    assert result.status_code == 401


def test_authentication_middleware_authorized():
    auth = code_20.AuthenticationMiddleware(api_key="secret")
    req = code_20.Request("GET", "/", headers={"Authorization": "Bearer secret"})
    result = auth.process_request(req)
    assert result == req


def test_web_framework_handle_request():
    app = code_20.WebFramework()

    def home_handler(request):
        return code_20.Response(200, {"message": "Welcome"})

    app.routes.append(code_20.Route("GET", "/", home_handler))
    req = code_20.Request("GET", "/")
    resp = app.handle_request(req)
    assert resp.status_code == 200
    assert resp.body["message"] == "Welcome"


def test_web_framework_404():
    app = code_20.WebFramework()
    req = code_20.Request("GET", "/nonexistent")
    resp = app.handle_request(req)
    assert resp.status_code == 404
