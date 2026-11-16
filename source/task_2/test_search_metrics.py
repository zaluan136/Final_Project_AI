import unittest
from threading import Event
from time import perf_counter

from task_2.benchmark import compare, endgames
from task_2.core.rules import GameRules
from task_2.search.algorithms import Searcher, SearchConfig


class SearchMetricTests(unittest.TestCase):
    def test_visits_and_expansions_are_distinct(self):
        rules = GameRules()
        for state in endgames():
            plain = Searcher(rules, SearchConfig(1,False,False,False)).choose(state,0)
            pruned = Searcher(rules, SearchConfig(1,True,False,False)).choose(state,0)
            self.assertEqual(plain.score,pruned.score)
            self.assertEqual(plain.action,pruned.action)
            for result in (plain,pruned):
                self.assertGreater(result.stats.expanded_nodes,0)
                self.assertLess(result.stats.expanded_nodes,result.stats.nodes)
            self.assertLessEqual(pruned.stats.nodes,plain.stats.nodes)

    def test_expired_search_expands_no_node(self):
        result = Searcher(GameRules()).choose(endgames()[0],0,deadline=perf_counter()-1)
        self.assertTrue(result.stats.timed_out)
        self.assertEqual(result.stats.expanded_nodes,0)

    def test_comparison_sample_counts_and_metrics(self):
        rows = compare(budget_ms=5,depth=1,repeats=2)
        self.assertEqual(len(rows),8)
        for row in rows:
            self.assertEqual(row.samples,4 if row.suite=='terminal' else 2)
            self.assertGreaterEqual(row.mean_expanded_nodes,0)
            self.assertLessEqual(row.mean_expanded_nodes,row.mean_nodes)
            self.assertGreaterEqual(row.std_expanded_nodes,0)
            self.assertGreaterEqual(row.std_depth,0)

    def test_invalid_or_cancelled_comparison(self):
        for repeats in (0,-1,True):
            with self.assertRaises(ValueError):compare(repeats=repeats)
        cancelled = Event();cancelled.set()
        self.assertEqual(compare(cancel_event=cancelled),[])


if __name__=='__main__':unittest.main()
