import cgi
import datetime
import decimal
import itertools

tablecounter = itertools.count(0)


def html(header_rows):
    """
    Convert a list of tuples describing a table into a HTML string
    """
    name = 'table%d' % next(tablecounter)
    return HtmlTable([map(fmt, row) for row in header_rows], name).render()


def truncate(text, n=600):
    """
    Truncate a text to the first `n` characters and add an ellipsis if
    the original text was longer than that.
    """
    ttext = text[:n]
    if len(text) > n:
        ttext += ' ...'
    return ttext


def fmt(number):
    """
    Format numbers in a nice way
    """
    if isinstance(number, datetime.datetime):
        return number.isoformat()[:19]
    elif isinstance(number, datetime.timedelta):
        return str(number)[:7]
    elif isinstance(number, (float, decimal.Decimal)):
        if number > 1000:
            return '{:,d}'.format(int(round(number)))
        elif number < 10:
            return '%6.3f' % number
        else:
            return str(int(number))
    return str(number)


class Fetcher(object):
    """
    Small wrapper over a DB API 2 cursor
    """
    def __init__(self, curs):
        self.curs = curs

    def query(self, templ, *args):
        self.curs.execute(templ, args)
        header = [r[0] for r in self.curs.description]
        return [header] + self.curs.fetchall()


class HtmlTable(object):
    """
    Convert a sequence header+body into a HTML table.
    """
    css = """\
    tr.evenRow { background-color: lightgreen }
    tr.oddRow { }
    th { background-color: lightblue }
    """
    maxrows = 5000
    border = "1"
    summary = ""

    def __init__(self, header_plus_body, name='noname',
                 empty_table='Empty table'):
        header, body = header_plus_body[0], header_plus_body[1:]
        self.name = name
        self.empty_table = empty_table
        rows = []  # rows is a finite sequence of tuples
        for i, row in enumerate(body):
            if i == self.maxrows:
                rows.append(
                    ["Table truncated because too big: more than %s rows" % i])
                break
            rows.append(row)
        self.rows = rows
        self.header = tuple(header)  # horizontal header

    def render(self, dummy_ctxt=None):
        out = "\n%s\n" % "".join(list(self._gen_table()))
        if not self.rows:
            out += '<em>%s</em>' % cgi.escape(self.empty_table, quote=True)
        return out

    def _gen_table(self):
        yield '<table id="%s" border="%s" summary="%s" class="tablesorter">\n'\
              % (self.name, self.border, self.summary)
        yield '<thead>\n'
        yield '<tr>%s</tr>\n' % ''.join(
            '<th>%s</th>\n' % h for h in self.header)
        yield '</thead>\n'
        yield '<tbody\n>'
        for r, row in enumerate(self.rows):
            yield '<tr class="%s">\n' % ["even", "odd"][r % 2]
            for col in row:
                yield '<td>%s</td>\n' % col
            yield '</tr>\n'
        yield '</tbody>\n'
        yield '</table>\n'


PERFORMANCE = '''
SELECT operation, tot_duration, pymemory, counts FROM uiapi.performance_view
WHERE oq_job_id=%s ORDER BY tot_duration DESC LIMIT 15
'''

CALCULATION = '''
SELECT distinct job_type, calculation_id, description
FROM uiapi.performance_view WHERE oq_job_id=%s
'''

NUM_REALIZATIONS = '''
SELECT b.id, count(*) FROM hzrdr.lt_realization AS a,
hzrdr.lt_source_model AS b
WHERE a.lt_model_id=b.id AND hazard_calculation_id=%s
GROUP BY b.id
'''

NUM_SITES = '''
SELECT count(a.id) FROM hzrdi.hazard_site
WHERE hazard_calculation_id=%s
'''

NUM_MODELS = '''
SELECT count(id) FROM hzrdr.lt_source_model WHERE hazard_calculation_id=%s
'''

MODEL_INFO = '''
SELECT a.id, lt_model_id, tectonic_region_type, num_sources, num_ruptures,
min_mag, max_mag, CASE WHEN num_ruptures > 0 THEN array_length(gsims, 1) ELSE 0
END as num_gsim, array_to_string(gsims, ',') AS gsims
FROM hzrdr.trt_model AS a, hzrdr.lt_source_model AS b
WHERE a.lt_model_id=b.id AND b.hazard_calculation_id=%s
ORDER BY a.id, num_sources
'''

MODEL_SUMMARY = '''
SELECT x.*, y.num_rlzs FROM (
SELECT b.id, b.sm_name, array_to_string(sm_lt_path, ',') AS sm_lt_path,
       count(tectonic_region_type) as num_trts,
       sum(num_sources) as num_sources, sum(num_ruptures) AS num_ruptures
FROM hzrdr.trt_model AS a, hzrdr.lt_source_model AS b
WHERE a.lt_model_id=b.id AND b.hazard_calculation_id=%s GROUP BY b.id) AS x,
(SELECT lt_model_id, count(*) AS num_rlzs FROM hzrdr.lt_realization
GROUP by lt_model_id) AS y
WHERE x.id=y.lt_model_id
ORDER BY num_rlzs * num_ruptures DESC
'''

JOB_STATS = '''
SELECT description, oq_job_id,
       stop_time, status, disk_space / 1024 / 1024 as disk_space_mb,
       duration FROM (
  SELECT oq_job_id, value AS description, stop_time, status, disk_space,
  stop_time - start_time as duration
  FROM uiapi.job_stats AS s
  INNER JOIN uiapi.oq_job AS o
  ON s.oq_job_id=o.id
  LEFT JOIN uiapi.job_param AS p
  ON o.id=p.job_id AND name='description') AS x
WHERE oq_job_id=%s;
'''

JOB_INFO = '''
SELECT * FROM uiapi.job_info WHERE oq_job_id=%s;
'''

JOB_PARAM = '''
SELECT name, value FROM uiapi.job_param WHERE job_id=%s ORDER BY name;
'''

GMF_STATS = '''
WITH gmf_stats AS (
SELECT count(*) AS nrows_per_rlz, avg(array_length(gmvs, 1)) AS gmvs_len,
       stddev(array_length(gmvs, 1)) AS stddev
       FROM hzrdr.gmf_data AS a, hzrdr.gmf AS b, uiapi.output AS c
       WHERE a.gmf_id=b.id AND b.output_id=c.id
       AND c.id=(SELECT max(x.id) FROM uiapi.output AS x, hzrdr.gmf AS y
                 WHERE x.id=y.output_id AND oq_job_id=%s))
SELECT nrows_per_rlz, gmvs_len, stddev FROM gmf_stats;
'''

SES_STATS = '''
SELECT c.lt_model_id, e.sm_name, count(*) AS n_ruptures,
(SELECT count(*) FROM hzrdr.lt_realization
WHERE lt_model_id=c.lt_model_id) AS n_realizations
FROM hzrdr.ses_rupture AS a,
hzrdr.probabilistic_rupture AS b, hzrdr.ses_collection AS c, uiapi.output AS d,
hzrdr.lt_source_model AS e
WHERE a.rupture_id=b.id AND b.ses_collection_id=c.id AND c.output_id=d.id
AND c.lt_model_id=e.id
AND oq_job_id=%s AND output_type='ses'
GROUP BY c.lt_model_id, e.sm_name
ORDER BY c.lt_model_id;
'''

ALL_JOBS = '''
SELECT s.oq_job_id, 'hazard ' || COALESCE(o.hazard_calculation_id::text, ''),
o.user_name, status FROM uiapi.job_stats AS s
INNER JOIN uiapi.oq_job AS o
ON o.id=s.oq_job_id
WHERE stop_time::date = %s OR stop_time IS NULL AND start_time >= %s
ORDER BY stop_time
'''

PAGE_TEMPLATE = '''\
<html>
<head>
<script src="http://ajax.googleapis.com/ajax/libs/jquery/2.1.1/jquery.min.js"></script>
<link rel="stylesheet" href="http://ajax.googleapis.com/ajax/libs/jqueryui/1.11.2/themes/smoothness/jquery-ui.css" />
<script src="http://ajax.googleapis.com/ajax/libs/jqueryui/1.11.2/jquery-ui.min.js"></script>
<script>
$(function() {
$("#tabs").tabs();
});
</script>
</head>
<body>
%s
</body>
</html>
'''


def make_tabs(tag_ids, tag_status, tag_contents):
    """
    Return a HTML string containing all the tabs we want to display
    """
    templ = '''
<div id="tabs">
<ul>
%s
</ul>
%s
</div>'''
    lis = []
    contents = []
    for i, (tag_id, status, tag_content) in enumerate(
            zip(tag_ids, tag_status, tag_contents), 1):
        mark = '.' if status == 'complete' else '!'
        lis.append('<li><a href="#tabs-%d">%s%s</a></li>' % (i, tag_id, mark))
        contents.append('<div id="tabs-%d">%s</div>' % (
            i, tag_content))
    return templ % ('\n'.join(lis), '\n'.join(contents))


def make_report(conn, isodate='today'):
    """
    Build a HTML report with the computations performed at the given isodate.
    Return the name of the report, which is saved in the current directory.
    """
    if isodate == 'today':
        isodate = datetime.date.today().isoformat()
    curs = conn.cursor()
    fetcher = Fetcher(curs)
    tag_ids = []
    tag_status = []
    tag_contents = []

    jobs = fetcher.query(ALL_JOBS, isodate, isodate)[1:]
    page = '<h2>%d job(s) finished before midnight of %s</h2>' % (
        len(jobs), isodate)
    for job_id, prev_job, user, status in jobs:
        page = ''
        tag_ids.append(job_id)
        tag_status.append(status)
        stats = fetcher.query(JOB_STATS, job_id)[1:]
        if not stats:
            continue
        (description, job_id, stop_time, status, disk_space,
         duration) = stats[0]
        num_rlzs = fetcher.query(NUM_REALIZATIONS, (job_id,))[1:]
        if num_rlzs:
            source_models, rlzs = zip(*num_rlzs)
            tot_rlzs = sum(rlzs)
        else:
            tot_rlzs = 0

        data = fetcher.query(JOB_INFO, job_id)
        if data[1:]:
            info_rows = (
                '<h3>Job Info for calculation=%s, %s</h3>'
                '<h3>owner: %s, realizations: %d </h3>' % (
                    job_id, description, user, tot_rlzs,
                )) + html(data)
            page += info_rows

        job_stats = '<h3>Job Stats for job %d [%s, %s]</h3>' % (
            job_id, user, prev_job) + html(
            fetcher.query(JOB_STATS, job_id))
        page += job_stats

        slowest = '<h3>Slowest operations</h3>' + html(
            fetcher.query(PERFORMANCE, job_id))
        page += slowest

        # the following is slow, so uncomment it only when you really
        # want to compute the GMF statistics
        # data = fetcher.query(GMF_STATS, job_id)
        # if data[1][0]:  # nrows nonzero
        #     gmf_rows = '<h3>GMF stats</h3>' + html(data)
        #    page += gmf_rows

        data = fetcher.query(MODEL_INFO, job_id)
        if data[1:]:
            info_rows = '<h3>TRT Model Info</h3>' + html(data)
            page += info_rows

        if data[2:]:
            dat = fetcher.query(MODEL_SUMMARY, job_id)
            if dat[1:]:
                num_models, = fetcher.query(NUM_MODELS, job_id)[1]
                info_rows = ('<h3>Model Summary: %s model(s)</h3>' %
                             num_models) + html(dat)
                page += info_rows

        page += '<h3>Job parameters</h3>'
        data = fetcher.query(JOB_PARAM, job_id)
        page += html((n, truncate(v)) for n, v in data)
        tag_contents.append(page)

    page = make_tabs(tag_ids, tag_status, tag_contents) + (
        'Report last updated: %s' % datetime.datetime.now())
    fname = 'jobs-%s.html' % isodate
    with open(fname, 'w') as f:
        f.write(PAGE_TEMPLATE % page)
    return fname
