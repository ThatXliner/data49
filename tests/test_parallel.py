from data49.parallel import Sluice


def test_sequential_pipeline_runs_grouped_functions_in_order():
    calls = []
    pipeline = [
        lambda: calls.append("a"),
        (lambda: calls.append("b"), lambda: calls.append("c")),
    ]
    Sluice(pipeline).run()
    assert calls == ["a", "b", "c"]


def test_sequential_chain_preserves_values_across_a_group():
    pipeline = [lambda: 2, (lambda value: value + 1, lambda value: value * 3)]
    assert Sluice(pipeline, chain=True).run() == 9
