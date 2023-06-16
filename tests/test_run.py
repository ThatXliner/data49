# import functools
# import operator
#
# import pytest
#
# from data49 import run
#
#
# def test_pipeline():
#     assert (
#         run.Pipeline([lambda: 1, functools.partial(operator.add, 1), lambda x: x * 9])()
#         == (1 + 1) * 9
#     )
#
#
# class TestSluice:
#     def test_synchronous(self):
#         g = []
#         pipeline = run.Sluice(
#             [
#                 lambda: g.append(0),
#                 lambda: g.append(1),
#                 lambda: g.append(2),
#                 lambda: g.append(3),
#             ]
#         )
#         pipeline.run()
#         assert g == list(range(4))
#
#     class TestAsynchronous:
#         def test_bundle(self):
#             g = []
#             pipeline = run.Sluice(
#                 [
#                     (
#                         lambda: g.append(0),
#                         lambda: g.append(1),
#                         lambda: g.append(2),
#                         lambda: g.append(3),
#                     )
#                 ],
#                 concurrent=True,
#             )
#             pipeline.run()
#             assert g == list(range(4))
#
#         def test_normalcase(self):
#             g = []
#             pipeline = run.Sluice(
#                 [
#                     lambda: g.append(0),
#                     lambda: g.append(1),
#                     lambda: g.append(2),
#                     lambda: g.append(3),
#                 ],
#                 concurrent=True,
#             )
#             pipeline.run()
#             for x in range(4):
#                 assert x in g
#
#         def test_no_chain(self):
#             with pytest.raises(ValueError):
#                 run.Sluice(
#                     [],
#                     concurrent=True,
#                     chain=True,
#                 ).run()
#
#     def test_typo(self):
#         g = []
#         pipeline = run.Sluice(
#             [
#                 lambda: g.append(0),
#                 lambda: g.append(1),
#                 lambda: g.append(2),
#                 lambda: g.append(3),
#             ]
#         )
#         with pytest.warns(UserWarning, match="I'm going to assume you meant"):
#             pipeline.rn()
#         assert g == list(range(4))
#
#
# def test_bundle():
#     assert (
#         run.Bundle(
#             [functools.partial(operator.add, 1) for _ in range(5)],
#             first=1,
#             chain=True,
#         )()
#         == 6
#     )
