# ConfluenceFormatter

Features

1. Add Confluence Page link to keywords using Confluence markdown
2. Save diff file of to be committed updates

# How To Use

```python
from confluenceFormatter import ConfluenceFormatter

api = ConfluenceFormatter('username', 'password', 'https://server.atlassian.net/wiki')
api.limit(1)
api.link("Word", "PageLocation") // Execute
api.link("Word", "PageLocation", verify=True) // Check diff
```
