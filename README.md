# ConfluenceFormatter

Nothing much for now.

In Progress:

1. Linking word to page

# How To Use

```python
from confluenceFormatter import ConfluenceFormatter

api = ConfluenceFormatter('username', 'password', 'https://server.atlassian.net/wiki')
api.limit(1)
api.link("Word", "PageLocation")
```
