"""
Unit tests for the RDKit service.

Covers:
  - SMILES validation (valid, invalid, empty)
  - Canonicalization
  - Tanimoto similarity (identical molecules, different molecules)
"""

import pytest

from app.services.rdkit_service import validate_smiles, compute_tanimoto


# Well-known SMILES for testing
ASPIRIN_SMILES = "CC(=O)Oc1ccccc1C(=O)O"
IBUPROFEN_SMILES = "CC(C)Cc1ccc(cc1)C(C)C(=O)O"
CAFFEINE_SMILES = "Cn1c(=O)c2c(ncn2C)n(C)c1=O"


# ─── Validation ─────────────────────────────────────────────────────


class TestValidateSmiles:
    """Tests for validate_smiles."""

    def test_valid_smiles_aspirin(self):
        """Aspirin SMILES should be valid."""
        is_valid, canonical = validate_smiles(ASPIRIN_SMILES)
        assert is_valid is True
        assert canonical is not None
        assert len(canonical) > 0

    def test_valid_smiles_ibuprofen(self):
        """Ibuprofen SMILES should be valid."""
        is_valid, canonical = validate_smiles(IBUPROFEN_SMILES)
        assert is_valid is True
        assert canonical is not None

    def test_invalid_smiles(self):
        """Gibberish string should be invalid."""
        is_valid, canonical = validate_smiles("not_a_real_smiles_XYZ!!!")
        assert is_valid is False
        assert canonical is None

    def test_empty_smiles(self):
        """Empty string should be invalid."""
        is_valid, canonical = validate_smiles("")
        assert is_valid is False
        assert canonical is None

    def test_whitespace_only_smiles(self):
        """Whitespace-only string should be invalid."""
        is_valid, canonical = validate_smiles("   ")
        assert is_valid is False
        assert canonical is None

    def test_canonicalization(self):
        """Different valid representations should produce the same canonical form."""
        _, canon1 = validate_smiles("c1ccccc1")   # benzene (aromatic)
        _, canon2 = validate_smiles("C1=CC=CC=C1") # benzene (Kekulé)
        assert canon1 is not None
        assert canon2 is not None
        assert canon1 == canon2


# ─── Tanimoto Similarity ───────────────────────────────────────────


class TestComputeTanimoto:
    """Tests for compute_tanimoto."""

    def test_tanimoto_identical(self):
        """Identical molecules should have similarity 1.0."""
        sim = compute_tanimoto(ASPIRIN_SMILES, ASPIRIN_SMILES)
        assert sim == pytest.approx(1.0, abs=1e-6)

    def test_tanimoto_different(self):
        """Structurally different molecules should have similarity < 1.0."""
        sim = compute_tanimoto(ASPIRIN_SMILES, CAFFEINE_SMILES)
        assert 0.0 <= sim < 1.0

    def test_tanimoto_invalid_smiles(self):
        """Invalid SMILES should return 0.0 without raising."""
        sim = compute_tanimoto(ASPIRIN_SMILES, "INVALID")
        assert sim == 0.0

    def test_tanimoto_both_invalid(self):
        """Both invalid SMILES should return 0.0."""
        sim = compute_tanimoto("INVALID1", "INVALID2")
        assert sim == 0.0

    def test_tanimoto_range(self):
        """Similarity between related molecules should be in (0, 1)."""
        sim = compute_tanimoto(ASPIRIN_SMILES, IBUPROFEN_SMILES)
        assert 0.0 < sim < 1.0
