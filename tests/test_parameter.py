from django_openapi import schema
from django_openapi.parameter import Cookie, Path, Query, Style


class Color(schema.Model):
    R = schema.Integer()
    G = schema.Integer()
    B = schema.Integer()


def test_query_form_true_string__default(rf):
    assert Query({"color": schema.String()}).parse_request(rf.get("/?color=blue")) == {
        "color": "blue",
    }


def test_query_form_true_array__default(rf):
    assert Query({"color": schema.List(schema.String())}).parse_request(
        rf.get("/?color=blue&color=black&color=brown")
    ) == {"color": ["blue", "black", "brown"]}


def test_query_form_true_object__default(rf):
    assert Query({"color": Color()}).parse_request(rf.get("/?R=100&G=200&B=150")) == {
        "color": {"R": 100, "G": 200, "B": 150}
    }


def test_query_form_false_string(rf):
    assert Query(
        {"color": schema.String()}, param_styles={"color": Style("form", False)}
    ).parse_request(rf.get("/?color=blue")) == {"color": "blue"}


def test_query_form_false_array(rf):
    assert Query(
        {"color": schema.List(schema.String)},
        param_styles={"color": Style("form", False)},
    ).parse_request(rf.get("/?color=blue,black,brown")) == {
        "color": ["blue", "black", "brown"]
    }


def test_query_form_false_object(rf):
    assert Query(
        {"color": Color()}, param_styles={"color": Style("form", False)}
    ).parse_request(rf.get("/?color=R,100,G,200,B,150")) == {
        "color": {"R": 100, "G": 200, "B": 150}
    }


def test_query_spaceDelimited_false_array(rf):
    assert Query(
        {"color": schema.List(schema.String)},
        param_styles={"color": Style("spaceDelimited", False)},
    ).parse_request(rf.get("/?color=blue%20black%20brown")) == {
        "color": ["blue", "black", "brown"]
    }


def test_query_pipeDelimited_false_array(rf):
    assert Query(
        {"color": schema.List(schema.String)},
        param_styles={"color": Style("pipeDelimited", False)},
    ).parse_request(rf.get("/?color=blue|black|brown")) == {
        "color": ["blue", "black", "brown"]
    }


def test_query_deepObject_true_object(rf):
    assert Query(
        {"color": Color()}, param_styles={"color": Style("deepObject", True)}
    ).parse_request(rf.get("/?color[R]=100&color[G]=200&color[B]=150")) == {
        "color": {"R": 100, "G": 200, "B": 150}
    }


def test_cookie_form_false_string__default(rf):
    request = rf.get("/")
    request.COOKIES["color"] = "blue"
    assert Cookie({"color": schema.String()}).parse_request(request) == {
        "color": "blue",
    }


def test_cookie_form_false_array__default(rf):
    req = rf.get("/")
    req.COOKIES["color"] = "blue,red,yellow"
    assert Cookie({"color": schema.List()}).parse_request(req) == {
        "color": ["blue", "red", "yellow"]
    }


def test_cookie_form_false_object__default(rf):
    req = rf.get("/")
    req.COOKIES["color"] = "B,0,G,0,R,0"
    assert Cookie({"color": Color()}).parse_request(req) == {
        "color": {"B": 0, "G": 0, "R": 0}
    }


def test_path_simple_falst_string__default():
    assert Path("/color/{color}").parse_kwargs({"color": "blue"}) == {"color": "blue"}


def test_path_simple_false_array__default():
    assert Path(
        "/color/{color}",
        {"color": schema.List()},
    ).parse_kwargs(
        {"color": "red,blue,yellow"}
    ) == {"color": ["red", "blue", "yellow"]}


def test_path_simple_true_array():
    assert Path(
        "/color/{color}",
        {"color": schema.List()},
        {"color": Style("simple", True)},
    ).parse_kwargs({"color": "red,blue,yellow"}) == {"color": ["red", "blue", "yellow"]}


def test_path_simple_false_object__default():
    assert Path(
        "/color/{color}",
        {"color": Color()},
    ).parse_kwargs(
        {"color": "R,100,G,200,B,150"}
    ) == {"color": {"B": 150, "G": 200, "R": 100}}


def test_path_simple_true_object():
    assert Path(
        "/color/{color}",
        {"color": Color()},
        {"color": Style("simple", True)},
    ).parse_kwargs({"color": "R=100,G=200,B=150"}) == {
        "color": {"B": 150, "G": 200, "R": 100}
    }
