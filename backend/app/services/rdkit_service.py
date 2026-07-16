"""
PatentPilot RDKit Service.

Provides molecule validation, canonicalization, and fingerprint-based
similarity computation using the RDKit cheminformatics toolkit.
"""

import logging

from rdkit import Chem
from rdkit.Chem import AllChem, DataStructs

logger = logging.getLogger(__name__)


def validate_smiles(smiles: str) -> tuple[bool, str | None]:
    """
    Validate and canonicalize a SMILES string.

    Args:
        smiles: Input SMILES string.

    Returns:
        Tuple of (is_valid, canonical_smiles_or_None).
    """
    if not smiles or not smiles.strip():
        logger.warning("Empty SMILES string received.")
        return (False, None)

    try:
        mol = Chem.MolFromSmiles(smiles.strip())
        if mol is None:
            logger.warning("RDKit could not parse SMILES: %s", smiles)
            return (False, None)

        canonical = Chem.MolToSmiles(mol)
        logger.info("Validated SMILES — canonical form: %s", canonical)
        return (True, canonical)
    except Exception as exc:
        logger.error("Unexpected error validating SMILES '%s': %s", smiles, exc)
        return (False, None)


def compute_tanimoto(smiles1: str, smiles2: str) -> float:
    """
    Compute Tanimoto similarity between two molecules using
    Morgan fingerprints (radius=2, 2048 bits).

    Args:
        smiles1: First SMILES string.
        smiles2: Second SMILES string.

    Returns:
        Tanimoto coefficient (0.0–1.0), or 0.0 on error.
    """
    try:
        mol1 = Chem.MolFromSmiles(smiles1)
        mol2 = Chem.MolFromSmiles(smiles2)

        if mol1 is None or mol2 is None:
            logger.warning(
                "Cannot compute Tanimoto — invalid SMILES: %s / %s",
                smiles1, smiles2,
            )
            return 0.0

        fp1 = AllChem.GetMorganFingerprintAsBitVect(mol1, radius=2, nBits=2048)
        fp2 = AllChem.GetMorganFingerprintAsBitVect(mol2, radius=2, nBits=2048)

        similarity = DataStructs.TanimotoSimilarity(fp1, fp2)
        return float(similarity)
    except Exception as exc:
        logger.error("Error computing Tanimoto similarity: %s", exc)
        return 0.0


def generate_molecule_svg(smiles: str) -> str | None:
    """
    Generate a 2D depiction of the molecule as an SVG string.

    Args:
        smiles: Input SMILES string.

    Returns:
        String containing SVG XML, or None on failure.
    """
    if not smiles or not smiles.strip():
        return None

    try:
        mol = Chem.MolFromSmiles(smiles.strip())
        if mol is None:
            return None

        # Generate 2D coordinates for drawing
        from rdkit.Chem import rdDepictor
        rdDepictor.Compute2DCoords(mol)

        # Draw to SVG with transparent background
        from rdkit.Chem.Draw import rdMolDraw2D
        drawer = rdMolDraw2D.MolDraw2DSVG(350, 300)
        
        # Configure drawing options for a clean look in light/dark modes
        options = drawer.drawOptions()
        options.backgroundColour = None
        options.clearBackground = True
        options.useBWAtomGlyphs = False  # Keep standard element colors (O=red, N=blue)
        
        # Draw the molecule
        drawer.DrawMolecule(mol)
        drawer.FinishDrawing()
        
        svg = drawer.GetDrawingText()
        
        # Strip XML header if present
        svg_start = svg.find("<svg")
        if svg_start != -1:
            svg = svg[svg_start:]
            
        return svg
    except Exception as exc:
        logger.error("Error generating SVG for SMILES '%s': %s", smiles, exc)
        return None
