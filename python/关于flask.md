# 关于flask的jsonify与json.dumps的一些追溯和思考

# 目录
- [一、起因](#一起因)
- [二、追溯错误与源码分析](#二追溯错误与源码分析)
- [三、思考](#三思考)

## 一、起因

有一天突然接到服务器报警
```python
TypeError: '<' not supported between instances of 'str' and 'int'
```

追溯错误栈的时候，定位到了 `flask.jsonify` 上面，导致错误的原因是在传入`flask.jsonify`的`dict的key里面同时混合了string和int`两种，修改完错误的数据之后，开始研究为什么会出现这样的错误，以及为什么会这么设计？

## 二、追溯错误与源码分析

源码追溯路径：`JSONDecoder` -> `flask.json.__init__.py` -> `_dump_arg_defaults`

然后我们开始分析一下这部分的源码
```python
def _dump_arg_defaults(kwargs, app=None):
    """Inject default arguments for dump functions."""
    if app is None:
        app = current_app

    if app:
        bp = app.blueprints.get(request.blueprint) if request else None
        kwargs.setdefault(
            "cls", bp.json_encoder if bp and bp.json_encoder else app.json_encoder
        )
        if not app.config["JSON_AS_ASCII"]:
            kwargs.setdefault("ensure_ascii", False)
        kwargs.setdefault("sort_keys", app.config["JSON_SORT_KEYS"])
    else:
        # 在这里 sort_keys 被设置为了 True
        kwargs.setdefault("sort_keys", True)
        kwargs.setdefault("cls", JSONEncoder)
```
这个项目使用的 `JSONDecoder`是继承的flask的，然后稍作修改做了一些兼容(处理`bson.ObjectId`，`datetime`之类的数据类型)，主体还是标准库当中`JSONEncoder`
然后我们继续看一下 标准库当中`JSONEncoder`中的`sort_keys`的使用是在 `JSONEncoder._iterencode_dict`
```python
    def _iterencode_dict(dct, _current_indent_level):
        # .....以上省略
        if _sort_keys:
            items = sorted(dct.items(), key=lambda kv: kv[0])
        # .....以下省略
```
看到这里，我就开始思考一个问题，为什么这里不修改成如下这样呢？
```python
    def _iterencode_dict(dct, _current_indent_level):
        # .....以上省略
        if _sort_keys:
            items = sorted(dct.items(), key=lambda kv: str(kv[0]))
        # .....以下省略
```
毕竟json的key是只有`string`的，这样是可以有效增加代码的鲁棒性的，但是官方为什么没有选择这么做？

`好家伙，我是不是获得了一个给python提pr的大好机会，以后我就是Python的贡献者之一了，想一想有点激动！！github启动！！！`

然后我找到了这个[issue25457](https://bugs.python.org/issue25457)
```python
python2.7
===========

Python 2.7.10 (default, May 29 2015, 10:02:30)
[GCC 4.8.4] on linux2
Type "help", "copyright", "credits" or "license" for more information.
>>> import json
>>> json.dumps({1 : 42, "foo" : "bar", None : "nada"}, sort_keys = True)
'{"null": "nada", "1": 42, "foo": "bar"}'

python3.5
============

Python 3.5.0 (default, Oct  5 2015, 12:03:13)
[GCC 4.8.5] on linux
Type "help", "copyright", "credits" or "license" for more information.
>>> import json
>>> json.dumps({1 : 42, "foo" : "bar", None : "nada"}, sort_keys = True)
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
  File "/usr/lib64/python3.5/json/__init__.py", line 237, in dumps
    **kw).encode(obj)
  File "/usr/lib64/python3.5/json/encoder.py", line 199, in encode
    chunks = self.iterencode(o, _one_shot=True)
  File "/usr/lib64/python3.5/json/encoder.py", line 257, in iterencode
    return _iterencode(o, 0)
TypeError: unorderable types: str() < int()
```
在这里，发现了更奇怪的问题就是在python2当中，确实是我想的样子的，但是为什么python3中修改成了现在这个样子呢？
在这个issue里面大佬们给出了理由
```
Since mixed type keys lack meaningful sort order, I'm not sure it's wrong to reject attempts to sort them. Converting to string is as arbitrary and full of potential for silently incorrect comparisons as the Python 2 behavior, and reintroducing it seems like a bad idea.
混合排序会引入不确定性，Python2那么处理不是一个好主意，现在挺好的，也不准备改回去
```
## 三、思考
当然上面讨论比较激烈，思考之后我比较赞同Python3的这种做法
1. `当你处理数据的时候应该明确的知道自己要做什么（要排序)。这里我个人觉得是flask的坑，sort_keys默认应该和标准库保持一致为False的`
2. `并且明确的知道你的数据是什么样的（确保传入的key就是全是字符串），这个是动态语言的缺点吧，这也是我越来越喜欢go的原因`

关于工作的思考
1. `还是那句话，不要相信传进来的数据，一定要检查，尤其是关键业务`
