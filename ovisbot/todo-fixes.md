---
Title: Bug Fixes / Code Suggestions
Author: ishtar
---

+ Add comments

+ Define constants for error messages:
```
ctf.py(271, 17)
ctf.py(501, 17)
ctf.py(536, 17)
ctf.py(599, 17)
ctf.py(685, 17)
ctf.py(770, 17)
ctf.py(797, 17)
```

+ Type hinting for static analysis
```py
def add(x:int, y:int) -> int:
    return x + y
```

+ Some code raises exceptions and some others not. I suggest to follow the exceptions model.
```
https://github.com/cybermouflons/ovisbot/blob/09c475c12a5b00789226e0d7e4b1a0d31263c82c/ovisbot/extensions/ctf/ctf.py#L646
```