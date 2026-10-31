"""Cognipeer gold SQL'lerinin SQLite'ta calismasi icin MySQL islev taklitleri
(sql_arastirma/fix_cognipeer.py'den, degistirilmeden). Hem gold hem model SQL'i ayni shim'lerle calisir."""
import re


# ---- UDF shims ----
def _parse_date_any(s):
    import datetime
    if s is None:
        return None
    s = str(s).strip()
    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%Y/%m/%d', '%m/%d/%Y'):
        try:
            return datetime.datetime.strptime(s, fmt)
        except Exception:
            continue
    return None

def udf_year(s):
    d = _parse_date_any(s)
    return d.year if d else None

def udf_month(s):
    d = _parse_date_any(s)
    return d.month if d else None

def udf_day(s):
    d = _parse_date_any(s)
    return d.day if d else None

def udf_quarter(s):
    d = _parse_date_any(s)
    return (d.month - 1) // 3 + 1 if d else None

def udf_dayofweek(s):
    d = _parse_date_any(s)
    return (d.weekday() + 1) % 7 + 1 if d else None  # MySQL: 1=Sunday..7=Saturday

def udf_now():
    import datetime
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def udf_curdate():
    import datetime
    return datetime.date.today().strftime('%Y-%m-%d')

def udf_datediff(d1, d2):
    a, b = _parse_date_any(d1), _parse_date_any(d2)
    return (a - b).days if a and b else None

def udf_time_to_sec(t):
    try:
        h, m, s = str(t).split(':')
        return int(h) * 3600 + int(m) * 60 + int(s)
    except Exception:
        return None

MYSQL_FMT_MAP = [
    ('%Y', '%Y'), ('%m', '%m'), ('%d', '%d'),
    ('%H', '%H'), ('%i', '%M'), ('%s', '%S'),
    ('%b', '%b'), ('%B', '%B'), ('%a', '%a'),
]

_TRUNC_FMT = {'year': '%Y-01-01', 'month': '%Y-%m-01', 'day': '%Y-%m-%d',
              'hour': '%Y-%m-%d %H:00:00', 'quarter': None}

def udf_date_trunc(unit, date_str):
    d = _parse_date_any(date_str)
    if not d:
        return None
    unit = str(unit).lower()
    if unit == 'quarter':
        q_month = (d.month - 1) // 3 * 3 + 1
        return d.replace(month=q_month, day=1).strftime('%Y-%m-%d')
    fmt = _TRUNC_FMT.get(unit)
    if not fmt:
        return date_str
    return d.strftime(fmt)

def udf_date_format(date_str, fmt):
    d = _parse_date_any(date_str)
    if not d:
        return None
    py_fmt = fmt
    for mysql_code, py_code in MYSQL_FMT_MAP:
        py_fmt = py_fmt.replace(mysql_code, py_code)
    try:
        return d.strftime(py_fmt)
    except Exception:
        return None

def needs_fetchall(sql):
    """A result set is pending (must be drained before commit) for SELECT/WITH,
    and also for any statement carrying a RETURNING clause (e.g. our writable-CTE rewrite)."""
    return bool(re.match(r'^\s*(SELECT|WITH)\b', sql, re.I)) or bool(re.search(r'\bRETURNING\b', sql, re.I))

def register_shims(con):
    con.create_function('YEAR', 1, udf_year)
    con.create_function('MONTH', 1, udf_month)
    con.create_function('DAY', 1, udf_day)
    con.create_function('QUARTER', 1, udf_quarter)
    con.create_function('DAYOFWEEK', 1, udf_dayofweek)
    con.create_function('NOW', 0, udf_now)
    con.create_function('CURDATE', 0, udf_curdate)
    con.create_function('GETDATE', 0, udf_now)
    con.create_function('DATEDIFF', 2, udf_datediff)
    con.create_function('TIME_TO_SEC', 1, udf_time_to_sec)
    con.create_function('DATE_FORMAT', 2, udf_date_format)
    con.create_function('DATE_TRUNC', 2, udf_date_trunc)
