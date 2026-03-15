# NukeMCP Plugins

Drop Python files here to extend NukeMCP with custom tools. Each file should
have a `register(server)` function following the same pattern as the built-in
tool modules in `src/nukemcp/tools/`.

Example plugin (`my_studio_tools.py`):

```python
def register(server):
    mcp = server.mcp
    conn = server.connection

    @mcp.tool()
    def my_custom_tool(node_name: str) -> dict:
        """Do something studio-specific."""
        return conn.send_command("get_node_info", {"node_name": node_name})
```

Files starting with `_` are ignored. Plugins load in alphabetical order.
