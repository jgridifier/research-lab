"""Freeze the complete published Y-9C result tree, including figures."""
import hashlib
from pathlib import Path

EXPECTED = {'figures/aggregate_nii.png': '8fd4b7266626fb8a13864a7601912188017aebeb5b4095102e7d1ae9364c03bd',
 'figures/annual_mae.png': 'ecefe4ce98aa5c0e99a0b4ddf4ebb1a0d0e788d7061508fe3c9c97731388ef7c',
 'figures/coverage.png': 'bf357a81f3f150d016ce3c3bdb0d7b14fd49e8c1a98a6f7747c3e0c1de40cabc',
 'figures/jpm_nii.png': '1a3040fd414ea7f0df878e3e89c65ff255d2b8b03e9839a04f5f70e2a2dd8893',
 'index.html': 'faaedd807d0bee2bebb71543bdc9f16db14e669cfaf30f03a1aac3088db9c7cc',
 'tables/by_year_errors.csv': '7325da199bae73eedc72da9a06948b5a5338b2f16edeecbc887b00f5e7db079d',
 'tables/by_year_errors.json': '8ff7b9b70c9c075d2a8b5371c6245af5a0051e3f90aa0b1c187814953b25b4ca',
 'tables/dm_tests.csv': '1b1bc30d520eee8df0a72e6460cc6702a2e5dfb0c9d85e14e9a1c1204f4142f4',
 'tables/dm_tests.json': 'b6050030fdf75551801ddb6b6cd54c78b8abcb699c744218e00b1e57bc854ee5',
 'tables/overall_errors.csv': '342ae6bbb809daf831ea4bf5ac5084104cd571896bb1eb7cba57193ef2b27a2d',
 'tables/overall_errors.json': '8584830080f7797fa1f591a318ec981e02cd2cd875504b380d762344f845682d',
 'tables/test_design.json': '8a52931a8a07d095dc15dff1d1c83e84ac9ef4964cb2a701c8d3ecd44ed692f4',
 'tables/vintage.json': '5f430aa25da83d1cebbb2919aa3a361f36b5ffdcd8c48fbba9a28de329e7ba80'}

def test_published_outputs_byte_identical():
    root = Path(__file__).resolve().parents[3] / "docs/tracks/y9c-panel/results"
    actual = {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in root.rglob("*") if p.is_file()}
    assert actual == EXPECTED, "Y-9C published results changed and must stay byte-identical"
