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
select operation,
-- tot_duration/(case when counts > 256 then 256 else counts end) as duration,
tot_duration, pymemory, counts from uiapi.performance_view
where oq_job_id=%s order by tot_duration desc limit 15
'''

CALCULATION = '''
select distinct job_type, calculation_id, description
from uiapi.performance_view where oq_job_id=%s
'''

NUM_REALIZATIONS = '''
select b.id, count(*) from hzrdr.lt_realization as a,
hzrdr.lt_source_model as b
where a.lt_model_id=b.id
and hazard_calculation_id=%s group by b.id
'''

NUM_SITES = '''
select count(a.id) from hzrdi.hazard_site
where hazard_calculation_id=%s
'''

NUM_MODELS = '''
select count(id) from hzrdr.lt_source_model where hazard_calculation_id=%s
'''

MODEL_INFO = '''
select a.id, lt_model_id, tectonic_region_type, num_sources, num_ruptures,
min_mag, max_mag, case when num_ruptures > 0 then array_length(gsims, 1) else 0
end as num_gsim, array_to_string(gsims, ',') as gsims
from hzrdr.trt_model as a, hzrdr.lt_source_model as b
where a.lt_model_id=b.id and b.hazard_calculation_id=%s
order by a.id, num_sources
'''

MODEL_SUMMARY = '''
select x.*, y.num_rlzs from (
select b.id, b.sm_name, array_to_string(sm_lt_path, ',') as sm_lt_path,
       count(tectonic_region_type) as num_trts,
       sum(num_sources) as num_sources, sum(num_ruptures) as num_ruptures
from hzrdr.trt_model as a, hzrdr.lt_source_model as b
where a.lt_model_id=b.id and b.hazard_calculation_id=%s group by b.id) as x,
(select lt_model_id, count(*) as num_rlzs from hzrdr.lt_realization
group by lt_model_id) as y
where x.id=y.lt_model_id
order by num_rlzs * num_ruptures desc
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
  INNER JOIN uiapi.job_param AS p
  ON o.id=p.job_id AND name='description') AS x
WHERE oq_job_id=%s;
'''

JOB_INFO = '''
SELECT * FROM uiapi.job_info where oq_job_id=%s;
'''

JOB_PARAM = '''
SELECT name, value FROM uiapi.job_param where job_id=%s ORDER BY name;
'''

GMF_STATS = '''
with gmf_stats as (
select count(*) as nrows_per_rlz, avg(array_length(gmvs, 1)) as gmvs_len,
       stddev(array_length(gmvs, 1)) as stddev
       from hzrdr.gmf_data as a, hzrdr.gmf as b, uiapi.output as c
       where a.gmf_id=b.id and b.output_id=c.id
       and c.id=(select max(x.id) from uiapi.output as x, hzrdr.gmf as y
                 where x.id=y.output_id and oq_job_id=%s))
select nrows_per_rlz, gmvs_len, stddev from gmf_stats;
'''

SES_STATS = '''
select c.lt_model_id, e.sm_name, count(*) as n_ruptures,
(select count(*) from hzrdr.lt_realization
where lt_model_id=c.lt_model_id) as n_realizations
from hzrdr.ses_rupture as a,
hzrdr.probabilistic_rupture as b, hzrdr.ses_collection as c, uiapi.output as d,
hzrdr.lt_source_model as e
where a.rupture_id=b.id and b.ses_collection_id=c.id and c.output_id=d.id
and c.lt_model_id=e.id
and oq_job_id=%s and output_type='ses'
group by c.lt_model_id, e.sm_name
order by c.lt_model_id;
'''

ALL_JOBS = '''
select s.oq_job_id, 'hazard ' || coalesce(o.hazard_calculation_id::text, ''),
o.user_name from uiapi.job_stats as s
inner join uiapi.oq_job as o
on o.id=s.oq_job_id
where stop_time::date=%s or stop_time is null
order by stop_time
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


def make_tabs(tag_ids, tag_contents):
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
    for i, (tag_id, tag_content) in enumerate(zip(tag_ids, tag_contents), 1):
        lis.append('<li><a href="#tabs-%d">%s</a></li>' % (i, tag_id))
        contents.append('<div id="tabs-%d">%s</div>' % (i, tag_content))
    return templ % ('\n'.join(lis), '\n'.join(contents))


def make_report(conn, isodate='today'):
    """
    Build a HTML report with the computations performed at the given isodate.
    Return the name of the report, which
    is saved in the current directory.
    """
    if isodate == 'today':
        isodate = datetime.date.today().isoformat()
    curs = conn.cursor()
    fetcher = Fetcher(curs)
    tag_ids = []
    tag_contents = []

    jobs = fetcher.query(ALL_JOBS, isodate)[1:]
    page = '<h2>%d job(s) finished before midnight of %s</h2>' % (
        len(jobs), isodate)
    for job_id, prev_job, user in jobs:
        page = ''
        tag_ids.append(job_id)
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

        ##data = fetcher.query(GMF_STATS, job_id)
        ##if data[1][0]:  # nrows nonzero
        ##    gmf_rows = '<h3>GMF stats</h3>' + html(data)
        ##    page += gmf_rows

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

    page = make_tabs(tag_ids, tag_contents) + (
        'Report last updated: %s' % datetime.datetime.now())
    fname = 'jobs-%s.html' % isodate
    with open(fname, 'w') as f:
        f.write(PAGE_TEMPLATE % page)
    return fname
