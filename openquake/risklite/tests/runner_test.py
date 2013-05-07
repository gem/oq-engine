from nose.tools import assert_equal
from openquake.concurrent.futures import \
    ProcessPoolExecutor, ThreadPoolExecutor
from openquake.risklite.parallel import Runner, BaseRunner


# from list to list
def double(elements):
    return [2 * el for el in elements]


# from list to integer: returns the number of saved elements
def save(elements):
    # save on a file or something like that
    return len(elements)


# from list to None
def dosomething(elements):
    pass


def ok(msg):
    pass


# test all the combinations of executors, runners and functions
def test_all():
    poolsize = 4
    for executor in (ProcessPoolExecutor(poolsize),
                     ThreadPoolExecutor(poolsize)):
        with executor:
            for runnercls in (BaseRunner, Runner):
                runner = runnercls([], executor)

                # less elements than the pool size
                out = runner.run_in_order(double, [1, 2, 3])
                assert_equal(out, [2, 4, 6])
                yield ok, 'doubling list of 3 elements with %s' % runner

                # more elements than the pool size
                out = runner.run_in_order(double, range(100))
                assert_equal(out, [2 * x for x in range(100)])
                yield ok, 'doubling list of 100 elements with %s' % runner

                # sum integers
                runner = runnercls(0, executor)
                saved = runner.run(save, range(100))
                assert_equal(saved, 100)
                yield ok, 'saving list of 100 elements with %s' % runner

                # ignore return values
                runner = runnercls(None, executor, agg=lambda acc, val: None)
                none = runner.run(dosomething, range(100))
                assert_equal(none, None)
                yield ok, 'working on 100 elements with %s' % runner
