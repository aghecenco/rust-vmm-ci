# Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
"""Test that performance does not decrease."""

import os, subprocess
import pytest

from utils import get_repo_root_path

BENCH_PATH = os.path.join(get_repo_root_path(), "target/criterion")


class BenchResult:
    bench_name = None
    result = None
    times = None
    changes = None

    def __init__(self, name):
        self.bench_name = name


@pytest.mark.skipif(
    not os.path.exists(BENCH_PATH),
    reason="this crate does not have benchmarks"
)
def test_bench():
    # Run cargo bench to get new numbers.
    results = {}
    for line in _run_cargo_bench().stdout.decode(encoding='utf-8').split('\n'):
        # Which benchmark are we assessing?
        if 'Benchmarking' in line:
            curr_bench = line.split('Benchmarking ')[1].split(':')[0]
            results[curr_bench] = BenchResult(curr_bench)
            continue
        # Do we encounter either one of the criterion pass/fail messages?
        elif 'No change in performance detected.' in line or \
            'Change within noise threshold.' in line:
            results[curr_bench].result = 'NO_CHANGE'
        elif 'Performance has regressed.' in line:
            results[curr_bench].result = 'REGRESSION'
        elif 'Performance has improved.' in line:
            results[curr_bench].result = 'IMPROVEMENT'

        # Save the durations.
        elif 'time:' in line:
            results[curr_bench].times = line.split('time: ')[1].strip()
        # Save the change percentages.
        elif 'change:' in line:
            results[curr_bench].changes = line.split('change: ')[1].strip()


    regressions = [b for b in results if results[b].result == 'REGRESSION']
    no_change = [b for b in results if results[b].result == 'NO_CHANGE']
    improvements = [b for b in results if results[b].result == 'IMPROVEMENT']

    if len(improvements) > 0:
        print('Improvements:')
        for bench in improvements:
            print(bench)
    if len(no_change) > 0:
        print('No change:')
        for bench in no_change:
            print(bench)
    if len(regressions) > 0:
        print('Regressions:')
        for bench in regressions:
            print(bench)
        assert False, "Benchmarks {} have regressed.".format(regressions)


def _run_cargo_bench():
    bench_cmd = "cargo bench " \
                   "--no-fail-fast " \
                   "--all-features " \
                   "--all-targets " \
                   "--workspace " \
                   "--quiet"

    return subprocess.run(
        bench_cmd, shell=True, check=True, stdout=subprocess.PIPE
    )
