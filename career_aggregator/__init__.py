"""
DB driver compatibility:
- Linux/macOS typically use `mysqlclient` (MySQLdb).
- Windows setups often prefer pure-Python `PyMySQL`.

If `mysqlclient` isn't installed, we transparently use PyMySQL as MySQLdb.
"""

try:
    import MySQLdb  # noqa: F401
except Exception:  # pragma: no cover
    try:
        import pymysql

        pymysql.install_as_MySQLdb()
    except Exception:
        # Let Django raise the underlying import error later with a clear message.
        pass

