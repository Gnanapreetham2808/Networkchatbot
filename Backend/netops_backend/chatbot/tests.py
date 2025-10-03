from django.test import TestCase
from Devices.device_resolver import resolve_device


class VijayawadaResolutionTests(TestCase):
	def _assert_alias(self, query: str, expected: str = "INVIJB1SW1"):
		dev, candidates, err = resolve_device(query)
		self.assertIsNotNone(dev, f"Device should resolve for query '{query}' (err={err}, candidates={candidates})")
		self.assertEqual(dev.get("alias"), expected, f"Expected alias {expected} for query '{query}' but got {dev.get('alias')}")
		self.assertFalse(candidates, f"Did not expect candidates for query '{query}'")

	def test_vij_short(self):
		self._assert_alias("show interfaces vij")

	def test_vijay_partial(self):
		self._assert_alias("show version vijay")

	def test_vijaya_partial(self):
		self._assert_alias("show ip route vijaya")

	def test_building_one(self):
		self._assert_alias("building 1 status")

	def test_india_keyword(self):
		self._assert_alias("india switch details")

	def test_mixed_ambiguous(self):
		dev, candidates, err = resolve_device("london and vijayawada status")
		# Expect ambiguity (both locations) -> no dev, some candidates
		self.assertIsNone(dev)
		self.assertTrue(candidates, "Expected candidates for ambiguous multi-site query")
		self.assertIsNotNone(err)
